from odoo import fields, models, api


class OsConfig(models.Model):
    _name = 'os.config'
    _description = 'Configuração Ordem de Serviço'

    funcionarios = fields.One2many('hr.employee', 'os_config_id', string='Funcionários',
                                   help='Funcionários que podem ser selecionados na Ordem de Serviço')
    horas = fields.Float(string='Horas', help='Quantidade de horas que o funcionário pode trabalhar na Ordem de Serviço')
    horas_consumidas = fields.Float(string='Horas Consumidas',
                                    help='Quantidade de horas que o funcionário já trabalhou na Ordem de Serviço',
                                    compute='_compute_horas_consumidas', store=True)
    