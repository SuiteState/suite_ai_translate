# -*- coding: utf-8 -*-
"""Supported language list for Discuss AI Translate.

Covers ~100 languages, aligned with Google Translate's supported set
and the capabilities of modern LLMs (OpenAI / Gemini). Since the
actual translation is performed by the LLM, this list is effectively
a UI picker — adding languages here has zero runtime cost on the
translation pipeline itself.

Language codes follow Odoo's convention (underscore, e.g. `zh_CN`)
not BCP-47 (`zh-CN`). This keeps the frontend/backend consistent
with Odoo's `res.lang` coding scheme.

If you add a language, update both:
  1. SUPPORTED_LANGUAGES here
  2. static/src/languages.js (frontend mirror)

LANG_PROMPT_NAME is derived automatically from SUPPORTED_LANGUAGES —
no need to maintain two parallel tables.
"""

# (code, english_name, native_name)
# 'auto' is a special frontend-only value meaning
# "translate into the current user's interface language".
SUPPORTED_LANGUAGES = [
    ('auto',  'Auto Detect',              'Auto'),

    # ---- Major world business languages -----------------------------
    ('en',    'English',                  'English'),
    ('zh_CN', 'Chinese (Simplified)',     '中文（简体）'),
    ('zh_TW', 'Chinese (Traditional)',    '中文（繁體）'),
    ('es',    'Spanish',                  'Español'),
    ('ar',    'Arabic',                   'العربية'),
    ('hi',    'Hindi',                    'हिन्दी'),
    ('pt',    'Portuguese',               'Português'),
    ('bn',    'Bengali',                  'বাংলা'),
    ('ru',    'Russian',                  'Русский'),
    ('ja',    'Japanese',                 '日本語'),
    ('de',    'German',                   'Deutsch'),
    ('fr',    'French',                   'Français'),
    ('ur',    'Urdu',                     'اردو'),
    ('id',    'Indonesian',               'Bahasa Indonesia'),
    ('it',    'Italian',                  'Italiano'),
    ('tr',    'Turkish',                  'Türkçe'),
    ('ko',    'Korean',                   '한국어'),
    ('vi',    'Vietnamese',               'Tiếng Việt'),
    ('fa',    'Persian',                  'فارسی'),
    ('pl',    'Polish',                   'Polski'),
    ('th',    'Thai',                     'ไทย'),
    ('nl',    'Dutch',                    'Nederlands'),

    # ---- Europe -----------------------------------------------------
    ('uk',    'Ukrainian',                'Українська'),
    ('ro',    'Romanian',                 'Română'),
    ('el',    'Greek',                    'Ελληνικά'),
    ('cs',    'Czech',                    'Čeština'),
    ('hu',    'Hungarian',                'Magyar'),
    ('sv',    'Swedish',                  'Svenska'),
    ('bg',    'Bulgarian',                'Български'),
    ('da',    'Danish',                   'Dansk'),
    ('fi',    'Finnish',                  'Suomi'),
    ('sk',    'Slovak',                   'Slovenčina'),
    ('no',    'Norwegian',                'Norsk'),
    ('hr',    'Croatian',                 'Hrvatski'),
    ('sr',    'Serbian',                  'Српски'),
    ('sl',    'Slovenian',                'Slovenščina'),
    ('lt',    'Lithuanian',               'Lietuvių'),
    ('lv',    'Latvian',                  'Latviešu'),
    ('et',    'Estonian',                 'Eesti'),
    ('bs',    'Bosnian',                  'Bosanski'),
    ('mk',    'Macedonian',               'Македонски'),
    ('sq',    'Albanian',                 'Shqip'),
    ('ca',    'Catalan',                  'Català'),
    ('eu',    'Basque',                   'Euskara'),
    ('gl',    'Galician',                 'Galego'),
    ('is',    'Icelandic',                'Íslenska'),
    ('ga',    'Irish',                    'Gaeilge'),
    ('cy',    'Welsh',                    'Cymraeg'),
    ('mt',    'Maltese',                  'Malti'),
    ('be',    'Belarusian',               'Беларуская'),
    ('lb',    'Luxembourgish',            'Lëtzebuergesch'),

    # ---- Middle East / South Asia -----------------------------------
    ('he',    'Hebrew',                   'עברית'),
    ('ps',    'Pashto',                   'پښتو'),
    ('ku',    'Kurdish',                  'Kurdî'),
    ('az',    'Azerbaijani',              'Azərbaycanca'),
    ('hy',    'Armenian',                 'Հայերեն'),
    ('ka',    'Georgian',                 'ქართული'),
    ('pa',    'Punjabi',                  'ਪੰਜਾਬੀ'),
    ('gu',    'Gujarati',                 'ગુજરાતી'),
    ('mr',    'Marathi',                  'मराठी'),
    ('ta',    'Tamil',                    'தமிழ்'),
    ('te',    'Telugu',                   'తెలుగు'),
    ('kn',    'Kannada',                  'ಕನ್ನಡ'),
    ('ml',    'Malayalam',                'മലയാളം'),
    ('si',    'Sinhala',                  'සිංහල'),
    ('ne',    'Nepali',                   'नेपाली'),
    ('or',    'Odia',                     'ଓଡ଼ିଆ'),
    ('as',    'Assamese',                 'অসমীয়া'),

    # ---- Southeast Asia ---------------------------------------------
    ('ms',    'Malay',                    'Bahasa Melayu'),
    ('tl',    'Tagalog (Filipino)',       'Tagalog'),
    ('my',    'Burmese',                  'မြန်မာ'),
    ('km',    'Khmer',                    'ខ្មែរ'),
    ('lo',    'Lao',                      'ລາວ'),
    ('jv',    'Javanese',                 'Basa Jawa'),
    ('su',    'Sundanese',                'Basa Sunda'),

    # ---- Africa -----------------------------------------------------
    ('sw',    'Swahili',                  'Kiswahili'),
    ('am',    'Amharic',                  'አማርኛ'),
    ('ha',    'Hausa',                    'Hausa'),
    ('yo',    'Yoruba',                   'Yorùbá'),
    ('ig',    'Igbo',                     'Igbo'),
    ('zu',    'Zulu',                     'isiZulu'),
    ('xh',    'Xhosa',                    'isiXhosa'),
    ('af',    'Afrikaans',                'Afrikaans'),
    ('so',    'Somali',                   'Soomaali'),
    ('rw',    'Kinyarwanda',              'Kinyarwanda'),
    ('sn',    'Shona',                    'chiShona'),
    ('mg',    'Malagasy',                 'Malagasy'),

    # ---- Central Asia / Mongolic ------------------------------------
    ('kk',    'Kazakh',                   'Қазақ тілі'),
    ('ky',    'Kyrgyz',                   'Кыргызча'),
    ('uz',    'Uzbek',                    'Oʻzbekcha'),
    ('tg',    'Tajik',                    'Тоҷикӣ'),
    ('tk',    'Turkmen',                  'Türkmençe'),
    ('mn',    'Mongolian',                'Монгол'),

    # ---- Americas ---------------------------------------------------
    ('ht',    'Haitian Creole',           'Kreyòl Ayisyen'),
    ('qu',    'Quechua',                  'Runa Simi'),
    ('gn',    'Guarani',                  'Avañe\'ẽ'),

    # ---- Other ------------------------------------------------------
    ('eo',    'Esperanto',                'Esperanto'),
    ('la',    'Latin',                    'Latina'),
    ('yi',    'Yiddish',                  'ייִדיש'),
    ('fy',    'Frisian',                  'Frysk'),
    ('gd',    'Scots Gaelic',             'Gàidhlig'),
    ('haw',   'Hawaiian',                 'ʻŌlelo Hawaiʻi'),
    ('mi',    'Maori',                    'Māori'),
    ('sm',    'Samoan',                   'Gagana Sāmoa'),
    ('co',    'Corsican',                 'Corsu'),
    ('ny',    'Chichewa',                 'Chichewa'),
    ('st',    'Sesotho',                  'Sesotho'),
]

# Language code -> name used in the LLM prompt.
# English names are used because LLMs recognize them most reliably.
# Auto-derived from SUPPORTED_LANGUAGES (skipping 'auto' entry) — no
# double maintenance.
LANG_PROMPT_NAME = {
    code: english_name
    for code, english_name, _native in SUPPORTED_LANGUAGES
    if code != 'auto'
}

# Defensive limit on single-message length (exception-layer guard,
# not a rate limit). Default value covers ~95% of conversational use
# cases (a normal long email). Admins can raise or lower this without
# a code change via the system parameter
# `suite_ai_translate.max_input_chars` (no UI surfaced — long-tail knob).
DEFAULT_MAX_INPUT_CHARS = 8000


def resolve_auto_language(user_lang):
    """Resolve a user's interface language (e.g. 'en_US', 'zh_CN', 'ar_001')
    to one of our supported language codes.

    Returns the supported code, or None if no match.
    """
    if not user_lang:
        return None
    if user_lang in LANG_PROMPT_NAME:
        return user_lang
    short = user_lang[:2]
    if short in LANG_PROMPT_NAME:
        return short
    return None
