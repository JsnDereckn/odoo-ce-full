/** @odoo-module **/

import { _t } from "@web/core/l10n/translation";
import { Order } from "@point_of_sale/app/store/models";
import { patch } from "@web/core/utils/patch";
import { useErrorHandlers } from "@point_of_sale/app/utils/hooks"; 
import { useService } from "@web/core/utils/hooks";
import { ReceiptScreen } from "@point_of_sale/app/screens/receipt_screen/receipt_screen"; // importamos la pantalla de las recibos 
import { ReprintReceiptScreen } from "@point_of_sale/app/screens/receipt_screen/reprint_receipt_screen";
import { useRef, useState, onWillStart, Component } from "@odoo/owl";
import { usePos } from "@point_of_sale/app/store/pos_hook";
import { session } from "@web/session";



patch(ReceiptScreen.prototype, {

    setup() {
        super.setup();
        this.pos = usePos();
        this.printer = useService("printer");
        useErrorHandlers();
        this.ui = useState(useService("ui"));
        this.orm = useService("orm");
        this.renderer = useService("renderer");
        this.buttonMailReceipt = useRef("order-mail-receipt-button");
        this.buttonPrintReceipt = useRef("order-print-receipt-button");
        this.currentOrder = this.pos.get_order();
        const partner = this.currentOrder.get_partner();
        this.orderUiState = this.currentOrder.uiState.ReceiptScreen;
        this.orderUiState.inputEmail =
            this.orderUiState.inputEmail || (partner && partner.email) || "";

        const baseUrl = session["web.base.url"];

        onWillStart(async () => {
            // When the order is paid, if there is still a part of the order
            // to send in preparation it is automatically sent
            if (this.pos.orderPreparationCategories.size) {
                try {
                    await this.pos.sendOrderInPreparationUpdateLastChange(this.currentOrder);
                } catch (error) {
                    Promise.reject(error);
                }
            }

            var OrderAccessToken = this.currentOrder.access_token;
            const current_order = await this.orm.call('pos.order', 'search_read', [
                [
                    ['access_token', '=', OrderAccessToken],
                ],
                ['account_move']
            ]);

            if (current_order.length > 0) {
                var account_move_arr = current_order[0].account_move;

                if (account_move_arr.length > 0) {
                    var account_move_id = current_order[0].account_move[0];
                    //************** Factuacion Electrónica **************/
                    const invoice_query = await this.orm.call('account.move', 'search_read', [
                        [
                            ['id', '=', account_move_id],
                        ],
                        [
                            'cufe_fel',
                            'qr_fel',
                            'qr_html',
                            'nro_protocolo_autorizacion_fel',
                            'fecha_recepcion_dgi_fel'
                        ]
                    ]);
                    if (invoice_query.length > 0) {
                        const invoice_data = invoice_query[0];
                        const SelectedOrder = this.pos.get_order();
                        SelectedOrder.cufe_fel = invoice_data.cufe_fel;
                        SelectedOrder.qr_fel = baseUrl + '/report/barcode/?barcode_type=QR&value=' + invoice_data.qr_fel;
                        SelectedOrder.qr_html = invoice_data.qr_html;
                        SelectedOrder.nro_protocolo_autorizacion_fel = invoice_data.nro_protocolo_autorizacion_fel;
                        SelectedOrder.fecha_recepcion_dgi_fel = invoice_data.fecha_recepcion_dgi_fel;
                    }//Fin de if if (invoice_query.length > 0)
                    //************** Factuacion Electrónica **************/
                }

            }//Fin de current_order.length > 0

        });
    }//
});



// Pantalla  
patch(ReprintReceiptScreen.prototype, {
    async setup() {
        super.setup();
        this.orm = useService('orm');

        const baseUrl = session.base_url;

        var account_move_id = this.props.order.account_move;
        //************** Factuacion Electrónica **************/
        const invoice_query = await this.orm.call('account.move', 'search_read', [
            [
                ['id', '=', account_move_id],
            ],
            [
                'cufe_fel',
                'qr_fel',
                'qr_html',
                'nro_protocolo_autorizacion_fel',
                'fecha_recepcion_dgi_fel'
            ]
        ]);

        if (invoice_query.length > 0) {
            const invoice_data = invoice_query[0];
            const SelectedOrder = this.pos.get_order();

            SelectedOrder.cufe_fel = invoice_data.cufe_fel;
            SelectedOrder.qr_fel = baseUrl + '/report/barcode/?barcode_type=QR&value=' + invoice_data.qr_fel;
            SelectedOrder.qr_html = invoice_data.qr_html;
            SelectedOrder.nro_protocolo_autorizacion_fel = invoice_data.nro_protocolo_autorizacion_fel;
            SelectedOrder.fecha_recepcion_dgi_fel = invoice_data.fecha_recepcion_dgi_fel;
        }//Fin de if if (invoice_query.length > 0)
        //************** Factuacion Electrónica **************/
    }
});


patch(Order.prototype, {
    export_for_printing() {
        return {
            ...super.export_for_printing(...arguments),
            invoice_data: this.pos.selectedOrder.invoice_data,
            cufe_fel: this.pos.selectedOrder.cufe_fel,
            qr_fel: this.pos.selectedOrder.qr_fel,
            qr_html: this.pos.selectedOrder.qr_html,
            nro_protocolo_autorizacion_fel: this.pos.selectedOrder.nro_protocolo_autorizacion_fel,
            fecha_recepcion_dgi_fel: this.pos.selectedOrder.fecha_recepcion_dgi_fel,
        };
    },
});


