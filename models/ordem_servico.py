# -*- coding: utf-8 -*-
from datetime import datetime
from odoo import api, fields, models, _
from odoo.exceptions import ValidationError


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
    # compra = fields.Many2one(related='pedidos_compra.order_id')
    certificado = fields.Many2many( related='pedidos_compra.order_id.certificados')
    cliente_id = fields.Many2one('res.partner', string='Cliente', store=True, index=True,
                                 related='pedido_venda.partner_id.parent_id')
    desenhos = fields.Many2many('ir.attachment', 'os_desenho_arquivo', 'os_id', 'desenhos_id',
                                string='Arquivos', store=True, copy=True)
    data_base = fields.Date(string='Data Base', store=True, copy=True)
    data_entrega = fields.Date(string='Data Entrega', store=True, copy=True)
    data_producao = fields.Date(string='Liberado para Produção', store=True, copy=True)
    data_faturamento = fields.Date(string='Liberado para Faturamento', store=True, copy=True)
    empresa = fields.Many2one('res.company', 'Company', store=True,
                              related='pedido_venda.company_id')
    entrega_efetiva = fields.Date(string='Entrega Efetiva', store=True, copy=True)
    fechamentos_ids = fields.Many2many('os.fechamento', 'os_fechamento_rel', 'os_id', 'os_ids', string='Fechamentos', store=True)
    liberado = fields.Many2one('res.users', string='Liberado por', index=True, required=True)

    responsavel = fields.Many2many('res.partner', 'os_partner_contact', 'id', 'contact_id', string='Responsável Técnico', translate=True, readonly=False, required=False,
                                   index=True, domain="[('parent_id','=',cliente_id)]")
    vendedor =fields.Many2one('res.users', string='Vendedor', translate=True, readonly=True, required=False,
                              change_default=True, index=True, tracking=1, related='pedido_venda.user_id')
    user_id = fields.Many2one('res.users', string='Elaborado por', required=True, default=lambda self: self.env.user)
    movimentacoes = fields.Many2many('stock.move.line', 'stock_move_line_os', 'id', 'os_id',
                                     string='Movimentações', required=False, index=True, copy=False)
    nf_entrada = fields.Many2many('os.nfs', 'nf_entrada_rel', 'os_id', 'os_nfs_id',
                                  string='NF Entrada', copy=True, store=True, readonly=False)
    nf_saida = fields.Many2many('os.nfs', 'nf_saida_rel', 'os_id', 'os_nfs_id',
                                string='NF Saida', readonly=False, store=True, copy=True)
    observacoes = fields.Text(string="Observações", store=True, copy=True)

    pedidos_compra = fields.Many2many('purchase.order.line', 'purchase_order_line_os_rel', 'os_id',
                                      'purchase_order_line_id', string='Pedidos de Compra', store=True, copy=True, domain="[('state','==','purchase'),('qty_received','!=',0)]")
    pedido_venda = fields.Many2many('sale.order', 'ordem_servico_rel_sale', 'os_id', 'sale_order_id',
                                    string='Pedidos de Venda', store=True, copy=True)
    posicao = fields.Many2one(related='pedido_venda.fiscal_position_id')
    pedido_venda_original = fields.Many2many('sale.order', 'os_rel_sale_original', 'os_id', 'sale_order_id',
                                    string='Pedido de Venda Original', store=True, copy=True)
    produtos = fields.Many2many('mrp.production', 'mrp_rel_os', 'mrp_production_id', 'os_id',
                                string='Produtos', store=True, copy=True, domain="[('state', '!=', 'cancel')]")

    lista_produtos = fields.Many2many('os.listaprod','mrplist_rel_os','mrplist_id', 'os_id', string='Lista de Materiais', store=True, compute='_lista_produtos')
    consumidos = fields.Many2many('os.consumidos', 'consumidos_rel_os','consumido_id', 'os_id', string='Ordem de Serviço', compute='_consumidos')
    nao_conform =fields.Many2many('mgmtsystem.nonconformity', 'os_rel_mgmt', 'os_id','mgmt_id', string='Não Conformidades')

    inspecoes = fields.Many2many('os.inspecoes', 'inspecoes_rel_os', 'os_inspecoes_id', 'os_id', string='Inspeções', store=True, copy=True)

    state = fields.Selection(
        [('draft', 'Provisória'), ('aberta', 'Aberta'), ('parcial', 'Parcialmente Entregue'), ('concluida', 'Concluida'), ('cancel', 'Cancelada')],
        string='Status', store=True, copy=True, default='draft')
    status_fat = fields.Selection(
        [('nao', 'Não Faturada'), ('parcial', 'Faturada Parcialmente'), ('faturada', 'Faturada'),
         ('paga', 'Paga')], default='nao',
        string='Faturamento', store=True, copy=True)

    tipo_os = fields.Selection(
        [('normal', 'Normal'), ('repeticao', 'Repetição'), ('manutencao', 'Manutencao'), ('rafael', 'Rafael')], default='normal',
        string='Tipo', store=True, copy=True, required=True)
    terc_total = fields.Boolean(string='Totalmente Terceirizada')

    ultimamsg = fields.Char(string='Mensagens', compute='_last_msg')
    ultiuser = fields.Char(string='Usuario', compute='_last_usr')

    visual_corte = fields.Boolean(string="Visual", store=True)
    dimen_corte = fields.Boolean(string="Dimensional", store=True)
    outras_corte = fields.Char(string='Outras', store=True, default='')
    resp_corte = fields.Many2one('hr.employee', string='Responsável', index=True)
    dt_corte = fields.Date(string='Dt. Corte', store=True, copy=True)

    visual_fura = fields.Boolean(string="Visual", store=True)
    dimen_fura = fields.Boolean(string="Dimensional", store=True)
    outras_fura = fields.Char(string='Outras', store=True, default='')
    resp_fura = fields.Many2one('hr.employee', string='Responsável', index=True)
    dt_fura = fields.Date(string='Dt. Furação', store=True, copy=True)

    visual_mont = fields.Boolean(string="Visual", store=True)
    dimen_mont = fields.Boolean(string="Dimensional", store=True)
    outras_mont = fields.Char(string='Outras', store=True, default='')
    resp_mont = fields.Many2one('hr.employee', string='Responsável', index=True)
    dt_mont = fields.Date(string='Dt. Montagem', store=True, copy=True)

    visual_usi = fields.Boolean(string="Visual", store=True)
    dimen_usi = fields.Boolean(string="Dimensional", store=True)
    outras_usi = fields.Char(string='Outras', store=True, default='')
    resp_usi = fields.Many2one('hr.employee', string='Responsável', index=True)
    dt_usi = fields.Date(string='Dt. Usinagem', store=True, copy=True)

    visual_solda = fields.Boolean(string="Visual", store=True)
    outras_solda = fields.Char(string='Outras', store=True, default='')
    resp_solda = fields.Many2one('hr.employee', string='Responsável', index=True)
    pro_solda = fields.Selection(
        [('Mag', 'MAG-AC1'), ('Tig', 'TIG-AC1'), ('um', '01-02A'), ('doisa', '02A'), ('tres', '03-06'),
         ('tresa', '03-06A'), ('quatro', '04-10')], string='Processo EPSC', default='tresa', store=True, copy=True,
        required=True)
    dt_solda = fields.Date(string='Dt. Solda', store=True, copy=True)

    visual_aca = fields.Boolean(string="Visual", store=True)
    dimen_aca = fields.Boolean(string="Dimensional", store=True)
    outras_aca = fields.Char(string='Outras', store=True,default='')
    resp_aca = fields.Many2one('hr.employee', string='Responsável', index=True)
    dt_aca = fields.Date(string='Dt. Acabamento', store=True, copy=True)

    visual_fin = fields.Boolean(string="Visual", store=True)
    dimen_fin = fields.Boolean(string="Dimensional", store=True)
    outras_fin = fields.Char(string='Outras', store=True, default='')
    resp_fin = fields.Many2one('hr.employee', string='Responsável', index=True)
    dt_fin = fields.Date(string='Dt. Insp. Final', store=True, copy=True)

    apontapend = fields.Selection([('Faltando', 'Faltando'), ('Parcial', 'Parcial'), ('Concluido', 'Concluido')], string='Apontamentos', compute='_apontapend')
    comprapend = fields.Selection([('Faltando', 'Faltando'), ('Parcial', 'Parcial'), ('Concluido', 'Concluido')],string='Compras', compute='_comprapend')
    certpend = fields.Selection([('Faltando', 'Faltando'), ('Parcial', 'Parcial'), ('Concluido', 'Concluido')],string='Certificados', compute='_certpend')
    desenhopend = fields.Selection([('Faltando', 'Faltando'), ('Parcial', 'Parcial'), ('Concluido', 'Concluido')],string='Desenhos', compute='_desenhopend')
    insppend =fields.Selection([('Faltando', 'Faltando'), ('Parcial', 'Parcial'), ('Concluido', 'Concluido')],string='Inspeções', compute='_insppend')

    # def _certificados(self):
    #     compras = self.pedidos_compra.order_id.certificados.ids
    #     if compras:
    #         self.certificado = [(4,0,compras)]
    #     else:
    #         self.certificado = [(5,0,0)]

    def _apontapend(self):
        for rec in self:
            if rec.apontamento:
                rec.apontapend = 'Concluido'
            else:
                rec.apontapend = 'Faltando'

    def _comprapend(self):
        for rec in self:
            if rec.pedidos_compra:
                rec.comprapend = 'Concluido'
            else:
                rec.comprapend = 'Faltando'

    def _certpend(self):
        for rec in self:
            if rec.certificado:
                rec.certpend = 'Concluido'
            else:
                rec.certpend = 'Faltando'

    def _desenhopend(self):
        for rec in self:
            if rec.desenhos:
                rec.desenhopend = 'Concluido'
            else:
                rec.desenhopend = 'Faltando'
    def _insppend(self):
        for rec in self:
            if rec.resp_fin and rec.dt_fin:
                rec.insppend = 'Concluido'
            else:
                rec.insppend = 'Faltando'



    def _lista_produtos(self):

        if self.lista_produtos:
            self.lista_produtos = [(5)]
        for rec in self.produtos:
            if rec.state != 'cancel':
                if rec.bom_id:
                    lista_id = rec.bom_id.id
                    lista = self.env['mrp.bom.line'].search([('bom_id','=',lista_id)])
                    for y in lista:
                        self.lista_produtos = [(0,0,{'produto': y.product_id.id,'qtd': y.product_qty, 'dimensoes': y.dimensoes, 'estoque': y.estoque})]



    def _consumidos(self):
        if self.produtos:
            for rec in self.produtos:
                if rec.state != 'cancel' and rec.state!='draft':
                    lista_id = rec.move_raw_ids

                    if lista_id:
                        for x in lista_id:
                            if x.quantity_done > 0:
                                produto = x.product_id.id
                                qtd = x.product_uom_qty
                                qtddone = x.quantity_done
                                dimensoes = x.dimensoes
                                estoque = x.estoque
                                valor = x.product_id.standard_price * x.quantity_done
                                produtocli = rec.product_id.id

                                self.consumidos = [(0,0,{'produto_con': produto,'qtd_con': qtd, 'qtd_consumido': qtddone,'dim_con': dimensoes, 'est_con': estoque, 'valor_con': valor,'produto_cli':produtocli})]
                            else:
                                self.consumidos = [(1, 0, [])]
                else:
                    self.consumidos = [(1, 0, [])]
        else:
            self.consumidos = [(6, 0, [])]



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

    def _last_msg(self):
        for rec in self:
            ids = rec.message_ids.ids
            if ids:
                rec.ultimamsg = rec.message_ids[0].body

    def _last_usr(self):
        for rec in self:
            msg_ids = rec.message_ids

            if msg_ids:
                ult = msg_ids[0].author_id.id
                ult = self.env['res.partner'].browse(ult).name
                if ult:
                    rec.ultiuser = ult

    def abrir_os(self):


        self.write({'state': 'aberta'})
        self.write({'status_fat': 'nao'})
        self.message_post(body=_("Ordem de Serviço Aberta"))
        confirm=True
        self._lista_produtos()
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

        if self.status_fat == 'nao':
            raise ValidationError("Selecione um status de faturamento diferente de Não Faturada.")
        if self.entrega_efetiva == False:
            raise ValidationError("Digite a data da entrega efetiva para encerrar a OS.")
        if not self.apontamento:
            if not self.terc_total:
                raise ValidationError("Insira um apontamento para encerrar a OS.")
        if not self.resp_fin:
            raise ValidationError("Selecione um Responsável pela Inspeção Final.")
        if not self.dt_fin:
            raise  ValidationError("Insira a data da Inspeção Final")

        else:
            self.write({'state': 'concluida'})
            self.message_post(body=_("Ordem de Serviço Concluida"))
        return {}

    def provisoria_os(self):
        self.write({'state': 'draft'})
        self.write({'status_fat': 'nao'})
        self.message_post(body=_("Mudado para Provisória"))
        return {}

    def cancelar_os(self):
        if self.state in ('cancel','draft'):
            raise ValidationError("Não é possível cancelar uma fatura provisória ou cancelada.")

        self.write({'state': 'cancel'})
        self.write({'status_fat': ''})
        self.message_post(body=_("Cancelada"))
        pedidos = self.pedido_venda.ids
        for ped in pedidos:
            self.env['sale.order'].browse(ped).write({'state': 'draft'})

