/** @odoo-module **/

import { Message } from "@mail/core/common/message";
import { patch } from "@web/core/utils/patch";
import { useState } from "@odoo/owl";
import { rpc } from "@web/core/network/rpc";
import { _t } from "@web/core/l10n/translation";
import { SelectMenu } from "@web/core/select_menu/select_menu";

import {
    SUPPORTED_LANGUAGES,
    formatLanguageLabel,
    shortLanguageTag,
    buildLanguageChoices,
    isRtlLanguage,
} from "./languages";

// Register SelectMenu on the Message component so the inherited
// template can use it. Same pattern Odoo itself uses to expose
// framework components to inherited templates.
Message.components = {
    ...(Message.components || {}),
    SelectMenu,
};

// Globally remember the user's last chosen translation target language.
const LS_LAST_LANG = "suite_ai_translate.lastTargetLang";

/**
 * Extend the Message component with:
 *   1. Inline translation panel (opened via the three-dot "AI Translate"
 *      action). Viewer-local: only visible to the user who clicked.
 *   2. "View original" toggle for outgoing messages that were sent via
 *      the Composer's ✈ translation-send button (have sat_original_body).
 */
patch(Message.prototype, {
    setup() {
        super.setup();

        this.satTranslate = useState({
            open: false,
            loading: false,
            // Default target language: English. Matches composer's
            // default and keeps the UI in a consistent "always has a
            // selected language" state (no empty toggler).
            lang: "en",
            text: "",
            error: null,
        });

        this.satOriginal = useState({
            shown: false,
        });
    },

    // ---- Language choices / helpers ------------------------------------

    get satLanguageChoices() {
        return SUPPORTED_LANGUAGES.filter((l) => l.code !== "auto");
    },

    /**
     * SelectMenu-ready choices for the incoming-panel language picker.
     * Each choice's `label` combines english + native + code so that
     * SelectMenu's fuzzyLookup (which only searches by label) matches
     * all three user inputs.
     */
    get satLanguageSelectChoices() {
        return buildLanguageChoices({ includeAuto: false });
    },

    satLabelFor(code) {
        return formatLanguageLabel(code);
    },

    /** Short ISO tag for the compact dropdown toggler (EN/AR/CN/...) */
    satShortLabel(code) {
        return code ? shortLanguageTag(code) : _t("Lang");
    },

    satIsRtl(code) {
        return isRtlLanguage(code);
    },

    // ---- localStorage helpers ------------------------------------------

    _satReadSavedLang() {
        try {
            const val = window.localStorage.getItem(LS_LAST_LANG);
            if (val && this.satLanguageChoices.some((l) => l.code === val)) {
                return val;
            }
        } catch (e) { /* ignore */ }
        return null;
    },

    _satSaveLang(code) {
        try {
            window.localStorage.setItem(LS_LAST_LANG, code);
        } catch (e) { /* ignore */ }
    },

    // ---- Translation panel lifecycle -----------------------------------

    async satOpenTranslatePanel() {
        if (this.satTranslate.open) {
            this.satTranslate.open = false;
            return;
        }
        this.satTranslate.open = true;
        this.satTranslate.error = null;

        // Prefer last used language from localStorage; else fall back
        // to whatever is currently in satTranslate.lang (default "en").
        // Either way we auto-translate so the user sees a result
        // immediately on opening the panel.
        const savedLang = this._satReadSavedLang();
        const targetLang = savedLang || this.satTranslate.lang;
        if (targetLang) {
            await this.satRunTranslate(targetLang);
        }
    },

    async satSelectLanguage(code) {
        if (!code) return;
        this._satSaveLang(code);
        await this.satRunTranslate(code);
    },

    async satRunTranslate(langCode) {
        // Defensive empty guard: never fire an RPC with a null/empty
        // target — surface the error locally instead. In practice the
        // default value "en" keeps us out of this branch.
        if (!langCode) {
            this.satTranslate.error = _t("No target language selected.");
            this.satTranslate.text = "";
            return;
        }
        this.satTranslate.loading = true;
        this.satTranslate.error = null;
        try {
            const result = await rpc(
                "/web/dataset/call_kw/mail.message/sat_translate_message",
                {
                    model: "mail.message",
                    method: "sat_translate_message",
                    args: [[this.message.id], langCode],
                    kwargs: {},
                }
            );
            this.satTranslate.lang = result.lang;
            this.satTranslate.text = result.text;
        } catch (e) {
            this.satTranslate.error =
                (e && e.data && e.data.message) ||
                (e && e.message) ||
                _t("Translation failed.");
            this.satTranslate.text = "";
        } finally {
            this.satTranslate.loading = false;
        }
    },

    satCloseTranslatePanel() {
        this.satTranslate.open = false;
    },

    // ---- View original ------------------------------------------------

    /** True if this outgoing message has archived original text. */
    get satHasOriginal() {
        return Boolean(this.message && this.message.sat_original_body);
    },

    /**
     * The original body text, coerced to a plain string and stripped
     * of HTML tags and Odoo's Markup "markup," prefix.
     *
     * CRITICAL: we do NOT pass `message.sat_original_body` directly
     * to `t-out`. When Odoo stores the field as a reactive OWL proxy,
     * safeOutput() treats it as a VNode and calls `.mount()` on it,
     * which crashes with:
     *   TypeError: this.child.mount is not a function
     * Returning a guaranteed string here and using `t-esc` in the
     * template sidesteps the safeOutput object branch entirely.
     *
     * The value may arrive as:
     *   - undefined / null  → ''
     *   - plain string      → use as-is
     *   - Markup object     → String(m) returns something like
     *                         'markup,<p>hello</p>' or '<p>hello</p>'
     *   - reactive proxy    → String(p) yields the underlying HTML
     * We normalize all cases by coercing, stripping a leading
     * 'markup,' prefix, and removing HTML tags — the composer stores
     * plain text originally, so any tags are framework-added wrappers
     * (typically <p>...</p>).
     */
    get satOriginalBodyText() {
        const v = this.message && this.message.sat_original_body;
        if (v == null) return "";
        let str = typeof v === "string" ? v : String(v);
        if (str.startsWith("markup,")) {
            str = str.slice("markup,".length);
        }
        // Strip HTML tags — the original is plain text, any tags are
        // framework-added (<p>, <br>, etc.).
        str = str.replace(/<br\s*\/?>/gi, "\n");
        str = str.replace(/<\/p>\s*<p[^>]*>/gi, "\n\n");
        str = str.replace(/<[^>]*>/g, "");
        // Decode a few common HTML entities we might see.
        str = str
            .replace(/&amp;/g, "&")
            .replace(/&lt;/g, "<")
            .replace(/&gt;/g, ">")
            .replace(/&quot;/g, '"')
            .replace(/&#39;/g, "'")
            .replace(/&nbsp;/g, " ");
        return str.trim();
    },

    /** Label like "Chinese (Simplified) / 中文（简体）" for the "sent as" tag. */
    get satOriginalTargetLabel() {
        const code = this.message && this.message.sat_translation_lang;
        if (!code) return "";
        return formatLanguageLabel(code);
    },

    satToggleOriginal() {
        this.satOriginal.shown = !this.satOriginal.shown;
    },
});
