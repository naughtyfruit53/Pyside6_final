# src/erp/logic/products_logic.py
# Converted to SQLAlchemy.

from PySide6.QtWidgets import QDialog, QVBoxLayout, QHBoxLayout, QLabel, QLineEdit, QComboBox, QCheckBox, QListWidget, QPushButton, QFileDialog, QMessageBox, QScrollArea, QWidget
from PySide6.QtCore import Qt, QLocale
from PySide6.QtGui import QCloseEvent, QDoubleValidator, QIntValidator
import logging
import pandas as pd
from datetime import datetime
from sqlalchemy import text, insert
from src.erp.logic.database.session import engine, Session
from src.core.config import get_database_url
from src.erp.logic.utils.utils import UNITS, add_unit  # From utils.py
from src.erp.logic.utils.products_utils import validate_schema, validate_product_name  # Updated import
from src.erp.logic.database.models import Base

logger = logging.getLogger(__name__)

class AddProductDialog(QDialog):
    def __init__(self, parent=None, app=None, callback=None, entries=None, is_edit=False, prefill_name=""):
        super().__init__(parent)
        self.app = app
        self.callback = callback
        self.entries = entries or {}
        self.drawings = []
        self.is_edit = is_edit
        self.prefill_name = prefill_name
        self.setWindowTitle("Edit Product" if is_edit else "Add Product")
        self.setFixedSize(400, 700)
        self.setModal(True)
        self.setup_ui()

    def setup_ui(self):
        logger.info("Creating add product dialog")
        main_layout = QVBoxLayout(self)
        main_layout.setContentsMargins(10, 10, 10, 10)

        scroll = QScrollArea()
        scroll.setWidgetResizable(True)
        content_widget = QWidget()
        scroll.setWidget(content_widget)
        content_layout = QVBoxLayout(content_widget)
        content_layout.setAlignment(Qt.AlignTop)

        title_label = QLabel("Edit Product" if self.is_edit else "Add Product")
        title_label.setObjectName("dialogTitleLabel")
        title_label.setStyleSheet("font-size: 14px; font-weight: bold; border: none; background-color: transparent;")
        title_label.setAlignment(Qt.AlignCenter)
        content_layout.addWidget(title_label)

        fields = [
            ("Name*", "normal"),
            ("Part No", "normal"),
            ("HSN Code", "normal"),
            ("Unit*", "combobox"),
            ("Unit Price*", "normal", "0.0"),
            ("GST Rate%", "combobox", "0%"),
            ("GST Type", "checkbox", False),
            ("Reorder Level", "normal", "0"),
            ("Description", "normal"),
            ("Is Manufactured", "checkbox", False),
        ]

        for label_text, field_type, *default in fields:
            row_layout = QHBoxLayout()
            label = QLabel(label_text)
            label.setObjectName("fieldLabel")
            label.setFixedWidth(120)
            row_layout.addWidget(label)

            if field_type == "combobox":
                combo = QComboBox()
                combo.setObjectName("textEntry")
                values = UNITS if label_text == "Unit*" else ["0%", "5%", "12%", "18%", "28%"]
                combo.addItems(values)
                if default:
                    combo.setCurrentText(default[0])
                if label_text == "GST Rate%":
                    combo.setEditable(False)
                self.entries[label_text] = combo
                row_layout.addWidget(combo)
            elif field_type == "checkbox":
                chk = QCheckBox("Inclusive" if label_text == "GST Type" else "")
                chk.setChecked(default[0] if default else False)
                self.entries[label_text] = chk
                row_layout.addWidget(chk)
            else:
                entry = QLineEdit()
                entry.setObjectName("textEntry")
                if default:
                    entry.setText(default[0])
                if label_text == "Unit Price*":
                    entry.setValidator(QDoubleValidator(0.0, 999999999.99, 2))
                elif label_text == "Reorder Level":
                    entry.setValidator(QIntValidator(0, 9999999))
                self.entries[label_text] = entry
                row_layout.addWidget(entry)
            content_layout.addLayout(row_layout)

        if self.prefill_name:
            self.entries["Name*"].setText(self.prefill_name)

        # Drawings upload section
        drawings_label = QLabel("Drawings (up to 5 files)")
        drawings_label.setObjectName("fieldLabel")
        drawings_label.setFixedWidth(120)
        content_layout.addWidget(drawings_label)
        self.drawings_list = QListWidget()
        self.drawings_list.setObjectName("listWidget")
        content_layout.addWidget(self.drawings_list)

        add_drawing_button = QPushButton("Add Drawing")
        add_drawing_button.setObjectName("actionButton")
        add_drawing_button.clicked.connect(self.add_drawing)
        remove_drawing_button = QPushButton("Remove Drawing")
        remove_drawing_button.setObjectName("actionButton")
        remove_drawing_button.clicked.connect(self.remove_drawing)
        content_layout.addWidget(add_drawing_button)
        content_layout.addWidget(remove_drawing_button)

        button_layout = QHBoxLayout()
        save_button = QPushButton("Save")
        save_button.setObjectName("actionButton")
        save_button.clicked.connect(self.save_product)
        cancel_button = QPushButton("Cancel")
        cancel_button.setObjectName("actionButton")
        cancel_button.clicked.connect(lambda: close_window(self, self.app))
        button_layout.addWidget(cancel_button)
        button_layout.addWidget(save_button)
        content_layout.addLayout(button_layout)

        main_layout.addWidget(scroll)

    def add_drawing(self):
        if len(self.drawings) >= 5:
            QMessageBox.warning(self, "Warning", "Maximum 5 drawings allowed")
            return
        file_paths, _ = QFileDialog.getOpenFileNames(self, "Select Drawings", "", "All files (*.*)")
        for file_path in file_paths:
            if file_path and len(self.drawings) < 5:
                self.drawings.append(file_path)
                self.drawings_list.addItem(file_path)

    def remove_drawing(self):
        selected = self.drawings_list.currentRow()
        if selected >= 0:
            self.drawings.pop(selected)
            self.drawings_list.takeItem(selected)

    def save_product(self):
        save_product(self.app, self.entries, self.drawings, self, self.callback)

    def closeEvent(self, event: QCloseEvent):
        close_window(self, self.app)
        super().closeEvent(event)

