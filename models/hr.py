
from odoo import fields, models, api
from datetime import datetime,timedelta, time
import pytz

class HrEmployee(models.Model):
    _inherit = "hr.employee"
    valor_hora = fields.Float(string='Valor Hora', store=True)
    tipo_contrato = fields.Selection([('clt', 'CLT'), ('ht', 'HT'), ('pj', 'PJ'),('estagio','Estágio')], string='Tipo de Contrato', store=True,
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

    def upvalor(self):
        for rec in self:
            rec._valorhora()
            rec._total()

    data_atual = datetime.now()
    ordem_servico = fields.Many2one('ordem.servico', string='Linha Apontamento', store=True, copy=True)
    check_in = fields.Datetime(string="Check In", default=data_atual.replace(hour=10, minute=00, second=00,  microsecond=00, tzinfo=None), required=True)
    check_out = fields.Datetime(string="Check Out", default=data_atual.replace(hour=20, minute=00, second=00, microsecond=00, tzinfo=None), required=True)
    valor_hora = fields.Float(string='Valor Hora', store=True)
    retrabalho = fields.Boolean(string='Retrabalho', store=True)
    ocioso = fields.Boolean(string='Ocioso',store = True)
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

    @api.onchange('employee_id')
    def _onchange_employee_id(self):
        """Atualiza valor_hora quando o funcionário é alterado"""
        if self.employee_id:
            self.valor_hora = self.employee_id.valor_hora

    @api.depends('check_out', 'check_in')
    def _total(self):
        for line in self:
            if not line.check_in or not line.check_out:
                line.normal_total = 0
                line.extra_total = 0
                line.valor_total = 0
                line.valor_extra_total = 0
                line.soma_total = 0
                continue

            # GARANTIR que valor_hora sempre tenha um valor
            if not line.valor_hora and line.employee_id:
                line.valor_hora = line.employee_id.valor_hora

            # Configuração de timezone
            tz = pytz.timezone('America/Sao_Paulo')

            # IMPORTANTE: O Odoo armazena em UTC, precisamos converter para o timezone local
            # Primeiro, garantir que estamos lidando com datetime aware
            if line.check_in.tzinfo is None:
                check_in_utc = pytz.utc.localize(line.check_in)
            else:
                check_in_utc = line.check_in

            if line.check_out.tzinfo is None:
                check_out_utc = pytz.utc.localize(line.check_out)
            else:
                check_out_utc = line.check_out

            # Converter UTC para timezone local
            entrada = check_in_utc.astimezone(tz)
            saida = check_out_utc.astimezone(tz)

            # DEBUG: Verificar as conversões
            print(f"=== CONVERSÃO UTC -> LOCAL ===")
            print(f"UTC - Entrada: {check_in_utc}, Saída: {check_out_utc}")
            print(f"Local - Entrada: {entrada}, Saída: {saida}")
            print(f"=================================")

            # Calcular horas trabalhadas totais
            horas_totais = (saida - entrada).total_seconds() / 3600

            # Criar horários de referência no timezone local
            inicio_jornada = tz.localize(datetime.combine(entrada.date(), time(7, 12)))
            fim_jornada = tz.localize(datetime.combine(entrada.date(), time(17, 0)))
            inicio_almoco = tz.localize(datetime.combine(entrada.date(), time(12, 0)))
            fim_almoco = tz.localize(datetime.combine(entrada.date(), time(13, 0)))

            # Calcular horas dentro do período normal (07:12-17:00)
            inicio_periodo_normal = max(entrada, inicio_jornada)
            fim_periodo_normal = min(saida, fim_jornada)

            if inicio_periodo_normal < fim_periodo_normal:
                horas_normais_bruto = (fim_periodo_normal - inicio_periodo_normal).total_seconds() / 3600
            else:
                horas_normais_bruto = 0

            # Verificar se trabalhou durante horário de almoço
            trabalhou_durante_almoco = (
                    inicio_periodo_normal.time() < time(13, 0) and
                    fim_periodo_normal.time() > time(12, 0) and
                    horas_normais_bruto >= 6
            )

            # Aplicar desconto de almoço apenas se necessário
            if trabalhou_durante_almoco:
                horas_normais = max(0, horas_normais_bruto - 1)
            else:
                horas_normais = horas_normais_bruto

            # Calcular horas extras (total - horas normais brutas)
            horas_extras = max(0, horas_totais - horas_normais_bruto)

            # DEBUG DETALHADO
            print(f"=== CÁLCULO HORAS ===")
            print(f"Entrada local: {entrada.time()}")
            print(f"Saída local: {saida.time()}")
            print(f"Horas totais: {horas_totais}")
            print(f"Horas normais bruto: {horas_normais_bruto}")
            print(f"Horas normais (com almoço): {horas_normais}")
            print(f"Horas extras: {horas_extras}")
            print(f"Trabalhou durante almoço: {trabalhou_durante_almoco}")
            print(f"=====================")

            # Aplicar regras específicas por tipo de contrato
            valor_hora = line.valor_hora

            if line.tipo_contrato == 'clt':
                # CLT: horas extras com adicional
                if line.cem_porcento:
                    valor_extra = horas_extras * valor_hora * 2
                else:
                    valor_extra = horas_extras * valor_hora * 1.5
            else:
                # HT/PJ: sem adicional para horas extras
                valor_extra = horas_extras * valor_hora

            # Calcular valor total
            valor_normal = horas_normais * valor_hora
            valor_total = valor_normal + valor_extra

            # Aplicar adicional noturno se necessário
            if line.hora_not:
                # Calcular horas noturnas (também convertendo para local)
                horas_noturnas = self._calcular_horas_noturnas(entrada, saida, tz)
                adicional_noturno = horas_noturnas * valor_hora * 0.2
                valor_total += adicional_noturno

            # Atualizar valores
            line.update({
                'normal_total': round(horas_normais, 2),
                'extra_total': round(horas_extras, 2),
                'valor_extra_total': round(valor_extra, 2),
                'valor_total': round(valor_total, 2),
                'soma_total': round(horas_normais + horas_extras, 2)
            })

    def _calcular_horas_noturnas(self, entrada, saida, tz):
        """Calcula horas no período noturno (22h às 5h) - já convertido para timezone local"""
        horas_noturnas = 0
        current_date = entrada.date()
        end_date = saida.date()

        while current_date <= end_date:
            inicio_noturno = tz.localize(datetime.combine(current_date, time(22, 0)))
            fim_noturno = tz.localize(datetime.combine(current_date + timedelta(days=1), time(5, 0)))

            inicio_periodo = max(entrada, inicio_noturno)
            fim_periodo = min(saida, fim_noturno)

            if inicio_periodo < fim_periodo:
                horas_noturnas += (fim_periodo - inicio_periodo).total_seconds() / 3600

            current_date += timedelta(days=1)

        return horas_noturnas

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