# -*- coding: utf-8 -*-
{
    'name': "Facturación Electrónica Panamá",

    'summary': "Módulo de facturación electrónica para Panamá.",

    'description': """
        Módulo de facturación electrónica para Panamá. Desarrollado por Brain Consulting con conexión con HKA Factory.
    """,

    'author': "Brain Consulting",
    'website': "https://www.brainbc.com",

    'category': 'accounting',
    'version': '0.1',
    
    'license': 'LGPL-3',

    'depends': ['base','mail','account','l10n_pa','phone_validation','uom','product'],

    'data': [
        'security/ir.model.access.csv',
        'data/invoice.xml',
        'data/consultar_ruc_dv.xml',
        'data/descargaPDF.xml',
        'data/descargaXML.xml',
        'views/account_move.xml',
        'views/dgi_catalogos.xml',
        'views/res_company.xml',
        'views/res_partner.xml',
        'views/product_template.xml',
        'views/uom_uom.xml',
        'views/account_tax.xml',
        'report/invoice_qweb.xml',
        'data/dgi_catalogos.xml',
        'data/res_partner.xml'
    ],
    
    'post_init_hook': 'post_init_hook',
}

