
from odoo import fields, models, api
class OsHorasconfig(models.TransientModel):
    _inherit = 'res.config.settings'

    horasmensais =fields.Float(string='Horas Mensais', default=176)
    funcionarios = fields.Many2many('hr.employee',domain="[('department_id','=','Produção')]", help='Mostra somente os funcionarios cadastrados no departamento de Produção')
    totalhoras = fields.Float(string='Total Horas', compute='_totalhoras')

    @api.onchange('funcionarios')
    def _totalhoras(self):
        tfunc = len(self.funcionarios)
        self.totalhoras = tfunc * self.horasmensais


    def set_values(self):
        """employee setting field values"""
        res = super(OsHorasconfig, self).set_values()
        self.env['ir.config_parameter'].sudo().set_param('oshoras.totalhoras', self.totalhoras)
        self.env['ir.config_parameter'].sudo().set_param('oshoras.funcionarios', self.funcionarios.ids)
        self.env['ir.config_parameter'].sudo().set_param('oshoras.horasmensais', self.horasmensais)

        return res

    @api.model
    def get_values(self):
        """employee setting field values"""
        res = super(OsHorasconfig, self).get_values()

        total = self.env['ir.config_parameter'].sudo().get_param('oshoras.totalhoras')
        funcio = self.env['ir.config_parameter'].sudo().get_param('oshoras.funcionarios.ids')
        mensal = self.env['ir.config_parameter'].sudo().get_param('oshoras.horasmensais')
        linhas = False
        if funcio:
            linhas = [(6,0,funcio)]
        res.update(
            totalhoras=float(total),
            funcionarios=linhas,
            horasmensais=float(mensal),
        )

        return res