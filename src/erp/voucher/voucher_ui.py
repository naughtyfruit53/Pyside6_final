# src/erp/voucher/voucher_ui.py
# Converted to use SQLAlchemy indirectly via imports.

from PySide6.QtWidgets import QMainWindow, QSplitter, QWidget, QVBoxLayout, QHBoxLayout, QPushButton, QComboBox, QLabel, QLineEdit, QTableWidget, QTableWidgetItem, QMessageBox, QHeaderView  # Added QHeaderView
from PySide6.QtCore import Qt
import logging
from src.core.config import get_log_path
from src.erp.logic.database.voucher import get_voucher_types
from src.erp.logic.utils.voucher_utils import VOUCHER_TYPES
from src.erp.voucher.voucher_management import VoucherManagement
from src.erp.voucher.custom_voucher import create_custom_voucher_type
from .base_voucher_form import BaseVoucherForm  # Import base for potential extension if needed

# Import all voucher form widgets
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

# Complete VOUCHER_WIDGETS with all forms
VOUCHER_WIDGETS = {
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
    "Rejection In": RejectionInOutForm,
    "Rejection Out": RejectionInOutForm,
    "Internal Return": InternalReturnForm,
    # Add more if new forms are created (e.g., for financial vouchers like "Payment Voucher")
}

logging.basicConfig(filename=get_log_path(), level=logging.DEBUG, format='%(asctime)s - %(name)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

class VoucherUI(QMainWindow):
    def __init__(self, app):
        super().__init__()
        self.app = app
        self.voucher_type_name = None
        self.current_voucher_category = None
        self.voucher_management = VoucherManagement(self, app)
        self.setStyleSheet("QMainWindow { background-color: #f0f0f0; }")
        self.init_ui()

    def init_ui(self):
        self.central_widget = QWidget()
        self.setCentralWidget(self.central_widget)
        self.main_layout = QVBoxLayout(self.central_widget)

        # Create splitter for 40-60 split view
        self.splitter = QSplitter(Qt.Horizontal)
        self.view_widget = QWidget()
        self.create_widget = QWidget()
        self.splitter.addWidget(self.view_widget)
        self.splitter.addWidget(self.create_widget)
        self.splitter.setSizes([400, 600])  # Initial 40-60 split
        self.splitter.setHandleWidth(8)
        self.main_layout.addWidget(self.splitter)

        # Restrict splitter to maintain 40-60 ratio
        self.splitter.splitterMoved.connect(self.restrict_sash_movement)

        # Setup view and create layouts
        self.view_layout = QVBoxLayout(self.view_widget)
        self.create_layout = QVBoxLayout(self.create_widget)

        # Add custom voucher button at top center of create widget
        self.custom_voucher_button = QPushButton("Create Custom Voucher")
        self.custom_voucher_button.clicked.connect(self.create_custom_voucher)
        self.custom_voucher_button.setStyleSheet("QPushButton { font-size: 14px; padding: 8px; }")
        self.create_layout.addWidget(self.custom_voucher_button, alignment=Qt.AlignCenter)

    def create_voucher_frame(self, parent, app, mode, voucher_category):
        logger.debug(f"Creating voucher frame: mode={mode}, category={voucher_category}")
        self.current_voucher_category = voucher_category
        voucher_type = voucher_category.replace('vouchers-', '')
        normalized_voucher_type = voucher_type.replace('_', ' ').title()
        if normalized_voucher_type.lower() == 'grn':
            normalized_voucher_type = 'GRN (Goods Received Note)'
        if normalized_voucher_type.lower() == 'rejection in':
            normalized_voucher_type = 'Rejection In'
        if normalized_voucher_type.lower() == 'rejection out':
            normalized_voucher_type = 'Rejection Out'
        self.voucher_type_name = normalized_voucher_type
        logger.debug(f"Normalized voucher type: {normalized_voucher_type} for category {voucher_category}")

        # Clear existing layouts before calling create_voucher_frame
        for widget in [self.create_widget, self.view_widget]:
            layout = widget.layout()
            if layout:
                while layout.count():
                    item = layout.takeAt(0)
                    if item.widget():
                        item.widget().deleteLater()

        # Initialize VoucherManagement for both views
        self.voucher_management.create_voucher_frame(self.create_widget, "create_voucher", self.voucher_type_name)
        self.voucher_management.create_voucher_frame(self.view_widget, "view_vouchers", self.voucher_type_name)

        return self.central_widget

    def restrict_sash_movement(self, pos, index):
        total_width = self.splitter.width()
        if total_width <= 0:
            return
        target_sash_pos = int(total_width * 0.4)  # Fixed at 40% of total width
        self.splitter.setSizes([target_sash_pos, total_width - target_sash_pos])
        logger.debug(f"Restricted sash movement: sash fixed at x={target_sash_pos}, total_width={total_width}")

    def create_custom_voucher(self):
        try:
            module_name = self.current_voucher_category.replace('vouchers-', '')
            create_custom_voucher_type(self.app, self, None, module_name, None, None,
                                      lambda: self.voucher_management.refresh_voucher_content(self.voucher_type_name))
        except Exception as e:
            logger.error(f"Failed to create custom voucher: {e}")
            QMessageBox.critical(self, "Error", f"Failed to create custom voucher: {e}")

    def display_voucher_form(self, voucher_management, voucher_type_id, voucher_category, voucher_name, voucher_data=None,
                            save_callback=None, add_product_callback=None, entities=None, products=None, payment_terms=None):
        logger.debug(f"Displaying voucher form for voucher_name: {voucher_name}, voucher_type_id: {voucher_type_id}")
        session = Session()
        try:
            result = session.execute(text("""
                SELECT column_name, data_type, is_mandatory, display_order
                FROM voucher_columns
                WHERE voucher_type_id = :voucher_type_id
                ORDER BY display_order
            """), {"voucher_type_id": voucher_type_id}).fetchall()
            columns = result
            
            # Clear previous form, keeping the custom voucher button
            while self.create_layout.count() > 1:
                item = self.create_layout.takeAt(1)
                if item.widget():
                    item.widget().deleteLater()

            VoucherClass = VOUCHER_WIDGETS.get(voucher_name, BaseVoucherForm)  # Fallback to base for unmatched/custom
            logger.info(f"Using voucher class {VoucherClass.__name__} for {voucher_name}")
            voucher_widget = VoucherClass(parent=self, voucher_management=voucher_management, voucher_type_id=voucher_type_id, voucher_category=voucher_category, voucher_name=voucher_name, voucher_data=voucher_data,
                                          save_callback=save_callback, add_product_callback=add_product_callback, entities=entities, products=products, payment_terms=payment_terms)
            self.create_layout.addWidget(voucher_widget)

            logger.debug(f"Displayed voucher form for voucher_type_id: {voucher_type_id}")
        except Exception as e:
            logger.error(f"Failed to display voucher form: {e}")
            QMessageBox.critical(self, "Error", f"Failed to display voucher form: {e}")
        finally:
            session.close()