# Revised vendors_ui.py

from PySide6.QtWidgets import QWidget, QDialog, QVBoxLayout, QHBoxLayout, QLabel, QTableWidget, QTableWidgetItem, QHeaderView, QPushButton, QGridLayout, QLineEdit, QComboBox, QMenu, QScrollArea
from PySide6.QtCore import Qt
import logging
from src.erp.logic.utils.utils import STATES

logger = logging.getLogger(__name__)

class VendorsWidget(QWidget):
    def __init__(self, parent=None, app=None):
        super().__init__(parent)
        self.app = app
        self.setup_ui()

    def setup_ui(self):
        logger.info("Creating vendors widget")
        main_layout = QVBoxLayout(self)
        main_layout.setContentsMargins(10, 10, 10, 10)

        # Title
        title_label = QLabel("Vendors")
        title_label.setObjectName("titleLabel")
        main_layout.addWidget(title_label)

        # Table
        self.vendor_table = QTableWidget()
        self.vendor_table.setColumnCount(6)
        self.vendor_table.setHorizontalHeaderLabels(["ID", "Name", "Contact No", "City", "State", "GST"])
        self.vendor_table.setObjectName("vendorTable")
        self.vendor_table.horizontalHeader().setSectionResizeMode(QHeaderView.Stretch)
        self.vendor_table.setSelectionMode(QTableWidget.SingleSelection)
        self.vendor_table.setContextMenuPolicy(Qt.CustomContextMenu)
        self.vendor_table.customContextMenuRequested.connect(self.show_context_menu)
        self.vendor_table.doubleClicked.connect(self.edit_vendor)
        self.vendor_table.horizontalHeader().setVisible(True)  # Ensure header is visible
        main_layout.addWidget(self.vendor_table)

        # Buttons
        button_layout = QHBoxLayout()
        add_button = QPushButton("Add Vendor")
        add_button.setObjectName("actionButton")
        add_button.clicked.connect(lambda: self.app.logic.vendors_logic.add_vendor(self.app, self, callback=self.load_vendors))
        import_button = QPushButton("Import from Excel")
        import_button.setObjectName("actionButton")
        import_button.clicked.connect(lambda: self.app.logic.vendors_logic.import_excel_vendors(self.load_vendors))
        export_button = QPushButton("Export to Excel")
        export_button.setObjectName("actionButton")
        export_button.clicked.connect(self.app.logic.vendors_logic.export_excel_vendors)
        sample_button = QPushButton("Download Sample Excel")
        sample_button.setObjectName("actionButton")
        sample_button.clicked.connect(self.app.logic.vendors_logic.download_sample_excel)
        button_layout.addWidget(add_button)
        button_layout.addWidget(import_button)
        button_layout.addWidget(export_button)
        button_layout.addWidget(sample_button)
        main_layout.addLayout(button_layout)

        self.load_vendors()

    def load_vendors(self):
        self.app.logic.vendors_logic.load_vendors(self)

    def show_context_menu(self, pos):
        if self.vendor_table.selectedItems():
            menu = QMenu()
            edit_action = menu.addAction("Edit")
            delete_action = menu.addAction("Delete")
            edit_action.triggered.connect(self.edit_vendor)
            delete_action.triggered.connect(self.delete_vendor)
            menu.exec(self.vendor_table.viewport().mapToGlobal(pos))

    def edit_vendor(self):
        if not self.vendor_table.selectedItems():
            return
        vendor_id = self.vendor_table.item(self.vendor_table.currentRow(), 0).text()
        self.app.logic.vendors_logic.edit_vendor(self.app, self, vendor_id, self.load_vendors)

    def delete_vendor(self):
        if not self.vendor_table.selectedItems():
            return
        vendor_id = self.vendor_table.item(self.vendor_table.currentRow(), 0).text()
        self.app.logic.vendors_logic.delete_vendor(self.app, self, vendor_id, self.load_vendors)

class AddVendorDialog(QDialog):
    def __init__(self, parent=None, app=None, callback=None, entries=None, edit_mode=False, vendor_id=None):
        super().__init__(parent)
        self.app = app
        self.callback = callback
        self.entries = entries or {}
        self.edit_mode = edit_mode
        self.vendor_id = vendor_id
        self.setWindowTitle("Add Vendor")
        self.setFixedSize(400, 600)
        self.setModal(True)
        self.setup_ui()

    def setup_ui(self):
        logger.info("Creating add vendor dialog")
        main_layout = QVBoxLayout(self)
        main_layout.setContentsMargins(10, 10, 10, 10)

        scroll = QScrollArea()
        scroll.setWidgetResizable(True)
        content_widget = QWidget()
        scroll.setWidget(content_widget)
        content_layout = QVBoxLayout(content_widget)
        content_layout.setAlignment(Qt.AlignTop)

        title_label = QLabel("Add Vendor")
        title_label.setObjectName("dialogTitleLabel")
        content_layout.addWidget(title_label)

        fields = [
            ("Name*", "normal"),
            ("Contact No*", "normal"),
            ("Address Line 1*", "normal"),
            ("Address Line 2", "normal"),
            ("City*", "normal"),
            ("State*", "combobox"),
            ("State Code*", "readonly"),
            ("PIN Code*", "normal"),
            ("GST No", "normal"),
            ("PAN No", "normal"),
            ("Email", "normal"),
        ]

        grid_layout = QGridLayout()
        for i, (label_text, state) in enumerate(fields):
            label = QLabel(label_text)
            label.setObjectName("fieldLabel")
            grid_layout.addWidget(label, i, 0, Qt.AlignLeft)

            if label_text == "State*":
                combo = QComboBox()
                combo.addItems([s[0] for s in STATES])
                combo.setObjectName("stateCombo")
                combo.setEditable(True)
                combo.setInsertPolicy(QComboBox.NoInsert)
                self.entries[label_text] = combo
                grid_layout.addWidget(combo, i, 1)
                combo.currentTextChanged.connect(lambda text: self.app.utils.update_state_code(text, self.entries["State Code*"]))
                combo.editTextChanged.connect(lambda text: self.app.utils.filter_combobox(combo, text))
            else:
                entry = QLineEdit()
                entry.setObjectName("textEntry")
                entry.setReadOnly(True if state == "readonly" else False)
                self.entries[label_text] = entry
                grid_layout.addWidget(entry, i, 1)

        content_layout.addLayout(grid_layout)

        button_layout = QHBoxLayout()
        save_button = QPushButton("Save")
        save_button.setObjectName("actionButton")
        save_button.clicked.connect(self.save)
        cancel_button = QPushButton("Cancel")
        cancel_button.setObjectName("actionButton")
        cancel_button.clicked.connect(self.cancel)
        button_layout.addWidget(cancel_button)
        button_layout.addWidget(save_button)
        content_layout.addLayout(button_layout)

        main_layout.addWidget(scroll)

    def save(self):
        if self.edit_mode:
            self.app.logic.vendors_logic.save_edit_vendor(self.app, self.entries, self, self.vendor_id, self.callback)
        else:
            self.app.logic.vendors_logic.save_vendor(self.app, self.entries, self, self.callback)

    def cancel(self):
        self.app.logic.vendors_logic.close_window(self, self.app)