# -*- coding: utf-8 -*-

from odoo import models, fields, api
import logging
_logger = logging.getLogger(__name__)

class AccountReversalFEL(models.Model):
    _name = 'account.reversal.fel'
    _description = 'Factura relacionada a nota de crédito FEL Panamá'
    
    name = fields.Many2one('account.move', string="Factura electrónica relacionada", domain=[('move_type', '=', 'out_invoice'), ('resultado_fel','=','procesado')], required=True)
    move_id = fields.Many2one('account.move', string="Nota de crédito")