# src/erp/ui/company_details_ui.py
# Converted to use SQLAlchemy in save and load.

from PySide6.QtWidgets import QWidget, QDialog, QVBoxLayout, QHBoxLayout, QGridLayout, QLabel, QLineEdit, QComboBox, QPushButton, QFileDialog, QMessageBox, QWidget, QCompleter
from PySide6.QtCore import Qt, QEvent, QObject, QStringListModel
import logging
import os
from sqlalchemy import text
from src.erp.logic.database.session import engine, Session
from src.core.config import get_static_path, get_log_path, get_database_url
from src.erp.logic.utils.utils import STATES, update_state_code
from src.erp.logic.company_details_logic import save_company_details, cancel_company_details
from src.erp.logic.default_directory import get_default_directory
from src.erp.ui.default_directory_ui import show_default_directory_setup

logging.basicConfig(
    filename=get_log_path(),
    level=logging.DEBUG,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

class ComboBoxEventFilter(QObject):
    def __init__(self, parent=None):
        super().__init__(parent)

    def eventFilter(self, obj, event):
        if isinstance(obj, QComboBox):
            if event.type() == QEvent.MouseButtonPress:
                logger.debug(f"Mouse press on QComboBox: {obj.objectName()}")
                if obj.objectName() == "stateCombo":
                    obj.showPopup()
            elif event.type() == QEvent.KeyPress:
                logger.debug(f"Key press on QComboBox: {obj.objectName()}, key: {event.key()}")
            elif event.type() == QEvent.FocusIn:
                logger.debug(f"Focus in on QComboBox: {obj.objectName()}")
        return super().eventFilter(obj, event)

class CompanyDetailsWidget(QWidget):
    def __init__(self, parent=None, app=None):
        super().__init__(parent)
        self.app = app
        self.entries = {}
        self.state_model = None
        self.setup_ui()

    def setup_ui(self):
        logger.debug("Creating Company Details widget")
        main_layout = QVBoxLayout(self)
        main_layout.setContentsMargins(5, 5, 5, 5)
        main_layout.setSpacing(5)

        content_layout = QVBoxLayout()
        content_layout.setAlignment(Qt.AlignTop)
        content_layout.setContentsMargins(3, 3, 3, 3)
        content_layout.setSpacing(5)

        title_label = QLabel("Company Details")
        title_label.setObjectName("titleLabel")
        content_layout.addWidget(title_label)

        fields = [
            ("Company Name*", "normal"),
            ("Address Line 1*", "normal"),
            ("Address Line 2", "normal"),
            ("City*", "normal"),
            ("State*", "combobox"),
            ("State Code*", "readonly"),
            ("PIN Code*", "normal"),
            ("GST No", "normal"),
            ("PAN No", "normal"),
            ("Contact No*", "normal"),
            ("Email", "normal"),
            ("Logo Path", "readonly")
        ]

        grid_layout = QGridLayout()
        grid_layout.setVerticalSpacing(5)
        grid_layout.setHorizontalSpacing(5)
        for i, (label_text, state) in enumerate(fields):
            label = QLabel(label_text)
            label.setObjectName("fieldLabel")
            grid_layout.addWidget(label, i, 0, Qt.AlignLeft)

            if label_text == "State*":
                combo = QComboBox()
                combo.setObjectName("stateCombo")
                combo.setEditable(True)
                combo.setInsertPolicy(QComboBox.NoInsert)
                combo.setFocusPolicy(Qt.StrongFocus)
                combo.setEnabled(True)
                combo.installEventFilter(ComboBoxEventFilter(combo))
                try:
                    states = [s[0] for s in STATES if isinstance(s, (list, tuple)) and len(s) > 0 and isinstance(s[0], str)]
                    self.state_model = QStringListModel(states)
                    logger.debug(f"Initialized state_model with {len(states)} states")
                except Exception as e:
                    logger.error(f"Error initializing state_model: {e}")
                    self.state_model = QStringListModel([])
                combo.setModel(self.state_model)
                completer = QCompleter(self.state_model, combo)
                completer.setCaseSensitivity(Qt.CaseInsensitive)
                completer.setFilterMode(Qt.MatchStartsWith)
                combo.setCompleter(completer)
                combo.setCurrentIndex(-1)
                combo.setPlaceholderText("Select a state")
                combo.editTextChanged.connect(lambda text: self.update_combobox_items(combo, text))
                combo.currentIndexChanged.connect(lambda index: self.on_state_index_changed(index))
                combo.activated.connect(lambda index: self.on_state_activated(combo.itemText(index)))
                self.entries[label_text] = combo
                grid_layout.addWidget(combo, i, 1)
            elif label_text == "Logo Path":
                logo_widget = QWidget()
                logo_layout = QHBoxLayout(logo_widget)
                logo_layout.setContentsMargins(0, 0, 0, 0)
                logo_layout.setSpacing(0)
                entry = QLineEdit()
                entry.setObjectName("logoPathEntry")
                entry.setReadOnly(True)
                entry.setFocusPolicy(Qt.StrongFocus)
                entry.setEnabled(True)
                self.entries[label_text] = entry
                logo_layout.addWidget(entry)
                browse_button = QPushButton("Browse")
                browse_button.setObjectName("actionButton")
                browse_button.setFixedWidth(60)
                browse_button.setFocusPolicy(Qt.StrongFocus)
                browse_button.setEnabled(True)
                browse_button.clicked.connect(lambda: self.upload_logo(entry))
                logo_layout.addWidget(browse_button)
                grid_layout.addWidget(logo_widget, i, 1)
            else:
                entry = QLineEdit()
                entry.setObjectName("textEntry")
                entry.setReadOnly(True if state == "readonly" else False)
                entry.setFocusPolicy(Qt.StrongFocus)
                entry.setEnabled(True)
                self.entries[label_text] = entry
                grid_layout.addWidget(entry, i, 1)

        content_layout.addLayout(grid_layout)

        button_layout = QHBoxLayout()
        button_layout.setSpacing(5)
        save_button = QPushButton("Save")
        save_button.setObjectName("saveButton")
        save_button.setFocusPolicy(Qt.StrongFocus)
        save_button.setEnabled(True)
        save_button.clicked.connect(self.save)
        cancel_button = QPushButton("Cancel")
        cancel_button.setObjectName("cancelButton")
        cancel_button.setFocusPolicy(Qt.StrongFocus)
        cancel_button.setEnabled(True)
        cancel_button.clicked.connect(self.cancel)
        button_layout.addWidget(save_button)
        button_layout.addWidget(cancel_button)
        content_layout.addLayout(button_layout)

        main_layout.addLayout(content_layout)
        self.setLayout(main_layout)

    def update_combobox_items(self, combo, text):
        try:
            logger.debug(f"Updating QComboBox with text: {text}")
            combo.editTextChanged.disconnect()
            model = combo.model()
            if not isinstance(STATES, (list, tuple)):
                logger.error(f"STATES is not a list or tuple: {type(STATES)}")
                model.setStringList([])
                return
            if not text:
                states = [s[0] for s in STATES if isinstance(s, (list, tuple)) and len(s) > 0 and isinstance(s[0], str)]
            else:
                states = [s[0] for s in STATES if isinstance(s, (list, tuple)) and len(s) > 0 and isinstance(s[0], str) and s[0].lower().startswith(text.lower())]
            model.setStringList(states)
            if states:
                combo.showPopup()
            logger.debug(f"Updated State* QComboBox items: {states}")
        except Exception as e:
            logger.error(f"Error in update_combobox_items: {e}")
            model.setStringList([])
        finally:
            combo.editTextChanged.connect(lambda text: self.update_combobox_items(combo, text))

    def on_state_index_changed(self, index):
        try:
            text = self.entries["State*"].itemText(index) if index >= 0 else ""
            logger.debug(f"State index changed in CompanyDetailsWidget: index {index}, text {text}")
            update_state_code(text, self.entries["State Code*"])
            logger.debug(f"State Code set to: {self.entries['State Code*'].text()}")
        except Exception as e:
            logger.error(f"Error in on_state_index_changed: {e}")
            self.entries["State Code*"].setText("")

    def on_state_activated(self, text):
        try:
            logger.debug(f"State activated in CompanyDetailsWidget: text {text}")
            update_state_code(text, self.entries["State Code*"])
            logger.debug(f"State Code set to: {self.entries['State Code*'].text()}")
        except Exception as e:
            logger.error(f"Error in on_state_activated: {e}")
            self.entries["State Code*"].setText("")

    def save(self):
        try:
            logger.debug("Starting save in CompanyDetailsWidget")
            company_data = {
                "company_name": self.entries["Company Name*"].text().strip(),
                "address1": self.entries["Address Line 1*"].text().strip(),
                "address2": self.entries["Address Line 2"].text().strip(),
                "city": self.entries["City*"].text().strip(),
                "state": self.entries["State*"].currentText().strip(),
                "pin": self.entries["PIN Code*"].text().strip(),
                "state_code": self.entries["State Code*"].text().strip(),
                "gst_no": self.entries["GST No"].text().strip(),
                "pan_no": self.entries["PAN No"].text().strip(),
                "contact_no": self.entries["Contact No*"].text().strip(),
                "email": self.entries["Email"].text().strip(),
                "logo_path": self.entries["Logo Path"].text().strip()
            }
            logger.debug(f"Attempting to save company details: {company_data}")
            if save_company_details(self, self.app, company_data):
                logger.info("Company details saved successfully in CompanyDetailsWidget")
                logger.debug("Calling check_company_details")
                self.app.check_company_details()
                logger.debug("Finished check_company_details")
                current_dir = get_default_directory()
                if not current_dir or not os.path.exists(current_dir):
                    show_default_directory_setup(self.app)
            else:
                logger.error("Failed to save company details in CompanyDetailsWidget")
                QMessageBox.critical(self, "Error", "Failed to save company details")
        except Exception as e:
            logger.error(f"Error saving company details in CompanyDetailsWidget: {e}")
            QMessageBox.critical(self, "Error", f"Failed to save company details: {e}")

    def upload_logo(self, entry):
        file_path, _ = QFileDialog.getOpenFileName(self, "Select Logo", "", "Image files (*.png *.jpg *.jpeg *.bmp)")
        if file_path:
            entry.setText(file_path)
            logger.debug(f"Logo selected: {file_path}")

    def cancel(self):
        try:
            logger.debug("Cancel button clicked in CompanyDetailsWidget")
            cancel_company_details(self, self.app)
        except Exception as e:
            logger.error(f"Error during cancel in CompanyDetailsWidget: {e}")
            QMessageBox.critical(self, "Error", f"Cancel failed: {e}")

class CompanySetupDialog(QDialog):
    def __init__(self, parent=None, app=None):
        super().__init__(parent)
        self.app = app
        self.entries = {}
        self.state_model = None
        self.setWindowTitle("Company Setup")
        self.setMinimumSize(400, 600)
        self.setModal(True)
        self.setEnabled(True)
        logger.info("Creating company setup dialog")
        self.setup_ui()
        self.adjustSize()

    def setup_ui(self):
        main_layout = QVBoxLayout(self)
        main_layout.setContentsMargins(10, 10, 10, 10)
        main_layout.setSpacing(5)

        content_layout = QVBoxLayout()
        content_layout.setAlignment(Qt.AlignTop)
        content_layout.setContentsMargins(3, 3, 3, 3)
        content_layout.setSpacing(5)

        title_label = QLabel("Company Setup")
        title_label.setAlignment(Qt.AlignCenter)
        content_layout.addWidget(title_label)

        fields = [
            ("Company Name*", "normal"),
            ("Address Line 1*", "normal"),
            ("Address Line 2", "normal"),
            ("City*", "normal"),
            ("State*", "combobox"),
            ("State Code*", "readonly"),
            ("PIN Code*", "normal"),
            ("GST No", "normal"),
            ("PAN No", "normal"),
            ("Contact No*", "normal"),
            ("Email", "normal"),
            ("Logo Path", "readonly")
        ]

        grid_layout = QGridLayout()
        grid_layout.setVerticalSpacing(5)
        grid_layout.setHorizontalSpacing(5)
        for i, (label_text, state) in enumerate(fields):
            label = QLabel(label_text)
            label.setObjectName("fieldLabel")
            grid_layout.addWidget(label, i, 0, Qt.AlignLeft)

            if label_text == "State*":
                combo = QComboBox()
                combo.setObjectName("stateCombo")
                combo.setEditable(True)
                combo.setInsertPolicy(QComboBox.NoInsert)
                combo.setFocusPolicy(Qt.StrongFocus)
                combo.setEnabled(True)
                combo.installEventFilter(ComboBoxEventFilter(combo))
                try:
                    states = [s[0] for s in STATES if isinstance(s, (list, tuple)) and len(s) > 0 and isinstance(s[0], str)]
                    self.state_model = QStringListModel(states)
                    logger.debug(f"Initialized state_model with {len(states)} states")
                except Exception as e:
                    logger.error(f"Error initializing state_model: {e}")
                    self.state_model = QStringListModel([])
                combo.setModel(self.state_model)
                completer = QCompleter(self.state_model, combo)
                completer.setCaseSensitivity(Qt.CaseInsensitive)
                completer.setFilterMode(Qt.MatchStartsWith)
                combo.setCompleter(completer)
                combo.setCurrentIndex(-1)
                combo.setPlaceholderText("Select a state")
                combo.editTextChanged.connect(lambda text: self.update_combobox_items(combo, text))
                combo.currentIndexChanged.connect(lambda index: self.on_state_index_changed(index))
                combo.activated.connect(lambda index: self.on_state_activated(combo.itemText(index)))
                self.entries[label_text] = combo
                grid_layout.addWidget(combo, i, 1)
            elif label_text == "Logo Path":
                logo_widget = QWidget()
                logo_layout = QHBoxLayout(logo_widget)
                logo_layout.setContentsMargins(0, 0, 0, 0)
                logo_layout.setSpacing(0)
                entry = QLineEdit()
                entry.setObjectName("logoPathEntry")
                entry.setReadOnly(True)
                entry.setFocusPolicy(Qt.StrongFocus)
                entry.setEnabled(True)
                self.entries[label_text] = entry
                logo_layout.addWidget(entry)
                browse_button = QPushButton("Browse")
                browse_button.setObjectName("actionButton")
                browse_button.setFixedWidth(60)
                browse_button.setFocusPolicy(Qt.StrongFocus)
                browse_button.setEnabled(True)
                browse_button.clicked.connect(lambda: self.upload_logo(entry))
                logo_layout.addWidget(browse_button)
                grid_layout.addWidget(logo_widget, i, 1)
            else:
                entry = QLineEdit()
                entry.setObjectName("textEntry")
                entry.setReadOnly(True if state == "readonly" else False)
                entry.setFocusPolicy(Qt.StrongFocus)
                entry.setEnabled(True)
                self.entries[label_text] = entry
                grid_layout.addWidget(entry, i, 1)

        content_layout.addLayout(grid_layout)

        button_layout = QHBoxLayout()
        button_layout.setSpacing(5)
        save_button = QPushButton("Save")
        save_button.setObjectName("saveButton")
        save_button.setFocusPolicy(Qt.StrongFocus)
        save_button.setEnabled(True)
        save_button.clicked.connect(self.save)
        cancel_button = QPushButton("Cancel")
        cancel_button.setObjectName("cancelButton")
        cancel_button.setFocusPolicy(Qt.StrongFocus)
        cancel_button.setEnabled(True)
        cancel_button.clicked.connect(self.cancel)
        button_layout.addWidget(save_button)
        button_layout.addWidget(cancel_button)
        content_layout.addLayout(button_layout)

        main_layout.addLayout(content_layout)
        self.setLayout(main_layout)

        for widget_type in [QLineEdit, QComboBox, QPushButton]:
            for widget in self.findChildren(widget_type):
                widget.setEnabled(True)
                logger.debug(f"Widget {widget.objectName()} enabled: {widget.isEnabled()}")

    def update_combobox_items(self, combo, text):
        try:
            logger.debug(f"Updating QComboBox with text: {text}")
            combo.editTextChanged.disconnect()
            model = combo.model()
            if not isinstance(STATES, (list, tuple)):
                logger.error(f"STATES is not a list or tuple: {type(STATES)}")
                model.setStringList([])
                return
            if not text:
                states = [s[0] for s in STATES if isinstance(s, (list, tuple)) and len(s) > 0 and isinstance(s[0], str)]
            else:
                states = [s[0] for s in STATES if isinstance(s, (list, tuple)) and len(s) > 0 and isinstance(s[0], str) and s[0].lower().startswith(text.lower())]
            model.setStringList(states)
            if states:
                combo.showPopup()
            logger.debug(f"Updated State* QComboBox items: {states}")
        except Exception as e:
            logger.error(f"Error in update_combobox_items: {e}")
            model.setStringList([])
        finally:
            combo.editTextChanged.connect(lambda text: self.update_combobox_items(combo, text))

    def on_state_index_changed(self, index):
        try:
            text = self.entries["State*"].itemText(index) if index >= 0 else ""
            logger.debug(f"State index changed in CompanySetupDialog: index {index}, text {text}")
            update_state_code(text, self.entries["State Code*"])
            logger.debug(f"State Code set to: {self.entries['State Code*'].text()}")
        except Exception as e:
            logger.error(f"Error in on_state_index_changed: {e}")
            self.entries["State Code*"].setText("")

    def on_state_activated(self, text):
        try:
            logger.debug(f"State activated in CompanySetupDialog: text {text}")
            update_state_code(text, self.entries["State Code*"])
            logger.debug(f"State Code set to: {self.entries['State Code*'].text()}")
        except Exception as e:
            logger.error(f"Error in on_state_activated: {e}")
            self.entries["State Code*"].setText("")

    def closeEvent(self, event):
        try:
            logger.debug("Close event in CompanySetupDialog")
            if not self.app.company_details_exist:
                logger.info("No company details exist, closing application on dialog close")
                self.app.exit_app()
                event.accept()
            else:
                super().closeEvent(event)
        except Exception as e:
            logger.error(f"Error in closeEvent: {e}")
            event.accept()

    def save(self):
        try:
            logger.debug("Starting save in CompanySetupDialog")
            company_data = {
                "company_name": self.entries["Company Name*"].text().strip(),
                "address1": self.entries["Address Line 1*"].text().strip(),
                "address2": self.entries["Address Line 2"].text().strip(),
                "city": self.entries["City*"].text().strip(),
                "state": self.entries["State*"].currentText().strip(),
                "pin": self.entries["PIN Code*"].text().strip(),
                "state_code": self.entries["State Code*"].text().strip(),
                "gst_no": self.entries["GST No"].text().strip(),
                "pan_no": self.entries["PAN No"].text().strip(),
                "contact_no": self.entries["Contact No*"].text().strip(),
                "email": self.entries["Email"].text().strip(),
                "logo_path": self.entries["Logo Path"].text().strip()
            }
            logger.debug(f"Attempting to save company details: {company_data}")
            if save_company_details(self, self.app, company_data):
                logger.info("Company details saved successfully in CompanySetupDialog")
                logger.debug("Calling accept in CompanySetupDialog")
                self.accept()
                logger.debug("Finished accept in CompanySetupDialog")
            else:
                logger.error("Failed to save company details in CompanySetupDialog")
                QMessageBox.critical(self, "Error", "Failed to save company details")
        except Exception as e:
            logger.error(f"Error saving company details in CompanySetupDialog: {e}")
            QMessageBox.critical(self, "Error", f"Failed to save company details: {e}")

    def cancel(self):
        try:
            logger.debug("Cancel button clicked in CompanySetupDialog")
            self.reject()
        except Exception as e:
            logger.error(f"Error during cancel in CompanySetupDialog: {e}")
            QMessageBox.critical(self, "Error", f"Cancel failed: {e}")

    def upload_logo(self, entry):
        file_path, _ = QFileDialog.getOpenFileName(self, "Select Logo", "", "Image files (*.png *.jpg *.jpeg *.bmp)")
        if file_path:
            entry.setText(file_path)
            logger.debug(f"Logo selected in setup: {file_path}")