import datetime
from odoo import fields, models, api, _
from odoo.exceptions import UserError



class HrEmployee(models.Model):
    _inherit = "hr.employee"
    valor_hora = fields.Float(string='Valor Hora', store=True)


class HrFields(models.Model):
    _inherit = "hr.attendance"

    ordem_servico = apontamento = fields.Many2many('ordem.servico', 'hr_attendance_os_rel', 'hr_attendance_id',
                                                   'ordem_servico_id',
                                                   string='Linha Apontamento', store=True, copy=True)
    valor_hora = fields.Float(string='Valor Hora', related='employee_id.valor_hora', readonly=True, store=True)
    retrabalho = fields.Boolean(string='Retrabalho', store=True)
    valor_total = fields.Float(string='Valor Total', readonly=True, store=True, compute='_total')

    @api.depends('valor_hora', 'worked_hours', 'valor_total')
    def _total(self):
        entnormal = "07:12:00"
        sainormal = "17:00:00"
        entalm ="12:00:00"
        saialm="13:00:00"
        ininot = "22:00:00"

        for line in self:
            entrada = datetime.strptime(self.check_in, "%H:%M:%S")
            saida = datetime.strptime(self.check_out, "%H:%M:%S")

#Calcula horas normais e subtrai o horario do almoço.
            if entrada >= entnormal and saida <= sainormal:
                if saida >= saialm and entrada <= entalm:
                    line.update({
                        'valor_total': line.valor_hora * (line.worked_hours - 3600)
                    })
#calcula hora extra

            if saida > sainormal and saida <= ininot:
                extra = saida - entrada
                extra = extra.total_seconds() / 3600
#Hora noturna-------------------------------
                if entrada > sainormal:
                    extra = saida - entrada
                    line.update({
                        'valor_total': line.valor_hora * (line.worked_hours - 3600)
                    })
#Verifica se teve horario de almoço
                    if saida >= saialm and entrada <= entalm:
                        line.update({
                            'valor_total': (line.valor_hora * (line.worked_hours - 3600)) + (extra * line.valor_hora * 1.5)
                        })
                    else:
                        line.update({
                            'valor_total': line.valor_hora * (line.worked_hours - extra) + (extra * line.valor_hora * 1.5)
                        })
#Extra normal--------------------------------
                else:
                    extra = saida - sainormal
                    line.update({
                        'valor_total': line.valor_hora * (line.worked_hours - 3600)
                    })
            # if entrada >= "00:01:00" and entrada < entnormal:



class OsCertificados(models.Model):
    _name = "os.certificados"
    _description = "Certificados"

    data_criacao = fields.Date(string='Data', store=True, copy=True)
    certificado = fields.Many2many('ir.attachment', 'certificados_os_rel', 'arquivos_id', 'ir_attachment_id',
                                   string='Certificado', store=True, copy=False)
    nota_fiscal = fields.Many2one('eletronic.document', string='Número NFE', copy=True, store=True, readonly=False)


class OsFotos(models.Model):
    _name = "os.fotos"
    _description = "Fotos"

    data_criacao = fields.Date(string='Data', store=True, copy=True)
    certificado = fields.Many2many('ir.attachment', 'fotos_os_rel', 'os_fotos_id', 'ir_attachment_id',
                                   string='Certificado', store=True, copy=False)


class OsPedidosCliente(models.Model):
    _name = "os.pedcli"
    _description = "Pedidos Cliente"

    data_criacao = fields.Date(string='Data', store=True, copy=True)
    pedido = fields.Many2many('ir.attachment', 'pedidos_os_rel', 'pedido_id', 'ir_attachment_id',
                              string='Pedido', store=True, copy=True)


class OsDesenhos(models.Model):
    _name = "os.desenhos"
    _description = "Desenhos"

    data_criacao = fields.Date(string='Data', store=True, copy=True)
    documento = fields.Char(string='Documento', store=True, copy=True)
    arquivo = fields.Many2many('ir.attachment', 'desenhos_os_rel', 'arquivos_id', 'ir_attachment_id',
                               string='Desenho', store=True, copy=True)
    os_arq = fields.Many2one('ordem.servico', string='Ordem de Serviço',
                             required=True, ondelete='cascade', index=True, copy=False)
    tipo = fields.Selection(
        [('Foto', 'Foto'), ('Peça', 'Peça'), ('Montagem', 'Montagem'), ('Plano de Corte', 'Plano de Corte')],
        string='Tipo', store=True, copy=True, required=True)
    setor = fields.Selection(
        [('Caldeiraria', 'Caldeiraria'), ('Equipamentos', 'Equipamentos'), ('Usinagem', 'Usinagem'),
         ('Outros', 'Outros')],
        string='Setor', store=True, copy=True, required=True)


# Campos adicionais(extra_fields)----------------------------------------------------------
class OsPurchaseLine(models.Model):
    _inherit = "purchase.order.line"

    ordem_servico = fields.Many2many('ordem.servico', 'purchase_order_line_os_rel', 'purchase_order_line_id', 'os_id',
                                     string='Pedidos de Compra', store=True, copy=True)

    @api.model
    def _prepare_stock_move_vals(self, picking, price_unit, product_uom_qty, product_uom):
        vals = super(OsPurchaseLine, self)._prepare_stock_move_vals(picking, price_unit, product_uom_qty, product_uom)
        vals['ordem_servico'] = self.ordem_servico.ids
        return vals



