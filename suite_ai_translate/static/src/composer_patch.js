/** @odoo-module **/

import { Composer } from "@mail/core/common/composer";
import { patch } from "@web/core/utils/patch";
import { useState } from "@odoo/owl";
import { rpc } from "@web/core/network/rpc";
import { _t } from "@web/core/l10n/translation";
import { SelectMenu } from "@web/core/select_menu/select_menu";

import {
    COMPOSER_LANGUAGES,
    formatLanguageLabel,
    shortLanguageTag,
    buildLanguageChoices,
    isRtlLanguage,
} from "./languages";

// Register SelectMenu on the Composer component so the inherited
// template can use it.
Composer.components = {
    ...(Composer.components || {}),
    SelectMenu,
};

/**
 * Extend the Composer with a manual translation flow:
 *
 *   [🌐] [lang▾] [🔄 translate]  [preview textarea]  [✈ send]  [✕]
 *   ─────────────────────────────────────────────────────────────
 *   [original input]       ... [emoji][attach]...[native send]
 *
 * Three buttons on the preview row:
 *   - [🔄]  — manually triggers translation of the current composer
 *             input text (populates the preview).
 *   - [✈]  — stashes the original text on thread.satPendingPost, swaps
 *             the translated preview into the composer input, and calls
 *             the native send path. The Store.getMessagePostParams patch
 *             (store_service_patch.js) reads the stash and injects
 *             sat_original_body / sat_translation_lang into post_data,
 *             so they are written atomically inside mail.message.create.
 *   - [✕]  — closes translation mode without touching the input.
 *
 * Why manual (no auto-translate on typing):
 *   Each translation is an LLM API call (OpenAI/Gemini) — slow
 *   (1–5s), costly (token billing), and occasionally times out.
 *   Auto-translating while the user is still typing produced a
 *   poor experience (requests piling up on pauses, errors shown
 *   while user was still thinking). Manual control makes the flow
 *   predictable and cheap.
 *
 * The native send button always sends whatever is currently in the
 * composer input (WYSIWYG). The preview is advisory — users who
 * want the translated body use the ✈ button; users who want the
 * original body use the native send button as usual.
 */