def add_product(app, parent=None, callback=None, prefill_name=""):
    if app.add_window_open:
        if app.add_window and not app.add_window.isHidden():
            app.add_window.raise_()
            app.add_window.activateWindow()
        return
    app.add_window = AddProductDialog(parent, app, callback, prefill_name=prefill_name)
    app.add_window_open = True
    app.add_window.show()

def save_product(app, entries, drawings, window, callback=None):
    session = Session()
    mandatory_fields = ["Name*", "Unit*", "Unit Price*", "GST Rate%", "Reorder Level"]
    name = entries["Name*"].text() if isinstance(entries["Name*"], QLineEdit) else entries["Name*"].currentText()
    unit = entries["Unit*"].currentText()
    unit_price_str = entries["Unit Price*"].text()
    gst_rate_str = entries["GST Rate%"].currentText()
    reorder_level_str = entries["Reorder Level"].text()

    if not all(entries[field].text() if isinstance(entries[field], QLineEdit) else entries[field].currentText() for field in mandatory_fields):
        QMessageBox.critical(window, "Error", "All mandatory fields are required")
        return

    if not entries["Unit Price*"].hasAcceptableInput():
        QMessageBox.critical(window, "Error", "Invalid unit price format")
        return

    if not entries["Reorder Level"].hasAcceptableInput():
        QMessageBox.critical(window, "Error", "Invalid reorder level format")
        return

    if not validate_product_name(name):
        QMessageBox.critical(window, "Error", "Product name contains invalid characters (e.g., ';', '--', '/*', '*/')")
        return

    try:
        locale = QLocale()
        unit_price, ok1 = locale.toDouble(unit_price_str)
        if not ok1:
            raise ValueError("Invalid unit price")
        reorder_level, ok2 = locale.toInt(reorder_level_str)
        if not ok2:
            raise ValueError("Invalid reorder level")
        gst_rate = float(gst_rate_str.replace("%", ""))
        is_gst_inclusive = "Inclusive" if entries["GST Type"].isChecked() else "Exclusive"
        drawings_str = ",".join(drawings) if drawings else ""

        if unit_price < 0 or reorder_level < 0 or gst_rate < 0:
            QMessageBox.critical(window, "Error", "Numeric fields cannot be negative")
            return

        if is_gst_inclusive == "Inclusive" and gst_rate > 0:
            unit_price /= (1 + gst_rate / 100)

        add_unit(unit)

        created_at = datetime.now()

        expected_columns = ["id", "name", "part_no", "hsn_code", "unit", "unit_price", "gst_rate",
                           "is_gst_inclusive", "reorder_level", "description", "created_at", "is_manufactured", "drawings"]

        if not validate_schema("products", expected_columns):
            QMessageBox.critical(window, "Error", "Database schema for products table is invalid")
            return

        existing = session.execute(text("SELECT id FROM products WHERE LOWER(name) = LOWER(:name)"), {"name": name}).fetchone()
        if existing:
            QMessageBox.critical(window, "Error", f"Product '{name}' already exists")
            return

        stmt = insert(Base.metadata.tables['products']).values(
            name=name,
            part_no=entries["Part No"].text(),
            hsn_code=entries["HSN Code"].text(),
            unit=unit,
            unit_price=unit_price,
            gst_rate=gst_rate,
            is_gst_inclusive=is_gst_inclusive,
            reorder_level=reorder_level,
            description=entries["Description"].text(),
            is_manufactured=1 if entries["Is Manufactured"].isChecked() else 0,
            created_at=created_at,
            drawings=drawings_str
        ).returning(Base.metadata.tables['products'].c.id)
        result = session.execute(stmt)
        product_id = result.fetchone()[0]

        session.execute(insert(Base.metadata.tables['stock']).values(
            product_id=product_id,
            quantity=0,
            unit=unit,
            last_updated=created_at
        ))

        session.execute(insert(Base.metadata.tables['audit_log']).values(
            table_name='products',
            record_id=product_id,
            action='INSERT',
            username='system_user',
            timestamp=created_at
        ))

        session.commit()

        QMessageBox.information(window, "Success", "Product added successfully")
        close_window(window, app)
        if callback:
            callback(product_id, name)
    except ValueError as ve:
        import traceback
        QMessageBox.critical(window, "Error", "Invalid numeric input")
        logger.error(f"Invalid input in save_product: {ve}\n{traceback.format_exc()}")
    except Exception as e:
        import traceback
        session.rollback()
        QMessageBox.critical(window, "Error", f"Database error: {e}")
        logger.error(f"Database error adding product: {e}\n{traceback.format_exc()}")
    finally:
        session.close()

