
from odoo import fields, models, api
from datetime import datetime,timedelta
import pytz

class HrEmployee(models.Model):
    _inherit = "hr.employee"
    valor_hora = fields.Float(string='Valor Hora', store=True)
    tipo_contrato = fields.Selection([('clt', 'CLT'), ('ht', 'HT'), ('pj', 'PJ')], string='Tipo de Contrato', store=True,
                            copy=True, required=True)
    horas_normais_total = fields.Float(string='Total Horas Normais', compute='_compute_horas_normais_total')
    horas_extras_total = fields.Float(string='Total Extras')

    # @api.depends('attendance_ids.check_in', 'attendance_ids.check_out')
    def _compute_horas_normais_total(self):
        """Computa horas normais de todos os funcionários em uma única busca."""
        if not self:
            return

        # Obter IDs de todos os funcionários a serem computados
        employee_ids = self.ids
        hoje = fields.Date.context_today(self)
        mes = hoje.month
        ano = hoje.year

        # Determinar início e fim do mês em UTC
        data_inicio = fields.Datetime.to_string(fields.Datetime.from_string(f"{ano}-{mes:02d}-01 00:00:00"))
        if mes == 12:
            data_fim = fields.Datetime.to_string(fields.Datetime.from_string(f"{ano + 1}-01-01 00:00:00"))
        else:
            data_fim = fields.Datetime.to_string(fields.Datetime.from_string(f"{ano}-{mes + 1:02d}-01 00:00:00"))

        # Buscar todas as marcações relevantes em uma única consulta
        domain = [
            ('employee_id', '=', employee_ids),
            ('check_in', '>=', data_inicio),
            ('check_in', '<', data_fim),
        ]
        attendances = self.env['hr.attendance'].search(domain)

        # Agrupar as horas normais por funcionário
        totals = {
            emp_id: 0.0
            for emp_id in employee_ids
        }
        for att in attendances:
            totals[att.employee_id.id] += att.normal_total or 0.0

        # Atribuir valores a cada funcionário
        for emp in self:
            emp.horas_normais_total = totals.get(emp.id, 0.0)

    @api.depends('attendance_ids.check_in', 'attendance_ids.check_out')
    def _compute_horas_extras_total(self):
        """Computa horas extras de todos os funcionários em uma única busca."""
        if not self:
            return

        employee_ids = self.ids
        hoje = fields.Date.context_today(self)
        mes = hoje.month
        ano = hoje.year

        data_inicio = fields.Datetime.to_string(fields.Datetime.from_string(f"{ano}-{mes:02d}-01 00:00:00"))
        if mes == 12:
            data_fim = fields.Datetime.to_string(fields.Datetime.from_string(f"{ano + 1}-01-01 00:00:00"))
        else:
            data_fim = fields.Datetime.to_string(fields.Datetime.from_string(f"{ano}-{mes + 1:02d}-01 00:00:00"))

        domain = [
            ('employee_id', 'in', employee_ids),
            ('check_in', '>=', data_inicio),
            ('check_in', '<', data_fim),
        ]
        attendances = self.env['hr.attendance'].search(domain)

        totals = {
            emp_id: 0.0
            for emp_id in employee_ids
        }
        for att in attendances:
            totals[att.employee_id.id] += att.extra_total or 0.0

        for emp in self:
            emp.horas_extras_total = totals.get(emp.id, 0.0)


