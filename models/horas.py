# -*- coding: utf-8 -*-
from odoo import fields, models, tools,api
from datetime import datetime


class OsHoras(models.Model):
    _name = 'os.horas'
    _description = 'Relatorio de Horas'
    _auto = False

    currency_id = fields.Many2one('res.currency', default=lambda self: self.env.company.currency_id, readonly=True)
    totalhoras = fields.Float(string='Total de Horas')
    previstas = fields.Float(string='Horas Previstas')
    vprevistas = fields.Monetary(string='Valor Horas Previstas')
    normal = fields.Float(string='Horas Normais')
    vnormal = fields.Monetary(string='Valor Horas Normais')
    extra = fields.Float(string='Horas Extras')
    retrabalho = fields.Float(string='Retrabalho')
    vretrabalho = fields.Monetary(string='Valor Retrabalho')
    utilizadas = fields.Float(string='Total Horas Utilizadas')
    vutilizadas = fields.Monetary(string='Valor Total Utilizadas')
    disponiveis = fields.Float(string='Horas Disponíveis')
    periodo = fields.Datetime(string="Data")

    @property
    def _get_query(self):
        return """CREATE OR REPLACE VIEW %s AS (
                WITH hr_summary AS (
            SELECT
                DATE_TRUNC('month', check_in + INTERVAL '3 hour') AS x_data_check_in,
                SUM(CASE WHEN retrabalho THEN normal_total ELSE 0 END) AS x_total_retrabalho,
                SUM(extra_total) AS x_total_extra,
                SUM(normal_total) AS x_total_normal,
                SUM(valor_total) AS x_valor_total
            FROM 
                hr_attendance
            GROUP BY 
                DATE_TRUNC('month', check_in + INTERVAL '3 hour')
        ),
        sale_summary AS (
            SELECT 
                DATE_TRUNC('month', date_order + INTERVAL '3 hour') AS x_month_date_order,
                SUM(horas_mo) AS x_total_mo_horas,
                SUM(valor_horas) AS x_valor_mo_horas
            FROM 
                sale_order
            WHERE 
                state = 'sale'
            GROUP BY 
                DATE_TRUNC('month', date_order + INTERVAL '3 hour')
        )
        SELECT 
            hr_summary.x_data_check_in AS periodo,
            COALESCE(hr_summary.x_total_retrabalho, 0) AS retrabalho,
            COALESCE(hr_summary.x_total_extra, 0) AS extra,
            COALESCE(hr_summary.x_total_normal, 0) AS normal,
            COALESCE(hr_summary.x_valor_total, 0) AS vnormal,
            COALESCE(sale_summary.x_total_mo_horas, 0) AS previstas,
            COALESCE(sale_summary.x_valor_mo_horas, 0) AS vprevistas
        FROM 
            hr_summary
        LEFT JOIN sale_summary ON hr_summary.x_data_check_in = sale_summary.x_month_date_order
        ORDER BY
            hr_summary.x_data_check_in DESC)
        """

    def init(self):
        tools.drop_view_if_exists(self.env.cr, self._table)
        self._cr.execute(
            """CREATE OR REPLACE VIEW %s AS (
                WITH hr_summary AS (
            SELECT 
                DATE_TRUNC('month', check_in + INTERVAL '3 hour') AS x_data_check_in,
                SUM(CASE WHEN retrabalho THEN normal_total ELSE 0 END) AS x_total_retrabalho,
                SUM(extra_total) AS x_total_extra,
                SUM(normal_total) AS x_total_normal,
                SUM(valor_total) AS x_valor_total
            FROM 
                hr_attendance
            GROUP BY 
                DATE_TRUNC('month', check_in + INTERVAL '3 hour')
            ),
            sale_summary AS (
                SELECT 
                    DATE_TRUNC('month', date_order + INTERVAL '3 hour') AS x_month_date_order,
                    SUM(horas_mo) AS x_total_mo_horas,
                    SUM(valor_horas) AS x_valor_mo_horas
                FROM 
                    sale_order
                WHERE 
                    state = 'sale'
                GROUP BY 
                    DATE_TRUNC('month', date_order + INTERVAL '3 hour')
            )
            SELECT 
                hr_summary.x_data_check_in AS periodo,
                COALESCE(hr_summary.x_total_retrabalho, 0) AS retrabalho,
                COALESCE(hr_summary.x_total_extra, 0) AS extra,
                COALESCE(hr_summary.x_total_normal, 0) AS normal,
                COALESCE(hr_summary.x_valor_total, 0) AS vnormal,
                COALESCE(sale_summary.x_total_mo_horas, 0) AS previstas,
                COALESCE(sale_summary.x_valor_mo_horas, 0) AS vprevistas
            FROM 
                hr_summary
            LEFT JOIN sale_summary ON hr_summary.x_data_check_in = sale_summary.x_month_date_order
            ORDER BY
                hr_summary.x_data_check_in DESC
            )
        """
            % self._table
        )


    def _previstas(self):
        osabertas = self.env["ordem.servico"].search([('state', '=', 'aberta')])
        if osabertas:
            for rec in osabertas:
                self.write({'previstas': sum(
                    rec.osabertas.pedido_venda.mapped('horas_mo')) if rec.osabertas.pedido_venda else 0})
                self.write({'vprevistas': sum(
                    rec.osabertas.pedido_venda.mapped('valor_horas')) if rec.osabertas.pedido_venda else 0})
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
        else:
            self.utilizadas = 0


        #self._previstas()

    # def create(self):
    #     for rec in self:
    #         result = super(OsHoras, self).create(vals)
    #         return result
