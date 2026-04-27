/** @odoo-module **/

import { Store } from "@mail/core/common/store_service";
import { patch } from "@web/core/utils/patch";

/**
 * Inject sat_original_body / sat_translation_lang into the message
 * post payload when the Composer's ✈ send-translation button has
 * stashed them on thread.satPendingPost.
 *
 * Runs inside the native messagePostMutex, so the stash is consumed
 * atomically — no concurrent send can pick up another send's stash.
 * The fields flow through the backend pipeline:
 *
 *   post_data → _get_allowed_message_params → message_post kwargs
 *             → _get_message_create_valid_field_names → mail.message.create
 *
 * Written in the same transaction as the message body: eliminates the
 * post-send mark_last race that existed in v1.1.0.
 */
patch(Store.prototype, {
    async getMessagePostParams({ thread }) {
        const params = await super.getMessagePostParams(...arguments);
        const pending = thread && thread.satPendingPost;
        if (pending && pending.target_lang) {
            // original_body may legitimately be an empty string (user
            // typed and then cleared the input before translating), so
            // check for key presence rather than truthiness.
            params.post_data.sat_original_body = pending.original_body ?? "";
            params.post_data.sat_translation_lang = pending.target_lang;
            thread.satPendingPost = null;
        }
        return params;
    },
});
