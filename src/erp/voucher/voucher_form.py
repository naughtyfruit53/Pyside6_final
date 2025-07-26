# src/erp/voucher/voucher_form.py
# No DB access; imports converted files.

# voucher_form.py

from PySide6.QtWidgets import QWidget, QMessageBox
from PySide6.QtCore import Qt
import logging
from .base_voucher_form import BaseVoucherForm
from .forms.sales_voucher_form import SalesVoucherForm
from .forms.purchase_voucher_form import PurchaseVoucherForm
from .forms.sales_order_form import SalesOrderForm
from .forms.purchase_order_form import PurchaseOrderForm
from .forms.quotation_form import QuotationForm
from .forms.proforma_invoice_form import ProformaInvoiceForm
from .forms.delivery_challan_form import DeliveryChallanForm
from .forms.credit_note_form import CreditNoteForm
from .forms.debit_note_form import DebitNoteForm
from .forms.grn_form import GRNForm
from .forms.rejection_in_out_form import RejectionInOutForm
from .forms.internal_return_form import InternalReturnForm

logging.basicConfig(filename='app.log', level=logging.DEBUG, format='%(asctime)s - %(name)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

VOUCHER_FORMS = {
    "Sales Voucher": SalesVoucherForm,
    "Purchase Voucher": PurchaseVoucherForm,
    "Sales Order": SalesOrderForm,
    "Purchase Order": PurchaseOrderForm,
    "Quotation": QuotationForm,
    "Proforma Invoice": ProformaInvoiceForm,
    "Delivery Challan": DeliveryChallanForm,
    "Credit Note": CreditNoteForm,
    "Debit Note": DebitNoteForm,
    "GRN (Goods Received Note)": GRNForm,
    "Rejection In/Out": RejectionInOutForm,
    "Internal Return": InternalReturnForm
}

def open_voucher_form(parent, app, module_name, voucher_type_id, voucher_type_name, voucher_data=None):
    """
    Open a voucher form widget for creating or editing a voucher.
    Uses the specific form class for the voucher type.
    """
    try:
        VoucherClass = VOUCHER_FORMS.get(voucher_type_name, BaseVoucherForm)
        logger.info(f"Opening voucher form using class {VoucherClass.__name__} for {voucher_type_name}")
        # Check if already open
        if hasattr(app, 'open_voucher_forms') and voucher_type_id in app.open_voucher_forms:
            logger.debug(f"Voucher form for {voucher_type_name} (ID: {voucher_type_id}) already open, raising existing dialog")
            app.open_voucher_forms[voucher_type_id].raise_()
            app.open_voucher_forms[voucher_type_id].activateWindow()
            return app.open_voucher_forms[voucher_type_id]
        
        voucher_form = VoucherClass(parent=parent, app=app, module_name=module_name, 
                                    voucher_type_id=voucher_type_id, voucher_type_name=voucher_type_name, 
                                    voucher_data=voucher_data)
        voucher_form.setWindowTitle(f"{voucher_type_name or 'Voucher'} Form")
        voucher_form.setFixedSize(800, 600)
        voucher_form.setModal(True)
        if not hasattr(app, 'open_voucher_forms'):
            app.open_voucher_forms = {}
        app.open_voucher_forms[voucher_type_id] = voucher_form
        voucher_form.finished.connect(lambda: app.open_voucher_forms.pop(voucher_type_id, None))
        voucher_form.exec()
        return voucher_form
    except Exception as e:
        logger.error(f"Failed to open voucher form for {voucher_type_name}: {e}")
        QMessageBox.critical(parent, "Error", f"Failed to open voucher form: {e}")
        return None