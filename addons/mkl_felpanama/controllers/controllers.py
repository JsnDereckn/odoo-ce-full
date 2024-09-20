# -*- coding: utf-8 -*-
from odoo import http, _
from odoo.http import request
from odoo import api, fields, models, tools, SUPERUSER_ID, _, Command
from datetime import datetime, date
import requests
import json
import base64
import logging
_logger = logging.getLogger(__name__)
import xml.etree.ElementTree as ET

URL_HKA = "https://emision.thefactoryhka.com.pa/ws/obj/v1.0/Service.svc"
URL_HKA_TEST = "https://demoemision.thefactoryhka.com.pa/ws/obj/v1.0/Service.svc"

class MKLSageAPI(http.Controller):
        
    @http.route('/sage/sign_document', type='http', auth='public', methods=['POST'], csrf=False)
    def sign_document(self, **kw):
        
        response = {
            'status': "ERROR",
            'status_fel': "No se proceso documento"
        }
        account_move = http.request.env['account.move'].sudo()
        
        if not 'test_mode' in kw:
            response['validation_error'] = "test_mode has not been recieved."
        
        if 'json_invoice' and 'test_mode' in kw:
        
            if kw['test_mode'] == '1':
                URL_HKA = URL_HKA_TEST
                
            str_json_invoice = str(kw['json_invoice']).strip()
            json_invoice = json.loads(str_json_invoice)
            
            
            json_invoice_beauty = json.dumps(json_invoice, indent=4)
            _logger.info(f"*json_invoice RECIBIDO: {json_invoice_beauty}")
            
            foliosObtenidos = []
            
            # for json_invoice in json_invoices:
            token_empresa = json_invoice["tokenEmpresa"]
            token_password = json_invoice["tokenPassword"]
            codigo_sucursal_emisor = json_invoice["codigoSucursalEmisor"]
            tipo_documento = json_invoice["tipoDocumento"]
            numeroDocumentoFiscal = json_invoice["numeroDocumentoFiscal"]
            puntoFacturacionFiscal = json_invoice["puntoFacturacionFiscal"]
            fecha_emision = json_invoice["fechaEmision"]
            destinoOperacion = json_invoice["destinoOperacion"]
            nro_identificacion_ext = json_invoice["nroIdentificacionExtranjero"]
            tipo_receptor_codigo = json_invoice["tipoClienteFE"]
            tipo_ruc = json_invoice["tipoContribuyente"]
            numero_ruc = json_invoice["numeroRUC"]
            dv = json_invoice["digitoVerificadorRUC"]
            razon_social = json_invoice["razonSocial"]
            direccion = json_invoice["direccion"]
            telefono = json_invoice["telefono1"]
            email = json_invoice["correoElectronico1"]
            pais = json_invoice["pais"]
            condiciones_entrega = json_invoice["condicionesEntrega"]
            moneda_exportacion = json_invoice["monedaOperExportacion"]
            puerto_embarque = json_invoice["puertoEmbarque"]
                    
            lista_items = []
            
            for item in json_invoice["listaItems"]:
                # _logger.info(f"*item: {item}")
                descripcion = item["descripcion"]
                codigo = item["codigo"]
                codigoCPBS = item["codigoCPBS"]
                uom = item["uom"]
                cantidad = item["cantidad"]
                precio_unitario = item["precio_unitario"]
                precio_unitario_descuento = item["precio_unitario_descuento"]
                precio_item = item["precio_item"]
                valor_total = item["valor_total"]
                tasaITBMS = item["tasaITBMS"]
                valorITBMS = item["valorITBMS"]
                
                lista_items.append({
                        "descripcion": descripcion, # product_id.name,
                        "codigo": codigo,
                        "codigoCPBS": codigoCPBS,
                        "unidadMedida": uom,
                        "cantidad": cantidad, #self.format2digits(item.quantity),
                        "precioUnitario": precio_unitario, #self.format2digits(item.price_unit),
                        "precioUnitarioDescuento": precio_unitario_descuento, #self.format2digits(item.discount*0.01),
                        "precioItem": precio_item, #self.format2digits(item.price_subtotal),
                        "valorTotal": valor_total, #self.format2digits(item.price_total),
                        "tasaITBMS": tasaITBMS,
                        "valorITBMS": valorITBMS #self.format2digits(valorITBMS),
                    })
            
            total_precio_neto = json_invoice["totalPrecioNeto"]
            total_ITBMS = json_invoice["totalITBMS"]
            total_factura = json_invoice["totalFactura"]
            fechaVenceCuota = json_invoice["fechaVenceCuota"]
            fel_relacionadas = json_invoice["fel_relacionadas"]
            codigo_doc = json_invoice["codigo_doc"]

            data_for_sign = {
                "tokenEmpresa": token_empresa,
                "tokenPassword": token_password,
                "codigoSucursalEmisor": codigo_sucursal_emisor,
                "tipoDocumento": tipo_documento, # self.tipo_documento_fel.codigo,
                "numeroDocumentoFiscal": numeroDocumentoFiscal,
                "fechaEmision": fecha_emision,
                "destinoOperacion": destinoOperacion,
                "nroIdentificacionExtranjero": nro_identificacion_ext, #partner_id.vat if partner_id.vat else "",
                "tipoClienteFE": tipo_receptor_codigo, #partner_id.tipo_receptor.codigo,
                "tipoContribuyente": tipo_ruc, #partner_id.tipo_ruc.codigo,
                "numeroRUC": numero_ruc, #partner_id.vat,
                "digitoVerificadorRUC": dv, #partner_id.dv,
                "razonSocial": razon_social, #partner_id.name,
                "direccion": direccion,
                "telefono1": telefono, #partner_id.phone if partner_id.phone else "",
                "correoElectronico1": email, #self.isFalseThenEmpty(partner_id.email),
                "pais": pais, #partner_id.country_id.code,
                "condicionesEntrega": condiciones_entrega, # self.condiciones_entrega_fel,
                "monedaOperExportacion": moneda_exportacion, #self.moneda_exportacion.name,
                "puertoEmbarque": puerto_embarque, #self.puerto_embarque,
                "listaItems": lista_items,
                "nroItems": len(lista_items),
                "totalPrecioNeto": total_precio_neto, #self.format2digits(self.amount_untaxed),
                "totalITBMS": total_ITBMS, #self.format2digits(self.amount_tax),
                "totalFactura": total_factura, #self.format2digits(self.amount_total),
                "fechaVenceCuota": fechaVenceCuota,
                "fel_relacionadas": fel_relacionadas,
                "codigo_doc": codigo_doc #, self.tipo_documento_fel.codigo
            }
            
            # _logger.info(f"*data_for_sign: {data_for_sign}")
            
            pre_xml = http.request.env['ir.qweb']._render('mkl_felpanama.enviar_fel_panama', data_for_sign)
            
            headers = {
                'Content-Type': 'text/xml',
                'SOAPAction': '"http://tempuri.org/IService/Enviar"'
            }
            xml_file = bytes(str(pre_xml), "utf-8")
            response_hka = requests.request("POST", URL_HKA, headers=headers, data=xml_file)

            if response_hka.status_code == 200:
                xml_response_kka = response_hka.content
                _logger.info(f"*xml_response_kka: \n{xml_response_kka}\n")
                singed_invoice_data = account_move.factura_decodifica(xml_response_kka)
                _logger.info(f"\n*singed_invoice_data: {singed_invoice_data}\n")
                response['status_fel'] = f"{singed_invoice_data['resultado']} - {singed_invoice_data['mensaje']}"
                response['cufe'] = singed_invoice_data['cufe'] if singed_invoice_data['cufe'] else ""
                
                datosDescargaArchivosHKA = {
                    'tokenEmpresa': token_empresa,
                    'tokenPassword': token_password,
                    'codigoSucursalEmisor': codigo_sucursal_emisor,
                    'numeroDocumentoFiscal': numeroDocumentoFiscal,
                    'puntoFacturacionFiscal': puntoFacturacionFiscal,
                    'tipoDocumento': tipo_documento,
                    'tipoEmision': "01"
                }
                
                response['xml_signed'] = self.descargarDocHKA(URL_HKA, "xml", datosDescargaArchivosHKA)
                response['pdf_signed'] = self.descargarDocHKA(URL_HKA, "pdf", datosDescargaArchivosHKA)
                
            else:
                response['status'] = f"Hubo un error al intentar enviar el documento a facturación electrónica. Código: \n{response_hka.status_code}"
                response['status_fel'] = f"Error al intentar foliar {response_hka.status_code}"
                
            # response["foliosObtenidos"] = foliosObtenidos
            
        # _logger.info(f"*response CONTROLLER: {response}")
        return json.dumps(response)
    
    
    def descargarDocHKA(self, url_api_hka, tipo, datosDescargaArchivosHKA):
        
        if tipo == 'pdf':
            pre_xml = http.request.env['ir.qweb']._render(
                'mkl_felpanama.descarga_pdf_hka', datosDescargaArchivosHKA)
            headers = {
                'Content-Type': 'text/xml',
                'SOAPAction': '"http://tempuri.org/IService/DescargaPDF"'
            }
        
        if tipo == 'xml':
            pre_xml = http.request.env['ir.qweb']._render(
                'mkl_felpanama.descarga_xml_hka', datosDescargaArchivosHKA)
            headers = {
                'Content-Type': 'text/xml',
                'SOAPAction': '"http://tempuri.org/IService/DescargaXML"'
            }
        xml_file = bytes(str(pre_xml), "utf-8")
        # _logger.info(f"\n\n---datosDescargaArchivosHKA xml_file\n\n: {xml_file}\n\n")
        response = requests.request( "POST", url_api_hka, headers=headers, data=xml_file)
        if response.status_code == 200:
            
            xml_response = response.content
            # _logger.info(f"*RESPONSE HKA DOCUMENT: {xml_response}")
            root = ET.fromstring(xml_response)
            namespace = {'a': 'http://schemas.datacontract.org/2004/07/Services.Response'}

            # codigo = root.find('.//a:codigo', namespaces=namespace).text
            # resultado = root.find('.//a:resultado', namespaces=namespace).text
            documento = root.find('.//a:documento', namespaces=namespace).text
            # name_factura = self.name.replace("/", "_")
            if documento:
                # if tipo == 'pdf':
                #     _logger.info(f"*Tengo PDF: {documento}")
                #     # self.write({
                #     #     'pdf_hka': documento,
                #     #     'pdf_hka_name': f"HKA_{datosDescargaArchivosHKA['numeroDocumentoFiscal']}.pdf"
                #     # })
                    
                if tipo == 'xml':
                    document_xml_data = base64.b64decode(documento)
                    root_document = ET.fromstring(document_xml_data)
                    namespace_doc = {'ns': 'http://dgi-fep.mef.gob.pa'}

                    fecha_emision_el = root_document.find('.//ns:dFechaEm', namespace_doc)
                    fecha_emision = ""
                    if fecha_emision_el is not None:
                        fecha_emision = fecha_emision_el.text
                        
                    _logger.info(f"*Tengo XML fecha emision: {fecha_emision}")

                    # self.write({
                    #     'xml_hka': documento,
                    #     'xml_hka_name': f"HKA_{name_factura}.xml",
                    #     'fecha_emision_dgi_fel': fecha_emision
                    # })
            
            return documento