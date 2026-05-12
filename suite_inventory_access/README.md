# Sales Stock Viewer

Lets sales reps view stock by location without granting them the
full Inventory user role.

## The problem this fixes

Native Odoo couples stock data visibility to `stock.group_stock_user`,
which also grants access to receipts, transfers, scrap, stocktake,
and the entire Inventory app menu. Sales reps who only need to check
on-hand quantities before quoting are forced into this all-or-nothing
trade-off.

The chronic complaint surfaces on the Odoo forum and
[GitHub issue #155477](https://github.com/odoo/odoo/issues/155477)
("Access right bad practice"). No upstream fix is on the roadmap.

## What this module does

Adds a narrow permission group with its own data surface and
dedicated menu. The group grants no inventory operational rights.

### Stock Viewer

Read-only access to:

- `stock.quant` — current on-hand quantities
- `stock.location`, `stock.warehouse` — location structure
- `stock.lot` — lot/serial master data

Adds **Sales → Products → Stock View** menu showing a "Stock by
Location" list, with optional Owner and Lot/Serial columns that
auto-hide in environments where consignment or lot tracking are
not enabled.

The list is grouped by location by default, filterable by
warehouse / product / owner / lot. Internal locations only and
positive on-hand quantity filters are applied by default.

An **On Hand** column is also added to the product variants list
for users in this group.

### Per-user location restriction

A new **Accessible Locations** field on the user form (Many2many
to `stock.location`) lets administrators scope each user to a
subset of locations. Empty = no restriction (sees every location
in the user's companies). Selecting a parent location automatically
includes all of its children.

The restriction applies via record rules. System administrators
are exempt.

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

- **Standalone views, no inheritance.** Stock-by-location list/form
  views are built from scratch rather than inheriting native Inventory
  views. This keeps the Inventory app's operation buttons (validate
  transfer, scrap, return) out of reach, and removes any risk of
  view xpath drift across point releases.
- **Group structure.** The group lives in its own `res.groups.privilege`
  under the Sales category, rendered as an independent checkbox in
  the user form.
- **Record rules.** A pair of rules for `stock.quant`: one company
  filter and one location filter. The location filter uses a Python
  ternary inside `domain_force` to express "empty M2M = no
  restriction".
- **Owner/lot column visibility** is controlled with the standard
  `stock.group_tracking_owner` / `stock.group_production_lot`
  groups, so columns auto-hide when those features are disabled.

## Permissions

| Group | Where it appears | What it grants |
|-------|------------------|----------------|
| Stock Visibility → Stock Viewer | User form, Sales privilege column | Read on quant/location/warehouse/lot; Sales → Stock View menu; On Hand column on product list |

The group does not imply any other group. Assign alongside the
user's existing Sales role. System administrators are exempt from
all restrictions.

## Known constraints

- The Stock View menu is parented under Sales. Users who have the
  Stock Viewer group but no Sales role at all will not see the
  Sales app, hence will not see the menu. Granting them
  `sales_team.group_sale_salesman` (User: Own Documents Only) is
  enough to surface the menu.
- The location M2M on `res.users` does not auto-restrict by
  company — administrators selecting locations should use the
  company-aware location list themselves.

## Out of scope

- Per-department or per-team location grants (per-user only).
- Write access to inventory data (this module is read-only by design).
- A configuration screen — there are no settings; behavior is
  determined by group membership and the per-user location field.

## Dependencies

- `stock` (the data this module exposes)
- `sales_team` (parent menu under Sales)

## License

LGPL-3
