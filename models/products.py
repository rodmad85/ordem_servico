
from odoo import fields, models, api
class CalcAttribute (models.Model):
    _inherit = "product.attribute.value"

    name = fields.Char()


class ProdDimensions(models.Model):
    _inherit = "product.product"

    peso_esp = fields.Float(string='Peso Específico Kg/m³', store=True, default=7800)
    peso_calc = fields.Float(string='Peso Calculado', digits='Stock Weight', compute='_calcpeso')

    @api.onchange('volume','peso_esp')
    def _calc_pesoesp(self):
        for rec in self:
            if rec.peso_esp:
                rec.peso_calc = rec.volume * rec.peso_esp
                rec.weight = rec.peso_calc


    def _calcpeso(self):

        if self.product_width != 0 and self.product_height != 0 and self.product_length != 0 and self.volume==0:
            self.volume = self.env["product.template"]._calc_volume(
                self.product_length,
                self.product_height,
                self.product_width,
                self.dimensional_uom_id,
            )
            self.peso_calc = self.volume * self.peso_esp
            self.weight = self.peso_calc
            exit()
        if self.volume and self.peso_esp:
            self.peso_calc = self.volume * self.peso_esp
            self.weight = self.peso_calc
        else:
            self.peso_calc = 0




class OsProduct(models.Model):
    _inherit = "product.category"

    comercial = fields.Boolean(string='Item Comercial', store=True)
    certificado = fields.Boolean(string='Exige Certificado', store=True)

    @api.onchange('parent_id')
    def _compute_com_cert(self):
        self.certificado = self.parent_id.certificado
        self.comercial = self.parent_id.comercial

class OsProductinfo(models.Model):
    _inherit = "product.template"

    certificado = fields.Boolean(string='Exige Certificado', store=True, related='categ_id.certificado')


