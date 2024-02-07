
from odoo import fields, models, api

class OsCertpick(models.Model):
    _inherit = "stock.picking"

    def button_validate(self):
        res = super(OsStockCert, self).button_validate
        for line in lines_to_check:
            if line.certificado is True:
                stock_wizcert()



        return res


    def stock_wizcert(self):
        return {
            'name': "Certificados",
            'type': 'ir.actions.act_window',
            'view_type': 'form',
            'view_mode': 'form',
            'res_model': 'os.stockcert',
            'view_id': self.env.ref('ordem_servico.stockcert_wizard_view').id,
            'target': 'new',
        }

class OsStockcert(models.TransientModel):
    _name = 'os.stockcert'
    _description = 'Certificados Estoque'

    linhas = fields.Many2many('stock.move.line')
    msg = fields.Text(string="Deseja entregar receber todos os certificados?", default="Deseja entregar parcialmente a OS?", readonly=True)

    def comfat(self):
        records = self.env['ordem.servico'].browse(self.env.context.get('active_ids'))
        for rec in records:
            # if rec.entrega_efetiva == False:
            #     raise UserError(_("Digite a data da entrega efetiva para entregar parcialmente a OS."))
            # else:
            #     for rec in records:
                    rec.write({'state': 'parcial'})
                    rec.write({'status_fat': 'parcial'})
                    rec.write({'entrega_efetiva': datetime.today()})
                    rec.message_post(body=_("Entregue Parcialmente e Faturada"))