# src/erp/voucher/forms/purchase_order_form.py

from src.erp.logic.utils.forms_utils import *
from src.erp.logic.utils.sequence_utils import get_next_purchase_order_sequence, increment_purchase_order_sequence

from sqlalchemy import text
from src.erp.logic.database.session import Session
from src.erp.logic.database.models import PurchaseOrder, PoItem, Vendor, CompanyDetail, PaymentTerm
from datetime import datetime
from PySide6.QtWidgets import QMessageBox
from src.erp.logic.database.voucher import get_voucher_type_id
import json

class PurchaseOrderForm(QWidget):
    def __init__(self, parent=None, app=None, module_name=None, voucher_type_id=None, voucher_type_name=None, voucher_data=None, voucher_management=None, voucher_category=None, voucher_name=None, save_callback=None, add_product_callback=None, entities=None, products=None, payment_terms=None):
        super().__init__(parent)
        self.app = app
        self.module_name = module_name
        self.voucher_type_id = voucher_type_id
        self.voucher_type_name = voucher_type_name if voucher_type_name else "Purchase Order"
        self.voucher_management = voucher_management
        self.save_callback = save_callback
        common_init(self, self.voucher_type_name, voucher_data, get_products, get_payment_terms)
        self.entities = get_vendors()
        self.processing_selection = False
        self.setObjectName("PurchaseOrderForm")
        apply_stylesheet(self, "purchase_order_form.qss")
        self.setup_ui()

    def setup_ui(self):
        logger.info(f"Creating Purchase Order form (ID: {self.voucher_type_id})")

        main_layout = QVBoxLayout(self)
        main_layout.setContentsMargins(10, 10, 10, 10)

        scroll = QScrollArea()
        scroll.setWidgetResizable(True)
        content_widget = QWidget()
        scroll.setWidget(content_widget)
        self.content_layout = QVBoxLayout(content_widget)
        self.content_layout.setAlignment(Qt.AlignTop)
        self.content_layout.setSpacing(5)  # Reduce spacing between elements

        # Title
        title_label = create_title_label("Create Purchase Order")
        self.content_layout.addWidget(title_label)

        # Header row: Voucher Number, Date, Required by Date
        header_fields = [
            ("Voucher Number*", 'text', "Voucher Number", get_next_purchase_order_sequence() or ''),
            ("Date*", 'date', "Voucher Date", self.voucher_data.get("Voucher Date", QDate.currentDate().toString("yyyy-MM-dd"))),
            ("Required by Date", 'date', "Required by Date", self.voucher_data.get("Required by Date", QDate.currentDate().toString("yyyy-MM-dd")))
        ]
        header_row, header_entries = create_header_row(header_fields)
        self.content_layout.addLayout(header_row)
        self.entries.update(header_entries)

        # Party row
        party_row, self.party_combo, self.payment_combo = create_party_row("Vendor", self.entities, self.payment_terms, self.voucher_data)
        self.content_layout.addLayout(party_row)
        self.party_combo.lineEdit().setAlignment(Qt.AlignLeft | Qt.AlignVCenter)
        self.payment_combo.lineEdit().setAlignment(Qt.AlignLeft | Qt.AlignVCenter)
        self.entries["Party Name"] = self.party_combo
        self.entries["Payment Terms"] = self.payment_combo

        # Set handlers for party combo
        self.party_combo.lineEdit().textChanged.connect(lambda text: handle_text_changed(text, self.party_combo, self.entities))
        self.party_combo.activated.connect(lambda index: self.handle_party_activated(index, self.party_combo, "Vendor"))
        self.party_combo.lineEdit().returnPressed.connect(lambda: self.handle_party_return_pressed(self.party_combo, "Vendor"))

        # Product table
        self.item_table = create_product_table()
        self.content_layout.addWidget(self.item_table)

        # Remove button
        remove_button = create_remove_button(lambda: remove_product(self.item_table, self.product_rows, lambda rows: update_totals(rows, self.total_amount, self.amount_in_words)))
        self.content_layout.addWidget(remove_button)

        # Total and words
        total_layout, words_layout, self.total_amount, self.amount_in_words = create_total_words()
        self.content_layout.addLayout(total_layout)
        self.content_layout.addLayout(words_layout)

        # Bottom layout
        bottom_layout = create_bottom_layout(self.app, self.voucher_type_name, self.save_voucher, lambda: self.app.show_frame("home"))
        self.content_layout.addLayout(bottom_layout)

        main_layout.addWidget(scroll)
        populate_product_table(self.item_table, self.product_rows, add_new_row, self.products, self.handle_activated, self.handle_return_pressed)
        self.update_product_frame_position()

    def handle_party_activated(self, index, combo, party_type):
        old_entities = self.entities[:]
        text = combo.itemText(index)
        if text.startswith("Add "):
            if text == f"Add New {party_type}":
                combo.lineEdit().setText("")
            else:
                suggested = text.split('"')[1]
                combo.lineEdit().setText(suggested)
            if party_type == "Customer":
                add_customer_callback(self, combo, self.voucher_management)
            else:
                add_vendor_callback(self, combo, self.voucher_management)
            new_entities = get_vendors()
            added = [name for name in new_entities if name not in old_entities]
            self.refresh_party_combo(combo, party_type)
            if added:
                combo.setCurrentText(added[0])

    def handle_party_return_pressed(self, combo, party_type):
        text = combo.lineEdit().text().strip()
        if not text:
            return
        index = combo.findText(text, Qt.MatchExactly)
        if index != -1:
            self.handle_party_activated(index, combo, party_type)
        else:
            add_idx = find_add_item(combo)
            if add_idx == -1:
                new_text = f'Add "{text}" as new {party_type.lower()}'
                combo.insertItem(0, new_text)
                add_idx = 0
            self.handle_party_activated(add_idx, combo, party_type)

    def refresh_party_combo(self, combo, party_type):
        combo.clear()
        self.entities = get_vendors()
        party_names = self.entities
        combo.addItems(party_names)
        if not party_names:
            combo.addItem(f"Add New {party_type}")
            combo.setCurrentIndex(0)
        else:
            combo.insertItem(0, f"Add New {party_type}")
            combo.setCurrentIndex(-1)
        completer = QCompleter(combo.model())
        completer.setFilterMode(Qt.MatchContains)
        completer.setCaseSensitivity(Qt.CaseInsensitive)
        completer.setCompletionMode(QCompleter.PopupCompletion)
        combo.setCompleter(completer)

    def handle_activated(self, index, combo, row):
        if self.processing_selection:
            return
        self.processing_selection = True
        try:
            text = combo.itemText(index)
            if text.startswith("Add "):
                if text == "Add New Product":
                    combo.lineEdit().setText("")
                else:
                    suggested = text.split('"')[1]
                    combo.lineEdit().setText(suggested)
                callback_to_use = self.add_product_cb if hasattr(self, 'add_product_cb') else add_product_callback
                callback_to_use(self, combo, self.voucher_management, self.voucher_type_id, self.products, self.app.font(), [100] * 7, self.update_product_frame_position, lambda table: populate_product_table(table, self.product_rows, add_new_row, self.products, self.handle_activated, self.handle_return_pressed))
            elif text:
                open_add_quantity_dialog(text, row, combo, self.products, lambda dialog, pid, n, h, u, gt, qt, pt, r, c, s: save_quantity_dialog(dialog, pid, n, h, u, gt, qt, pt, r, c, s, self.products, self.item_table, self.product_rows, lambda rows: update_totals(rows, self.total_amount, self.amount_in_words), self.app, "Sales" in self.voucher_type_name, self))
        finally:
            self.processing_selection = False

    def handle_return_pressed(self, combo, row):
        if self.processing_selection:
            return
        self.processing_selection = True
        try:
            text = combo.lineEdit().text().strip()
            if not text:
                return
            index = combo.findText(text, Qt.MatchExactly)
            if index != -1:
                self.handle_activated(index, combo, row)
            else:
                add_idx = find_add_item(combo)
                if add_idx == -1:
                    new_text = f'Add "{text}" as new product'
                    combo.insertItem(0, new_text)
                    add_idx = 0
                self.handle_activated(add_idx, combo, row)
        finally:
            self.processing_selection = False

    def resizeEvent(self, event: QResizeEvent):
        super().resizeEvent(event)
        self.update_product_frame_position()

    def update_product_frame_position(self):
        pass

    def save_voucher(self):
        session = Session()
        try:
            # Collect form data
            po_number = self.entries["Voucher Number"].text().strip()
            date_str = self.entries["Voucher Date"].date().toString("yyyy-MM-dd")
            required_by_date_str = self.entries["Required by Date"].date().toString("yyyy-MM-dd")
            vendor_name = self.entries["Party Name"].currentText().strip()
            payment_terms = self.entries["Payment Terms"].currentText().strip()

            # Validate mandatory fields
            if not po_number or not date_str or not vendor_name:
                QMessageBox.critical(self, "Error", "All mandatory fields are required")
                return False
            if not self.product_rows:
                QMessageBox.critical(self, "Error", "At least one product is required")
                return False
            if vendor_name in ["No vendors available"]:
                QMessageBox.critical(self, "Error", "Valid vendor is required")
                return False

            # Get vendor_id
            vendor = session.query(Vendor).filter_by(name=vendor_name).first()
            if not vendor:
                QMessageBox.critical(self, "Error", "Selected vendor not found")
                return False
            vendor_id = vendor.id

            # Add payment term if new and not empty
            payment_terms = payment_terms.strip()
            if payment_terms:
                if not session.query(PaymentTerm).filter_by(term=payment_terms).first():
                    session.add(PaymentTerm(term=payment_terms))
            else:
                payment_terms = None

            # Get states for GST calculation
            company_state = session.query(CompanyDetail.state).filter_by(id=1).first()
            if company_state:
                company_state = company_state[0]
            else:
                QMessageBox.critical(self, "Error", "Company details not found")
                return False
            entity_state = session.query(Vendor.state).filter_by(id=vendor_id).first()[0]
            is_same_state = (company_state == entity_state)

            # Calculate totals and GST
            subtotal = sum(item["Qty"] * item["Unit Price"] for item in self.product_rows)
            cgst = sum(item["Qty"] * item["Unit Price"] * (item["GST Rate"] / 200) for item in self.product_rows) if is_same_state else 0
            sgst = cgst
            igst = sum(item["Qty"] * item["Unit Price"] * (item["GST Rate"] / 100) for item in self.product_rows) if not is_same_state else 0
            total_amount = subtotal + cgst + sgst + igst

            # Parse dates
            po_date = datetime.strptime(date_str, "%Y-%m-%d")
            delivery_date = datetime.strptime(required_by_date_str, "%Y-%m-%d") if required_by_date_str else None

            # Check if update or insert
            po = session.query(PurchaseOrder).filter_by(po_number=po_number).first()
            if po:
                # Update existing PO
                po.vendor_id = vendor_id
                po.po_date = po_date
                po.delivery_date = delivery_date
                po.total_amount = total_amount
                po.cgst_amount = cgst
                po.sgst_amount = sgst
                po.igst_amount = igst
                po.payment_terms = payment_terms
                # Delete existing items
                session.query(PoItem).filter_by(po_id=po.id).delete()
                po_id = po.id
                action = "UPDATE"
            else:
                # Insert new PO
                po = PurchaseOrder(
                    po_number=po_number,
                    vendor_id=vendor_id,
                    po_date=po_date,
                    delivery_date=delivery_date,
                    total_amount=total_amount,
                    cgst_amount=cgst,
                    sgst_amount=sgst,
                    igst_amount=igst,
                    grn_status="Pending",
                    is_deleted=0,
                    payment_terms=payment_terms
                )
                session.add(po)
                session.flush()  # Get po.id
                po_id = po.id
                action = "INSERT"

            # Insert items
            for item in self.product_rows:
                po_item = PoItem(
                    po_id=po_id,
                    product_id=item["product_id"],
                    quantity=item["Qty"],
                    unit=item["Unit"],
                    unit_price=item["Unit Price"],
                    gst_rate=item["GST Rate"],
                    amount=item["Amount"]
                )
                session.add(po_item)

            # Audit log for purchase_orders
            session.execute(text("""
                INSERT INTO audit_log (table_name, record_id, action, username, timestamp)
                VALUES (:table_name, :record_id, :action, :username, :timestamp)
            """), {
                "table_name": "purchase_orders",
                "record_id": po_id,
                "action": action,
                "username": self.app.current_user["username"] if self.app.current_user else "system_user",
                "timestamp": datetime.now().strftime("%Y-%m-%d %H:%M:%S")
            })

            # Sync to voucher_instances for index visibility
            voucher_type_id = get_voucher_type_id(self.voucher_type_name)
            voucher_data_json = json.dumps({
                "Voucher Number": po_number,
                "Voucher Date": date_str,
                "Required by Date": required_by_date_str,
                "Party Name": vendor_name,
                "Payment Terms": payment_terms,
                "items": self.product_rows
            })
            voucher_result = session.execute(text("""
                INSERT INTO voucher_instances (voucher_type_id, voucher_number, created_at, date, data, module_name, record_id, total_amount, cgst_amount, sgst_amount, igst_amount)
                VALUES (:voucher_type_id, :voucher_number, :created_at, :date, :data, :module_name, :record_id, :total_amount, :cgst, :sgst, :igst) RETURNING id
            """), {
                "voucher_type_id": voucher_type_id,
                "voucher_number": po_number,
                "created_at": datetime.now(),
                "date": po_date,
                "data": voucher_data_json,
                "module_name": self.module_name,
                "record_id": po_id,
                "total_amount": total_amount,
                "cgst": cgst,
                "sgst": sgst,
                "igst": igst
            })
            voucher_id = voucher_result.fetchone()[0]

            # Sync items to voucher_items
            for item in self.product_rows:
                session.execute(text("""
                    INSERT INTO voucher_items (voucher_id, name, hsn_code, qty, unit, unit_price, gst_rate, amount)
                    VALUES (:voucher_id, :name, :hsn_code, :qty, :unit, :unit_price, :gst_rate, :amount)
                """), {
                    "voucher_id": voucher_id,
                    "name": item["Name"],
                    "hsn_code": item["HSN Code"],
                    "qty": item["Qty"],
                    "unit": item["Unit"],
                    "unit_price": item["Unit Price"],
                    "gst_rate": item["GST Rate"],
                    "amount": item["Amount"]
                })

            # Audit log for voucher_instances
            session.execute(text("""
                INSERT INTO audit_log (table_name, record_id, action, username, timestamp)
                VALUES (:table_name, :record_id, :action, :username, :timestamp)
            """), {
                "table_name": "voucher_instances",
                "record_id": voucher_id,
                "action": action,
                "username": self.app.current_user["username"] if self.app.current_user else "system_user",
                "timestamp": datetime.now().strftime("%Y-%m-%d %H:%M:%S")
            })

            session.commit()
            if action == "INSERT":
                increment_purchase_order_sequence(po_number)
            QMessageBox.information(self, "Success", "Purchase Order saved successfully")
            if self.voucher_management:
                self.voucher_management.refresh_view()
            if self.save_callback:
                self.save_callback()
            return True
        except Exception as e:
            session.rollback()
            logger.error(f"Failed to save purchase order: {e}")
            QMessageBox.critical(self, "Error", f"Database error: {e}")
            return False
        finally:
            session.close()