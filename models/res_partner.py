from odoo import models

class ResPartner(models.Model):
    _inherit = 'res.partner'

    def name_get(self):
        if self._context.get('show_only_contact_name'):
            return [(partner.id, partner.name) for partner in self]
        return super(ResPartner, self).name_get()