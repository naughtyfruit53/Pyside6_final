# src/erp/voucher/voucher_operations.py

import logging
import json
import os
from datetime import date, datetime
from PySide6.QtWidgets import QMessageBox, QDialog, QVBoxLayout, QHBoxLayout, QLabel, QLineEdit, QComboBox, QPushButton, QTableWidgetItem
from PySide6.QtGui import QDoubleValidator, QFontMetrics
from PySide6.QtCore import Qt
from sqlalchemy import text
from src.erp.logic.database.session import engine, Session
from src.core.config import get_database_url, get_log_path
from src.erp.logic.database.voucher import get_voucher_columns, get_voucher_types, get_voucher_type_id
from src.erp.logic.utils.voucher_utils import get_products, get_payment_terms, get_product_stock, get_customers, get_vendors
from src.erp.logic.utils.utils import add_unit, create_module_directory
from src.templates.document_templates_logic import generate_delivery_challan_template
from src.erp.logic.pdf_generator_logic import PDFGeneratorLogic
from src.erp.logic.utils.sequence_utils import (
    get_next_sales_inv_sequence, increment_sales_inv_sequence,
    get_next_purchase_inv_sequence, increment_purchase_inv_sequence,
    get_next_proforma_sequence, increment_proforma_sequence,
    get_next_delivery_challan_sequence, increment_delivery_challan_sequence,
    get_next_quote_sequence, increment_quote_sequence,
    get_next_purchase_order_sequence, increment_purchase_order_sequence,
    get_next_sales_order_sequence, increment_sales_order_sequence,
    get_next_internal_return_sequence, increment_internal_return_sequence
)
from src.erp.voucher.voucher_form import open_voucher_form
from src.erp.logic.products_logic import add_product
from src.erp.logic.utils.utils import add_unit, create_module_directory

