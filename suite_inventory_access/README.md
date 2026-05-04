# Inventory Access for Sales and Accounting

Lets sales reps view stock by location and lets accountants browse
stock-move history without granting either of them the full
Inventory user role.

## The problem this fixes

Native Odoo couples inventory data visibility to the same group
that grants operational rights. Two real-world consequences:

- **Sales reps** who need to check on-hand quantities before
  quoting are forced into `stock.group_stock_user`, which exposes
  receipts, transfers, scrap, stocktake validation, and the entire
  Inventory app menu — none of which they should touch.
- **Accountants** who need to review stock-move history (for
  consignment matching, COGS reconciliation, year-end review) face
  the same all-or-nothing trade-off. The companion module
  `suite_inventory_access_landed_cost` extends this fix to landed
  cost adjustments.

The chronic complaint surfaces on the Odoo forum and
[GitHub issue #155477](https://github.com/odoo/odoo/issues/155477)
("Access right bad practice"). No upstream fix is on the roadmap.

## What this module does

Adds two narrow, independent permission groups, each with its own
data surface and dedicated menu. Neither group inherits any
inventory operational rights.

### Stock Viewer (Sales side)

Read-only access to:

- `stock.quant` — current on-hand quantities
- `stock.location`, `stock.warehouse` — location structure
- `stock.lot` — lot/serial master data

Adds **Sales → Stock View** menu showing a "Stock by Location"
list, with optional Owner and Lot/Serial columns that auto-hide
in environments where consignment or lot tracking are not enabled.

The list is grouped by location by default, filterable by
warehouse / product / owner / lot. Internal locations only and
positive on-hand quantity filters are applied by default.

### Stock History (Accounting side)

Read-only access to:

- `stock.move`, `stock.move.line` — movement history
- `stock.location`, `stock.warehouse`, `stock.lot`, `stock.picking.type`

Adds **Accounting → Reporting → Stock Moves** menu with a
read-only history list. Includes a built-in **Consignment Only**
filter (matches moves whose underlying move lines have an owner
set) for quickly reviewing vendor-owned outbound and inbound flow.

### Per-user location restriction

A new **Accessible Locations** field on the user form (Many2many
to `stock.location`) lets administrators scope each user to a
subset of locations. Empty = no restriction (sees every location
in the user's companies). Selecting a parent location automatically
includes all of its children.

The restriction applies to both groups via record rules. System
administrators are exempt.

## Compatibility

| Item | Support |
|------|---------|
| Odoo 19.0 Enterprise | Yes |
| Odoo 19.0 Community | Yes (only depends on community modules) |
| Multi-company | Yes (record rules use `company_ids`) |
| Multi-warehouse | Yes |
| Multi-location toggle off | Yes (the model exists either way; menus simply show fewer rows) |
| Lot/serial toggle off | Yes (Lot column hidden via `stock.group_production_lot`) |
| Consignment toggle off | Yes (Owner column hidden via `stock.group_tracking_owner`) |

## Architecture notes

- **Standalone views, no inheritance.** Stock-by-location and
  stock-move-history list/form views are built from scratch rather
  than inheriting native Inventory views. This keeps the Inventory
  app's operation buttons (validate transfer, scrap, return) out
  of reach for the new groups, and removes any risk of view xpath
  drift across point releases.
- **Group structure.** Each group lives in its own `res.groups.privilege`
  (Sales-side privilege under the Sales category, Accounting-side
  privilege under the Accounting category). Both render as
  independent checkboxes in the user form rather than mixing into
  the existing radio-button privileges.
- **Record rules.** A pair of rules per model: one company filter
  and one location filter. The location filter uses a Python
  ternary inside `domain_force` to express "empty M2M = no
  restriction" — Odoo's `safe_eval` for `ir.rule` accepts this.
- **Owner/lot column visibility** is controlled with the standard
  `stock.group_tracking_owner` / `stock.group_production_lot`
  groups, so columns auto-hide in environments where those features
  are disabled.

## Companion module

`suite_inventory_access_landed_cost` adds landed-cost RWCD access
plus an Accounting → Accounting → Landed Costs menu for the Stock
History group. It auto-installs when `stock_landed_costs` is also
present, and is silent otherwise.

## Permissions

| Group | Where it appears | What it grants |
|-------|------------------|----------------|
| Stock Visibility → Stock Viewer | User form, Sales privilege column | Read on quant/location/warehouse/lot; Sales → Stock View menu |
| Stock History → Stock History | User form, Accounting privilege column | Read on move/move-line/location/warehouse/lot/picking-type; Accounting → Reporting → Stock Moves menu |

Neither group implies any other group; assign alongside the user's
existing Sales / Accounting roles. System administrators are
exempt from all restrictions.

## Known constraints

- The Stock View menu is parented under Sales. Users who have the
  Stock Viewer group but no Sales role at all will not see the
  Sales app, hence will not see the menu. Granting them
  `sales_team.group_sale_salesman` (User: Own Documents Only) is
  enough to surface the menu.
- The Stock Moves menu is parented under Accounting → Reporting,
  which requires `account.group_account_readonly` or
  `account.group_account_invoice`. Standard accountant roles
  satisfy this.
- The location M2M on `res.users` does not auto-restrict by
  company — administrators selecting locations should use the
  company-aware location list themselves.

## Out of scope

- Per-department or per-team location grants (v1 is per-user only).
- Write access to inventory data (this module is read-only by
  design; the companion landed-cost module is the only RWCD add-on).
- A configuration screen — there are no settings; behavior is
  determined by group membership and the per-user location field.

## Dependencies

- `stock` (the data this module exposes)
- `sales_team` (parent menu under Sales)
- `account` (parent menu under Accounting)

## License

LGPL-3
