
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



    def button_confirm(self):
        res = super().button_confirm()

        grupo_admin = self.env.ref('purchase.group_purchase_manager')
        grupo_interno = self.env.ref('base.group_user')

        # Filtra apenas os usuários do grupo de administradores de compras que também são usuários internos
        users = grupo_admin.users.filtered(lambda u: grupo_interno in u.groups_id)

        partner_ids = users.mapped('partner_id').ids

        base_url = self.env['ir.config_parameter'].sudo().get_param('web.base.url')
        link = f"{base_url}/web#id={self.id}&model=purchase.order&view_type=form"

        mensagem = (
            f"Pedido de compra nº: <b>{self.name}</b><br/>"
            f"Fornecedor: <b>{self.partner_id.display_name}</b><br/>"
            f"Aguardando sua aprovação.<br/>"
            f"<a href='{link}' target='_blank'>Clique aqui para abrir o pedido</a>"
        )

        # ✅ Passo 1: Cria mensagem sem notificação por e-mail para seguidores
        message = self.message_post(
            body=mensagem,
            message_type='notification',
            subtype_xmlid='mail.mt_comment',
            notify_by_email=False,  # <- ESSENCIAL!
        )

        # ✅ Passo 2: Cria notificações manuais apenas no sino
        existing_notifications = self.env['mail.notification'].sudo().search([
            ('mail_message_id', '=', message.id),
            ('res_partner_id', 'in', partner_ids),
        ])
        notified_partners = existing_notifications.mapped('res_partner_id').ids
        missing_partners = set(partner_ids) - set(notified_partners)

        notifications = [{
            'mail_message_id': message.id,
            'res_partner_id': partner_id,
            'notification_type': 'inbox',
            'is_read': False,
        } for partner_id in missing_partners]

        if notifications:
            self.env['mail.notification'].sudo().create(notifications)

        return res

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
                    rec.payment_mode_id and rec.payment_mode_id.name == 'PIX'
                    and rec.partner_id and rec.partner_id.pix_key_ids
            ):
                # Pega o valor da chave pix do primeiro item
                rec.chave_pix = rec.partner_id.pix_key_ids[0].key
            else:
                rec.chave_pix = False

    @api.onchange('payment_mode_id')
    def _onchange_forma_pagamento_pix(self):
        if self.payment_mode_id and self.payment_mode_id.name == 'PIX':
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
