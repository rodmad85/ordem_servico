from odoo import fields, models, api


class OsProduct(models.Model):
    _inherit = "product.category"

    comercial = fields.Boolean(string='Item Comercial', store=True)
    certificado = fields.Boolean(string='Exige Certificado', store=True)

    @api.onchange('parent_id')
    def _compute_com_cert(self):
        self.certificado = self.parent_id.certificado
        self.comercial = self.parent_id.comercial

# Migrado para product_specific_weight----------------


# class ProdDimensions(models.Model):
#     _inherit = "product.product"
#
#     peso_calc = fields.Float(string='Peso Calculado', digits='Stock Weight', compute='_calcpeso')
#     peso_esp = fields.Float(string='Peso Específico Kg/m³', store=True, copy=True, related='material.peso')
#     material = fields.Many2one('os.pesomateriais', store=True, copy=True)
#     product_length = fields.Float("length", copy=True)
#     product_height = fields.Float("height", copy=True)
#     product_width = fields.Float("width", copy=True)
#     dimensional_uom_id = fields.Many2one(
#         "uom.uom",
#         "Dimensional UoM",
#         domain=lambda self: self._get_dimension_uom_domain(),
#         help="UoM for length, height, width",
#         default=lambda self: self.env.ref("uom.product_uom_meter"), copy=True
#     )
#
#     @api.onchange('volume','peso_esp')
#     def _calc_pesoesp(self):
#         for rec in self:
#             if rec.peso_esp:
#                 rec.peso_calc = rec.volume * rec.peso_esp
#                 rec.weight = rec.peso_calc
#
#
#     def _calcpeso(self):
#
#         if self.product_width != 0 and self.product_height != 0 and self.product_length != 0 and self.volume==0:
#             self.volume = self.env["product.template"]._calc_volume(
#                 self.product_length,
#                 self.product_height,
#                 self.product_width,
#                 self.dimensional_uom_id,
#             )
#             self.peso_calc = self.volume * self.peso_esp
#             self.weight = self.peso_calc
#             exit()
#         if self.volume and self.peso_esp:
#             self.peso_calc = self.volume * self.peso_esp
#             self.weight = self.peso_calc
#         else:
#             self.peso_calc = 0


# class OsPesomateriais(models.Model):
#     _name = "os.pesomateriais"
#
#     name = fields.Char('Nome')
#     peso = fields.Float('Peso Kg/m³')

class OsProductinfo(models.Model):
    _inherit = "product.template"

    certificado = fields.Boolean(string='Exige Certificado', copy=True, store=True, related='categ_id.certificado')
#     product_length = fields.Float("length", copy=True)
#     product_height = fields.Float("height", copy=True)
#     product_width = fields.Float("width", copy=True)
#     peso_esp = fields.Float(string='Peso Específico Kg/m³', store=True, copy=True, related='material.peso')
#     material = fields.Many2one('os.pesomateriais', store=True, copy=True)
#     peso_calc = fields.Float(string='Peso Calculado', digits='Stock Weight', compute='_calcpeso')
#     product_variant_ids = fields.One2many('product.product', 'product_tmpl_id', 'Products', required=True, copy=True)
#
#
#
#     @api.onchange('volume', 'peso_esp')
#     def _calc_pesoesp(self):
#         for rec in self:
#             if rec.peso_esp:
#                 rec.peso_calc = rec.volume * rec.peso_esp
#                 rec.weight = rec.peso_calc
#
#     def _calcpeso(self):
#
#         if self.product_width != 0 and self.product_height != 0 and self.product_length != 0 and self.volume==0:
#             self.volume = self.env["product.template"]._calc_volume(
#                 self.product_length,
#                 self.product_height,
#                 self.product_width,
#                 self.dimensional_uom_id,
#             )
#             self.peso_calc = self.volume * self.peso_esp
#             self.weight = self.peso_calc
#             exit()
#         if self.volume and self.peso_esp:
#             self.peso_calc = self.volume * self.peso_esp
#             self.weight = self.peso_calc
#         else:
#             self.peso_calc = 0
# class OsProductWeight(models.Model):
#     _inherit = "product.template.attribute.line"
#
#     weight = fields.Float('Peso Kg/m³')
