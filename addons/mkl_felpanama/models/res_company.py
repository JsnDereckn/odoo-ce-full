# -*- coding: utf-8 -*-

from odoo import models, fields, api
import logging
_logger = logging.getLogger(__name__)

URL_HKA = "https://emision.thefactoryhka.com.pa/ws/obj/v1.0/Service.svc"

class ResCompany(models.Model):
    _inherit = 'res.company'
    
    @api.onchange('test_fel')
    def test_fel_change(self):
        for rec in self:
            if rec.test_fel:
                rec.token_empresa = "numnskxocrwv_tfhka"
                rec.token_password = ",a@w@hL,;uuX"
                rec.codigo_sucursal_emisor = "0004"
                rec.tipo_sucursal_fel = 1 #Por default el primer valor
                rec.url_hka = "https://demoemision.thefactoryhka.com.pa/ws/obj/v1.0/Service.svc"
                rec.punto_facturacion_fiscal = "001"
            else:
                rec.token_empresa = ""
                rec.token_password = ""
                rec.codigo_sucursal_emisor = ""
                rec.tipo_sucursal_fel = None
                rec.url_hka = URL_HKA
                rec.punto_facturacion_fiscal = ""
    
    test_fel = fields.Boolean(string="Modo pruebas")
    url_hka = fields.Char(string="URL API HKA", default=URL_HKA)
    token_empresa = fields.Char(string='Token Empresa')
    token_password = fields.Char(string='Token Password')
    codigo_sucursal_emisor = fields.Char(string="Código sucursal emisor")
    tipo_sucursal_fel = fields.Many2one('dgi.tipo.sucursal', string="Tipo de sucursal")
    punto_facturacion_fiscal = fields.Char(string="Punto facturación fiscal")
    num_factura_inicial = fields.Integer(string="Offset facturación", default=0)
    
    
