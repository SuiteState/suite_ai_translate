# -*- coding: utf-8 -*-
from odoo import api, models


class ResCompany(models.Model):
    """Mark res.company.create() so that res.partner can detect when a
    partner is being auto-created as the companion of a new company.

    See ResPartner._suite_default_company_id() for the full reasoning.
    Without this flag, the new company's partner gets stamped with the
    *current active* company's id (not the new company's), which silently
    breaks multi-company routing for the freshly created company.

    This is the only side-effect this model adds. It does not modify any
    other res.company behaviour.
    """
    _inherit = 'res.company'

    @api.model_create_multi
    def create(self, vals_list):
        return super(
            ResCompany,
            self.with_context(suite_creating_company=True),
        ).create(vals_list)
