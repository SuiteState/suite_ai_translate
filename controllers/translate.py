# -*- coding: utf-8 -*-
import logging
import time

from odoo import _, http
from odoo.exceptions import UserError
from odoo.http import request

from ..models.languages import LANG_PROMPT_NAME

_logger = logging.getLogger(__name__)


class SuiteAITranslateController(http.Controller):
    """HTTP endpoints for Discuss AI Translate.

    The module follows a near-WYSIWYG philosophy: the native Discuss
    send path is NOT intercepted in any way. Our UI helps the user
    produce translated text and then swaps it into the composer input
    before the user hits the native send button; whatever the user
    sees at send time is what gets posted.

    Endpoints:
      * /suite_ai_translate/compose      - translate a draft (pure, no side effects)
      * /suite_ai_translate/get_last_id  - snapshot of the thread's last msg.id
                                          (for race-free mark_last)
      * /suite_ai_translate/mark_last    - record the pre-translation original
                                          text on a just-sent message so it
                                          remains viewable internally
    """

    @http.route(
        '/suite_ai_translate/compose',
        type='jsonrpc',
        auth='user',
    )
    def compose_preview(self, text, target_lang):
        """Translate composer draft text. Pure function, no persistence.

        Returns:
            {'text': '<translated>'} on success,
            {'error': '<reason>'} on failure.
        """
        text = (text or '').strip()
        if not text:
            return {'text': ''}

        # Explicit empty guard for target_lang — distinct from
        # "unsupported code" so the frontend can show a better message.
        if not target_lang or not str(target_lang).strip():
            return {'error': _("No target language selected.")}

        if target_lang not in LANG_PROMPT_NAME:
            return {'error': _("Unsupported target language.")}

        Message = request.env['mail.message']
        try:
            translated = Message._sat_call_llm(text, target_lang)
            return {'text': translated}
        except UserError as e:
            return {'error': str(e)}
        except Exception as e:
            _logger.exception("suite_ai_translate compose failed")
            return {'error': _("Translation failed: %s", str(e))}

    @http.route(
        '/suite_ai_translate/get_last_id',
        type='jsonrpc',
        auth='user',
    )
    def get_last_id(self, thread_model, thread_id):
        """Return the max mail.message id currently in the thread, used
        as a BASELINE by the composer right BEFORE it calls the native
        send path. mark_last then searches for the first message whose
        id > baseline, which is guaranteed to be the one we just sent
        (even if the DB write hadn't flushed at send-time).

        Without this baseline, mark_last's "last message by me in
        thread" search was racing against the not-yet-committed new
        message and kept stamping the PREVIOUS message with the CURRENT
        send's original text — every send was offset by one.
        """
        if not thread_model or not thread_id:
            return {'id': 0}
        last = request.env['mail.message'].search([
            ('model', '=', thread_model),
            ('res_id', '=', int(thread_id)),
        ], order='id desc', limit=1)
        return {'id': last.id if last else 0}

    @http.route(
        '/suite_ai_translate/mark_last',
        type='jsonrpc',
        auth='user',
    )
    def mark_last(self, thread_model, thread_id, original_body,
                  target_lang, baseline_id=0):
        """Record original text + translation language on the message
        the current user JUST posted to the given thread.

        ``baseline_id`` is the max mail.message id the thread had
        immediately before ``super.sendMessage()`` was called on the
        frontend. We search for ``id > baseline_id``, which uniquely
        identifies the message we just sent and avoids the race where
        the new message hadn't committed yet and we would have stamped
        the PREVIOUS one.

        We retry up to 10 times at 100ms intervals because the send
        happens in a separate HTTP request that may still be committing
        when mark_last arrives.

        Failure is non-fatal: if we can't find the message, we log a
        warning but don't disrupt the user's send flow.
        """
        if not thread_model or not thread_id:
            return {'ok': False, 'reason': 'bad_thread'}
        if target_lang not in LANG_PROMPT_NAME:
            return {'ok': False, 'reason': 'bad_lang'}

        author_id = request.env.user.partner_id.id
        baseline_id = int(baseline_id or 0)

        domain = [
            ('author_id', '=', author_id),
            ('model', '=', thread_model),
            ('res_id', '=', int(thread_id)),
        ]
        if baseline_id:
            domain.append(('id', '>', baseline_id))

        last_msg = None
        # Retry loop to handle the send-commit race. Each iteration
        # rolls back the current transaction's snapshot and invalidates
        # the cache so the subsequent search() sees rows committed by
        # OTHER transactions (specifically the parallel HTTP request
        # that's posting the new message). We deliberately do NOT
        # cr.commit() here — committing inside an HTTP controller before
        # the route returns breaks Odoo's transaction-boundary contract
        # and is rejected by the Odoo Apps review process.
        for attempt in range(10):
            request.env.cr.rollback()
            request.env.invalidate_all()
            last_msg = request.env['mail.message'].sudo().search(
                domain, order='id desc', limit=1,
            )
            if last_msg:
                break
            time.sleep(0.1)

        if not last_msg:
            _logger.warning(
                "mark_last: no new message found after baseline=%s "
                "for user=%s, thread=%s/%s",
                baseline_id, author_id, thread_model, thread_id,
            )
            return {'ok': False, 'reason': 'not_found'}

        # Defense in depth: even though the domain restricts to
        # author_id == current user (so we already filtered to "my own
        # messages"), explicitly verify write access on the recordset
        # before doing the sudo() write. This is a belt-and-suspenders
        # check against any future change that loosens the domain.
        try:
            last_msg.sudo(False).check_access('write')
        except Exception:
            _logger.warning(
                "mark_last: write access denied on message %s for user %s",
                last_msg.id, request.env.user.id,
            )
            return {'ok': False, 'reason': 'access_denied'}

        last_msg.with_context(mail_notrack=True).write({
            'sat_original_body': original_body or '',
            'sat_translation_lang': target_lang,
        })
        return {'ok': True, 'message_id': last_msg.id}
