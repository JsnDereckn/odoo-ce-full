# -*- coding: utf-8 -*-
{
    'name': "POS: Facturación Electrónica Panamá para Punto de Venta",

    'summary': "Módulo de facturación electrónica para Panamá para POS. (Point Of Sale)",

    'description': """
Módulo de facturación electrónica para Panamá POS. Desarrollado por Mentor Keep Learning en colaboración con Brain Consulting.
    """,

    'author': "Mentor Keep Learning",
    'website': "https://www.mentorconsultoria.com",

    'category': 'accounting',
    'version': '0.1',
    'license': 'LGPL-3',

    'depends': ['base','mkl_felpanama','point_of_sale','web'],

    'data': [
        'views/pos_config.xml',
    ],
    'assets': {
        'point_of_sale._assets_pos': [
            'mkl_felpanama_pos/static/src/xml/OrderReceipt/OrderReceipt.xml',
            'mkl_felpanama_pos/static/src/xml/Partner_screens.xml',
            'mkl_felpanama_pos/static/src/js/receipt.js',
            'mkl_felpanama_pos/static/src/js/models.js',
            'mkl_felpanama_pos/static/src/js/payment.js',
            'mkl_felpanama_pos/static/src/js/partner_editor.js',
            'mkl_felpanama_pos/static/src/js/pos_store.js'
        ]
    }
}