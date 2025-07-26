# src/erp/logic/manufacturing_logic.py
# Converted to SQLAlchemy.

import logging
from datetime import datetime
from PySide6.QtWidgets import QMessageBox, QTableWidgetItem
from sqlalchemy import text
from src.erp.logic.database.session import engine, Session
from src.core.config import get_database_url
from src.erp.logic.utils.utils import add_unit, filter_combobox

logger = logging.getLogger(__name__)

class ManufacturingLogic:
    def __init__(self, app):
        self.app = app
        self.manufacturing_ui = None
        self.bom_ui = None
        self.work_order_ui = None
        self.close_work_order_ui = None

    def set_manufacturing_ui(self, ui):
        self.manufacturing_ui = ui
        self.load_manufacturing_data()

    def set_bom_ui(self, ui):
        self.bom_ui = ui
        self.load_manufactured_products()
        self.load_components()

    def set_work_order_ui(self, ui):
        self.work_order_ui = ui
        self.load_boms()

    def set_close_work_order_ui(self, ui):
        self.close_work_order_ui = ui
        self.load_open_work_orders()

    def load_manufacturing_data(self):
        session = Session()
        try:
            result = session.execute(text("""
                SELECT b.id, p.name, b.created_at FROM bom b JOIN products p ON b.manufactured_product_id = p.id
            """)).fetchall()
            if self.manufacturing_ui and hasattr(self.manufacturing_ui, 'bom_table'):
                self.manufacturing_ui.bom_table.setRowCount(0)
                for row_idx, row_data in enumerate(result):
                    self.manufacturing_ui.bom_table.insertRow(row_idx)
                    for col_idx, value in enumerate(row_data):
                        self.manufacturing_ui.bom_table.setItem(row_idx, col_idx, QTableWidgetItem(str(value)))
            logger.debug(f"Loaded {len(result)} BOM records")
        except Exception as e:
            logger.error(f"Failed to load manufacturing data: {e}")
            if self.manufacturing_ui:
                QMessageBox.critical(self.manufacturing_ui, "Error", f"Failed to load manufacturing data: {e}")
        finally:
            session.close()

    def load_manufactured_products(self):
        session = Session()
        try:
            result = session.execute(text("SELECT name FROM products WHERE is_manufactured = 1 ORDER BY name")).fetchall()
            products = [row[0] for row in result]
            logger.info(f"Loaded {len(products)} manufactured products")
            self.bom_ui.product_combo.clear()
            self.bom_ui.product_combo.addItems(products if products else ["No manufactured products available"])
            if products:
                self.bom_ui.product_combo.setCurrentText(products[0])
            else:
                logger.warning("No manufactured products found in database")
        except Exception as e:
            logger.error(f"Failed to load manufactured products: {e}")
            QMessageBox.critical(self.bom_ui, "Error", f"Failed to load products: {e}")
            self.bom_ui.product_combo.addItems(["Error loading products"])
            self.bom_ui.product_combo.setCurrentText("Error loading products")
        finally:
            session.close()

        self.bom_ui.product_combo.textActivated.connect(lambda: filter_combobox(self.bom_ui.product_combo))

    def load_components(self):
        session = Session()
        try:
            result = session.execute(text("SELECT name FROM products WHERE is_manufactured = 0 ORDER BY name")).fetchall()
            components = [row[0] for row in result]
            self.bom_ui.component_combo.clear()
            self.bom_ui.component_combo.addItems(components if components else [""])
            if components:
                self.bom_ui.component_combo.setCurrentText(components[0])
        except Exception as e:
            logger.error(f"Failed to load components: {e}")
            QMessageBox.critical(self.bom_ui, "Error", f"Failed to load components: {e}")
        finally:
            session.close()

        self.bom_ui.component_combo.textActivated.connect(lambda: filter_combobox(self.bom_ui.component_combo))

    def load_boms(self):
        session = Session()
        try:
            result = session.execute(text("SELECT b.id, p.name FROM bom b JOIN products p ON b.manufactured_product_id = p.id ORDER BY p.name")).fetchall()
            boms = [f"{row[0]} ({row[1]})" for row in result]
            self.work_order_ui.bom_combo.clear()
            self.work_order_ui.bom_combo.addItems(boms if boms else [""])
            if boms:
                self.work_order_ui.bom_combo.setCurrentText(boms[0])
        except Exception as e:
            logger.error(f"Failed to load BOMs: {e}")
            QMessageBox.critical(self.work_order_ui, "Error", f"Failed to load BOMs: {e}")
        finally:
            session.close()

        self.work_order_ui.bom_combo.textActivated.connect(lambda: filter_combobox(self.work_order_ui.bom_combo))

    def load_open_work_orders(self):
        session = Session()
        try:
            result = session.execute(text("""
                SELECT w.id, p.name, w.quantity
                FROM work_orders w
                JOIN bom b ON w.bom_id = b.id
                JOIN products p ON b.manufactured_product_id = p.id
                WHERE w.status = 'Open'
                ORDER BY w.id
            """)).fetchall()
            work_orders = [f"ID {row[0]}: {row[1]} ({row[2]} units)" for row in result]
            self.close_work_order_ui.work_order_combo.clear()
            self.close_work_order_ui.work_order_combo.addItems(work_orders if work_orders else [""])
            if work_orders:
                self.close_work_order_ui.work_order_combo.setCurrentText(work_orders[0])
        except Exception as e:
            logger.error(f"Failed to load open work orders: {e}")
            QMessageBox.critical(self.close_work_order_ui, "Error", f"Failed to load work orders: {e}")
        finally:
            session.close()

        self.close_work_order_ui.work_order_combo.textActivated.connect(lambda: filter_combobox(self.close_work_order_ui.work_order_combo))

    def add_manufactured_product(self):
        if hasattr(self.app, 'add_window_open') and self.app.add_window_open:
            if hasattr(self.app, 'add_window') and self.app.add_window:
                self.app.add_window.raise_()
            return
        dialog = AddManufacturedProductDialog(self.bom_ui, self.app)
        self.app.add_window = dialog
        self.app.add_window_open = True
        dialog.exec()

    def save_product(self):
        dialog = self.app.add_window
        name = dialog.entries["Name*"].text()
        unit = dialog.entries["Unit*"].currentText()
        description = dialog.entries["Description"].text()

        if not name or not unit:
            QMessageBox.critical(dialog, "Error", "Name and Unit are required")
            return

        session = Session()
        try:
            insert_stmt = insert(Base.metadata.tables['products']).values(
                name=name,
                unit_price=0,
                unit=unit,
                description=description or None,
                is_manufactured=1,
                gst_rate=0,
                is_gst_inclusive='Exclusive',
                reorder_level=0
            ).returning(Base.metadata.tables['products'].c.id)
            result = session.execute(insert_stmt)
            product_id = result.fetchone()[0]
            add_unit(unit)
            session.execute(text("INSERT INTO audit_log (table_name, record_id, action, user, timestamp) VALUES ('products', :product_id, 'INSERT', 'system_user', :timestamp)"),
                          {"product_id": product_id, "timestamp": datetime.now()})
            session.commit()
            QMessageBox.information(dialog, "Success", "Manufactured product added")
            self.load_manufactured_products()
            dialog.accept()
            self.app.add_window = None
            self.app.add_window_open = False
        except Exception as e:
            session.rollback()
            logger.error(f"Failed to add manufactured product: {e}")
            QMessageBox.critical(dialog, "Error", f"Failed to add product: {e}")
        finally:
            session.close()

    def add_component(self):
        component = self.bom_ui.component_combo.currentText()
        try:
            qty = int(self.bom_ui.quantity_input.text())
            if not component or qty <= 0:
                QMessageBox.critical(self.bom_ui, "Error", "Select a component and enter a positive quantity")
                return
            row_count = self.bom_ui.component_table.rowCount()
            self.bom_ui.component_table.insertRow(row_count)
            self.bom_ui.component_table.setItem(row_count, 0, QTableWidgetItem(component))
            self.bom_ui.component_table.setItem(row_count, 1, QTableWidgetItem(str(qty)))
            self.bom_ui.quantity_input.setText("1")
            if self.bom_ui.component_combo.count() > 0:
                self.bom_ui.component_combo.setCurrentIndex(0)
        except ValueError:
            QMessageBox.critical(self.bom_ui, "Error", "Quantity must be an integer")

    def remove_component(self):
        selected = self.bom_ui.component_table.selectedIndexes()
        if selected:
            self.bom_ui.component_table.removeRow(selected[0].row())

    def save_bom(self):
        product = self.bom_ui.product_combo.currentText()
        if not product or self.bom_ui.component_table.rowCount() == 0:
            QMessageBox.critical(self.bom_ui, "Error", "Select a manufactured product and add at least one component")
            return

        session = Session()
        try:
            result = session.execute(text("SELECT id FROM products WHERE name = :product AND is_manufactured = 1"), {"product": product}).fetchone()
            if not result:
                QMessageBox.critical(self.bom_ui, "Error", "Invalid manufactured product")
                return
            product_id = result[0]

            insert_stmt = insert(Base.metadata.tables['bom']).values(
                manufactured_product_id=product_id,
                created_at=datetime.now()
            ).returning(Base.metadata.tables['bom'].c.id)
            result = session.execute(insert_stmt)
            bom_id = result.fetchone()[0]

            for row in range(self.bom_ui.component_table.rowCount()):
                comp_name = self.bom_ui.component_table.item(row, 0).text()
                qty = int(self.bom_ui.component_table.item(row, 1).text())
                comp_result = session.execute(text("SELECT id FROM products WHERE name = :comp_name AND is_manufactured = 0"), {"comp_name": comp_name}).fetchone()
                if comp_result:
                    comp_id = comp_result[0]
                    session.execute(insert(Base.metadata.tables['bom_components']).values(
                        bom_id=bom_id,
                        component_id=comp_id,
                        quantity=qty
                    ))
            session.execute(text("INSERT INTO audit_log (table_name, record_id, action, user, timestamp) VALUES ('bom', :bom_id, 'INSERT', 'system_user', :timestamp)"),
                          {"bom_id": bom_id, "timestamp": datetime.now()})
            session.commit()
            QMessageBox.information(self.bom_ui, "Success", "BOM created successfully")
            self.clear_bom()
            if hasattr(self.app, 'work_order_ui') and self.app.work_order_ui:
                self.load_boms()
        except Exception as e:
            session.rollback()
            logger.error(f"Failed to save BOM: {e}")
            QMessageBox.critical(self.bom_ui, "Error", f"Failed to save BOM: {e}")
        finally:
            session.close()

    def clear_bom(self):
        if self.bom_ui.product_combo.count() > 0:
            self.bom_ui.product_combo.setCurrentIndex(0)
        self.bom_ui.component_table.setRowCount(0)
        self.bom_ui.quantity_input.setText("1")

    def save_work_order(self):
        bom = self.work_order_ui.bom_combo.currentText()
        try:
            work_order_quantity = int(self.work_order_ui.quantity_input.text())
            if not bom or work_order_quantity <= 0:
                QMessageBox.critical(self.work_order_ui, "Error", "Select a valid BOM and positive quantity")
                return
            bom_id = int(bom.split('(')[0].strip())
            session = Session()
            components = session.execute(text("""
                SELECT bc.component_id, bc.quantity, p.name, p.unit
                FROM bom_components bc
                JOIN products p ON bc.component_id = p.id
                WHERE bc.bom_id = :bom_id
            """), {"bom_id": bom_id}).fetchall()
            if not components:
                QMessageBox.critical(self.work_order_ui, "Error", "No components found for selected BOM")
                return

            insufficient = []
            for component_id, comp_quantity, comp_name, _ in components:
                required_quantity = int(comp_quantity * work_order_quantity)
                stock_result = session.execute(text("SELECT quantity FROM stock WHERE product_id = :component_id"), {"component_id": component_id}).fetchone()
                available_quantity = stock_result[0] if stock_result else 0
                if available_quantity < required_quantity:
                    insufficient.append(f"{comp_name}: Need {required_quantity}, Available {available_quantity}")
            if insufficient:
                QMessageBox.critical(self.work_order_ui, "Insufficient Stock", "\n".join(insufficient))
                return

            current_time = datetime.now()
            fiscal_year = datetime.now().strftime("%Y-%Y")
            doc_number = self.get_next_doc_number(session, "WO_OUT", fiscal_year)
            for component_id, comp_quantity, _, unit in components:
                required_quantity = int(comp_quantity * work_order_quantity)
                stock_result = session.execute(text("SELECT id, quantity FROM stock WHERE product_id = :component_id"), {"component_id": component_id}).fetchone()
                new_quantity = stock_result[1] - required_quantity
                session.execute(text("UPDATE stock SET quantity = :new_quantity, last_updated = :current_time WHERE id = :stock_id"),
                              {"new_quantity": new_quantity, "current_time": current_time, "stock_id": stock_result[0]})
                session.execute(insert(Base.metadata.tables['material_transactions']).values(
                    doc_number=doc_number,
                    type='Out',
                    date=current_time,
                    product_id=component_id,
                    quantity=required_quantity,
                    purpose='Work Order',
                    remarks=f'Work Order BOM ID {bom_id}'
                ))

            insert_stmt = insert(Base.metadata.tables['work_orders']).values(
                bom_id=bom_id,
                quantity=work_order_quantity,
                created_at=current_time
            ).returning(Base.metadata.tables['work_orders'].c.id)
            result = session.execute(insert_stmt)
            work_order_id = result.fetchone()[0]
            session.execute(text("INSERT INTO audit_log (table_name, record_id, action, user, timestamp) VALUES ('work_orders', :work_order_id, 'INSERT', 'system_user', :current_time)"),
                          {"work_order_id": work_order_id, "current_time": current_time})
            session.commit()
            QMessageBox.information(self.work_order_ui, "Success", "Work Order created successfully")
            self.clear_work_order()
            if hasattr(self.app, 'close_work_order_ui') and self.app.close_work_order_ui:
                self.load_open_work_orders()
        except ValueError:
            QMessageBox.critical(self.work_order_ui, "Error", "Quantity must be an integer")
        except Exception as e:
            session.rollback()
            logger.error(f"Failed to save work order: {e}")
            QMessageBox.critical(self.work_order_ui, "Error", f"Failed to save work order: {e}")
        finally:
            session.close()

    def get_next_doc_number(self, session, doc_type, fiscal_year):
        result = session.execute(text("SELECT last_sequence FROM doc_sequences WHERE doc_type = :doc_type AND fiscal_year = :fiscal_year"),
                               {"doc_type": doc_type, "fiscal_year": fiscal_year}).fetchone()
        if result:
            sequence = result[0] + 1
            session.execute(text("UPDATE doc_sequences SET last_sequence = :sequence WHERE doc_type = :doc_type AND fiscal_year = :fiscal_year"),
                          {"sequence": sequence, "doc_type": doc_type, "fiscal_year": fiscal_year})
        else:
            sequence = 1
            session.execute(text("INSERT INTO doc_sequences (doc_type, fiscal_year, last_sequence) VALUES (:doc_type, :fiscal_year, :sequence)"),
                          {"doc_type": doc_type, "fiscal_year": fiscal_year, "sequence": sequence})
        return f"{doc_type}/{fiscal_year}/{sequence:04d}"

    def clear_work_order(self):
        if self.work_order_ui.bom_combo.count() > 0:
            self.work_order_ui.bom_combo.setCurrentIndex(0)
        self.work_order_ui.quantity_input.setText("1")

    def close_selected_work_order(self):
        work_order = self.close_work_order_ui.work_order_combo.currentText()
        if not work_order:
            QMessageBox.critical(self.close_work_order_ui, "Error", "No work order selected")
            return
        try:
            work_order_id = int(work_order.split(':')[0].replace('ID', '').strip())
            session = Session()
            result = session.execute(text("""
                SELECT w.quantity, b.manufactured_product_id, p.unit
                FROM work_orders w
                JOIN bom b ON w.bom_id = b.id
                JOIN products p ON b.manufactured_product_id = p.id
                WHERE w.id = :work_order_id
            """), {"work_order_id": work_order_id}).fetchone()
            if not result:
                QMessageBox.critical(self.close_work_order_ui, "Error", "Invalid work order")
                return
            quantity, product_id, unit = result

            stock_result = session.execute(text("SELECT id, quantity FROM stock WHERE product_id = :product_id"), {"product_id": product_id}).fetchone()
            current_time = datetime.now()
            if stock_result:
                new_quantity = stock_result[1] + quantity
                session.execute(text("UPDATE stock SET quantity = :new_quantity, last_updated = :current_time WHERE id = :stock_id"),
                              {"new_quantity": new_quantity, "current_time": current_time, "stock_id": stock_result[0]})
            else:
                session.execute(insert(Base.metadata.tables['stock']).values(
                    product_id=product_id,
                    quantity=quantity,
                    unit=unit,
                    last_updated=current_time
                ))

            session.execute(text("UPDATE work_orders SET status = 'Closed', closed_at = :current_time WHERE id = :work_order_id"),
                          {"current_time": current_time, "work_order_id": work_order_id})
            session.execute(text("INSERT INTO audit_log (table_name, record_id, action, user, timestamp) VALUES ('work_orders', :work_order_id, 'UPDATE', 'system_user', :current_time)"),
                          {"work_order_id": work_order_id, "current_time": current_time})
            session.commit()
            QMessageBox.information(self.close_work_order_ui, "Success", "Work Order closed successfully")
            self.load_open_work_orders()
        except Exception as e:
            session.rollback()
            logger.error(f"Failed to close work order: {e}")
            QMessageBox.critical(self.close_work_order_ui, "Error", f"Failed to close work order: {e}")
        finally:
            session.close()