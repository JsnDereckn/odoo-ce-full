# -*- coding: utf-8 -*-
from odoo import models, fields

class PosConfig(models.Model):
    _inherit = 'pos.config'

    def default_consumidor_final(self):
        partner_id = False
        consumidor_final_partner = self.env.ref('mkl_felpanama.res_partner_consumidor_final')
        if consumidor_final_partner:
            partner_id = consumidor_final_partner.id
        return partner_id
    
    res_partner_id = fields.Many2one('res.partner', string="Cliente por default", default=default_consumidor_final)


