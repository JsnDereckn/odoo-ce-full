# -*- coding: utf-8 -*-

from odoo import models, fields, api
import logging
_logger = logging.getLogger(__name__)

class DGITipoReceptor(models.Model):
    _name = 'dgi.tipo.receptor'
    _description = 'Tipo de receptor DGI'
    
    name = fields.Char(string="Tipo de receptor")
    codigo = fields.Char(string="Código DGI")
    
class DGITipoDocumento(models.Model):
    _name = 'dgi.tipo.documento'
    _description = 'Tipo de documento DGI'
    
    name = fields.Char(string="Tipo de documento")
    codigo = fields.Char(string="Código DGI")
    
class DGITipoSucursal(models.Model):
    _name = 'dgi.tipo.sucursal'
    _description = 'Tipo de sucursal DGI'
    
    name = fields.Char(string="Tipo de sucursal")
    codigo = fields.Char(string="Código DGI")
    
class DGITipoRUC(models.Model):
    _name = 'dgi.tipo.ruc'
    _description = 'Tipo de RUC (contribuyente) DGI'
    
    name = fields.Char(string="Tipo de RUC (contribuyente)")
    codigo = fields.Char(string="Código DGI")
    
class DGIBienesServicios(models.Model):
    _name = 'dgi.bienes.servicios'
    _description = 'Bien o servicio DGI'
    
    name = fields.Char(string="Bien o servicio")
    codigo = fields.Char(string="Código bien o servicio")
    
class DGITasasITBMS(models.Model):
    _name = 'dgi.tasa.itbms'
    _description = 'Tasa del ITBMS aplicable'
    
    name = fields.Char(string="Nombre")
    codigo = fields.Char(string="Código")