
from odoo import fields, models, api
class OsMrp(models.Model):
    _inherit = "mrp.production"

    ordem_servico = fields.Many2one('ordem.servico', string='Ordem de Serviço', required=False, index=True, copy=False)

    terceiros = fields.Selection([('nenhum','Nenhum'),('laser','Laser'),('dobra','Dobra'),('pintura','Pintura'),('tratamento','Tratamento Químico')],string='Andamento', default='nenhum',store=True, copy=True, required=False)

    @api.model
    def create(self, vals):
        """ Sobrescreve o create para copiar ordem_servico do sale.order quando criado via MTO """
        # Chama o create original primeiro
        record = super(OsMrp, self).create(vals)

        # Se a produção tem origem de uma venda (MTO)
        if record.origin:
            # Busca o sale.order pela origem
            sale_orders = self.env['sale.order'].search([
                ('name', '=', record.origin)
            ])

            # Alternativa: busca pelo procurement group
            if not sale_orders and record.procurement_group_id:
                sale_orders = self.env['sale.order'].search([
                    ('procurement_group_id', '=', record.procurement_group_id.id)
                ])

            # Copia a ordem_servico do sale.order para a produção
            if sale_orders and sale_orders.ordem_servico:
                # Pega a primeira ordem de serviço do sale.order
                ordem_servico_id = sale_orders.ordem_servico[0].id
                record.ordem_servico = ordem_servico_id

                # Log para debug
                _logger.info(
                    f"Ordem de serviço {ordem_servico_id} copiada da venda {sale_orders.name} para produção {record.name}")

        return record

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
