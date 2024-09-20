# -*- coding: utf-8 -*-
import logging
_logger = logging.getLogger(__name__)

from odoo import api, fields, models, tools, _
from odoo.exceptions import ValidationError, UserError

class PosSession(models.Model):
    _inherit = "pos.session"
    
    def _loader_params_res_partner(self):
        return {
            'search_params': {
                'domain': self._get_partners_domain(),
                'fields': [
                    'name', 'street', 'city', 'state_id', 'country_id', 'vat', 'dv', 'tipo_receptor', 'tipo_ruc', 'lang', 'phone', 'zip', 'mobile', 'email',
                    'barcode', 'write_date', 'property_account_position_id', 'property_product_pricelist', 'parent_name'
                ],
            },
        }
        
    def _loader_params_dgi_tipo_ruc(self):
        return {'search_params': {'domain': [], 'fields': ['name', 'codigo']}}

    def _get_pos_ui_dgi_tipo_ruc(self, params):
        return self.env['dgi.tipo.ruc'].search_read(**params['search_params'])
    
    def _loader_params_dgi_tipo_receptor(self):
        return {'search_params': {'domain': [], 'fields': ['name', 'codigo']}}

    def _get_pos_ui_dgi_tipo_receptor(self, params):
        return self.env['dgi.tipo.receptor'].search_read(**params['search_params'])
        
    @api.model
    def _pos_ui_models_to_load(self):
        models_to_load = super(PosSession, self)._pos_ui_models_to_load()
        models_to_load.append('dgi.tipo.ruc')
        models_to_load.append('dgi.tipo.receptor')
        return models_to_load