/** @odoo-module */

import { _t } from "@web/core/l10n/translation";
import { PosStore } from "@point_of_sale/app/store/pos_store";
import { patch } from "@web/core/utils/patch";

patch(PosStore.prototype, {
    async _processData(loadedData) {
        await super._processData(...arguments);
        this.tipos_ruc = loadedData["dgi.tipo.ruc"];
        this.tipos_receptor = loadedData["dgi.tipo.receptor"];
    }
});