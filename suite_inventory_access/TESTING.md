# Testing checklist — suite_inventory_access

Manual verification scenarios. Run on a fresh Odoo 19 Enterprise
database with the module installed.

## Setup

Create three test users (no inventory rights for any of them):

- **U1 — Pure Sales User**
  - Sales: User: Own Documents Only
  - Stock Visibility: Stock Viewer (the new group)
  - Accessible Locations: empty
- **U2 — Sales User with location restriction**
  - Sales: User: Own Documents Only
  - Stock Visibility: Stock Viewer
  - Accessible Locations: WH/Stock only (assume there is also WH/Stock/Shelf-A and a separate WH2/Stock)
- **U3 — Pure Accountant**
  - Accounting: Accountant
  - Stock History: Stock History (the new group)
  - Accessible Locations: empty

System administrator session is used for setup steps and the cross-checks.

## Scenarios

### A. Sales: Stock by Location menu visibility

| Step | Expected |
|------|----------|
| Log in as U1 | Sales menu visible. Sales → Stock View → "Stock by Location" entry visible. |
| Open Stock by Location | List loads. Default filters: Internal Locations Only + On Hand > 0. Columns include Location, Warehouse, Product, Quantity. Owner / Lot columns visible only if those features are enabled. |
| No Inventory app menu | The Inventory app does not appear in the apps switcher. Nothing about Receipts / Transfers / Scrap / Stocktake is reachable. |
| Try to create a quant from the list | Create button is hidden (`create="false"`). |
| Open the form view | Form is read-only (`edit="false"`). No save / delete / duplicate buttons. |

### B. Sales: per-user location restriction

| Step | Expected |
|------|----------|
| Log in as U2 | Stock by Location list shows quants in WH/Stock and any child location (Shelf-A). Quants in WH2/Stock are absent. |
| Search for a known WH2 product | Returns no result via the menu, even though the product exists. |
| As admin, clear U2's Accessible Locations | U2 sees all locations again on next page reload. |
| As admin, set U2 to a parent location only | U2 sees parent + all child locations. |

### C. Accounting: Stock Moves history

| Step | Expected |
|------|----------|
| Log in as U3 | Accounting → Reporting → Stock Moves entry visible. |
| Open Stock Moves | Default filters: Done + Last 30 Days. List columns include Date, Reference, Product, Done qty, Source/Destination Location, State (badge). |
| Apply Consignment Only filter | Only moves whose underlying move lines have an owner set are returned. (Verify by setting up a consigned vendor receipt first.) |
| Open a move form | Form is read-only. Operations tab shows the move lines including Owner column when consignment is enabled. |
| Try to validate / cancel | No buttons in the header. |

### D. Owner / lot column auto-hide

| Step | Expected |
|------|----------|
| As admin, disable Inventory → Settings → Operations → Lots & Serial Numbers | Lot column disappears from both the Stock by Location list and the Stock Move form. No errors on view load. |
| Disable Consignment in the same settings panel | Owner column disappears similarly. Consignment Only filter on the move list is hidden. |
| Re-enable both | Columns reappear as expected. |

### E. Multi-company

| Step | Expected |
|------|----------|
| As admin, create Company B and a warehouse in Company B | (setup) |
| Add U1 to both companies | U1 can switch between companies via the company selector. |
| Switch U1 to Company A | Stock by Location list shows only Company A quants. |
| Switch U1 to Company B | List shows only Company B quants. |
| Switch to "All Companies" | Quants from both companies appear (subject to Accessible Locations filter, if set). |

### F. System administrator exemption

| Step | Expected |
|------|----------|
| As admin, with no Stock Visibility / Stock History group assigned, navigate to the Sales / Accounting menu | The new menu entries are not visible (admin still respects action group_ids). |
| Assign Stock Viewer to admin | Menu entries appear. |
| With Accessible Locations set on admin | Admin still sees every location regardless (system admin exemption applies). |

### G. Companion landed-cost bridge (only if `stock_landed_costs` installed)

| Step | Expected |
|------|----------|
| Verify `suite_inventory_access_landed_cost` auto-installed | Visible in Apps → Installed. |
| As U3, navigate to Accounting → Accounting → Landed Costs | Menu entry visible. List loads. Create button works (RWCD granted). |
| Create a landed cost record, allocate to a vendor receipt | Standard landed cost flow works without warehouse rights. |
| Without the bridge module (uninstall stock_landed_costs first) | Bridge module is also uninstalled. Base module continues to work. |

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
- [ ] G scenarios pass if landed cost installed; not applicable otherwise
- [ ] No traceback on module install / uninstall / reinstall
- [ ] No traceback on Lot / Consignment toggle
