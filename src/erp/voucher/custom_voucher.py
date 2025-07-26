# src/erp/voucher/custom_voucher.py
# Converted to use SQLAlchemy.

import logging
from PySide6.QtWidgets import QDialog, QVBoxLayout, QHBoxLayout, QLabel, QLineEdit, QPushButton, QMessageBox
from sqlalchemy import text
from src.core.config import get_database_url, get_log_path
from src.erp.logic.database.voucher import create_voucher_type, get_voucher_types
from src.erp.logic.utils.voucher_utils import VOUCHER_TYPES

logging.basicConfig(filename=get_log_path(), level=logging.DEBUG, format='%(asctime)s - %(name)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

def get_voucher_types_by_module(module):
    session = Session()
    try:
        voucher_names = session.query(VoucherType.voucher_name).filter_by(category=module).all()
        return [row[0] for row in voucher_names]
    except SQLAlchemyError as e:
        logger.error(f"Failed to get voucher types for module {module}: {e}")
        return []
    finally:
        session.close()

def create_custom_voucher_type(app, parent, voucher_type_id, module_name, is_active=1):
    """Create a new voucher type in the database."""
    session = Session()
    try:
        voucher_type = VoucherType(
            voucher_name=type_name,
            type_code=type_code,
            category=category,
            is_active=is_active
        )
        session.add(voucher_type)
        session.commit()
        logger.info(f"Created voucher type {type_name} (ID: {voucher_type.id}, code: {type_code})")
        return voucher_type.id
    except SQLAlchemyError as e:
        session.rollback()
        logger.error(f"Failed to create voucher type {type_name}: {e}")
        return None
    except Exception as e:
        session.rollback()
        logger.error(f"Unexpected error in create_voucher_type for {type_name}: {e}")
        return None
    finally:
        session.close()

def create_custom_voucher_type(app, parent, voucher_type_id, module_name, success_callback, error_callback, refresh_callback):
    logger.debug(f"Creating custom voucher type for module_name={module_name}")
    try:
        dialog = CustomVoucherDialog(app, parent, module_name, success_callback, error_callback, refresh_callback)
        dialog.exec()
    except Exception as e:
        logger.error(f"Failed to open custom voucher dialog: {e}")
        if error_callback:
            error_callback(f"Failed to open custom voucher dialog: {e}")
        else:
            QMessageBox.critical(parent, "Error", f"Failed to open custom voucher dialog: {e}")

class CustomVoucherDialog(QDialog):
    def __init__(self, app, parent, module_name, success_callback, error_callback, refresh_callback):
        super().__init__(parent)
        self.app = app
        self.module_name = module_name
        self.success_callback = success_callback
        self.error_callback = error_callback
        self.refresh_callback = refresh_callback
        self.setWindowTitle("Create Custom Voucher Type")
        self.setFixedSize(400, 200)
        self.setModal(True)
        self.init_ui()

    def init_ui(self):
        layout = QVBoxLayout(self)

        # Voucher name input
        name_layout = QHBoxLayout()
        name_layout.addWidget(QLabel("Voucher Type Name*"))
        self.name_edit = QLineEdit()
        name_layout.addWidget(self.name_edit)
        layout.addLayout(name_layout)

        # Buttons
        button_layout = QHBoxLayout()
        save_button = QPushButton("Save")
        save_button.clicked.connect(self.save_voucher_type)
        cancel_button = QPushButton("Cancel")
        cancel_button.clicked.connect(self.reject)
        button_layout.addWidget(save_button)
        button_layout.addWidget(cancel_button)
        layout.addLayout(button_layout)

    def save_voucher_type(self):
        session = Session()
        try:
            voucher_name = self.name_edit.text().strip()
            if not voucher_name:
                logger.warning("Voucher type name is empty")
                QMessageBox.critical(self, "Error", "Voucher type name is required")
                return

            existing_vouchers = [vt.lower() for vt in VOUCHER_TYPES]
            if voucher_name.lower() in existing_vouchers:
                logger.warning(f"Voucher type '{voucher_name}' already exists")
                QMessageBox.critical(self, "Error", f"Voucher type '{voucher_name}' already exists")
                return

            voucher_type_id = create_voucher_type(voucher_name, self.module_name)
            if voucher_type_id:
                logger.info(f"Custom voucher type '{voucher_name}' created with ID {voucher_type_id}")
                QMessageBox.information(self, "Success", f"Custom voucher type '{voucher_name}' created successfully")
                if self.success_callback:
                    self.success_callback(voucher_type_id, voucher_name)
                if self.refresh_callback:
                    self.refresh_callback()
                self.accept()
            else:
                logger.error(f"Failed to create voucher type '{voucher_name}'")
                QMessageBox.critical(self, "Error", "Failed to create voucher type")
                if self.error_callback:
                    self.error_callback("Failed to create voucher type")
        except Exception as e:
            logger.error(f"Unexpected error creating voucher type '{voucher_name}': {e}")
            QMessageBox.critical(self, "Error", f"Failed to create voucher type: {e}")
            if self.error_callback:
                self.error_callback(f"Failed to create voucher type: {e}")
        finally:
            session.close()

def update_voucher_types(parent):
    try:
        voucher_types = get_voucher_types()
        # Update UI if necessary (e.g., refresh combobox in parent UI)
        logger.debug(f"Updated voucher types: {voucher_types}")
    except Exception as e:
        logger.error(f"Failed to update voucher types: {e}")
        QMessageBox.critical(parent, "Error", f"Failed to update voucher types: {e}")