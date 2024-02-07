
from odoo import fields, models, api
class CalcAttribute (models.Model):
    _inherit = "product.attribute.value"

    name = fields.Char()


class ProdDimensions(models.Model):
    _inherit = "product.product"

    peso_esp = fields.Float(string="Peso Específico Kg/m³", store=True, compute="_calc_pesoesp")

    def _calc_pesoesp(self):
        for rec in self:
            if rec.peso_esp:
                rec.weight = rec.volume * rec.peso_esp


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


