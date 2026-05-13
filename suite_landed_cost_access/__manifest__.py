{
    'name': 'Landed Costs for Accountants',
    'version': '19.0.1.0.0',
    'category': 'Inventory/Inventory',
    'summary': (
        'Let accounting users create and validate landed costs '
        'without Inventory Administrator rights -- landed cost '
        'access control, landed cost for accountants, landed cost '
        'permission, freight cost allocation, accounting landed cost'
    ),
    'description': """
Keywords: landed cost access, landed cost for accountants,
landed cost permission, landed cost without inventory admin,
freight cost allocation, customs duty allocation,
accounting landed cost, landed cost access control,
inventory valuation adjustment, landed cost accounting,
stock landed cost permission, vendor bill landed cost,
bill of lading cost, shipping cost allocation,
import duty allocation, ancillary cost distribution

Landed Costs for Accountants
============================

Native Odoo restricts landed cost management to the Inventory
Administrator role. Accountants who need to allocate freight,
customs, and other ancillary costs into inventory valuation must
be granted full Inventory admin rights -- including Configuration,
Adjustments, and all operational menus.

This module adds a standalone Landed Cost User group that grants
accounting users the ability to create, validate, and manage
landed cost records, without unlocking any Inventory operational
or configuration screens.

The group appears as a checkbox in user settings under the
Accounting section. A dedicated Landed Costs menu is added under
Accounting for quick access.

Pure permission layer. No new models, no business logic changes.
Safe to install and uninstall at any time.
""",
    'author': 'SuiteState',
    'maintainer': 'ElectroState FZCO',
    'website': 'https://suitestate.com',
    'license': 'LGPL-3',
    'depends': [
        'stock_landed_costs',
    ],
    'data': [
        'security/landed_cost_access_groups.xml',
        'security/ir.model.access.csv',
        'views/account_move_views.xml',
        'views/menu.xml',
    ],
    'images': [
        'static/description/suite_landed_cost_access_screenshot.png',
        'static/description/screenshot_bill.png',
        'static/description/screenshot_land_cost.png',
        'static/description/screenshot_setting.png',
    ],
    'installable': True,
    'application': False,
    'auto_install': False,
}
