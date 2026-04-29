# -*- coding: utf-8 -*-
from odoo import api, fields, models, _
from odoo.exceptions import ValidationError


class ContactGuardConfig(models.Model):
    """Per-company configuration for Contact Guard.

    Activity status semantics:
        Days since last confirmed sale order:
          - days < warning_after_days        -> active
          - warning_after_days <= days < sleeping_after_days  -> warning
          - sleeping_after_days <= days < dormant_after_days  -> sleeping
          - days >= dormant_after_days       -> dormant

        Read as: "Warning after 30 days" means a customer becomes
        Warning the day they hit the 30-day mark.

        Customers with no confirmed order ever -> blank (no status).
    """
    _name = 'suite.contact.guard.config'
    _description = 'Contact Guard Configuration'
    _rec_name = 'company_id'

    company_id = fields.Many2one(
        'res.company',
        string='Company',
        required=True,
        default=lambda self: self.env.company,
        ondelete='cascade',
    )

    # Phone uniqueness
    suite_phone_min_length = fields.Integer(
        string='Phone Min Length',
        default=8,
        required=True,
        help='Minimum number of digits for a phone number to be valid. '
             'Counted after stripping non-digit characters and the "00" '
             'international prefix. Set lower for short national numbers.',
    )

    # Activity status
    suite_activity_enabled = fields.Boolean(
        string='Track Customer Activity',
        default=False,
        help='When enabled, a daily cron computes activity status for all '
             'customers in this company based on their last confirmed sale.',
    )
    suite_warning_after_days = fields.Integer(
        string='Warning after (days)',
        default=30,
        help='Customer becomes "Warning" once this many days have passed '
             'since their last confirmed sale order.',
    )
    suite_sleeping_after_days = fields.Integer(
        string='Sleeping after (days)',
        default=60,
        help='Customer becomes "Sleeping" once this many days have passed '
             'since their last confirmed sale order.',
    )
    suite_dormant_after_days = fields.Integer(
        string='Dormant after (days)',
        default=90,
        help='Customer becomes "Dormant" once this many days have passed '
             'since their last confirmed sale order.',
    )

    _company_unique = models.Constraint(
        'UNIQUE(company_id)',
        'A Contact Guard configuration already exists for this company.',
    )

    @api.constrains('suite_phone_min_length')
    def _check_phone_min_length(self):
        for rec in self:
            if rec.suite_phone_min_length < 1:
                raise ValidationError(_(
                    'Phone Min Length must be at least 1.'
                ))

    @api.constrains(
        'suite_activity_enabled',
        'suite_warning_after_days',
        'suite_sleeping_after_days',
        'suite_dormant_after_days',
    )
    def _check_activity_thresholds(self):
        for rec in self:
            if not rec.suite_activity_enabled:
                continue
            warn = rec.suite_warning_after_days
            sleep = rec.suite_sleeping_after_days
            dormant = rec.suite_dormant_after_days
            if not (0 < warn < sleep < dormant):
                raise ValidationError(_(
                    'Activity thresholds must be in ascending order, all '
                    'greater than 0:\n'
                    '  Warning after < Sleeping after < Dormant after\n'
                    'Got: warning=%(w)s, sleeping=%(s)s, dormant=%(d)s.'
                ) % {'w': warn, 's': sleep, 'd': dormant})

    @api.model
    def _get_for_current_company(self):
        """Return config for current company, or empty recordset if missing."""
        return self.search(
            [('company_id', '=', self.env.company.id)],
            limit=1,
        )
