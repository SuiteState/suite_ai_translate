# -*- coding: utf-8 -*-
import logging

from psycopg2 import IntegrityError

from odoo import _, api, fields, models
from odoo.exceptions import UserError
from odoo.tools import html2plaintext

from odoo.addons.ai.utils.llm_api_service import LLMApiService
from odoo.addons.ai.utils.llm_providers import get_provider

from .languages import (
    LANG_PROMPT_NAME,
    DEFAULT_MAX_INPUT_CHARS,
    resolve_auto_language,
)
from .res_config_settings import (
    DEFAULT_PRIMARY_MODEL,
    DEFAULT_FAILOVER_MODEL,
)

_logger = logging.getLogger(__name__)


# ICP parameter names for each provider's API key. Anchored on the
# native `ai` module's parameter names (verified from source). Used to
# short-circuit failover: if a provider's key isn't configured, skip it
# instead of making a doomed LLM call.
#
# A provider NOT listed here is treated optimistically — we assume the
# key exists and let the actual LLM call decide. This keeps the module
# forward-compatible with future providers Odoo may add to the `ai`
# module.
_PROVIDER_KEY_PARAMS = {
    'openai': 'ai.openai_key',
    'google': 'ai.google_key',
}

# Default LLM sampling temperature. Low value keeps translation
# deterministic and faithful. Overridable via ICP
# `suite_ai_translate.temperature` for advanced tuning (not surfaced
# in the Settings UI — 99% of users shouldn't touch it).
_DEFAULT_TEMPERATURE = 0.2


