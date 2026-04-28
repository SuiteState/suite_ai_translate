# -*- coding: utf-8 -*-
{
    'name': 'Discuss AI Translate',
    'version': '19.0.1.2.3',
    'category': 'Productivity/Discuss',
    'summary': 'AI translation for incoming and outgoing messages in Discuss, WhatsApp, and chatter.',
    'description': """
Discuss AI Translate
====================

AI translation for messages in Odoo Discuss, WhatsApp, email composer, and
record chatter. Translation works in two directions:

- **Incoming**: translate any received message on demand from its three-dot
  menu, with a 100+ language picker.
- **Outgoing**: translate composer drafts before sending. The original draft
  text is archived on the sent message and remains accessible via
  *View original*.

Other capabilities:

- Coverage across Discuss channels, direct messages, floating chat windows,
  WhatsApp conversations, email composer, chatter on any ``mail.thread``
  model, and the live chat agent view.
- Automatic provider failover between a primary and a backup AI model.
- Per-message translation caching in Odoo's native ``mail.message.translation``
  table.
- No author/recipient names, attachments, or record context transmitted to
  the AI provider -- only the text being translated and the target language.

Powered by Odoo 19's native AI framework. Reuses the OpenAI or Google Gemini
API key already configured in Odoo's AI settings.

See the app's listing page for full documentation, screenshots, supported
chat surfaces, privacy details, and configuration options.
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
        # portal/livechat (public) users cannot use translation -- loading
        # the JS there would only waste bandwidth.
        'web.assets_backend': [
            'suite_ai_translate/static/src/**/*',
        ],
    },
    'images': [
        'static/description/suite_ai_translate_screenshot.png',
        'static/description/screenshot_01.png',
        'static/description/screenshot_02.png',
        'static/description/screenshot_03.png',
    ],
    'installable': True,
    'application': False,
    'auto_install': False,
}