class HrFields(models.Model):
    _inherit = "hr.attendance"

    def upaponta(self):
        for rec in self:
            rec._total()
            rec._tree_to_os()

    def upvalor(self):
        for rec in self:
            rec._valorhora()
            rec._total()

    data_atual = datetime.now()
    ordem_servico = fields.Many2many('ordem.servico', 'hr_attendance_os_rel', 'hr_attendance_id',
                                                   'ordem_servico_id',
                                                   string='Linha Apontamento', store=True, copy=True)
    os_tree = fields.Many2one('ordem.servico',string="OS", store=True)
    check_in = fields.Datetime(string="Check In", default=data_atual.replace(hour=10, minute=12, second=00,  microsecond=00, tzinfo=None), required=True)
    check_out = fields.Datetime(string="Check Out", default=data_atual.replace(hour=20, minute=00, second=00, microsecond=00, tzinfo=None), required=True)
    valor_hora = fields.Float(string='Valor Hora', store=True, readonly=True)
    retrabalho = fields.Boolean(string='Retrabalho', store=True)
    cem_porcento = fields.Boolean(string='100%', store=True)
    hora_not = fields.Boolean(string='Noturno', store=True)
    normal_total = fields.Float(string='Horas Normais', store=True, readonly=True, compute='_total')
    extra_total = fields.Float(string='Horas Extras', store=True, readonly=True)
    soma_total = fields.Float(string="Total de Horas", store=True)
    valor_extra_total = fields.Float(string="Valor Extras", store=True, readonly=True)
    valor_total = fields.Float(string='Valor Total', readonly=True, store=True)
    tipo_contrato = fields.Selection(string="Tipo de Contrato", related='employee_id.tipo_contrato')
    currency_id = fields.Many2one('res.currency', 'Currency',
                                  default=lambda self: self.env.user.company_id.currency_id.id, required=True)


    def _os_tree(self):
        for line in self:
            if line.ordem_servico:
                os = line.ordem_servico[0]
                line.write({'os_tree': os})

    @api.onchange('employee_id')
    def _valorhora(self):
        self.valor_hora = self.employee_id.valor_hora


    @api.depends('check_out','check_in')
    def _tree_to_os(self):
        for line in self:
            if line.os_tree:
                line.write({'ordem_servico': self.os_tree})

    @api.depends('check_out', 'check_in')
    def _total(self):
        tz = pytz.timezone('America/Sao_Paulo')
        dtent = self.check_in.date()
        if self.valor_hora == 0:
            self.valor_hora = self.employee_id.valor_hora
        if self.check_out:
            dtsai = self.check_out.date()
            entnormal = tz.localize(datetime.combine(dtent, datetime.strptime("07:12:00", '%H:%M:%S').time()))
            sainormal = tz.localize(datetime.combine(dtent, datetime.strptime("17:00:00", '%H:%M:%S').time()))
            entalm = tz.localize(datetime.combine(dtent,datetime.strptime("12:00:00", '%H:%M:%S').time()))
            saialm = tz.localize(datetime.combine(dtent, datetime.strptime("13:00:00", '%H:%M:%S').time()))
            ininot = tz.localize(datetime.combine(dtent, datetime.strptime("22:00:00", '%H:%M:%S').time()))
            fimnot = tz.localize(datetime.combine(dtsai, datetime.strptime("05:00:00", '%H:%M:%S').time()))
            noturna = 0
            extra = 0
            almoco = 0

            for line in self:

                if self.check_in and self.check_out:
                    entrada = self.check_in.astimezone(tz) - timedelta(hours=3)
                    #entrada = entrada.replace(tzinfo=None)
                    saida = self.check_out .astimezone(tz) - timedelta(hours=3)
                    #saida = saida.replace(tzinfo=None)
                else:
                    return

#Calcula horas normais.-----------------------------------------------------------
                if entrada >= entnormal and saida <= sainormal:
                    if entrada >= saialm and saida <= sainormal:
                        line.normal_total=line.worked_hours
                    if entrada < entalm and saida <= entalm:
                        line.normal_total=line.worked_hours

#calcula hora extra-----------------------------------------------------

                if saida >= sainormal and entrada >= entnormal:
                    extra = saida - sainormal
                    extra = extra.total_seconds() / 3600

                if entrada < entnormal and saida <= sainormal:
                    extra = entnormal - entrada
                    extra = extra.total_seconds() / 3600

                if entrada < entnormal and saida > sainormal:
                    extra = (entnormal - entrada)+(saida - sainormal)
                    extra = extra.total_seconds() / 3600
#Hora noturna-------------------------------
                if saida >= ininot and saida <= fimnot:
                    noturna = saida - ininot
                    noturna = float (noturna.total_seconds() / 3600)

#Almoço-------------------------------------------------------
                if line.worked_hours >= 6:
                    if entrada >= saialm:
                        almoco = 0
                    else:
                        almoco = -1

