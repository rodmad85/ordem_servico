
from odoo import fields, models, api

class AccountMove(models.Model):
    _inherit = 'account.move'

    ordem_servico = fields.Many2many('ordem.servico', 'os_rel_accountmove', 'account_move_id', 'os_id',
                                     string='Ordem de Serviço', required=False, index=True,
                                     copy=True, store=True, readonly=False)

class OsAccountMove(models.Model):
    _inherit = 'account.move'

    ordem_servico = fields.Many2many('ordem.servico', 'ordem_servico_rel_account', 'sale_order_id', 'os_id',
                                     string='Ordem de Serviço', required=False, index=True,
                                     copy=True, store=True, readonly=False)
