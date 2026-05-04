from collections import defaultdict

from odoo import api, fields, models


class AccountMove(models.Model):
    _inherit = 'account.move'

    # ------------------------------------------------------------------
    # Reverse links to the settlement ledger
    # ------------------------------------------------------------------
    suite_consignment_cogs_line_ids = fields.One2many(
        'suite.consignment.cogs.line',
        'invoice_id',
        string='Consignment Lines',
    )
    suite_consignment_settled_line_ids = fields.One2many(
        'suite.consignment.cogs.line',
        'bill_id',
        string='Settled Consignment Lines',
    )

    # ------------------------------------------------------------------
    # List-decoration / search support (compute, store=True)
    # ------------------------------------------------------------------
    suite_has_consigned = fields.Boolean(
        string='Has Consigned Items',
        compute='_compute_suite_consignment_flags',
        store=True,
    )
    suite_consignment_pending = fields.Boolean(
        string='Consignment Pending Settlement',
        compute='_compute_suite_consignment_flags',
        store=True,
    )

    @api.depends(
        'suite_consignment_cogs_line_ids',
        'suite_consignment_cogs_line_ids.state',
    )
    def _compute_suite_consignment_flags(self):
        for move in self:
            lines = move.suite_consignment_cogs_line_ids
            move.suite_has_consigned = bool(lines)
            move.suite_consignment_pending = any(
                line.state == 'pending' for line in lines
            )

    # ------------------------------------------------------------------
    # Posting hook — populate the settlement ledger
    #
    # Note on scope: this module never touches the COGS journal entry
    # produced by stock_account. Native Odoo computes the correct total
    # COGS amount when an invoice line mixes own and consigned stock
    # (the consigned portion's value is excluded from move.value at
    # delivery time, so the invoice-time COGS reflects only the own
    # portion). This module only adds a settlement ledger so accountants
    # can match each consigned outbound to a vendor bill.
    # ------------------------------------------------------------------
    def _post(self, soft=True):
        posted = super()._post(soft=soft)
        for move in posted:
            if move.move_type == 'out_invoice':
                move._suite_create_consignment_lines_from_invoice()
            elif move.move_type == 'out_refund':
                move._suite_create_consignment_lines_from_refund()
        return posted

    def _suite_create_consignment_lines_from_invoice(self):
        """Walk this invoice's underlying outbound stock moves and create
        one Consignment Settlement Line per (invoice line × consigned
        owner). Direction filter restricts to delivery moves so prior
        return pickings on the same SO line do not double-count.
        """
        self.ensure_one()
        if not self.invoice_line_ids:
            return
        Ledger = self.env['suite.consignment.cogs.line']
        for line in self.invoice_line_ids:
            consigned_by_owner = self._suite_consigned_outbound_by_owner(line)
            for owner, qty in consigned_by_owner.items():
                if not qty:
                    continue
                Ledger.create({
                    'invoice_id': self.id,
                    'invoice_line_id': line.id,
                    'product_id': line.product_id.id,
                    'quantity': qty,
                    'owner_id': owner.id,
                })

    def _suite_create_consignment_lines_from_refund(self):
        """Mirror the original invoice's settlement ledger rows with
        proportional negative quantities. Walks the original invoice's
        ledger (suite_consignment_cogs_line_ids on reversed_entry_id)
        rather than the refund's underlying stock moves, because return
        moves do not reliably carry the consigning owner_id.
        """
        self.ensure_one()
        original = self.reversed_entry_id
        if not original or not original.suite_consignment_cogs_line_ids:
            return
        Ledger = self.env['suite.consignment.cogs.line']
        # Map refund line → original invoice line by product.
        # Partial refunds get a proportional reverse quantity.
        refund_lines_by_product = defaultdict(lambda: self.env['account.move.line'])
        for refund_line in self.invoice_line_ids:
            if refund_line.product_id:
                refund_lines_by_product[refund_line.product_id] |= refund_line
        for orig_ledger in original.suite_consignment_cogs_line_ids:
            refund_lines = refund_lines_by_product.get(orig_ledger.product_id)
            if not refund_lines:
                continue
            orig_invoice_line = orig_ledger.invoice_line_id
            if not orig_invoice_line or not orig_invoice_line.quantity:
                continue
            refund_qty = sum(refund_lines.mapped('quantity'))
            if not refund_qty:
                continue
            ratio = refund_qty / orig_invoice_line.quantity
            reverse_qty = -orig_ledger.quantity * ratio
            if not reverse_qty:
                continue
            Ledger.create({
                'invoice_id': self.id,
                'invoice_line_id': refund_lines[:1].id,
                'product_id': orig_ledger.product_id.id,
                'quantity': reverse_qty,
                'owner_id': orig_ledger.owner_id.id,
                'reverse_of_id': orig_ledger.id,
            })

    @staticmethod
    def _suite_consigned_outbound_by_owner(invoice_line):
        """Return ``{owner_partner: qty_in_invoice_line_uom}`` for the
        consigned move lines underlying the given invoice line,
        restricted to delivery direction (location_dest_id is a
        customer location). Uses native helper
        stock.move.line._is_consigned_valued_line for detection.
        """
        result = defaultdict(float)
        moves = invoice_line._get_stock_moves().filtered(
            lambda m: m.state == 'done'
            and m.location_dest_id.usage == 'customer'
        )
        for ml in moves.move_line_ids:
            if not ml._is_consigned_valued_line():
                continue
            qty = ml.product_uom_id._compute_quantity(
                ml.quantity, invoice_line.product_uom_id
            )
            result[ml.owner_id] += qty
        return dict(result)