#Calculos----------------------------------------------------
#Hora normal--------------------------------------------
                if entrada >= entnormal and saida <= sainormal:
                    if almoco < 0:
                        if self.cem_porcento:
                            line.write({
                                'valor_total': 2*(line.valor_hora * (line.worked_hours + almoco)),
                                'extra_total':line.worked_hours + almoco,
                                'valor_extra_total': line.valor_hora * (line.worked_hours + almoco),
                                'normal_total': 0,
                                'soma_total': self.extra_total + self.normal_total
                            })
                        else:
                            line.write({
                                'valor_total': line.valor_hora * (line.worked_hours + almoco),
                                'normal_total': line.worked_hours + almoco - extra,
                                'soma_total': self.extra_total + self.normal_total
                            })
                    else:
                        if self.cem_porcento:
                            line.write({
                                'valor_total': 2*(line.valor_hora * line.worked_hours),
                                'normal_total': 0,
                                'valor_extra_total': line.valor_hora * (line.worked_hours + almoco),
                                'extra_total': line.worked_hours + almoco,
                                'soma_total': self.extra_total + self.normal_total
                            })
                        else:
                            line.write({
                                'valor_total': line.valor_hora * line.worked_hours,
                                'normal_total': line.worked_hours + almoco - extra,
                                'valor_extra_total': extra * line.valor_hora,
                                'extra_total': extra,
                                'soma_total': self.extra_total + self.normal_total
                            })

#Hora Extra--------------------------------------------------------------
                if extra > 0 and noturna == 0:
                    if almoco < 0:
                        if entrada <= entalm:
                            if self.tipo_contrato == 'clt':
                                if self.cem_porcento:
                                    line.write({
                                        'valor_total': 2*(line.valor_hora * (line.worked_hours + almoco)),
                                        'valor_extra_total': line.valor_hora * (line.worked_hours + almoco),
                                        'extra_total': line.worked_hours + almoco,
                                        'normal_total': 0,
                                        'soma_total': self.extra_total + self.normal_total
                                    })
                                else:
                                    line.write({
                                        'valor_total': line.valor_hora * (line.worked_hours - extra + almoco) + (extra * line.valor_hora * 1.5),
                                        'valor_extra_total': extra * line.valor_hora * 1.5,
                                        'normal_total': line.worked_hours + almoco - extra,
                                        'extra_total': extra,
                                        'soma_total': self.extra_total + self.normal_total

                                    })
                            else:
                                line.write({
                                    'valor_total': line.valor_hora * (line.worked_hours + almoco),
                                    'normal_total': line.worked_hours + almoco - extra,
                                    'valor_extra_total': extra * line.valor_hora,
                                    'extra_total': extra,
                                    'soma_total': self.extra_total + self.normal_total
                                })
                        else:
                            if self.tipo_contrato == 'clt':
                                if self.cem_porcento:
                                    line.write({
                                        'valor_total': 2*(line.valor_hora * (line.worked_hours + almoco)),
                                        'valor_extra_total': line.valor_hora * (extra + almoco),
                                        'extra_total': extra + almoco,
                                        'normal_total': 0,
                                        'soma_total': self.extra_total + self.normal_total
                                    })
                                else:
                                    line.write({
                                        'valor_total': line.valor_hora * (line.worked_hours - extra + almoco) + (extra * line.valor_hora * 1.5),
                                        'valor_extra_total': extra * line.valor_hora * 1.5,
                                        'extra_total': extra,
                                        'normal_total': line.worked_hours - extra + almoco,
                                        'soma_total': self.extra_total + self.normal_total

                                    })
                            else:
                                line.write({
                                    'valor_total': line.valor_hora * line.worked_hours,
                                    'normal_total': line.worked_hours + almoco,
                                    'soma_total': self.extra_total + self.normal_total
                                })
                    else:
                        if self.tipo_contrato == 'clt':
                            if self.cem_porcento:
                                line.write({
                                    'valor_total': 2*(line.valor_hora * line.worked_hours),
                                    'valor_extra_total': line.valor_total / 2,
                                    'extra_total': line.worked_hours + almoco,
                                    'normal_total': 0,
                                    'soma_total': self.extra_total + self.normal_total
                                })
                            else:
                                line.write({
                                        'valor_total': line.valor_hora * (line.worked_hours - extra) + (extra * line.valor_hora * 1.5),
                                        'valor_extra_total': extra * line.valor_hora * 1.5,
                                        'extra_total': extra,
                                        'normal_total': line.worked_hours + almoco - extra,
                                        'soma_total': self.extra_total + self.normal_total
                                    })
                        else:
                            line.write({
                                    'valor_total': line.valor_hora * line.worked_hours,
                                    'normal_total': line.worked_hours + almoco,
                                    'soma_total': self.extra_total + self.normal_total
                                })
