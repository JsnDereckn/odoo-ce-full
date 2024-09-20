# -*- coding: utf-8 -*-

from odoo import api, fields, models, tools, _, SUPERUSER_ID
from odoo.exceptions import UserError, ValidationError

import logging
_logger = logging.getLogger(__name__)

class AccountTax(models.Model):
    _inherit = 'account.tax'
    
    tasa_itbms = fields.Many2one('dgi.tasa.itbms', string="Tasa ITBMS")
    
    @api.onchange('amount')
    def _onchange_amount(self):
        for rec in self:
            if rec.amount:
                tasa_found = self.env['dgi.tasa.itbms'].sudo().search([
                    ('name','like',str(int(rec.amount)))
                ])
                if tasa_found:
                    rec.tasa_itbms = tasa_found.id