# class OrdemServicoPendencias(models.Model):
#     _name = "ordem.servico.pendencias"
#
#     compras = fields.Many2many()
#     desenhos = fields.Many2many()
#     apontamentos = fields.Many2many()
#     entregas = fields.Many2many()
#     inspecoes = fields.Char()
#
# class OsComprasPend(models.Model):
#     _name = "os.compras.pend"


class OsListaprod(models.Model):
    _name="os.listaprod"

    os = fields.Many2many('ordem.servico', 'mrplist_rel_os','os_id', 'mrplist_id', string='Ordem de Serviço')
    produto = fields.Many2one('product.product',string='Produto')
    estoque = fields.Boolean(string='Estoque')
    dimensoes = fields.Char(string='Dimensões')
    qtd = fields.Float(string='Quantidade')

class OsConsumidos(models.Model):
    _name="os.consumidos"

    os = fields.Many2many('ordem.servico', 'consumidos_rel_os','os_id', 'consumido_id', string='Ordem de Serviço')
    produto_cli = fields.Many2one('product.product',string='Produto')
    produto_con = fields.Many2one('product.product',string='Produto')
    est_con = fields.Boolean(string='Estoque')
    dim_con = fields.Char(string='Dimensões')
    qtd_con = fields.Float(string='Quantidade')
    qtd_consumido = fields.Float(string='Qtd. Consumido')
    valor_con = fields.Float(string='Total')

