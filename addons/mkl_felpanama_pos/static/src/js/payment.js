/** @odoo-module **/

import { _t } from "@web/core/l10n/translation";
import { patch } from "@web/core/utils/patch";
import { PaymentScreen } from "@point_of_sale/app/screens/payment_screen/payment_screen";
import { ErrorPopup } from "@point_of_sale/app/errors/popups/error_popup";

patch(PaymentScreen.prototype, {
    async _finalizeValidation() {
        try {
            await super._finalizeValidation(...arguments);
        } catch (error) {
            this.env.services.ui.unblock()
            this.popup.add(ErrorPopup, {
                title: _t("Error facturación electrónica"),
                body: _t(
                    error.data.message
                ),
            });
        }
    }
});


