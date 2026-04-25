/** @odoo-module **/

/**
 * Frontend mirror of models/languages.py.
 *
 * Keep this list in sync with the Python SUPPORTED_LANGUAGES tuple.
 * The actual translation is performed by the LLM (OpenAI / Gemini) so
 * there is no runtime cost to supporting a large number of languages —
 * this is effectively a UI picker list.
 *
 * 'auto' is a frontend-only value: when picked for translating an
 * incoming message it resolves to the user's interface language on the
 * server side. It is NOT offered for outgoing composer translation —
 * the sender must explicitly pick the target language.
 */
export const SUPPORTED_LANGUAGES = [
    { code: "auto",  en: "Auto Detect",              native: "Auto" },

    // ---- Major world business languages ----------------------------
    { code: "en",    en: "English",                  native: "English" },
    { code: "zh_CN", en: "Chinese (Simplified)",     native: "中文（简体）" },
    { code: "zh_TW", en: "Chinese (Traditional)",    native: "中文（繁體）" },
    { code: "es",    en: "Spanish",                  native: "Español" },
    { code: "ar",    en: "Arabic",                   native: "العربية" },
    { code: "hi",    en: "Hindi",                    native: "हिन्दी" },
    { code: "pt",    en: "Portuguese",               native: "Português" },
    { code: "bn",    en: "Bengali",                  native: "বাংলা" },
    { code: "ru",    en: "Russian",                  native: "Русский" },
    { code: "ja",    en: "Japanese",                 native: "日本語" },
    { code: "de",    en: "German",                   native: "Deutsch" },
    { code: "fr",    en: "French",                   native: "Français" },
    { code: "ur",    en: "Urdu",                     native: "اردو" },
    { code: "id",    en: "Indonesian",               native: "Bahasa Indonesia" },
    { code: "it",    en: "Italian",                  native: "Italiano" },
    { code: "tr",    en: "Turkish",                  native: "Türkçe" },
    { code: "ko",    en: "Korean",                   native: "한국어" },
    { code: "vi",    en: "Vietnamese",               native: "Tiếng Việt" },
    { code: "fa",    en: "Persian",                  native: "فارسی" },
    { code: "pl",    en: "Polish",                   native: "Polski" },
    { code: "th",    en: "Thai",                     native: "ไทย" },
    { code: "nl",    en: "Dutch",                    native: "Nederlands" },

    // ---- Europe ----------------------------------------------------
    { code: "uk",    en: "Ukrainian",                native: "Українська" },
    { code: "ro",    en: "Romanian",                 native: "Română" },
    { code: "el",    en: "Greek",                    native: "Ελληνικά" },
    { code: "cs",    en: "Czech",                    native: "Čeština" },
    { code: "hu",    en: "Hungarian",                native: "Magyar" },
    { code: "sv",    en: "Swedish",                  native: "Svenska" },
    { code: "bg",    en: "Bulgarian",                native: "Български" },
    { code: "da",    en: "Danish",                   native: "Dansk" },
    { code: "fi",    en: "Finnish",                  native: "Suomi" },
    { code: "sk",    en: "Slovak",                   native: "Slovenčina" },
    { code: "no",    en: "Norwegian",                native: "Norsk" },
    { code: "hr",    en: "Croatian",                 native: "Hrvatski" },
    { code: "sr",    en: "Serbian",                  native: "Српски" },
    { code: "sl",    en: "Slovenian",                native: "Slovenščina" },
    { code: "lt",    en: "Lithuanian",               native: "Lietuvių" },
    { code: "lv",    en: "Latvian",                  native: "Latviešu" },
    { code: "et",    en: "Estonian",                 native: "Eesti" },
    { code: "bs",    en: "Bosnian",                  native: "Bosanski" },
    { code: "mk",    en: "Macedonian",               native: "Македонски" },
    { code: "sq",    en: "Albanian",                 native: "Shqip" },
    { code: "ca",    en: "Catalan",                  native: "Català" },
    { code: "eu",    en: "Basque",                   native: "Euskara" },
    { code: "gl",    en: "Galician",                 native: "Galego" },
    { code: "is",    en: "Icelandic",                native: "Íslenska" },
    { code: "ga",    en: "Irish",                    native: "Gaeilge" },
    { code: "cy",    en: "Welsh",                    native: "Cymraeg" },
    { code: "mt",    en: "Maltese",                  native: "Malti" },
    { code: "be",    en: "Belarusian",               native: "Беларуская" },
    { code: "lb",    en: "Luxembourgish",            native: "Lëtzebuergesch" },

    // ---- Middle East / South Asia ----------------------------------
    { code: "he",    en: "Hebrew",                   native: "עברית" },
    { code: "ps",    en: "Pashto",                   native: "پښتو" },
    { code: "ku",    en: "Kurdish",                  native: "Kurdî" },
    { code: "az",    en: "Azerbaijani",              native: "Azərbaycanca" },
    { code: "hy",    en: "Armenian",                 native: "Հայերեն" },
    { code: "ka",    en: "Georgian",                 native: "ქართული" },
    { code: "pa",    en: "Punjabi",                  native: "ਪੰਜਾਬੀ" },
    { code: "gu",    en: "Gujarati",                 native: "ગુજરાતી" },
    { code: "mr",    en: "Marathi",                  native: "मराठी" },
    { code: "ta",    en: "Tamil",                    native: "தமிழ்" },
    { code: "te",    en: "Telugu",                   native: "తెలుగు" },
    { code: "kn",    en: "Kannada",                  native: "ಕನ್ನಡ" },
    { code: "ml",    en: "Malayalam",                native: "മലയാളം" },
    { code: "si",    en: "Sinhala",                  native: "සිංහල" },
    { code: "ne",    en: "Nepali",                   native: "नेपाली" },
    { code: "or",    en: "Odia",                     native: "ଓଡ଼ିଆ" },
    { code: "as",    en: "Assamese",                 native: "অসমীয়া" },

    // ---- Southeast Asia --------------------------------------------
    { code: "ms",    en: "Malay",                    native: "Bahasa Melayu" },
    { code: "tl",    en: "Tagalog (Filipino)",       native: "Tagalog" },
    { code: "my",    en: "Burmese",                  native: "မြန်မာ" },
    { code: "km",    en: "Khmer",                    native: "ខ្មែរ" },
    { code: "lo",    en: "Lao",                      native: "ລາວ" },
    { code: "jv",    en: "Javanese",                 native: "Basa Jawa" },
    { code: "su",    en: "Sundanese",                native: "Basa Sunda" },

    // ---- Africa ----------------------------------------------------
    { code: "sw",    en: "Swahili",                  native: "Kiswahili" },
    { code: "am",    en: "Amharic",                  native: "አማርኛ" },
    { code: "ha",    en: "Hausa",                    native: "Hausa" },
    { code: "yo",    en: "Yoruba",                   native: "Yorùbá" },
    { code: "ig",    en: "Igbo",                     native: "Igbo" },
    { code: "zu",    en: "Zulu",                     native: "isiZulu" },
    { code: "xh",    en: "Xhosa",                    native: "isiXhosa" },
    { code: "af",    en: "Afrikaans",                native: "Afrikaans" },
    { code: "so",    en: "Somali",                   native: "Soomaali" },
    { code: "rw",    en: "Kinyarwanda",              native: "Kinyarwanda" },
    { code: "sn",    en: "Shona",                    native: "chiShona" },
    { code: "mg",    en: "Malagasy",                 native: "Malagasy" },

    // ---- Central Asia / Mongolic -----------------------------------
    { code: "kk",    en: "Kazakh",                   native: "Қазақ тілі" },
    { code: "ky",    en: "Kyrgyz",                   native: "Кыргызча" },
    { code: "uz",    en: "Uzbek",                    native: "Oʻzbekcha" },
    { code: "tg",    en: "Tajik",                    native: "Тоҷикӣ" },
    { code: "tk",    en: "Turkmen",                  native: "Türkmençe" },
    { code: "mn",    en: "Mongolian",                native: "Монгол" },

    // ---- Americas --------------------------------------------------
    { code: "ht",    en: "Haitian Creole",           native: "Kreyòl Ayisyen" },
    { code: "qu",    en: "Quechua",                  native: "Runa Simi" },
    { code: "gn",    en: "Guarani",                  native: "Avañe'ẽ" },

    // ---- Other -----------------------------------------------------
    { code: "eo",    en: "Esperanto",                native: "Esperanto" },
    { code: "la",    en: "Latin",                    native: "Latina" },
    { code: "yi",    en: "Yiddish",                  native: "ייִדיש" },
    { code: "fy",    en: "Frisian",                  native: "Frysk" },
    { code: "gd",    en: "Scots Gaelic",             native: "Gàidhlig" },
    { code: "haw",   en: "Hawaiian",                 native: "ʻŌlelo Hawaiʻi" },
    { code: "mi",    en: "Maori",                    native: "Māori" },
    { code: "sm",    en: "Samoan",                   native: "Gagana Sāmoa" },
    { code: "co",    en: "Corsican",                 native: "Corsu" },
    { code: "ny",    en: "Chichewa",                 native: "Chichewa" },
    { code: "st",    en: "Sesotho",                  native: "Sesotho" },
];

