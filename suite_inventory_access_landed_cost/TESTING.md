# Testing checklist — suite_inventory_access_landed_cost

Manual verification scenarios. Run on a fresh Odoo 19 Enterprise
database with both `suite_inventory_access` and `stock_landed_costs`
installed (the bridge module then auto-installs).

## Setup

Reuse the **U3 — Pure Accountant** user from the base module's
TESTING.md:

- Accounting: Accountant
- Stock History: Stock History
- Accessible Locations: empty
- No `stock.group_stock_user` membership

## Scenarios

### A. Auto-install behavior

| Step | Expected |
|------|----------|
| Fresh DB with `stock_landed_costs` not yet installed | Bridge module also not installed. Apps → Installed list does not show it. |
| Install `stock_landed_costs` | Bridge module auto-installs. Apps → Installed shows both. |
| Uninstall `stock_landed_costs` | Bridge module is also uninstalled. Base module continues to work. |
| Reinstall both | Bridge re-activates cleanly. No tracebacks. |

### B. Menu and view access

| Step | Expected |
|------|----------|
| Log in as U3 | Accounting → Accounting → Landed Costs menu entry visible. |
| Open Landed Costs | Native list view loads. Create button is available (RWCD granted). |
| Click Create | Form opens. All native landed cost fields editable. |
| Fill amount, pick a vendor bill / move, set a cost type | Standard landed cost flow works exactly as if the user had stock_user rights. |
| Compute / Validate | Native compute and validation actions succeed. Valuation adjustments are created. |
| Cancel and re-validate | Both directions work without errors. |

### C. Inventory app stays out of reach

| Step | Expected |
|------|----------|
| As U3, look for Inventory app in the apps switcher | Inventory app is not visible. |
| As U3, navigate directly to /odoo/inventory via URL | Access denied or permission error. |
| As U3, navigate to /odoo/landed-costs via URL | The Landed Costs list opens normally (allowed because the action is gated to U3's group). |

### D. Co-existence with native Inventory user

| Step | Expected |
|------|----------|
| Create user U4 with stock_user role only (no Stock History group) | U4 can access landed cost via Inventory app menu as before. |
| U4 has no Accounting menu | Confirmed. |
| Both U3 (via Accounting) and U4 (via Inventory) can list and edit the same landed cost records | Yes. RWCD applies to both, no record rule conflict. |

### E. Multi-company

| Step | Expected |
|------|----------|
| Create Company B and a vendor bill in Company B | (setup) |
| As U3 in Company A | Landed Costs list shows Company A records only. |
| Switch U3 to Company B | List shows Company B records only. |
| Switch to All Companies | List shows both. |
| Per-user location restriction (set on U3) | Affects the base module's Stock Moves menu but does not directly affect landed cost (landed cost itself is not location-scoped via record rule). |

### F. Bridge dependency strictness

| Step | Expected |
|------|----------|
| Try to install bridge module without `suite_inventory_access` | Install fails with a clear missing-dependency error. (Odoo manifest enforces this.) |
| Try to install bridge module without `stock_landed_costs` | Same — install fails. |
| Both prerequisites present | Bridge installs cleanly. |

## Sign-off

- [ ] All A-F scenarios pass
- [ ] No traceback on bridge install / uninstall / reinstall in either order
- [ ] Native Inventory user (U4) is unaffected