logging.basicConfig(filename=get_log_path(), level=logging.DEBUG, format='%(asctime)s - %(name)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

def save_voucher(parent, voucher_type_id, form_entries, module_name):
    logger.debug(f"Saving voucher: type_id={voucher_type_id}, module_name={module_name}")
    sequence_functions = {
        "Sales Voucher": (get_next_sales_inv_sequence, increment_sales_inv_sequence),
        "Purchase Voucher": (get_next_purchase_inv_sequence, increment_purchase_inv_sequence),
        "Proforma Invoice": (get_next_proforma_sequence, increment_proforma_sequence),
        "Delivery Challan": (get_next_delivery_challan_sequence, increment_delivery_challan_sequence),
        "Quotation": (get_next_quote_sequence, increment_quote_sequence),
        "Purchase Order": (get_next_purchase_order_sequence, increment_purchase_order_sequence),
        "Sales Order": (get_next_sales_order_sequence, increment_sales_order_sequence),
        "Internal Return": (get_next_internal_return_sequence, increment_internal_return_sequence)
    }
    session = Session()
    try:
        voucher_type_name = next((vt[1] for vt in get_voucher_types() if vt[0] == voucher_type_id), "Unknown")
        sequence_func, increment_func = sequence_functions.get(voucher_type_name, (lambda: None, lambda x: None))

        data = {}
        for key, entry in form_entries.items():
            if isinstance(entry, QLineEdit):
                data[key] = entry.text()
            elif isinstance(entry, QComboBox):
                data[key] = entry.currentText()
            elif isinstance(entry, QDateEdit):
                data[key] = entry.date().toString("yyyy-MM-dd")
            elif isinstance(entry, QCheckBox):
                data[key] = "Yes" if entry.isChecked() else "No"

        mandatory_fields = [col[0] for col in get_voucher_columns(voucher_type_id) if col[2]]
        mandatory_fields.extend(["Voucher Number", "Voucher Date", "Party Name"])
        if not all(data.get(field) for field in mandatory_fields) or any(v in ["No customers available", "No vendors available"] for v in data.values()):
            QMessageBox.critical(parent, "Error", "All mandatory fields are required")
            return False

        is_sales_voucher = voucher_type_name in ["Sales Voucher", "Proforma Invoice", "Quotation", "Sales Order", "Delivery Challan", "Internal Return"]
        entity_key = "Customer" if is_sales_voucher else "Vendor"
        table = "customers" if is_sales_voucher else "vendors"
        result = session.execute(text(f"SELECT id FROM {table} WHERE name = :name"), {"name": data.get(entity_key, "")}).fetchone()
        if not result:
            logger.error(f"{table[:-1].capitalize()} not found: {data.get(entity_key)}")
            QMessageBox.critical(parent, "Error", f"Selected {table[:-1]} not found")
            return False
        entity_id = result[0]

        payment_term = data.get("Payment Terms", "").strip()
        if payment_term:
            session.execute(text("INSERT OR IGNORE INTO payment_terms (term) VALUES (:term)"), {"term": payment_term})

        data["items"] = parent.item_entries
        result = session.execute(text("SELECT state FROM company_details WHERE id = 1")).fetchone()
        company_state = result[0]
        result = session.execute(text(f"SELECT state FROM {table} WHERE id = :entity_id"), {"entity_id": entity_id}).fetchone()
        entity_state = result[0]
        is_same_state = (company_state == entity_state)
        subtotal = sum(item["quantity"] * item["unit_price"] for item in parent.item_entries)
        cgst = sum(item["quantity"] * item["unit_price"] * (item["gst_rate"] / 200) for item in parent.item_entries) if is_same_state else 0
        sgst = cgst
        igst = sum(item["quantity"] * item["unit_price"] * (item["gst_rate"] / 100) for item in parent.item_entries) if not is_same_state else 0
        total_amount = subtotal + cgst + sgst + igst

        voucher_number = data.get("Voucher Number", sequence_func())
        data_json = json.dumps(data)
        result = session.execute(text("SELECT id FROM voucher_instances WHERE voucher_number = :voucher_number"), {"voucher_number": voucher_number}).fetchone()
        if result:
            voucher_id = result[0]
            session.execute(text("UPDATE voucher_instances SET voucher_type_id = :voucher_type_id, voucher_number = :voucher_number, date = :date, data = :data, total_amount = :total_amount, cgst_amount = :cgst, sgst_amount = :sgst, igst_amount = :igst WHERE id = :voucher_id"),
                            {"voucher_type_id": voucher_type_id, "voucher_number": voucher_number, "date": data.get("Voucher Date", date.today().strftime("%d-%m-%Y")), "data": data_json, "total_amount": total_amount, "cgst": cgst, "sgst": sgst, "igst": igst, "voucher_id": voucher_id})
            session.execute(text("DELETE FROM voucher_items WHERE voucher_id = :voucher_id"), {"voucher_id": voucher_id})
            action = "UPDATE"
        else:
            insert_stmt = text("INSERT INTO voucher_instances (voucher_type_id, voucher_number, date, data, module_name, record_id, total_amount, cgst_amount, sgst_amount, igst_amount) "
                          "VALUES (:voucher_type_id, :voucher_number, :date, :data, :module_name, :record_id, :total_amount, :cgst, :sgst, :igst) RETURNING id")
            result = session.execute(insert_stmt,
                          {"voucher_type_id": voucher_type_id, "voucher_number": voucher_number, "date": data.get("Voucher Date", date.today().strftime("%d-%m-%Y")), "data": data_json, "module_name": module_name, "record_id": 0, "total_amount": total_amount, "cgst": cgst, "sgst": sgst, "igst": igst})
            voucher_id = result.fetchone()[0]
            action = "INSERT"

        for item in parent.item_entries:
            session.execute(text("""
                INSERT INTO voucher_items (voucher_id, product_id, quantity, unit_price, gst_rate, amount)
                VALUES (:voucher_id, :product_id, :quantity, :unit_price, :gst_rate, :amount)
            """), {"voucher_id": voucher_id, "product_id": item["product_id"], "quantity": item["quantity"], "unit_price": item["unit_price"], "gst_rate": item["gst_rate"], "amount": item["amount"]})

        session.execute(text("""
            INSERT INTO audit_log (table_name, record_id, action, username, timestamp)
            VALUES (:table_name, :record_id, :action, :username, :timestamp)
        """), {"table_name": "voucher_instances", "record_id": voucher_id, "action": action, "username": parent.app.current_user["username"] if parent.app.current_user else "system_user", "timestamp": datetime.now().strftime("%Y-%m-%d %H:%M:%S")})

        increment_func(voucher_number)

        session.commit()

        return True
    except Exception as e:
        session.rollback()
        logger.error(f"Failed to save voucher: {e}")
        QMessageBox.critical(parent, "Error", f"Database error: {e}")
        return False
    finally:
        session.close()

def validate_integer(self, value):
    if value == "":
        return True
    try:
        int(value)
        return True
    except ValueError:
        return False

def validate_float(self, value):
    if value == "":
        return True
    try:
        float(value)
        return True
    except ValueError:
        return False

def handle_product_selection(self, voucher_type_id, product_var, products, font, col_widths, update_product_frame_position):
    if not product_var or product_var == "No products available":
        logger.warning("No product selected or no products available")
        return
    selected_product = next((p for p in products if p[1].lower() == product_var.lower()), None)
    if selected_product:
        add_item(self, voucher_type_id, product_var, products, font, col_widths, update_product_frame_position)
    else:
        logger.error(f"Product not found: {product_var}")
        QMessageBox.critical(self.app, "Error", f"Product '{product_var}' not found")

def add_product_callback(voucher_form, product_combo, product_var, voucher_type_id, products, font, col_widths, update_product_frame_position, callback=None):
    add_product_and_open_popup(voucher_form, product_combo, product_var, voucher_type_id, products, font, col_widths, update_product_frame_position, callback)

def add_product_and_open_popup(self, product_combo, product_var, voucher_type_id, products, font, col_widths, update_product_frame_position, callback=None):
    def product_added_callback(product_id, product_name):
        products[:] = get_products()
        product_combo.clear()
        product_combo.addItems([p[1] for p in products] or ["No products available"])
        product_combo.setCurrentText(product_name)
        logger.debug(f"Product combobox updated, selected: {product_name}")
        from src.erp.voucher.voucher_operations import handle_product_selection
        handle_product_selection(self, voucher_type_id, product_var, products, font, col_widths, update_product_frame_position)
        if callback:
            callback(self.item_table)
    for child_window in self.app.children():
        if isinstance(child_window, QDialog) and child_window.windowTitle() == "Add Product":
            child_window.raise_()
            return
    add_product(self.app, callback=product_added_callback)
    self.app.add_window_open = False  # Reset flag after dialog closes

def add_item(self, voucher_type_id, product_var, products, font, col_widths, update_product_frame_position):
    if not product_var or product_var == "No products available":
        return
    selected_product = next((p for p in products if p[1].lower() == product_var.lower()), None)
    if not selected_product:
        return
    if self.app.add_window_open:
        if self.app.add_window:
            self.app.add_window.raise_()
        return
    add_win = QDialog(self.app)
    add_win.setWindowTitle("Add Item to Voucher")
    add_win.setFixedSize(400, 300)
    add_win.setModal(True)
    layout = QVBoxLayout(add_win)

    product_id, name, hsn, unit, unit_price, gst = selected_product

    stock_var = str(get_product_stock(product_id) or "Error")
    stock_label = QLabel(f"Current Stock: {stock_var}")
    stock_label.setStyleSheet(f"color: {'green' if stock_var.isdigit() and int(stock_var) > 0 else 'red'}")
    layout.addWidget(stock_label)

    layout.addWidget(QLabel("Quantity*"))
    qty_edit = QLineEdit("1")
    qty_edit.setValidator(QDoubleValidator(0.0, 1000000.0, 2))
    layout.addWidget(qty_edit)

    layout.addWidget(QLabel("Unit Price*"))
    price_edit = QLineEdit(str(unit_price))
    price_edit.setValidator(QDoubleValidator(0.0, 1000000.0, 2))
    layout.addWidget(price_edit)

    layout.addWidget(QLabel("Unit*"))
    unit_combo = QComboBox()
    unit_values = UNITS or ["Piece", "Kg", "Unit"]
    unit_combo.addItems(unit_values)
    unit_combo.setCurrentText(unit)
    layout.addWidget(unit_combo)

    def save_item():
        try:
            qty = float(qty_edit.text())
            new_price = float(price_edit.text())
            new_unit = unit_combo.currentText()
            if qty <= 0 or new_price <= 0 or not new_unit:
                raise ValueError("Quantity, price, and unit must be valid")
            add_unit(new_unit)
            if abs(new_price - unit_price) > 0.01:
                if QMessageBox.question(self.app, "Update Price", "Do you want to update the product price in the database?") == QMessageBox.Yes:
                    session = Session()
                    try:
                        session.execute(text("UPDATE products SET unit_price = :new_price WHERE id = :product_id"), {"new_price": new_price, "product_id": product_id})
                        session.execute(text("INSERT INTO audit_log (table_name, record_id, action, \"user\", timestamp) VALUES (:table_name, :record_id, :action, :username, :timestamp)"),
                                        {"table_name": "products", "record_id": product_id, "action": "UPDATE", "username": "system_user", "timestamp": date.today().strftime("%Y-%m-%Y")})
                        session.commit()
                    except Exception as e:
                        session.rollback()
                        logger.error(f"Failed to update product price: {e}")
                    finally:
                        session.close()
            amount = qty * new_price * (1 + gst / 100)
            item = {
                "product_id": product_id,
                "product_name": name,
                "hsn_code": hsn,
                "quantity": qty,
                "unit": new_unit,
                "unit_price": new_price,
                "gst_rate": gst,
                "amount": amount
            }
            self.item_entries.append(item)
            row_count = self.item_table.rowCount()
            self.item_table.insertRow(row_count - 1)
            for col, val in enumerate((name, hsn, qty, new_unit, new_price, gst, amount)):
                item_widget = QTableWidgetItem(str(val))
                item_widget.setTextAlignment(Qt.AlignCenter)
                self.item_table.setItem(row_count - 1, col, item_widget)
            for col, val in enumerate((name, hsn, qty, new_unit, new_price, gst, amount)):
                width = QFontMetrics(font).horizontalAdvance(str(val)) + 20
                col_widths[col] = max(col_widths.get(col, 100), width)
                self.item_table.setColumnWidth(col, col_widths[col])
            update_product_frame_position(self.item_table)
            add_win.accept()
        except (ValueError, Exception) as e:
            logger.error(f"Error saving item: {e}")
            QMessageBox.critical(add_win, "Error", f"Invalid input: {e}")

    button_layout = QHBoxLayout()
    save_button = QPushButton("Save")
    save_button.clicked.connect(save_item)
    cancel_button = QPushButton("Cancel")
    cancel_button.clicked.connect(add_win.reject)
    button_layout.addWidget(save_button)
    button_layout.addWidget(cancel_button)
    layout.addLayout(button_layout)

    add_win.exec()

def edit_item(self, products, font, col_widths, update_product_frame_position):
    selected_row = self.item_table.currentRow()
    if selected_row < 0 or selected_row == self.item_table.rowCount() - 1:
        return
    values = [self.item_table.item(selected_row, col).text() for col in range(self.item_table.columnCount())]
    product_id = next((p[0] for p in products if p[1].lower() == values[0].lower()), None)
    if not product_id:
        QMessageBox.critical(self.app, "Error", "Product not found")
        return
    selected_product = next((p for p in products if p[0] == product_id), None)
    if not selected_product:
        QMessageBox.critical(self.app, "Error", "Invalid product")
        return
    if self.app.add_window_open:
        if self.app.add_window:
            self.app.add_window.raise_()
        return
    edit_win = QDialog(self.app)
    edit_win.setWindowTitle("Edit Item in Voucher")
    edit_win.setFixedSize(400, 300)
    edit_win.setModal(True)
    layout = QVBoxLayout(edit_win)

    product_id, name, hsn, unit, unit_price, gst = selected_product

    stock_var = str(get_product_stock(product_id) or "Error")
    stock_label = QLabel(f"Current Stock: {stock_var}")
    stock_label.setStyleSheet(f"color: {'green' if stock_var.isdigit() and int(stock_var) > 0 else 'red'}")
    layout.addWidget(stock_label)

    layout.addWidget(QLabel("Quantity*"))
    qty_edit = QLineEdit(str(values[2]))
    qty_edit.setValidator(QDoubleValidator(0.0, 1000000.0, 2))
    layout.addWidget(qty_edit)

    layout.addWidget(QLabel("Unit Price*"))
    price_edit = QLineEdit(str(values[4]))
    price_edit.setValidator(QDoubleValidator(0.0, 1000000.0, 2))
    layout.addWidget(price_edit)

    layout.addWidget(QLabel("Unit*"))
    unit_combo = QComboBox()
    unit_values = UNITS or ["Piece", "Kg", "Unit"]
    unit_combo.addItems(unit_values)
    unit_combo.setCurrentText(values[3])
    layout.addWidget(unit_combo)

    def save_edited_item():
        try:
            qty = float(qty_edit.text())
            new_price = float(price_edit.text())
            new_unit = unit_combo.currentText()
            if qty <= 0 or new_price <= 0 or not new_unit:
                raise ValueError("Quantity, price, and unit must be valid")
            add_unit(new_unit)
            if abs(new_price - selected_product[4]) > 0.01:
                if QMessageBox.question(self.app, "Update Price", "Do you want to update the product price in the database?") == QMessageBox.Yes:
                    session = Session()
                    try:
                        session.execute(text("UPDATE products SET unit_price = :new_price WHERE id = :product_id"), {"new_price": new_price, "product_id": product_id})
                        session.execute(text("INSERT INTO audit_log (table_name, record_id, action, \"user\", timestamp) VALUES (:table_name, :record_id, :action, :username, :timestamp)"),
                                        {"table_name": "products", "record_id": product_id, "action": "UPDATE", "username": "system_user", "timestamp": date.today().strftime("%Y-%m-%Y")})
                        session.commit()
                    except Exception as e:
                        session.rollback()
                        logger.error(f"Failed to update product price: {e}")
                    finally:
                        session.close()
            amount = qty * new_price * (1 + float(values[5]) / 100)
            new_values = (values[0], values[1], qty, new_unit, new_price, values[5], amount)
            for col, val in enumerate(new_values):
                item = QTableWidgetItem(str(val))
                item.setTextAlignment(Qt.AlignCenter)
                self.item_table.setItem(selected_row, col, item)
            for item in self.item_entries:
                if item["product_name"] == values[0] and item["unit"] == values[3]:
                    item.update({"quantity": qty, "unit": new_unit, "unit_price": new_price, "amount": amount})
                    break
            for col, val in enumerate(new_values):
                width = QFontMetrics(font).horizontalAdvance(str(val)) + 20
                col_widths[col] = max(col_widths.get(col, 100), width)
                self.item_table.setColumnWidth(col, col_widths[col])
            update_product_frame_position(self.item_table)
            edit_win.accept()
        except (ValueError, Exception) as e:
            logger.error(f"Error saving edited item: {e}")
            QMessageBox.critical(edit_win, "Error", f"Invalid input: {e}")

    button_layout = QHBoxLayout()
    save_button = QPushButton("Save")
    save_button.clicked.connect(save_edited_item)
    cancel_button = QPushButton("Cancel")
    cancel_button.clicked.connect(edit_win.reject)
    button_layout.addWidget(save_button)
    button_layout.addWidget(cancel_button)
    layout.addLayout(button_layout)

    edit_win.exec()

def delete_item(self, font, col_widths, update_product_frame_position):
    selected_row = self.item_table.currentRow()
    if selected_row < 0 or selected_row == self.item_table.rowCount() - 1:
        return
    if QMessageBox.question(self.app, "Confirm Delete", "Delete this item from the voucher?") == QMessageBox.Yes:
        values = [self.item_table.item(selected_row, col).text() for col in range(self.item_table.columnCount())]
        self.item_entries = [item for item in self.item_entries if not (item["product_name"] == values[0] and item["unit"] == values[3])]
        self.item_table.removeRow(selected_row)
        update_product_frame_position(self.item_table)
        from src.core.utils.voucher_utils import PRODUCT_COLUMNS
        for col in range(len(PRODUCT_COLUMNS)):
            max_width = QFontMetrics(font).horizontalAdvance(PRODUCT_COLUMNS[col][0]) + 20
            for row in range(self.item_table.rowCount()):
                if row == self.item_table.rowCount() - 1:
                    continue
                val = self.item_table.item(row, col).text()
                width = QFontMetrics(font).horizontalAdvance(str(val)) + 20
                max_width = max(max_width, width)
            col_widths[col] = max_width
            self.item_table.setColumnWidth(col, col_widths[col])

def save_voucher_pdf(app, voucher_id, voucher_type_id, voucher_type_name):
    session = Session()
    try:
        result = session.execute(text("SELECT voucher_number, data, date FROM voucher_instances WHERE id = :voucher_id"), {"voucher_id": voucher_id}).fetchone()
        if not result:
            logger.error(f"Voucher not found: id={voucher_id}")
            QMessageBox.critical(app, "Error", f"Voucher not found")
            return
        voucher_number, data_json, voucher_date = result
        data = json.loads(data_json) if data_json else {}
        items = data.get("items", [])
        entity_name = data.get("Customer", data.get("Vendor", ""))
        is_sales_voucher = voucher_type_name in ["Sales Voucher", "Proforma Invoice", "Quotation", "Sales Order", "Delivery Challan", "Internal Return"]
        table = "customers" if is_sales_voucher else "vendors"
        result = session.execute(text(f"SELECT id, address1, address2, city, state, pin, gst_no, contact_no FROM {table} WHERE name = :entity_name"), {"entity_name": entity_name}).fetchone()
        if not result:
            logger.error(f"{table[:-1].capitalize()} not found: {entity_name}")
            QMessageBox.critical(app, "Error", f"Selected {table[:-1]} not found")
            return
        entity_id, address1, address2, city, state, pin, gst_no, contact_no = result
        result = session.execute(text("SELECT name, address, address_2, city, state, pin_code, gst_no, contact_no, email, logo_path FROM company_details WHERE id = 1")).fetchone()
        company_name, company_address, company_address_2, company_city, company_state, company_pin, company_gst, company_contact, company_email, company_logo = result if result else ("Your Company", "Your Address", "", "City", "State", "Pin", "GST", "Contact", "Email", None)
        is_same_state = (company_state == state)
        subtotal = sum(item["quantity"] * item["unit_price"] for item in items)
        cgst = sum(item["quantity"] * item["unit_price"] * (item["gst_rate"] / 200) for item in items) if is_same_state else 0
        sgst = cgst
        igst = sum(item["quantity"] * item["unit_price"] * (item["gst_rate"] / 100) for item in items) if not is_same_state else 0
        total_amount = subtotal + cgst + sgst + igst
        module_dir = create_module_directory(voucher_type_name.replace(" ", "_"))
        if not module_dir:
            QMessageBox.critical(app, "Error", "Default directory not set")
            return
        voucher_number_clean = voucher_number.replace("/", "_")
        file_path = os.path.join(module_dir, f"{voucher_type_name.replace(' ', '_')}_{voucher_number_clean}.pdf")
        if voucher_type_name == "Delivery Challan":
            company_data = [company_name, company_address, company_address_2, company_city, company_state, company_pin, company_gst, company_contact, company_email, company_logo]
            customer_data = [entity_name, address1, address2, city, state, pin, gst_no, contact_no]
            items_for_pdf = [
                {"s_no": idx + 1, "description": item["product_name"], "hsn_code": item["hsn_code"], "quantity": item["quantity"], "unit": item["unit"], "rate": item["unit_price"], "gst_rate": item["gst_rate"], "amount": item["amount"]}
                for idx, item in enumerate(items)
            ]
            doc = generate_delivery_challan_template(
                file_path=file_path,
                company_data=company_data,
                customer_data=customer_data,
                voucher_number=voucher_number,
                voucher_date=voucher_date,
                delivery_date=data.get("Delivery Date", None),
                challan_number=voucher_number,  # Assuming voucher_number is used as challan_number
                items=items_for_pdf,
                total_amount=total_amount,
                cgst=cgst,
                sgst=sgst,
                igst=igst
            )
            doc.build(doc.elements)  # Build the PDF
            success = True
        else:
            success = PDFGeneratorLogic.generate_voucher_pdf(
                voucher_type=voucher_type_name,
                file_path=file_path,
                voucher_id=voucher_id,
                voucher_number=voucher_number,
                entity_id=entity_id,
                voucher_date=voucher_date,
                items=items,
                total_amount=total_amount,
                cgst=cgst,
                sgst=sgst,
                igst=igst,
                module_name=self.current_voucher_category,
                voucher_type_id=voucher_type_id,
                payment_terms=data.get("Payment Terms", "Net 30"),
                delivery_date=data.get("Delivery Date", None)
            )
        if success:
            QMessageBox.information(app, "Success", f"{voucher_type_name} PDF saved at {file_path}")
        else:
            QMessageBox.critical(app, "Error", "Failed to generate PDF")
    except Exception as e:
        logger.error(f"Failed to save voucher PDF: {e}")
        QMessageBox.critical(app, "Error", f"Failed to save PDF: {e}")
    finally:
        session.close()

def edit_voucher(parent, voucher_id):
    session = Session()
    try:
        result = session.execute(text("SELECT voucher_type_id, voucher_number, date, data, module_name FROM voucher_instances WHERE id = :voucher_id"), {"voucher_id": voucher_id}).fetchone()
        if result:
            voucher_type_id, voucher_number, date, data_json, module_name = result
            data = json.loads(data_json) if data_json else {}
            voucher_data = {
                "id": voucher_id,
                "voucher_number": voucher_number,
                "date": date,
                "data": data,
                "items": data.get("items", []),
                "delivery_date": data.get("Delivery Date", ""),
                "payment_terms": data.get("Payment Terms", ""),
                "entity_name": data.get("Customer", data.get("Vendor", ""))
            }
            voucher_type_name = next((vt[1] for vt in get_voucher_types() if vt[0] == voucher_type_id), "Unknown")
            parent.app.show_frame(module_name)
            parent.display_voucher_form(
                parent, voucher_type_id, module_name, voucher_type_name, voucher_data,
                save_callback=save_voucher,
                entities=get_customers() if "sales" in voucher_type_name.lower() else get_vendors(),
                products=get_products(),
                payment_terms=get_payment_terms()
            )
    except Exception as e:
        logger.error(f"Failed to load voucher for editing: {e}")
        QMessageBox.critical(parent, "Error", f"Failed to load voucher: {e}")
    finally:
        session.close()

def delete_voucher(parent, voucher_id):
    session = Session()
    try:
        result = session.execute(text("SELECT voucher_number, voucher_type_id FROM voucher_instances WHERE id = :voucher_id"), {"voucher_id": voucher_id}).fetchone()
        if not result:
            logger.error(f"Voucher not found: id={voucher_id}")
            QMessageBox.critical(parent, "Error", f"Voucher not found")
            return
        voucher_number, voucher_type_id = result
        voucher_type_name = next((vt[1] for vt in get_voucher_types() if vt[0] == voucher_type_id), "Unknown")
        if QMessageBox.question(parent, "Confirm Delete", f"Delete voucher {voucher_number}?") != QMessageBox.Yes:
            return
        session.execute(text("DELETE FROM voucher_items WHERE voucher_id = :voucher_id"), {"voucher_id": voucher_id})
        session.execute(text("DELETE FROM voucher_instances WHERE id = :voucher_id"), {"voucher_id": voucher_id})
        session.execute(text("INSERT INTO audit_log (table_name, record_id, action, username, timestamp) VALUES (:table_name, :record_id, :action, :username, :timestamp)"),
                        {"table_name": "voucher_instances", "record_id": voucher_id, "action": "DELETE", "username": parent.app.current_user["username"] if parent.app.current_user else "system_user", "timestamp": datetime.now().strftime("%Y-%m-%d %H:%M:%S")})
        session.commit()
        parent.voucher_management.create_voucher_table(parent.voucher_management.view_widget, voucher_type_name)
        QMessageBox.information(parent, "Success", f"Voucher {voucher_number} deleted successfully")
    except Exception as e:
        session.rollback()
        logger.error(f"Failed to delete voucher: {e}")
        QMessageBox.critical(parent, "Error", f"Failed to delete voucher: {e}")
    finally:
        session.close()

# Added function: get_eligible_pos (fetches all Purchase Order voucher numbers and their items for simplicity)
def get_eligible_pos():
    session = Session()
    try:
        po_type_id = next((vt[0] for vt in get_voucher_types() if vt[1] == "Purchase Order"), None)
        grn_type_id = next((vt[0] for vt in get_voucher_types() if vt[1] == "GRN (Goods Received Note)"), None)
        if not po_type_id or not grn_type_id:
            logger.warning("Purchase Order or GRN voucher type not found")
            return [], {}
        result = session.execute(text("""
            SELECT po.voucher_number, po.data
            FROM voucher_instances po
            LEFT JOIN voucher_instances grn ON grn.voucher_type_id = :grn_type_id AND (grn.data::json ->> 'PO Number') = po.voucher_number
            WHERE po.voucher_type_id = :po_type_id AND grn.id IS NULL
            ORDER BY po.created_at DESC
        """), {"po_type_id": po_type_id, "grn_type_id": grn_type_id}).fetchall()
        eligible_pos = [num for num, _ in result]
        details = {num: json.loads(data_json).get("items", []) for num, data_json in result}
        return eligible_pos, details
    except Exception as e:
        logger.error(f"Failed to get eligible POs: {e}")
        return [], {}
    finally:
        session.close()