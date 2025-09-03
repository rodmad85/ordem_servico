from odoo import fields, models, api
from odoo.exceptions import ValidationError

class OsSale(models.Model):
    _inherit = "sale.order"

    ordem_servico = fields.One2many(
        'ordem.servico', 'pedido_venda', string='Ordem de Serviço', copy=True, tracking=True
    )
    partner_id = fields.Many2one(
        'res.partner', string='Customer', readonly=True,
        states={'draft': [('readonly', False)], 'sent': [('readonly', False)]},
        required=True, change_default=True, index=True, tracking=1,
        domain="['|', ('company_id', '=', False), ('company_id', '=', company_id)]"
    )
    grupo = fields.Boolean(string='Grupo', compute='_check_group', default=True)
    mediadesc = fields.Float(string='Media Desc', compute='_mediadesc', store=True)
    pedido = fields.Many2many(
        'ir.attachment', 'pedicliente_os_rel', 'ir_attachment_id', 'pedido_id',
        string='Pedido', copy=True, tracking=True
    )


    @api.constrains('state', 'client_order_ref', 'pedido')
    def _check_client_order_ref(self):
        emp = self.company_id

        for order in self:
            if order.state in ['sale', 'done']:
                if not order.client_order_ref and emp.os_refcli is True:
                    raise ValidationError("O campo Referência do Cliente é obrigatório para pedidos confirmados.")
                if not order.pedido and emp.os_pedcli is True:
                    raise ValidationError("O campo Pedido do Cliente é obrigatório para pedidos confirmados.")
                if not order.ordem_servico and emp.os_req is True:
                    raise ValidationError("O campo Ordem de Serviço é obrigatório para pedidos confirmados.")
                if not order.order_line:
                    raise ValidationError("Insira ao menos 1 item para confirmar o pedido.")
                if order.amount_total == 0:
                    raise ValidationError("O pedido precisa ter um valor maior que 0.")


    def _mediadesc(self):
        for order in self:
            if order.discount_total and order.price_total_no_discount:
                order.update({'mediadesc': order.discount_total / order.price_total_no_discount})
            else:
                order.update({'mediadesc': 0})

    @api.model
    def _check_group(self):
        for rec in self:
            if self.env.user.has_group('ordem_servico.ordem_admin'):
                rec.grupo = True
            else:
                rec.grupo = rec.user_id.id == self.env.user.id

    def _action_cancel(self):
        self.ordem_servico.write({'state': 'draft'})
        return super()._action_cancel()

    def _prepare_invoice(self):
        invoice_vals = super()._prepare_invoice()
        invoice_vals['ordem_servico'] = self.ordem_servico.ids
        return invoice_vals

    def _action_done(self):
        res = super()._action_done()
        self.ordem_servico.write({'state': 'done'})
        return res

class OsSaleLine(models.Model):
    _inherit = "sale.order.line"

    mo_line = fields.Monetary(string='Mão de Obra', store=True)
    mp_line = fields.Monetary(string='Materia Prima', store=True)
    valordesc = fields.Monetary(string='Valor Desconto', store=True, compute='_compute_total_desc')
    cost = fields.Float(string='Custo', related='product_id.standard_price')
    mto = fields.Boolean(
        string='Produzir',
        help="Se marcado, uma Ordem de Produção será criada ao confirmar o pedido.", default=True
    )

    def _create_mto_production(self):
        """Cria uma Ordem de Produção para a linha MTO, configurando rotas primeiro."""
        self.ensure_one()

        # Obtém as rotas necessárias
        buy_route = self.env.ref('purchase.route_warehouse0_buy', raise_if_not_found=False)
        manufacture_route = self.env.ref('mrp.route_warehouse0_manufacture', raise_if_not_found=False)
        mto_route = self.env.ref('stock.route_warehouse0_mto', raise_if_not_found=False)

        # Configura as rotas no produto (se existirem)
        if self.product_id and buy_route and manufacture_route and mto_route:
            self.product_id.write({
                'route_ids': [(6, 0, [buy_route.id, manufacture_route.id, mto_route.id])]
            })

        # Cria a ordem de produção
        mo = self.env['mrp.production'].create({
            'product_id': self.product_id.id,
            'product_qty': self.product_uom_qty,
            'product_uom_id': self.product_uom.id,
            'origin': self.order_id.name,
            'ordem_servico': [(6, 0, self.order_id.ordem_servico.ids)]
        })

        mo.action_confirm()
        return mo
        """Cria uma Ordem de Produção para a linha MTO."""
        self.ensure_one()
        mo = self.env['mrp.production'].create({
            'product_id': self.product_id.id,
            'product_qty': self.product_uom_qty,
            'product_uom_id': self.product_uom.id,
            'origin': self.order_id.name,
            'ordem_servico': [(6, 0, self.order_id.ordem_servico.ids)]
        })
        mo.action_confirm()
        return mo

    @api.depends('price_unit', 'discount', 'product_uom_qty')
    def _compute_total_desc(self):
        for line in self:
            line.valordesc = line.price_unit * (line.discount / 100.0) * line.product_uom_qty


class ConfirmMTOWizard(models.TransientModel):
    _name = 'confirm.mto.wizard'
    _description = 'Wizard de Confirmação MTO'

    sale_order_id = fields.Many2one('sale.order', string='Pedido de Venda')
    message = fields.Text(string='Mensagem', readonly=True)

    def action_confirm(self):
        # Confirma o pedido via método padrão, que agora vai criar apenas os MTO marcados
        return self.sale_order_id.with_context(bypass_mto_warning=True)._confirm_with_mto()

    def action_cancel(self):
        return {'type': 'ir.actions.act_window_close'}