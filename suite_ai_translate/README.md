# Discuss AI Translate

AI translation for incoming and outgoing messages in Odoo Discuss,
WhatsApp, and chatter.

Translation operates in two directions:

- **Incoming** — translate received messages on demand for reading.
- **Outgoing** — translate composer drafts before sending; the original
  draft text is archived on the sent message.

Translation is performed by the AI provider configured in Odoo's native
`ai` module (OpenAI or Google Gemini). The module does not require its
own API key or SaaS account.

---

## Functionality

- **Outgoing message translation.**
  Type a draft in the composer in any source language, click *AI Translate*
  above the composer, then send the translated version. The original
  draft text is archived on the sent message and accessible via *View
  original*.

- **Incoming message translation.**
  Open a message's three-dot menu and select *AI Translate*. The
  translated text appears inline below the original, with a language
  picker supporting over 100 languages. The last-used target language is
  remembered per user.

- **Chat surface coverage.**
  Discuss channels and direct messages, floating chat windows, WhatsApp
  conversations, the email composer, record chatter on any
  `mail.thread` model (CRM, Sales, Helpdesk, etc.), and the live chat
  agent view.

- **Provider failover.**
  A primary model and a failover model can be configured. If the primary
  provider call fails (network error, rate limit, invalid key), the
  request is retried on the failover model.

- **Translation caching.**
  Translation results are cached per message and target language in
  Odoo's native `mail.message.translation` table. Cache entries vacuum
  automatically after 2 weeks of non-access.

- **Privacy by design.**
  Only the text being translated and the target language code are
  transmitted. No author/recipient names, attachments, or record context.
  Disabled by default; an administrator must explicitly enable the
  feature.

---

## Scope

### Supported

- Discuss channels and direct messages
- Floating chat windows (right-bottom popups from the messaging menu)
- WhatsApp conversations (when Odoo's native `whatsapp` module is set up)
- Email composer (`mail.compose.message`)
- Chatter on any business record (CRM, Sales, Helpdesk, Tasks, any model with `mail.thread`)
- Live chat conversations — agent side, accessed via the Discuss channel view

### Not in scope

- **Live chat frontend popup (visitor side).** The visitor-facing popup widget uses a separate composer component. Agents handle the conversation from the Discuss backend view, where translation works fully.
- **Knowledge module articles.** The Knowledge module uses a different content structure than `mail.thread` and is not covered.
- **System UI labels** (menus, buttons, field names). Odoo's built-in i18n translation system handles these.

---

## AI provider extensibility

The default build supports the AI providers integrated in Odoo's native
`ai` module: OpenAI and Google Gemini. The module's provider layer can
be extended to other AI providers — for example, when the default
providers are not reachable from a given region, when a
domain-specialized model is preferred for a specific language pair, or
when a different provider is required for organizational reasons.

For inquiries about extending to a different AI provider, contact
<Hello@suitestate.com>.

---

## Supported Languages

Over 100 languages, including English, Arabic, Chinese (Simplified and
Traditional), Spanish, Hindi, Portuguese, Bengali, Russian, Japanese,
German, French, Urdu, Indonesian, Italian, Turkish, Korean, Vietnamese,
Persian, Polish, Thai, Dutch, Ukrainian, Hebrew, Swahili, and others.
Translation quality for a given language pair depends on the AI provider.

Right-to-left languages (Arabic, Persian, Urdu, Hebrew, Pashto, Kurdish,
Yiddish) render with `dir="rtl"` in the translation preview.

---

## Requirements

- Odoo 19 Enterprise
- The native `ai` and `ai_app` modules (shipped with Enterprise)
- An API key from OpenAI or Google Gemini configured in
  *Settings → General Settings → AI*
- Network egress from the Odoo server to `api.openai.com` and/or
  `generativelanguage.googleapis.com`

---

## Configuration

1. Install the module.
2. Go to *Settings → General Settings → AI*, add at least one provider
   API key.
3. In the *Discuss AI Translate* section of the same page, toggle
   **Enable Discuss AI Translate** on, and pick the default translation
   model (defaults to `gpt-5-mini`).
4. Optionally set a **Failover Model** from a different provider.

The *AI Translate* action then appears on every message, and the
composer gets a translate toggle.

### Advanced parameters

Two system parameters are available (*Technical → Parameters → System
Parameters*):

| Parameter                                  | Default | Purpose                                   |
|--------------------------------------------|---------|-------------------------------------------|
| `suite_ai_translate.max_input_chars`        | `8000`  | Per-message length cap before translation |
| `suite_ai_translate.temperature`            | `0.2`   | LLM sampling temperature                  |

---

## Privacy

The feature is disabled by default. Once enabled, the module transmits
only:

- The plain-text body of the message or composer draft selected for translation
- The target language code

What is not sent: author/recipient names, partner records, email
addresses, phone numbers, attachments, images, files, database records,
CRM context, sales data, invoice data, or analytics/telemetry.

Translated results are cached locally in the Odoo database
(`mail.message.translation`) and auto-vacuum after 2 weeks.

---

## License

LGPL-3.0-or-later. See the `LICENSE` file for the full license text.

## Author

**SuiteState** — Odoo modules and consultancy, Dubai.
Maintained by ElectroState FZCO. Website: <https://suitestate.com>
