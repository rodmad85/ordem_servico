from odoo import fields, models, api


class OsResumo(models.Model):
    _name = 'os.resumo'
    _description = 'Resumo de Ordem de Serviço'

    name = fields.Char(string='Nome', default='Resumo de OS')
    hprevista = fields.Float(string='Horas Previstas')
    hrealizada = fields.Float(string='Horas Realizadas')
    hcmes = fields.Float(string='Horas Consumidas no mês')
    hdmes = fields.Float(string='Horas Disponíveis no mês')
    cprevista = fields.Float(string='Compras Previstas')
    crealizada = fields.Float(string='Compras Realizadas')
    diff_horas = fields.Float(string='Saldo Horas')
    percentcompra = fields.Float(string='Percentual de Compra')
    compra_valor_aberto = fields.Float(string='Valor Aberto de Compra')

    linha_ids = fields.One2many('os.resumo.linha', 'resumo_id', string='Linhas do Resumo')

    @api.model
    def create(self, vals):
        record = super().create(vals)
        record._carregar_dados()
        return record

    def _carregar_dados(self):
        """Preenche totais e linhas com OS abertas/parciais"""
        self.ensure_one()
        self.linha_ids.unlink()

        abertas = self.env['os.fechamento'].search([('state', '=', 'aberta')])
        parciais = self.env['os.fechamento'].search([('state', '=', 'parcial')])
        todas = abertas + parciais

        hprevista = hrealizada = cprevista = crealizada = diff_horas = 0.0
        linhas = []

        for rec in todas:
            rec.updt()
            linhas.append((0, 0, {'fechamento_id': rec.id}))

            hprevista += rec.horas_prevista or 0.0
            hrealizada += rec.horas_real or 0.0
            cprevista += rec.mp_prevista or 0.0
            crealizada += rec.mp_real or 0.0
            diff_horas += rec.horas_resultado or 0.0

        self.write({
            'linha_ids': linhas,
            'hprevista': hprevista,
            'hrealizada': hrealizada,
            'cprevista': cprevista,
            'crealizada': crealizada,
            'diff_horas': diff_horas,
            'percentcompra': (crealizada / cprevista * 100) if cprevista else 0.0,
            'compra_valor_aberto': (cprevista - crealizada) if cprevista else 0.0,
        })

    @api.model
    def default_get(self, fields_list):
        res = super().default_get(fields_list)

        abertas = self.env['os.fechamento'].search([('state', '=', 'aberta')])
        parciais = self.env['os.fechamento'].search([('state', '=', 'parcial')])
        todas = abertas + parciais
        todas = todas.sorted(key=lambda f: f.data_entrega or fields.Date.today())

        hprevista = hrealizada = cprevista = crealizada = diff_horas = 0.0
        linhas = []

        for rec in todas:
            rec.updt()
            linhas.append((0, 0, {'fechamento_id': rec.id}))

            hprevista += rec.horas_prevista or 0.0
            hrealizada += rec.horas_real or 0.0
            cprevista += rec.mp_prevista or 0.0
            crealizada += rec.mp_real or 0.0
            diff_horas += rec.horas_resultado or 0.0

        res.update({
            'linha_ids': linhas,
            'hprevista': hprevista,
            'hrealizada': hrealizada,
            'cprevista': cprevista,
            'crealizada': crealizada,
            'diff_horas': diff_horas,
            'percentcompra': (crealizada / cprevista * 100) if cprevista else 0.0,
            'compra_valor_aberto': (cprevista - crealizada) if cprevista else 0.0,
        })

        return res

    def print_report(self):
        self.ensure_one()
        return self.env.ref('ordem_servico.action_report_os_resumo').report_action(self.linha_ids)

    def action_ver_linhas_group(self):
        self.ensure_one()
        return {
            'name': 'Resumo por Cliente',
            'type': 'ir.actions.act_window',
            'res_model': 'os.resumo.linha',
            'groups': 'ordem_admin',
            'view_mode': 'tree',
            'domain': [('resumo_id', '=', self.id)],
            'context': {'group_by': 'cliente'},
            'target': 'current',
        }


class OsResumoLinha(models.Model):
    _name = 'os.resumo.linha'
    _description = 'Resumo de OS em Aberto e Parcial'
    _order = 'data_entrega asc'

    resumo_id = fields.Many2one('os.resumo', string='Resumo')
    fechamento_id = fields.Many2one('os.fechamento', string='Fechamento', readonly=True)

    os_id = fields.Char(string='OS', related='fechamento_id.name', readonly=True)
    cliente = fields.Char(string='Cliente', related='fechamento_id.cliente.name', readonly=True, store=True)
    valor_pedido = fields.Monetary(string='Valor Pedido', related='fechamento_id.valor_pedido', readonly=True, store=True)
    data_entrega = fields.Date(string='Data Entrega', related='fechamento_id.data_entrega', readonly=True, store=True)
    mp_prevista = fields.Monetary(string='MP Prevista', related='fechamento_id.mp_prevista', readonly=True, store=True)
    mp_real = fields.Monetary(string='MP Real', related='fechamento_id.mp_real', readonly=True, store=True)
    progress_compra = fields.Float(string='% Compras', related='fechamento_id.progress_compra', digits=(16, 2), readonly=True)

    diff_compra = fields.Monetary(string='Diferença Compras', compute='_compute_diffs', readonly=True, store=True)
    horas_prevista = fields.Float(string='Horas Previstas', related='fechamento_id.horas_prevista', readonly=True, store=True)
    horas_real = fields.Float(string='Horas Reais', related='fechamento_id.horas_real', readonly=True, store=True)
    perc_horas = fields.Float(string='% Horas', compute='_compute_diffs', readonly=True, store=True)
    diff_horas = fields.Float(string='Diferença Horas', compute='_compute_diffs', readonly=True, store=True)

    currency_id = fields.Many2one(related='fechamento_id.currency_id', readonly=True)

    @api.depends('mp_prevista', 'mp_real', 'horas_prevista', 'horas_real')
    def _compute_diffs(self):
        for rec in self:
            rec.diff_compra = (rec.mp_prevista or 0.0) - (rec.mp_real or 0.0)
            rec.diff_horas = (rec.horas_prevista or 0.0) - (rec.horas_real or 0.0)
            rec.perc_horas = (rec.horas_real / rec.horas_prevista * 100) if rec.horas_prevista else 0.0
            rec.progress_compra = (rec.mp_real / rec.mp_prevista * 100) if rec.horas_prevista else 0.0
