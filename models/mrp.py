
from odoo import fields, models, api
class OsMrp(models.Model):
    _inherit = "mrp.production"

    ordem_servico = fields.Many2many('ordem.servico', 'mrp_rel_os', 'os_id', 'mrp_production_id',
                                     string='Ordem de Serviço', required=False, index=True, copy=False)
    andamento = fields.Selection([('material','Aguardando Material'),('terceiro','Terceiros'),('usinagem','Usinagem'),('corte', 'Corte'), ('dobra', 'Dobra'), ('solda', 'Solda'), ('montagem', 'Montagem'), ('acabamento','Acabamento'), ('teste','Testando'),('parcial','Parcialmente Pronto'),('pronto','Todos Prontos')], default='material',
        string='Andamento', store=True, copy=True, required=True)
    terceiros = fields.Selection([('nenhum','Nenhum'),('laser','Laser'),('dobra','Dobra'),('pintura','Pintura'),('tratamento','Tratamento Químico')],string='Andamento', default='nenhum',store=True, copy=True, required=False)


    @api.model
    def _get_move_raw_values(self, product_id, product_uom_qty, product_uom, operation_id=False, bom_line=False):
        vals = super(OsMrp, self)._get_move_raw_values(product_id, product_uom_qty, product_uom, operation_id=False, bom_line=False)
        vals['dimensoes'] =  bom_line.dimensoes
        vals['estoque'] = bom_line.estoque

        return vals

    @api.onchange('andamento')
    def _seleciona_terceiro(self):
        if self.andamento != 'terceiro':
            self.terceiros = 'nenhum'

    def name_get(self):
        result = []
        for rec in self:
            result.append((rec.id, '%s'%(rec.product_id.name)))
        return result

class OsMrpBomLine(models.Model):
    _inherit = "mrp.bom.line"

    dimensoes = fields.Char(string='Dimensões', store=True)
    estoque = fields.Char(string='Em estoque', store=True)
    funcionarios = fields.Many2one('hr.employee')
    valor = fields.Float(related='product_id.standard_price')
