# Consignment Settlement Ledger

A per-line ledger that tracks each consigned outbound on a
customer invoice and lets accounting match it to the vendor's
eventual settlement bill. Runs alongside Odoo's native
consignment flow without modifying inventory valuation or COGS
journal entries.

## Background

Odoo's native consignment flow handles inventory valuation
correctly: vendor-owned stock (move lines with an `owner_id`)
contributes zero to `move.value` at delivery, so a customer
invoice's COGS posting reflects only the own-stock portion. The
consigned cost is recognised separately when the matching vendor
bill is posted through the standard `in_invoice` flow.

What's missing in native is the **matching surface** between
those two events. A finance team has no built-in way to answer
"which of these consigned outbounds has been settled, and against
which vendor bill?" — that linkage exists only as ad-hoc
spreadsheets or memory.

This module fills that gap with a line-level settlement ledger.

## What this module does

**No configuration. No new accounts. Activates on install.**

When a customer invoice is posted, the module:

1. Walks the invoice's underlying outbound stock moves (delivery
   direction only — prior return pickings on the same SO line are
   excluded so quantities do not double-count).
2. For every `(invoice line × consigning owner)` combination,
   creates one row in the **Consignment Settlement** ledger
   (`suite.consignment.cogs.line`) with the outbound quantity in
   the invoice line's UoM.
3. Sets a "Consignment Pending" flag on the invoice and surfaces
   the new rows in a notebook tab on the invoice form.

When the vendor settlement bill arrives, accounting:

1. Opens the relevant ledger rows from **Accounting → Customers
   → Consignment Settlement**, filtered by vendor, by pending
   status, by date range, etc.
2. Sets the **Vendor Bill** field on each row to the bill they
   just created. The unit cost auto-fills from the first matching
   product line on the bill and remains editable.
3. Each settled row turns green; the invoice's "Consignment
   Pending" flag clears once all of its lines have been matched.

When a customer credit note is posted (returns / refunds):

1. The module mirrors the original invoice's ledger rows with
   proportional negative quantities, anchored to the credit note.
2. Reverse rows carry a **Reverses** link back to the originating
   row for traceability.
3. Accounting matches each reverse row to a vendor refund / credit
   note through the same flow.

## Workflow

Standard, with the new ledger inserted as a matching surface:

1. Receive vendor-owned stock with an owner on the receipt move
   (the standard Odoo consignment flow). The owner alone is the
   trigger; PO is optional.
2. Sell mixed (own + consigned) units to a customer. Confirm and
   deliver as normal.
3. Post the customer invoice. Module silently creates ledger rows
   for the consigned portion of each invoice line.
4. Receive the vendor's consignment settlement bill. Create the
   vendor bill in Odoo through the standard `in_invoice` flow.
5. Open the relevant ledger rows, assign the **Vendor Bill** on
   each, verify the auto-filled product cost.
6. Returns: post a customer credit note. Module creates reverse
   ledger rows. Match each to a vendor return credit when it
   arrives.

## Settings

None. The module activates on installation and is silent for
invoices that contain no consigned stock.

## Architecture notes

- **Native COGS untouched.** This module never overrides
  `_stock_account_prepare_realtime_out_lines_vals` or any other
  COGS preparation method. Native correctly excludes consigned
  move lines from `move.value` at delivery, so invoice-time COGS
  reflects only the own-stock portion automatically.
- **Anchor.** Settlement rows are anchored to the customer invoice
  line, not to the underlying physical stock move. Invoices and
  bills are pure accounting documents; the ledger is the bridge
  between them and does not duplicate stock-level data.
- **Direction filter on outbound walk.** When creating ledger rows
  from a posted invoice, only stock moves in the delivery
  direction (`location_dest_id.usage == 'customer'`) are
  considered. Prior return pickings on the same SO line therefore
  do not contribute to the outbound count.
- **Refund handling via reversed_entry, not return moves.** When
  a customer credit note is posted, the module walks the original
  invoice's ledger rows and creates proportional reverse copies.
  Return move lines are deliberately not consulted, because
  Odoo's reservation does not reliably propagate the consigning
  `owner_id` to return-direction move lines.
- **State.** The ledger row's status is computed from the linked
  invoice and bill states. There is no parallel state machine to
  maintain. Cancelling either the invoice or the bill propagates
  automatically.
- **Multi-company.** Each company's invoices are processed
  independently. Ledger rows carry the invoice's `company_id`.

## Compatibility

| Item | Support |
|------|---------|
| Odoo 19.0 Enterprise | Yes |
| Odoo 19.0 Community | Yes (only depends on community modules) |
| Anglo-Saxon valuation | Yes |
| Continental valuation | Yes |
| Multi-company | Yes |
| Multi-currency | Yes (ledger row inherits the invoice's currency) |
| Customer returns / credit notes | Yes (reverse ledger rows with negative quantity) |
| Pure-consigned sales (no own stock on the line) | Yes |
| Mixed sales (own + consigned on the same line) | Yes |

## Pairs well with

- **`suite_inventory_access`** — gives accountants read access to
  `stock.move` with a built-in "Consignment Only" filter, plus
  read access to `stock.quant` and locations. With both modules
  installed, accountants can cross-jump from a settlement ledger
  row to the underlying stock move to verify quantities and
  locations without needing Inventory user rights. Each module is
  fully usable on its own.

## Out of scope

- Outbound consignment (own stock placed at customer locations).
- Per product-category override of the COGS account — the
  consigned cost enters via the vendor bill, routed by standard
  product / category configuration.
- A vendor-bill matching wizard. v1 relies on standard Odoo
  vendor-bill creation followed by selection on the ledger row.
- Splitting a single consigned outbound across multiple vendor
  bills. v1 supports one bill per ledger row.
- Auto-accrual at invoice posting. v1 leaves consignment cost
  recognition to the vendor bill posting event; profit-and-loss
  in the window between invoice posting and bill posting reflects
  only the own portion of COGS.

## Permissions

Reuses the native Accounting groups; no new group is added.

| Group | Access on settlement ledger |
|-------|------------------------------|
| `account.group_account_invoice` | Read |
| `account.group_account_user` | Read / write / create |
| `account.group_account_manager` | Full (read / write / create / delete) |
| Settings administrators | Full (Odoo's standard exemption) |

## Dependencies

- `mail` (chatter on ledger rows)
- `stock_account` (for the `_is_consigned_valued_line` helper used
  to detect consigned move lines)
- `sale_stock` (provides `account.move.line._get_stock_moves` to
  walk invoice line → stock move)

## License

LGPL-3
