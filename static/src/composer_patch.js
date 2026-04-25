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

// ---------------------------------------------------------------------
// Cross-tab send lock
// ---------------------------------------------------------------------
// The Composer component's `satCompose.sending` flag guards against
// double-clicks WITHIN a single Composer instance. It does not protect
// against the user sending from two browser tabs (or two windows) on
// the same thread nearly simultaneously — each tab has its own Composer
// state. In that case two parallel `get_last_id` calls can snapshot the
// same baseline, two `mark_last` calls then race to stamp the same
// just-posted message, and the ORIGINAL text ends up written to the
// wrong message (silent data misalignment — worse than a visible error).
//
// This lock is a SOFT guard: a per-thread key in `localStorage` (shared
// across tabs of the same origin) stamped with the start time of the
// active send. The key auto-expires after LOCK_TTL_MS so a crashed or
// forcibly-closed tab cannot leave a permanent deadlock. If acquiring
// the lock fails for any reason (disabled localStorage, private-mode
// quota errors), we degrade gracefully to "no lock" — callers are no
// worse off than before this guard existed.
//
// Covers the common "two tabs" case. Does NOT cover cross-device
// concurrency (laptop + phone on the same account firing at the same
// millisecond) — that residual risk is accepted; `baseline_id` in
// mark_last still mitigates it probabilistically.
const LOCK_TTL_MS = 5000;

function _satLockKey(thread) {
    if (!thread || !thread.model || !thread.id) {
        return null;
    }
    return `suite_ai_translate.sending:${thread.model}:${thread.id}`;
}

function _satTryAcquireSendLock(lockKey) {
    if (!lockKey) return true;
    try {
        const raw = window.localStorage.getItem(lockKey);
        const stamp = raw ? parseInt(raw, 10) : 0;
        if (stamp && !Number.isNaN(stamp) &&
            Date.now() - stamp < LOCK_TTL_MS) {
            return false;
        }
        window.localStorage.setItem(lockKey, Date.now().toString());
        return true;
    } catch (e) {
        // localStorage disabled / private mode quota error / etc.
        // Degrade to "no lock" — callers rely on state.sending and
        // baseline_id as additional guards.
        return true;
    }
}

function _satReleaseSendLock(lockKey) {
    if (!lockKey) return;
    try {
        window.localStorage.removeItem(lockKey);
    } catch (e) { /* ignore */ }
}

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
 *   - [✈]  — swaps the translated preview text into the composer
 *             input, calls the native send path, then records the
 *             pre-translation original text internally via
 *             /suite_ai_translate/mark_last so it remains viewable
 *             later ("View original" toggle).
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

    // ---- Send-translation (✈) button: swap-in translation, send, record original -----

    /**
     * Swap the translation into the composer input, fire the native
     * send path, then ping mark_last to stamp the just-posted message
     * with the pre-translation original text for internal archival.
     *
     * If mark_last fails (network hiccup, thread lookup miss), we log
     * a warning but do NOT disrupt the send — the message is already
     * out and the user can move on. The only consequence is a missing
     * "View original" link on that one message.
     */
    async satUse() {
        const state = this.satCompose;
        const preview = (state.preview || "").trim();
        if (!preview || state.sending) return;

        const composer = this.props.composer;
        const thread = composer && composer.thread;
        const originalText = this.satOriginalText;
        const targetLang = state.target;

        // Cross-tab soft lock: refuse to start a new send while another
        // tab / window has one in flight on the same thread. See the
        // block comment at the top of this file for rationale.
        const lockKey = _satLockKey(thread);
        if (!_satTryAcquireSendLock(lockKey)) {
            this.satCompose.error = _t(
                "Another translated message on this conversation is " +
                "still being processed. Please wait a moment and try again."
            );
            return;
        }

        state.sending = true;

        try {
            // 1. Snapshot the thread's current max message.id as a
            //    baseline, BEFORE sending. mark_last will then look
            //    for `id > baseline` — the new message is guaranteed
            //    to satisfy that, while the previous message (the
            //    actual race culprit) will not. Without this guard,
            //    mark_last kept stamping the PREVIOUS message because
            //    the new one hadn't committed yet when it ran, so
            //    each send was offset by one in the "View original"
            //    archive.
            let baselineId = 0;
            if (thread && thread.model && thread.id) {
                try {
                    const res = await rpc(
                        "/suite_ai_translate/get_last_id",
                        {
                            thread_model: thread.model,
                            thread_id: thread.id,
                        }
                    );
                    baselineId = (res && res.id) || 0;
                } catch (e) {
                    // Non-fatal: worst case mark_last falls back to
                    // "latest message by me" semantics (racy but no
                    // worse than the original code).
                    console.warn(
                        "suite_ai_translate: get_last_id failed",
                        e && (e.message || e)
                    );
                }
            }

            // 2. Replace composer input with the translation so that the
            //    native send path posts exactly that text as the body.
            this._satSetComposerText(preview);

            // 3. Call the native send (handles @mentions, attachments,
            //    message_type, subtype, WhatsApp routing, etc.)
            await super.sendMessage();

            // 4. Best-effort: write the original text + target language
            //    onto the message we just posted. Non-fatal on failure.
            if (thread && thread.model && thread.id) {
                try {
                    await rpc("/suite_ai_translate/mark_last", {
                        thread_model: thread.model,
                        thread_id: thread.id,
                        original_body: originalText,
                        target_lang: targetLang,
                        baseline_id: baselineId,
                    });
                } catch (e) {
                    // Log but don't surface — the message has been sent.
                    // The only loss is the "View original" link on it.
                    console.warn(
                        "suite_ai_translate: mark_last failed",
                        e && (e.message || e)
                    );
                }
            }

            // 5. Exit translation mode so the user is back to normal.
            this._satExitTranslateMode();
        } catch (e) {
            // Native send itself failed — leave the composer input as
            // the translated text so the user can retry, and surface
            // the error.
            this.satCompose.error =
                (e && e.data && e.data.message) ||
                (e && e.message) ||
                _t("Failed to send translated message.");
        } finally {
            state.sending = false;
            _satReleaseSendLock(lockKey);
        }
    },

    /** ✕ button: exit translation mode without touching the input. */
    satClose() {
        this._satExitTranslateMode();
    },
});