def edit_product(app, product_id, callback, parent=None):
    session = Session()
    try:
        product = session.execute(text("SELECT * FROM products WHERE id = :product_id"), {"product_id": product_id}).fetchone()
        if not product:
            QMessageBox.critical(app, "Error", "Product not found")
            return
    except Exception as e:
        logger.error(f"Error fetching product: {e}")
        QMessageBox.critical(app, "Error", f"Failed to fetch product: {e}")
        return
    finally:
        session.close()

    if app.add_window_open:
        if app.add_window and not app.add_window.isHidden():
            app.add_window.raise_()
            return

    entries = {}
    fields = [
        ("Name*", product[1]),
        ("Part No", product[2] or ""),
        ("HSN Code", product[3] or ""),
        ("Unit*", product[4]),
        ("Unit Price*", str(product[5])),
        ("GST Rate%", f"{product[6]}%"),
        ("GST Type", product[7] == "Inclusive"),
        ("Reorder Level", str(product[8])),
        ("Description", product[9] or ""),
        ("Is Manufactured", bool(product[11])),
    ]

    dialog = AddProductDialog(parent, app, callback, entries, is_edit=True)
    dialog.drawings = product[12].split(",") if product[12] else []
    for drawing in dialog.drawings:
        if drawing:
            dialog.drawings_list.addItem(drawing)

    for label, value in fields:
        if label in ["Unit*", "GST Rate%"]:
            dialog.entries[label].setCurrentText(value)
        elif label in ["GST Type", "Is Manufactured"]:
            dialog.entries[label].setChecked(value)
        else:
            dialog.entries[label].setText(value)

    dialog.save_product = lambda: save_edit_product(app, dialog.entries, dialog.drawings, dialog, product[0], callback)
    app.add_window = dialog
    app.add_window_open = True
    dialog.show()