#Hora noturna------------------------------------------------------------------------------------------
#hora com periodo noturno
                if noturna > 0 and self.hora_not:
                    if self.tipo_contrato == 'clt':
                        if almoco < 0:
                                line.write({
                                    'valor_total': ((noturna * 1.35 * line.valor_hora) + ((line.worked_hours - noturna + almoco) * line.valor_hora)),
                                })
                        else:
                                line.write({
                                    'valor_total': ((noturna * 1.35 * line.valor_hora) + ((line.worked_hours - noturna) * line.valor_hora)),
                                })
                    else:
                        line.write({
                            'valor_total': (line.worked_hours * line.valor_hora),
                        })

#hora normal + noturno + extra
                if noturna > 0 and extra > 0 and not self.hora_not:
                    if self.tipo_contrato == 'clt':
                        if almoco < 0:
                            line.write({
                                'valor_total': ((noturna * 1.35 * line.valor_hora) + (line.worked_hours - noturna - extra + almoco * line.valor_hora) + (extra * 1.5 * line.valor_hora)),
                                'valor_extra_total':extra * 1.5 * line.valor_hora,
                                'extra_total': extra,
                                'normal_total': line.worked_hours + almoco - extra,
                                'soma_total': self.extra_total + self.normal_total
                            })
                        else:
                            line.write({
                                'valor_total': ((noturna * 1.35 * line.valor_hora) + (line.worked_hours - noturna - extra * line.valor_hora) + (extra * 1.5 * line.valor_hora)),
                                'valor_extra_total': extra * 1.5 * line.valor_hora,
                                'extra_total': extra,
                                'normal_total': line.worked_hours + almoco - extra,
                                'soma_total': self.extra_total + self.normal_total

                            })
                    else:
                        line.write({
                            'valor_total': ((noturna * line.valor_hora) + (line.worked_hours - noturna - extra * line.valor_hora) + (extra * line.valor_hora)),
                            'valor_extra_total': extra * line.valor_hora,
                            'extra_total': extra,
                            'normal_total': line.worked_hours + almoco - extra,
                            'soma_total': self.extra_total + self.normal_total

                        })

class HrReport(models.Model):
    _inherit = "hr.attendance.report"

    normal_total = fields.Float(string='Horas Normais', store=True, readonly=True)
    extra_total = fields.Float(string='Horas Extras', store=True, readonly=True)
    valor_extra_total = fields.Float(string="Valor Extras", store=True, readonly=True)
    valor_total = fields.Float(string='Valor Total', readonly=True, store=True)


    @api.model
    def _select(self):
        return """
                SELECT
                    hra.id,
                    hr_employee.department_id,
                    hra.employee_id,
                    hr_employee.company_id,
                    hra.check_in,
                    hra.worked_hours,
                    hra.normal_total,
                    hra.valor_total,
                    hra.extra_total,
                    hra.valor_extra_total,
                    
                    coalesce(ot.duration, 0) as overtime_hours
            """

    @api.model
    def _from(self):
        return """
                FROM (
                    SELECT
                        id,
                        row_number() over (partition by employee_id, CAST(check_in AS DATE)) as ot_check,
                        employee_id,
                        CAST(check_in
                                at time zone 'utc'
                                at time zone
                                    (SELECT calendar.tz FROM resource_calendar as calendar
                                    INNER JOIN hr_employee as employee ON employee.id = hr_attendance.employee_id
                                    WHERE calendar.id = employee.resource_calendar_id)
                        as DATE) as check_in,
                        worked_hours,
                        normal_total,
                        valor_total,
                        extra_total,
                        valor_extra_total
                    FROM
                        hr_attendance
                    ) as hra
            """

    def _join(self):
        return """
                LEFT JOIN hr_employee ON hr_employee.id = hra.employee_id
                LEFT JOIN hr_attendance_overtime ot
                    ON hra.ot_check = 1
                    AND ot.employee_id = hra.employee_id
                    AND ot.date = hra.check_in
                    AND ot.adjustment = FALSE
            """