# src/erp/voucher/column_management.py
# Converted to use SQLAlchemy.

from PySide6.QtWidgets import QDialog, QVBoxLayout, QHBoxLayout, QLabel, QComboBox, QPushButton, QCheckBox, QTreeWidget, QTreeWidgetItem, QMessageBox
from PySide6.QtCore import Qt, Signal
from PySide6.QtGui import QFont
import logging
from sqlalchemy import text
from src.erp.logic.database.session import engine, Session
from src.erp.logic.database.voucher import get_voucher_columns, add_voucher_column, delete_voucher_column
from src.erp.logic.utils.utils import filter_combobox, suggest_data_type, suggest_calculation_logic, LEDGER_COLUMNS
from src.core.config import get_database_url, get_log_path

logging.basicConfig(filename=get_log_path(), level=logging.DEBUG, format='%(asctime)s - %(name)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

class ReorderTreeWidget(QTreeWidget):
    itemDropped = Signal()

    def dropEvent(self, event):
        super().dropEvent(event)
        self.itemDropped.emit()

class ColumnManagement:
    def __init__(self, app):
        self.app = app
        self.form_columns = ["Voucher Number", "Date", "Delivery Date", "Customer", "Vendor", "Payment Terms"]

    def add_column_dialog(self, parent, voucher_type_id):
        if not voucher_type_id:
            QMessageBox.critical(parent, "Error", "No voucher type selected")
            return
        try:
            dialog = AddColumnDialog(parent, voucher_type_id, lambda: self.app.frames["voucher_management"].refresh_voucher_content())
            dialog.exec()
        except Exception as e:
            logger.error(f"Error opening add_column_dialog for voucher_type_id {voucher_type_id}: {e}")
            QMessageBox.critical(parent, "Error", f"Failed to open column dialog: {e}")

    def manage_columns(self, parent, voucher_name):
        session = Session()
        try:
            voucher_type_id = session.execute(text("SELECT id FROM voucher_types WHERE voucher_name = :voucher_name"), {"voucher_name": voucher_name}).fetchone()
            if not voucher_type_id:
                logger.error(f"Voucher type '{voucher_name}' not found")
                QMessageBox.critical(parent, "Error", f"Voucher type '{voucher_name}' not found")
                return
            voucher_type_id = voucher_type_id[0]
            self.add_column_dialog(parent, voucher_type_id)
        except Exception as e:
            logger.error(f"Database error fetching voucher type '{voucher_name}': {e}")
            QMessageBox.critical(parent, "Error", f"Database error: {e}")
        finally:
            session.close()

class AddColumnDialog(QDialog):
    def __init__(self, parent, voucher_type_id, callback):
        super().__init__(parent)
        self.voucher_type_id = voucher_type_id
        self.callback = callback
        self.setWindowTitle("Manage Voucher Columns")
        self.setFixedSize(600, 550)
        self.setModal(True)
        self.column_ids = {}
        self.init_ui()

    def init_ui(self):
        layout = QVBoxLayout(self)

        # Title
        layout.addWidget(QLabel("Manage Voucher Columns", font=QFont("Helvetica", 14)))

        # Tree widget for columns
        self.columns_tree = ReorderTreeWidget()
        self.columns_tree.setHeaderLabels(["Column Name", "Mandatory", "Calculated"])
        self.columns_tree.setColumnWidth(0, 200)
        self.columns_tree.setColumnWidth(1, 100)
        self.columns_tree.setColumnWidth(2, 100)
        self.columns_tree.setDragDropMode(QTreeWidget.InternalMove)
        self.columns_tree.itemDropped.connect(self.handle_drop)
        layout.addWidget(self.columns_tree)

        # Input frame
        input_layout = QHBoxLayout()
        dropdown_layout = QHBoxLayout()
        dropdown_layout.addWidget(QLabel("Select New Column:"))
        self.column_name_combo = QComboBox()
        available_columns = [col for col in LEDGER_COLUMNS if col not in [c[1] for c in get_voucher_columns(self.voucher_type_id)]]
        self.column_name_combo.addItems(available_columns)
        self.column_name_combo.setEditable(True)
        self.column_name_combo.editTextChanged.connect(lambda text: filter_combobox(text, self.column_name_combo, available_columns))
        dropdown_layout.addWidget(self.column_name_combo)
        add_button = QPushButton("Add Column")
        add_button.clicked.connect(self.save_column)
        dropdown_layout.addWidget(add_button)
        input_layout.addLayout(dropdown_layout)

        checkboxes_layout = QVBoxLayout()
        self.mandatory_check = QCheckBox("Mandatory")
        self.calculated_check = QCheckBox("Calculated Field")
        checkboxes_layout.addWidget(self.mandatory_check)
        checkboxes_layout.addWidget(self.calculated_check)
        input_layout.addLayout(checkboxes_layout)
        layout.addLayout(input_layout)

        # Buttons
        button_layout = QHBoxLayout()
        delete_button = QPushButton("Delete Selected Column")
        delete_button.clicked.connect(self.delete_column)
        cancel_button = QPushButton("Cancel")
        cancel_button.clicked.connect(self.reject)
        button_layout.addWidget(delete_button)
        button_layout.addWidget(cancel_button)
        layout.addLayout(button_layout)

        self.column_name_combo.currentTextChanged.connect(self.update_fields)
        self.load_columns()

    def load_columns(self):
        session = Session()
        try:
            self.columns_tree.clear()
            columns = get_voucher_columns(self.voucher_type_id)
            logger.debug(f"Loaded columns for voucher_type_id {self.voucher_type_id}: {columns}")
            if not columns:
                QMessageBox.information(self, "Info", "No columns exist for this voucher type. Add new columns below.")
            for col in sorted(columns, key=lambda x: x[3]):
                col_id, name, data_type, mandatory, order, is_calculated, calc_logic = col
                item = QTreeWidgetItem([name, "Yes" if mandatory else "No", "Yes" if is_calculated else "No"])
                self.columns_tree.addTopLevelItem(item)
                self.column_ids[name] = col_id
        except Exception as e:
            logger.error(f"Unexpected error loading columns: {e}")
            QMessageBox.critical(self, "Error", f"Failed to load columns: {e}")
            self.reject()
        finally:
            session.close()

    def update_fields(self):
        try:
            column_name = self.column_name_combo.currentText().strip()
            if column_name:
                calc_logic, is_calculated = suggest_calculation_logic(column_name)
                self.calculated_check.setChecked(is_calculated)
                self.mandatory_check.setEnabled(not is_calculated)
        except Exception as e:
            logger.error(f"Error updating column fields: {e}")

    def save_column(self):
        session = Session()
        try:
            column_name = self.column_name_combo.currentText().strip()
            if not column_name:
                QMessageBox.critical(self, "Error", "Column Name is required")
                return
            if column_name in [c[1] for c in get_voucher_columns(self.voucher_type_id)]:
                QMessageBox.critical(self, "Error", f"Column '{column_name}' already exists")
                return

            is_mandatory = 1 if self.mandatory_check.isChecked() else 0
            is_calculated = 1 if self.calculated_check.isChecked() else 0
            data_type = suggest_data_type(column_name)
            calc_logic, _ = suggest_calculation_logic(column_name) if is_calculated else (None, False)
            calc_logic_json = json.dumps(calc_logic) if calc_logic else None
            display_order = len(get_voucher_columns(self.voucher_type_id)) + 1
            column_id = add_voucher_column(self.voucher_type_id, column_name, data_type, is_mandatory, display_order, is_calculated, calc_logic_json)
            if column_id:
                QMessageBox.information(self, "Success", f"Column '{column_name}' added successfully")
                self.load_columns()
                self.callback()
                self.column_name_combo.setCurrentText("")
                self.mandatory_check.setChecked(False)
                self.calculated_check.setChecked(False)
                available_columns = [col for col in LEDGER_COLUMNS if col not in [c[1] for c in get_voucher_columns(self.voucher_type_id)]]
                self.column_name_combo.clear()
                self.column_name_combo.addItems(available_columns)
                logger.info(f"Added column '{column_name}' with ID {column_id}")
            else:
                QMessageBox.critical(self, "Error", "Failed to add column")
        except Exception as e:
            logger.error(f"Error adding column {column_name}: {e}")
            QMessageBox.critical(self, "Error", f"Failed to add column: {e}")
        finally:
            session.close()

    def delete_column(self):
        session = Session()
        try:
            selected = self.columns_tree.currentItem()
            if not selected:
                QMessageBox.warning(self, "Warning", "Please select a column to delete")
                return
            col_name = selected.text(0)
            col_id = self.column_ids.get(col_name)
            if not col_id:
                QMessageBox.critical(self, "Error", f"No column ID found for {col_name}")
                return
            if QMessageBox.question(self, "Confirm", f"Are you sure you want to delete column '{col_name}'?") == QMessageBox.Yes:
                if delete_voucher_column(col_id):
                    self.load_columns()
                    self.callback()
                    available_columns = [col for col in LEDGER_COLUMNS if col not in [c[1] for c in get_voucher_columns(self.voucher_type_id)]]
                    self.column_name_combo.clear()
                    self.column_name_combo.addItems(available_columns)
                    logger.info(f"Deleted column ID {col_id}: {col_name}")
                else:
                    QMessageBox.critical(self, "Error", f"Failed to delete column '{col_name}'")
        except Exception as e:
            logger.error(f"Failed to delete column {col_name}: {e}")
            QMessageBox.critical(self, "Error", f"Failed to delete column: {e}")
        finally:
            session.close()

    def handle_drop(self):
        session = Session()
        try:
            items = [self.columns_tree.topLevelItem(i) for i in range(self.columns_tree.topLevelItemCount())]
            selected_item = self.columns_tree.currentItem()
            selected_index = items.index(selected_item)
            target_index = self.columns_tree.indexOfTopLevelItem(selected_item)
            if selected_index == target_index:
                return
            col_name = selected_item.text(0)
            col_id = self.column_ids.get(col_name)
            if not col_id:
                logger.error(f"No column ID found for {col_name}")
                QMessageBox.critical(self, "Error", f"Column ID not found for {col_name}")
                return
            columns = get_voucher_columns(self.voucher_type_id)
            columns = sorted(columns, key=lambda x: x[3])
            col_data = columns[selected_index]
            columns.pop(selected_index)
            columns.insert(target_index, col_data)
            for idx, col in enumerate(columns):
                session.execute(text("UPDATE voucher_columns SET display_order = :display_order WHERE id = :col_id"), {"display_order": idx + 1, "col_id": col[0]})
            session.commit()
            self.load_columns()
            self.callback()
            logger.debug(f"Dropped {col_name} at index {target_index}")
        except Exception as e:
            session.rollback()
            logger.error(f"Unexpected error reordering columns: {e}")
            QMessageBox.critical(self, "Error", f"Failed to reorder columns: {e}")
        finally:
            session.close()