
from odoo import fields, models, api
class OsPurchaseLine(models.Model):
    _inherit = "purchase.order.line"

    ordem_servico = fields.Many2many('ordem.servico', 'purchase_order_line_os_rel', 'purchase_order_line_id', 'os_id',
                                     string='Pedidos de Compra', store=True, copy=True)
    valor_os = fields.Float(string='Valor proporcional',compute='_total_linha_os')

    def _total_linha_os(self):
        for rec in self:
            preco = rec.price_subtotal
            len_os= len(rec.ordem_servico)
            rec.valor_os = preco / len_os


    @api.model
    def _prepare_stock_move_vals(self, picking, price_unit, product_uom_qty, product_uom):
        vals = super(OsPurchaseLine, self)._prepare_stock_move_vals(picking, price_unit, product_uom_qty, product_uom)
        vals['ordem_servico'] = self.ordem_servico.ids
        vals['secondary_uom_qty'] = self.secondary_uom_qty
        vals['secondary_uom_id'] = self.secondary_uom_id
        return vals


class OsPurchase(models.Model):
    _inherit = "purchase.order"

    forma_pagamento = fields.Many2one('payment.acquirer', string='Forma de Pagamento', required=False,
                                      ondelete='restrict', index=True, copy=False)
    oss = fields.Many2many('os.total.purchase', 'purchase_totalos_rel','purchase_order_id', 'os_total_purchase_id', string='Total OS', store=True, copy=True)
    certificados = fields.Many2many('ir.attachment', 'certificados_os_rel', 'ir_attachment_id', 'arquivos_id',
                                    string='Certificado', store=True, copy=False, required=True)

    def _prepare_invoice(self):
        invoice_vals = super(OsPurchase,self)._prepare_invoice()
        for order in self:
            for line in order.order_line:
                ids = order.order_line
                ordens = tuple(set(ids.ordem_servico.ids))

            invoice_vals['ordem_servico'] = ordens
        return invoice_vals

    def uposs(self):
        ids = self.order_line
        ordens = tuple(set(ids.ordem_servico))
        qtd = len(ordens)

        if qtd >= 1:
            for rec in ordens:
                total = 0
                for id in ids:
                    for o in id.ordem_servico:
                        if rec.id == o.id:
                            total += id.price_total / len(id.ordem_servico)
                for i in self.oss:
                    if i.os.id == rec.id:
                        self.oss = [(2,i.id)]
                self.oss = [(0,0, {'os': rec.id, 'valor': total, 'pedido': self, })]

class TotalOs(models.Model):
    _name = "os.total.purchase"
    os = fields.Many2one('ordem.servico', string='Ordem de Serviço', store=True, copy=True)
    valor = fields.Float(string="Total")
    pedido = fields.Many2many('purchase.order', 'purchase_totalos_rel', 'os_total_purchase_id', 'purchase_order_id', string='Total OS', store=True, copy=True)

