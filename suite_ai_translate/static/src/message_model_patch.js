/** @odoo-module **/

import { Message } from "@mail/core/common/message_model";
import { patch } from "@web/core/utils/patch";

/**
 * Declare backend-exposed custom fields on the frontend Message model
 * so OWL's reactivity system tracks them.
 *
 * Translation caching is backed by the native mail.message.translation
 * table (not a field on mail.message), so no cache field is declared
 * here.
 */
patch(Message.prototype, {
    /**
     * @type {string|undefined} Pre-translation original body text,
     * written atomically inside mail.message.create via the native
     * post_data pipeline when the Composer's ✈ translation-send button
     * is clicked.
     */
    sat_original_body: undefined,

    /**
     * @type {string|undefined} Target language code of the composer
     * translation that was applied (e.g. 'en', 'ar').
     */
    sat_translation_lang: undefined,
});
