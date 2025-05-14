
from odoo import fields, models, api
from odoo.exceptions import ValidationError

class OsMaintenance(models.Model):
    _inherit = ["maintenance.request"]

    funcionario = fields.Many2one('hr.employee', string='Funcionário', related='equipment_id.employee_id', store=True)
    res_partner = fields.Many2one('res.partner', string='Assistência', store=True)
    show_res_partner = fields.Boolean(compute="_compute_visibility_fields", store=False)

    @api.constrains('maintenance_team_id', 'res_partner')
    def _check_assistencia_obrigatoria(self):
        for record in self:
            if record.maintenance_team_id and record.maintenance_team_id.name == 'Manutenção Externa' and not record.res_partner:
                raise ValidationError(
                    "O campo 'Assistência' é obrigatório quando a Equipe de Manutenção é 'Manutenção Externa'.")

    @api.depends('maintenance_team_id')
    def _compute_visibility_fields(self):
        for rec in self:
            team = rec.maintenance_team_id.name if rec.maintenance_team_id else ''
            rec.show_res_partner = team == 'Manutenção Externa'
            rec.user_id = ''

    @api.onchange('maintenance_team_id')
    def _onchange_team_id(self):
        if self.maintenance_team_id and self.maintenance_team_id.name == 'Manutenção Externa' and not self.res_partner:
            return {
                'warning': {
                    'title': "Atenção",
                    'message': "Selecione uma Assistência para a equipe 'Manutenção Externa'.",
                }
            }