def save_edit_product(app, entries, drawings, window, product_id, callback):
    session = Session()
    mandatory_fields = ["Name*", "Unit*", "Unit Price*", "GST Rate%", "Reorder Level"]
    name = entries["Name*"].text() if isinstance(entries["Name*"], QLineEdit) else entries["Name*"].currentText()
    unit = entries["Unit*"].currentText()
    unit_price_str = entries["Unit Price*"].text()
    gst_rate_str = entries["GST Rate%"].currentText()
    reorder_level_str = entries["Reorder Level"].text()

    if not all(entries[field].text() if isinstance(entries[field], QLineEdit) else entries[field].currentText() for field in mandatory_fields):
        QMessageBox.critical(window, "Error", "All mandatory fields are required")
        return

    if not entries["Unit Price*"].hasAcceptableInput():
        QMessageBox.critical(window, "Error", "Invalid unit price format")
        return

    if not entries["Reorder Level"].hasAcceptableInput():
        QMessageBox.critical(window, "Error", "Invalid reorder level format")
        return

    if not validate_product_name(name):
        QMessageBox.critical(window, "Error", "Product name contains invalid characters (e.g., ';', '--', '/*', '*/')")
        return

    try:
        locale = QLocale()
        unit_price, ok1 = locale.toDouble(unit_price_str)
        if not ok1:
            raise ValueError("Invalid unit price")
        reorder_level, ok2 = locale.toInt(reorder_level_str)
        if not ok2:
            raise ValueError("Invalid reorder level")
        gst_rate = float(gst_rate_str.replace("%", ""))
        is_gst_inclusive = "Inclusive" if entries["GST Type"].isChecked() else "Exclusive"
        drawings_str = ",".join(drawings) if drawings else ""

        if unit_price < 0 or reorder_level < 0 or gst_rate < 0:
            QMessageBox.critical(window, "Error", "Numeric fields cannot be negative")
            return

        if is_gst_inclusive == "Inclusive" and gst_rate > 0:
            unit_price /= (1 + gst_rate / 100)

        add_unit(unit)

        existing = session.execute(text("SELECT id FROM products WHERE LOWER(name) = LOWER(:name) AND id != :product_id"), {"name": name, "product_id": product_id}).fetchone()
        if existing:
            QMessageBox.critical(window, "Error", f"Product '{name}' already exists")
            return

        session.execute(text("""
            UPDATE products
            SET name = :name, part_no = :part_no, hsn_code = :hsn_code, unit = :unit, unit_price = :unit_price, gst_rate = :gst_rate, is_gst_inclusive = :is_gst_inclusive,
                reorder_level = :reorder_level, description = :description, is_manufactured = :is_manufactured, drawings = :drawings
            WHERE id = :product_id
        """), {
            "name": name,
            "part_no": entries["Part No"].text(),
            "hsn_code": entries["HSN Code"].text(),
            "unit": unit,
            "unit_price": unit_price,
            "gst_rate": gst_rate,
            "is_gst_inclusive": is_gst_inclusive,
            "reorder_level": reorder_level,
            "description": entries["Description"].text(),
            "is_manufactured": 1 if entries["Is Manufactured"].isChecked() else 0,
            "drawings": drawings_str,
            "product_id": product_id
        })

        session.execute(text("""
            UPDATE stock
            SET unit = :unit, last_updated = :last_updated
            WHERE product_id = :product_id
        """), {"unit": unit, "last_updated": datetime.now(), "product_id": product_id})

        session.execute(text("""
            INSERT INTO audit_log (table_name, record_id, action, username, timestamp)
            VALUES ('products', :product_id, 'UPDATE', 'system_user', :last_updated)
        """), {"product_id": product_id, "last_updated": datetime.now()})

        session.commit()

        QMessageBox.information(window, "Success", "Product updated successfully")
        close_window(window, app)
        if callback:
            callback(product_id, name)
    except ValueError as ve:
        import traceback
        QMessageBox.critical(window, "Error", "Invalid numeric input")
        logger.error(f"Invalid input in save_edit_product: {ve}\n{traceback.format_exc()}")
    except Exception as e:
        import traceback
        session.rollback()
        QMessageBox.critical(window, "Error", f"Database error: {e}")
        logger.error(f"Database error editing product: {e}\n{traceback.format_exc()}")
    finally:
        session.close()

