
from odoo import fields, models, api
from odoo.exceptions import UserError

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
        # vals['secondary_uom_qty'] = self.secondary_uom_qty
        # vals['secondary_uom_id'] = self.secondary_uom_id
        return vals


class OsPurchase(models.Model):
    _inherit = "purchase.order"

    forma_pagamento = fields.Many2one('payment.provider', string='Forma de Pagamento', required=True,
                                      ondelete='restrict', index=True, copy=False)
    forma_pagamento_nome = fields.Char(
        string="Nome da Forma de Pagamento",
        related="forma_pagamento.name",
        store=False,
    )

    oss = fields.Many2many('os.total.purchase', 'purchase_totalos_rel','purchase_order_id', 'os_total_purchase_id', string='Total OS', store=True, copy=True)
    certificados = fields.Many2many('ir.attachment', 'certificados_os_rel', 'ir_attachment_id', 'arquivos_id',
                                    string='Certificado', store=True, copy=False, required=True)
    chave_pix = fields.Char(
        string='Chave Pix',
        readonly=True,
        compute='_compute_chave_pix',
        store=False,  # ou True, se quiser armazenar
        copy=False
    )

    def action_open_pix_wizard(self):
        self.ensure_one()
        if not self.partner_id:
            raise UserError("Informe o parceiro antes de tentar cadastrar a chave PIX.")
        return {
            'type': 'ir.actions.act_window',
            'res_model': 'missing.pix.key.wizard',
            'view_mode': 'form',
            'target': 'new',
            'context': {
                'default_partner_id': self.partner_id.id,
            }
        }

    @api.depends('forma_pagamento', 'partner_id', 'partner_id.pix_key_ids')
    def _compute_chave_pix(self):
        for rec in self:
            if (
                    rec.forma_pagamento and rec.forma_pagamento.name == 'PIX'
                    and rec.partner_id and rec.partner_id.pix_key_ids
            ):
                # Pega o valor da chave pix do primeiro item
                rec.chave_pix = rec.partner_id.pix_key_ids[0].key
            else:
                rec.chave_pix = False

    @api.onchange('forma_pagamento')
    def _onchange_forma_pagamento_pix(self):
        if self.forma_pagamento and self.forma_pagamento.name == 'PIX':
            if self.partner_id and not self.partner_id.pix_key_ids:
                self.chave_pix = False
                return {
                    'warning': {
                        'title': "Chave PIX ausente",
                        'message': "Este parceiro não possui chave PIX cadastrada. Por favor, cadastre uma chave antes de continuar.",
                    }
                }
        else:
            self.chave_pix = False

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



class MissingPixKeyWizard(models.TransientModel):
    _name = 'missing.pix.key.wizard'
    _description = 'Chave PIX ausente'

    partner_id = fields.Many2one('res.partner', string="Parceiro", required=True)

    def action_choose_other_payment(self):
        # Apenas fecha o wizard, o usuário pode escolher outra forma de pagamento manualmente
        return {'type': 'ir.actions.act_window_close'}

    def action_create_pix_key(self):
        # Abre o formulário do parceiro na aba de vendas e compras
        return {
            'type': 'ir.actions.act_window',
            'name': 'Criar Chave PIX',
            'res_model': 'res.partner',
            'res_id': self.partner_id.id,
            'view_mode': 'form',
            'target': 'current',
        }


class TotalOs(models.Model):
    _name = "os.total.purchase"
    os = fields.Many2one('ordem.servico', string='Ordem de Serviço', store=True, copy=True)
    valor = fields.Float(string="Total")
    pedido = fields.Many2many('purchase.order', 'purchase_totalos_rel', 'os_total_purchase_id', 'purchase_order_id', string='Total OS', store=True, copy=True)