// Languages available for OUTGOING composer translation (no 'auto').
export const COMPOSER_LANGUAGES = SUPPORTED_LANGUAGES.filter(
    (l) => l.code !== "auto"
);

// RTL languages — used to apply dir="rtl" on translation preview/display.
export const RTL_LANGUAGES = new Set([
    "ar", "fa", "ur", "he", "ps", "ku", "yi",
]);

/**
 * Return a human-readable label for a language code.
 * Format: "English / العربية" (English name / native name).
 * When english name == native name (e.g. English, Esperanto), collapse.
 */
export function formatLanguageLabel(code) {
    const lang = SUPPORTED_LANGUAGES.find((l) => l.code === code);
    if (!lang) {
        return code;
    }
    if (lang.code === "auto" || lang.en === lang.native) {
        return lang.en;
    }
    return `${lang.en} / ${lang.native}`;
}

/**
 * Return the short ISO-style tag for compact dropdown togglers.
 * Two-letter uppercase code, with a few common exceptions:
 *   - zh_CN → CN, zh_TW → TW (country-code convention users recognize)
 *   - auto  → Auto
 * Unknown codes fall back to the first segment uppercased.
 */
export function shortLanguageTag(code) {
    const overrides = {
        auto: "Auto",
        zh_CN: "CN",
        zh_TW: "TW",
    };
    if (code in overrides) {
        return overrides[code];
    }
    if (!code) {
        return "";
    }
    // Strip region suffix if any (shouldn't happen given our data but
    // defensive) and uppercase.
    return code.split("_")[0].toUpperCase();
}

