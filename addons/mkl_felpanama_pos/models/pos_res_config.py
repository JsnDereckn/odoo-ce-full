# -*- coding: utf-8 -*-
from odoo import fields, models, api, _

class ResConfigSettings(models.TransientModel):
	_inherit = 'res.config.settings'

	pos_res_partner_id = fields.Many2one(related='pos_config_id.res_partner_id', readonly=False)