patch(Composer.prototype, {
    setup() {
        super.setup();

        this.satCompose = useState({
            enabled: false,     // translation mode on/off
            target: "en",       // target language code
            preview: "",        // AI translation (editable)
            loading: false,     // translate RPC in flight
            sending: false,     // send-translation (✈) in flight
            error: null,
        });
    },

    // ---- Language choices / helpers ------------------------------------

    get satComposerLanguages() {
        return COMPOSER_LANGUAGES;
    },

    /**
     * SelectMenu-ready choices for the composer language picker.
     * Excludes 'auto' (composer always needs an explicit target).
     */
    get satComposerSelectChoices() {
        return buildLanguageChoices({ includeAuto: false });
    },

    /**
     * Full label used inside the expanded dropdown menu items.
     * (SelectMenu uses choice.label directly — this helper is kept
     * for any template fragments that still reference it.)
     */
    satComposerLabel(code) {
        return formatLanguageLabel(code) || code;
    },

    /** Short ISO tag for the compact dropdown toggler (EN/AR/CN/...) */
    satShortLabel(code) {
        return code ? shortLanguageTag(code) : _t("Lang");
    },

    satIsRtl(code) {
        return isRtlLanguage(code);
    },

    // ---- Draft text accessor -------------------------------------------

    get satOriginalText() {
        const c = this.props.composer;
        if (!c) return "";
        return ((c.composerText ?? c.text ?? "") || "").trim();
    },

    /** Set the composer draft text across all known field aliases. */
    _satSetComposerText(newText) {
        const c = this.props.composer;
        if (!c) return;
        if ("composerText" in c) c.composerText = newText;
        // Do NOT set composerHtml here: setting composerText already triggers
        // composerText.onUpdate → prettifyMessageText → composerHtml (with
        // proper \n → <br/> conversion). Writing composerHtml a second time
        // with the raw plain-text value would overwrite that correctly-
        // formatted HTML and cause multi-line translations to lose their
        // line breaks when sent.
        if ("text" in c) c.text = newText;
    },

    // ---- Mode toggle ---------------------------------------------------

    satToggleTranslateMode() {
        this.satCompose.enabled = !this.satCompose.enabled;
        if (!this.satCompose.enabled) {
            this._satExitTranslateMode();
        }
        // Entering mode: preview stays empty until the user clicks
        // the manual translate button.
    },

    _satExitTranslateMode() {
        this.satCompose.enabled = false;
        this.satCompose.preview = "";
        this.satCompose.error = null;
    },

    /** Target language change from the SelectMenu picker. */
    satSelectTarget(code) {
        if (!code) return;
        this.satCompose.target = code;
        // Keep any existing preview so the user can compare before
        // manually re-translating. Clearing would feel jarring.
    },

    satOnPreviewInput(ev) {
        this.satCompose.preview = ev.target.value;
    },

    // ---- Manual translate (triggered by the 🔄 button) -----------------

    /**
     * User explicitly requests a translation of the current composer
     * input. No debounce, no auto-firing — translation only happens
     * when this is called.
     */
    async satManualTranslate() {
        if (this.satCompose.loading) {
            return; // guard against double-clicks
        }
        await this.satRequestPreview();
    },

    async satRequestPreview() {
        const text = this.satOriginalText;
        if (!text) {
            this.satCompose.preview = "";
            return;
        }
        // Defensive target-lang guard. In practice satCompose.target is
        // always set (initial value "en", required=true in the UI), but
        // keep this check so a future regression doesn't silently fire
        // RPCs with an empty target.
        if (!this.satCompose.target) {
            this.satCompose.error = _t("No target language selected.");
            this.satCompose.preview = "";
            return;
        }
        this.satCompose.loading = true;
        this.satCompose.error = null;
        try {
            const result = await rpc("/suite_ai_translate/compose", {
                text,
                target_lang: this.satCompose.target,
            });
            if (result && result.error) {
                this.satCompose.error = result.error;
                this.satCompose.preview = "";
            } else {
                this.satCompose.preview = (result && result.text) || "";
            }
        } catch (e) {
            this.satCompose.error =
                (e && e.data && e.data.message) ||
                (e && e.message) ||
                _t("Translation failed.");
            this.satCompose.preview = "";
        } finally {
            this.satCompose.loading = false;
        }
    },

    // ---- Send-translation (✈) button ----------------------------------

    /**
     * Stash the pre-translation original text on thread.satPendingPost,
     * swap the translated preview into the composer input, then fire
     * the native send path.
     *
     * The Store.getMessagePostParams patch (store_service_patch.js) reads
     * thread.satPendingPost and injects sat_original_body /
     * sat_translation_lang into post_data, so they are written atomically
     * inside the same mail.message.create transaction as the message body.
     * This eliminates the mark_last post-send race from v1.1.0.
     *
     * On send failure the stash is cleared so a retry doesn't carry
     * stale data. The error is surfaced to the user; the translated text
     * remains in the composer input so they can retry without re-typing.
     */
    async satUse() {
        const state = this.satCompose;
        const preview = (state.preview || "").trim();
        if (!preview || state.sending) return;

        const composer = this.props.composer;
        const thread = composer && composer.thread;
        const originalText = this.satOriginalText;
        const targetLang = state.target;

        state.sending = true;
        try {
            // 1. Stash pre-translation metadata on the thread so
            //    getMessagePostParams (store_service_patch.js) can inject
            //    it into post_data within the same mutex-protected call.
            if (thread) {
                thread.satPendingPost = {
                    original_body: originalText,
                    target_lang: targetLang,
                };
            }

            // 2. Replace composer input with the translation so that the
            //    native send path posts exactly that text as the body.
            this._satSetComposerText(preview);

            // 3. Call the native send (handles @mentions, attachments,
            //    message_type, subtype, WhatsApp routing, etc.)
            await super.sendMessage();

            // 4. Exit translation mode so the user is back to normal.
            this._satExitTranslateMode();
        } catch (e) {
            // Native send failed — clear stash so a retry doesn't carry
            // stale data, then surface the error. The composer input
            // still holds the translated text so the user can retry.
            if (thread) {
                thread.satPendingPost = null;
            }
            this.satCompose.error =
                (e && e.data && e.data.message) ||
                (e && e.message) ||
                _t("Failed to send translated message.");
        } finally {
            state.sending = false;
        }
    },

    /** ✕ button: exit translation mode without touching the input. */
    satClose() {
        this._satExitTranslateMode();
    },
});
