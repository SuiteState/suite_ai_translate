# -*- coding: utf-8 -*-
{
    'name': 'Discuss AI Translate',
    'version': '19.0.1.1.0',
    'category': 'Productivity/Discuss',
    'summary': 'AI-powered translation for Discuss, chatter, and WhatsApp messages.',
    'description': """
Discuss AI Translate
====================

AI-powered translation for Odoo Discuss channels, WhatsApp conversations,
direct messages, and record chatters. Powered by Odoo's native AI framework
(OpenAI / Google Gemini) — reuses the API key you already configured in
Odoo's AI settings, no separate SaaS account required.

Features
--------
* **Translate incoming messages on demand** — click "AI Translate" in any
  message's three-dot menu to see the translation inline, with a 100+
  language picker.
* **Translate outgoing messages before sending** — compose in your own
  language, preview the translation, send the translated version with
  one click. The original text is archived on the message for internal
  "View original" access.
* **Works everywhere Discuss works** — internal channels, WhatsApp,
  direct messages, record chatter (CRM, Sales, Helpdesk, any
  mail.thread).
* **Automatic provider failover** — configure primary + failover models
  (e.g. OpenAI + Gemini). If the primary provider fails, translation
  retries on the failover automatically.
* **Translation caching** — results cached per message + target language
  in Odoo's native translation table. Re-opening a translated message
  is instant and costs no API credits.
* **Right-to-left language support** — Arabic, Persian, Urdu, Hebrew,
  Pashto, Kurdish, Yiddish render correctly in the translation UI.

Data Transmission & Privacy
---------------------------
This module transmits message text to a third-party AI provider (OpenAI
or Google Gemini, as configured) over HTTPS for the sole purpose of
translation. No author names, attachments, record context, or metadata
are transmitted. The feature is **DISABLED BY DEFAULT** and must be
explicitly enabled by an administrator in Settings → General Settings →
AI → Discuss AI Translate. Review the provider's terms and your
organization's data policies before enabling.

Requirements
------------
* Odoo 19 Enterprise (depends on ``ai`` and ``ai_app`` modules).
* An OpenAI and/or Google Gemini API key configured in
  Settings → General Settings → AI.
* Network egress from the Odoo server to ``api.openai.com`` and/or
  ``generativelanguage.googleapis.com``.

Note on WhatsApp
----------------
This module does NOT integrate with the WhatsApp Business API itself.
It simply adds translation capability to WhatsApp conversations
ALREADY handled by Odoo's native ``whatsapp`` module. To use
translation on WhatsApp messages, you must have Odoo's ``whatsapp``
module installed and configured with a valid Meta WhatsApp Business
Account (separate subscription and setup, managed entirely by Odoo's
native module, not by us). If you don't use WhatsApp, all other
Discuss features work without it.

Supported Languages
-------------------
Over 100 languages including English, Arabic, Chinese (Simplified &
Traditional), Spanish, Hindi, Portuguese, Bengali, Russian, Japanese,
German, French, Urdu, Indonesian, Italian, Turkish, Korean, Vietnamese,
Persian, Polish, Thai, Dutch, Ukrainian, Hebrew, Swahili, and many more.
    """,
    'author': 'SuiteState',
    'maintainer': 'ElectroState FZCO',
    'website': 'https://suitestate.com',
    'license': 'LGPL-3',
    'depends': [
        'mail',
        'ai',
        'ai_app',
    ],
    'data': [
        'views/res_config_settings_views.xml',
    ],
    'assets': {
        # Discuss UI lives in web.assets_backend. We do NOT load into
        # mail.assets_public: our RPC endpoints are auth='user', so
        # portal/livechat (public) users cannot use translation — loading
        # the JS there would only waste bandwidth.
        'web.assets_backend': [
            'suite_ai_translate/static/src/**/*',
        ],
    },
    'images': [
        'static/description/icon.png',
    ],
    'installable': True,
    'application': False,
    'auto_install': False,
}
