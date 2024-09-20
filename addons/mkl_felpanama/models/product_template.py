# -*- coding: utf-8 -*-

from collections import defaultdict

from odoo import api, fields, models, tools, _, SUPERUSER_ID
from odoo.exceptions import UserError, ValidationError
from odoo.osv import expression

import logging
_logger = logging.getLogger(__name__)

class ProductTemplate(models.Model):
    _inherit = 'product.template'

    @tools.ormcache()
    def _get_default_uom_id(self):
        default_uom_id = self.env['uom.uom'].sudo().search([('name','=','und')],limit=1)
        return default_uom_id.id
    
    uom_id = fields.Many2one(
        'uom.uom', 'Unidad de medida',
        default=_get_default_uom_id, required=True,
        help="Default unit of measure used for all stock operations.")
    
    codigo_fel = fields.Many2one('dgi.bienes.servicios', string="Código facuración electrónica")