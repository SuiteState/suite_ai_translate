# Inventory Access — Landed Cost (Bridge)

Companion bridge module for `suite_inventory_access`. Auto-installs
when both `suite_inventory_access` and `stock_landed_costs` are
present. Has no effect otherwise.

## What it does

Grants the **Stock History** group (defined in
`suite_inventory_access`) full RWCD access to:

- `stock.landed.cost`
- `stock.landed.cost.lines`
- `stock.valuation.adjustment.lines`

And adds **Accounting → Accounting → Landed Costs** menu entry
exposing the standard Landed Cost views to that group.

This lets accountants perform landed cost adjustments without
being granted the full Inventory user role.

## Why a separate module

`stock_landed_costs` is an optional addon — it is not always
installed, especially on Community deployments and on lightweight
Enterprise setups. Referencing `stock.landed.cost` from the base
module would force a hard dependency, breaking installation in
environments that do not need landed cost.

The bridge pattern (`auto_install: True` with both prerequisites in
`depends`) means this module activates automatically only when
both pieces are in place, and stays out of the way otherwise.

## Compatibility

| Item | Support |
|------|---------|
| Odoo 19.0 Enterprise | Yes |
| Odoo 19.0 Community | Yes (only if `stock_landed_costs` is installed) |
| Multi-company | Yes (inherits `suite_inventory_access` record rules) |
| Per-user location restriction | Yes (inherits via the same group) |

## Architecture notes

- **Reuses native landed-cost views.** The action created by this
  module declares `res_model = 'stock.landed.cost'` and lets Odoo
  resolve the default list/form views from `stock_landed_costs`.
  This avoids duplicating view definitions and keeps the module
  in sync with upstream view changes.
- **Action gated by `group_ids`.** Only members of
  `suite_inventory_access.suite_group_accounting_stock_history`
  can open the action; the menu inherits visibility from the
  action.
- **No new models, no new fields.** Pure permission and menu glue.

## Permissions

| Group | Access |
|-------|--------|
| `suite_inventory_access.suite_group_accounting_stock_history` | RWCD on `stock.landed.cost`, `stock.landed.cost.lines`, `stock.valuation.adjustment.lines`; sees Landed Costs menu |
| Members of native `stock.group_stock_user` | Continue to access landed costs through the Inventory app as before — this module adds, does not replace |

## Out of scope

- Approval workflow on landed cost (adjacent paid modules cover this).
- Landed cost templates beyond the native ones.
- Cost rule engines or split allocations beyond native behavior.

## Dependencies

- `suite_inventory_access` (the base group this module attaches to)
- `stock_landed_costs` (the model/views this module re-exposes)

## License

LGPL-3
