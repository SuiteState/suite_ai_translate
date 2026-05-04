from odoo import api, fields, models


class StockMove(models.Model):
    _inherit = 'stock.move'

    suite_owner_names = fields.Char(
        string='Owner(s)',
        compute='_compute_suite_owner_names',
        search='_search_suite_owner_names',
    )

    @api.depends('move_line_ids.owner_id')
    def _compute_suite_owner_names(self):
        for move in self:
            owners = move.move_line_ids.owner_id
            move.suite_owner_names = ', '.join(owners.mapped('name')) if owners else False

    def _search_suite_owner_names(self, operator, value):
        return [('move_line_ids.owner_id.name', operator, value)]
