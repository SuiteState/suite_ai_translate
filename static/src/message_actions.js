/** @odoo-module **/

import { registerMessageAction } from "@mail/core/common/message_actions";
import { _t } from "@web/core/l10n/translation";

/**
 * Register an "AI Translate" action in the Message more-actions menu.
 *
 * Named "AI Translate" (not "Translate") to distinguish from Odoo's
 * native Google Translate-based action, which may coexist if the user
 * has configured a Google Translate API key.
 *
 * Our condition mirrors the native `isTranslatable()` exclusion rules
 * (skip empty bodies, notifications, inbox, internal discuss.channel),
 * but intentionally does NOT gate on `hasMessageTranslationFeature`.
 * That flag is tied to Google Translate API key presence and is none
 * of our business — our feature is driven by the AI provider config,
 * which lives in a separate Settings area.
 *
 * WhatsApp messages live on discuss.channel but need to be translatable.
 * We explicitly allow them back in.
 */
registerMessageAction("suite_ai_translate", {
    condition: ({ message, thread }) => {
        if (!message) return false;
        if (message.isEmpty) return false;
        if (message.isBodyEmpty) return false;
        if (message.hasMailNotificationSummary) return false;
        if (message.isNotification) return false;
        if (!message.body) return false;

        // Thread-scope exclusions: skip Inbox only.
        // All discuss.channel types are allowed (channels, DMs, groups,
        // WhatsApp) — the module description advertises translation in
        // all Discuss contexts, so we do not replicate the native
        // Google Translate exclusion which is a policy specific to that
        // feature (key presence check), not a general UI constraint.
        const model = thread?.model;
        if (model === "mail.box") return false;
        return true;
    },
    icon: "fa fa-language",
    name: _t("AI Translate"),
    sequence: 75,
    onSelected: ({ message, owner }) => {
        // owner is the Message component instance; the method is
        // defined in message_patch.js.
        if (owner && typeof owner.satOpenTranslatePanel === "function") {
            owner.satOpenTranslatePanel();
        }
    },
});
