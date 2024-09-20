# -*- coding: utf-8 -*-

import xml.etree.ElementTree as ET
from odoo.exceptions import ValidationError
from odoo import models, fields, api
import requests
import logging
_logger = logging.getLogger(__name__)


class ResPartner(models.Model):
    _inherit = 'res.partner'

    @api.onchange('phone', 'country_id', 'company_id')
    def _onchange_phone_validation(self):
        if self.phone:
            self.phone = self.phone

    @api.onchange('mobile', 'country_id', 'company_id')
    def _onchange_mobile_validation(self):
        if self.mobile:
            self.mobile = self.mobile

    tipo_receptor = fields.Many2one(
        'dgi.tipo.receptor', string="Tipo de receptor (FEL)", tracking=True)
    tipo_ruc = fields.Many2one(
        'dgi.tipo.ruc', string="Tipo de RUC (contribuyente)", tracking=True)
    
    dv = fields.Char(string="Dígito verificador", tracking=True)

    def check_not_filled_fields(self):
        company = self.env.company
        boolean_dict = {
            "(Empresa) Token empresa": company.token_empresa,
            "(Empresa) Token password": company.token_password,
            "(Cliente) Tipo de RUC": self.tipo_ruc.codigo,
            "(Cliente) RUC": self.vat
        }
        false_values = ""
        for key, value in boolean_dict.items():
            if not value:
                false_values += f"\n*{key}"
        if false_values != "":
            raise ValidationError(
                f"No es posible continuar, no se han especificado los siguientes campos: \n{false_values}")

    def ruc_values(self):
        self.check_not_filled_fields()
        company = self.env.company
        token_empresa = company.token_empresa
        token_password = company.token_password
        return {
            "tokenEmpresa": token_empresa,
            "tokenPassword": token_password,
            "tipoRuc": self.tipo_ruc.codigo,
            "ruc": self.vat
        }

    def html_alert_message_post(self, type, codigo, resultado, mensaje):
        body = f"""<div class="alert alert-{type}" role="alert">
                <span>Repuesta consulta RUC DV:</span>
                <ul style="list-style-type:disc;">
                    <li><b>Código:</b> {codigo}</li>
                    <li><b>Resultado:</b> {resultado}</li>
                    <li><b>Mensaje:</b> {mensaje}</li>
                </ul>  
            </div>"""
        self.message_post(body=body, body_is_html=True)

    def validar_ruc_dv(self):
        company = self.env.company
        url = company.url_hka
        if not url:
            raise ValidationError(f"No se han establecido los datos de facturación en la configuración de la compañía.")

        pre_xml = self.env['ir.qweb']._render(
            'mkl_felpanama.consultar_ruc_dv_fel_panama', self.ruc_values())
        _logger.info(pre_xml)

        headers = {
            'Content-Type': 'text/xml',
            'SOAPAction': '"http://tempuri.org/IService/ConsultarRucDV"'
        }
        xml_file = bytes(str(pre_xml), "utf-8")
        response = requests.request(
            "POST", url, headers=headers, data=xml_file)

        if response.status_code == 200:
            xml_response = response.content
            _logger.info("*RESPONSE content: \n\n")
            _logger.info(xml_response)
            root = ET.fromstring(xml_response)
            namespace = {
                'a': 'http://schemas.datacontract.org/2004/07/Services.Response'}

            codigo = root.find('.//a:codigo', namespaces=namespace).text
            mensaje = root.find('.//a:mensaje', namespaces=namespace).text
            resultado = root.find('.//a:resultado', namespaces=namespace).text
            # _logger.info(f"*codigo: {codigo}, mensaje: {mensaje}, resultado: {resultado}")

            if codigo == "200":
                tipo_ruc = root.find('.//a:tipoRuc', namespace).text
                dv = root.find('.//a:dv', namespace).text
                razon_social = root.find('.//a:razonSocial', namespace).text

                mensaje_adicional = f'''
                    <div>
                        <b>Datos del RUC recibidos</b>
                        <ul>
                            <li>Razon social: <b>{razon_social}</b></li>
                            <li>DV: <b>{dv}</b></li>
                            <li>Tipo de RUC: <b>{tipo_ruc}</b></li>
                        </ul>
                    </div>
                '''
                
                self.write({
                    'name': razon_social,
                    'dv': dv,
                    # 'tipo_receptor': 1
                })

                self.html_alert_message_post(
                    "success", codigo, resultado, mensaje+mensaje_adicional)
            else:
                self.html_alert_message_post(
                    "warning", codigo, resultado, mensaje)

        else:
            raise ValidationError(
                f"Hubo un error al intentar consultar el RUC - DV. Código: \n{response.status_code}")
