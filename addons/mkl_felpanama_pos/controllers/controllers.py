# -*- coding: utf-8 -*-
# from odoo import http


# class MklFelpanamaPos(http.Controller):
#     @http.route('/mkl_felpanama_pos/mkl_felpanama_pos', auth='public')
#     def index(self, **kw):
#         return "Hello, world"

#     @http.route('/mkl_felpanama_pos/mkl_felpanama_pos/objects', auth='public')
#     def list(self, **kw):
#         return http.request.render('mkl_felpanama_pos.listing', {
#             'root': '/mkl_felpanama_pos/mkl_felpanama_pos',
#             'objects': http.request.env['mkl_felpanama_pos.mkl_felpanama_pos'].search([]),
#         })

#     @http.route('/mkl_felpanama_pos/mkl_felpanama_pos/objects/<model("mkl_felpanama_pos.mkl_felpanama_pos"):obj>', auth='public')
#     def object(self, obj, **kw):
#         return http.request.render('mkl_felpanama_pos.object', {
#             'object': obj
#         })

