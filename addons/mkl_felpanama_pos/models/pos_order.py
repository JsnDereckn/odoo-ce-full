# -*- coding: utf-8 -*-
import logging
_logger = logging.getLogger(__name__)

from odoo import api, fields, models, tools, _
from odoo.exceptions import ValidationError, UserError

class PosOrder(models.Model):
    _inherit = "pos.order"
    
    def _create_invoice(self, move_vals):
        move_type = move_vals['move_type']
        codigo_doc = "01"
        
        if move_type == "out_refund":
            codigo_doc = "04"
            pos_refunded_invoice_ids = move_vals['pos_refunded_invoice_ids']
            reversal_ids = []
            for move_id in pos_refunded_invoice_ids:
                reversal_ids.append((0, 0, {
                    'name': move_id
                }))
            move_vals['es_nota_credito_relacionada'] = True
            # move_vals['reversed_entry_ids'] = reversal_ids
            move_vals['reversed_entry_ids'] = [(0, 0, {
                    'name': pos_refunded_invoice_ids[0]
                })]
            # raise ValidationError(f"*move_vals POS: {move_vals}")
            
        doc_type_fel = self.env['dgi.tipo.documento'].sudo().search([('codigo','=',codigo_doc)],limit=1)
        move_vals['tipo_documento_fel'] = doc_type_fel.id
        new_move = super(PosOrder, self)._create_invoice(move_vals)
        new_move.crear_folio_fel()
        return new_move