def delete_product(app, product_id, callback):
    session = Session()
    try:
        product_name = session.execute(text("SELECT name FROM products WHERE id = :product_id"), {"product_id": product_id}).fetchone()
        if not product_name:
            QMessageBox.critical(app, "Error", "Product not found")
            return
        product_name = product_name[0]

        po_count = session.execute(text("SELECT COUNT(*) FROM po_items WHERE product_id = :product_id"), {"product_id": product_id}).fetchone()[0]
        if po_count > 0:
            QMessageBox.critical(app, "Error", f"Cannot delete '{product_name}' as it is referenced in purchase orders.")
            return
        mt_count = session.execute(text("SELECT COUNT(*) FROM material_transactions WHERE product_id = :product_id"), {"product_id": product_id}).fetchone()[0]
        if mt_count > 0:
            QMessageBox.critical(app, "Error", f"Cannot delete '{product_name}' as it is referenced in material transactions.")
            return

        if QMessageBox.question(app, "Confirm Delete", f"Delete '{product_name}'?") != QMessageBox.Yes:
            return

        session.execute(text("DELETE FROM stock WHERE product_id = :product_id"), {"product_id": product_id})
        session.execute(text("DELETE FROM products WHERE id = :product_id"), {"product_id": product_id})
        session.execute(text("""
            INSERT INTO audit_log (table_name, record_id, action, username, timestamp)
            VALUES ('products', :product_id, 'DELETE', 'system_user', :timestamp)
        """), {"product_id": product_id, "timestamp": datetime.now()})
        session.commit()

        QMessageBox.information(app, "Success", "Product deleted successfully")
        callback()
    except Exception as e:
        session.rollback()
        logger.error(f"Error deleting product: {e}")
        QMessageBox.critical(app, "Error", f"Failed to delete: {e}")
    finally:
        session.close()

