{
    'name': 'Landed Cost Access for Accountants | Inventory Access Bridge',
    'version': '19.0.1.0.0',
    'category': 'Inventory/Inventory',
    'summary': (
        'Companion to Inventory Access Control: adds landed cost RWCD access '
        'and Accounting menu for the Stock History group. Requires suite_inventory_access.'
    ),
    'description': """
Inventory Access — Landed Cost Bridge
=====================================

Auto-installs when both suite_inventory_access and stock_landed_costs
are present. Grants the Accounting Stock History group full RWCD
access to Landed Cost records and adds a Landed Costs menu under
Accounting -> Operations so accountants can perform landed cost
adjustments without needing Inventory user rights.

Multi-company aware. No effect when stock_landed_costs is not
installed (this module is then not installed either).
""",
    'author': 'SuiteState',
    'website': 'https://suitestate.com',
    'license': 'LGPL-3',
    'depends': [
        'suite_inventory_access',
        'stock_landed_costs',
    ],
    'data': [
        'security/ir.model.access.csv',
        'views/landed_cost_views.xml',
    ],
    'images': [
        'static/description/suite_inventory_access_landed_cost_screenshort.png',
        'static/description/screenshort_landed_cost.png',
        'static/description/screenshort_mixed_invoice.png',
        'static/description/screenshort_consignment.png',
        'static/description/screenshort_setting.png',
    ],
    'installable': True,
    'application': False,
    'auto_install': True,
}
