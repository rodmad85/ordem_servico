from odoo import fields, models, api


class OrdemServicoReport(models.TransientModel):
    _name = 'ordem.servico.report'
    _description = 'Impressão OS'

    def action_print_report(self):
