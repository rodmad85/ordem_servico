from odoo import fields, models


class BaseDocumentLayout(models.TransientModel):
    _inherit = 'base.document.layout'

    mobile = fields.Char(related='company_id.mobile', readonly=True)
    cnpj_cpf = fields.Char(related='company_id.cnpj_cpf', readonly=True)
    inscr_est = fields.Char(related='company_id.inscr_est', readonly=True)
    inscr_mun = fields.Char(related='company_id.inscr_mun', readonly=True)
    l10n_br_ie_code = fields.Char(related='company_id.l10n_br_ie_code', readonly=True)
    l10n_br_im_code = fields.Char(related='company_id.l10n_br_im_code', readonly=True)
