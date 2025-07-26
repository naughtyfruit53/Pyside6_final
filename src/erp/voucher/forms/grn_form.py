# Revised script: src/erp/voucher/forms/grn_form.py

from src.erp.logic.utils.forms_utils import *
from src.erp.logic.utils.sequence_utils import get_next_grn_sequence, increment_grn_sequence
from src.erp.logic.database.voucher import get_voucher_type_id
import json

GRN_PRODUCT_COLUMNS = [
    "Name", "HSN Code", "Ordered Qty", "Received Qty", "Accepted Qty", "Rejected Qty", "Remarks"
]

class GRNForm(QWidget):
    def __init__(self, parent=None, app=None, module_name=None, voucher_type_id=None, voucher_type_name=None, voucher_data=None, voucher_management=None, voucher_category=None, voucher_name=None, save_callback=None, add_product_callback=None, entities=None, products=None):
        super().__init__(parent)
        self.app = app
        self.module_name = module_name
        self.voucher_type_id = voucher_type_id
        self.voucher_type_name = voucher_type_name if voucher_type_name else "GRN (Goods Received Note)"
        self.voucher_management = voucher_management
        common_init(self, self.voucher_type_name, voucher_data, get_products, lambda: None)  # No payment_terms for GRN
        self.entities = get_vendors()
        # Ensure product_rows is list of dicts with default values
        self.product_rows = self.voucher_data.get("items", []) if self.voucher_data else []
        if not isinstance(self.product_rows, list):
            logger.warning(f"Invalid product_rows type: {type(self.product_rows)}, resetting to empty list")
            self.product_rows = []
        # Sanitize product_rows
        sanitized_rows = []
        for p in self.product_rows:
            if not isinstance(p, dict):
                logger.warning(f"Invalid product row type {type(p)} in GRN edit, skipping")
                continue
            product = {}
            for key, value in p.items():
                new_key = {
                    "name": "Name",
                    "hsn_code": "HSN Code",
                    "ordered_qty": "Ordered Qty",
                    "received_qty": "Received Qty",
                    "accepted_qty": "Accepted Qty",
                    "rejected_qty": "Rejected Qty",
                    "remarks": "Remarks"
                }.get(key, key)
                product[new_key] = value
            # Ensure numeric fields have valid values
            for field in ["Ordered Qty", "Received Qty", "Accepted Qty", "Rejected Qty"]:
                try:
                    product[field] = float(product.get(field, 0))
                except (ValueError, TypeError):
                    logger.warning(f"Invalid value for {field} in product {product.get('Name', 'unknown')}: {product.get(field)}, setting to 0")
                    product[field] = 0
            product["Remarks"] = str(product.get("Remarks", ""))
            sanitized_rows.append(product)
        self.product_rows = sanitized_rows
        logger.debug(f"Initialized GRNForm with product_rows: {self.product_rows}")
        self.setObjectName("GRNForm")
        apply_stylesheet(self, "grn_form.qss")
        self.setup_ui()

    def setup_ui(self):
        logger.info(f"Creating GRN form (ID: {self.voucher_type_id})")

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
        title_label = create_title_label("Create GRN")
        self.content_layout.addWidget(title_label)

        # Header row: GRN Number, PO Number
        header_fields = [
            ("GRN Number*", 'text', "Voucher Number", self.voucher_data.get("Voucher Number", get_next_grn_sequence())),
            ("PO Number*", 'combo', "PO Number", self.voucher_data.get("PO Number", ""))
        ]
        header_row, header_entries = create_header_row(header_fields)
        self.content_layout.addLayout(header_row)
        self.entries.update(header_entries)
        self.entries["PO Number"].lineEdit().setAlignment(Qt.AlignLeft | Qt.AlignVCenter)
        # Populate PO combo
        try:
            from src.erp.voucher.voucher_operations import get_eligible_pos
            po_values, _ = get_eligible_pos()
        except ImportError as e:
            logger.error(f"Failed to import and call get_eligible_pos: {e}")
            po_values = []
        self.entries["PO Number"].addItems(po_values)
        self.entries["PO Number"].setCurrentIndex(-1)

        # Details row: Date, Vendor (read-only), Material Received Date
        details_row = QHBoxLayout()
        details_row.setSpacing(10)
        # Date
        date_label = QLabel("Date*")
        date_label.setObjectName("fieldLabel")
        date_label.setAlignment(Qt.AlignLeft | Qt.AlignVCenter)
        self.date_entry = QDateEdit()
        self.date_entry.setObjectName("grnDateEntry")
        date_line_edit = self.date_entry.lineEdit()
        if date_line_edit:
            date_line_edit.setAlignment(Qt.AlignLeft | Qt.AlignVCenter)
        self.date_entry.setCalendarPopup(True)
        self.date_entry.setDate(QDate.fromString(self.voucher_data.get("Voucher Date", QDate.currentDate().toString("yyyy-MM-dd")), "yyyy-MM-dd"))
        self.entries["Voucher Date"] = self.date_entry
        date_subrow = QHBoxLayout()
        date_subrow.setSpacing(0)
        date_subrow.setContentsMargins(0, 0, 0, 0)
        date_subrow.addWidget(date_label)
        date_subrow.addWidget(self.date_entry, stretch=1)
        details_row.addLayout(date_subrow, stretch=1)

        # Vendor (read-only line edit)
        vendor_label = QLabel("Vendor*")
        vendor_label.setObjectName("fieldLabel")
        vendor_label.setAlignment(Qt.AlignLeft | Qt.AlignVCenter)
        self.vendor_entry = QLineEdit()
        self.vendor_entry.setObjectName("vendorEntry")
        self.vendor_entry.setAlignment(Qt.AlignLeft | Qt.AlignVCenter)
        self.vendor_entry.setReadOnly(True)
        self.vendor_entry.setText(self.voucher_data.get("Party Name", ""))
        self.entries["Party Name"] = self.vendor_entry
        vendor_subrow = QHBoxLayout()
        vendor_subrow.setSpacing(0)
        vendor_subrow.setContentsMargins(0, 0, 0, 0)
        vendor_subrow.addWidget(vendor_label)
        vendor_subrow.addWidget(self.vendor_entry, stretch=1)
        details_row.addLayout(vendor_subrow, stretch=1)

        # Material Received Date
        material_label = QLabel("Material Received Date*")
        material_label.setObjectName("fieldLabel")
        material_label.setAlignment(Qt.AlignLeft | Qt.AlignVCenter)
        self.material_date_entry = QDateEdit()
        self.material_date_entry.setObjectName("materialDateEntry")
        material_line_edit = self.material_date_entry.lineEdit()
        if material_line_edit:
            material_line_edit.setAlignment(Qt.AlignLeft | Qt.AlignVCenter)
        self.material_date_entry.setCalendarPopup(True)
        self.material_date_entry.setDate(QDate.fromString(self.voucher_data.get("Material Received Date", QDate.currentDate().toString("yyyy-MM-dd")), "yyyy-MM-dd"))
        self.entries["Material Received Date"] = self.material_date_entry
        material_subrow = QHBoxLayout()
        material_subrow.setSpacing(0)
        material_subrow.setContentsMargins(0, 0, 0, 0)
        material_subrow.addWidget(material_label)
        material_subrow.addWidget(self.material_date_entry, stretch=1)
        details_row.addLayout(material_subrow, stretch=1)

        self.content_layout.addLayout(details_row)

        existing_po = self.voucher_data.get("PO Number", "")
        if existing_po:
            if self.entries["PO Number"].findText(existing_po) == -1:
                self.entries["PO Number"].addItem(existing_po)
            self.entries["PO Number"].setCurrentText(existing_po)

        self.entries["PO Number"].currentTextChanged.connect(self.populate_from_po)

        if self.voucher_data.get("id"):
            self.entries["PO Number"].setEnabled(False)

        # Product table with GRN-specific columns
        self.item_table = create_product_table(GRN_PRODUCT_COLUMNS, GRN_PRODUCT_COLUMNS)
        self.item_table.itemChanged.connect(self.update_product_rows)
        self.content_layout.addWidget(self.item_table)

        # Bottom layout
        bottom_layout = create_bottom_layout(self.app, self.voucher_type_name, self.save_voucher, lambda: self.app.show_frame("home"))
        self.content_layout.addLayout(bottom_layout)

        main_layout.addWidget(scroll)
        self.populate_product_table(self.item_table)
        self.update_product_frame_position()

    def populate_from_po(self, po_num):
        if po_num:
            session = Session()
            try:
                po_type_id = get_voucher_type_id('Purchase Order')
                result = session.execute(text("""
                    SELECT id, data
                    FROM voucher_instances
                    WHERE voucher_number = :po_num AND voucher_type_id = :po_type_id
                """), {"po_num": po_num, "po_type_id": po_type_id}).fetchone()
                if result:
                    po_id, data_json = result
                    data = json.loads(data_json)
                    vendor = data.get('Party Name', '')
                    self.vendor_entry.setText(vendor)
                    items_result = session.execute(text("""
                        SELECT name, hsn_code, qty, unit, unit_price, gst_rate, amount
                        FROM voucher_items
                        WHERE voucher_id = :po_id
                    """), {"po_id": po_id}).fetchall()
                    items = []
                    for r in items_result:
                        item = {
                            "Name": r[0],
                            "HSN Code": r[1],
                            "Qty": r[2],
                            "Unit": r[3],
                            "Unit Price": r[4],
                            "GST Rate": r[5],
                            "Amount": r[6]
                        }
                        items.append(item)
                    logger.debug(f"Retrieved PO items: {items}")
                    if not self.voucher_data.get("id"):
                        self.product_rows = []
                        for item in items:
                            product_row = {
                                "Name": item.get("Name", ""),
                                "HSN Code": item.get("HSN Code", ""),
                                "Ordered Qty": float(item.get("Qty", 0)),
                                "Received Qty": 0.0,
                                "Accepted Qty": 0.0,
                                "Rejected Qty": 0.0,
                                "Remarks": "",
                                "product_id": None,
                                "Unit": item.get("Unit", ""),
                                "Unit Price": float(item.get("Unit Price", 0)),
                                "GST Rate": float(item.get("GST Rate", 0)),
                                "Amount": 0.0
                            }
                            # Get product_id
                            prod_result = session.execute(text("""
                                SELECT id FROM products WHERE name = :name AND hsn_code = :hsn_code
                            """), {"name": product_row["Name"], "hsn_code": product_row["HSN Code"]}).fetchone()
                            if prod_result:
                                product_row["product_id"] = prod_result[0]
                            self.product_rows.append(product_row)
                        logger.debug(f"Populated product_rows: {self.product_rows}")
                        self.populate_product_table(self.item_table)
            except Exception as e:
                logger.error(f"Failed to populate from PO: {e}")
                QMessageBox.critical(self, "Error", f"Failed to populate from PO: {str(e)}")
            finally:
                session.close()

    def resizeEvent(self, event: QResizeEvent):
        super().resizeEvent(event)
        self.update_product_frame_position()

    def update_product_frame_position(self):
        pass

    def populate_product_table(self, table):
        table.setRowCount(len(self.product_rows))
        for row_idx, product in enumerate(self.product_rows):
            for col_idx, col_name in enumerate(GRN_PRODUCT_COLUMNS):
                item = QTableWidgetItem()
                value = str(product.get(col_name, ""))
                item.setText(value)
                if col_name == "Ordered Qty":
                    item.setFlags(item.flags() & ~Qt.ItemIsEditable)  # Make Ordered Qty non-editable
                table.setItem(row_idx, col_idx, item)
        logger.debug(f"Populated table with product_rows: {self.product_rows}")

    def update_product_rows(self, item):
        row = item.row()
        col = item.column()
        col_name = GRN_PRODUCT_COLUMNS[col]
        text = item.text()
        if col_name in ["Received Qty", "Accepted Qty", "Rejected Qty"]:
            try:
                float(text)
            except ValueError:
                logger.warning(f"Invalid input '{text}' for {col_name} in row {row}, setting to 0")
                item.setText("0")
                text = "0"
        self.product_rows[row][col_name] = text
        logger.debug(f"Updated product_rows[{row}][{col_name}] to '{text}'")

    def pre_save_check_grn(self, product):
        try:
            received = float(product.get("Received Qty", "0"))
            accepted = float(product.get("Accepted Qty", "0"))
            rejected = float(product.get("Rejected Qty", "0"))
            if accepted + rejected != received:
                logger.error(f"Validation failed for product {product.get('Name', 'unknown')}: Accepted ({accepted}) + Rejected ({rejected}) != Received ({received})")
                QMessageBox.critical(self, "Error", f"Accepted + Rejected must equal Received Qty for product {product.get('Name', 'unknown')}")
                return False
            return True
        except (ValueError, TypeError) as e:
            logger.error(f"Validation error for product {product.get('Name', 'unknown')}: {e}, product data: {product}")
            QMessageBox.critical(self, "Error", f"Invalid quantity data for product {product.get('Name', 'unknown')}")
            return False

    def save_voucher(self):
        logger.debug(f"Attempting to save GRN with product_rows: {self.product_rows}")
        save_voucher(self, ["Voucher Number", "Voucher Date", "Party Name", "PO Number", "Material Received Date"], increment_grn_sequence, product_columns=GRN_PRODUCT_COLUMNS, pre_save_check=self.pre_save_check_grn, stock_update=True, stock_update_direction=1, stock_update_key="Accepted Qty")