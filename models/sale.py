from odoo import fields, models, api
from odoo.exceptions import ValidationError


class OsSale(models.Model):
    _inherit = ["sale.order"]
    ordem_servico = fields.Many2many('ordem.servico', 'ordem_servico_rel_sale', 'sale_order_id', 'os_id',
                                     string='Ordem de Serviço', required=False, index=True,
                                     copy=True, store=True, readonly=False)
    horas_mo = fields.Integer(string='Total Horas', required=True, store=True)
    valor_horas = fields.Monetary(string='Valor Horas', required=True, store=True, default="50")
    valor_total_horas = fields.Monetary(string='Total Horas', required=True, store=True, readonly=True, compute="_amount_resultado")
    valor_total_hmanual = fields.Monetary(string='Valor Horas Manual', store=True)
    imposto = fields.Many2one('os.impostos.line', string='Imposto %', store=True)
    materia_prima = fields.Monetary(string='Matéria Prima', required=True, store=True)
    terceiros = fields.Monetary(string='Terceiros', store=True, default="")
    resultado = fields.Monetary(string='Total Sem Imposto', store=False, compute='_amount_resultado')
    partner_id = fields.Many2one(
        'res.partner', string='Customer', readonly=True,
        states={'draft': [('readonly', False)], 'sent': [('readonly', False)]},
        required=True, change_default=True, index=True, tracking=1,
        domain="['|', ('company_id', '=', False), ('company_id', '=', company_id)]", )
    grupo = fields.Boolean(string='Grupo', compute='_check_group', default=True)
    mediadesc = fields.Float(string='Media Desc', compute='_mediadesc', store=True)
    pedido = fields.Many2many('ir.attachment', 'pedicliente_os_rel', 'ir_attachment_id', 'pedido_id',
                              string='Pedido', store=True, copy=True)

    # Cálculo de valor de orçamento
    @api.onchange('valor_horas','horas_mo')
    def _amount_resultado(self):

        for rec in self:
            rec.update({'resultado': rec.valor_horas + rec.materia_prima + rec.terceiros})
            rec.update({'valor_total_horas': rec.valor_horas * rec.horas_mo})

    def _mediadesc(self):
        for order in self:
            if self.discount_total and self.price_total_no_discount:
                order.update({'mediadesc': order.discount_total / order.price_total_no_discount})
            else:
                order.update({'mediadesc': 0})

    def write(self, vals):
        res = super(OsSale, self).write(vals)
        for order in self:
            if order.horas_mo == 0:
                raise ValidationError("Preencha as Horas!")
            elif order.valor_horas == 0:
                raise ValidationError("Preencha o Valor Horas!")
            elif order.materia_prima == 0:
                raise ValidationError("Preencha a Materia Prima!")
        return res

    @api.model
    def _check_group(self):

        for rec in self:

            if self.env.user.has_group('ordem_servico.ordem_admin'):
                self.grupo = True
            else:
                if rec.user_id.id == self.env.user.id:
                    self.grupo = True
                else:
                    self.grupo = False

    def _action_cancel(self):

        oss = self.ordem_servico.ids
        for os in oss:
            self.env['ordem.servico'].browse(os).write({'state': 'draft'})

        res = super(OsSale, self)._action_cancel()
        return res

    def _action_confirm(self):

        oss = self.ordem_servico.ids
        name = self.name
        for os in oss:
            self.env['ordem.servico'].browse(os).write({'state': 'aberta'})

        producao = self.env['mrp.production'].search([('origin', '=', name)])
        producao.write({'ordem_servico': oss})

        res = super(OsSale, self)._action_confirm()
        return res

    def _prepare_invoice(self):
        invoice_vals = super(OsSale, self)._prepare_invoice()
        invoice_vals['ordem_servico'] = self.ordem_servico.ids
        return invoice_vals

    def _action_done(self):
        vals = super(OsSale, self)._action_done()
        vals['ordem_servico'] = self.ordem_servico.ids


class OsSaleLine(models.Model):
    _inherit = ["sale.order.line"]

    mo_line = fields.Monetary(string='Mão de Obra', store=True)
    mp_line = fields.Monetary(string='Materia Prima', store=True)
    valordesc = fields.Monetary(string='Valor Desconto', store=True, compute='total_desc')
    cost = fields.Float(string='Custo', related='product_id.standard_price')

    def _amount_cost(self):

        for line in self:
            line.cost = line.product_id.standard_price
            self.cost = line.cost

    @api.depends('price_unit', 'discount', 'product_uom_qty')
    def total_desc(self):
        for order in self:
            for line in order:
                line.valordesc = line.price_unit * (line.discount / 100.0) * line.product_uom_qty
