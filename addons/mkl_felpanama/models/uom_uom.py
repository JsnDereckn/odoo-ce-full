# -*- coding: utf-8 -*-

from odoo import models, fields, api
import logging
_logger = logging.getLogger(__name__)

class UomUom(models.Model):
    _inherit = 'uom.uom'
    
    documentacion_fel = fields.Char(string="Documentación facturación electrónica")