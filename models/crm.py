from odoo import fields, models


class CrmLead(models.Model):
    _inherit = 'crm.lead'

    medium_id = fields.Many2one(required=True, ondelete="restrict")
    tag_ids = fields.Many2many(required=True, ondelete="restrict")
