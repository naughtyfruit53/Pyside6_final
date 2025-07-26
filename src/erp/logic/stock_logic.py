# src/erp/logic/stock_logic.py
# Converted to SQLAlchemy.

import logging
from datetime import datetime
from PySide6.QtWidgets import QMessageBox, QDialog, QVBoxLayout, QHBoxLayout, QLabel, QLineEdit, QComboBox, QPushButton, QFileDialog, QCheckBox, QTableWidgetItem
from PySide6.QtGui import QColor, QFont
from PySide6.QtCore import Qt
from sqlalchemy import text, insert
from src.erp.logic.database.session import engine, Session
from src.core.config import get_database_url
from src.erp.logic.utils.utils import UNITS, add_unit
from src.erp.logic.utils.document_utils import generate_stock_report
from src.erp.logic.products_logic import add_product, edit_product
import pandas as pd
from src.erp.logic.database.models import Base

logging.basicConfig(filename='app.log', level=logging.DEBUG, format='%(asctime)s - %(name)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

class StockLogic:
    def __init__(self, app):
        self.app = app
        self.stock_ui = None

    def set_ui(self, stock_ui):
        self.stock_ui = stock_ui
        self.load_stock()

    def _load_stock(self, search_text='', show_zero=False):
        session = Session()
        try:
            query = text("""
                SELECT p.name, p.unit, COALESCE(s.quantity, 0), p.unit_price, 
                       (COALESCE(s.quantity, 0) * p.unit_price) as total_value, p.reorder_level, s.last_updated
                FROM products p
                LEFT JOIN stock s ON s.product_id = p.id
            """)
            params = {}
            where_clauses = []
            if search_text:
                where_clauses.append("p.name ILIKE :search_text")
                params["search_text"] = f"%{search_text}%"
            if not show_zero:
                where_clauses.append("COALESCE(s.quantity, 0) > 0")
            if where_clauses:
                query = text(query.text + " WHERE " + " AND ".join(where_clauses) + " ORDER BY p.name")
            stock_data = session.execute(query, params).fetchall()
            logger.info(f"Loaded {len(stock_data)} stock items")
            self.stock_ui.stock_table.setRowCount(0)
            integer_units = {'Pcs', 'Nos', 'Set', 'Pair'}  # Define integer units; adjust as needed based on your UNITS
            for row_idx, row_data in enumerate(stock_data):
                self.stock_ui.stock_table.insertRow(row_idx)
                name, unit, quantity, unit_price, total_value, reorder_level, last_updated = row_data
                quantity_float = float(quantity)
                if unit in integer_units:
                    quantity_str = str(int(quantity_float))
                else:
                    quantity_str = f"{quantity_float:.2f}"
                table_data = [
                    str(name) if name is not None else 'N/A',
                    f"{quantity_str} {unit}",
                    f"{float(unit_price):.2f}" if unit_price is not None else 'N/A',
                    f"{float(total_value):.2f}" if total_value is not None else 'N/A',
                    str(reorder_level) if reorder_level is not None else 'N/A',
                    str(last_updated) if last_updated is not None else 'N/A'
                ]
                numerical_data = [
                    None,  # Product Name
                    quantity_float,  # Quantity for sorting
                    float(unit_price) if unit_price is not None else 0.0,
                    float(total_value) if total_value is not None else 0.0,
                    int(reorder_level) if reorder_level is not None else 0,
                    last_updated  # Keep as string for now
                ]
                for col_idx, value_str in enumerate(table_data):
                    item = QTableWidgetItem(value_str)
                    item.setTextAlignment(Qt.AlignCenter)
                    if col_idx == 0:
                        font = QFont()
                        font.setBold(True)
                        item.setFont(font)
                    if numerical_data[col_idx] is not None:
                        item.setData(Qt.UserRole, numerical_data[col_idx])
                    self.stock_ui.stock_table.setItem(row_idx, col_idx, item)
                # Highlight low stock
                reorder_level_int = int(reorder_level) if reorder_level is not None else 0
                if quantity_float <= reorder_level_int:
                    for col in range(self.stock_ui.stock_table.columnCount()):
                        self.stock_ui.stock_table.item(row_idx, col).setBackground(QColor("yellow"))
            self.stock_ui.stock_table.resizeColumnsToContents()
        except Exception as e:
            logger.error(f"Failed to load stock: {e}")
            QMessageBox.critical(self.stock_ui, "Error", f"Failed to load stock: {e}")
        finally:
            session.close()

    def load_stock(self, show_zero=False):
        search_text = self.stock_ui.search_input.text().lower() if self.stock_ui else ''
        self._load_stock(search_text, show_zero)

    def filter_stock(self, show_zero=False):
        search_text = self.stock_ui.search_input.text().lower()
        self._load_stock(search_text, show_zero)

    def view_product_details(self):
        selected_rows = self.stock_ui.stock_table.selectedIndexes()
        if not selected_rows:
            QMessageBox.warning(self.stock_ui, "Warning", "Please select a product")
            return
        product_name = self.stock_ui.stock_table.item(selected_rows[0].row(), 0).text()
        session = Session()
        try:
            data = session.execute(text("SELECT description, gst_rate FROM products WHERE name = :product_name"), {"product_name": product_name}).fetchone()
            description = data[0]
            gst_rate = data[1]
            details = f"Product: {product_name}\nDescription: {description or 'N/A'}\nGST Rate: {gst_rate or 'N/A'}"
            QMessageBox.information(self.stock_ui, "Product Details", details)
        except Exception as e:
            logger.error(f"Failed to view product details: {e}")
            QMessageBox.critical(self.stock_ui, "Error", f"Failed to view product details: {e}")
        finally:
            session.close()

    def edit_product(self):
        selected_rows = self.stock_ui.stock_table.selectedIndexes()
        if not selected_rows:
            QMessageBox.warning(self.stock_ui, "Warning", "Please select a product")
            return
        product_name = self.stock_ui.stock_table.item(selected_rows[0].row(), 0).text()
        session = Session()
        try:
            product_id = session.execute(text("SELECT id FROM products WHERE name = :product_name"), {"product_name": product_name}).fetchone()[0]
            if product_id is None:
                QMessageBox.warning(self.stock_ui, "Warning", "Product ID not found")
                return
            edit_product(self.app, product_id, lambda *_: self.load_stock(show_zero=self.stock_ui.show_zero_chk.isChecked()), parent=self.stock_ui)
        except Exception as e:
            logger.error(f"Failed to retrieve product ID: {e}")
            QMessageBox.critical(self.stock_ui, "Error", f"Failed to edit product: {e}")
        finally:
            session.close()

    def edit_stock(self):
        selected_rows = self.stock_ui.stock_table.selectedIndexes()
        if not selected_rows:
            QMessageBox.warning(self.stock_ui, "Warning", "Please select a product")
            return
        row = selected_rows[0].row()
        product_name = self.stock_ui.stock_table.item(row, 0).text()
        session = Session()
        try:
            result = session.execute(text("""
                SELECT p.id, COALESCE(s.quantity, 0), p.unit
                FROM products p LEFT JOIN stock s ON p.id = s.product_id
                WHERE p.name = :product_name
            """), {"product_name": product_name}).fetchone()
            product_id, quantity, unit = result
            dialog = EditStockDialog(self.stock_ui, self.app, product_name, quantity, unit, product_id)
            dialog.exec()
            self.load_stock(show_zero=self.stock_ui.show_zero_chk.isChecked())
        except Exception as e:
            logger.error(f"Failed to edit stock: {e}")
            QMessageBox.critical(self.stock_ui, "Error", f"Failed to edit stock: {e}")
        finally:
            session.close()

    def manual_entry(self):
        dialog = ManualEntryDialog(self.stock_ui, self.app)
        dialog.exec()
        self.load_stock(show_zero=self.stock_ui.show_zero_chk.isChecked())

    def get_company_data(self):
        session = Session()
        try:
            result = session.execute(text("SELECT key, value FROM company_settings")).fetchall()
            return result
        except Exception as e:
            logger.error(f"Failed to fetch company data: {e}")
            return [("Company Name", "Your Company")]
        finally:
            session.close()

    def generate_stock_pdf(self):
        file_path, _ = QFileDialog.getSaveFileName(self.stock_ui, "Save Stock Report", f"stock_report_{datetime.now().strftime('%Y%m%d_%H%M%S')}.pdf", "PDF files (*.pdf)")
        if not file_path:
            return
        session = Session()
        try:
            stock_data = session.execute(text("""
                SELECT p.name, p.hsn_code, p.unit, COALESCE(s.quantity, 0), p.unit_price, p.reorder_level, p.gst_rate
                FROM products p
                LEFT JOIN stock s ON s.product_id = p.id
                ORDER BY p.name
            """)).fetchall()
            items = [
                {
                    "s_no": idx + 1,
                    "description": row[0],
                    "hsn_code": row[1] or 'N/A',
                    "unit": row[2],
                    "quantity": row[3],
                    "unit_price": row[4],
                    "reorder_level": row[5],
                    "gst_rate": row[6] or 'N/A'
                } for idx, row in enumerate(stock_data)
            ]
            company_data = self.get_company_data()
            generate_stock_report(file_path, company_data, items)
            QMessageBox.information(self.stock_ui, "Success", f"Stock report generated at {file_path}")
        except Exception as e:
            logger.error(f"Failed to generate stock PDF: {e}")
            QMessageBox.critical(self.stock_ui, "Error", f"Failed to generate stock PDF: {e}")
        finally:
            session.close()

    def import_stock(self):
        file_path, _ = QFileDialog.getOpenFileName(self.stock_ui, "Import Stock", "", "Excel files (*.xlsx *.xls)")
        if not file_path:
            return
        try:
            logger.info(f"Starting import from file: {file_path}")
            df = pd.read_excel(file_path, sheet_name="Sheet1")
            logger.info(f"Read {len(df)} rows from Excel")
            df.columns = [col.strip().lower() for col in df.columns]
            required_columns = ['name', 'quantity', 'unit']
            if not all(col in df.columns for col in required_columns):
                missing = [col for col in required_columns if col not in df.columns]
                logger.error(f"Missing columns: {', '.join(missing)}")
                QMessageBox.critical(self.stock_ui, "Error", f"Missing columns: {', '.join(missing)}")
                return
            session = Session()
            products = session.execute(text("SELECT id, name, unit FROM products")).fetchall()
            product_dict = {}
            for pid, db_name, db_unit in products:
                if db_name is not None:
                    norm_db_name = ' '.join(db_name.strip().split()).lower()
                    product_dict[norm_db_name] = (pid, db_name, db_unit)
            duplicates = False
            for index, row in df.iterrows():
                name_val = row.get('name')
                if pd.isna(name_val):
                    continue
                original_name = str(name_val)
                name = ' '.join(original_name.strip().split())
                norm_key = name.lower()
                if norm_key in product_dict:
                    duplicates = True
                    break
            import_mode = ["replace"]
            if duplicates:
                mode_dialog = QDialog(self.stock_ui)
                mode_dialog.setWindowTitle("Stock Import Options")
                layout = QVBoxLayout()
                layout.addWidget(QLabel("Duplicates found.\nChoose action:\n- Add: Add imported quantities to existing stock\n- Replace: Overwrite existing stock with imported quantities"))
                btn_frame = QHBoxLayout()
                btn_add = QPushButton("Add")
                btn_add.clicked.connect(lambda: (import_mode.__setitem__(0, "add"), mode_dialog.accept()))
                btn_replace = QPushButton("Replace")
                btn_replace.clicked.connect(lambda: (import_mode.__setitem__(0, "replace"), mode_dialog.accept()))
                btn_frame.addWidget(btn_add)
                btn_frame.addWidget(btn_replace)
                layout.addLayout(btn_frame)
                mode_dialog.setLayout(layout)
                if mode_dialog.exec() != QDialog.Accepted:
                    QMessageBox.information(self.stock_ui, "Import Cancelled", "Stock import has been cancelled.")
                    return
            import_mode = import_mode[0]
            logger.info(f"Import mode selected: {import_mode}")
            imported = 0
            updated = 0
            mismatched_units = []
            for index, row in df.iterrows():
                name_val = row.get('name')
                if pd.isna(name_val):
                    logger.info(f"Skipping row {index}: name is NaN")
                    continue
                original_name = str(name_val)
                name = ' '.join(original_name.strip().split())
                if not name:
                    logger.info(f"Skipping row {index}: name is empty after normalization")
                    continue
                quantity_val = row.get('quantity')
                if pd.isna(quantity_val):
                    logger.info(f"Skipping row {index}: quantity is NaN for {name}")
                    continue
                try:
                    quantity = float(quantity_val)
                except ValueError:
                    logger.warning(f"Skipping row {index}: invalid quantity '{quantity_val}' for {name}")
                    continue
                unit_val = row.get('unit')
                if pd.isna(unit_val):
                    logger.info(f"Skipping row {index}: unit is NaN for {name}")
                    continue
                unit = str(unit_val).strip()
                logger.info(f"Processing item: {name}, quantity: {quantity}, unit: {unit}")
                gst_rate = None
                if 'gst_rate' in df.columns:
                    gst_rate_val = row.get('gst_rate')
                    if not pd.isna(gst_rate_val):
                        gst_rate = float(gst_rate_val)
                is_gst_inclusive = None
                if 'is_gst_inclusive' in df.columns:
                    gst_inclusive_val = row.get('is_gst_inclusive')
                    if not pd.isna(gst_inclusive_val) and gst_inclusive_val in ['Inclusive', 'Exclusive']:
                        is_gst_inclusive = str(gst_inclusive_val)
                # Default to 'Exclusive' if not provided in import
                if is_gst_inclusive is None:
                    is_gst_inclusive = 'Exclusive'
                unit_price = row.get('unit_price', 0.0)
                if pd.isna(unit_price):
                    unit_price = 0.0
                else:
                    unit_price = float(unit_price)
                reorder_level = row.get('reorder_level', 0)
                if pd.isna(reorder_level):
                    reorder_level = 0
                else:
                    reorder_level = int(reorder_level)
                description = row.get('description', None)
                if pd.isna(description):
                    description = None
                else:
                    description = str(description)
                hsn_code = row.get('hsn_code', None)
                if pd.isna(hsn_code):
                    hsn_code = None
                else:
                    hsn_code = str(hsn_code)
                part_no = row.get('part_no', None)
                if pd.isna(part_no):
                    part_no = None
                else:
                    part_no = str(part_no)
                is_manufactured = row.get('is_manufactured', 0)
                if pd.isna(is_manufactured):
                    is_manufactured = 0
                else:
                    is_manufactured = int(is_manufactured)
                drawings = row.get('drawings', None)
                if pd.isna(drawings):
                    drawings = None
                else:
                    drawings = str(drawings)
                created_at = datetime.now()
                norm_key = name.lower()
                if norm_key in product_dict:
                    product_id, db_name, db_unit = product_dict[norm_key]
                    if unit.lower() != db_unit.lower():
                        mismatched_units.append(f"{original_name} (file: {unit}, db: {db_unit})")
                        logger.warning(f"Skipped due to unit mismatch: {original_name} (file: {unit}, db: {db_unit})")
                        continue
                    logger.info(f"Found existing product: {name} (ID: {product_id})")
                    # Update name to normalized if different
                    if db_name != name:
                        session.execute(text("UPDATE products SET name = :name WHERE id = :product_id"), {"name": name, "product_id": product_id})
                        session.execute(text("INSERT INTO audit_log (table_name, record_id, action, username, timestamp) VALUES ('products', :product_id, 'UPDATE_NAME', 'system_user', :timestamp)"),
                                      {"product_id": product_id, "timestamp": datetime.now()})
                        logger.info(f"Updated product name to {name}")
                    update_fields = []
                    update_values = {}
                    if hsn_code is not None:
                        update_fields.append("hsn_code = :hsn_code")
                        update_values["hsn_code"] = hsn_code
                    if part_no is not None:
                        update_fields.append("part_no = :part_no")
                        update_values["part_no"] = part_no
                    if gst_rate is not None:
                        update_fields.append("gst_rate = :gst_rate")
                        update_values["gst_rate"] = gst_rate
                    if is_gst_inclusive is not None:
                        update_fields.append("is_gst_inclusive = :is_gst_inclusive")
                        update_values["is_gst_inclusive"] = is_gst_inclusive
                    if unit_price is not None:
                        update_fields.append("unit_price = :unit_price")
                        update_values["unit_price"] = unit_price
                    if reorder_level is not None:
                        update_fields.append("reorder_level = :reorder_level")
                        update_values["reorder_level"] = reorder_level
                    if description is not None:
                        update_fields.append("description = :description")
                        update_values["description"] = description
                    if is_manufactured is not None:
                        update_fields.append("is_manufactured = :is_manufactured")
                        update_values["is_manufactured"] = is_manufactured
                    if drawings is not None:
                        update_fields.append("drawings = :drawings")
                        update_values["drawings"] = drawings
                    if update_fields:
                        update_sql = "UPDATE products SET " + ", ".join(update_fields) + " WHERE id = :product_id"
                        update_values["product_id"] = product_id
                        session.execute(text(update_sql), update_values)
                        session.execute(text("""
                            INSERT INTO audit_log (table_name, record_id, action, username, timestamp)
                            VALUES ('products', :product_id, 'UPDATE', 'system_user', :timestamp)
                        """), {"product_id": product_id, "timestamp": datetime.now()})
                        logger.info(f"Updated product fields for {name}")
                    existing_stock = session.execute(text("SELECT quantity FROM stock WHERE product_id = :product_id"), {"product_id": product_id}).fetchone()
                    if existing_stock:
                        current_quantity = existing_stock[0]
                        if import_mode == "add":
                            quantity += current_quantity
                            updated += 1
                            logger.info(f"Added to existing quantity for {name}: new quantity {quantity}")
                        else:
                            updated += 1
                            logger.info(f"Replacing existing stock for {name}")
                    else:
                        imported += 1
                        logger.info(f"No existing stock for {name}, inserting new")
                    session.execute(text("""
                        INSERT INTO stock (product_id, quantity, unit, last_updated)
                        VALUES (:product_id, :quantity, :unit, :last_updated)
                        ON CONFLICT DO NOTHING
                    """), {"product_id": product_id, "quantity": quantity, "unit": unit, "last_updated": datetime.now()})
                    session.execute(text("""
                        UPDATE stock SET quantity = :quantity, unit = :unit, last_updated = :last_updated
                        WHERE product_id = :product_id
                    """), {"product_id": product_id, "quantity": quantity, "unit": unit, "last_updated": datetime.now()})
                    session.execute(text("INSERT INTO audit_log (table_name, record_id, action, username, timestamp) VALUES ('stock', :product_id, :action, 'system_user', :timestamp)"),
                                  {"product_id": product_id, "action": f"IMPORT_{import_mode.upper()}", "timestamp": datetime.now()})
                    logger.info(f"Updated stock for {name}: quantity {quantity}")
                else:
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
                        is_manufactured=is_manufactured,
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
                    imported += 1
                    logger.info(f"Created new product: {name} (ID: {product_id})")
                session.execute(text("""
                    UPDATE stock SET quantity = :quantity, unit = :unit, last_updated = :last_updated
                    WHERE product_id = :product_id
                """), {"product_id": product_id, "quantity": quantity, "unit": unit, "last_updated": datetime.now()})
                session.execute(text("INSERT INTO audit_log (table_name, record_id, action, username, timestamp) VALUES ('stock', :product_id, :action, 'system_user', :timestamp)"),
                              {"product_id": product_id, "action": f"IMPORT_{import_mode.upper()}", "timestamp": datetime.now()})
                logger.info(f"Updated stock for {name}: quantity {quantity}")
            session.commit()
            logger.info("Import committed to database")
            if mismatched_units:
                msg = "The following items were skipped due to unit mismatch:\n" + "\n".join(mismatched_units)
                QMessageBox.warning(self.stock_ui, "Warning", msg)
            QMessageBox.information(self.stock_ui, "Import Complete", f"Imported {imported} new, updated {updated}")
            logger.info(f"Import complete: {imported} new, {updated} updated, {len(mismatched_units)} skipped")
            self.load_stock(show_zero=self.stock_ui.show_zero_chk.isChecked())
        except Exception as e:
            session.rollback()
            logger.error(f"Error importing stock: {e}")
            QMessageBox.critical(self.stock_ui, "Error", f"Failed to import stock: {e}")
        finally:
            session.close()

    def export_stock(self):
        file_path, _ = QFileDialog.getSaveFileName(self.stock_ui, "Export Stock", f"stock_export_{datetime.now().strftime('%Y%m%d_%H%M%S')}.xlsx", "Excel files (*.xlsx)")
        if not file_path:
            return
        session = Session()
        try:
            query = text("""
                SELECT p.name AS Name, COALESCE(s.quantity, 0) AS Quantity, p.unit AS Unit, p.gst_rate AS 'GST Rate', p.hsn_code AS 'HSN Code', p.part_no AS 'Part No', p.unit_price AS 'Unit Price', p.reorder_level AS 'Reorder Level', p.description AS Description, p.is_gst_inclusive AS 'Is GST Inclusive', p.is_manufactured AS 'Is Manufactured', p.drawings AS Drawings
                FROM products p LEFT JOIN stock s ON p.id = s.product_id
                ORDER BY p.name
            """)
            df = pd.read_sql_query(query, session.connection())
            df.to_excel(file_path, sheet_name="Sheet1", index=False)
            session.execute(text("INSERT INTO audit_log (table_name, record_id, action, username, timestamp) VALUES ('stock', 0, 'EXPORT', 'system_user', :timestamp)"),
                          {"timestamp": datetime.now()})
            session.commit()
            QMessageBox.information(self.stock_ui, "Success", f"Exported to {file_path}")
        except Exception as e:
            logger.error(f"Error exporting stock: {e}")
            QMessageBox.critical(self.stock_ui, "Error", f"Failed to export stock: {e}")
        finally:
            session.close()

    def download_sample(self):
        file_path, _ = QFileDialog.getSaveFileName(self.stock_ui, "Download Sample", "sample_stock.xlsx", "Excel files (*.xlsx)")
        if not file_path:
            return
        try:
            sample_data = pd.DataFrame({
                "Name": ["Sample Product"],
                "Quantity": [10],
                "Unit": ["Pcs"],
                "GST Rate": [18.0],
                "HSN Code": ["1234"],
                "Part No": ["ABC123"],
                "Unit Price": [100.0],
                "Reorder Level": [5],
                "Description": ["Sample description"],
                "Is GST Inclusive": ["Exclusive"],
                "Is Manufactured": [0],
                "Drawings": ["path/to/drawings"]
            })
            sample_data.to_excel(file_path, sheet_name="Sheet1", index=False)
            session = Session()
            session.execute(text("INSERT INTO audit_log (table_name, record_id, action, username, timestamp) VALUES ('stock', 0, 'SAMPLE_DOWNLOAD', 'system_user', :timestamp)"),
                          {"timestamp": datetime.now()})
            session.commit()
            QMessageBox.information(self.stock_ui, "Success", f"Sample saved to {file_path}")
        except Exception as e:
            session.rollback()
            logger.error(f"Error downloading sample: {e}")
            QMessageBox.critical(self.stock_ui, "Error", f"Failed to download sample: {e}")
        finally:
            session.close()

class EditStockDialog(QDialog):
    def __init__(self, parent=None, app=None, product_name=None, quantity=0, unit=None, product_id=None):
        super().__init__(parent)
        self.app = app
        self.product_name = product_name
        self.quantity = quantity
        self.unit = unit
        self.product_id = product_id
        self.setWindowTitle("Edit Stock")
        self.setFixedSize(400, 200)
        self.setup_ui()

    def setup_ui(self):
        layout = QVBoxLayout(self)
        layout.setContentsMargins(10, 10, 10, 10)
        layout.setSpacing(10)

        title_label = QLabel("Edit Stock", self)
        title_label.setStyleSheet("font-size: 14px; font-weight: bold; border: none; background-color: transparent;")
        title_label.setAlignment(Qt.AlignCenter)
        layout.addWidget(title_label)

        # Product
        product_row = QHBoxLayout()
        product_label = QLabel("Product", self)
        product_label.setStyleSheet("border: none; background-color: transparent;")
        product_label.setFixedWidth(100)
        product_entry = QLineEdit(self)
        product_entry.setText(self.product_name)
        product_entry.setReadOnly(True)
        product_entry.setFixedWidth(200)
        product_row.addWidget(product_label)
        product_row.addWidget(product_entry)
        layout.addLayout(product_row)

        # Quantity
        quantity_row = QHBoxLayout()
        quantity_label = QLabel("Quantity*", self)
        quantity_label.setStyleSheet("border: none; background-color: transparent;")
        quantity_label.setFixedWidth(100)
        self.quantity_entry = QLineEdit(self)
        self.quantity_entry.setText(str(self.quantity))
        self.quantity_entry.setFixedWidth(200)
        quantity_row.addWidget(quantity_label)
        quantity_row.addWidget(self.quantity_entry)
        layout.addLayout(quantity_row)

        # Unit
        unit_row = QHBoxLayout()
        unit_label = QLabel("Unit", self)
        unit_label.setStyleSheet("border: none; background-color: transparent;")
        unit_label.setFixedWidth(100)
        unit_entry = QLineEdit(self)
        unit_entry.setText(self.unit)
        unit_entry.setReadOnly(True)
        unit_entry.setFixedWidth(200)
        unit_row.addWidget(unit_label)
        unit_row.addWidget(unit_entry)
        layout.addLayout(unit_row)

        button_frame = QHBoxLayout()
        save_button = QPushButton("Save", self)
        save_button.setStyleSheet("padding: 5px 20px;")
        save_button.clicked.connect(self.save_stock)
        cancel_button = QPushButton("Cancel", self)
        cancel_button.setStyleSheet("padding: 5px 20px;")
        cancel_button.clicked.connect(self.reject)
        button_frame.addWidget(save_button)
        button_frame.addWidget(cancel_button)
        layout.addLayout(button_frame)

    def save_stock(self):
        session = Session()
        try:
            quantity = float(self.quantity_entry.text())
            if quantity < 0:
                raise ValueError("Quantity cannot be negative")
            # Check if exists
            existing = session.execute(text("SELECT id FROM stock WHERE product_id = :product_id"), {"product_id": self.product_id}).fetchone()
            if existing:
                session.execute(text("""
                    UPDATE stock SET quantity = :quantity, unit = :unit, last_updated = :last_updated
                    WHERE product_id = :product_id
                """), {"product_id": self.product_id, "quantity": quantity, "unit": self.unit, "last_updated": datetime.now()})
            else:
                session.execute(text("""
                    INSERT INTO stock (product_id, quantity, unit, last_updated)
                    VALUES (:product_id, :quantity, :unit, :last_updated)
                """), {"product_id": self.product_id, "quantity": quantity, "unit": self.unit, "last_updated": datetime.now()})
            session.execute(text("INSERT INTO audit_log (table_name, record_id, action, username, timestamp) VALUES ('stock', :product_id, 'UPDATE', 'system_user', :timestamp)"),
                          {"product_id": self.product_id, "timestamp": datetime.now()})
            session.commit()
            QMessageBox.information(self, "Success", "Stock updated successfully")
            self.accept()
        except (ValueError, Exception) as e:
            session.rollback()
            QMessageBox.critical(self, "Error", f"Failed to save stock: {e}")
        finally:
            session.close()

class ManualEntryDialog(QDialog):
    def __init__(self, parent=None, app=None):
        super().__init__(parent)
        self.app = app
        self.setWindowTitle("Manual Stock Entry")
        self.setFixedSize(400, 250)
        self.setup_ui()

    def setup_ui(self):
        layout = QVBoxLayout(self)
        layout.setContentsMargins(10, 10, 10, 10)
        layout.setSpacing(10)

        title_label = QLabel("Manual Stock Entry", self)
        title_label.setStyleSheet("font-size: 14px; font-weight: bold; border: none; background-color: transparent;")
        title_label.setAlignment(Qt.AlignCenter)
        layout.addWidget(title_label)

        # Product
        product_row = QHBoxLayout()
        product_label = QLabel("Product*", self)
        product_label.setStyleSheet("border: none; background-color: transparent;")
        product_label.setFixedWidth(100)
        self.product_combo = QComboBox(self)
        self.product_combo.setFixedWidth(180)
        self.load_products()
        self.product_combo.currentTextChanged.connect(self.update_unit)
        add_btn = QPushButton("+")
        add_btn.setFixedWidth(20)
        add_btn.clicked.connect(self.add_product)
        product_row.addWidget(product_label)
        product_row.addWidget(self.product_combo)
        product_row.addWidget(add_btn)
        layout.addLayout(product_row)

        # Quantity
        quantity_row = QHBoxLayout()
        quantity_label = QLabel("Quantity*", self)
        quantity_label.setStyleSheet("border: none; background-color: transparent;")
        quantity_label.setFixedWidth(100)
        self.quantity_entry = QLineEdit(self)
        self.quantity_entry.setFixedWidth(200)
        quantity_row.addWidget(quantity_label)
        quantity_row.addWidget(self.quantity_entry)
        layout.addLayout(quantity_row)

        # Unit
        unit_row = QHBoxLayout()
        unit_label = QLabel("Unit*", self)
        unit_label.setStyleSheet("border: none; background-color: transparent;")
        unit_label.setFixedWidth(100)
        self.unit_entry = QLineEdit(self)
        self.unit_entry.setReadOnly(True)
        self.unit_entry.setFixedWidth(200)
        unit_row.addWidget(unit_label)
        unit_row.addWidget(self.unit_entry)
        layout.addLayout(unit_row)

        button_frame = QHBoxLayout()
        save_button = QPushButton("Save", self)
        save_button.setStyleSheet("padding: 5px 20px;")
        save_button.clicked.connect(self.save_stock)
        cancel_button = QPushButton("Cancel", self)
        cancel_button.setStyleSheet("padding: 5px 20px;")
        cancel_button.clicked.connect(self.reject)
        button_frame.addWidget(save_button)
        button_frame.addWidget(cancel_button)
        layout.addLayout(button_frame)

    def load_products(self):
        session = Session()
        try:
            result = session.execute(text("SELECT name FROM products ORDER BY name")).fetchall()
            products = [row[0] for row in result]
            self.product_combo.clear()
            self.product_combo.addItems(products)
        except Exception as e:
            logger.error(f"Failed to load products: {e}")
            QMessageBox.critical(self, "Error", f"Failed to load products: {e}")
        finally:
            session.close()

    def update_unit(self, product_name):
        if not product_name:
            self.unit_entry.setText("")
            return
        session = Session()
        try:
            unit = session.execute(text("SELECT unit FROM products WHERE name = :product_name"), {"product_name": product_name}).fetchone()
            self.unit_entry.setText(unit[0] if unit else "")
        except Exception as e:
            logger.error(f"Failed to update unit: {e}")
            self.unit_entry.setText("")
            QMessageBox.critical(self, "Error", f"Failed to update unit: {e}")
        finally:
            session.close()

    def add_product(self):
        add_product(self.app, parent=self, callback=lambda *_: self.load_products())

    def save_stock(self):
        product_name = self.product_combo.currentText()
        if not product_name:
            QMessageBox.critical(self, "Error", "Product is required")
            return
        session = Session()
        try:
            quantity = float(self.quantity_entry.text())
            unit = self.unit_entry.text()
            if quantity < 0:
                raise ValueError("Quantity cannot be negative")
            product_id = session.execute(text("SELECT id FROM products WHERE name = :product_name"), {"product_name": product_name}).fetchone()[0]
            # Check if exists
            existing = session.execute(text("SELECT id FROM stock WHERE product_id = :product_id"), {"product_id": product_id}).fetchone()
            if existing:
                session.execute(text("""
                    UPDATE stock SET quantity = :quantity, unit = :unit, last_updated = :last_updated
                    WHERE product_id = :product_id
                """), {"product_id": product_id, "quantity": quantity, "unit": unit, "last_updated": datetime.now()})
            else:
                session.execute(text("""
                    INSERT INTO stock (product_id, quantity, unit, last_updated)
                    VALUES (:product_id, :quantity, :unit, :last_updated)
                """), {"product_id": product_id, "quantity": quantity, "unit": unit, "last_updated": datetime.now()})
            session.execute(text("INSERT INTO audit_log (table_name, record_id, action, username, timestamp) VALUES ('stock', :product_id, 'UPSERT', 'system_user', :timestamp)"),
                          {"product_id": product_id, "timestamp": datetime.now()})
            session.commit()
            QMessageBox.information(self, "Success", "Stock saved successfully")
            self.accept()
        except (ValueError, Exception) as e:
            session.rollback()
            QMessageBox.critical(self, "Error", f"Failed to save stock: {e}")
        finally:
            session.close()