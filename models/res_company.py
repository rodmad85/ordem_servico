from odoo import fields, models, api


class ModelName(models.Model):
    _inherit = "res.company"

    os_req = fields.Boolean('Obrigatorio OS', help='Obrigatorio o preenchimento da OS ao confirmar pedido de venda')
    os_refcli= fields.Boolean('Obrigatorio Referência', help='Obrigatório o preenchimento da Referência do Cliente')
    os_pedcli = fields.Boolean('Obrigatorio Pedido', help='Obrigatório o preenchimento do anexo do Pedido do Cliente')
    os_insp = fields.Boolean('Obrigatorio Inspeções', help='Obrigatório o preenchimento das Inspeções')
    os_aponta = fields.Boolean('Obrigatorio Apontamentos', help='Obrigatório o preenchimento das Horas Trabralhadas')