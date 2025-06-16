
from odoo import fields, models, api
class OsMrp(models.Model):
    _inherit = "mrp.production"

    ordem_servico = fields.Many2many('ordem.servico', 'mrp_rel_os', 'os_id', 'mrp_production_id',
                                     string='Ordem de Serviço', required=False, index=True, copy=False)

    terceiros = fields.Selection([('nenhum','Nenhum'),('laser','Laser'),('dobra','Dobra'),('pintura','Pintura'),('tratamento','Tratamento Químico')],string='Andamento', default='nenhum',store=True, copy=True, required=False)

    def _create_backorder(self):
        backorders = super()._create_backorder()
        for backorder in backorders:
            if self.ordem_servico:
                backorder.write({
                    'ordem_servico': [(6, 0, self.ordem_servico.ids)]
                })
        return backorders

    def _generate_moves(self):
        moves = super()._generate_moves()
        for move in moves:
            if self.ordem_servico:
                move.write({
                    'ordem_servico': [(6, 0, self.ordem_servico.ids)]
                })
                if move.picking_id:
                    move.picking_id.write({
                        'ordem_servico': [(6, 0, self.ordem_servico.ids)]
                    })
        return moves

    def button_mark_done(self):
        res = super().button_mark_done()
        for production in self:
            os_ids = production.ordem_servico.ids
            # Busca pickings gerados pela produção com base no campo origin
            pickings = self.env['stock.picking'].search([('origin', '=', production.origin)])
            for picking in pickings:
                if os_ids:
                    picking.write({'ordem_servico': [(6, 0, os_ids)]})
        return res

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
