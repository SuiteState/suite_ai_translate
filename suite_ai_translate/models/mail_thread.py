# -*- coding: utf-8 -*-
from odoo import models


class MailThread(models.AbstractModel):
    _inherit = 'mail.thread'

    def _get_allowed_message_params(self):
        """Pass our translation fields through the controller whitelist
        into message_post kwargs.

        The base set is {'email_add_signature', 'message_type',
        'subtype_xmlid'}. We add sat_original_body and
        sat_translation_lang so the Composer's ✈ button can inject them
        into the native send payload and have them written atomically
        inside the same mail.message.create transaction.
        """
        return super()._get_allowed_message_params() | {
            'sat_original_body',
            'sat_translation_lang',
        }

    def _get_message_create_valid_field_names(self):
        """Allow our translation fields to be written during
        mail.message.create inside message_post.

        Without this override the base implementation's
        _raise_for_invalid_parameters() would raise ValueError and
        abort the entire send.
        """
        return super()._get_message_create_valid_field_names() | {
            'sat_original_body',
            'sat_translation_lang',
        }
