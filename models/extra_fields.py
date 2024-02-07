
from odoo import models, api


class OsAttach(models.Model):
    _inherit = "ir.attachment"

    @api.model
    def create(self, vals):
        publico = {'public': True}
        vals.update(publico)
        return super().create(vals)



