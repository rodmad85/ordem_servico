
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

    dimensoes = fields.Char(string='Dimensões', store=True)
    estoque = fields.Char(string='Estoque', store=True)
    certificado = fields.Boolean(related='product_id.certificado')


class OsStockLine(models.Model):
    _inherit = "stock.move.line"
    ordem_servico = fields.Many2many('ordem.servico', 'stock_move_line_os', 'os_id', 'id',
                                     string='Ordem de Serviço', required=False, index=True, copy=False,
                                     related='move_id.ordem_servico')
    fornecedor = fields.Many2one(string='Fornecedor', related='picking_id.partner_id')


class OsIncoterm(models.Model):
    _inherit = 'account.incoterms'

    def name_get(self):
        result = []
        for rec in self:
            result.append((rec.id, '%s - %s'%(rec.code,rec.name)))
        return result