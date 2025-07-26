# Revised script: src/erp/voucher/voucher_management.py

from PySide6.QtWidgets import QWidget, QVBoxLayout, QHBoxLayout, QComboBox, QTableWidget, QTableWidgetItem, QPushButton, QMessageBox, QHeaderView, QMenu
from PySide6.QtGui import QAction
from PySide6.QtCore import Qt
import logging
from sqlalchemy import text
from src.erp.logic.database.session import engine, Session
from src.core.config import get_database_url
from src.erp.logic.database.voucher import get_voucher_types, get_voucher_type_id, item_based_vouchers
from src.erp.voucher.voucher_operations import add_product_and_open_popup, edit_voucher, delete_voucher, save_voucher_pdf
# Import all custom form classes
from src.erp.voucher.forms.sales_voucher_form import SalesVoucherForm
from src.erp.voucher.forms.purchase_voucher_form import PurchaseVoucherForm
from src.erp.voucher.forms.sales_order_form import SalesOrderForm
from src.erp.voucher.forms.purchase_order_form import PurchaseOrderForm
from src.erp.voucher.forms.quotation_form import QuotationForm
from src.erp.voucher.forms.proforma_invoice_form import ProformaInvoiceForm
from src.erp.voucher.forms.delivery_challan_form import DeliveryChallanForm
from src.erp.voucher.forms.credit_note_form import CreditNoteForm
from src.erp.voucher.forms.debit_note_form import DebitNoteForm
from src.erp.voucher.forms.grn_form import GRNForm
from src.erp.voucher.forms.rejection_in_out_form import RejectionInOutForm
from src.erp.voucher.forms.internal_return_form import InternalReturnForm
from src.erp.voucher.base_voucher_form import BaseVoucherForm  # Import BaseVoucherForm
from src.erp.logic.utils.sequence_utils import *  # Import all sequence functions to fix NameError

