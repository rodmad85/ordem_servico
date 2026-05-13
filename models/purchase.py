
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

    forma_pagamento = fields.Many2one('payment.provider', string='Forma de Pagamento',
                                      ondelete='restrict', index=True, copy=False)
    payment_mode_id_name = fields.Char(
        string="Nome da Forma de Pagamento",
        related="payment_mode_id.name",
        store=False,
    )
    incoterm_id = fields.Many2one(required=True)
    fiscal_position_id = fields.Many2one(required=True)
    payment_term_id = fields.Many2one(required=True)
    vendedor = fields.Many2one('res.partner', string='Vendedor', readonly=False, required=False,
                                   index=True, domain="[('parent_id','=',partner_id)]", context={'show_only_contact_name': True})
    oss = fields.Many2many('os.total.purchase', 'purchase_totalos_rel','purchase_order_id', 'os_total_purchase_id', string='Total OS', store=True, copy=True)
    certificados = fields.Many2many('ir.attachment', 'certificados_os_rel', 'ir_attachment_id', 'arquivos_id',
                                    string='Certificado', store=True, copy=False, required=True)
    tipo_pix = fields.Char (string='Tipo',
        readonly=True,
        store=True,  # ou True, se quiser armazenar
        copy=False)
    chave_pix = fields.Char(
        string='Chave Pix',
        readonly=True,
        compute='_compute_chave_pix',
        store=True,  # ou True, se quiser armazenar
        copy=False
    )

    def read(self, fields=None, load='_classic_read'):
        # Override de read: carrega via super() (preserva todo comportamento padrão),
        # então ajusta APENAS o label de 'vendedor' quando preenchido.
        # Fluxo 2: reabertura do formulário usa read do purchase.order, que retorna
        # display_name padrão 'Empresa, Contato'. Aqui substituímos por [id, partner.name]
        # via name_get com contexto, sem alterar valor gravado.
        # Afeta somente 'vendedor', preserva global.
        result = super().read(fields=fields, load=load)
        if fields and 'vendedor' in fields:
            vendedor_ids = list(set(
                record['vendedor'][0]
                for record in result
                if record.get('vendedor')
            ))
            if vendedor_ids:
                partner_names = dict(
                    self.env['res.partner']
                    .with_context(show_only_contact_name=True)
                    .browse(vendedor_ids)
                    .name_get()
                )
                for record in result:
                    vid_tuple = record.get('vendedor')
                    if vid_tuple and vid_tuple[0] in partner_names:
                        record['vendedor'] = (vid_tuple[0], partner_names[vid_tuple[0]])
        return result

    def action_approve_all_purchases(self):
        for rec in self:
            if rec.state == 'to approve':
                rec.button_approve()

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

    @api.depends('payment_mode_id', 'partner_id', 'partner_id.pix_key_ids')
    def _compute_chave_pix(self):
        for rec in self:
            if (
                    rec.payment_mode_id and rec.payment_mode_id.name == 'Pix'
                    and rec.partner_id and rec.partner_id.pix_key_ids
            ):
                pix_key = rec.partner_id.pix_key_ids[0]

                rec.chave_pix = pix_key.key

                selection = pix_key._fields['key_type']._description_selection(self.env)
                rec.tipo_pix = dict(selection).get(pix_key.key_type, pix_key.key_type)

            else:
                rec.chave_pix = False
                rec.tipo_pix = False

    @api.onchange('payment_mode_id')
    def _onchange_forma_pagamento_pix(self):
        if self.payment_mode_id and self.payment_mode_id.name == 'Pix':
            if not self.partner_id.pix_key_ids:
                self.chave_pix = False
                return {
                    'warning': {
                        'title': "Chave PIX ausente",
                        'message': "Este parceiro não possui chave PIX cadastrada. Por favor, cadastre uma chave antes de continuar.",
                    }
                }
            else:
                _compute_chave_pix()


    def _prepare_invoice(self):
        invoice_vals = super(OsPurchase,self)._prepare_invoice()
        for order in self:
            for line in order.order_line:
                ids = order.order_line
                ordens = tuple(set(ids.ordem_servico.ids))

            invoice_vals['ordem_servico'] = ordens
            invoice_vals['payment_mode_id'] = order.payment_mode_id.id
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
