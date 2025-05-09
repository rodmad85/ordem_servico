
from odoo import fields, models, api
from datetime import datetime,timedelta
import pytz

class HrEmployee(models.Model):
    _inherit = "hr.employee"
    valor_hora = fields.Float(string='Valor Hora', store=True)
    tipo_contrato = fields.Selection([('clt', 'CLT'), ('ht', 'HT'), ('pj', 'PJ')], string='Tipo de Contrato', store=True,
                            copy=True, required=True)

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
                line.update({'os_tree': os})

    @api.onchange('employee_id')
    def _valorhora(self):
        self.valor_hora = self.employee_id.valor_hora


    @api.depends('check_out','check_in')
    def _tree_to_os(self):
        for line in self:
            if line.os_tree:
                line.update({'ordem_servico': self.os_tree})

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
                                    line.update({
                                        'valor_total': 2*(line.valor_hora * (line.worked_hours + almoco)),
                                        'valor_extra_total': line.valor_hora * (line.worked_hours + almoco),
                                        'extra_total': line.worked_hours + almoco,
                                        'normal_total': 0,
                                        'soma_total': self.extra_total + self.normal_total
                                    })
                                else:
                                    line.update({
                                        'valor_total': line.valor_hora * (line.worked_hours - extra + almoco) + (extra * line.valor_hora * 1.5),
                                        'valor_extra_total': extra * line.valor_hora * 1.5,
                                        'normal_total': line.worked_hours + almoco - extra,
                                        'extra_total': extra,
                                        'soma_total': self.extra_total + self.normal_total

                                    })
                            else:
                                line.update({
                                    'valor_total': line.valor_hora * (line.worked_hours + almoco),
                                    'normal_total': line.worked_hours + almoco - extra,
                                    'valor_extra_total': extra * line.valor_hora,
                                    'extra_total': extra,
                                    'soma_total': self.extra_total + self.normal_total
                                })
                        else:
                            if self.tipo_contrato == 'clt':
                                if self.cem_porcento:
                                    line.update({
                                        'valor_total': 2*(line.valor_hora * (line.worked_hours + almoco)),
                                        'valor_extra_total': line.valor_hora * (extra + almoco),
                                        'extra_total': extra + almoco,
                                        'normal_total': 0,
                                        'soma_total': self.extra_total + self.normal_total
                                    })
                                else:
                                    line.update({
                                        'valor_total': line.valor_hora * (line.worked_hours - extra + almoco) + (extra * line.valor_hora * 1.5),
                                        'valor_extra_total': extra * line.valor_hora * 1.5,
                                        'extra_total': extra,
                                        'normal_total': line.worked_hours - extra + almoco,
                                        'soma_total': self.extra_total + self.normal_total

                                    })
                            else:
                                line.update({
                                    'valor_total': line.valor_hora * line.worked_hours,
                                    'normal_total': line.worked_hours + almoco,
                                    'soma_total': self.extra_total + self.normal_total
                                })
                    else:
                        if self.tipo_contrato == 'clt':
                            if self.cem_porcento:
                                line.update({
                                    'valor_total': 2*(line.valor_hora * line.worked_hours),
                                    'valor_extra_total': line.valor_total / 2,
                                    'extra_total': line.worked_hours + almoco,
                                    'normal_total': 0,
                                    'soma_total': self.extra_total + self.normal_total
                                })
                            else:
                                line.update({
                                        'valor_total': line.valor_hora * (line.worked_hours - extra) + (extra * line.valor_hora * 1.5),
                                        'valor_extra_total': extra * line.valor_hora * 1.5,
                                        'extra_total': extra,
                                        'normal_total': line.worked_hours + almoco - extra,
                                        'soma_total': self.extra_total + self.normal_total
                                    })
                        else:
                            line.update({
                                    'valor_total': line.valor_hora * line.worked_hours,
                                    'normal_total': line.worked_hours + almoco,
                                    'soma_total': self.extra_total + self.normal_total
                                })
#Hora noturna------------------------------------------------------------------------------------------
#hora com periodo noturno
                if noturna > 0 and self.hora_not:
                    if self.tipo_contrato == 'clt':
                        if almoco < 0:
                                line.update({
                                    'valor_total': ((noturna * 1.35 * line.valor_hora) + ((line.worked_hours - noturna + almoco) * line.valor_hora)),
                                })
                        else:
                                line.update({
                                    'valor_total': ((noturna * 1.35 * line.valor_hora) + ((line.worked_hours - noturna) * line.valor_hora)),
                                })
                    else:
                        line.update({
                            'valor_total': (line.worked_hours * line.valor_hora),
                        })

#hora normal + noturno + extra
                if noturna > 0 and extra > 0 and not self.hora_not:
                    if self.tipo_contrato == 'clt':
                        if almoco < 0:
                            line.update({
                                'valor_total': ((noturna * 1.35 * line.valor_hora) + (line.worked_hours - noturna - extra + almoco * line.valor_hora) + (extra * 1.5 * line.valor_hora)),
                                'valor_extra_total':extra * 1.5 * line.valor_hora,
                                'extra_total': extra,
                                'normal_total': line.worked_hours + almoco - extra,
                                'soma_total': self.extra_total + self.normal_total
                            })
                        else:
                            line.update({
                                'valor_total': ((noturna * 1.35 * line.valor_hora) + (line.worked_hours - noturna - extra * line.valor_hora) + (extra * 1.5 * line.valor_hora)),
                                'valor_extra_total': extra * 1.5 * line.valor_hora,
                                'extra_total': extra,
                                'normal_total': line.worked_hours + almoco - extra,
                                'soma_total': self.extra_total + self.normal_total

                            })
                    else:
                        line.update({
                            'valor_total': ((noturna * line.valor_hora) + (line.worked_hours - noturna - extra * line.valor_hora) + (extra * line.valor_hora)),
                            'valor_extra_total': extra * line.valor_hora,
                            'extra_total': extra,
                            'normal_total': line.worked_hours + almoco - extra,
                            'soma_total': self.extra_total + self.normal_total

                        })
