# -*- coding: utf-8 -*-
import datetime
from odoo import api, fields, models, _
from odoo.exceptions import UserError, ValidationError



class OrdemServico(models.Model):
    _name = "ordem.servico"
    _description = "Ordem de Servico"
    _inherit = ["mail.thread", "mail.activity.mixin"]
    _rec_name = 'name'
    _defaults = {'user_id': lambda self, cr, uid, ctx=None: uid}


    name = fields.Char('Número', index=True, required=True, readonly=True, tracking=True,
                       translate=True, default=lambda self: _('New'))
    apontamento = fields.Many2many('hr.attendance', 'hr_attendance_os_rel', 'ordem_servico_id', 'hr_attendance_id',
                                   string='Linha Apontamento', store=True, copy=True, index=True)
    certificados = fields.Many2many('os.certificados', 'os_certificados_arquivos', 'certificados_id', 'os_id',
                                    string='Arquivos', store=True, copy=True)
    cliente_id = fields.Many2one('res.partner', string='Cliente', store=True, index=True,
                                 related='pedido_venda.partner_id.parent_id')
    desenhos = fields.Many2many('os.desenhos', 'os_desenhos_arquivos', 'os_id', 'desenhos_id',
                                string='Arquivos', store=True, copy=True)
    data_base = fields.Date(string='Data Base', store=True, copy=True)
    data_entrega = fields.Date(string='Data Entrega', store=True, copy=True)
    data_producao = fields.Date(string='Liberado para Produção', store=True, copy=True)
    data_faturamento = fields.Date(string='Liberado para Faturamento', store=True, copy=True)
    empresa = fields.Many2one('res.company', 'Company', store=True,
                              related='pedido_venda.company_id')
    entrega_efetiva = fields.Date(string='Entrega Efetiva', store=True, copy=True)
    fechamentos_ids = fields.Many2many('os.fechamento','os_fechamento_rel', 'os_id','os_ids', string='Fechamentos', store=True)
    liberado = fields.Many2one('res.users', string='Liberado por', index=True, required=True)

    responsavel = fields.Many2many('res.partner', 'os_partner_contact', 'id', 'contact_id', string='Responsável Técnico', translate=True, readonly=False, required=False,
                                   index=True, domain="[('parent_id','=',cliente_id)]")
    vendedor =fields.Many2one( 'res.users', string='Vendedor', translate=True, readonly=True, required=False,
                              change_default=True, index=True, tracking=1, related='pedido_venda.user_id')
    user_id = fields.Many2one('res.users', string='Elaborado por', required=True, default=lambda self: self.env.user)
    movimentacoes = fields.Many2many('stock.move.line', 'stock_move_line_os', 'id', 'os_id',
                                     string='Movimentações', required=False, index=True, copy=False)
    nf_entrada = fields.Many2many('os.nfs', 'nf_entrada_rel', 'os_id', 'os_nfs_id',
                                  string='NF Entrada', copy=True, store=True, readonly=False)
    nf_saida = fields.Many2many('os.nfs', 'nf_saida_rel', 'os_id', 'os_nfs_id',
                                string='NF Saida', readonly=False, store=True, copy=True)
    observacoes = fields.Text(string="Observações", store=True, copy=True)
    pedidos_cliente = fields.Many2many('os.pedcli', 'pedcli_os_rel', 'os_id', 'os_pedcli_id',
                                       string="Pedidos Cliente", store=True, copy=True)
    pedidos_compra = fields.Many2many('purchase.order.line', 'purchase_order_line_os_rel', 'os_id',
                                      'purchase_order_line_id', string='Pedidos de Compra', store=True, copy=True)
    pedido_venda = fields.Many2many('sale.order', 'ordem_servico_rel_sale', 'os_id', 'sale_order_id',
                                    string='Pedidos de Venda', store=True, copy=True)
    pedido_venda_original = fields.Many2many('sale.order', 'os_rel_sale_original', 'os_id', 'sale_order_id',
                                    string='Pedido de Venda Original', store=True, copy=True)
    produtos = fields.Many2many('mrp.production', 'mrp_rel_os', 'mrp_production_id', 'os_id',
                                string='Produtos', store=True, copy=True)
    inspecoes = fields.Many2many('os.inspecoes', 'inspecoes_rel_os', 'os_inspecoes_id', 'os_id', string='Inspeções', store=True, copy=True)
    state = fields.Selection(
        [('draft', 'Provisória'),('aberta', 'Aberta'), ('parcial', 'Parcialmente Entregue'), ('concluida', 'Concluida'), ('cancel', 'Cancelada')],
        string='Status', store=True, copy=True, default='draft')
    status_fat = fields.Selection(
        [('nao', 'Não Faturada'), ('parcial', 'Faturada Parcialmente'), ('faturada', 'Faturada'),
         ('paga', 'Paga')], default='nao',
        string='Faturamento', store=True, copy=True, )

    tipo_os = fields.Selection(
        [('normal', 'Normal'), ('repeticao', 'Repetição'), ('manutencao', 'Manutencao'), ('rafael', 'Rafael')], default='normal',
        string='Tipo', store=True, copy=True, required=True)


    @api.onchange('tipo_os')
    def compute_tipo_os(self):
        if self.tipo_os == 'manutencao':
            self.empresa = 1
            self.cliente_id = 1


            self.write({'empresa': 1})
            self.write({'cliente_id': 1})

        if self.tipo_os == 'rafael':
            self.empresa = 1
            self.cliente_id = 2625
            self.write({'empresa': 1})
            self.write({'cliente_id': 2625})


    @api.model
    def create(self, vals):
        if vals.get('name', _('New')) == _('New'):
            if vals.get('tipo_os') == 'normal':
                vals['name'] = self.env['ir.sequence'].next_by_code('ordem.seq') or _('New')

            if vals.get('tipo_os') == 'repeticao':
                vals['name'] = self.env['ir.sequence'].next_by_code('ordem.seq') or _('New')

            if vals.get('tipo_os') == 'manutencao':
                vals['name'] = self.env['ir.sequence'].next_by_code('ordem.manu') or _('New')

            if vals.get('tipo_os') == 'rafael':
                vals['name'] = self.env['ir.sequence'].next_by_code('ordem.rafa') or _('New')


            result = super(OrdemServico, self).create(vals)
            val = {'os_ids': result.id}
            self.env['os.fechamento'].create(val)
        return result



    def name_get(self):
        res = []
        for record in self:
            res.append((record.id, record.name))
        return res


    def abrir_os(self):
        self.write({'state': 'aberta'})
        self.write({'status_fat': 'nao'})


        pedidos = self.pedido_venda.ids
        for ped in pedidos:
            self.env['sale.order'].browse(ped).write({'state': 'sale'})

        return {}


    def parcial_os(self):

        # self.env['os.fechamento'].browse(self.id).write({'state': 'parcial'})
        return {
            'name': "Entrega Parcial",
            'type': 'ir.actions.act_window',
            'view_type': 'form',
            'view_mode': 'form',
            'res_model': 'os.parcial.wizard',
            'view_id': self.env.ref('ordem_servico.parcial_wizard_view').id,
            'target': 'new',
        }

    def concluida_os(self):
        self.write({'state': 'concluida'})
        return {}

    def provisoria_os(self):
        self.write({'state': 'draft'})
        self.write({'status_fat': 'nao'})
        return {}

    def cancelar_os(self):
        if self.state in ('cancel','draft'):
            raise UserError(_("Não é possível cancelar uma fatura provisória ou cancelada."))

        self.write({'state': 'cancel'})
        self.write({'status_fat': ''})

        pedidos = self.pedido_venda.ids
        for ped in pedidos:
            self.env['sale.order'].browse(ped).write({'state': 'draft'})

    class OsParcialWizard(models.TransientModel):
        _name = 'os.parcial.wizard'
        _description = 'Entrega Parcial'

        msg = fields.Text(string="Deseja entregar parcialmente a OS?", default="Deseja entregar parcialmente a OS?", readonly=True)

        def comfat(self):
            records = self.env['ordem.servico'].browse(self.env.context.get('active_ids'))
            for rec in records:
                rec.write({'state': 'parcial'})
                rec.write({'status_fat': 'parcial'})

        def semfat(self):
            records = self.env['ordem.servico'].browse(self.env.context.get('active_ids'))
            for rec in records:
                rec.write({'state': 'parcial'})
                rec.write({'status_fat': 'nao'})


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
            rec._amount_mo_real()
            rec._amount_valor_horas()
            rec._amount_horas_real()
            rec._amount_horas_retrabalho()
            rec._amount_horas_total()
            rec._amount_valor_horas_retrabalho()
            rec._amount_horas_resultado()
            rec._amount_mo_resultado()
            rec._amount_mp_resultado()
            rec._amount_total_gasto()
            rec._amount_valor_pedido()

    os_ids = fields.Many2one('ordem.servico', string='Ordem de Serviço', required=True)
    cliente = fields.Many2one('res.partner', 'Company', store=True,
                              related='os_ids.pedido_venda.partner_id.parent_id')
    empresa = fields.Many2one('res.company', string='Empresa', related='os_ids.empresa')
    posicao = fields.Many2one('account.fiscal.position', string='Fiscal Position',
        domain="[('company_id', '=', company_id)]", check_company=True, related='os_ids.pedido_venda.fiscal_position_id')
    data_base = fields.Date(string='Data Base', store=True, copy=True, related='os_ids.data_base')
    entrega_efetiva = fields.Date(string='Entrega Efetiva', store=True, copy=True, related='os_ids.entrega_efetiva')
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


    custo_fixo = fields.Float(string='Custo Fixo', store=True, copy=True)
    margem = fields.Float(string='Margem', store=True, copy=True)

    mo_real = fields.Monetary(string='Valor Total MO', store=True, copy=True, compute='_amount_mo_real', group_operator='sum')
    mp_real = fields.Monetary(string='Compras Real', store=True, copy=True, compute='_amount_mp_real', group_operator='sum')
    comissao_real = fields.Monetary(string='Comissão Real', store=True, copy=True, group_operator='sum')
    imposto_real = fields.Float(string='Imposto Real', store=True, copy=True, group_operator='sum', compute='_amount_imposto_real')
    progress_compra = fields.Float(string='% Compras', store=True, compute='_compute_compra')
    horas_real = fields.Float(string='Horas Reais', store=True, copy=True, compute='_amount_horas_real', group_operator='sum')
    horas_retrabalho = fields.Float(string='Horas Retrabalho', store=True, copy=True, compute='_amount_horas_retrabalho', group_operator='sum')
    horas_total = fields.Float(string='Horas Reais', store=True, copy=True, compute='_amount_horas_total', group_operator='sum')
    valor_horas = fields.Float(string='Valor Horas', store=True, copy=True, compute='_amount_valor_horas', group_operator='sum')
    valor_horas_retrabalho = fields.Monetary(string='Valor Horas Retrabalho', store=True, copy=True,
                                          compute='_amount_valor_horas_retrabalho', group_operator='sum')


    horas_resultado = fields.Float(string='Horas', store=True, copy=True, compute='_amount_horas_resultado', help='Horas Reais - Horas Previstas', group_operator='sum')
    mo_resultado = fields.Monetary(string='Valor Horas', store=True, copy=True, compute='_amount_mo_resultado', help='Horas Reais - Horas Previstas', group_operator='sum')
    mp_resultado = fields.Monetary(string='MP/Terceiros', store=True, copy=True, compute='_amount_mp_resultado', help='(MP Prevista + Terceiros Previsto) - (MP Real + Terceiros Real)', group_operator='sum')
    impostos_resultado = fields.Monetary(string='Impostos', store=True, copy=True, compute='_amount_imposto_real')
    impostos_resultado_percen = fields.Float(string='Impostos %', store=True, copy=True)


    orcado = fields.Monetary(string='Orçado', store=True, copy=True, compute='_amount_total_orcado', group_operator='sum')
    total_gasto = fields.Monetary(string='Total de Gastos', store=True, copy=True, compute='_amount_total_gasto', help='Total de MP Real + Total de MO Real + Comissao + Impostos', group_operator='sum')
    orcado_gasto = fields.Monetary(string='Orçado X Gastos', store=True, copy=True)
    resultado = fields.Monetary(string='Resultado', store=True, copy=True, readonly=True, help='Valor de Venda - Total de Gastos', compute='_amount_total_gasto', group_operator='sum')
    resultado_percen = fields.Float(string='Resultado %', store=True, copy=True, readonly=True, compute='_amount_total_gasto', group_operator='avg')




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
            rec.orcado_gasto = rec.total_gasto - rec.orcado


    @api.depends('os_ids.state')
    def _amount_imposto_real(self):
        for rec in self:
            if rec.entrega_efetiva == True:
                entrega = datetime.date.strftime(self.entrega_efetiva, '%m/%Y')
                posicao = sum(rec.posicao.meses.filtered(lambda l: l.name == entrega).mapped('percentual'))
                rec.impostos_resultado = rec.valor_pedido * (posicao / 100)
                rec.imposto_real = posicao / 100

    @api.depends('os_ids.state')
    def _amount_mp_real(self):
        for rec in self:
            total = sum(rec.os_ids.pedidos_compra.mapped('price_total')) if rec.os_ids.pedidos_compra else 0
            rec.mp_real = total


    @api.depends('os_ids.state')
    def _amount_mo_real(self):
        for rec in self:
            total = sum(rec.os_ids.apontamento.mapped('valor_total')) if rec.os_ids.apontamento else 0
            rec.mo_real = total

    @api.depends('os_ids.state')
    def _amount_valor_horas(self):
        for rec in self:
            total = sum(rec.os_ids.apontamento.filtered(lambda l: l.retrabalho == False).mapped('valor_total')) if rec.os_ids.apontamento else 0
            rec.horas_real = total

    @api.depends('os_ids.state')
    def _amount_horas_real(self):
        for rec in self:
            total = sum(rec.os_ids.apontamento.filtered(lambda l: l.retrabalho == False).mapped('worked_hours')) if rec.os_ids.apontamento else 0
            rec.horas_real = total

    @api.depends('os_ids.state')
    def _amount_horas_retrabalho(self):
        for rec in self:
            total = sum(rec.os_ids.apontamento.filtered(lambda l: l.retrabalho).mapped('worked_hours')) if rec.os_ids.apontamento else 0
            rec.horas_retrabalho = total

    @api.depends('os_ids.state')
    def _amount_horas_total(self):
        for rec in self:

            total = sum(rec.os_ids.apontamento.mapped('worked_hours')) if rec.os_ids.apontamento else 0
            rec.horas_total = total

    @api.depends('os_ids.state')
    def _amount_valor_horas_retrabalho(self):
        for rec in self:
            total = sum(rec.os_ids.apontamento.filtered(lambda l: l.retrabalho).mapped('valor_total')) if rec.os_ids.apontamento else 0
            rec.valor_horas_retrabalho = total


    @api.depends('os_ids.state')
    def _amount_horas_resultado(self):
        for rec in self:
            real = sum(rec.os_ids.apontamento.mapped('worked_hours')) if rec.os_ids.apontamento else 0
            previ = sum(rec.os_ids.pedido_venda.mapped('horas_mo')) if rec.os_ids.pedido_venda else 0
            rec.horas_resultado = previ - real

    @api.depends('os_ids.state')
    def _amount_mo_resultado(self):
        for rec in self:
            real = sum(rec.os_ids.pedido_venda.mapped('valor_horas')) if rec.os_ids.pedido_venda else 0
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

            gasto = mp + mo + rec.comissao + rec.imposto_real
            rec.resultado = valor_pedido - gasto