class OsPurchase(models.Model):
    _inherit = "purchase.order"

    forma_pagamento = fields.Many2one('payment.acquirer', string='Forma de Pagamento', required=False,
                                      ondelete='restrict', index=True, copy=False)

    oss = fields.One2many('os.total.purchase', 'id', string='Total OS', compute='get_values', copy=True)
    @api.model
    def get_values(self):
        ids =self.order_line
        ordens = tuple(set(ids.ordem_servico))
        total = 0

        for rec in ordens:
            total = 0
            for id in ids:
                contagem = len(id.ordem_servico)
                for o in id.ordem_servico:
                    if rec.id == o.id:
                        total += id.price_total / contagem
            self.oss += self.env['os.total.purchase'].create({'os': rec.name, 'valor': total})



class TotalOs(models.Model):
    _name = "os.total.purchase"
    os = fields.Char(string="Ordem de Serviço")
    valor = fields.Float(string="Total")
class OsStock(models.Model):
    _inherit = "stock.move"

    ordem_servico = fields.Many2many('ordem.servico', 'stock_move_rel_os', 'os_id', 'id',
                                     string='Ordem de Serviço', required=False, index=True, copy=False)


class OsStockLine(models.Model):
    _inherit = "stock.move.line"
    ordem_servico = fields.Many2many('ordem.servico', 'stock_move_line_os', 'os_id', 'id',
                                     string='Ordem de Serviço', required=False, index=True, copy=False,
                                     related='move_id.ordem_servico')
    fornecedor = fields.Many2one(string='Fornecedor', related='picking_id.partner_id')


class OsMrp(models.Model):
    _inherit = "mrp.production"

    ordem_servico = fields.Many2many('ordem.servico', 'mrp_rel_os', 'os_id', 'mrp_production_id',
                                     string='Ordem de Serviço', required=False, index=True, copy=False)


class OsSale(models.Model):
    _inherit = ["sale.order"]

    ordem_servico = fields.Many2many('ordem.servico', 'ordem_servico_rel_sale', 'sale_order_id', 'os_id',
                                     string='Ordem de Serviço', required=False, index=True,
                                     copy=True, store=True, readonly=False)
    horas_mo = fields.Integer(string='Total Horas', store=True)
    valor_horas = fields.Monetary(string='Valor Horas', store=True)
    imposto = fields.Many2one('os.impostos.line', string='Imposto %', store=True)
    materia_prima = fields.Monetary(string='Matéria Prima', store=True)
    terceiros = fields.Monetary(string='Terceiros', store=True)
    resultado = fields.Monetary(string='Total Sem Imposto', store=False, compute='_amount_resultado')
    partner_id = fields.Many2one(
        'res.partner', string='Customer', readonly=True,
        states={'draft': [('readonly', False)], 'sent': [('readonly', False)]},
        required=True, change_default=True, index=True, tracking=1,
        domain="['|', ('company_id', '=', False), ('company_id', '=', company_id)]", )


    @api.depends('valor_horas', 'materia_prima', 'terceiros')
    def _amount_resultado(self):
        for rec in self:
            rec.update({'resultado': rec.valor_horas + rec.materia_prima + rec.terceiros})

    @api.model
    def _action_cancel(self):

        oss = self.ordem_servico.ids
        for os in oss:
            self.env['ordem.servico'].browse(os).write({'state': 'draft'})

        res = super(OsSale, self)._action_cancel()
        return res

    def _action_confirm(self):

        oss = self.ordem_servico.ids
        name = self.name
        for os in oss:
            self.env['ordem.servico'].browse(os).write({'state': 'aberta'})


        producao = self.env['mrp.production'].search([('origin', '=', name)])
        producao.write({'ordem_servico': oss})

        res = super(OsSale, self)._action_confirm()
        return res

class OsSaleLine(models.Model):
    _inherit = ["sale.order.line"]

    mo_line = fields.Monetary(string='Mão de Obra', store=True)
    mp_line = fields.Monetary(string='Materia Prima', store=True)

class OsImpostos(models.Model):
    _inherit = ["account.fiscal.position"]

    meses = fields.Many2many('os.impostos.line', 'os_impostos_line_rel', 'os_impostos_line_id', 'impostos_id',
                             string="Taxas", required=False, ondelete='cascade')


class OsImpostosLine(models.Model):
    _name = "os.impostos.line"

    fiscal_position = fields.Many2one('account.fiscal.position', string="Posição Fiscal", default=lambda self: self.id,
                                      store=True)
    mes = fields.Date(string='Data', store=True, copy=True, required=True)
    name = fields.Char(string='Name', store=True, compute='_compute_name')
    percentual = fields.Float(string='Percentual', store=True, required=True)

    @api.depends('mes')
    def _compute_name(self):

        for record in self:
            nome = datetime.date.strftime(record.mes, '%m/%Y')
            busca = self.search([('name', '=', nome)])
        if busca:
            raise UserError(_("Já existe lancamento no mesmo período"))
        else:
            for record in self:
                record.name = datetime.date.strftime(record.mes, '%m/%Y')


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
