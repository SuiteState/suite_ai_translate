from odoo import fields, models


class ResUsers(models.Model):
    _inherit = 'res.users'

    suite_accessible_location_ids = fields.Many2many(
        'stock.location',
        'suite_res_users_stock_location_rel',
        'user_id',
        'location_id',
        string='Accessible Locations',
        help=(
            "Restricts the locations this user can see in the Sales Stock "
            "Viewer and Accounting Stock History menus. Leave empty to "
            "grant access to every location reachable by the user's "
            "companies. Selecting a parent location automatically grants "
            "access to all of its child locations."
        ),
    )
