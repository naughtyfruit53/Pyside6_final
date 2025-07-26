# src/erp/voucher/base_voucher_form.py
# Converted to use SQLAlchemy.

from PySide6.QtWidgets import QWidget, QVBoxLayout, QHBoxLayout, QLabel, QLineEdit, QComboBox, QCheckBox, QTableWidget, QPushButton, QDateEdit, QMessageBox, QScrollArea
from PySide6.QtCore import Qt, QDate
import logging
from datetime import datetime
from sqlalchemy import text
from src.core.config import get_database_url, get_log_path
from src.erp.logic.utils.voucher_utils import get_products, get_payment_terms, get_customers, get_vendors, item_based_vouchers, PRODUCT_COLUMNS
from src.erp.logic.utils.sequence_utils import (
    get_next_doc_sequence, commit_doc_sequence, get_fiscal_year,
    get_next_sales_inv_sequence, get_next_purchase_voucher_sequence, get_next_sales_order_sequence,
    get_next_purchase_order_sequence, get_next_quote_sequence, get_next_proforma_sequence,
    get_next_delivery_challan_sequence, get_next_credit_note_sequence, get_next_debit_note_sequence,
    get_next_grn_sequence, get_next_rejection_in_out_sequence, get_next_internal_return_sequence,
    get_next_contra_voucher_sequence, get_next_inter_department_voucher_sequence, get_next_journal_voucher_sequence,
    get_next_non_sales_credit_note_sequence, get_next_payment_voucher_sequence, get_next_receipt_voucher_sequence
)
from src.erp.voucher.callbacks import add_product_callback, add_customer_callback, add_vendor_callback, close_window_item
from src.erp.logic.utils.utils import number_to_words, STATES, update_state_code
import json

