# Discuss AI Translate

**AI-powered message translation for Odoo Discuss, WhatsApp, and chatter.**

Communicate effortlessly across languages — translate incoming messages
on demand, and draft outgoing messages in your own language before they
are sent in the recipient's.

---

## Features

- **Translate incoming messages on demand**
  Open the three-dot menu on any message and pick a target language.
  The translated text appears inline below the bubble. The original
  stays intact — just collapse the panel to hide it.

- **Compose in your language, send in theirs**
  Turn on the translator on the composer, type in Chinese / Arabic /
  any supported language, and see a live English (or any target)
  preview as you type. Click **Use** to send the translated version.
  The "View original" link on the sent message lets you recall what
  you actually wrote.

- **Works everywhere Discuss works**
  Internal channels, WhatsApp conversations, record chatter, direct
  messages, live chat.

- **Native Odoo AI integration**
  Uses Odoo 19's built-in AI framework — no extra services to
  configure. Plug in an **OpenAI** or **Google Gemini** API key and
  you are ready. If both are configured, automatic failover kicks in
  when one provider fails.

- **Cost-aware**
  Translations are cached per message using Odoo's native
  `mail.message.translation` table, so repeated views don't re-hit
  the API.

- **Privacy-aware**
  Nothing leaves your Odoo instance except the text being translated,
  sent directly to the AI provider you configured.

---

## Supported Languages

English · Arabic · Chinese (Simplified) · Spanish · Portuguese · French
· Persian · Russian · Turkish · Swahili · German · Italian · Urdu · Hindi

---

## Requirements

- Odoo 19 Enterprise
- The native `ai` and `ai_app` modules (shipped with Enterprise)
- An API key from **OpenAI** or **Google Gemini** configured in
  *Settings → AI*

---

## Configuration

1. Install the module.
2. Go to **Settings → AI**, add at least one provider API key.
3. In the same settings tab, pick the default translation model
   (defaults to `gpt-5-mini` — fast and economical).

That's it. The *AI Translate* action appears on every message
immediately, and the composer gets a translate toggle.

### Advanced (optional)

Long-tail tuning knobs exposed as System Parameters
(*Technical → Parameters → System Parameters*) — no UI, defaults
cover 99% of use cases:

| Parameter                                  | Default | Purpose                                   |
|--------------------------------------------|---------|-------------------------------------------|
| `suite_ai_translate.max_input_chars`        | `8000`  | Per-message length cap before translation |
| `suite_ai_translate.temperature`            | `0.2`   | LLM sampling temperature                  |

---

## Supported Chat Surfaces

| Surface                | Works? |
|------------------------|--------|
| Discuss internal channels | ✔ |
| WhatsApp conversations    | ✔ |
| Record chatter            | ✔ |
| Direct messages           | ✔ |
| Live chat                 | ✔ |

---

## License

LGPL-3.0-or-later. See the `LICENSE` file for the full license text.

## Author

**SuiteState** — Odoo modules and consultancy, Dubai.
Maintained by ElectroState FZCO. Website: <https://suitestate.com>
