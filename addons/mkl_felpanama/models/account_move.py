# -*- coding: utf-8 -*-

from datetime import datetime, timezone
from odoo.http import request
from urllib.parse import quote
import xml.etree.ElementTree as ET
from odoo.exceptions import ValidationError, UserError
from odoo import models, fields, api, http, _
import requests
import logging
_logger = logging.getLogger(__name__)
from pathlib import Path
import base64
import io

from odoo.tools import config

class AccountMove(models.Model):
    _inherit = 'account.move'

    @api.depends('invoice_datetime')
    @api.onchange('invoice_datetime')
    def get_default_invoice_datetime(self):
        for rec in self:
            rec.invoice_date = rec.invoice_datetime

    def format2digits(self, number):
        return f"{number:.2f}"
    
    def format3digits(self, number):
        return f"{number:.3f}"
    
    def format4digits(self, number):
        return f"{number:.4f}"
    
    def isFalseThenEmpty(self, value):
        return value if value else ""

    def isFalseThenEmptySpace(self, value):
        return f"{value} " if value else ""
    
    invoice_datetime = fields.Datetime(string='Fecha y hora de factura', index=True, copy=False, default=lambda self: fields.Datetime.now())
    
    @api.depends('move_type')
    def _get_focumento_fel_records(self):
        for rec in self:
            domain = [('codigo','in',['-1'])] # Inicialización para dominio vacio
            if rec.move_type == "out_invoice":
                allowed_doc_type_codes = []
                allowed_doc_type_codes.append('01') #Factura operación interna
                allowed_doc_type_codes.append('02') #Factura de importación
                allowed_doc_type_codes.append('03') #Factura de exportación
                allowed_doc_type_codes.append('08') #Factura de zona franca
                domain = [('codigo','in', allowed_doc_type_codes)]
            
            if rec.move_type == "out_refund":
                allowed_doc_type_codes = []
                allowed_doc_type_codes.append('04') #Nota de crédito referencia a una o varias FE
                allowed_doc_type_codes.append('06') #Nota de crédito genérica
                domain = [('codigo','in', allowed_doc_type_codes)]
                
            tipos_doc = self.env["dgi.tipo.documento"].search(domain)
            
            if len(tipos_doc) > 0:
                rec.tipos_documento_fel_permitidos = tipos_doc
            else:
                rec.tipos_documento_fel_permitidos = None
    
    tipos_documento_fel_permitidos = fields.Many2many('dgi.tipo.documento', compute=_get_focumento_fel_records)
    
    tipo_documento_fel = fields.Many2one('dgi.tipo.documento', string="Tipo de documento", domain="[('id', 'in', tipos_documento_fel_permitidos)]", required=False)
    
    def getDocumentNumber(self):
        company = self.env.company
        num_factura_inicial = company.num_factura_inicial
        return str(self.id + num_factura_inicial).zfill(6)
    
    def has_more_than_two_decimals(self, number):
        str_number = str(number)
        parts = str_number.split('.')
        if len(parts) == 2 and len(parts[1]) > 2:
            return True
        else:
            return False

    def fel_values(self):
        company = self.env.company
        partner_id = self.partner_id
        token_empresa = company.token_empresa
        token_password = company.token_password
        codigo_sucursal_emisor = company.codigo_sucursal_emisor
        numeroDocumentoFiscal = self.getDocumentNumber()

        razonSocial = partner_id.name
        fecha_emision = f"{self.invoice_datetime.strftime('%Y-%m-%dT%H:%M:%S%z')}{'-05:00'}"

        self.check_not_filled_fields()

        lista_items = []
        totalITBMS = 0

        for item in self.invoice_line_ids:
            product_id = item.product_id
            impuestos = 0
            tasaITBMS = "01"
            for tax in item.tax_ids:
                impuestos += tax.amount * 0.01
                if not tax.tasa_itbms:
                    raise UserError(f"El impuesto {tax.name} no tiene configurada una tasa de ITBMS.") 
                tasaITBMS = tax.tasa_itbms.codigo

            valorITBMS = impuestos * (item.price_subtotal)
            totalITBMS += valorITBMS
            
            codigoCPBS = product_id.codigo_fel.codigo
            codigo = product_id.default_code if product_id.default_code else ""
            
            uom = product_id.uom_id.name
            
            if not uom:
                raise UserError(f"El producto {product_id.name} no tiene configurada una unidad de medida.") 
            
            
            precio_unitario_descuento = (item.discount / 100) * item.price_unit
            
            precio_unitario_descuento = self.format4digits(precio_unitario_descuento)
            
            # if not self.has_more_than_two_decimals(precio_unitario_descuento):
            #     precio_unitario_descuento =  self.format2digits(precio_unitario_descuento)
            # else:
            #     precio_unitario_descuento
            precio_item = item.price_subtotal
                
            lista_items.append({
                "descripcion": item.name,
                "codigo": codigo,
                "codigoCPBS": codigoCPBS,
                "unidadMedida": uom,
                "cantidad": self.format2digits(item.quantity),
                "precioUnitario": self.format2digits(item.price_unit),
                "precioUnitarioDescuento": precio_unitario_descuento,
                "precioItem": self.format2digits(precio_item),
                "valorTotal": self.format2digits(item.price_total),
                "tasaITBMS": tasaITBMS,
                "valorITBMS": self.format2digits(valorITBMS),
            })
            
        direccion = f"{self.isFalseThenEmptySpace(partner_id.street)}{self.isFalseThenEmptySpace(partner_id.street2)}{self.isFalseThenEmptySpace(partner_id.city)}{self.isFalseThenEmptySpace(partner_id.state_id.name)}{self.isFalseThenEmptySpace(partner_id.country_id.name)}{self.isFalseThenEmptySpace(partner_id.zip)}".rstrip()
        
        destinoOperacion = "1"
        
        if self.tipo_documento_fel.codigo == "03":
            destinoOperacion = "2" #Exportación
        
        fel_relacionadas = []
        if self.tipo_documento_fel.codigo == "04":
            for fact in self.reversed_entry_ids:
                fel_relacionadas.append({
                    'fechaEmisionDocFiscalReferenciado': fact.name.fecha_emision_dgi_fel,
                    'cufeFEReferenciada': fact.name.cufe_fel
                })
        
        fechaVenceCuota = self.invoice_date_due.strftime('%Y-%m-%dT%H:%M:%S%z-05:00')
        
        return {
            "tokenEmpresa": token_empresa,
            "tokenPassword": token_password,
            "codigoSucursalEmisor": codigo_sucursal_emisor,
            "tipoDocumento": self.tipo_documento_fel.codigo,
            "numeroDocumentoFiscal": numeroDocumentoFiscal,
            "fechaEmision": fecha_emision,
            "destinoOperacion": destinoOperacion,
            "nroIdentificacionExtranjero": partner_id.vat if partner_id.vat else "",
            "tipoClienteFE": partner_id.tipo_receptor.codigo,
            "tipoContribuyente": partner_id.tipo_ruc.codigo,
            "numeroRUC": partner_id.vat,
            "digitoVerificadorRUC": partner_id.dv,
            "razonSocial": partner_id.name,
            "direccion": direccion,
            "telefono1": partner_id.phone if partner_id.phone else "",
            "correoElectronico1": self.isFalseThenEmpty(partner_id.email),
            "pais": partner_id.country_id.code,
            "razonSocial": razonSocial,
            "condicionesEntrega": self.condiciones_entrega_fel,
            "monedaOperExportacion": self.moneda_exportacion.name,
            "puertoEmbarque": self.puerto_embarque,
            "listaItems": lista_items,
            "nroItems": len(lista_items),
            "totalPrecioNeto": self.format2digits(self.amount_untaxed),
            "totalITBMS": self.format2digits(self.amount_tax),
            "totalFactura": self.format2digits(self.amount_total),
            "fechaVenceCuota": fechaVenceCuota,
            "fel_relacionadas": fel_relacionadas,
            "codigo_doc": self.tipo_documento_fel.codigo
        }

    def check_not_filled_fields(self):
        company = self.env.company
        partner_id = self.partner_id
        boolean_dict = {
            "(Empresa) Token empresa": company.token_empresa,
            "(Empresa) Token password": company.token_password,
            "(Empresa) Código de sucursal emisor": company.codigo_sucursal_emisor,
            "(Empresa) Tipo de sucursal": company.tipo_sucursal_fel.codigo,
            "(Cliente) Tipo de receptor FE": partner_id.tipo_receptor.codigo,
            "(Cliente) Código de país": partner_id.country_id.code,
            "(Factura) Tipo de documento": self.tipo_documento_fel
        }
        false_values = ""
        for key, value in boolean_dict.items():
            if not value:
                false_values += f"\n*{key}"
        if false_values != "":
            raise UserError(
                f"No es posible continuar, no se han especificado los siguientes campos: \n{false_values}")

    def crear_folio_fel(self):
        if self.respuesta_xml:
            raise UserError(
                f"Este documento ya se ha enviado a facturación electrónica previamente.")

        company = self.env.company
        url = company.url_hka
        if not url:
            raise UserError(f"No se han establecido los datos de facturación en la configuración de la compañía.")

        pre_xml = self.env['ir.qweb']._render(
            'mkl_felpanama.enviar_fel_panama', self.fel_values())
        
        self.write({
            "envio_xml": base64.b64encode(bytes(str(pre_xml), "utf-8"))
        })
        
        _logger.info(f"*** XML Previo: {pre_xml}")

        headers = {
            'Content-Type': 'text/xml',
            'SOAPAction': '"http://tempuri.org/IService/Enviar"'
        }
        xml_file = bytes(str(pre_xml), "utf-8")
        response = requests.request(
            "POST", url, headers=headers, data=xml_file)

        if response.status_code == 200:
            xml_response = response.content
            _logger.info(f"*** xml_response: \n\n{xml_response}")
            self.factura_decodifica_datos(xml_response)
        else:
            raise UserError(
                f"Hubo un error al intentar enviar el documento a facturación electrónica. Código: \n{response.status_code}")

    def html_alert_message_post(self, type, codigo, resultado, mensaje):
        mensaje = mensaje.replace('|', '|<br/>')
        body = f"""<div class="alert alert-{type}" role="alert">
                <span>Repuesta facturación electrónica:</span>
                <ul style="list-style-type:disc;">
                    <li>
                        <b>Código:</b> {codigo}</li>
                    <li>
                        <b>Resultado:</b> {resultado}</li>
                    <li>
                        <b>Mensaje:</b> {mensaje}</li>
                </ul>
                </div>""" 
        self.message_post(body=body, body_is_html=True)
        
        
    def factura_decodifica(self, xml_response):
        root = ET.fromstring(xml_response)

        namespace = {
            'a': 'http://schemas.datacontract.org/2004/07/Services.Response'}

        codigo = root.find('.//a:codigo', namespaces=namespace).text
        resultado = root.find('.//a:resultado', namespaces=namespace).text
        mensaje = root.find('.//a:mensaje', namespaces=namespace).text
        cufe = root.find('.//a:cufe', namespaces=namespace).text
        qr = root.find('.//a:qr', namespaces=namespace).text
        fecha_recepcion_dgi = root.find(
            './/a:fechaRecepcionDGI', namespaces=namespace).text
        nro_protocolo_autorizacion = root.find(
            './/a:nroProtocoloAutorizacion', namespaces=namespace).text
        
        result = {
            'codigo': codigo,
            'resultado': resultado,
            'mensaje': mensaje,
            'cufe': cufe,
            'qr': qr,
            'fecha_recepcion_dgi': fecha_recepcion_dgi,
            'nro_protocolo_autorizacion': nro_protocolo_autorizacion
        }
        
        return result

    def factura_decodifica_datos(self, xml_response):
        datos_factura = self.factura_decodifica(xml_response)

        codigo = datos_factura['codigo']
        resultado = datos_factura['resultado']
        mensaje = datos_factura['mensaje']
        cufe = datos_factura['cufe']
        qr = datos_factura['qr']
        fecha_recepcion_dgi = datos_factura['fecha_recepcion_dgi']
        nro_protocolo_autorizacion = datos_factura['nro_protocolo_autorizacion']

        if codigo == "200":
            self.write({
                "respuesta_xml": base64.b64encode(bytes(str(xml_response), "utf-8")),
                "codigo_fel": codigo,
                "resultado_fel": resultado,
                "mensaje_fel": mensaje,
                "cufe_fel": cufe,
                "qr_fel": qr,
                "fecha_recepcion_dgi_fel": fecha_recepcion_dgi,
                "nro_protocolo_autorizacion_fel": nro_protocolo_autorizacion
            })
            self.html_alert_message_post("success", codigo, resultado, mensaje)
            self.download_docs_hka()
        elif codigo == "102":
            self.write({
                "respuesta_xml": base64.b64encode(bytes(str(xml_response), "utf-8")),
                "codigo_fel": codigo,
                "resultado_fel": resultado,
                "mensaje_fel": mensaje,
                "cufe_fel": cufe,
                "qr_fel": qr,
                "fecha_recepcion_dgi_fel": fecha_recepcion_dgi,
                "nro_protocolo_autorizacion_fel": nro_protocolo_autorizacion
            })
            self.html_alert_message_post("info", codigo, resultado, mensaje)
            self.download_docs_hka()
        else:
            self.html_alert_message_post("warning", codigo, resultado, mensaje)
            

    envio_xml = fields.Binary(string="XML envío FEL", copy=False)
    respuesta_xml = fields.Binary(string="XML respuesta FEL", copy=False)
    pdf_hka = fields.Binary(string="PDF HKA", copy=False)
    xml_hka = fields.Binary(string="XML HKA", copy=False)

    def _get_xml_fel_name(self):
        for rec in self:
            respuesta_xml_name = ""
            envio_xml_name = ""
            if rec.name:
                factura_name = rec.name.replace("/", "_")
                respuesta_xml_name = f"{factura_name}.xml"
                envio_xml_name = f"PRE_{factura_name}.xml"
                
            rec.respuesta_xml_name = respuesta_xml_name
            rec.envio_xml_name = envio_xml_name

    respuesta_xml_name = fields.Char( string="Nombre XML", compute="_get_xml_fel_name", tracking=False)
    
    envio_xml_name = fields.Char( string="Nombre XML envio", compute="_get_xml_fel_name", tracking=False)
    
    pdf_hka_name = fields.Char(string="Nombre PDF HKA", tracking=False)
    xml_hka_name = fields.Char(string="Nombre XML HKA", tracking=False)

    codigo_fel = fields.Char(string="Código", copy=False, tracking=False)
    resultado_fel = fields.Char(string="Resultado FEL", copy=False, tracking=False)
    mensaje_fel = fields.Char(string="Mensaje", copy=False, tracking=False)
    cufe_fel = fields.Char(string="CUFE", copy=False, tracking=False)
    qr_fel = fields.Char(string="QR URL", copy=False, tracking=False)
    fecha_recepcion_dgi_fel = fields.Char( string="Fecha recepción DGI", copy=False, tracking=False)
    fecha_emision_dgi_fel = fields.Char( string="Fecha emisión DGI", copy=False, tracking=False)
    nro_protocolo_autorizacion_fel = fields.Char( string="Nro. Protocolo autorización", copy=False, tracking=False)

    def get_qr_html(self):
        for rec in self:
            if rec.qr_fel:
                qr_url_value = f"/report/barcode/?barcode_type=QR&value='{rec.qr_fel}'"
                # _logger.info(qr_url_value)
                qr_url_value_encode = quote(rec.qr_fel)
                # _logger.info(qr_url_value_encode)
                rec.qr_html = f'<img src="{qr_url_value}" style="width:180px;height:180px; />'
            else:
                rec.qr_html = ""

    qr_html = fields.Html(string="Código QR", compute=get_qr_html)

    def get_extra_addons_path(self):
        extra_addons_path = False
        addons_path = config['addons_path']
        paths = addons_path.split(',')
        paths = [path.strip() for path in paths if path.strip()]
        # _logger.info(f"*paths: {paths}")
        if len(paths) > 1:
            extra_addons_path = paths[1]
        return extra_addons_path
    
    def leer_datos_catalogos_xsd(self, catalogos_path):
        xsd_namespace = {'xs': 'http://www.w3.org/2001/XMLSchema'}
        
        # Crear modelos de impuestos
        '''tax_7_sale_exist = self.env['account.tax'].sudo().search([ ('type_tax_use','=','sale'), ('amount','=',7)
            ])
        
        tax_7_purchase_exist = self.env['account.tax'].sudo().search([ ('type_tax_use','=','purchase'), ('amount','=',7)
            ])
        
        if not tax_7_sale_exist:
            country_id_panama = self.env['res.country'].sudo().search([('name','=','Panama')],limit=1)
            tax_group_panama = self.env['account.tax.group'].sudo().create({
                'name': "Impuesto del 7%",
                'country_id': country_id_panama.id
            })
            tax_7_sale_exist = self.env['account.tax'].sudo().create({
                'name': "7% Ventas",
                'tax_group_id': tax_group_panama.id,
                'country_id': country_id_panama.id,
                'invoice_label': "7% Ventas",
                'type_tax_use': "sale",
                'amount': 7
            })
        
        if not tax_7_purchase_exist:
            country_id_panama = self.env['res.country'].sudo().search([('name','=','Panama')],limit=1)
            tax_group_panama = self.env['account.tax.group'].sudo().create({
                'name': "Impuesto del 7%",
                'country_id': country_id_panama.id
            })
            tax_7_purchase_exist = self.env['account.tax'].sudo().create({
                'name': "7% Compras",
                'tax_group_id': tax_group_panama.id,
                'country_id': country_id_panama.id,
                'invoice_label': "7% Compras",
                'type_tax_use': "purchase",
                'amount': 7
            })
            
        # Default taxes for Panama
        company = self.env.company
        company.write({
            'account_sale_tax_id': tax_7_sale_exist.id,
            'account_purchase_tax_id': tax_7_purchase_exist.id
        })'''
        
        # Importar unidades de medida
        product_uom_categ_unit = self.env.ref('uom.product_uom_categ_unit').id
        units_uom = self.env.ref('uom.product_uom_unit').id
        
        uom_category_id = self.env['uom.category'].sudo().search([('id','=',product_uom_categ_unit)], limit=1)
        unidades_uom_id = self.env['uom.uom'].sudo().search([('id','=',units_uom)], limit=1)
        unidades_uom_id.write({
            'name': 'Base (referencia)'
        })
        xsd_uom = f'{catalogos_path}/FE_UnidadesMedida_v1.00.xsd'
        tree = ET.parse(xsd_uom)
        root = tree.getroot()
        
        simple_type_element = root.find('.//xs:simpleType[@name="unidadesMedida"]', namespaces=xsd_namespace)

        if simple_type_element is not None:
            for enumeration_element in simple_type_element.findall('.//xs:enumeration', namespaces=xsd_namespace):
                value = enumeration_element.get('value')
                documentation_element = enumeration_element.find('.//xs:documentation', namespaces=xsd_namespace)
                documentation = documentation_element.text if documentation_element is not None else None
                
                if value != "":
                    uom_exists = self.env['uom.uom'].sudo().search([('name','=', value)])
                    if len(uom_exists) > 0:
                        uom_exists.write({
                            'documentacion_fel': documentation
                        })
                    else:
                        uom_values = {
                            'name': value,
                            'active': True,
                            'rounding': 0.01000,
                            'documentacion_fel': documentation,
                            'uom_type': 'smaller',
                            'category_id': uom_category_id.id
                        }
                        uom_exists.create(uom_values)
        
        
        # Importacion FE_v1.00.xsd
        xsd_uom = f'{catalogos_path}/FE_v1.00.xsd'
        tree = ET.parse(xsd_uom)
        root = tree.getroot()
        
        def getValuesComplexType(element_name):
            values = []
            # _logger.info(f"*element_name: {element_name}")
            simpleType = root.find(f'.//xs:complexType[@name="gDGenType"]//xs:element[@name="{element_name}"]//xs:simpleType', namespaces=xsd_namespace)

            if simpleType is not None:
                for enumeration in simpleType.findall('.//xs:enumeration', namespaces=xsd_namespace):
                    value = enumeration.get('value')
                    documentation = enumeration.find('.//xs:documentation', namespaces=xsd_namespace)
                    documentation = documentation.text if documentation is not None else None
                    # _logger.info(f"*value: {value}: {documentation}")
                    values.append({
                        'value': value,
                        'documentation': documentation
                    })
            return values
                
        # dgi.tipo.documento
        for valor in getValuesComplexType('iDoc'):
            self.env['dgi.tipo.documento'].sudo().create({
                'name': valor['documentation'],
                'codigo': valor['value']
            })
            
        # # dgi.tipo.sucursal
        for valor in getValuesComplexType('iTipoSuc'):
            self.env['dgi.tipo.sucursal'].sudo().create({
                'name': valor['documentation'],
                'codigo': valor['value']
            })
        
        # dgi.tasa.itbms
        complexType = root.find(f'.//xs:complexType[@name="gItemType"]//xs:element[@name="gITBMSItem"]//xs:complexType', namespaces=xsd_namespace)
        if complexType is not None:
                for enumeration in complexType.findall('.//xs:enumeration', namespaces=xsd_namespace):
                    value = enumeration.get('value')
                    documentation = enumeration.find('.//xs:documentation', namespaces=xsd_namespace)
                    documentation = documentation.text.strip().replace("\n", "") if documentation is not None else None
                    #_logger.info(f"*value: {value}, documentation: {documentation}")
                    self.env['dgi.tasa.itbms'].sudo().create({
                        'name': documentation,
                        'codigo': value
                    })
         
            
        # Importacion FE_BienesServicios_v1.00.xsd
        xsd_uom = f'{catalogos_path}/FE_BienesServicios_v1.00.xsd'
        tree = ET.parse(xsd_uom)
        root = tree.getroot()
        
        restriction_element = root.find('.//xs:simpleType[@name="descBienes"]//xs:restriction', namespaces=xsd_namespace)

        for enumeration_element in restriction_element.findall('.//xs:enumeration', namespaces=xsd_namespace):
            value = enumeration_element.get('value')
            annotation_element = enumeration_element.find('./xs:annotation', namespaces=xsd_namespace)
            documentation_element = annotation_element.find('./xs:documentation', namespaces=xsd_namespace)
            # _logger.info(f"*** [{value}]: {documentation_element.text}\n")
            self.env['dgi.bienes.servicios'].sudo().create({
                'name': documentation_element.text,
                'codigo': value
            })
    
    def importar_catalogos(self):
        # second_addons_path = self.get_extra_addons_path()
        second_addons_path = self.get_extra_addons_path()
        if second_addons_path:
            catalogos_path = f'{second_addons_path}/mkl_felpanama/data/catalogos'
            self.leer_datos_catalogos_xsd(catalogos_path)
            
    def download_docs_hka(self):
        self.descargarDocHKA('pdf')
        self.descargarDocHKA('xml')
    
    def descargarDocHKA(self, tipo):
        company = self.env.company
        tokenEmpresa = company.token_empresa
        tokenPassword = company.token_password
        url = company.url_hka
        
        codigoSucursalEmisor = company.codigo_sucursal_emisor
        numeroDocumentoFiscal = self.getDocumentNumber()
        puntoFacturacionFiscal = company.punto_facturacion_fiscal
        tipoDocumento = self.tipo_documento_fel.codigo
        tipoEmision = "01"
        
        invoice_values = {
            'tokenEmpresa': tokenEmpresa,
            'tokenPassword': tokenPassword,
            'codigoSucursalEmisor': codigoSucursalEmisor,
            'numeroDocumentoFiscal': numeroDocumentoFiscal,
            'puntoFacturacionFiscal': puntoFacturacionFiscal,
            'tipoDocumento': tipoDocumento,
            'tipoEmision': tipoEmision
        }
        
        if not url:
            raise UserError(f"No se han establecido los datos de facturación en la configuración de la compañía.")
        
        if tipo == 'pdf':
            pre_xml = self.env['ir.qweb']._render(
                'mkl_felpanama.descarga_pdf_hka', invoice_values)
            # _logger.info(pre_xml)
            headers = {
                'Content-Type': 'text/xml',
                'SOAPAction': '"http://tempuri.org/IService/DescargaPDF"'
            }
        
        if tipo == 'xml':
            pre_xml = self.env['ir.qweb']._render(
                'mkl_felpanama.descarga_xml_hka', invoice_values)
            # _logger.info(pre_xml)
            headers = {
                'Content-Type': 'text/xml',
                'SOAPAction': '"http://tempuri.org/IService/DescargaXML"'
            }
        
        xml_file = bytes(str(pre_xml), "utf-8")
        response = requests.request( "POST", url, headers=headers, data=xml_file)
        if response.status_code == 200:
            xml_response = response.content
            root = ET.fromstring(xml_response)
            namespace = {'a': 'http://schemas.datacontract.org/2004/07/Services.Response'}

            # codigo = root.find('.//a:codigo', namespaces=namespace).text
            # resultado = root.find('.//a:resultado', namespaces=namespace).text
            documento = root.find('.//a:documento', namespaces=namespace).text
            # name_factura = self.name.replace("/", "_")
            name_factura = numeroDocumentoFiscal
            
            if documento:
                if tipo == 'pdf':
                    self.write({
                        'pdf_hka': documento,
                        'pdf_hka_name': f"HKA_{name_factura}.pdf"
                    })
                    
                if tipo == 'xml':
                    document_xml_data = base64.b64decode(documento)
                    root_document = ET.fromstring(document_xml_data)
                    namespace_doc = {'ns': 'http://dgi-fep.mef.gob.pa'}

                    fecha_emision_el = root_document.find('.//ns:dFechaEm', namespace_doc)
                    fecha_emision = ""
                    if fecha_emision_el is not None:
                        fecha_emision = fecha_emision_el.text

                    self.write({
                        'xml_hka': documento,
                        'xml_hka_name': f"HKA_{name_factura}.xml",
                        'fecha_emision_dgi_fel': fecha_emision
                    })

                    
    #Override from original function
    def action_send_and_print(self):
        template = self.env.ref(self._get_mail_template(), raise_if_not_found=False)
        # Attach XML to email template
        if self.xml_hka:
                xml_attachment = self.env['ir.attachment'].sudo().search([('name','=', self.xml_hka_name)], limit=1)
                if xml_attachment:
                    attachment = xml_attachment
                else:
                    attachment = {
                        'name': self.xml_hka_name,
                        'display_name': self.xml_hka_name,
                        'res_name': self.xml_hka_name,
                        'store_fname': self.xml_hka_name,
                        'type': 'binary',
                        'datas': self.xml_hka,
                        'res_model': "mkl_felpanama",
                        'mimetype': 'application/xml'
                    }
                    attachment = self.env['ir.attachment'].create(attachment)
                template.attachment_ids = [(6, 0, [attachment.id])]

        if any(not x.is_sale_document(include_receipts=True) for x in self):
            raise UserError(_("You can only send sales documents"))

        return {
            'name': _("Enviar e imprimir"),
            'type': 'ir.actions.act_window',
            'view_type': 'form',
            'view_mode': 'form',
            'res_model': 'account.move.send',
            'target': 'new',
            'context': {
                'active_ids': self.ids,
                'default_mail_template_id': template and template.id or False,
            },
        }
        
    @api.onchange('tipo_documento_fel')
    def _check_is_exportation(self):
        for rec in self:
            rec.es_exportacion_fel = False
            if rec.tipo_documento_fel.codigo == "03":
                rec.es_exportacion_fel = True
                
    #Para exportación
    es_exportacion_fel = fields.Boolean(string="¿Es documento de exportación?", compute=_check_is_exportation)
    condiciones_entrega_fel = fields.Char(string="Condiciones de entrega FEL", copy=False)
    moneda_exportacion = fields.Many2one('res.currency', string="Moneda operación exportación", copy=False)
    puerto_embarque = fields.Char(string="Puerto embarque", copy=False)
    
    #Para Notas de crédito con FEL relacionadas
    @api.onchange('tipo_documento_fel')
    def _check_nota_credito_rel(self):
        for rec in self:
            rec.es_nota_credito_relacionada = False
            if rec.tipo_documento_fel.codigo == "04":
                rec.es_nota_credito_relacionada = True
        
    es_nota_credito_relacionada = fields.Boolean()
    reversed_entry_ids = fields.One2many('account.reversal.fel', 'move_id', string="FEL's relacionadas")
    