class OsParcialWizard(models.TransientModel):
    _name = 'os.parcial.wizard'
    _description = 'Entrega Parcial'

    msg = fields.Text(string="Deseja entregar parcialmente a OS?", default="Deseja entregar parcialmente a OS?", readonly=True)

    def comfat(self):
        records = self.env['ordem.servico'].browse(self.env.context.get('active_ids'))
        for rec in records:
           rec.write({'state': 'parcial'})
           rec.write({'status_fat': 'parcial'})
           rec.write({'entrega_efetiva': datetime.today()})
           rec.message_post(body=_("Entregue Parcialmente e Faturada"))

    def semfat(self):
        records = self.env['ordem.servico'].browse(self.env.context.get('active_ids'))
        for rec in records:
            if not self.entrega_efetiva:
                raise ValidationError("Digite a data da entrega efetiva para entregar parcialmente a OS.")
            else:
                for rec in records:
                    rec.write({'state': 'parcial'})
                    rec.write({'status_fat': 'nao'})
                    rec.message_post(body=_("Entregue Parcialmente e Não Faturada"))


class OsPedidosCliente(models.Model):
    _name = "os.pedcli"
    _description = "Pedidos Cliente"

    pedido = fields.Many2many('ir.attachment', 'pedidos_os_rel', 'pedido_id', 'ir_attachment_id',
                              string='Pedido', store=True, copy=True)

