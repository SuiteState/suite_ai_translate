{
    'name': 'Inventory Access Control | Stock Visibility for Sales & Accounting',
    'version': '19.0.1.0.0',
    'category': 'Inventory/Inventory',
    'summary': (
        'Warehouse access control: stock visibility by location for sales reps '
        'and stock-move history for accountants, without full Inventory user rights'
    ),
    'description': """
Inventory Access for Sales and Accounting
=========================================

Native Odoo couples inventory data visibility to the full
Inventory user role. Sales reps cannot check on-hand quantities
without inheriting receipt, transfer, scrap and stocktake rights;
accountants cannot review stock-move history or perform landed
cost adjustments without the same blanket grant.

This module adds two narrow, independent permission groups that
each expose a small read-only data surface plus a dedicated menu,
without unlocking any of Inventory's operational screens.

Sales Stock Viewer
------------------
- Read-only access to stock.quant, stock.location, stock.warehouse
  and stock.lot.
- New "Stock by Location" menu under Sales, listing current
  on-hand quantities grouped by location, with optional owner
  and lot columns that auto-hide when those features are off.
- Optional per-user location restriction via a new "Accessible
  Locations" field on the user form. Empty = see all locations
  the user's company has access to.

Accounting Stock History
------------------------
- Read-only access to stock.move, stock.move.line, stock.location,
  stock.warehouse and stock.lot.
- New "Stock Moves" menu under Accounting -> Reporting, with a
  built-in "Consignment Only" filter (owner-restricted move lines).

The companion module suite_inventory_access_landed_cost auto
installs when stock_landed_costs is present and adds landed cost
RWCD access plus a Landed Costs menu under Accounting for the
Accounting Stock History group.

Multi-company aware. Independent groups. Standard Odoo system
admin exemption.
""",
    'author': 'SuiteState',
    'website': 'https://suitestate.com',
    'license': 'LGPL-3',
    'depends': [
        'stock',
        'sales_team',
        'account',
    ],
    'data': [
        'security/inventory_access_groups.xml',
        'security/ir.model.access.csv',
        'security/inventory_access_rules.xml',
        'views/res_users_views.xml',
        'views/product_views.xml',
        'views/quant_views.xml',
        'views/move_views.xml',
        'views/menu.xml',
    ],
    'images': [
        'static/description/suite_inventory_access_screenshort.png',
        'static/description/screenshort_setting.png',
        'static/description/screenshort_quant.png',
    ],
    'installable': True,
    'application': False,
    'auto_install': False,
}