logging.basicConfig(filename='app.log', level=logging.DEBUG, format='%(asctime)s - %(name)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

class VoucherManagement:
    def __init__(self, parent, app):
        self.parent = parent
        self.app = app
        self.item_based_vouchers = item_based_vouchers
        self.create_container = None  # Store reference to the create widget/container
        self.view_widget = None  # Store reference to the view widget
        self.voucher_type_name = None

    def normalize_voucher_type(self, voucher_type_name):
        """Normalize voucher type name to match database voucher_name."""
        normalized = voucher_type_name.replace('vouchers-', '').replace('_', ' ')
        lower_norm = normalized.lower()
        
        # Special cases to handle variations without breaking casing
        if 'grn' in lower_norm or 'goods received note' in lower_norm:
            logger.debug(f"Normalized '{voucher_type_name}' to 'GRN (Goods Received Note)' via special case")
            return 'GRN (Goods Received Note)'
        elif 'rejection in' in lower_norm:
            logger.debug(f"Normalized '{voucher_type_name}' to 'Rejection In' via special case")
            return 'Rejection In'
        elif 'rejection out' in lower_norm:
            logger.debug(f"Normalized '{voucher_type_name}' to 'Rejection Out' via special case")
            return 'Rejection Out'
        
        # For other types, apply title() but log for debug
        titled = normalized.title()
        logger.debug(f"Normalized '{voucher_type_name}' to '{titled}' (no special case)")
        return titled

    def create_voucher_frame(self, parent_widget, mode, voucher_type_name):
        layout = parent_widget.layout()
        if not layout:
            layout = QVBoxLayout(parent_widget)
            parent_widget.setLayout(layout)
        else:
            while layout.count():
                item = layout.takeAt(0)
                if item.widget():
                    item.widget().deleteLater()

        self.voucher_type_name = self.normalize_voucher_type(voucher_type_name)

        if mode == "create_voucher":
            self.create_container = parent_widget  # Store the create container
            # Directly refresh with the normalized voucher name
            self.refresh_voucher_content(self.voucher_type_name)

        elif mode == "view_vouchers":
            self.view_widget = parent_widget  # Store the view widget
            self.create_voucher_table(parent_widget, self.voucher_type_name)

    def handle_voucher_selection(self, voucher_name):
        logger.debug(f"Handling voucher selection: {voucher_name}")
        try:
            self.refresh_voucher_content(voucher_name)
        except Exception as e:
            logger.error(f"Failed to handle voucher selection for {voucher_name}: {e}")
            QMessageBox.critical(self.parent, "Error", f"Failed to handle voucher selection: {str(e)}")

    def refresh_voucher_content(self, voucher_name):
        self.voucher_type_name = voucher_name
        logger.debug(f"Refreshing voucher content for {voucher_name}")
        session = Session()
        try:
            voucher_type_id = get_voucher_type_id(voucher_name)
            if voucher_type_id is None:
                logger.error(f"No voucher type ID found for {voucher_name}")
                QMessageBox.critical(self.parent, "Error", f"Voucher type {voucher_name} not found in database")
                return
            logger.debug(f"Found voucher type ID {voucher_type_id} for {voucher_name}")

            entities = self.get_entities(voucher_name)
            products = self.get_products()
            payment_terms = self.get_payment_terms()

            # Complete dictionary for all custom forms
            form_classes = {
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
                "Rejection In": RejectionInOutForm,  # Map to shared form
                "Rejection Out": RejectionInOutForm,  # Map to shared form
                "Internal Return": InternalReturnForm,
                # Add more if new forms are created (e.g., for financial vouchers)
            }

            form_class = form_classes.get(voucher_name, BaseVoucherForm)  # Fallback to base for unmatched/custom
            logger.info(f"Using form class {form_class.__name__} for voucher {voucher_name}")

            # Clear existing content in create container
            layout = self.create_container.layout()
            if layout is None:
                layout = QVBoxLayout(self.create_container)
                self.create_container.setLayout(layout)
            while layout.count() > 0:  # No combo now, clear all
                item = layout.takeAt(0)
                if item.widget():
                    item.widget().deleteLater()

            kwargs = {
                "parent": self.create_container,
                "app": self.app,
                "module_name": f"vouchers-{voucher_name.lower().replace(' ', '_').replace('_(goods_received_note)', '')}",
                "voucher_type_id": voucher_type_id,
                "voucher_type_name": voucher_name,
                "voucher_data": None,
                "voucher_management": self,
                "entities": entities,
                "products": products
            }

            if voucher_name != "GRN (Goods Received Note)":
                kwargs["payment_terms"] = payment_terms

            form = form_class(**kwargs)
            form.entities = entities  # Manual fallback set for forms like PurchaseOrderForm that might not handle it
            layout.addWidget(form)
        except Exception as e:
            logger.error(f"Failed to refresh voucher content for {voucher_name}: {e}")
            QMessageBox.critical(self.parent, "Error", f"Failed to refresh voucher content: {str(e)}")
        finally:
            session.close()

    def refresh_view(self):
        if self.view_widget:
            self.create_voucher_table(self.view_widget, self.voucher_type_name)

    def create_voucher_table(self, parent_widget, voucher_type_name):
        session = Session()
        try:
            voucher_type_id = get_voucher_type_id(voucher_type_name)
            if voucher_type_id is None:
                logger.error(f"No voucher type ID found for {voucher_type_name}")
                QMessageBox.critical(parent_widget, "Error", f"Voucher type {voucher_type_name} not found")
                return
            self.current_voucher_type_id = voucher_type_id
            is_sales = "sales" in voucher_type_name.lower() or "delivery" in voucher_type_name.lower() or "credit" in voucher_type_name.lower() or "rejection out" in voucher_type_name.lower()
            party_label = "Customer Name" if is_sales else "Vendor Name"
            result = session.execute(text("""
                SELECT vi.id, vi.voucher_number, vi.date, vi.total_amount, vi.data::json ->> 'Party Name' AS party_name
                FROM voucher_instances vi
                WHERE vi.voucher_type_id = :voucher_type_id
                ORDER BY vi.created_at DESC
            """), {"voucher_type_id": voucher_type_id}).fetchall()

            table = QTableWidget()
            table.setRowCount(len(result))
            table.setColumnCount(3)
            table.setHorizontalHeaderLabels([f"{voucher_type_name} No.", party_label, "Total Amount"])

            for row, (voucher_id, voucher_number, voucher_date, total_amount, party_name) in enumerate(result):
                formatted_number = f"{voucher_number}/{voucher_date.strftime('%d-%b')}" if voucher_date else voucher_number
                voucher_num_item = QTableWidgetItem(formatted_number)
                voucher_num_item.setData(Qt.UserRole, voucher_id)
                table.setItem(row, 0, voucher_num_item)
                table.setItem(row, 1, QTableWidgetItem(party_name or ""))
                table.setItem(row, 2, QTableWidgetItem(str(total_amount) if total_amount is not None else ""))

            table.resizeColumnsToContents()
            table.horizontalHeader().setSectionResizeMode(QHeaderView.Stretch)
            table.setContextMenuPolicy(Qt.CustomContextMenu)
            table.customContextMenuRequested.connect(lambda pos: self.show_context_menu(pos, table))

            layout = parent_widget.layout()
            if layout:
                while layout.count():
                    item = layout.takeAt(0)
                    if item.widget():
                        item.widget().deleteLater()
            else:
                layout = QVBoxLayout(parent_widget)
            layout.addWidget(table)
            parent_widget.setLayout(layout)
        except Exception as e:
            logger.error(f"Failed to create voucher table for {voucher_type_name}: {e}")
            QMessageBox.critical(parent_widget, "Error", f"Failed to create voucher table: {str(e)}")
        finally:
            session.close()

    def show_context_menu(self, position, table):
        row = table.rowAt(position.y())
        if row < 0:
            return
        vid = table.item(row, 0).data(Qt.UserRole)
        menu = QMenu()
        edit_act = QAction(f"Edit {self.voucher_type_name}")
        edit_act.triggered.connect(lambda: edit_voucher(self.parent, vid))
        menu.addAction(edit_act)
        delete_act = QAction(f"Delete {self.voucher_type_name}")
        delete_act.triggered.connect(lambda: delete_voucher(self.parent, vid))
        menu.addAction(delete_act)
        pdf_act = QAction("Save as PDF")
        pdf_act.triggered.connect(lambda: save_voucher_pdf(self.app, vid, self.current_voucher_type_id, self.voucher_type_name))
        menu.addAction(pdf_act)
        menu.exec(table.viewport().mapToGlobal(position))

    def get_entities(self, voucher_type_name):
        session = Session()
        try:
            is_sales = "sales" in voucher_type_name.lower() or "delivery" in voucher_type_name.lower() or "credit" in voucher_type_name.lower() or "rejection out" in voucher_type_name.lower()
            if is_sales:
                result = session.execute(text("SELECT name FROM customers ORDER BY name")).fetchall()
            else:
                result = session.execute(text("SELECT name FROM vendors ORDER BY name")).fetchall()
            return [row[0] for row in result]
        except Exception as e:
            logger.error(f"Error fetching entities for {voucher_type_name}: {e}")
            QMessageBox.critical(self.parent, "Error", f"Error fetching entities: {str(e)}")
            return []
        finally:
            session.close()

    def get_products(self):
        session = Session()
        try:
            result = session.execute(text("SELECT id, name, hsn_code, unit, unit_price, gst_rate FROM products")).fetchall()
            return result
        except Exception as e:
            logger.error(f"Error fetching products: {e}")
            QMessageBox.critical(self.parent, "Error", f"Error fetching products: {str(e)}")
            return []
        finally:
            session.close()

    def get_payment_terms(self):
        session = Session()
        try:
            result = session.execute(text("SELECT term FROM payment_terms")).fetchall()
            return [row[0] for row in result]
        except Exception as e:
            logger.error(f"Error fetching payment terms: {e}")
            QMessageBox.critical(self.parent, "Error", f"Error fetching payment terms: {str(e)}")
            return []
        finally:
            session.close()