class OsDesenhos(models.Model):
    _name = "os.desenhos"
    _description = "Desenhos"

    data_criacao = fields.Date(string='Data', store=True, copy=True)
    documento = fields.Char(string='Documento', store=True, copy=True)
    arquivo = fields.Many2many('ir.attachment', 'desenhos_os_rel', 'arquivos_id', 'ir_attachment_id',
                               string='Desenho', store=True, copy=True)
    public = fields.Boolean()
    tipo = fields.Selection(
        [('Foto', 'Foto'), ('Peça', 'Peça'), ('Montagem', 'Montagem'), ('Plano de Corte', 'Plano de Corte')],
        string='Tipo', store=True, copy=True, required=True)
    setor = fields.Selection(
        [('Caldeiraria', 'Caldeiraria'), ('Equipamentos', 'Equipamentos'), ('Usinagem', 'Usinagem'),
         ('Outros', 'Outros')],
        string='Setor', store=True, copy=True, required=True)



class OsInspecoes(models.TransientModel):
    _name = "os.inspecoes"
    _description = "Inspeções"


    name = fields.Char(string='Inspeção', required=True, store=True, default=lambda self: _('New'))
    tipo = fields.Selection([('Dimensional', 'Dimensional'), ('Estanqueidade', 'Estanqueidade'),
                             ('Ultrasom em Solda', 'Ultrasom em Solda'), ('Líquido Penetrante', 'Líquido Penetrante'),('Outros','Outros')],
                            string='Tipo', default='Dimensional',required=True, store=True, copy=True)
    status = fields.Selection([('Aprovado', 'Aprovado'), ('Reprovado', 'Reprovado')],
                              string='Status', default='Aprovado', store=True, copy=True)
    cliente_id = fields.Many2one('res.partner', string='Cliente', store=True, related='ordem_servico.pedido_venda.partner_id.parent_id')
    pedido_venda = fields.Many2many('sale.order', 'insp_rel_sale', 'os_id', 'sale_order_id',string='Pedidos de Venda', store=True, copy=True, related='ordem_servico.pedido_venda')
    ordem_servico = fields.Many2many('ordem.servico', 'inspecoes_rel_os', 'os_id', 'os_inspecoes_id', string='Ordem de Serviço', store=True, copy=True)
    produto_desenho = fields.Char(string='Desenho', store=True, related='producao.product_id.default_code')
    producao = fields.Many2one('mrp.production',string='Produto', required=True, store=True)
    medidas = fields.Many2many('os.inspecoes.linhas', 'medidas_rel_inspecoes', string='Medidas', store=True)
    processo = fields.Text(string='Processo Utilizado', store=True, copy=True)
    setor = fields.Selection([('Corte e Dobra', 'Corte e Dobra'), ('Furação', 'Furação'), ('Usinagem','Usinagem'),
                              ('Montagem','Montagem'),('Solda', 'Solda'), ('Acabamento', 'Acabamento'),
                              ('Inspeção Final', 'Inspeção Final')],string='Setor', default='Inspeção Final',store=True, copy=True, required=True)
    desvio = fields.Char(string='Desvio', store=True, copy=True)
    nota = fields.Text(string='Nota', store=True, copy=True, default='Partes e peças acima citadas sofreram inspeção dimensional e que medidas encontram-se conforme as tolerâncias para caldeiraria DIN-7168')
    conclusao = fields.Text(string='Conclusão', store=True, copy=True, default='Equipamento / Peça Liberada para próxima etapa.')
    data_criacao = fields.Datetime(string='Data de Criação', default=fields.Datetime.now, store=True, copy=True)
    user_id = fields.Many2one('res.users', string='Usuario', index=True,
                              default=lambda self: self.env.user, check_company=True)
    responsavel = fields.Many2one('res.users', string='Responsável', index=True)

    # @api.onchange('ordem_servico')
    # def _ordem_servico(self):
    #
    #     rec = self.env['ordem.servico'].browse(self.ordem_servico.id).produtos
    #     print(rec)
    #     self.producao = rec


    @api.constrains('tipo', 'medidas')
    def valida_medidas(self):
        for rec in self:
            if rec.tipo == 'Dimensional' and not rec.medidas.ids:
                raise ValidationError(_("Informe uma medida para salvar!"))

    @api.model
    def create(self, vals):

        if vals.get('name', _('New')) == _('New'):
            vals['name'] = self.env['ir.sequence'].next_by_code('insp_os.seq') or _('New')

        result = super(OsInspecoes, self).create(vals)

        return result


    def print_insp(self):
        # inspecoes = self.env['os.inspecoes'].search_read([])

        data = {
            'form': self.read()[0],
        }
        return self.env.ref('ordem_servico.action_os_inspecoes').report_action(self)

