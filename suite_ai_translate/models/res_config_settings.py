# -*- coding: utf-8 -*-
from odoo import fields, models


# Supported LLM models for translation, shared by both the primary and
# failover Selection fields below. Maintained in a single list so adding
# a new model (e.g. when Odoo's `ai` module adds Anthropic / Mistral
# support) touches exactly one place. Labels are kept neutral here —
# primary-specific phrasing ("recommended") is moved to field `help`
# text so the same choice list works for both fields.
_MODEL_CHOICES = [
    # OpenAI
    ('gpt-5-mini',       'OpenAI GPT-5 Mini'),
    ('gpt-5',            'OpenAI GPT-5'),
    ('gpt-4.1-mini',     'OpenAI GPT-4.1 Mini'),
    ('gpt-4.1',          'OpenAI GPT-4.1'),
    ('gpt-4o',           'OpenAI GPT-4o'),
    # Google
    ('gemini-2.5-flash', 'Google Gemini 2.5 Flash'),
    ('gemini-2.5-pro',   'Google Gemini 2.5 Pro'),
]

# Single source of truth for default models. ``mail_message.py``
# imports these for its ICP fallback values so the defaults stay
# consistent across the Settings UI and runtime behavior.
DEFAULT_PRIMARY_MODEL = 'gpt-5-mini'
DEFAULT_FAILOVER_MODEL = 'gemini-2.5-flash'


class ResConfigSettings(models.TransientModel):
    _inherit = 'res.config.settings'

    sat_enabled = fields.Boolean(
        string='Enable Discuss AI Translate',
        default=False,
        config_parameter='suite_ai_translate.enabled',
        help="Enable AI-powered translation in Discuss messages. "
             "When enabled, message text selected for translation will be "
             "sent to the configured AI provider (OpenAI or Google Gemini) "
             "over HTTPS. No other data is transmitted. Translation text "
             "is cached locally in Odoo (auto-vacuumed after 2 weeks) to "
             "minimize repeat API calls. You must review your organization's "
             "data handling policies and the providers' terms before enabling.",
    )

    sat_llm_model = fields.Selection(
        selection=_MODEL_CHOICES,
        string='Translation Model',
        default=DEFAULT_PRIMARY_MODEL,
        config_parameter='suite_ai_translate.llm_model',
        help="Primary model used for translating Discuss messages. "
             "GPT-5 Mini (the default) offers the best balance of "
             "quality, speed, and cost for conversational translation. "
             "Switch to a larger model only if you observe quality "
             "issues with specific language pairs.",
    )

    sat_llm_failover_model = fields.Selection(
        selection=_MODEL_CHOICES,
        string='Failover Model',
        default=DEFAULT_FAILOVER_MODEL,
        config_parameter='suite_ai_translate.llm_failover_model',
        help="Model used as automatic fallback when the primary model's "
             "provider fails (network error, rate limit, invalid key). "
             "Pick a model from a DIFFERENT provider than the primary — "
             "failing over to the same provider gives no real resilience. "
             "Only triggered if the other provider has an API key configured.",
    )