class MailMessage(models.Model):
    _inherit = 'mail.message'

    sat_original_body = fields.Html(
        string='Original Body (before AI translation)',
        copy=False,
        sanitize_style=True,
        help="When an outgoing message is sent via the Composer's "
             "translation send button, this stores the author's "
             "pre-translation text for internal 'View original' access.",
    )

    sat_translation_lang = fields.Char(
        string='AI Translation Target Language',
        copy=False,
        help="Target language code used when this outgoing message "
             "was translated before sending (e.g. 'en', 'ar').",
    )

    # ------------------------------------------------------------------
    # Expose our fields to the Discuss frontend Store
    # ------------------------------------------------------------------

    def _to_store_defaults(self, target):
        return super()._to_store_defaults(target) + [
            'sat_original_body',
            'sat_translation_lang',
        ]

    # ------------------------------------------------------------------
    # Translation core - shared by message translation & composer preview
    # ------------------------------------------------------------------


    @api.model
    def _sat_build_system_prompt(self, target_lang_code):
        """Build the translator system prompt for a given target language."""
        target_name = LANG_PROMPT_NAME.get(target_lang_code)
        if not target_name:
            raise UserError(
                _("Language '%s' is not supported.", target_lang_code)
            )
        return (
            f"You are a professional translator. "
            f"Translate the user's text into {target_name}.\n\n"
            f"Rules:\n"
            f"- Translate to {target_name} regardless of the source language. "
            f"If the source is already in {target_name}, rephrase naturally "
            f"while preserving the original meaning.\n"
            f"- Preserve numbers, product names, model codes, "
            f"and proper nouns exactly as written.\n"
            f"- Preserve line breaks and basic structure.\n"
            f"- Output ONLY the translated text. "
            f"No preamble, no quotes, no explanation, no language labels."
        )

    @api.model
    def _sat_get_primary_model(self):
        """Return (provider, model) preferred by admin settings."""
        ICP = self.env['ir.config_parameter'].sudo()
        model = ICP.get_param(
            'suite_ai_translate.llm_model', DEFAULT_PRIMARY_MODEL,
        )
        provider = get_provider(self.env, model)
        return provider, model

    @api.model
    def _sat_get_failover_model(self):
        """Return (provider, model) used as automatic fallback when the
        primary provider fails. Configured via Settings -> AI -> Discuss
        AI Translate -> Failover Model.
        """
        ICP = self.env['ir.config_parameter'].sudo()
        model = ICP.get_param(
            'suite_ai_translate.llm_failover_model', DEFAULT_FAILOVER_MODEL,
        )
        provider = get_provider(self.env, model)
        return provider, model

    @api.model
    def _sat_provider_has_key(self, provider):
        """Check if a given provider has an API key configured.

        For known providers (see ``_PROVIDER_KEY_PARAMS``) we probe the
        anchored ICP key. For unknown providers (e.g. a future Anthropic
        / Mistral addition in the ``ai`` module), we assume the key
        exists and let the actual LLM call decide — this avoids a hard
        dependency on us maintaining a complete provider list.
        """
        param_name = _PROVIDER_KEY_PARAMS.get(provider)
        if param_name is None:
            return True
        ICP = self.env['ir.config_parameter'].sudo()
        return bool(ICP.get_param(param_name))

    @api.model
    def _sat_is_enabled(self):
        """Whether Discuss AI Translate is enabled by the administrator.

        This is the opt-in gate required by Odoo Apps vendor guidelines:
        message text is transmitted to a third-party AI provider, so the
        feature is OFF by default and must be explicitly enabled in
        Settings -> AI -> Discuss AI Translate.
        """
        ICP = self.env['ir.config_parameter'].sudo()
        return bool(ICP.get_param('suite_ai_translate.enabled'))

    @api.model
    def _sat_call_llm(self, text, target_lang_code):
        """Translate ``text`` into ``target_lang_code`` via the configured LLM.

        Implements automatic failover: if the primary provider fails and
        the configured failover provider has a key configured, retries
        with it. Both primary and failover models are admin-configurable
        (Settings -> AI -> Discuss AI Translate).

        Returns the translated string. Raises UserError on unrecoverable failure.
        """
        # Opt-in gate: refuse to transmit any text until the admin has
        # explicitly enabled the feature in Settings. This is enforced
        # at the lowest layer so every entry point (composer preview,
        # message translation) is covered uniformly.
        if not self._sat_is_enabled():
            raise UserError(_(
                "Discuss AI Translate is not enabled. An administrator "
                "must enable it in Settings -> General Settings -> AI -> "
                "Discuss AI Translate before translation features become "
                "available."
            ))

        if not text:
            return ''

        # Per-message length cap. Read from ICP so admins can raise or
        # lower it without a code change (no UI — long-tail knob, see
        # languages.py for rationale).
        ICP = self.env['ir.config_parameter'].sudo()
        try:
            max_chars = int(ICP.get_param(
                'suite_ai_translate.max_input_chars',
                DEFAULT_MAX_INPUT_CHARS,
            ))
        except (TypeError, ValueError):
            max_chars = DEFAULT_MAX_INPUT_CHARS
        if len(text) > max_chars:
            raise UserError(_(
                "The message is too long to translate (%(len)s characters, "
                "maximum is %(max)s). Please translate it in smaller "
                "pieces, or ask an administrator to raise the limit "
                "(System Parameter: suite_ai_translate.max_input_chars).",
                len=len(text),
                max=max_chars,
            ))

        system_prompt = self._sat_build_system_prompt(target_lang_code)
        primary_provider, primary_model = self._sat_get_primary_model()
        failover_provider, failover_model = self._sat_get_failover_model()

        # Sampling temperature: low by default (deterministic), but
        # overridable via ICP for advanced tuning.
        try:
            temperature = float(ICP.get_param(
                'suite_ai_translate.temperature', _DEFAULT_TEMPERATURE,
            ))
        except (TypeError, ValueError):
            temperature = _DEFAULT_TEMPERATURE

        # Build failover chain: primary first, then the configured
        # failover only if it's a DIFFERENT provider and has a key.
        # Same-provider failover gives no real resilience (if OpenAI
        # is down, another OpenAI model is also down), so skip it.
        chain = [(primary_provider, primary_model)]
        if (failover_provider != primary_provider
                and self._sat_provider_has_key(failover_provider)):
            chain.append((failover_provider, failover_model))

        last_error = None
        for provider, model in chain:
            if not self._sat_provider_has_key(provider):
                last_error = _("No API key configured for provider '%s'.", provider)
                continue
            try:
                service = LLMApiService(env=self.env, provider=provider)
                responses = service.request_llm(
                    llm_model=model,
                    system_prompts=[system_prompt],
                    user_prompts=[],
                    inputs=[{'role': 'user', 'content': text}],
                    temperature=temperature,
                )
                result = (responses[0] if responses else '').strip()
                if result:
                    return result
                last_error = _("Empty response from %s.", provider)
            except Exception as e:
                _logger.warning(
                    "suite_ai_translate: provider %s failed: %s", provider, e
                )
                last_error = str(e)
                continue

        # All providers exhausted.
        raise UserError(_(
            "Translation failed. Please check the AI provider configuration "
            "in Settings -> General Settings -> AI.\n\nDetails: %s",
            last_error or _("unknown error"),
        ))

    # ------------------------------------------------------------------
    # Public method: translate an existing message on demand
    # ------------------------------------------------------------------

    def sat_translate_message(self, target_lang_code):
        """Translate this message's body into ``target_lang_code``.

        Cache is backed by the native ``mail.message.translation`` table
        (unique per message + target_lang, auto-vacuumed after 2 weeks).
        This avoids maintaining our own schema and inherits Odoo's
        cleanup machinery.

        ``target_lang_code`` may be 'auto', in which case it resolves to
        the current user's interface language. If the user's language is
        not in our supported list, raises UserError.

        Returns:
            dict(lang=str, text=str, cached=bool)
        """
        self.ensure_one()
        self.check_access('read')

        # Opt-in gate: refuse the entire translation path (including
        # cache hits) when the feature is disabled. This makes "disable"
        # a clean kill switch — if an admin flips it off in response to
        # a data governance question, previously-cached translations
        # stop being served too.
        if not self._sat_is_enabled():
            raise UserError(_(
                "Discuss AI Translate is not enabled. An administrator "
                "must enable it in Settings -> General Settings -> AI -> "
                "Discuss AI Translate before translation features become "
                "available."
            ))

        # Explicit empty guard: reject empty / None / whitespace early
        # with a clear message, before the generic "not supported" path.
        if not target_lang_code or not str(target_lang_code).strip():
            raise UserError(_(
                "No target language selected. Please pick a language "
                "from the menu."
            ))

        # Auto-resolve target language.
        if target_lang_code == 'auto':
            resolved = resolve_auto_language(self.env.user.lang)
            if not resolved:
                raise UserError(_(
                    "Your interface language is not in the supported "
                    "translation list. Please pick a target language "
                    "from the menu."
                ))
            target_lang_code = resolved

        if target_lang_code not in LANG_PROMPT_NAME:
            raise UserError(_(
                "Language '%s' is not supported.", target_lang_code
            ))

        # Cache lookup via native mail.message.translation table.
        # Keyed by (message_id, target_lang); the table has a unique
        # index on that pair so search().limit=1 is a point lookup.
        Translation = self.env['mail.message.translation'].sudo()
        cached = Translation.search([
            ('message_id', '=', self.id),
            ('target_lang', '=', target_lang_code),
        ], limit=1)
        if cached:
            return {
                'lang': target_lang_code,
                'text': html2plaintext(cached.body or '').strip(),
                'cached': True,
            }

        # Extract plain text from HTML body.
        plain = html2plaintext(self.body or '').strip()
        if not plain:
            return {'lang': target_lang_code, 'text': '', 'cached': False}

        # Call LLM.
        translated = self._sat_call_llm(plain, target_lang_code)

        # Write into the native cache table. source_lang is required
        # by the native schema; we don't run explicit language detection
        # to save an API call, and store a sentinel value.
        #
        # Use a savepoint so that a unique-constraint violation (race
        # condition: two requests translating the same message to the
        # same language at the same time) rolls back only the INSERT,
        # not the entire transaction. Without the savepoint, catching
        # IntegrityError at the Python level leaves the PostgreSQL
        # transaction in an aborted state, causing the HTTP layer's
        # COMMIT to fail — the RPC would return an error to the
        # frontend even though the translation itself succeeded.
        try:
            with self.env.cr.savepoint():
                Translation.create({
                    'message_id': self.id,
                    'source_lang': 'auto',
                    'target_lang': target_lang_code,
                    'body': translated,
                })
        except IntegrityError as e:
            # Expected race: another request created the same
            # (message_id, target_lang) entry between our cache lookup
            # and this create. The unique index rejects our insert —
            # non-fatal, we still have the translated result to return.
            #
            # We deliberately do NOT catch generic Exception here: disk
            # full, schema mismatch, permission errors are real bugs and
            # should surface, not be swallowed as "cache miss".
            _logger.debug(
                "suite_ai_translate: cache race for message %s -> %s: %s",
                self.id, target_lang_code, e,
            )

        return {
            'lang': target_lang_code,
            'text': translated,
            'cached': False,
        }
