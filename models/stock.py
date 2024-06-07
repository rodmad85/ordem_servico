
from odoo import fields, models, api


class OsStockQuant(models.Model):
    _inherit = "stock.quant"
    obs = fields.Text(string='Observações', store=True)

    @api.model
    def _get_inventory_fields_write(self):
        res = super()._get_inventory_fields_write()
        res += ['obs']
        return res

    def _get_inventory_fields_create(self):
        res = super()._get_inventory_fields_create()
        res += ['obs']
        return res


class OsStock(models.Model):
    _inherit = "stock.move"

    ordem_servico = fields.Many2many('ordem.servico', 'stock_move_rel_os', 'os_id', 'id',
                                     string='Ordem de Serviço', required=False, index=True, copy=False)
    secondary_uom_qty = fields.Float('Qtd. Secundária')
    secondary_uom_id = fields.Many2one("product.secondary.unit",
        inverse_name="product_movesec_id",
        string="Secondary Unit of Measure",
        help="Default Secondary Unit of Measure.",
    )

    dimensoes = fields.Char(string='Dimensões', store=True)
    estoque = fields.Char(string='Estoque', store=True)
    certificado = fields.Boolean(related='product_id.certificado')
    funcionarios = fields.Many2many('hr.employee', 'stock_move_func_lines', 'move_id', 'move_id_line', compute='_funcionarios')

    def _funcionarios(self):
        for rec in self:
            rec.funcionarios = [(2)]
            linha = rec.id
            teste = self.env['stock.move.line'].search([('move_id','=',linha)]).funcionario.ids
            if teste:
                rec.funcionarios = teste
            else:
                rec.funcionarios = [(5,)]





class OsStockLine(models.Model):
    _inherit = "stock.move.line"
    ordem_servico = fields.Many2many('ordem.servico', 'stock_move_line_os', 'os_id', 'id',
                                     string='Ordem de Serviço', required=False, index=True, copy=False,
                                     related='move_id.ordem_servico')
    secondary_uom_qty = fields.Float('Qtd. Secundária', related='move_id.secondary_uom_qty')
    # secondary_uom_id = fields.Many2one(related='move_id.secondary_uom_id')
    fornecedor = fields.Many2one(string='Fornecedor', related='picking_id.partner_id')
    funcionario = fields.Many2one('hr.employee',store=True)

class OsIncoterm(models.Model):
    _inherit = 'account.incoterms'

    def name_get(self):
        result = []
        for rec in self:
            result.append((rec.id, '%s - %s'%(rec.code,rec.name)))
        return result
class OSPicking(models.Model):
    _inherit = 'stock.picking'

    partner_id_carrier = fields.Many2one('res.partner', string='Partner', required=True,ondelete='restrict')

# class OsStockCertWiz(models.TransientModel):
#     _name = 'os.stockcert.wizard'
#     _description = 'Certificado Wizard'
#
#     msg = fields.Text(string="Deseja receber todos os certificados?", default="Deseja receber todos os certificados?", readonly=True)
#     linhas = fields.One2many('stock.move', 'product_move_cert', string='Produtos com Certificado')
#
#     def action_done(self):
#         for line in self.linhas.mapped('certificado'):
#             line.button_done_cert()
#
# class OsStockCertwizLine(models.TransientModel):
#     _name = 'os.stockcert.wizard.line'
#     _description = 'Linhas Certificados Wizard'
#
#     product_id = fields.Many2one('product.product','Produto')



#         _inherit = "stock.picking"

    # def button_validate(self):
    #     super(OsStockPicking,self).button_validate(self)
    #     picks = self.env['stock.picking'].search([('certificado', '=', True)])
    #     if picks:
    #         view = self.env.ref('os.stockcert.view')
    #         return {
    #             'name': _('Certificados'),
    #             'type': 'ir.actions.act_window',
    #             'view_mode': 'form',
    #             'res_model': 'os.stockcert.wizard',
    #             'views': [(view.id, 'form')],
    #             'view_id': view.id,
    #             'target': 'new',
    #             'context': dict(self.env.context,
    #                             default_pick_ids=[(4, picks.id) for picks in self]),
    #         }

        #Cria a lista de produtos com certificado
