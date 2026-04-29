# -*- coding: utf-8 -*-
import logging
import re
from odoo import api, fields, models, _
from odoo.exceptions import ValidationError

_logger = logging.getLogger(__name__)

# Sale order states considered confirmed business for activity tracking.
_CONFIRMED_SO_STATES = ('sale', 'done')

# Default phone min length, used as fallback when config is absent.
_DEFAULT_PHONE_MIN_LENGTH = 8


class ResPartner(models.Model):
    _inherit = 'res.partner'

    company_id = fields.Many2one(
        default=lambda self: self._suite_default_company_id(),
    )

    @api.model
    def _suite_default_company_id(self):
        """Inject self.env.company as the default company_id, except when
        this partner is being auto-created as the companion record of a
        new res.company.

        Why this matters:
            Odoo's res.company.create() automatically creates a partner via
            the partner_id field. That partner.create() runs *before* the
            new company exists in DB, so any default resolving to
            self.env.company picks up the *current active* company, not the
            new one being created. This pollutes the company_id of the new
            company's partner, which then breaks downstream routing
            (warehouses, journals, etc.) until manually corrected.

            We mark the call stack via res.company.create() with a context
            flag and skip default-injection when we see it. Odoo's native
            flow then assigns the correct company_id afterwards.
        """
        if self.env.context.get('suite_creating_company'):
            return False
        return self.env.company

    # ── Phone uniqueness (ORM-level, no DB constraint) ────────

    suite_phone_normalized = fields.Char(
        string='Phone (normalized)',
        readonly=True,
        copy=False,
        index=True,
        help='Digits-only normalized form of the phone number, used for '
             'duplicate detection. Auto-computed on write.',
    )

    # ── Customer activity status ──────────────────────────────

    suite_last_order_date = fields.Date(
        string='Last Order Date',
        readonly=True,
        copy=False,
        groups='suite_contact_guard.group_contact_guard_admin,'
               'base.group_partner_manager',
    )
    suite_days_since_order = fields.Integer(
        string='Days Since Last Order',
        readonly=True,
        copy=False,
        # Disable aggregation: summing "days since last order" across
        # a group has no business meaning — what shows up next to
        # "Active (6)" should be empty, not 70 days. aggregator=False
        # is the Odoo 17+ replacement for the legacy group_operator.
        aggregator=False,
        help='Days since last confirmed sale order. Meaningful only when '
             'suite_has_orders is True; otherwise the value is 0 and should '
             'be treated as "no orders yet" rather than "0 days ago".',
        groups='suite_contact_guard.group_contact_guard_admin,'
               'base.group_partner_manager',
    )
    suite_has_orders = fields.Boolean(
        string='Has Confirmed Orders',
        readonly=True,
        copy=False,
        default=False,
        help='True once the customer has at least one confirmed sale order. '
             'Used to distinguish "0 days since order" from "never ordered" '
             'in views and to drive activity-status display logic.',
        groups='suite_contact_guard.group_contact_guard_admin,'
               'base.group_partner_manager',
    )
    suite_activity_status = fields.Selection(
        selection=[
            ('active', 'Active'),
            ('warning', 'Warning'),
            ('sleeping', 'Sleeping'),
            ('dormant', 'Dormant'),
        ],
        string='Activity Status',
        readonly=True,
        copy=False,
        groups='suite_contact_guard.group_contact_guard_admin,'
               'base.group_partner_manager',
    )

    # ── Role flags for view expressions ───────────────────────

    suite_is_admin = fields.Boolean(
        string='Is Contact Guard Admin',
        compute='_compute_suite_role_flags',
        store=False,
    )
    suite_is_contact_manager = fields.Boolean(
        string='Is Contact Manager',
        compute='_compute_suite_role_flags',
        store=False,
    )
    suite_is_purchase_user = fields.Boolean(
        string='Is Purchase User',
        compute='_compute_suite_role_flags',
        store=False,
    )
    suite_is_my_contact = fields.Boolean(
        string='Is My Contact',
        compute='_compute_suite_is_my_contact',
        store=False,
    )

    @api.depends_context('uid')
    def _compute_suite_role_flags(self):
        user = self.env.user
        is_admin = user.has_group(
            'suite_contact_guard.group_contact_guard_admin'
        )
        is_contact_mgr = user.has_group('base.group_partner_manager')
        is_purchase_user = user.has_group('purchase.group_purchase_user')
        for rec in self:
            rec.suite_is_admin = is_admin
            rec.suite_is_contact_manager = is_contact_mgr
            rec.suite_is_purchase_user = is_purchase_user

    @api.depends('user_id')
    @api.depends_context('uid')
    def _compute_suite_is_my_contact(self):
        uid = self.env.uid
        for rec in self:
            rec.suite_is_my_contact = (rec.user_id.id == uid)

    # ── Phone normalization helpers ───────────────────────────

    @staticmethod
    def _normalize_phone(raw):
        """Strip to digits only; remove leading '00' international prefix.

        Examples:
            '+971 50 123 4567'   -> '971501234567'
            '00 971 50 1234567'  -> '971501234567'
            '971-50-123-4567'    -> '971501234567'
            ''                   -> False
            None                 -> False
        """
        if not raw:
            return False
        digits = re.sub(r'\D', '', raw)
        if digits.startswith('00'):
            digits = digits[2:]
        return digits or False

    def _get_phone_min_length(self, company_id=None):
        """Resolve min length from config, falling back to default.

        If company_id is given, looks up the config for that company,
        which matters when a contact is being created under a company
        different from the current user's active company.
        """
        Config = self.env['suite.contact.guard.config'].sudo()
        if company_id:
            config = Config.search(
                [('company_id', '=', company_id)],
                limit=1,
            )
        else:
            config = Config._get_for_current_company()
        if config and config.suite_phone_min_length > 0:
            return config.suite_phone_min_length
        return _DEFAULT_PHONE_MIN_LENGTH

    def _validate_phone(self, normalized, company_id=None):
        """Raise if normalized phone is shorter than the configured minimum."""
        if not normalized:
            return
        min_len = self._get_phone_min_length(company_id=company_id)
        if len(normalized) < min_len:
            raise ValidationError(_(
                'Phone number must be at least %(min)s digits. Got: %(got)s'
            ) % {'min': min_len, 'got': normalized})

    def _skip_phone_check(self):
        """Return True when duplicate checks should be bypassed.

        Bypass scenarios:
        - env.su: system automation, migration, lead -> contact sync
        - public user: anonymous visitors going through self-signup flows
        - portal user: external customers operating their own data via the
          customer portal (e.g. editing their own profile, adding a delivery
          address). Phone uniqueness is intended to prevent internal
          malicious behaviour and junk data from staff, so external users
          are out of scope.
        - import_file context: bulk CSV/XLSX imports via Odoo Import Wizard
        - suite_skip_phone_check context: explicit opt-out for callers
        """
        if self.env.su:
            return True
        user = self.env.user
        if user._is_public() or user.has_group('base.group_portal'):
            return True
        ctx = self.env.context
        return bool(
            ctx.get('import_file') or ctx.get('suite_skip_phone_check')
        )

    def _check_phone_duplicate(self, normalized, company_id, exclude_ids=None):
        """Raise a friendly error if normalized phone already exists in the
        same company.
        """
        if not normalized:
            return
        domain = [
            ('suite_phone_normalized', '=', normalized),
            ('company_id', '=', company_id),
        ]
        if exclude_ids:
            domain += [('id', 'not in', list(exclude_ids))]
        if self.sudo().search(domain, limit=1):
            raise ValidationError(_(
                'A contact with this phone number already exists: %s'
            ) % normalized)

    # ── CRUD overrides ────────────────────────────────────────

    @api.model_create_multi
    def create(self, vals_list):
        skip = self._skip_phone_check()
        seen = set()
        for vals in vals_list:
            if 'phone' in vals:
                norm = self._normalize_phone(vals.get('phone'))
                if norm and not skip:
                    effective_company_id = (
                        vals.get('company_id') or self.env.company.id
                    )
                    if not effective_company_id:
                        raise ValidationError(_(
                            'A contact must belong to a company before a '
                            'phone number can be set.'
                        ))
                    self._validate_phone(
                        norm, company_id=effective_company_id,
                    )
                    key = (norm, effective_company_id)
                    if key in seen:
                        raise ValidationError(_(
                            'A contact with this phone number already '
                            'exists: %s'
                        ) % norm)
                    self._check_phone_duplicate(
                        norm, company_id=effective_company_id,
                    )
                    seen.add(key)
                # else: norm=False (no phone given) or skip=True (import).
                # Store normalized as-is without validation.
                vals['suite_phone_normalized'] = norm
        return super().create(vals_list)

    def write(self, vals):
        vals = dict(vals)  # avoid mutating caller's dict
        skip = self._skip_phone_check()

        new_company_id = vals.get('company_id')

        if 'phone' in vals:
            norm = self._normalize_phone(vals.get('phone'))
            if norm and not skip:
                # Ensure each record has an effective company before
                # validating and checking duplicates. Group by company
                # so we look up min_length from the right config.
                partners_by_company = {}
                for rec in self:
                    effective_company = new_company_id or rec.company_id.id
                    if not effective_company:
                        raise ValidationError(_(
                            "Contact '%s' must belong to a company before a "
                            "phone number can be set."
                        ) % rec.name)
                    partners_by_company.setdefault(
                        effective_company, []
                    ).append(rec.id)

                # Validate min length using each affected company's config.
                # When records span multiple companies, we validate against
                # all of them; the strictest min_length wins.
                for company_id in partners_by_company:
                    self._validate_phone(norm, company_id=company_id)

                # Check duplicates per company.
                for company_id, ids in partners_by_company.items():
                    self._check_phone_duplicate(
                        norm,
                        company_id=company_id,
                        exclude_ids=ids,
                    )
            # else: phone is being cleared (norm=False), or skip=True
            # (e.g. bulk import). Both are handled silently -- no
            # validation, no duplicate check, just store the normalized
            # value (False or as-is).
            vals['suite_phone_normalized'] = norm

            # Phone edit protection: once filled, only privileged roles
            # may change it. env.su bypasses (system automation, sync, etc.)
            if not self.env.su:
                user = self.env.user
                is_admin = user.has_group(
                    'suite_contact_guard.group_contact_guard_admin'
                )
                is_contact_mgr = user.has_group(
                    'base.group_partner_manager'
                )
                is_purchase_mgr = user.has_group(
                    'purchase.group_purchase_manager'
                )
                for rec in self:
                    if not rec.phone:
                        # First time filling -- allowed for anyone.
                        continue
                    if rec.user_id:
                        # Customer with assigned salesperson:
                        # locked to admin and contact manager.
                        if not is_admin and not is_contact_mgr:
                            raise ValidationError(_(
                                "Phone for '%s' can only be changed by a "
                                "Contact Guard Administrator or Contact "
                                "Manager."
                            ) % rec.name)
                    else:
                        # Contact without salesperson (e.g. vendor):
                        # purchase manager also allowed.
                        if (not is_admin and not is_contact_mgr
                                and not is_purchase_mgr):
                            raise ValidationError(_(
                                "Phone for '%s' can only be changed by a "
                                "Contact Guard Administrator, Contact "
                                "Manager, or Purchase Manager."
                            ) % rec.name)

        elif new_company_id and not skip:
            # company_id changed without phone change:
            # re-check existing phone uniqueness against new company.
            for rec in self.sudo():
                if rec.suite_phone_normalized:
                    self._check_phone_duplicate(
                        rec.suite_phone_normalized,
                        company_id=new_company_id,
                        exclude_ids=[rec.id],
                    )

        # Salesperson protection: only Contact Guard Admin can write user_id.
        # env.su bypasses (e.g. lead -> contact creation carries salesperson).
        if 'user_id' in vals and not self.env.su:
            if not self.env.user.has_group(
                'suite_contact_guard.group_contact_guard_admin'
            ):
                raise ValidationError(_(
                    'Only Contact Guard Administrators can assign or change '
                    'the salesperson on a contact.'
                ))

        return super().write(vals)

    # ── Cron: customer activity status update ─────────────────

    def _cron_update_activity_status(self):
        """Recompute activity status for every customer, per active company."""
        today = fields.Date.context_today(self)
        Config = self.env['suite.contact.guard.config'].sudo()
        BATCH_SIZE = 1000

        active_companies = self.env['res.company'].sudo().search([
            ('active', '=', True),
        ])

        for company in active_companies:
            config = Config.with_company(company)._get_for_current_company()
            if not config or not config.suite_activity_enabled:
                continue

            all_customer_ids = self.sudo().search([
                ('customer_rank', '>', 0),
                ('company_id', '=', company.id),
            ]).ids

            if not all_customer_ids:
                continue

            _logger.info(
                'Contact Guard: Processing %d customers for company %s',
                len(all_customer_ids), company.name,
            )

            warning = config.suite_warning_after_days or 0
            sleeping = config.suite_sleeping_after_days or 0
            dormant = config.suite_dormant_after_days or 0

            for i in range(0, len(all_customer_ids), BATCH_SIZE):
                batch_ids = all_customer_ids[i:i + BATCH_SIZE]
                self._process_activity_batch(
                    batch_ids,
                    company_id=company.id,
                    today=today,
                    warning=warning,
                    sleeping=sleeping,
                    dormant=dormant,
                )

            _logger.info(
                'Contact Guard: Completed company %s', company.name,
            )

    def _process_activity_batch(
        self, batch_ids, company_id, today,
        warning, sleeping, dormant,
    ):
        """Process one batch of customer partners.

        Status mapping (days since last confirmed sale order):
            days < warning_after_days        -> 'active'
            warning_after_days <= days < sleeping_after_days  -> 'warning'
            sleeping_after_days <= days < dormant_after_days  -> 'sleeping'
            days >= dormant_after_days       -> 'dormant'

        Read as: "Warning after 30 days" means the day a partner crosses
        the 30-day mark, they switch from Active to Warning.

        Customers with no confirmed order ever get all activity fields
        cleared (blank status).
        """
        customers = self.sudo().browse(batch_ids)

        self.env.cr.execute(
            'SELECT partner_id, MAX(date_order)::date '
            'FROM sale_order '
            'WHERE partner_id IN %s '
            '  AND company_id = %s '
            '  AND state IN %s '
            'GROUP BY partner_id',
            [tuple(batch_ids), company_id, _CONFIRMED_SO_STATES],
        )
        last_order_map = dict(self.env.cr.fetchall())

        to_clear = []
        by_status = {}

        for partner in customers:
            last_date = last_order_map.get(partner.id)

            if last_date:
                days = (today - last_date).days
                if days < warning:
                    new_status = 'active'
                elif days < sleeping:
                    new_status = 'warning'
                elif days < dormant:
                    new_status = 'sleeping'
                else:
                    new_status = 'dormant'

                if (
                    partner.suite_activity_status != new_status
                    or partner.suite_last_order_date != last_date
                    or partner.suite_days_since_order != days
                    or not partner.suite_has_orders
                ):
                    by_status.setdefault(
                        (new_status, last_date, days), [],
                    ).append(partner.id)
            else:
                # No confirmed order ever: clear all activity fields.
                # has_orders=False is what view logic uses to render the
                # "never ordered" state (blank instead of "0 days").
                if (
                    partner.suite_activity_status
                    or partner.suite_last_order_date
                    or partner.suite_days_since_order
                    or partner.suite_has_orders
                ):
                    to_clear.append(partner.id)

        ctx = {'tracking_disable': True, 'mail_notrack': True}

        if to_clear:
            self.sudo().browse(to_clear).with_context(**ctx).write({
                'suite_last_order_date': False,
                'suite_days_since_order': 0,
                'suite_activity_status': False,
                'suite_has_orders': False,
            })

        for (new_status, last_date, days), ids in by_status.items():
            self.sudo().browse(ids).with_context(**ctx).write({
                'suite_last_order_date': last_date,
                'suite_days_since_order': days,
                'suite_activity_status': new_status,
                'suite_has_orders': True,
            })
