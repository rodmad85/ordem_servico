
from odoo import fields, models, api




class OsAccountMove(models.Model):
    _inherit = 'account.move'

    ordem_servico = fields.Many2many('ordem.servico', 'ordem_servico_rel_account', 'sale_order_id', 'os_id',
                                     string='Ordem de Serviço', required=False, index=True,
                                     copy=True, store=True, readonly=False)
    payment_mode_id_name = fields.Char(
        string="Nome da Forma de Pagamento",
        related="payment_mode_id.name",
        store=False,
    )

    chave_pix = fields.Char(
        string='Chave Pix',
        readonly=True,
        compute='_compute_chave_pix',
        store=False,  # ou True, se quiser armazenar
        copy=False
    )

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