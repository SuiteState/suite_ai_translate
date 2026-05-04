from odoo import _, api, fields, models


class SuiteConsignmentCogsLine(models.Model):
    _name = 'suite.consignment.cogs.line'
    _description = 'Consignment Settlement Line'
    _inherit = ['mail.thread', 'mail.activity.mixin']
    _order = 'invoice_id desc, id desc'
    _rec_name = 'name'

    name = fields.Char(
        string='Reference',
        required=True,
        copy=False,
        readonly=True,
        default=lambda self: _('New'),
        index=True,
    )

    # ------------------------------------------------------------------
    # Invoice side (system-populated, read-only)
    # ------------------------------------------------------------------
    invoice_id = fields.Many2one(
        'account.move',
        string='Customer Invoice',
        required=True,
        readonly=True,
        ondelete='cascade',
        index=True,
    )
    invoice_line_id = fields.Many2one(
        'account.move.line',
        string='Invoice Line',
        readonly=True,
        ondelete='cascade',
    )
    sale_order_line_id = fields.Many2one(
        'sale.order.line',
        string='Sale Order Line',
        compute='_compute_sale_order_line_id',
        store=True,
    )
    sale_order_id = fields.Many2one(
        'sale.order',
        string='Sale Order',
        related='sale_order_line_id.order_id',
        store=True,
    )
    product_id = fields.Many2one(
        'product.product',
        string='Product',
        required=True,
        readonly=True,
        index=True,
    )
    quantity = fields.Float(
        string='Quantity',
        required=True,
        readonly=True,
        digits='Product Unit of Measure',
    )
    owner_id = fields.Many2one(
        'res.partner',
        string='Owner / Vendor',
        required=True,
        readonly=True,
        index=True,
    )
    sales_unit_price = fields.Float(
        string='Sales Unit Price',
        related='invoice_line_id.price_unit',
        store=True,
        digits='Product Price',
    )
    sales_subtotal = fields.Monetary(
        string='Sales Subtotal',
        compute='_compute_sales_subtotal',
        store=True,
    )

    # ------------------------------------------------------------------
    # Bill side (user-editable)
    # ------------------------------------------------------------------
    bill_id = fields.Many2one(
        'account.move',
        string='Vendor Bill',
        domain=(
            "[('move_type', 'in', ('in_invoice', 'in_refund')),"
            " ('partner_id', '=', owner_id),"
            " ('state', '=', 'posted')]"
        ),
        copy=False,
        index=True,
        tracking=True,
    )
    product_cost = fields.Float(
        string='Product Cost',
        digits='Product Price',
        copy=False,
        tracking=True,
        help=(
            "Unit cost of the consigned product. Auto-filled from the "
            "first matching product line on the selected vendor bill, "
            "and overwritten whenever the bill is changed. May be edited "
            "manually after sync."
        ),
    )
    cost_subtotal = fields.Monetary(
        string='Cost Subtotal',
        compute='_compute_cost_subtotal',
        store=True,
    )

    # ------------------------------------------------------------------
    # Refund traceability
    # ------------------------------------------------------------------
    reverse_of_id = fields.Many2one(
        'suite.consignment.cogs.line',
        string='Reverses',
        readonly=True,
        copy=False,
        index='btree_not_null',
        help=(
            "Set on rows generated from a customer credit note. Points "
            "back to the original invoice's settlement ledger row."
        ),
    )
    reversed_by_ids = fields.One2many(
        'suite.consignment.cogs.line',
        'reverse_of_id',
        string='Reversed By',
    )

    # ------------------------------------------------------------------
    # Status (compute, read-only)
    # ------------------------------------------------------------------
    state = fields.Selection(
        selection=[
            ('draft', 'Draft'),
            ('pending', 'Pending'),
            ('settled', 'Settled'),
            ('cancelled', 'Cancelled'),
        ],
        string='Status',
        compute='_compute_state',
        store=True,
        index=True,
    )

    # ------------------------------------------------------------------
    # Currency / company (related)
    # ------------------------------------------------------------------
    currency_id = fields.Many2one(
        'res.currency',
        related='invoice_id.currency_id',
        store=True,
    )
    company_id = fields.Many2one(
        'res.company',
        related='invoice_id.company_id',
        store=True,
        index=True,
    )

    # ------------------------------------------------------------------
    # Compute methods
    # ------------------------------------------------------------------
    @api.depends('invoice_line_id.sale_line_ids')
    def _compute_sale_order_line_id(self):
        for rec in self:
            rec.sale_order_line_id = rec.invoice_line_id.sale_line_ids[:1]

    @api.depends('quantity', 'sales_unit_price')
    def _compute_sales_subtotal(self):
        for rec in self:
            rec.sales_subtotal = rec.quantity * rec.sales_unit_price

    @api.depends('quantity', 'product_cost')
    def _compute_cost_subtotal(self):
        for rec in self:
            rec.cost_subtotal = rec.quantity * rec.product_cost

    @api.depends('invoice_id.state', 'bill_id', 'bill_id.state')
    def _compute_state(self):
        for rec in self:
            invoice_state = rec.invoice_id.state
            if invoice_state == 'cancel':
                rec.state = 'cancelled'
            elif invoice_state == 'draft':
                rec.state = 'draft'
            elif not rec.bill_id or rec.bill_id.state != 'posted':
                rec.state = 'pending'
            else:
                rec.state = 'settled'

    # ------------------------------------------------------------------
    # Onchange — bill selection always overwrites product_cost
    # ------------------------------------------------------------------
    @api.onchange('bill_id')
    def _onchange_bill_id(self):
        for rec in self:
            if not rec.bill_id:
                rec.product_cost = 0.0
                continue
            matching = rec.bill_id.invoice_line_ids.filtered(
                lambda line, p=rec.product_id: line.product_id == p
            )
            rec.product_cost = matching[:1].price_unit

    # ------------------------------------------------------------------
    # Create — assign sequence-based name
    # ------------------------------------------------------------------
    @api.model_create_multi
    def create(self, vals_list):
        for vals in vals_list:
            if vals.get('name', _('New')) == _('New'):
                vals['name'] = self.env['ir.sequence'].next_by_code(
                    'suite.consignment.cogs.line'
                ) or _('New')
        return super().create(vals_list)
