
from odoo import fields, models


class MgmtNon(models.Model):
    _inherit = 'mgmtsystem.nonconformity'

    ordem_servico = fields.Many2many('ordem.servico', 'os_rel_mgmt', 'mgmt_id', 'os_id',
                                     string='Ordem de Serviço', required=False, index=True,
                                     copy=True, store=True, readonly=False)
    partner_id = fields.Many2one("res.partner", "Partner", required=True, related='ordem_servico.cliente_id')