class OsInspecoes(models.TransientModel):
    _name = "os.inspecoes"
    _description = "Inspeções"


    name = fields.Char(string='Inspeção', required=True, store=True, default=lambda self: _('New'))
    tipo = fields.Selection([('Dimensional', 'Dimensional'), ('Estanqueidade', 'Estanqueidade'),
                             ('Ultrasom em Solda', 'Ultrasom em Solda'), ('Líquido Penetrante', 'Líquido Penetrante'),('Outros','Outros')],
                            string='Tipo', store=True, copy=True)
    status = fields.Selection([('Aprovado', 'Aprovado'), ('Reprovado', 'Reprovado')],
                              string='Status', store=True, copy=True)
    ordem_servico = fields.Many2one('ordem.servico', 'Ordem de Serviço', required=True, index=True, copy=False)
    produto_desenho = fields.Char(string='Desenho', required=True, store=True)
    produto_descricao = fields.Char(string='Descrição', required=True, store=True)
    medidas = fields.Many2many('os.inspecoes.linhas', 'medidas_rel_inspecoes', string='Medidas', store=True)
    processo = fields.Text(string='Processo Utilizado', store=True, copy=True)
    setor = fields.Selection([('Corte e Dobra', 'Corte e Dobra'), ('Furação', 'Furação'), ('Usinagem','Usinagem'), ('Montagem','Montagem'),('Solda', 'Solda'), ('Acabamento', 'Acabamento'), ('Inspeção Final', 'Inspeção Final')],
                              string='Setor', store=True, copy=True, required=True)
    desvio = fields.Char(string='Desvio', store=True, copy=True)
    nota = fields.Text(string='Nota', store=True, copy=True)
    conclusao = fields.Text(string='Conclusão', store=True, copy=True)
    data_criacao = fields.Date(string='Data de Criação', store=True, copy=True)
    user_id = fields.Many2one('res.users', string='Usuario', index=True,
                              default=lambda self: self.env.user, check_company=True)
    responsavel = fields.Many2one('res.users', string='Responsável', index=True)

    @api.model
    def create(self, vals):

        if vals.get('name', _('New')) == _('New'):
            vals['name'] = self.env['ir.sequence'].next_by_code('insp_os.seq') or _('New')

        result = super(OsInspecoes, self).create(vals)

        return result

    def default_get(self, fields):
        res = super(OsInspecoes, self).default_get(fields)
        teste = self.env['ordem.servico'].browse('id')
        res['ordem_servico'] = self.env['ordem.servico'].browse(self.env.context.get('active_ids'))
        return res

    @api.constrains('tipo', 'medidas')
    def valida_medidas(self):
        for rec in self:
            if rec.tipo == 'Dimensional' and not rec.medidas.ids:
                raise ValidationError(_("Informe uma medida para salvar!"))


class OsInspecoesLinhas(models.Model):
    _name = "os.inspecoes.linhas"
    _description = "Linhas Inspeções"

    posicao = fields.Char(string='Posição', store=True, required=True)
    medida_sol = fields.Float(string='Medida Solicitada', store=True, copy=True)
    medida_real = fields.Float(string='Medida Encontrada', store=True, copy=True)
    medida_total = fields.Float(string='Desvio Total', compute='_desvio', store=True, copy=True)


    @api.depends('medida_sol', 'medida_real', 'medida_total')
    def _desvio(self):
        for line in self:

            line.update({
                'medida_total': (self.medida_sol - self.medida_real) * (-1)

            })