class OsInspecoesLinhas(models.Model):
    _name = "os.inspecoes.linhas"
    _description = "Linhas Inspeções"

    posicao = fields.Char(string='Posição', size=10, store=True, required=True)
    medida_sol = fields.Float(string='Medida Solicitada', store=True, copy=True)
    medida_real = fields.Float(string='Medida Encontrada', store=True, copy=True)
    medida_total = fields.Float(string='Desvio Total', store=True, copy=True)


    @api.onchange('medida_sol', 'medida_real')
    def _desvio(self):
        for line in self:
            if self.medida_sol and self.medida_real:
                line.update({
                    'medida_total': (self.medida_sol - self.medida_real) * (-1)

                })

# class OsCertificados(models.Model):
#     _name = "os.certificados"
#     _description = "Certificados"

    # data_criacao = fields.Date(string='Data', store=True, copy=True)
    # certificado = fields.Many2many('ir.attachment', 'certificados_os_rel', 'arquivos_id', 'ir_attachment_id',
    #                                string='Certificado', store=True, copy=False, required=True)
    # fornecedor = fields.Many2one('res.partner',string='Fornecedor',store=True, copy=True, required=True)
    # nota_fiscal = fields.Char(string='Número NFE', copy=True, store=True, readonly=False)

class OsFotos(models.Model):
    _name = "os.fotos"
    _description = "Fotos"

    data_criacao = fields.Date(string='Data', store=True, copy=True)
    certificado = fields.Many2many('ir.attachment', 'fotos_os_rel', 'os_fotos_id', 'ir_attachment_id',
                                   string='Certificado', store=True, copy=False)

