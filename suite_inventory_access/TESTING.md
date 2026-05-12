# Testing checklist — suite_inventory_access (Sales Stock Viewer)

Manual verification scenarios. Run on a fresh Odoo 19 Enterprise
database with the module installed.

## Setup

Create two test users (no inventory rights for either):

- **U1 — Pure Sales User**
  - Sales: User: Own Documents Only
  - Stock Visibility: Stock Viewer (the new group)
  - Accessible Locations: empty
- **U2 — Sales User with location restriction**
  - Sales: User: Own Documents Only
  - Stock Visibility: Stock Viewer
  - Accessible Locations: WH/Stock only (assume there is also WH/Stock/Shelf-A and a separate WH2/Stock)

System administrator session is used for setup steps and cross-checks.

## Scenarios

### A. Sales: Stock by Location menu visibility

| Step | Expected |
|------|----------|
| Log in as U1 | Sales menu visible. Sales → Products → Stock View entry visible. |
| Open Stock View | List loads. Default filters: Internal Locations Only + On Hand > 0. Columns include Location, Warehouse, Product, Quantity. Owner / Lot columns visible only if those features are enabled. |
| No Inventory app menu | The Inventory app does not appear in the apps switcher. Nothing about Receipts / Transfers / Scrap / Stocktake is reachable. |
| Try to create a quant from the list | Create button is hidden (`create="false"`). |
| Open the form view | Form is read-only (`edit="false"`). No save / delete / duplicate buttons. |

### B. Sales: per-user location restriction

| Step | Expected |
|------|----------|
| Log in as U2 | Stock View list shows quants in WH/Stock and any child location (Shelf-A). Quants in WH2/Stock are absent. |
| Search for a known WH2 product | Returns no result via the menu, even though the product exists. |
| As admin, clear U2's Accessible Locations | U2 sees all locations again on next page reload. |
| As admin, set U2 to a parent location only | U2 sees parent + all child locations. |

### C. On Hand column on product list

| Step | Expected |
|------|----------|
| Log in as U1 | Sales → Products → Product Variants list shows On Hand column. |
| Column shows correct quantities | Values match what the Stock View menu shows for the same products. |
| Negative / zero decoration | Zero shows warning color, negative shows danger color. |

### D. Owner / lot column auto-hide

| Step | Expected |
|------|----------|
| As admin, disable Inventory → Settings → Operations → Lots & Serial Numbers | Lot column disappears from the Stock View list. No errors on view load. |
| Disable Consignment in the same settings panel | Owner column disappears. Consigned (Vendor-Owned) filter is hidden. |
| Re-enable both | Columns reappear as expected. |

### E. Multi-company

| Step | Expected |
|------|----------|
| As admin, create Company B and a warehouse in Company B | (setup) |
| Add U1 to both companies | U1 can switch between companies via the company selector. |
| Switch U1 to Company A | Stock View list shows only Company A quants. |
| Switch U1 to Company B | List shows only Company B quants. |
| Switch to "All Companies" | Quants from both companies appear (subject to Accessible Locations filter, if set). |

### F. System administrator exemption

| Step | Expected |
|------|----------|
| As admin, with no Stock Visibility group assigned, navigate to Sales menu | The Stock View menu entry is not visible (admin still respects action group_ids). |
| Assign Stock Viewer to admin | Menu entry appears. |
| With Accessible Locations set on admin | Admin still sees every location regardless (system admin exemption applies). |

## Known boundaries (do not test as bugs)

- A user with Stock Viewer but no Sales role at all sees no menu —
  granting the lowest sales group (User: Own Documents Only) is
  required for the menu hierarchy to render.
- Administrative users always see the Inventory app and all menus
  regardless of which groups they are assigned.
- The location M2M on res.users is not company-filtered in its
  domain — admins picking locations should be aware of which
  company they are scoping.

## Sign-off

- [ ] All A-F scenarios pass
- [ ] No traceback on module install / uninstall / reinstall
- [ ] No traceback on Lot / Consignment toggle