logging.basicConfig(filename=get_log_path(), level=logging.DEBUG, format='%(asctime)s - %(name)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

class BaseVoucherForm(QWidget):
    def __init__(self, parent=None, app=None, module_name=None, voucher_type_id=None, voucher_type_name=None, voucher_data=None, voucher_management=None, voucher_category=None, voucher_name=None, save_callback=None, add_product_callback=None, entities=None, products=None, payment_terms=None):
        super().__init__(parent)
        self.app = app
        self.module_name = module_name
        self.voucher_type_id = voucher_type_id
        self.voucher_type_name = voucher_type_name if voucher_type_name else "Unknown"
        self.voucher_data = voucher_data or {}
        self.voucher_management = voucher_management
        self.voucher_category = voucher_category
        self.voucher_name = voucher_name
        self.save_callback = save_callback
        self.add_product_cb = add_product_callback
        self.entities = entities
        self.products = products
        self.payment_terms = payment_terms
        self.entries = {}
        self.product_rows = self.voucher_data.get("items", []) if self.voucher_data else []
        self.setObjectName("baseVoucherForm")  # Set object name for potential QSS styling
        self.setup_ui()

    def setup_ui(self):
        logger.info(f"Creating voucher form for {self.voucher_type_name} (ID: {self.voucher_type_id})")
        # Check for existing layout and clear it
        if self.layout():
            while self.layout().count():
                item = self.layout().takeAt(0)
                if item.widget():
                    item.widget().deleteLater()
            self.setLayout(None)

        main_layout = QVBoxLayout(self)
        main_layout.setContentsMargins(10, 10, 10, 10)

        scroll = QScrollArea()
        scroll.setWidgetResizable(True)
        content_widget = QWidget()
        scroll.setWidget(content_widget)
        self.content_layout = QVBoxLayout(content_widget)
        self.content_layout.setAlignment(Qt.AlignLeft | Qt.AlignTop)

        title_label = QLabel(f"{self.voucher_type_name} Form")
        title_label.setObjectName("dialogTitleLabel")
        self.content_layout.addWidget(title_label)

        from src.erp.logic.database.session import Session  # Import here to ensure availability
        session = Session()
        try:
            result = session.execute(text("SELECT column_name, data_type, is_mandatory, display_order, is_calculated, calculation_logic FROM voucher_columns WHERE voucher_type_id = :voucher_type_id ORDER BY display_order"), {"voucher_type_id": self.voucher_type_id}).fetchall()
            columns = result
        except Exception as e:
            logger.error(f"Failed to fetch voucher columns: {e}")
            QMessageBox.critical(self, "Error", f"Failed to fetch voucher columns: {e}")
            return
        finally:
            session.close()

        common_fields = [
            ("Voucher Date", "date", True),
            ("Party Name", "combobox", True),
            ("State", "combobox", False),
            ("State Code", "text", False),
            ("Payment Terms", "combobox", False),
        ]

        sequence = None
        sequence_functions = {
            "Sales Voucher": get_next_sales_inv_sequence,
            "Purchase Voucher": get_next_purchase_voucher_sequence,
            "Sales Order": get_next_sales_order_sequence,
            "Purchase Order": get_next_purchase_order_sequence,
            "Quotation": get_next_quote_sequence,
            "Proforma Invoice": get_next_proforma_sequence,
            "Delivery Challan": lambda: get_next_delivery_challan_sequence(),
            "Credit Note": get_next_credit_note_sequence,
            "Debit Note": get_next_debit_note_sequence,
            "GRN (Goods Received Note)": lambda: None,  # Handled in form
            "Rejection In": get_next_rejection_in_out_sequence,
            "Rejection Out": get_next_rejection_in_out_sequence,
            "Internal Return": get_next_internal_return_sequence,
            "Contra Voucher": get_next_contra_voucher_sequence,
            "Inter Department Voucher": get_next_inter_department_voucher_sequence,
            "Journal Voucher": get_next_journal_voucher_sequence,
            "Non-Sales Credit Note": get_next_non_sales_credit_note_sequence,
            "Payment Voucher": get_next_payment_voucher_sequence,
            "Receipt Voucher": get_next_receipt_voucher_sequence
        }
        sequence_func = sequence_functions.get(self.voucher_type_name)
        if sequence_func:
            sequence = sequence_func()
        if sequence:
            self.entries["Voucher Number"] = sequence
        else:
            logger.warning(f"No sequence generated for {self.voucher_type_name}")

        all_fields = common_fields + [(c[0], c[1], c[2]) for c in columns if c[0] not in [f[0] for f in common_fields]]

        # Special handling for Voucher Number to place it next to the label (side-by-side, left-aligned)
        voucher_num_layout = QHBoxLayout()
        voucher_num_label = QLabel("Voucher Number*")
        voucher_num_label.setObjectName("fieldLabel")
        voucher_num_layout.addWidget(voucher_num_label)
        voucher_num_entry = QLineEdit()
        voucher_num_entry.setObjectName("textEntry")
        voucher_num_entry.setText(self.voucher_data.get("Voucher Number", sequence))
        voucher_num_entry.setReadOnly(True)
        voucher_num_entry.setAlignment(Qt.AlignLeft)  # Explicitly set text alignment to left
        voucher_num_entry.setStyleSheet("text-align: left;")  # Force left alignment via inline stylesheet
        self.entries["Voucher Number"] = voucher_num_entry
        voucher_num_layout.addWidget(voucher_num_entry)
        voucher_num_layout.setSpacing(5)  # Reduce spacing between label and field for closer placement
        voucher_num_layout.addStretch()  # Push to left
        voucher_num_layout.setAlignment(Qt.AlignLeft)
        self.content_layout.addLayout(voucher_num_layout)

        for column_name, data_type, is_mandatory in all_fields:
            row_layout = QHBoxLayout()
            label_text = f"{column_name}{'*' if is_mandatory else ''}"
            label = QLabel(label_text)
            label.setObjectName("fieldLabel")
            row_layout.addWidget(label)

            if data_type.lower() == "date":
                entry = QDateEdit()
                entry.setObjectName("textEntry")
                entry.setCalendarPopup(True)
                entry.setDate(QDate.fromString(self.voucher_data.get(column_name, QDate.currentDate().toString("yyyy-MM-dd")), "yyyy-MM-dd"))
                self.entries[column_name] = entry
            elif column_name == "Party Name":
                entry = QComboBox()
                entry.setObjectName("textEntry")
                is_sales_voucher = self.voucher_type_name in ["Sales Voucher", "Sales Order", "Quotation", "Proforma Invoice", "Delivery Challan", "Credit Note", "Internal Return"]
                entities_list = get_customers() if is_sales_voucher else get_vendors()
                entry.addItems(entities_list or ["No entities available"])
                entry.setEditable(True)
                entry.setCurrentText(self.voucher_data.get(column_name, ""))
                self.entries[column_name] = entry
                add_entity_button = QPushButton("Add")
                add_entity_button.setObjectName("actionButton")
                if is_sales_voucher:
                    add_entity_button.clicked.connect(lambda: add_customer_callback(self, entry, self.voucher_management))
                else:
                    add_entity_button.clicked.connect(lambda: add_vendor_callback(self, entry, self.voucher_management))
                row_layout.addWidget(add_entity_button)
            elif column_name == "State":
                entry = QComboBox()
                entry.setObjectName("textEntry")
                entry.addItems([s[0] for s in STATES])
                entry.setCurrentText(self.voucher_data.get(column_name, ""))
                entry.currentTextChanged.connect(lambda: self.update_state_code())
                self.entries[column_name] = entry
            elif column_name == "State Code":
                entry = QLineEdit()
                entry.setObjectName("textEntry")
                entry.setReadOnly(True)
                entry.setText(self.voucher_data.get(column_name, ""))
                self.entries[column_name] = entry
            elif column_name == "Payment Terms":
                entry = QComboBox()
                entry.setObjectName("textEntry")
                payment_terms_list = self.payment_terms if self.payment_terms is not None else get_payment_terms()
                entry.addItems(payment_terms_list or ["No payment terms available"])
                entry.setEditable(True)
                entry.setCurrentText(self.voucher_data.get(column_name, ""))
                self.entries[column_name] = entry
            elif data_type.lower() == "real" or data_type.lower() == "integer":
                entry = QLineEdit()
                entry.setObjectName("textEntry")
                entry.setText(self.voucher_data.get(column_name, ""))
                self.entries[column_name] = entry
            elif data_type.lower() == "checkbox":
                entry = QCheckBox()
                entry.setChecked(self.voucher_data.get(column_name, "No") == "Yes")
                self.entries[column_name] = entry
            else:
                entry = QLineEdit()
                entry.setObjectName("textEntry")
                entry.setText(self.voucher_data.get(column_name, ""))
                self.entries[column_name] = entry
            row_layout.addWidget(entry)
            row_layout.addStretch()
            row_layout.setAlignment(Qt.AlignLeft)
            self.content_layout.addLayout(row_layout)

        if self.voucher_type_name in item_based_vouchers:
            product_label = QLabel("Products")
            product_label.setObjectName("fieldLabel")
            self.content_layout.addWidget(product_label)

            product_row_layout = QHBoxLayout()
            self.product_combo = QComboBox()
            self.product_combo.setObjectName("textEntry")
            if self.products is None:
                self.products = get_products()
            self.product_combo.addItems([p[1] for p in self.products] or ["No products available"])
            self.product_combo.setEditable(True)
            product_row_layout.addWidget(self.product_combo)

            add_product_button = QPushButton("Add Product")
            add_product_button.setObjectName("actionButton")
            callback_to_use = self.add_product_cb if self.add_product_cb else add_product_callback
            add_product_button.clicked.connect(lambda: callback_to_use(self, self.product_combo, self.voucher_management))
            product_row_layout.addWidget(add_product_button)
            product_row_layout.addStretch()
            product_row_layout.setAlignment(Qt.AlignLeft)
            self.content_layout.addLayout(product_row_layout)

            self.item_table = QTableWidget()
            self.item_table.setRowCount(0)
            self.item_table.setColumnCount(len(PRODUCT_COLUMNS))
            self.item_table.setHorizontalHeaderLabels([col[0] for col in PRODUCT_COLUMNS])
            self.item_table.setObjectName("tableWidget")
            self.content_layout.addWidget(self.item_table)

            remove_product_button = QPushButton("Remove Selected Product")
            remove_product_button.setObjectName("actionButton")
            remove_product_button.clicked.connect(self.remove_product)
            self.content_layout.addWidget(remove_product_button)

        total_layout = QHBoxLayout()
        total_label = QLabel("Total Amount")
        total_label.setObjectName("fieldLabel")
        self.total_amount = QLineEdit()
        self.total_amount.setObjectName("textEntry")
        self.total_amount.setReadOnly(True)
        total_layout.addWidget(total_label)
        total_layout.addWidget(self.total_amount)
        total_layout.addStretch()
        total_layout.setAlignment(Qt.AlignLeft)
        self.content_layout.addLayout(total_layout)

        words_layout = QHBoxLayout()
        words_label = QLabel("Amount in Words")
        words_label.setObjectName("fieldLabel")
        self.amount_in_words = QLineEdit()
        self.amount_in_words.setObjectName("textEntry")
        self.amount_in_words.setReadOnly(True)
        words_layout.addWidget(words_label)
        words_layout.addWidget(self.amount_in_words)
        words_layout.addStretch()
        words_layout.setAlignment(Qt.AlignLeft)
        self.content_layout.addLayout(words_layout)

        button_layout = QHBoxLayout()
        save_button = QPushButton("Save")
        save_button.setObjectName("actionButton")
        save_button.clicked.connect(self.save_voucher)
        cancel_button = QPushButton("Cancel")
        cancel_button.setObjectName("actionButton")
        cancel_button.clicked.connect(lambda: close_window_item(self, self))
        button_layout.addWidget(cancel_button)
        button_layout.addWidget(save_button)
        button_layout.addStretch()
        button_layout.setAlignment(Qt.AlignLeft)
        self.content_layout.addLayout(button_layout)

        main_layout.addWidget(scroll)
        if self.voucher_type_name in item_based_vouchers:
            self.populate_product_table(self.item_table)
            self.update_product_frame_position()

    def update_state_code(self):
        state = self.entries["State"].currentText()
        state_code = update_state_code(state)
        self.entries["State Code"].setText(state_code)

    def update_product_frame_position(self):
        self.item_table.resizeColumnsToContents()

    def populate_product_table(self, table):
        table.setRowCount(len(self.product_rows))
        for row_idx, product in enumerate(self.product_rows):
            for col_idx, (col_name, _, _, _, _, calc_logic) in enumerate(PRODUCT_COLUMNS):
                item = QTableWidgetItem()
                if calc_logic:
                    item.setFlags(item.flags() & ~Qt.ItemIsEditable)
                value = str(product.get(col_name, ""))
                item.setText(value)
                table.setItem(row_idx, col_idx, item)
        self.update_totals()

    def remove_product(self):
        selected = self.item_table.currentRow()
        if selected >= 0:
            self.item_table.removeRow(selected)
            self.product_rows.pop(selected)
        self.update_totals()

    def update_totals(self):
        total = 0.0
        for product in self.product_rows:
            amount = float(product.get("Amount", 0))
            total += amount
        self.total_amount.setText(f"{total:.2f}")
        self.amount_in_words.setText(number_to_words(total))

    def save_voucher(self):
        from src.erp.logic.database.session import Session  # Import here to ensure availability
        session = Session()
        try:
            mandatory_fields = [row[0] for row in session.execute(text("SELECT column_name FROM voucher_columns WHERE voucher_type_id = :voucher_type_id AND is_mandatory = 1"), {"voucher_type_id": self.voucher_type_id}).fetchall()]
            mandatory_fields.append("Voucher Number")
            mandatory_fields.append("Voucher Date")
            mandatory_fields.append("Party Name")

            for field in mandatory_fields:
                if field in self.entries:
                    value = self.entries[field].text() if isinstance(self.entries[field], QLineEdit) else self.entries[field].currentText() if isinstance(self.entries[field], QComboBox) else ""
                    if not value:
                        QMessageBox.critical(self, "Error", f"Mandatory field '{field}' is missing")
                        return

            voucher_data = {}
            for column_name, entry in self.entries.items():
                if isinstance(entry, QLineEdit):
                    voucher_data[column_name] = entry.text()
                elif isinstance(entry, QComboBox):
                    voucher_data[column_name] = entry.currentText()
                elif isinstance(entry, QDateEdit):
                    voucher_data[column_name] = entry.date().toString("yyyy-MM-dd")
                elif isinstance(entry, QCheckBox):
                    voucher_data[column_name] = "Yes" if entry.isChecked() else "No"

            if self.voucher_type_name in item_based_vouchers and not self.product_rows:
                QMessageBox.critical(self, "Error", f"At least one product is required for {self.voucher_type_name}")
                return

            if self.voucher_type_name == "Delivery Challan":
                for product in self.product_rows:
                    product_id = product.get("product_id")
                    quantity = float(product.get("quantity", 0))
                    session.execute(text("SELECT quantity FROM stock WHERE product_id = :product_id"), {"product_id": product_id})
                    current_stock = session.fetchone()
                    if not current_stock or current_stock[0] < quantity:
                        QMessageBox.critical(self, "Error", f"Insufficient stock for product {product['product_name']}")
                        return

            voucher_id = self.voucher_data.get("id")
            if voucher_id:
                session.execute(text("SELECT voucher_number FROM voucher_instances WHERE id = :voucher_id"), {"voucher_id": voucher_id})
                existing_voucher_number = session.fetchone()[0]
                voucher_data["Voucher Number"] = existing_voucher_number
                session.execute(text("UPDATE voucher_instances SET voucher_type_id = :voucher_type_id, voucher_number = :voucher_number, date = :date, data = :data, total_amount = :total_amount WHERE id = :voucher_id"),
                                {"voucher_type_id": self.voucher_type_id, "voucher_number": voucher_data["Voucher Number"], "date": voucher_data["Voucher Date"], "data": json.dumps(voucher_data), "total_amount": float(self.total_amount.text() or 0), "voucher_id": voucher_id})
                session.execute(text("DELETE FROM voucher_items WHERE voucher_id = :voucher_id"), {"voucher_id": voucher_id})
                action = "UPDATE"
            else:
                insert_params = {
                    "voucher_type_id": self.voucher_type_id,
                    "voucher_number": voucher_data["Voucher Number"],
                    "created_at": datetime.now(),
                    "date": voucher_data["Voucher Date"],
                    "data": json.dumps(voucher_data),
                    "module_name": self.module_name,
                    "record_id": 0,
                    "total_amount": float(self.total_amount.text() or 0)
                }
                result = session.execute(text("""
                    INSERT INTO voucher_instances (voucher_type_id, voucher_number, created_at, date, data, module_name, record_id, total_amount)
                    VALUES (:voucher_type_id, :voucher_number, :created_at, :date, :data, :module_name, :record_id, :total_amount) RETURNING id
                """), insert_params)
                voucher_id = result.fetchone()[0]
                action = "INSERT"

            for product in self.product_rows:
                session.execute(text("""
                    INSERT INTO voucher_items (voucher_id, product_name, hsn_code, quantity, unit, unit_price, gst_rate, amount)
                    VALUES (:voucher_id, :product_name, :hsn_code, :quantity, :unit, :unit_price, :gst_rate, :amount)
                """), {"voucher_id": voucher_id, "product_name": product["product_name"], "hsn_code": product["hsn_code"], "quantity": product["quantity"], "unit": product["unit"], "unit_price": product["unit_price"], "gst_rate": product["gst_rate"], "amount": product["amount"]})

            if self.voucher_type_name == "Delivery Challan":
                for product in self.product_rows:
                    session.execute(text("UPDATE stock SET quantity = quantity - :quantity WHERE product_id = :product_id"), {"quantity": float(product.get("quantity", 0)), "product_id": product.get("product_id")})

            session.execute(text("INSERT INTO audit_log (table_name, record_id, action, user, timestamp) VALUES (:table_name, :record_id, :action, :user, :timestamp)"),
                            {"table_name": "voucher_instances", "record_id": voucher_id, "action": action, "user": "system_user", "timestamp": datetime.now().strftime("%Y-%m-%d %H:%M:%S")})
            session.commit()

            QMessageBox.information(self, "Success", f"{self.voucher_type_name} saved successfully")
            if self.voucher_management:
                self.voucher_management.refresh_voucher_content()
            if self.save_callback:
                self.save_callback()
            self.close()  # Close the dialog/widget instead of accept() since it's QDialog
        except Exception as e:
            session.rollback()
            logger.error(f"Failed to save voucher: {e}")
            QMessageBox.critical(self, "Error", f"Database error: {e}")
        finally:
            session.close()