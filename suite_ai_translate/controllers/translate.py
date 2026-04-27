# -*- coding: utf-8 -*-
import logging

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

    Endpoint:
      * /suite_ai_translate/compose — translate a draft (pure, no side effects)

    The sat_original_body and sat_translation_lang fields are written
    atomically inside the native /mail/message/post pipeline via
    Store.getMessagePostParams (frontend) and the mail.thread whitelist
    overrides (backend). No separate mark_last endpoint is needed.
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
