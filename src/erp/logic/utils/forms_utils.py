# Revised script: src/erp/logic/utils/forms_utils.py

from PySide6.QtWidgets import QWidget, QVBoxLayout, QHBoxLayout, QLabel, QLineEdit, QComboBox, QPushButton, QDateEdit, QMessageBox, QScrollArea, QTableWidget, QTableWidgetItem, QDialog, QCompleter
from PySide6.QtCore import Qt, QDate
from PySide6.QtGui import QResizeEvent, QDoubleValidator
from PySide6.QtWidgets import QHeaderView
import json
import logging
import os
from datetime import datetime
from sqlalchemy import text
from src.erp.logic.database.session import engine, Session
from src.core.config import get_database_url, get_log_path, get_static_path
from src.erp.logic.utils.voucher_utils import get_products, get_payment_terms, PRODUCT_COLUMNS, get_product_stock, get_vendors, get_customers
from src.erp.voucher.callbacks import add_product_callback, add_customer_callback, add_vendor_callback
from src.erp.logic.utils.utils import number_to_words
import shiboken6

logging.basicConfig(filename=get_log_path(), level=logging.DEBUG, format='%(asctime)s - %(name)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

def common_init(self, voucher_type_name, voucher_data, products_func, payment_terms_func):
    self.voucher_data = voucher_data or {}
    self.products = self.products if hasattr(self, 'products') and self.products is not None else products_func()
    self.payment_terms = self.payment_terms if hasattr(self, 'payment_terms') and self.payment_terms is not None else payment_terms_func()
    self.entries = {}
    self.product_rows = self.voucher_data.get("items", []) if self.voucher_data else []
    # Add product_id to existing product_rows if editing
    if self.voucher_data and self.product_rows:
        session = Session()
        try:
            for product in self.product_rows:
                if not isinstance(product, dict):
                    logger.warning(f"Invalid product row type {type(product)} in {voucher_type_name}, skipping")
                    continue
                result = session.execute(text("SELECT id FROM products WHERE name = :name AND hsn_code = :hsn_code"), {"name": product.get("Name"), "hsn_code": product.get("HSN Code")}).fetchone()
                if result:
                    product["product_id"] = result[0]
                else:
                    logger.warning(f"Product not found for {voucher_type_name} edit: {product.get('Name')}")
            logger.debug(f"Initialized product_rows for {voucher_type_name}: {self.product_rows}")
        except Exception as e:
            logger.error(f"Error adding product_id to rows for {voucher_type_name}: {e}")
        finally:
            session.close()

def apply_stylesheet(self, qss_filename):
    qss_path = os.path.join(get_static_path(""), "qss", qss_filename)
    if os.path.exists(qss_path):
        with open(qss_path, "r") as f:
            self.setStyleSheet(f.read())
    else:
        logger.warning(f"Stylesheet not found: {qss_path}")

def create_title_label(title_text):
    title_label = QLabel(title_text)
    title_label.setObjectName("titleLabel")
    title_label.setAlignment(Qt.AlignCenter)
    title_label.setStyleSheet("border: none; background: transparent;")
    return title_label

def create_header_row(fields):
    header_row = QHBoxLayout()
    header_row.setSpacing(10)
    entries = {}
    for label_text, entry_type, entry_key, default_value in fields:
        label = QLabel(label_text)
        label.setObjectName("fieldLabel")
        label.setAlignment(Qt.AlignLeft | Qt.AlignVCenter if label_text == fields[0][0] else Qt.AlignRight | Qt.AlignVCenter)
        label.setStyleSheet("font-weight: bold; color: #333333; padding: 2px 0px 2px 5px; background-color: transparent; border: none;")
        if entry_type == 'text':
            entry = QLineEdit()
            entry.setObjectName("numberEntry")
            entry.setAlignment(Qt.AlignLeft | Qt.AlignVCenter)
            entry.setStyleSheet("background-color: #f0f0f0; border: 1px solid #cccccc; border-radius: 4px; padding: 5px 5px 5px 0px; font-size: 12px; color: #333333;")
            entry.setText(default_value)
            entry.setReadOnly(True)
        elif entry_type == 'date':
            entry = QDateEdit()
            entry.setObjectName("dateEntry")
            entry.lineEdit().setAlignment(Qt.AlignLeft | Qt.AlignVCenter)
            entry.setCalendarPopup(True)
            entry.setDate(QDate.fromString(default_value, "yyyy-MM-dd") if default_value else QDate.currentDate())
        elif entry_type == 'combo':
            entry = QComboBox()
            entry.setObjectName("comboEntry")
            entry.setEditable(True)
            entry.lineEdit().setAlignment(Qt.AlignLeft | Qt.AlignVCenter)
        subrow = QHBoxLayout()
        subrow.setSpacing(0)
        subrow.setContentsMargins(0, 0, 0, 0)
        subrow.addWidget(label)
        subrow.addWidget(entry, stretch=1)
        header_row.addLayout(subrow)
        entries[entry_key] = entry
    return header_row, entries

def create_party_row(party_type, entities, payment_terms, voucher_data):
    party_row = QHBoxLayout()
    party_row.setSpacing(10)
    # Party (Customer/Vendor)
    party_label = QLabel(f"{party_type}*")
    party_label.setObjectName("fieldLabel")
    party_label.setAlignment(Qt.AlignLeft | Qt.AlignVCenter)
    party_combo = QComboBox()
    party_combo.setObjectName("partyCombo")
    party_names = entities
    party_combo.addItems(party_names)
    if not party_names:
        party_combo.addItem(f"Add New {party_type}")
        party_combo.setCurrentIndex(0)
    else:
        party_combo.insertItem(0, f"Add New {party_type}")
        party_combo.setCurrentIndex(-1)
    party_combo.setEditable(True)
    party_combo.lineEdit().setAlignment(Qt.AlignLeft | Qt.AlignVCenter)
    party_combo.setCurrentText(voucher_data.get("Party Name", ""))
    completer = QCompleter(party_combo.model())
    completer.setFilterMode(Qt.MatchContains)
    completer.setCaseSensitivity(Qt.CaseInsensitive)
    completer.setCompletionMode(QCompleter.PopupCompletion)
    party_combo.setCompleter(completer)
    party_subrow = QHBoxLayout()
    party_subrow.setSpacing(0)
    party_subrow.setContentsMargins(0, 0, 0, 0)
    party_subrow.addWidget(party_label)
    party_subrow.addWidget(party_combo, stretch=1)
    party_row.addLayout(party_subrow)

    party_row.addStretch()

    # Payment Terms
    payment_label = QLabel("Payment Terms")
    payment_label.setObjectName("fieldLabel")
    payment_label.setAlignment(Qt.AlignRight | Qt.AlignVCenter)
    payment_combo = QComboBox()
    payment_combo.setObjectName("paymentCombo")
    payment_terms_list = payment_terms or ["No payment terms available"]
    payment_combo.addItems(payment_terms_list)
    payment_combo.setEditable(True)
    payment_combo.lineEdit().setAlignment(Qt.AlignLeft | Qt.AlignVCenter)
    payment_combo.setCurrentText(voucher_data.get("Payment Terms", ""))
    payment_subrow = QHBoxLayout()
    payment_subrow.setSpacing(0)
    payment_subrow.setContentsMargins(0, 0, 0, 0)
    payment_subrow.addWidget(payment_label)
    payment_subrow.addWidget(payment_combo, stretch=1)
    party_row.addLayout(payment_subrow)

    return party_row, party_combo, payment_combo

def create_product_table(columns=PRODUCT_COLUMNS, labels=None):
    item_table = QTableWidget()
    item_table.setObjectName("productTable")
    item_table.setRowCount(0)
    item_table.setColumnCount(len(columns))
    header_labels = labels or [c[0] if isinstance(c, (tuple, list)) else c for c in columns]
    item_table.setHorizontalHeaderLabels(header_labels)
    item_table.horizontalHeader().setSectionResizeMode(0, QHeaderView.Stretch)
    for i in range(1, len(columns)):
        item_table.horizontalHeader().setSectionResizeMode(i, QHeaderView.ResizeToContents)
    item_table.verticalHeader().setVisible(True)
    item_table.verticalHeader().setSectionResizeMode(QHeaderView.ResizeToContents)
    item_table.verticalHeader().setDefaultSectionSize(35)
    return item_table

def create_remove_button(remove_func):
    remove_product_button = QPushButton("Remove Selected Product")
    remove_product_button.setObjectName("removeProductButton")
    remove_product_button.clicked.connect(remove_func)
    return remove_product_button

def create_total_words():
    total_layout = QHBoxLayout()
    total_label = QLabel("Total Amount")
    total_label.setObjectName("fieldLabel")
    total_amount = QLineEdit()
    total_amount.setObjectName("totalAmountEntry")
    total_amount.setReadOnly(True)
    total_subrow = QHBoxLayout()
    total_subrow.setSpacing(0)
    total_subrow.addWidget(total_label)
    total_subrow.addWidget(total_amount, stretch=1)
    total_layout.addLayout(total_subrow)

    words_layout = QHBoxLayout()
    words_label = QLabel("Amount in Words")
    words_label.setObjectName("fieldLabel")
    amount_in_words = QLineEdit()
    amount_in_words.setObjectName("amountWordsEntry")
    amount_in_words.setReadOnly(True)
    words_subrow = QHBoxLayout()
    words_subrow.setSpacing(0)
    words_subrow.addWidget(words_label)
    words_subrow.addWidget(amount_in_words, stretch=1)
    words_layout.addLayout(words_subrow)

    return total_layout, words_layout, total_amount, amount_in_words

def create_bottom_layout(app, voucher_type_name, save_func, cancel_func):
    bottom_layout = QHBoxLayout()
    manage_column_button = QPushButton("Manage Column")
    manage_column_button.setObjectName("actionButton")
    manage_column_button.clicked.connect(lambda: app.column_management.manage_columns(app, voucher_type_name))
    bottom_layout.addWidget(manage_column_button)
    bottom_layout.addStretch()

    save_button = QPushButton("Save")
    save_button.setObjectName("saveButton")
    save_button.clicked.connect(save_func)
    cancel_button = QPushButton("Cancel")
    cancel_button.setObjectName("cancelButton")
    cancel_button.clicked.connect(cancel_func)
    bottom_layout.addWidget(cancel_button)
    bottom_layout.addWidget(save_button)

    return bottom_layout

def handle_text_changed(text, combo, names):
    line_edit = combo.lineEdit()
    line_edit.blockSignals(True)
    try:
        text = text.strip()
        lower_text = text.lower()
        idx = find_add_item(combo)
        if not text:
            if idx == -1:
                combo.insertItem(0, "Add New Product" if combo.objectName() == "textEntry" else "Add New Customer" if "customer" in combo.objectName() else "Add New Vendor")
            else:
                combo.setItemText(idx, "Add New Product" if combo.objectName() == "textEntry" else "Add New Customer" if "customer" in combo.objectName() else "Add New Vendor")
        else:
            matching = any(lower_text in p.lower() for p in names)
            if matching:
                if idx != -1:
                    combo.removeItem(idx)
            else:
                new_text = f'Add "{text}" as new product' if combo.objectName() == "textEntry" else f'Add "{text}" as new customer' if "customer" in combo.objectName() else f'Add "{text}" as new vendor'
                if idx == -1:
                    combo.insertItem(0, new_text)
                else:
                    combo.setItemText(idx, new_text)
    finally:
        line_edit.blockSignals(False)

def find_add_item(combo):
    for i in range(combo.count()):
        if combo.itemText(i).startswith("Add "):
            return i
    return -1

def add_new_row(item_table, handle_activated_func, handle_return_pressed_func, products):
    if item_table.rowCount() > 0 and item_table.cellWidget(item_table.rowCount() - 1, 0) is not None:
        return  # Already has an add product row
    row = item_table.rowCount()
    item_table.insertRow(row)
    product_combo = QComboBox()
    product_combo.setObjectName("textEntry")
    product_names = [p[1] for p in products]
    product_combo.addItems(product_names)
    if not product_names:
        product_combo.addItem("Add New Product")
        product_combo.setCurrentIndex(0)
    else:
        product_combo.insertItem(0, "Add New Product")
        product_combo.setCurrentIndex(-1)
    product_combo.setEditable(True)
    completer = QCompleter(product_combo.model())
    completer.setFilterMode(Qt.MatchContains)
    completer.setCaseSensitivity(Qt.CaseInsensitive)
    completer.setCompletionMode(QCompleter.PopupCompletion)
    product_combo.setCompleter(completer)
    product_combo.lineEdit().textChanged.connect(lambda text, combo=product_combo, names=product_names: handle_text_changed(text, combo, names))
    if handle_activated_func is not None:
        product_combo.activated.connect(lambda index, combo=product_combo, r=row: handle_activated_func(index, combo, r))
    if handle_return_pressed_func is not None:
        product_combo.lineEdit().returnPressed.connect(lambda combo=product_combo, r=row: handle_return_pressed_func(combo, r))
    item_table.setCellWidget(row, 0, product_combo)

def open_add_quantity_dialog(product_name, row, combo, products, save_quantity_func):
    selected_product = next((p for p in products if p[1] == product_name), None)
    if not selected_product:
        return
    product_id, name, hsn, unit, unit_price, gst = selected_product
    stock = get_product_stock(product_id) or 0

    dialog = QDialog(combo.parent())
    dialog.setWindowTitle(f"Add Quantity for {name}")
    dialog.setFixedSize(350, 300)
    layout = QVBoxLayout(dialog)

    qty_label = QLabel("Quantity*")
    qty_label.setStyleSheet("border: none; background: transparent;")
    qty_edit = QLineEdit("1")
    qty_edit.setValidator(QDoubleValidator(0.0, 1000000.0, 2))
    layout.addWidget(qty_label)
    layout.addWidget(qty_edit)

    unit_label = QLabel("Unit")
    unit_label.setStyleSheet("border: none; background: transparent;")
    unit_edit = QLineEdit(unit)
    unit_edit.setReadOnly(True)
    layout.addWidget(unit_label)
    layout.addWidget(unit_edit)

    price_label = QLabel("Unit Price*")
    price_label.setStyleSheet("border: none; background: transparent;")
    price_edit = QLineEdit(str(unit_price))
    price_edit.setValidator(QDoubleValidator(0.0, 1000000.0, 2))
    layout.addWidget(price_label)
    layout.addWidget(price_edit)

    gst_label = QLabel("GST Rate*")
    gst_label.setStyleSheet("border: none; background: transparent;")
    gst_edit = QLineEdit(str(gst or 0))
    gst_edit.setValidator(QDoubleValidator(0.0, 100.0, 2))
    layout.addWidget(gst_label)
    layout.addWidget(gst_edit)

    stock_hbox = QHBoxLayout()
    stock_hbox.addStretch()
    stock_label = QLabel(f"Current Stock: {stock}")
    stock_label.setStyleSheet("border: none; background: transparent;")
    color = "red" if stock == 0 else "green"
    stock_label.setStyleSheet(f"color: {color}; border: none; background: transparent;")
    stock_hbox.addWidget(stock_label)
    layout.addLayout(stock_hbox)

    button_layout = QHBoxLayout()
    save_button = QPushButton("Save")
    save_button.setDefault(True)
    save_button.clicked.connect(lambda: save_quantity_func(dialog, product_id, name, hsn, unit, gst_edit.text(), qty_edit.text(), price_edit.text(), row, combo, stock))
    cancel_button = QPushButton("Cancel")
    cancel_button.clicked.connect(dialog.reject)
    button_layout.addWidget(save_button)
    button_layout.addWidget(cancel_button)
    layout.addLayout(button_layout)

    result = dialog.exec()
    if result == QDialog.Rejected:
        if shiboken6.isValid(combo):
            combo.lineEdit().setText("")

def save_quantity_dialog(dialog, product_id, name, hsn, unit, gst_text, qty_text, price_text, row, combo, stock, products, item_table, product_rows, update_totals_func, app, stock_check, form):
    try:
        qty_val = float(qty_text)
        price_val = float(price_text)
        gst_val = float(gst_text or 0)
        if qty_val <= 0 or price_val <= 0:
            raise ValueError("Quantity and unit price must be positive.")
        if stock_check and qty_val > stock:
            raise ValueError("Insufficient stock for this product.")
        
        original_price = next(p[4] for p in products if p[0] == product_id)
        original_gst = next(p[5] for p in products if p[0] == product_id) or 0
        update_price_db = False
        update_gst_db = False
        if abs(price_val - original_price) > 0.01:
            reply = QMessageBox.question(dialog.parent(), "Update Price", "Do you want to update the product price in the database?")
            if reply == QMessageBox.Yes:
                update_price_db = True
        if abs(gst_val - original_gst) > 0.01:
            reply = QMessageBox.question(dialog.parent(), "Update GST", "Do you want to update the product GST rate in the database?")
            if reply == QMessageBox.Yes:
                update_gst_db = True

        amount = qty_val * price_val * (1 + gst_val / 100)

        # Fill the current row
        values = [name, hsn, qty_val, unit, price_val, gst_val, amount]
        for col, val in enumerate(values):
            item = QTableWidgetItem(str(val))
            item_table.setItem(row, col, item)

        # Clear the combo text before removing
        if shiboken6.isValid(combo):
            combo.lineEdit().setText("")

        # Remove the combo from this row
        item_table.removeCellWidget(row, 0)

        # Schedule deletion of the combo
        if shiboken6.isValid(combo):
            combo.deleteLater()

        # Append to product_rows
        product_rows.append({
            "product_id": product_id,
            "Name": name,
            "HSN Code": hsn,
            "Qty": qty_val,
            "Unit": unit,
            "Unit Price": price_val,
            "GST Rate": gst_val,
            "Amount": amount
        })

        add_new_row(item_table, form.handle_activated, form.handle_return_pressed, products)

        update_totals_func(product_rows)

        session = Session()
        try:
            if update_price_db:
                session.execute(text("UPDATE products SET unit_price = :unit_price WHERE id = :product_id"), {"unit_price": price_val, "product_id": product_id})
                session.execute(text("INSERT INTO audit_log (table_name, record_id, action, username, timestamp) VALUES (:table_name, :record_id, :action, :username, :timestamp)"),
                                {"table_name": "products", "record_id": product_id, "action": "UPDATE", "username": app.current_user["username"] if app.current_user else "system_user", "timestamp": datetime.now().strftime("%Y-%m-%d %H:%M:%S")})
            if update_gst_db:
                session.execute(text("UPDATE products SET gst_rate = :gst_rate WHERE id = :product_id"), {"gst_rate": gst_val, "product_id": product_id})
                session.execute(text("INSERT INTO audit_log (table_name, record_id, action, username, timestamp) VALUES (:table_name, :record_id, :action, :username, :timestamp)"),
                                {"table_name": "products", "record_id": product_id, "action": "UPDATE", "username": app.current_user["username"] if app.current_user else "system_user", "timestamp": datetime.now().strftime("%Y-%m-%d %H:%M:%S")})
            session.commit()
        finally:
            session.close()
        # Update local products list
        for idx, p in enumerate(products):
            if p[0] == product_id:
                new_tuple = list(p)
                if update_price_db:
                    new_tuple[4] = price_val
                if update_gst_db:
                    new_tuple[5] = gst_val
                products[idx] = tuple(new_tuple)
                break

        dialog.accept()
    except ValueError as e:
        QMessageBox.critical(dialog, "Error", str(e))

def populate_product_table(table, product_rows, add_new_row_func=None, products=None, handle_activated=None, handle_return_pressed=None):
    table.setRowCount(len(product_rows))
    for row_idx, product in enumerate(product_rows):
        for col_idx, col_name in enumerate([c[0] if isinstance(c, (tuple, list)) else c for c in PRODUCT_COLUMNS]):
            item = QTableWidgetItem()
            value = str(product.get(col_name, ""))
            item.setText(value)
            table.setItem(row_idx, col_idx, item)
    if add_new_row_func:
        add_new_row_func(table, handle_activated, handle_return_pressed, products)

def remove_product(table, product_rows, update_totals_func):
    selected_rows = sorted(set(index.row() for index in table.selectedIndexes() if index.row() < table.rowCount() - 1), reverse=True)  # Skip last row
    for row in selected_rows:
        table.removeRow(row)
        product_rows.pop(row)
    update_totals_func(product_rows)

def update_totals(product_rows, total_amount, amount_in_words):
    total = 0.0
    for product in product_rows:
        amount = float(product.get("Amount", 0))
        total += amount
    total_amount.setText(f"{total:.2f}")
    amount_in_words.setText(number_to_words(total))

def save_voucher(self, mandatory_fields, sequence_func, stock_check=False, stock_update=False, product_columns=PRODUCT_COLUMNS, pre_save_check=None, stock_update_direction=-1, stock_update_key="Qty"):
    logger.debug(f"Starting save_voucher for {self.voucher_type_name} with product_rows: {self.product_rows}")
    if pre_save_check:
        for product in self.product_rows:
            logger.debug(f"Checking product: {product}")
            if not pre_save_check(product):
                logger.error(f"Pre-save check failed for product: {product}")
                return

    # Check mandatory fields
    for field in mandatory_fields:
        if field in self.entries:
            entry = self.entries[field]
            if isinstance(entry, QLineEdit):
                value = entry.text()
            elif isinstance(entry, QComboBox):
                value = entry.currentText()
            elif isinstance(entry, QDateEdit):
                if entry.date().isValid():
                    value = entry.date().toString("yyyy-MM-dd")
                else:
                    value = ""
            else:
                value = ""
            if not value or value.startswith("Add "):
                logger.error(f"Mandatory field '{field}' is missing or invalid: {value}")
                QMessageBox.critical(self, "Error", f"Mandatory field '{field}' is missing or invalid")
                return

    # Optional stock check before saving
    if stock_check:
        for product in self.product_rows:
            if "product_id" in product:
                stock = get_product_stock(product["product_id"]) or 0
                qty = float(product.get(stock_update_key, 0))
                if stock < qty:
                    logger.error(f"Insufficient stock for product {product.get('Name', 'unknown')}: {stock} < {qty}")
                    QMessageBox.critical(self, "Error", f"Insufficient stock for product {product.get('Name', 'unknown')}")
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

    if not self.product_rows:
        logger.error(f"No products provided for {self.voucher_type_name}")
        QMessageBox.critical(self, "Error", "At least one product is required for " + self.voucher_type_name)
        return

    # Calculate total_amount
    total_amount = sum(float(p.get("Amount", 0)) for p in self.product_rows)

    session = Session()
    try:
        voucher_id = self.voucher_data.get("id")
        if voucher_id:
            existing_voucher_number = session.execute(text("SELECT voucher_number FROM voucher_instances WHERE id = :voucher_id"), {"voucher_id": voucher_id}).fetchone()[0]
            voucher_data["Voucher Number"] = existing_voucher_number
            session.execute(text("""
                UPDATE voucher_instances
                SET voucher_type_id = :voucher_type_id, module_name = :module_name, date = :date, data = :data, total_amount = :total_amount
                WHERE id = :voucher_id
            """), {"voucher_type_id": self.voucher_type_id, "module_name": self.module_name, "date": voucher_data["Voucher Date"], "data": json.dumps(voucher_data), "total_amount": total_amount, "voucher_id": voucher_id})
            session.execute(text("DELETE FROM voucher_items WHERE voucher_id = :voucher_id"), {"voucher_id": voucher_id})
            action = "UPDATE"
        else:
            result = session.execute(text("""
                INSERT INTO voucher_instances (voucher_type_id, module_name, voucher_number, date, data, total_amount, created_at)
                VALUES (:voucher_type_id, :module_name, :voucher_number, :date, :data, :total_amount, :created_at)
                RETURNING id
            """), {"voucher_type_id": self.voucher_type_id, "module_name": self.module_name, "voucher_number": voucher_data["Voucher Number"], "date": voucher_data["Voucher Date"], "data": json.dumps(voucher_data), "total_amount": total_amount, "created_at": datetime.now()})
            voucher_id = result.fetchone()[0]
            action = "INSERT"

        column_mapping = {
            "Name": "name",
            "HSN Code": "hsn_code",
            "Qty": "qty",
            "Unit": "unit",
            "Unit Price": "unit_price",
            "GST Rate": "gst_rate",
            "Amount": "amount",
            "Ordered Qty": "ordered_qty",
            "Received Qty": "received_qty",
            "Accepted Qty": "accepted_qty",
            "Rejected Qty": "rejected_qty",
            "Remarks": "remarks"
        }
        product_column_names = [c[0] if isinstance(c, (tuple, list)) else c for c in product_columns]
        mapped_columns_str = ', '.join(column_mapping.get(col, col) for col in product_column_names)

        is_grn = self.voucher_type_name == "GRN (Goods Received Note)"
        if is_grn:
            extra_columns = ["qty", "unit", "unit_price", "gst_rate", "amount"]
            mapped_columns_str += ', ' + ', '.join(extra_columns)

        for product in self.product_rows:
            logger.debug(f"Saving product row: {product}")
            product_values = {column_mapping.get(col, col): product.get(col, "") for col in product_column_names}
            if is_grn:
                accepted_qty = float(product.get("Accepted Qty", 0))
                unit = product.get("Unit", "")
                unit_price = float(product.get("Unit Price", 0))
                gst_rate = float(product.get("GST Rate", 0))
                amount = accepted_qty * unit_price * (1 + gst_rate / 100)
                product_values.update({
                    "qty": accepted_qty,
                    "unit": unit,
                    "unit_price": unit_price,
                    "gst_rate": gst_rate,
                    "amount": amount
                })
            insert_sql = f"""
                INSERT INTO voucher_items (voucher_id, {mapped_columns_str})
                VALUES(:voucher_id, {', '.join(':' + column_mapping.get(col, col) for col in product_column_names)}{', :qty, :unit, :unit_price, :gst_rate, :amount' if is_grn else ''})
            """
            product_values["voucher_id"] = voucher_id
            session.execute(text(insert_sql), product_values)

        # Optional stock update
        if stock_update:
            for product in self.product_rows:
                if "product_id" in product:
                    quantity = float(product.get(stock_update_key, 0))
                    session.execute(text("UPDATE stock SET quantity = quantity + :quantity * :direction WHERE product_id = :product_id"), {"quantity": quantity, "direction": stock_update_direction, "product_id": product["product_id"]})

        session.execute(text("""
            INSERT INTO audit_log (table_name, record_id, action, username, timestamp)
            VALUES (:table_name, :record_id, :action, :username, :timestamp)
        """), {"table_name": "voucher_instances", "record_id": voucher_id, "action": action, "username": self.app.current_user["username"] if self.app.current_user else "system_user", "timestamp": datetime.now().strftime("%Y-%m-%d %H:%M:%S")})

        sequence_func(voucher_data["Voucher Number"])

        session.commit()

        QMessageBox.information(self, "Success", self.voucher_type_name + " saved successfully")
        if self.voucher_management:
            self.voucher_management.refresh_voucher_content(self.voucher_type_name)
            self.voucher_management.refresh_view()
        if hasattr(self, 'save_callback') and self.save_callback:
            self.save_callback()
        self.close()
    except Exception as e:
        session.rollback()
        logger.error(f"Failed to save {self.voucher_type_name}: {e}")
        QMessageBox.critical(self, "Error", f"Database error: {e}")
    finally:
        session.close()