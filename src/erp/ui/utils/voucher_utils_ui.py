# src/ui/utils/voucher_utils_ui.py
from PySide6.QtWidgets import QDialog, QVBoxLayout, QLabel, QComboBox, QPushButton, QTreeWidget, QTreeWidgetItem, QHeaderView, QMessageBox
from PySide6.QtCore import Qt
import logging
from src.logic.config import get_log_path
from src.logic.utils.voucher_utils import get_voucher_types, create_voucher_type
from src.logic.database.voucher import get_voucher_columns, delete_voucher_column

logging.basicConfig(filename=get_log_path(), level=logging.DEBUG, format='%(asctime)s - %(name)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

def show_custom_voucher_dialog(app, default_voucher_id: int, module_name: str, main_combo_callback=None) -> None:
    """Displays a dialog to manage voucher types and their columns."""
    logger.info(f"Opening show_custom_voucher_dialog for module: {module_name}, default_voucher_id: {default_voucher_id}")
    try:
        dialog = QDialog(app)
        dialog.setWindowTitle("Manage Voucher Types")
        dialog.setFixedSize(650, 500)
        dialog.setWindowModality(Qt.ApplicationModal)
        
        layout = QVBoxLayout(dialog)
        
        title_label = QLabel("Select or Create Voucher Type")
        title_label.setStyleSheet("font-size: 14px; font-weight: bold;")
        layout.addWidget(title_label)
        
        voucher_types = get_voucher_types(module_name)
        selected_voucher_type = QComboBox()
        selected_voucher_type.addItems([v[1] for v in voucher_types])
        layout.addWidget(selected_voucher_type)
        
        def update_voucher_types():
            """Updates the voucher types combobox."""
            nonlocal voucher_types
            try:
                voucher_types = get_voucher_types(module_name)
                selected_voucher_type.clear()
                selected_voucher_type.addItems([v[1] for v in voucher_types])
                if voucher_types:
                    selected_voucher_type.setCurrentText(voucher_types[-1][1])
                    load_columns(voucher_types[-1][0])
                logger.debug("Updated voucher types combobox")
            except Exception as e:
                logger.error(f"Error updating voucher types: {e}")
                QMessageBox.critical(dialog, "Error", f"Failed to update voucher types: {e}")
        
        def on_voucher_type_select():
            """Handles voucher type selection from QComboBox."""
            try:
                selected_name = selected_voucher_type.currentText()
                selected_voucher = next((v for v in voucher_types if v[1] == selected_name), None)
                if selected_voucher:
                    load_columns(selected_voucher[0])
                    logger.debug(f"Selected voucher type: {selected_name}")
            except Exception as e:
                logger.error(f"Error selecting voucher type: {e}")
                QMessageBox.critical(dialog, "Error", f"Failed to select voucher type: {e}")
        
        selected_voucher_type.currentTextChanged.connect(on_voucher_type_select)
        
        create_button = QPushButton("Create New Voucher Type")
        create_button.clicked.connect(lambda: create_custom_voucher_type(app, dialog, default_voucher_id, module_name, selected_voucher_type, update_voucher_types, main_combo_callback))
        layout.addWidget(create_button)
        
        columns_tree = QTreeWidget()
        columns_tree.setHeaderLabels(["ID", "Column Name", "Data Type", "Mandatory", "Display Order", "Calculated"])
        columns_tree.header().setSectionResizeMode(QHeaderView.ResizeToContents)
        columns_tree.setSelectionMode(QTreeWidget.SingleSelection)
        layout.addWidget(columns_tree)
        
        def load_columns(voucher_type_id: int):
            """Loads columns for the selected voucher type into the QTreeWidget."""
            try:
                columns_tree.clear()
                columns = get_voucher_columns(voucher_type_id)
                logger.debug(f"Loaded columns for voucher_type_id {voucher_type_id}: {columns}")
                if not columns:
                    QMessageBox.information(dialog, "Info", "No columns exist for this voucher type. Add new columns below.")
                for col in sorted(columns, key=lambda x: x[3]):  # Sort by display_order
                    col_id, name, data_type, mandatory, order, is_calculated, calc_logic = col
                    item = QTreeWidgetItem([str(col_id), name, data_type, "Yes" if mandatory else "No", str(order), "Yes" if is_calculated else "No"])
                    columns_tree.addTopLevelItem(item)
            except sqlite3.Error as e:
                logger.error(f"Database error loading columns: {e}")
                QMessageBox.critical(dialog, "Error", f"Database error: {e}")
            except Exception as e:
                logger.error(f"Unexpected error loading columns: {e}")
                QMessageBox.critical(dialog, "Error", f"Failed to load columns: {e}")
        
        def add_column():
            """Opens the add column dialog for the selected voucher type."""
            try:
                selected_name = selected_voucher_type.currentText()
                selected_voucher = next((v for v in voucher_types if v[1] == selected_name), None)
                if not selected_voucher:
                    QMessageBox.warning(dialog, "Warning", "Please select a voucher type")
                else:
                    from src.erp.voucher_management.column_management import add_column_dialog
                    add_column_dialog(dialog, selected_voucher[0], lambda: load_columns(selected_voucher[0]))
            except Exception as e:
                logger.error(f"Error opening add column dialog: {e}")
                QMessageBox.critical(dialog, "Error", f"Failed to open add column dialog: {e}")
        
        def delete_column():
            """Deletes the selected column from the voucher type."""
            try:
                selected = columns_tree.selectedItems()
                if not selected:
                    QMessageBox.warning(dialog, "Error", "Please select a column to delete")
                    return
                col_id = selected[0].text(0)
                col_name = selected[0].text(1)
                if QMessageBox.question(dialog, "Confirm", f"Are you sure you want to delete column '{col_name}'?") == QMessageBox.Yes:
                    if delete_voucher_column(int(col_id)):
                        selected_name = selected_voucher_type.currentText()
                        selected_voucher = next((v for v in voucher_types if v[1] == selected_name), None)
                        if selected_voucher:
                            load_columns(selected_voucher[0])
                        logger.info(f"Deleted column ID {col_id}: {col_name}")
                    else:
                        QMessageBox.critical(dialog, "Error", f"Failed to delete column '{col_name}'")
            except Exception as e:
                logger.error(f"Error deleting column: {e}")
                QMessageBox.critical(dialog, "Error", f"Failed to delete column: {e}")
        
        add_button = QPushButton("Add Column")
        add_button.clicked.connect(add_column)
        layout.addWidget(add_button)
        
        delete_button = QPushButton("Delete Column")
        delete_button.clicked.connect(delete_column)
        layout.addWidget(delete_button)
        
        if default_voucher_id:
            selected_voucher = next((v for v in voucher_types if v[0] == default_voucher_id), None)
            if selected_voucher:
                selected_voucher_type.setCurrentText(selected_voucher[1])
                load_columns(default_voucher_id)
            else:
                logger.warning(f"Default voucher ID {default_voucher_id} not found")
        elif voucher_types:
            selected_voucher_type.setCurrentText(voucher_types[0][1])
            load_columns(voucher_types[0][0])
        
        dialog.setLayout(layout)
        dialog.exec_()
        logger.info("Custom voucher dialog opened successfully")
    except Exception as e:
        logger.error(f"Failed to open custom voucher dialog: {e}")
        QMessageBox.critical(app, "Error", f"Failed to open dialog: {e}")

def create_custom_voucher_type(app, dialog, default_voucher_id, module_name, voucher_type_combo, update_voucher_types, main_combo_callback):
    """Create a new custom voucher type."""
    try:
        create_dialog = QDialog(dialog)
        create_dialog.setWindowTitle("Create New Voucher Type")
        create_dialog.setFixedSize(400, 200)
        create_dialog.setWindowModality(Qt.ApplicationModal)
        
        layout = QVBoxLayout(create_dialog)
        
        name_label = QLabel("Voucher Type Name")
        name_label.setStyleSheet("font-size: 12px;")
        layout.addWidget(name_label)
        
        name_entry = QLineEdit()
        layout.addWidget(name_entry)
        
        desc_label = QLabel("Description")
        desc_label.setStyleSheet("font-size: 12px;")
        layout.addWidget(desc_label)
        
        desc_entry = QLineEdit()
        layout.addWidget(desc_entry)
        
        def submit():
            name = name_entry.text().strip()
            description = desc_entry.text().strip()
            if not name:
                QMessageBox.warning(create_dialog, "Warning", "Voucher type name is required")
                return
            if name in [v[1] for v in get_voucher_types(module_name)]:
                QMessageBox.warning(create_dialog, "Warning", f"Voucher type '{name}' already exists")
                return
            voucher_type_id = create_voucher_type(name, description, module_name, False)
            if voucher_type_id:
                update_voucher_types()
                if main_combo_callback:
                    main_combo_callback()
                create_dialog.accept()
                logger.info(f"Created custom voucher type: {name}")
            else:
                QMessageBox.critical(create_dialog, "Error", f"Failed to create voucher type '{name}'")
        
        create_button = QPushButton("Create")
        create_button.clicked.connect(submit)
        layout.addWidget(create_button)
        
        create_dialog.setLayout(layout)
        create_dialog.exec_()
    except Exception as e:
        logger.error(f"Failed to create custom voucher type: {e}")
        QMessageBox.critical(dialog, "Error", f"Failed to create voucher type: {e}")