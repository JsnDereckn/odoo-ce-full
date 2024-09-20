# -*- coding: utf-8 -*-

from odoo import models, fields, api
from odoo.tools.translate import _
from odoo.exceptions import UserError

import logging
_logger = logging.getLogger(__name__)

class AccountMoveReversal(models.TransientModel):
    _inherit = 'account.move.reversal'
    
    reversed_entry_ids = fields.Many2many('account.reversal.fel', string="FEL's relacionadas")
    
    def reverse_moves(self, is_modify=False):
        action = super(AccountMoveReversal, self).reverse_moves(is_modify=False)
        nota_credito_rel = self.env['dgi.tipo.documento'].search([('codigo','=','04')], limit=1)
        
        moves_for_reversal = self.env['account.move'].browse(self.env.context['active_ids']) if self.env.context.get('active_model') == 'account.move' else self.env['account.move']
        
        reversal_recs = []
        if len(moves_for_reversal) > 0:
            for move in moves_for_reversal:
                reversal_recs.append((0, 0, {
                    'name': move.id
                }))
        
        for new_reversal in self.new_move_ids:
            new_reversal.write({
                'es_nota_credito_relacionada': True,
                'tipo_documento_fel': nota_credito_rel.id,
                'reversed_entry_ids': reversal_recs
            })
        
        return action