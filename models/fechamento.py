
from odoo import fields, models, api
from datetime import datetime

class OsFechamento(models.Model):
    _name="os.fechamento"
    _description = "Fechamento"
    _rec_name = 'name'

    def updt(self):
        for rec in self:
            rec._amount_tc_prevista()
            rec._amount_mp_prevista()
            rec._amount_mo_prevista()
            rec._amount_horas_prevista()
            rec._compute_compra()
            rec._amount_total_orcado()
            rec._amount_imposto_real()
            rec._amount_mp_real()
            rec._amount_consumidos()
            rec._amount_mo_real()
            rec._amount_valor_horas()
            rec._amount_valor_extra()
            rec._amount_horas_real()
            rec._amount_horas_retrabalho()
            rec._amount_extra_real()
            rec._amount_horas_retrabalho()
            rec._amount_horas_total()
            rec._amount_valor_horas_retrabalho()
            rec._amount_horas_resultado()
            rec._amount_mo_resultado()
            rec._amount_mp_resultado()
            rec._amount_total_gasto()
            rec._amount_valor_pedido()
            rec._getcusto()

    os_ids = fields.Many2one('ordem.servico', string='Ordem de Serviço', required=True)
    cliente = fields.Many2one('res.partner', 'Company', store=True,
                              related='os_ids.pedido_venda.partner_id.parent_id')
    empresa = fields.Many2one('res.company', string='Empresa', related='os_ids.empresa')
    data_base = fields.Date(string='Data Base', store=True, copy=True, related='os_ids.data_base')
    data_entrega = fields.Date(string='Data Entrega', store=True, copy=True, related='os_ids.data_entrega')
    entrega_efetiva = fields.Date(string='Entrega Efetiva', store=True, copy=True, related='os_ids.entrega_efetiva')
    posicao = fields.Many2one(related='os_ids.posicao')
    condicao = fields.Many2one(related='os_ids.pedido_venda.payment_term_id')
    valor_pedido = fields.Monetary(string='Valor da Venda', store=True, compute='_amount_valor_pedido')
    state = fields.Selection(
        [('draft', 'Provisória'), ('aberta', 'Aberta'), ('parcial', 'Parcialmente Entregue'),
         ('concluida', 'Concluida'), ('cancel', 'Cancelada')],
        string='Status', store=True, copy=True, related='os_ids.state')
    status_fat = fields.Selection(
        [('nao', 'Não Faturada'), ('parcial', 'Faturada Parcialmente'), ('faturada', 'Faturada'),
         ('paga', 'Paga')], string='Faturamento', store=True, copy=True, related='os_ids.status_fat')

    currency_id = fields.Many2one('res.currency', default=lambda self: self.env.company.currency_id, readonly=True)
    name = fields.Char(string='Nome', store=True, related='os_ids.name')
    horas_prevista = fields.Float(string='Horas Previstas', store=True, copy=True, compute='_amount_horas_prevista', group_operator='sum')
    tc_prevista = fields.Monetary(string='Terceiros Previsto', store=True, compute='_amount_tc_prevista', group_operator='sum')
    mo_prevista = fields.Monetary(string='MO Prevista', store=True, compute='_amount_mo_prevista', group_operator='sum')
    mp_prevista = fields.Monetary(string='MP Prevista', store=True, compute='_amount_mp_prevista', group_operator='sum')
    comissao = fields.Monetary(string='Comissão', store=True, group_operator='sum')

    custo_fixo = fields.Float(string='Custo Fixo %', store=True, copy=True)
    valor_custofixo = fields.Monetary(string='Custo Fixo', store=True, copy=True)
    margem = fields.Float(string='Margem', store=True, copy=True)

    mo_real = fields.Monetary(string='Valor Total MO', store=True, copy=True, compute='_amount_mo_real', group_operator='sum')
    mp_real = fields.Monetary(string='Compras Real', store=True, copy=True, compute='_amount_mp_real', group_operator='sum')
    consumidos = fields.Many2many(related='os_ids.consumidos')
    consumidos_total = fields.Monetary('Consumido', compute='_amount_consumidos')
    comissao_real = fields.Monetary(string='Comissão Real', store=True, copy=True, group_operator='sum')
    imposto_real = fields.Float(string='Imposto Real', store=True, copy=True, group_operator='sum', compute='_amount_imposto_real')
    progress_compra = fields.Float(string='% Compras', store=True, compute='_compute_compra')
    extra_real = fields.Float(string='Horas Extras', store=True, compute='_amount_extra_real', group_operator='sum')
    horas_real = fields.Float(string='Horas Reais', store=True, copy=True, compute='_amount_horas_real', group_operator='sum')
    horas_retrabalho = fields.Float(string='Horas Retrabalho', store=True, copy=True, compute='_amount_horas_retrabalho', group_operator='sum')
    horas_total = fields.Float(string='Horas Reais', store=True, copy=True, compute='_amount_horas_total', group_operator='sum')
    valor_horas = fields.Float(string='Valor Horas', store=True, copy=True, compute='_amount_valor_horas', group_operator='sum')
    valor_horas_retrabalho = fields.Monetary(string='Valor Horas Retrabalho', store=True, copy=True,
                                          compute='_amount_valor_horas_retrabalho', group_operator='sum')
    valor_extra = fields.Float(string='Valor Extra', store=True, copy=True, compute='_amount_valor_extra', group_operator='sum')

    horas_resultado = fields.Float(string='Horas', store=True, copy=True, compute='_amount_horas_resultado', help='Horas Reais - Horas Previstas', group_operator='sum')
    mo_resultado = fields.Monetary(string='Valor Horas', store=True, copy=True, compute='_amount_mo_resultado', help='Horas Reais - Horas Previstas', group_operator='sum')
    mp_resultado = fields.Monetary(string='MP/Terceiros', store=True, copy=True, compute='_amount_mp_resultado', help='(MP Prevista + Terceiros Previsto) - (MP Real + Terceiros Real)', group_operator='sum')
    impostos_resultado = fields.Monetary(string='Impostos', store=True, copy=True, compute='_amount_imposto_real')
    impostos_resultado_percen = fields.Float(string='Impostos %', store=True, copy=True)

    atraso = fields.Integer('Atraso', compute='_compute_atraso')

    orcado = fields.Monetary(string='Orçado', store=True, copy=True, compute='_amount_total_orcado', group_operator='sum')
    total_gasto = fields.Monetary(string='Total de Gastos', store=True, copy=True, compute='_amount_total_gasto', help='Total de MP Real + Total de MO Real + Comissao + Impostos', group_operator='sum')
    orcado_gasto = fields.Monetary(string='Orçado X Gastos', store=True, copy=True)
    resultado = fields.Monetary(string='Resultado', store=True, copy=True, readonly=True, help='Valor de Venda - Total de Gastos', compute='_amount_total_gasto', group_operator='sum')
    resultado_percen = fields.Float(string='Resultado %', store=True, copy=True, readonly=True, compute='_amount_total_gasto', group_operator='avg')


    def _compute_atraso(self):
        for rec in self:
            if rec.data_entrega and rec.entrega_efetiva:
                if rec.data_entrega < rec.entrega_efetiva:
                    atraso = (rec.entrega_efetiva - rec.data_entrega).days
                    rec.atraso=atraso
                else:
                    rec.atraso = 0
            else:
                rec.atraso = 0


    def _getcusto(self):
        config = self.env['ir.config_parameter'].sudo()
        custo = config.get_param('orcamento.custo_fixo')

        self.custo_fixo=custo
        self.valor_custofixo = self.valor_pedido * (float(self.custo_fixo) / 100)

    @api.depends('os_ids.state')
    def _amount_tc_prevista(self):
        for rec in self:
            total = sum(rec.os_ids.pedido_venda.mapped('terceiros')) if rec.os_ids.pedido_venda else 0
            rec.tc_prevista = total

    @api.depends('os_ids.state')
    def _amount_mp_prevista(self):
        for rec in self:
            total = sum(rec.os_ids.pedido_venda.mapped('materia_prima')) if rec.os_ids.pedido_venda else 0
            rec.mp_prevista = total

    @api.depends('os_ids.state')
    def _amount_mo_prevista(self):
        for rec in self:
            total = sum(rec.os_ids.pedido_venda.mapped('valor_horas')) if rec.os_ids.pedido_venda else 0
            rec.mo_prevista = total

    @api.depends('os_ids.state')
    def _amount_horas_prevista(self):
        for rec in self:
            total = sum(rec.os_ids.pedido_venda.mapped('horas_mo')) if rec.os_ids.pedido_venda else 0
            rec.horas_prevista = total

    @api.depends('os_ids.state')
    def _amount_valor_pedido(self):
        for rec in self:
            total = sum(rec.os_ids.pedido_venda.mapped('amount_total')) if rec.os_ids.pedido_venda else 0
            rec.valor_pedido = total

    @api.depends('os_ids.state')
    def _compute_compra(self):
        for rec in self:
            mpprev = sum(rec.os_ids.pedido_venda.mapped('materia_prima')) if rec.os_ids.pedido_venda else 0
            mpreal = sum(rec.os_ids.pedidos_compra.mapped('price_total')) if rec.os_ids.pedidos_compra else 0
            if mpprev:
                if mpreal:
                    total = mpreal / mpprev
                    rec.progress_compra = total * 100

    @api.depends('os_ids.state')
    def _amount_total_orcado(self):
        for rec in self:
            mpprev = sum(rec.os_ids.pedido_venda.mapped('materia_prima')) if rec.os_ids.pedido_venda else 0
            moprev = sum(rec.os_ids.pedido_venda.mapped('valor_horas')) if rec.os_ids.pedido_venda else 0
            tcprev = sum(rec.os_ids.pedido_venda.mapped('terceiros')) if rec.os_ids.pedido_venda else 0
            rec.orcado = mpprev + moprev + tcprev


    @api.depends('os_ids.state')
    def _amount_imposto_real(self):
        for rec in self:
            if rec.posicao:
                if rec.entrega_efetiva:
                    entrega = datetime.strftime(self.entrega_efetiva, '%m/%Y')
                    pedi = rec.os_ids.pedido_venda
                    if len(pedi) > 1:
                        posi = pedi[0].fiscal_position_id.id
                    else:
                        posi = pedi.fiscal_position_id.id
                    posicoes = self.env["os.impostos.line"].search([('fiscal_position', '=', posi)])
                    for i in posicoes:
                        dt = datetime.strftime(i.mes, '%m/%Y')
                        if dt == entrega:
                            self.imposto_real = i.percentual
                            self.posicao = self.env["l10n_br_fiscal.operation"].browse(posi)

                    rec.write({'imposto_real': self.imposto_real / 100,
                               'impostos_resultado': rec.valor_pedido * (self.imposto_real / 100)})

    @api.depends('os_ids.state')

    def _amount_consumidos(self):
        for rec in self:
            total = sum(rec.os_ids.consumidos.mapped('valor_con')) if rec.os_ids.consumidos else 0
            rec.consumidos_total = total

    def _amount_mp_real(self):
        for rec in self:
            total = sum(rec.os_ids.pedidos_compra.filtered(lambda l: l.state == 'purchase').mapped('price_total')) if rec.os_ids.pedidos_compra else 0
            rec.mp_real = total + rec.consumidos_total



    @api.depends('os_ids.state')
    def _amount_mo_real(self):
        for rec in self:
            total = sum(rec.os_ids.apontamento.mapped('valor_total')) if rec.os_ids.apontamento else 0
            rec.mo_real = total

    @api.depends('os_ids.state')
    def _amount_valor_horas(self):
        for rec in self:
            total = sum(rec.os_ids.apontamento.filtered(lambda l: l.retrabalho == False).mapped('soma_total')) if rec.os_ids.apontamento else 0
            rec.horas_real = total

    @api.depends('os_ids.state')
    def _amount_horas_real(self):
        for rec in self:
            total = sum(rec.os_ids.apontamento.filtered(lambda l: l.retrabalho == False).mapped('normal_total')) if rec.os_ids.apontamento else 0
            rec.horas_real = total

    @api.depends('os_ids.state')
    def _amount_extra_real(self):
        for rec in self:
            total = sum(rec.os_ids.apontamento.filtered(lambda l: l.retrabalho == False).mapped('extra_total')) if rec.os_ids.apontamento else 0
            rec.extra_real = total
    @api.depends('os_ids.state')
    def _amount_horas_retrabalho(self):
        for rec in self:
            total = sum(rec.os_ids.apontamento.filtered(lambda l: l.retrabalho).mapped('soma_total')) if rec.os_ids.apontamento else 0
            rec.horas_retrabalho = total

    @api.depends('os_ids.state')
    def _amount_horas_total(self):
        for rec in self:

            total = sum(rec.os_ids.apontamento.mapped('soma_total')) if rec.os_ids.apontamento else 0
            rec.horas_total = total

    @api.depends('os_ids.state')
    def _amount_valor_horas_retrabalho(self):
        for rec in self:
            total = sum(rec.os_ids.apontamento.filtered(lambda l: l.retrabalho).mapped('valor_total')) if rec.os_ids.apontamento else 0
            rec.valor_horas_retrabalho = total

    @api.depends('os_ids.state')
    def _amount_valor_extra(self):
        for rec in self:
            total = sum(rec.os_ids.apontamento.filtered(lambda l: l.retrabalho == False).mapped('valor_extra_total')) if rec.os_ids.apontamento else 0
            rec.valor_extra = total
    @api.depends('os_ids.state')
    def _amount_horas_resultado(self):
        for rec in self:
            real = sum(rec.os_ids.apontamento.mapped('soma_total')) if rec.os_ids.apontamento else 0
            previ = sum(rec.os_ids.pedido_venda.mapped('horas_mo')) if rec.os_ids.pedido_venda else 0
            rec.horas_resultado = previ - real

    @api.depends('os_ids.state')
    def _amount_mo_resultado(self):
        for rec in self:
            real = rec.mo_real
            prev = sum(rec.os_ids.pedido_venda.mapped('valor_horas')) if rec.os_ids.pedido_venda else 0
            rec.mo_resultado = prev - real

    @api.depends('os_ids.state')
    def _amount_mp_resultado(self):
        for rec in self:

            rec.mp_resultado = rec.mp_prevista - rec.mp_real

    @api.depends('os_ids.state')
    def _amount_total_gasto(self):
        for rec in self:
            mp = sum(rec.os_ids.pedidos_compra.mapped('price_total')) if rec.os_ids.pedidos_compra else 0
            mo = sum(rec.os_ids.apontamento.mapped('valor_total')) if rec.os_ids.apontamento else 0
            valor_pedido = sum(rec.os_ids.pedido_venda.mapped('amount_total')) if rec.os_ids.pedido_venda else 0

            gasto = mp + mo + rec.comissao + rec.impostos_resultado + rec.valor_custofixo + rec.consumidos_total + rec.valor_custofixo
            diferenca = rec.orcado - gasto
            if gasto > 0 and valor_pedido> 0:
                resul = (valor_pedido - gasto) / valor_pedido
            else:
                resul = 100
            rec.write({'resultado' : valor_pedido - gasto,'total_gasto':gasto, 'orcado_gasto': diferenca, 'resultado_percen': resul})
    @api.model
    def _mensagens(self):
        for rec in self:
            ids = rec.message_ids.ids
            if ids:
                rec.ultimamsg = rec.message_ids[0].body

    def _users(self):
        for rec in self:
            msg_ids = rec.message_ids

            if msg_ids:
                ult = msg_ids[0].author_id.id
                ult = self.env['res.partner'].browse(ult).name
                if ult:
                    rec.ultiuser = ult



