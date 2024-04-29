
from odoo import tools
from odoo import fields, models, api
from datetime import datetime
class OsHoras (models.Model):
    _name = 'os.horas'
    _description = 'Relatorio de Horas'

    
    currency_id = fields.Many2one('res.currency', default=lambda self: self.env.company.currency_id, readonly=True)
    totalhoras = fields.Float(string='Total de Horas')
    previstas =fields.Float(string='Horas Previstas', compute='_previstas')
    vprevistas=fields.Monetary(string='Valor Horas Previstas')
    normal =fields.Float(string='Horas Normais')
    vnormal=fields.Monetary(string='Valor Horas Normais')
    extra =fields.Float(string='Horas Extras')
    vextra=fields.Monetary(string='Valor Horas Extras')
    retrabalho =fields.Float(string='Retrabalho')
    vretrabalho = fields.Monetary(string='Valor Retrabalho')
    utilizadas = fields.Float(string='Total Horas Utilizadas')
    vutilizadas = fields.Monetary(string='Valor Total Utilizadas')
    disponiveis = fields.Float(string='Horas Disponíveis')

    def default_get(self, fields):
        res = super(OsHoras, self).default_get(fields)
        t_horas = self.env['ir.config_parameter'].sudo().get_param('oshorasconfig.totalhoras')

        res.update({
            'totalhoras': t_horas,
        })

        return res

    def _previstas(self):
        osabertas = self.env["ordem.servico"].search([('state', '=', 'aberta')])
        if osabertas:
            for rec in osabertas:
                self.write({'previstas': sum(rec.osabertas.pedido_venda.mapped('horas_mo')) if rec.osabertas.pedido_venda else 0})
                self.write({'vprevistas': sum(rec.osabertas.pedido_venda.mapped('valor_horas')) if rec.osabertas.pedido_venda else 0})
            self._utilizadas()
            self.create()

    def _utilizadas(self):

        hoje = datetime.today()
        dt = datetime.strftime(hoje, '%Y')
        apontamento = self.env["hr.attendance"].search([('check_in', '>=', dt)])
        if apontamento:
            for rec in self:
                normal = sum(rec.mapped('normal_total')) if rec else 0
                self.normal += normal

                retrabalho = sum(rec.filtered(lambda l: l.retrabalho).mapped('normal_total')) if rec else 0
                self.retrabalho += retrabalho

                extra = sum(rec.filtered(lambda l: l.retrabalho == False).mapped(
                'extra_total')) if rec else 0
                self.extra += extra

                self.utilizadas += self.normal + self.retrabalho + self.extra
        else: self.utilizadas = 0






    def init(self):
        tools.drop_view_if_exists(self.env.cr, self._table)
        self._previstas()

    def create(self):
        for rec in self:
            result = super(OsHoras, self).create(vals)
            return result