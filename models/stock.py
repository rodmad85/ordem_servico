import logging
from odoo import fields, models, api

_logger = logging.getLogger(__name__)

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

    ordem_servico = fields.Many2many('ordem.servico', 'stock_move_rel_os', 'os_id', 'id')
    dimensoes=fields.Char(string='Dimensões', store=True)
    estoque = fields.Char(string='Estoque', store=True)
    certificado = fields.Boolean(related='product_id.certificado')
    funcionarios = fields.Many2many('hr.employee', 'stock_move_func_lines', 'move_id', 'move_id_line',
                                    compute='_funcionarios')

    def _funcionarios(self):
        for rec in self:
            rec.funcionarios = [(2)]
            linha = rec.id
            teste = self.env['stock.move.line'].search([('move_id', '=', linha)]).funcionario.ids
            if teste:
                rec.funcionarios = teste
            else:
                rec.funcionarios = [(5,)]

    @api.depends('raw_material_production_id.ordem_servico', 'production_id.ordem_servico')
    def _compute_ordem_servico(self):
        for move in self:
            if move.raw_material_production_id:
                move.ordem_servico = move.raw_material_production_id.ordem_servico
            elif move.production_id:
                move.ordem_servico = move.production_id.ordem_servico

    def _set_ordem_servico(self):
        """Método vazio necessário para campos computados editáveis"""
        pass

class OsStockLine(models.Model):
    _inherit = "stock.move.line"
    ordem_servico = fields.Many2many(
        'ordem.servico',
        'stock_move_line_os_rel',  # Nome diferente para evitar conflito
        'move_line_id',  # Referência ao move.line
        'os_id',  # Referência à ordem de serviço
        string='Ordem de Serviço',
        compute='_compute_ordem_servico',
        store=True
    )
    fornecedor = fields.Many2one(string='Fornecedor', related='picking_id.partner_id')
    funcionario = fields.Many2one('hr.employee', store=True)
    placa = fields.Char(string='Placa', size=7)

    @api.depends('move_id.ordem_servico')
    def _compute_ordem_servico(self):
        for line in self:
            line.ordem_servico = line.move_id.ordem_servico


class OsIncoterm(models.Model):
    _inherit = 'account.incoterms'

    def name_get(self):
        result = []
        for rec in self:
            result.append((rec.id, '%s - %s' % (rec.code, rec.name)))
        return result


class OSPicking(models.Model):
    _inherit = 'stock.picking'

    part_carrier = fields.Char(string='Motorista')
    rg_cpf = fields.Char(string='RG/CPF')
    carrier_track_ref = fields.Char(string='Placa')

    ordem_servico = fields.Many2many(
        'ordem.servico',
        'stock_picking_rel_os',
        'picking_id',
        'os_id',
        string='Ordem de Serviço',
        required=False,
        index=True,
        store=True,
        copy=False

    )


class StockRule(models.Model):
    _inherit = "stock.rule"

    def _run_manufacture(self, procurements):
        productions = super()._run_manufacture(procurements)
        for production in productions:
            _logger.info(
                "MO Criada: %s | Produto: %s | BoM: %s | Regra disparada: %s",
                production.name,
                production.product_id.display_name,
                production.bom_id.display_name,
                production.rule_id.name
            )
        return productions