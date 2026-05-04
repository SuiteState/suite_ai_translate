{
    'name': 'Consignment Settlement & COGS | Invoice-to-Bill Matching',
    'version': '19.0.1.0.0',
    'category': 'Accounting/Accounting',
    'summary': (
        'Consignment settlement ledger matching customer-invoice outbounds to vendor '
        'bills line by line, with pending / settled status and consignment COGS tracking'
    ),
    'description': """
Consignment Settlement Ledger
=============================

Adds a settlement ledger that tracks each consigned outbound on
a customer invoice and lets accounting match it to the vendor's
eventual settlement bill, line by line.

Background
----------

Odoo's native consignment flow handles inventory valuation
correctly: vendor-owned stock (move lines with an owner_id)
contributes zero value at invoice posting, so the customer
invoice's COGS reflects the own-stock portion only. The vendor
side is recognised separately when the settlement bill is
posted through the standard vendor bill flow.

What this module adds is the missing matching surface between
those two events. Without it, accounting has to manually cross
reference each consigned customer outbound with the relevant
vendor bill line; with it, every consigned outbound becomes a
ledger row that can be assigned to a vendor bill, with status
tracked automatically.

What this module does
---------------------

When a customer invoice is posted:

- For every invoice line that ships consigned stock, the module
  creates one Consignment Settlement Line per (line x consigning
  vendor), with the outbound quantity in the invoice line's UoM.
- A notebook tab on the customer invoice form lists those
  settlement lines for quick inspection.

When a customer credit note is posted:

- The module mirrors the original invoice's settlement ledger
  rows with proportional negative quantities, so the matching
  surface stays consistent on partial returns. (Return stock
  pickings are not consulted -- consigning owner_id is not
  reliably preserved on return move lines.)

When the vendor settlement bill arrives:

- Accounting opens the relevant ledger rows (filterable by
  vendor / pending / date), assigns the Vendor Bill field on
  each row, and verifies the auto-filled product cost.
- Each settled row turns green; the customer invoice's
  Consignment Pending flag clears once all of its lines have
  been matched to a posted bill.

Activates automatically on installation. Dormant for invoices
that contain no consigned stock.
""",
    'author': 'SuiteState',
    'website': 'https://suitestate.com',
    'license': 'LGPL-3',
    'depends': [
        'mail',
        'stock_account',
        'sale_stock',
    ],
    'data': [
        'security/ir.model.access.csv',
        'data/ir_sequence.xml',
        'views/consignment_cogs_line_views.xml',
        'views/account_move_views.xml',
        'views/menu.xml',
    ],
    'images': [
        'static/description/suite_consignment_cogs_screenshot.png',
        'static/description/suite_consignment_settlement.png',
    ],
    'installable': True,
    'application': False,
    'auto_install': False,
}