/**
 * Build a combined searchable label for SelectMenu.
 * SelectMenu's fuzzyLookup only searches by `choice.label`, so we
 * pack english name + native name + ISO code all into one string.
 * User typing "Jap" / "日本" / "ja" all hit Japanese.
 *
 * Display format chosen to be readable when shown in the dropdown:
 *   "Japanese — 日本語 (ja)"
 * For same-name languages (English / Esperanto), collapse:
 *   "English (en)"
 */
export function searchableLabel(code) {
    const lang = SUPPORTED_LANGUAGES.find((l) => l.code === code);
    if (!lang) {
        return code;
    }
    if (lang.code === "auto") {
        return lang.en;
    }
    if (lang.en === lang.native) {
        return `${lang.en} (${lang.code})`;
    }
    return `${lang.en} — ${lang.native} (${lang.code})`;
}

export function isRtlLanguage(code) {
    return RTL_LANGUAGES.has(code);
}

/**
 * Build a list of SelectMenu `choices` entries for the full language
 * list (used both by composer and incoming panel — just filter 'auto'
 * out for composer).
 */
export function buildLanguageChoices({ includeAuto = false } = {}) {
    return SUPPORTED_LANGUAGES
        .filter((l) => includeAuto || l.code !== "auto")
        .map((l) => ({
            value: l.code,
            label: searchableLabel(l.code),
        }));
}
