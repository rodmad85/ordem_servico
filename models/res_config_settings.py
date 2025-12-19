from ast import literal_eval
from odoo import fields, models, api


class ResConfigSettings(models.TransientModel):
    _inherit = 'res.config.settings'

    # Adicionar campos relacionados à empresa
    horasmensais = fields.Float(
        string='Horas Mensais',
        related='company_id.horasmensais',
        readonly=False
    )

    funcionarios = fields.Many2many(
        'hr.employee',
        'oshr_rel_config',
        'conf_id',
        'os_id',
        string='Funcionários',
        related='company_id.funcionarios',
        readonly=False
    )

    totalhoras = fields.Float(
        string='Total Horas',
        related='company_id.totalhoras',
        readonly=False
    )

    entrada = fields.Datetime(
        string="Entrada",
        related='company_id.entrada',
        readonly=False
    )

    saida = fields.Datetime(
        string="Saida",
        related='company_id.saida',
        readonly=False
    )

    @api.onchange('funcionarios')
    def _totalhoras(self):
        for record in self:
            if record.company_id:
                tfunc = len(record.funcionarios)
                record.totalhoras = tfunc * record.horasmensais

    # Os métodos set_values e get_values não são mais necessários
    # pois estamos usando campos relacionados (related fields)


class ResCompany(models.Model):
    _inherit = 'res.company'

    horasmensais = fields.Float(
        string='Horas Mensais',
        default=176,
        help="Horas mensais padrão por funcionário"
    )

    funcionarios = fields.Many2many(
        'hr.employee',
        'company_employee_rel',
        'company_id',
        'employee_id',
        string='Funcionários da Empresa',
        domain="[('company_id', '=', id)]"  # Filtra funcionários da mesma empresa
    )

    totalhoras = fields.Float(
        string='Total Horas',
        compute='_compute_total_horas',
        store=True
    )

    entrada = fields.Datetime(string="Entrada Padrão")
    saida = fields.Datetime(string="Saída Padrão")

    @api.depends('funcionarios', 'horasmensais')
    def _compute_total_horas(self):
        for company in self:
            tfunc = len(company.funcionarios)
            company.totalhoras = tfunc * company.horasmensais