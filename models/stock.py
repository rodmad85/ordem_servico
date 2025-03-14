
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
    # secondary_uom_qty = fields.Float('Qtd. Secundária', related='move_id.secondary_uom_qty')
    # secondary_uom_id = fields.Many2one(related='move_id.secondary_uom_id')
    fornecedor = fields.Many2one(string='Fornecedor', related='picking_id.partner_id')
    funcionario = fields.Many2one('hr.employee',store=True)
    placa = fields.Char(string='Placa', size=7)


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

