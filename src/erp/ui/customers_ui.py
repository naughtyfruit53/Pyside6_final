# src/erp/ui/customers_ui.py
# No direct DB access; calls logic.

from PySide6.QtWidgets import QWidget, QDialog, QVBoxLayout, QHBoxLayout, QLabel, QTableWidget, QTableWidgetItem, QHeaderView, QPushButton, QGridLayout, QLineEdit, QComboBox, QMenu, QScrollArea
from PySide6.QtCore import Qt
import logging
from src.erp.logic.utils.utils import STATES

logger = logging.getLogger(__name__)

class CustomersWidget(QWidget):
    def __init__(self, parent=None, app=None):
        super().__init__(parent)
        self.app = app
        self.setup_ui()

    def setup_ui(self):
        logger.info("Creating customers widget")
        main_layout = QVBoxLayout(self)
        main_layout.setContentsMargins(10, 10, 10, 10)

        # Title
        title_label = QLabel("Customers")
        title_label.setObjectName("titleLabel")
        main_layout.addWidget(title_label)

        # Table
        self.customer_tree = QTableWidget()
        self.customer_tree.setColumnCount(6)
        self.customer_tree.setHorizontalHeaderLabels(["ID", "Name", "Contact No", "City", "State", "GST"])
        self.customer_tree.setObjectName("customerTable")
        self.customer_tree.horizontalHeader().setSectionResizeMode(QHeaderView.Stretch)
        self.customer_tree.setSelectionMode(QTableWidget.SingleSelection)
        self.customer_tree.setContextMenuPolicy(Qt.CustomContextMenu)
        self.customer_tree.customContextMenuRequested.connect(self.show_context_menu)
        self.customer_tree.doubleClicked.connect(self.edit_customer)
        main_layout.addWidget(self.customer_tree)

        # Buttons
        button_layout = QHBoxLayout()
        add_button = QPushButton("Add Customer")
        add_button.setObjectName("actionButton")
        add_button.clicked.connect(lambda: self.app.logic.customers_logic.add_customer(self.app, callback=self.load_customers))
        import_button = QPushButton("Import from Excel")
        import_button.setObjectName("actionButton")
        import_button.clicked.connect(lambda: self.app.logic.customers_logic.import_excel_customers(self.load_customers))
        export_button = QPushButton("Export to Excel")
        export_button.setObjectName("actionButton")
        export_button.clicked.connect(self.app.logic.customers_logic.export_excel_customers)
        sample_button = QPushButton("Download Sample Excel")
        sample_button.setObjectName("actionButton")
        sample_button.clicked.connect(self.app.logic.customers_logic.download_sample_excel)
        button_layout.addWidget(add_button)
        button_layout.addWidget(import_button)
        button_layout.addWidget(export_button)
        button_layout.addWidget(sample_button)
        main_layout.addLayout(button_layout)

        self.load_customers()

    def load_customers(self):
        self.app.logic.customers_logic.load_customers(self)

    def show_context_menu(self, pos):
        if self.customer_tree.selectedItems():
            menu = QMenu()
            edit_action = menu.addAction("Edit")
            delete_action = menu.addAction("Delete")
            edit_action.triggered.connect(self.edit_customer)
            delete_action.triggered.connect(self.delete_customer)
            menu.exec(self.customer_tree.viewport().mapToGlobal(pos))

    def edit_customer(self):
        if not self.customer_tree.selectedItems():
            return
        customer_id = self.customer_tree.item(self.customer_tree.currentRow(), 0).text()
        self.app.logic.customers_logic.edit_customer(self.app, customer_id, self.load_customers)

    def delete_customer(self):
        if not self.customer_tree.selectedItems():
            return
        customer_id = self.customer_tree.item(self.customer_tree.currentRow(), 0).text()
        self.app.logic.customers_logic.delete_customer(self.app, customer_id, self.load_customers)

class AddCustomerDialog(QDialog):
    def __init__(self, parent=None, app=None, callback=None, entries=None):
        super().__init__(parent)
        self.app = app
        self.callback = callback
        self.entries = entries or {}
        self.setWindowTitle("Add Customer")
        self.setFixedSize(400, 600)
        self.setModal(True)
        self.setup_ui()

    def setup_ui(self):
        logger.info("Creating add customer dialog")
        main_layout = QVBoxLayout(self)
        main_layout.setContentsMargins(10, 10, 10, 10)

        scroll = QScrollArea()
        scroll.setWidgetResizable(True)
        content_widget = QWidget()
        scroll.setWidget(content_widget)
        content_layout = QVBoxLayout(content_widget)
        content_layout.setAlignment(Qt.AlignTop)

        title_label = QLabel("Add Customer")
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
                combo.currentTextChanged.connect(lambda text: self.app.utils.update_state_code(text, self.entries["State Code*"]))
                combo.editTextChanged.connect(lambda text: self.app.utils.filter_combobox(combo, text))
                self.entries[label_text] = combo
                grid_layout.addWidget(combo, i, 1)
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
        save_button.clicked.connect(lambda: self.app.logic.customers_logic.save_customer(self.app, self.entries, self, self.callback))
        cancel_button = QPushButton("Cancel")
        cancel_button.setObjectName("actionButton")
        cancel_button.clicked.connect(lambda: self.app.logic.customers_logic.close_window(self, self.app))
        button_layout.addWidget(cancel_button)
        button_layout.addWidget(save_button)
        content_layout.addLayout(button_layout)

        main_layout.addWidget(scroll)