class OsNfs(models.Model):
    _name = "os.nfs"

    partner_id = fields.Many2one('res.partner', string='Fornecedor', translate=True, readonly=True, required=False,
                                 change_default=True, index=True, related='numero_nfe.partner_id')
    partner_id_saida = fields.Many2one('res.partner', string='Cliente', translate=True, readonly=True, required=False,
                                       change_default=True, index=True, related='nfe_saida.partner_id')

    numero_nfe = fields.Many2many('l10n_br_fiscal.document', 'nfe_entrada_os_rel', 'account_move_id',
                                  'ordem_servico_id',
                                  string='Número NFE', copy=True, store=True, readonly=False)
    # data_emissao = fields.Datetime(string=u"Data da Emissão", translate=True, readonly=True, required=False,
    #                           change_default=True, index=True, tracking=1, related='numero.data_emissao')
    # natureza_operacao = fields.Char(string='Natureza da Operação', translate=True, readonly=True,
    #                                required=False,
    #                                change_default=True, index=True, tracking=1,
    #                                related='numero.natureza_operacao')
    nfe_saida = fields.Many2many('l10n_br_fiscal.document', 'nfe_saida_os_rel', 'account_move_id', 'ordem_servico_id',
                                 string='Número NFE', copy=True, store=True, readonly=False)