def import_excel_products(app, callback):
    file_path, _ = QFileDialog.getOpenFileName(None, "Select File", "", "Excel files (*.xlsx *.xls);;All files (*.*)")
    if not file_path:
        logger.info("No file selected")
        return

    session = Session()
    try:
        df = pd.read_excel(file_path, sheet_name="Sheet1")
        df.columns = [col.strip().lower() for col in df.columns]
        expected_columns = ['name', 'part no', 'hsn code', 'unit', 'unit price', 'gst rate', 'gst type', 'reorder level', 'description', 'drawings']
        if not all(col in df.columns for col in expected_columns):
            missing_cols = [col for col in expected_columns if col not in df.columns]
            logger.error(f"Missing columns: {missing_cols}")
            QMessageBox.critical(app, "Error", f"Missing columns: {missing_cols}")
            return

        imported_count = 0
        updated_count = 0
        created_at = datetime.now()
        expected_db_columns = ["id", "name", "part_no", "hsn_code", "unit", "unit_price", "gst_rate",
                               "is_gst_inclusive", "reorder_level", "description", "created_at", "is_manufactured", "drawings"]
        if not validate_schema("products", expected_db_columns):
            QMessageBox.critical(app, "Error", "Database schema for products table is invalid")
            return

        products = session.execute(text("SELECT id, name, unit FROM products")).fetchall()
        product_dict = {}
        for pid, db_name, db_unit in products:
            if db_name is not None:
                norm_db_name = ' '.join(db_name.strip().split()).lower()
                product_dict[norm_db_name] = (pid, db_name, db_unit)
        for index, row in df.iterrows():
            try:
                name = str(row['name']).strip() if pd.notna(row['name']) else None
                part_no = str(row['part no']).strip() if pd.notna(row['part no']) else ""
                unit = str(row['unit']).strip() if pd.notna(row['unit']) else None
                unit_price_val = row['unit price']
                if isinstance(unit_price_val, str):
                    unit_price_val = unit_price_val.replace(",", "")
                unit_price = float(unit_price_val) if pd.notna(row['unit price']) else 0.0
                gst_rate_val = row['gst rate']
                if isinstance(gst_rate_val, str):
                    gst_rate_val = gst_rate_val.replace(",", "")
                gst_rate = float(gst_rate_val) if pd.notna(row['gst rate']) else 0.0
                is_gst_inclusive = str(row['gst type']).strip() if pd.notna(row['gst type']) else "Exclusive"
                is_gst_inclusive = "Inclusive" if is_gst_inclusive.lower() == "inclusive" else "Exclusive"
                reorder_level_val = row['reorder level']
                if isinstance(reorder_level_val, str):
                    reorder_level_val = reorder_level_val.replace(",", "")
                reorder_level = int(reorder_level_val) if pd.notna(row['reorder level']) else 0
                hsn_code = str(row['hsn code']).strip() if pd.notna(row['hsn code']) else ""
                description = str(row['description']).strip() if pd.notna(row['description']) else ""
                drawings = str(row['drawings']).strip() if pd.notna(row['drawings']) else ""

                if not name or not unit:
                    logger.warning(f"Skipping row {index + 2}: Missing mandatory fields")
                    continue

                if not validate_product_name(name):
                    logger.warning(f"Skipping row {index + 2}: Invalid product name")
                    continue

                existing = session.execute(text("""
                    SELECT id, part_no, hsn_code, unit, unit_price, gst_rate, is_gst_inclusive, reorder_level, description, is_manufactured, drawings
                    FROM products WHERE LOWER(name) = LOWER(:name)
                """), {"name": name}).fetchone()

                if existing:
                    product_id, db_part_no, db_hsn_code, db_unit, db_unit_price, db_gst_rate, db_is_gst_inclusive, db_reorder_level, db_description, db_is_manufactured, db_drawings = existing
                    updates = {}
                    if part_no and not db_part_no:
                        updates['part_no'] = part_no
                    if hsn_code and not db_hsn_code:
                        updates['hsn_code'] = hsn_code
                    if unit and unit != db_unit:
                        updates['unit'] = unit
                    if pd.notna(row['unit price']) and unit_price != db_unit_price:
                        updates['unit_price'] = unit_price
                    if pd.notna(row['gst rate']) and gst_rate != db_gst_rate:
                        updates['gst_rate'] = gst_rate
                    if is_gst_inclusive != db_is_gst_inclusive:
                        updates['is_gst_inclusive'] = is_gst_inclusive
                    if pd.notna(row['reorder level']) and reorder_level != db_reorder_level:
                        updates['reorder_level'] = reorder_level
                    if description and not db_description:
                        updates['description'] = description
                    if drawings and not db_drawings:
                        updates['drawings'] = drawings

                    if updates:
                        set_clause = ", ".join(f"{key} = :{key}" for key in updates.keys())
                        updates['product_id'] = product_id
                        session.execute(text(f"""
                            UPDATE products
                            SET {set_clause}
                            WHERE id = :product_id
                        """), updates)
                        session.execute(text("""
                            UPDATE stock
                            SET unit = :unit, last_updated = :last_updated
                            WHERE product_id = :product_id
                        """), {"unit": unit, "last_updated": datetime.now(), "product_id": product_id})
                        session.execute(text("""
                            INSERT INTO audit_log (table_name, record_id, action, username, timestamp)
                            VALUES ('products', :product_id, 'UPDATE', 'system_user', :timestamp)
                        """), {"product_id": product_id, "timestamp": datetime.now()})
                        updated_count += 1
                    continue

                stmt = insert(Base.metadata.tables['products']).values(
                    name=name,
                    hsn_code=hsn_code,
                    part_no=part_no,
                    unit=unit,
                    unit_price=unit_price,
                    gst_rate=gst_rate,
                    is_gst_inclusive=is_gst_inclusive,
                    reorder_level=reorder_level,
                    description=description,
                    created_at=created_at,
                    drawings=drawings
                ).returning(Base.metadata.tables['products'].c.id)
                result = session.execute(stmt)
                product_id = result.fetchone()[0]
                session.execute(insert(Base.metadata.tables['stock']).values(
                    product_id=product_id,
                    quantity=0,
                    unit=unit,
                    last_updated=created_at
                ))
                session.execute(insert(Base.metadata.tables['audit_log']).values(
                    table_name='products',
                    record_id=product_id,
                    action='INSERT',
                    username='system_user',
                    timestamp=created_at
                ))
                imported_count += 1
            except Exception as e:
                logger.error(f"Error processing row {index + 2}: {e}")
                continue

        session.commit()

        QMessageBox.information(app, "Success", f"Imported {imported_count} new, updated {updated_count} products")
        callback()
    except Exception as e:
        session.rollback()
        logger.error(f"Unexpected error importing products: {e}")
        QMessageBox.critical(app, "Error", f"Failed to import: {e}")
    finally:
        session.close()

