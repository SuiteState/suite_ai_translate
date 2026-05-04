# Testing checklist — suite_consignment_cogs

Manual verification scenarios for the Consignment Settlement
Ledger module. Run on a fresh Odoo 19 Enterprise database with
the module installed and the Inventory → Settings → Operations →
Consignment toggle enabled.

## Setup

- Two storable products: `P-OWN` (own stock) and `P-MIXED`
  (used in mixed-sale scenarios; consigned units share this SKU
  with own units in some scenarios).
- Two vendors: `Vendor-A` (consignor), `Vendor-B`.
- One customer: `Cust-1`.
- Two warehouses (optional, for multi-warehouse cross-check).
- Standard Sales / Accounting users.

Receive consigned stock:

- Create a manual receipt or PO receipt where the move line's
  `Owner` field is set to `Vendor-A`. Validate. Verify the quants
  in `WH/Stock` show `Vendor-A` as owner and that
  `move.value == 0` for that consigned receipt.

## Scenarios

### A. Pure-consigned sale (no own stock involved)

| Step | Expected |
|------|----------|
| Receive 10 of `P-MIXED` consigned from Vendor-A. No own stock. | Quants show 10 with owner=Vendor-A. |
| SO `Cust-1` for 5 of `P-MIXED`. Confirm. Deliver 5. | Delivery uses consigned quants. |
| Create and post the customer invoice. | Invoice posts. **Native COGS journal posts no COGS line** (price_unit = 0 → continue). Sales income and AR posted normally. |
| Settlement ledger | One row created: invoice line × Vendor-A, qty=5, state='pending'. Visible on the invoice's "Consignment Lines" notebook tab. |
| Invoice list view | "Consignment Pending" flag set on this invoice. |

### B. Mixed-sale (5 own + 5 consigned, same SKU on one line)

| Step | Expected |
|------|----------|
| Have 5 of `P-MIXED` own stock at avg cost 100. Have 5 consigned from Vendor-A. | (setup) |
| SO `Cust-1` for 10 of `P-MIXED` at sale price 200. Confirm. Deliver 10. | Delivery picks 5 own + 5 consigned (Odoo prefers own first; verify). |
| Post invoice. | **Native COGS journal**: total = 500 (own portion only). Verify in the journal entry: COGS line total amount is 500, not 1000. |
| Settlement ledger | One row created: invoice line × Vendor-A, qty=5, state='pending'. |

### C. Vendor settlement bill matching

| Step | Expected |
|------|----------|
| Continue from B. Vendor-A sends a settlement bill for 5 units at 80 each. | (setup) |
| Create vendor bill (`in_invoice`) for Vendor-A, 5 of `P-MIXED` at 80. Post. | Standard vendor bill flow. |
| Open Accounting → Customers → Consignment Settlement. Filter by Vendor-A, pending. | The Scenario B ledger row appears. |
| Set Vendor Bill = the bill just posted. | `product_cost` auto-fills to 80. `cost_subtotal` becomes 400. |
| Save. State changes to 'settled'. Row turns green. | Confirmed. |
| Reopen the invoice from Scenario B. | "Consignment Pending" flag now cleared. |
| Open the vendor bill. | "Settled Consignment Lines" notebook tab shows this ledger row. |

### D. Customer credit note (full refund)

| Step | Expected |
|------|----------|
| Continue from B (do not proceed with C settlement; or pick a separate fresh invoice for clarity). | (setup) |
| From the customer invoice, click "Credit Note" → "Full refund (and new draft)" or just full refund. Post the credit note. | Credit note posts. |
| Settlement ledger | A new row is created against the credit note: qty = -5 (negative), state='pending', `reverse_of_id` points to the original Scenario B ledger row. |

### E. Customer credit note (partial refund)

| Step | Expected |
|------|----------|
| Set up a fresh mixed sale: 6 own + 4 consigned from Vendor-A on one invoice line of 10 units at 200. Post invoice. | Settlement row: qty=4. |
| Issue partial credit note for 5 of the 10 units. Post. | Credit note posts with quantity=5. |
| Settlement ledger | Reverse row created with qty = `-4 × (5/10) = -2`, state='pending', `reverse_of_id` set. |

### F. Cancellation propagation

| Step | Expected |
|------|----------|
| Cancel a posted customer invoice that has consignment ledger rows. | Ledger rows' state recomputes to 'cancelled'. |
| Cancel a posted vendor bill that was matched on a ledger row. | Ledger row state reverts to 'pending' (`bill_id.state != 'posted'`). |
| Reset invoice to draft. | Ledger rows show 'draft' state. |

### G. Multi-company

| Step | Expected |
|------|----------|
| Create the same setup in Company B. Post a mixed-sale invoice in Company B. | Ledger rows carry Company B's `company_id`. |
| Switch user to Company A. Open Consignment Settlement menu. | Only Company A rows visible. |
| Switch to All Companies. | Both companies' rows appear. |

### H. Pairs-well-with check (only if `suite_inventory_access` installed)

| Step | Expected |
|------|----------|
| As a Stock-History-group accountant, open a settlement ledger row. | Cross-jump to invoice line works (read access). |
| Open Accounting → Reporting → Stock Moves → Consignment Only filter. | The corresponding outbound move appears. Quantity matches the ledger row's quantity. |

## Known boundaries (do not test as bugs)

- A stock return picking that is not followed by a customer credit
  note does not create a reverse ledger row. The module ties
  reversals to the credit note event by design — no credit note,
  no accounting reversal.
- Non-trivial proportional refunds (e.g., refund split across
  multiple lines that originally pointed to different consigning
  owners) are mapped by product only. Edge cases involving the
  same product on multiple lines may need manual ledger cleanup.
- Auto-fill of `product_cost` reads only the first matching
  product line on the bill. Multiple matching lines on one bill
  require manual review.

## Sign-off

- [ ] All A-G scenarios pass
- [ ] H passes if `suite_inventory_access` installed; not applicable otherwise
- [ ] No traceback on module install / uninstall / reinstall
- [ ] No traceback on any cancel / re-post sequence
