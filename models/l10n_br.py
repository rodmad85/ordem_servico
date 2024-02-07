
from odoo import fields, models, api

class OsAccountMove(models.Model):
    _inherit = "l10n_br_fiscal.document"
    ordem_servico = fields.Many2many('ordem.servico', 'ordem_servico_rel_accountmove', 'account_move_id', 'os_id',
                                     string='Ordem de Serviço', required=False, index=True,
                                     copy=True, store=True, readonly=False)

class OsImpostos(models.Model):
    _inherit = ["l10n_br_fiscal.operation"]

    meses = fields.One2many('os.impostos.line', 'fiscal_position',
                             string="Taxas", required=False, ondelete='cascade', auto_join=True)

class OsImpostosLine(models.Model):
    _name = "os.impostos.line"
    _order = 'fiscal_position'

    fiscal_position = fields.Many2one('l10n_br_fiscal.operation', string="Posição Fiscal", store=True, index=True)
    mes = fields.Date(string='Data', store=True, copy=True, required=True)
    name = fields.Char(string='Name', store=True, default='imp')
    percentual = fields.Float(string='Percentual', store=True, required=True)