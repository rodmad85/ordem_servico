from odoo import fields, models, api
from datetime import datetime


class OsFechamento(models.Model):
    _name = "os.fechamento"
    _description = "Fechamento"
    _rec_name = 'name'

    def updt(self):
        for rec in self:
            rec._getcusto()
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
            rec._amount_valor_pedido()


    os_ids = fields.Many2one('ordem.servico', string='Ordem de Serviço', required=True)
    cliente = fields.Many2one('res.partner', 'Company', 
                              related='os_ids.pedido_venda.partner_id.parent_id')
    empresa = fields.Many2one('res.company', string='Empresa', related='os_ids.empresa')
    data_base = fields.Date(string='Data Base',  copy=True, related='os_ids.data_base')
    data_entrega = fields.Date(string='Data Entrega',  copy=True, related='os_ids.data_entrega')
    entrega_efetiva = fields.Date(string='Entrega Efetiva',  copy=True, related='os_ids.entrega_efetiva')
    posicao = fields.Many2one(related='os_ids.posicao')
    condicao = fields.Many2one(related='os_ids.pedido_venda.payment_term_id')
    valor_pedido = fields.Monetary(string='Valor da Venda',  compute='_amount_valor_pedido')
    state = fields.Selection(
        [('draft', 'Provisória'), ('aberta', 'Aberta'), ('parcial', 'Parcialmente Entregue'),
         ('concluida', 'Concluida'), ('cancel', 'Cancelada')],
        string='Status',  copy=True, related='os_ids.state')
    status_fat = fields.Selection(
        [('nao', 'Não Faturada'), ('parcial', 'Faturada Parcialmente'), ('faturada', 'Faturada'),
         ('paga', 'Paga')], string='Faturamento',  copy=True, related='os_ids.status_fat')

    currency_id = fields.Many2one('res.currency', default=lambda self: self.env.company.currency_id, readonly=True)
    name = fields.Char(string='Nome',  related='os_ids.name')
    horas_prevista = fields.Float(string='Horas Previstas', copy=True, compute='_amount_horas_prevista',
                                  group_operator='sum')
    tc_prevista = fields.Monetary(string='Terceiros Previsto', compute='_amount_tc_prevista',
                                  group_operator='sum')
    mo_prevista = fields.Monetary(string='MO Prevista', store=False, compute='_amount_mo_prevista', group_operator='sum')
    mp_prevista = fields.Monetary(string='MP Prevista', store=False, compute='_amount_mp_prevista', group_operator='sum')
    comissao = fields.Monetary(string='Comissão',  group_operator='sum')

    custo_fixo = fields.Float(string='Custo Fixo %',  copy=True, compute='_getcusto')
    valor_custofixo = fields.Monetary(string='Custo Fixo',  copy=True)
    margem = fields.Float(string='Margem',  copy=True)

    mo_real = fields.Monetary(string='Valor Total MO', copy=True, store=False, compute='_amount_mo_real',
                              group_operator='sum')
    mp_real = fields.Monetary(string='Compras Real', copy=True, store=False, compute='_amount_mp_real',
                              group_operator='sum')
    consumidos = fields.Many2many(related='os_ids.consumidos')
    comprados = fields.Many2many(related='os_ids.pedidos_compra')
    consumidos_total = fields.Monetary('Consumido', store=False, compute='_amount_consumidos')
    comissao_real = fields.Monetary(string='Comissão Real',  copy=True, group_operator='sum')
    imposto_real = fields.Float(string='Imposto Real', copy=True, group_operator='sum',
                                )
    progress_compra = fields.Float(string='% Compras', store=False, compute='_compute_compra')
    extra_real = fields.Float(string='Horas Extras', store=False, compute='_amount_extra_real', group_operator='sum')
    horas_real = fields.Float(string='Horas Reais',  copy=True, store=False, compute='_amount_horas_real',
                              group_operator='sum')
    horas_retrabalho = fields.Float(string='Horas Retrabalho',  copy=True, store=False,
                                    compute='_amount_horas_retrabalho', group_operator='sum')
    horas_total = fields.Float(string='Horas Reais',  copy=True, store=False, compute='_amount_horas_total',
                               group_operator='sum')
    valor_horas = fields.Float(string='Valor Horas',  copy=True, store=False, compute='_amount_valor_horas',
                               group_operator='sum')
    valor_horas_retrabalho = fields.Monetary(string='Valor Horas Retrabalho',  copy=True,
                                             store=False, compute='_amount_valor_horas_retrabalho', group_operator='sum')
    valor_extra = fields.Float(string='Valor Extra',  copy=True, store=False, compute='_amount_valor_extra',
                               group_operator='sum')

    horas_resultado = fields.Float(string='Horas',  copy=True, store=False, compute='_amount_horas_resultado',
                                   help='Horas Reais - Horas Previstas', group_operator='sum')
    mo_resultado = fields.Monetary(string='Valor Horas',  copy=True, store=False, compute='_amount_mo_resultado',
                                   help='Horas Reais - Horas Previstas', group_operator='sum')
    mp_resultado = fields.Monetary(string='MP/Terceiros',  copy=True, store=False, compute='_amount_mp_resultado',
                                   help='(MP Prevista + Terceiros Previsto) - (MP Real + Terceiros Real) - Somente produtos recebidos',
                                   group_operator='sum')
    impostos_resultado = fields.Monetary(string='Impostos',  copy=True)
    impostos_resultado_percen = fields.Float(string='Impostos %',  copy=True)

    atraso = fields.Integer('Atraso', store=False, compute='_compute_atraso')

    orcado = fields.Monetary(string='Orçado',  copy=True, store=False, compute='_amount_total_orcado',
                             group_operator='sum', help='MP Prevista + Valor Horas Prevista + Terceiros Previsto')
    total_gasto = fields.Monetary(string='Total de Gastos', copy=True, store=False, compute='_amount_total_gasto',
                                  help='Total de MP Real + Total de MO Real + Comissao + Custo Fixo + Impostos',
                                  group_operator='sum')
    orcado_gasto = fields.Monetary(string='Orçado X Gastos',  copy=True, help='Orçado - Gastos (sem custo fixo)')
    resultado = fields.Monetary(string='Resultado', copy=True, readonly=True,
                                help='Valor de Venda - Total de Gastos', store=False, compute='_amount_total_gasto',
                                group_operator='sum')
    resultado_percen = fields.Float(string='Resultado %', copy=True, readonly=True,
                                    store=False, compute='_amount_total_gasto', group_operator='avg')
    @api.depends('data_entrega','entrega_efetiva')
    def _compute_atraso(self):
        for rec in self:
            if rec.data_entrega and rec.entrega_efetiva:
                if rec.data_entrega < rec.entrega_efetiva:
                    atraso = (rec.entrega_efetiva - rec.data_entrega).days
                    rec.atraso = atraso
                else:
                    rec.atraso = 0
            else:
                rec.atraso = 0

    def _getcusto(self):
        config = self.env['ir.config_parameter'].sudo()
        custo = config.get_param('orcamento.custo_fixo')
        for rec in self:
            rec.custo_fixo = float(custo) / 100
            rec.valor_custofixo = rec.valor_pedido * rec.custo_fixo

    
    def _amount_tc_prevista(self):
        for rec in self:
            total = sum(rec.os_ids.pedido_venda.mapped('terceiros')) if rec.os_ids.pedido_venda else 0
            rec.tc_prevista = total

    
    def _amount_mp_prevista(self):
        for rec in self:
            total = sum(rec.os_ids.pedido_venda.mapped('materia_prima')) if rec.os_ids.pedido_venda else 0
            rec.mp_prevista = total

    
    def _amount_mo_prevista(self):
        for rec in self:
            pedidos = len(rec.os_ids.pedido_venda)
            if pedidos == 0:
                pedidos = 1

            horas = sum(rec.os_ids.pedido_venda.mapped('valor_horas')) / pedidos
            total = horas * rec.horas_prevista
            totalm = sum(rec.os_ids.pedido_venda.mapped('valor_total_hmanual')) if rec.os_ids.pedido_venda else 0

            if totalm:
                rec.mo_prevista = totalm
            else:
                rec.mo_prevista = total

    
    def _amount_horas_prevista(self):
        for rec in self:
            total = sum(rec.os_ids.pedido_venda.mapped('horas_mo')) if rec.os_ids.pedido_venda else 0
            rec.horas_prevista = total

    
    def _amount_valor_pedido(self):
        for rec in self:
            total = sum(rec.os_ids.pedido_venda.mapped('amount_total')) if rec.os_ids.pedido_venda else 0
            rec.valor_pedido = total

    
    def _compute_compra(self):
        for rec in self:
            mpprev = sum(rec.os_ids.pedido_venda.mapped('materia_prima')) if rec.os_ids.pedido_venda else 0
            mpreal = sum(rec.os_ids.pedidos_compra.mapped('valor_os')) if rec.os_ids.pedidos_compra else 0
            if mpprev and mpreal:
                if mpreal:
                    total = mpreal / mpprev
                    rec.progress_compra = total * 100
            rec.progress_compra = 0

    
    def _amount_total_orcado(self):
        for rec in self:
            mpprev = sum(rec.os_ids.pedido_venda.mapped('materia_prima')) if rec.os_ids.pedido_venda else 0
            moprev = sum(rec.os_ids.pedido_venda.mapped('valor_horas')) if rec.os_ids.pedido_venda else 0
            tcprev = sum(rec.os_ids.pedido_venda.mapped('terceiros')) if rec.os_ids.pedido_venda else 0
            rec.orcado = mpprev + moprev + tcprev

    
    def _amount_imposto_real(self):
        for rec in self:
            if rec.posicao:

                if rec.entrega_efetiva:
                    mes = rec.entrega_efetiva.month
                    ano = rec.entrega_efetiva.year
                    dt_str = str(ano) + '-' + str(mes).zfill(2) + '-' + '01'
                    pedi = rec.os_ids.pedido_venda

                    #Verifica o tipo de serviço e pesquisa sua aliquota.
                    if pedi[0].fiscal_position_id.name == 'Serviço' or pedi[0].fiscal_position_id.name == 'Serviço c retenção':
                        city_comp = self.env.company.city_id
                        city_part = rec.cliente.city_id
                        if city_part == city_comp:
                            ret = True
                        else:
                            ret = False
                        if ret:
                            percen = self.env['os.impostos.line'].search(
                                [('fiscal_position.name', '=', 'Serviço c retenção'), ('mes', '=', dt_str)]).percentual
                        else:
                            percen = self.env['os.impostos.line'].search(
                            [('fiscal_position.name', '=', 'Serviço'), ('mes', '=', dt_str)]).percentual


                    #Calcula o imposto caso não seja do tipo Serviço.
                    else:
                        if pedi.fiscal_position_id.name == 'Industrialização':
                            percen = self.env['os.impostos.line'].search(
                                [('fiscal_position.name', '=', 'Industrialização'), ('mes', '=', dt_str)]).percentual

                        if pedi.fiscal_position_id.name == 'Venda':
                            percen = self.env['os.impostos.line'].search(
                                [('fiscal_position.name', '=', 'Venda'), ('mes', '=', dt_str)]).percentual

                    rec.imposto_real = percen / 100
                    rec.impostos_resultado = rec.valor_pedido * (rec.imposto_real / 100)

                else:
                    rec.imposto_real = 0.0



    def _amount_consumidos(self):
        for rec in self:
            total = sum(rec.os_ids.consumidos.mapped('valor_con')) if rec.os_ids.consumidos else 0.0
            rec.consumidos_total = total

    def _amount_mp_real(self):
        for rec in self:
            os = rec.os_ids
            total = sum(os.pedidos_compra.mapped('valor_os')) if os.pedidos_compra else 0.0 #filtered(lambda l: l.state == 'purchase' and l.qty_received > 0)
            rec.mp_real = total

    
    def _amount_mo_real(self):
        for rec in self:
            total = sum(rec.os_ids.apontamento.mapped('valor_total')) if rec.os_ids.apontamento else 0
            rec.mo_real = total

    
    def _amount_valor_horas(self):
        for rec in self:
            total = sum(rec.os_ids.apontamento.filtered(lambda l: l.retrabalho == False).mapped(
                'soma_total')) if rec.os_ids.apontamento else 0
            rec.horas_real = total

    
    def _amount_horas_real(self):
        for rec in self:
            total = sum(rec.os_ids.apontamento.filtered(lambda l: l.retrabalho == False).mapped(
                'normal_total')) if rec.os_ids.apontamento else 0
            rec.horas_real = total

    
    def _amount_extra_real(self):
        for rec in self:
            total = sum(rec.os_ids.apontamento.filtered(lambda l: l.retrabalho == False).mapped(
                'extra_total')) if rec.os_ids.apontamento else 0
            rec.extra_real = total

    
    def _amount_horas_retrabalho(self):
        for rec in self:
            total = sum(rec.os_ids.apontamento.filtered(lambda l: l.retrabalho).mapped(
                'soma_total')) if rec.os_ids.apontamento else 0
            rec.horas_retrabalho = total

    
    def _amount_horas_total(self):
        for rec in self:
            total = sum(rec.os_ids.apontamento.mapped('soma_total')) if rec.os_ids.apontamento else 0
            rec.horas_total = total

    
    def _amount_valor_horas_retrabalho(self):
        for rec in self:
            total = sum(rec.os_ids.apontamento.filtered(lambda l: l.retrabalho).mapped(
                'valor_total')) if rec.os_ids.apontamento else 0
            rec.valor_horas_retrabalho = total

    
    def _amount_valor_extra(self):
        for rec in self:
            total = sum(rec.os_ids.apontamento.filtered(lambda l: l.retrabalho == False).mapped(
                'valor_extra_total')) if rec.os_ids.apontamento else 0
            rec.valor_extra = total

    
    def _amount_horas_resultado(self):
        for rec in self:
            real = sum(rec.os_ids.apontamento.mapped('soma_total')) if rec.os_ids.apontamento else 0
            previ = sum(rec.os_ids.pedido_venda.mapped('horas_mo')) if rec.os_ids.pedido_venda else 0
            rec.horas_resultado = previ - real

    
    def _amount_mo_resultado(self):
        for rec in self:
            rec.mo_resultado = rec.mo_prevista - rec.mo_real

    
    def _amount_mp_resultado(self):
        for rec in self:
            rec.mp_resultado = rec.mp_prevista - rec.mp_real

    @api.depends('mp_real','mo_real','impostos_resultado','valor_custofixo','consumidos_total')
    def _amount_total_gasto(self):
        self.updt()
        for rec in self:

            gasto = rec.mp_real + rec.mo_real + rec.comissao + rec.impostos_resultado + rec.valor_custofixo + rec.consumidos_total
            diferenca = rec.orcado - gasto
            if gasto > 0 and rec.valor_pedido > 0:
                resul = (rec.valor_pedido - gasto) / rec.valor_pedido
            else:
                resul = 100
            rec.total_gasto = gasto
            rec.orcado_gasto = rec.mo_prevista + rec.mp_prevista + rec.tc_prevista + rec.comissao - gasto - rec.valor_custofixo
            rec.resultado = rec.valor_pedido - gasto
            rec.resultado_percen = resul


            # rec.write({'resultado': rec.valor_pedido - gasto, 'total_gasto': gasto, 'orcado_gasto': diferenca,
            #            'resultado_percen': resul})

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
