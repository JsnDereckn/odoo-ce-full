# -*- coding: utf-8 -*-

from . import controllers
from . import models
from . import wizard

def update_records_after_installation(env):
    records_to_update = env['report.paperformat'].search(['|',('name', '=', "US Letter"), ('name','=',"A4")])
    for record in records_to_update:
        record.write({
            'margin_top': 25,
            'margin_bottom': 20,
            'margin_left': 5,
            'margin_right': 5,
            'header_spacing': 20
        })

def post_init_hook(env):
    update_records_after_installation(env)
    env['account.move'].importar_catalogos()