from ast import literal_eval
from odoo import fields, models, api

class ResConfigSettings(models.TransientModel):
    _inherit = 'res.config.settings'

    horasmensais =fields.Float(string='Horas Mensais', config_parameter='ordem_servico.horasmensais',default=176)
    funcionarios = fields.Many2many('hr.employee','oshr_rel_config', 'conf_id', 'os_id', string='Funcionários')
    totalhoras = fields.Float(string='Total Horas', config_parameter='ordem_servico.totalhoras', default='')
    entrada = fields.Datetime(string="Entrada")
    saida = fields.Datetime(string="Saida")

    @api.onchange('funcionarios')
    def _totalhoras(self):
        tfunc = len(self.funcionarios)
        self.totalhoras = tfunc * self.horasmensais
        self.write({'totalhoras': tfunc * self.horasmensais})


    def set_values(self):
        """employee setting field values"""
        res = super(ResConfigSettings, self).set_values()
        self.env['ir.config_parameter'].sudo().set_param('oshorasconfig.totalhoras', self.totalhoras)
        self.env['ir.config_parameter'].sudo().set_param('ordem_servico.funcionarios', self.funcionarios.ids)
        self.env['ir.config_parameter'].sudo().set_param('oshorasconfig.horasmensais', self.horasmensais)
        self.env['ir.config_parameter'].sudo().set_param('oshorasconfig.entrada', self.entrada)
        self.env['ir.config_parameter'].sudo().set_param('oshorasconfig.saida', self.saida)

        return res

    @api.model
    def get_values(self):
        """employee setting field values"""
        res = super(ResConfigSettings, self).get_values()


        total = self.env['ir.config_parameter'].sudo().get_param('oshorasconfig.totalhoras')
        funcio = self.env['ir.config_parameter'].sudo().get_param('ordem_servico.funcionarios')
        mensal = self.env['ir.config_parameter'].sudo().get_param('oshorasconfig.horasmensais')
        ent = self.env['ir.config_parameter'].sudo().get_param('oshorasconfig.entrada')
        sai = self.env['ir.config_parameter'].sudo().get_param('oshorasconfig.saida')
        linhas = False
        if funcio:
            linhas = [(6,0,literal_eval(funcio))]
        res.update(
            totalhoras=float(total),
            funcionarios=linhas,
            horasmensais=float(mensal),
            entrada=ent,
            saida=sai,
        )

        return res