def export_products():
    file_path, _ = QFileDialog.getSaveFileName(None, "Save File", f"products_export_{datetime.now().strftime('%Y%m%d_%H%M%S')}.xlsx", "Excel files (*.xlsx)")
    if not file_path:
        return

    session = Session()
    try:
        query = text("""
            SELECT name, part_no, hsn_code, unit, unit_price, gst_rate, is_gst_inclusive AS 'gst type',
                   reorder_level, description, drawings
            FROM products
            ORDER BY name
        """)
        df = pd.read_sql_query(query, session.connection())
        df.to_excel(file_path, sheet_name="Sheet1", index=False)
        session.execute(text("""
            INSERT INTO audit_log (table_name, record_id, action, username, timestamp)
            VALUES ('products', 0, 'EXPORT', 'system_user', :timestamp)
        """), {"timestamp": datetime.now()})
        session.commit()
        QMessageBox.information(None, "Success", f"Exported to {file_path}")
    except Exception as e:
        logger.error(f"Unexpected error exporting products: {e}")
        QMessageBox.critical(None, "Error", f"Failed to export: {e}")
    finally:
        session.close()

def download_sample():
    file_path, _ = QFileDialog.getSaveFileName(None, "Save Sample File", "sample_products.xlsx", "Excel files (*.xlsx)")
    if not file_path:
        return

    try:
        df = pd.DataFrame(columns=['name', 'part no', 'hsn code', 'unit', 'unit price', 'gst rate', 'gst type', 'reorder level', 'description', 'drawings'])
        df.to_excel(file_path, sheet_name="Sheet1", index=False)
        QMessageBox.information(None, "Success", f"Sample saved to {file_path}")
    except Exception as e:
        logger.error(f"Error saving sample: {e}")
        QMessageBox.critical(None, "Error", f"Failed to save sample: {e}")

def close_window(window, app):
    window.close()
    app.add_window = None
    app.add_window_open = False