from PySide6.QtWidgets import QWidget, QVBoxLayout, QHBoxLayout, QLabel, QComboBox, QPushButton, QTableWidget, QTableWidgetItem, QHeaderView, QLineEdit, QDialog, QMessageBox
from PySide6.QtCore import Qt
import logging

logger = logging.getLogger(__name__)

class ManufacturingUI(QWidget):
    def __init__(self, parent=None, app=None):
        super().__init__(parent)
        self.app = app
        self.setup_ui()

    def setup_ui(self):
        logger.info("Setting up Manufacturing UI")
        layout = QVBoxLayout(self)
        layout.setContentsMargins(10, 10, 10, 10)
        layout.setSpacing(10)

        # Header
        title_label = QLabel("Manufacturing Management", self)
        title_label.setStyleSheet("font-size: 24px; font-weight: bold;")
        layout.addWidget(title_label)

        description_label = QLabel(
            "Manage your manufacturing operations, including bills of materials, work orders, and production processes.",
            self)
        description_label.setWordWrap(True)
        description_label.setStyleSheet("font-size: 14px;")
        layout.addWidget(description_label)

        layout.addStretch()

class BOMUI(QWidget):
    def __init__(self, parent=None, app=None):
        super().__init__(parent)
        self.app = app
        self.setup_ui()

    def setup_ui(self):
        logger.info("Setting up BOM UI")
        layout = QVBoxLayout(self)
        layout.setContentsMargins(10, 10, 10, 10)
        layout.setSpacing(10)

        # Header
        title_label = QLabel("Create Bill of Materials", self)
        title_label.setStyleSheet("font-size: 16px; font-weight: bold;")
        layout.addWidget(title_label)

        # Manufactured Product Section
        product_frame = QWidget(self)
        product_layout = QHBoxLayout(product_frame)
        product_layout.setSpacing(5)

        product_label = QLabel("Manufactured Product*", self)
        product_label.setStyleSheet("font-size: 12px;")
        product_layout.addWidget(product_label)

        self.product_combo = QComboBox(self)
        self.product_combo.setFixedWidth(200)
        self.product_combo.setStyleSheet("padding: 5px;")
        product_layout.addWidget(self.product_combo)

        add_product_button = QPushButton("Add Product", self)
        add_product_button.setStyleSheet("padding: 5px 10px;")
        product_layout.addWidget(add_product_button)
        product_layout.addStretch()

        layout.addWidget(product_frame)

        # Component Products Section
        components_label = QLabel("Component Products", self)
        components_label.setStyleSheet("font-size: 12px; font-weight: bold;")
        layout.addWidget(components_label)

        self.component_table = QTableWidget(self)
        self.component_table.setRowCount(0)
        self.component_table.setColumnCount(2)
        self.component_table.setHorizontalHeaderLabels(["Product Name", "Quantity"])
        self.component_table.horizontalHeader().setSectionResizeMode(0, QHeaderView.Stretch)
        self.component_table.horizontalHeader().setSectionResizeMode(1, QHeaderView.Fixed)
        self.component_table.setColumnWidth(1, 100)
        self.component_table.setStyleSheet("QTableWidget { border: 1px solid #ccc; }")
        layout.addWidget(self.component_table)

        # Add Component Frame
        add_component_frame = QWidget(self)
        add_component_layout = QHBoxLayout(add_component_frame)
        add_component_layout.setSpacing(5)

        add_component_label = QLabel("Add Component:", self)
        add_component_layout.addWidget(add_component_label)

        self.component_combo = QComboBox(self)
        self.component_combo.setFixedWidth(200)
        self.component_combo.setStyleSheet("padding: 5px;")
        add_component_layout.addWidget(self.component_combo)

        self.quantity_input = QLineEdit(self)
        self.quantity_input.setFixedWidth(80)
        self.quantity_input.setText("1")
        self.quantity_input.setStyleSheet("padding: 5px;")
        add_component_layout.addWidget(self.quantity_input)

        add_button = QPushButton("Add", self)
        add_button.setStyleSheet("padding: 5px 10px;")
        add_component_layout.addWidget(add_button)

        remove_button = QPushButton("Remove", self)
        remove_button.setStyleSheet("padding: 5px 10px;")
        add_component_layout.addWidget(remove_button)
        add_component_layout.addStretch()

        layout.addWidget(add_component_frame)

        # Buttons
        button_frame = QWidget(self)
        button_layout = QHBoxLayout(button_frame)
        button_layout.setSpacing(10)

        save_button = QPushButton("Save", self)
        save_button.setStyleSheet("padding: 5px 20px;")
        button_layout.addWidget(save_button)

        clear_button = QPushButton("Clear", self)
        clear_button.setStyleSheet("padding: 5px 20px;")
        button_layout.addWidget(clear_button)
        button_layout.addStretch()

        layout.addWidget(button_frame)
        layout.addStretch()

        # Connect signals
        add_product_button.clicked.connect(self.app.manufacturing_logic.add_manufactured_product)
        add_button.clicked.connect(self.app.manufacturing_logic.add_component)
        remove_button.clicked.connect(self.app.manufacturing_logic.remove_component)
        save_button.clicked.connect(self.app.manufacturing_logic.save_bom)
        clear_button.clicked.connect(self.app.manufacturing_logic.clear_bom)

class WorkOrderUI(QWidget):
    def __init__(self, parent=None, app=None):
        super().__init__(parent)
        self.app = app
        self.setup_ui()

    def setup_ui(self):
        logger.info("Setting up Work Order UI")
        layout = QVBoxLayout(self)
        layout.setContentsMargins(10, 10, 10, 10)
        layout.setSpacing(10)

        # Header
        title_label = QLabel("Create Work Order", self)
        title_label.setStyleSheet("font-size: 16px; font-weight: bold;")
        layout.addWidget(title_label)

        # BOM Selection
        bom_frame = QWidget(self)
        bom_layout = QHBoxLayout(bom_frame)
        bom_layout.setSpacing(5)

        bom_label = QLabel("BOM Selection", self)
        bom_label.setStyleSheet("font-size: 12px;")
        bom_layout.addWidget(bom_label)

        self.bom_combo = QComboBox(self)
        self.bom_combo.setFixedWidth(200)
        self.bom_combo.setStyleSheet("padding: 5px;")
        bom_layout.addWidget(self.bom_combo)
        bom_layout.addStretch()

        layout.addWidget(bom_frame)

        # Quantity
        quantity_frame = QWidget(self)
        quantity_layout = QHBoxLayout(quantity_frame)
        quantity_layout.setSpacing(5)

        quantity_label = QLabel("Quantity*", self)
        quantity_label.setStyleSheet("font-size: 12px;")
        quantity_layout.addWidget(quantity_label)

        self.quantity_input = QLineEdit(self)
        self.quantity_input.setFixedWidth(80)
        self.quantity_input.setText("1")
        self.quantity_input.setStyleSheet("padding: 5px;")
        quantity_layout.addWidget(self.quantity_input)
        quantity_layout.addStretch()

        layout.addWidget(quantity_frame)

        # Buttons
        button_frame = QWidget(self)
        button_layout = QHBoxLayout(button_frame)
        button_layout.setSpacing(10)

        save_button = QPushButton("Save", self)
        save_button.setStyleSheet("padding: 5px 20px;")
        button_layout.addWidget(save_button)

        clear_button = QPushButton("Clear", self)
        clear_button.setStyleSheet("padding: 5px 20px;")
        button_layout.addWidget(clear_button)
        button_layout.addStretch()

        layout.addWidget(button_frame)
        layout.addStretch()

        # Connect signals
        save_button.clicked.connect(self.app.manufacturing_logic.save_work_order)
        clear_button.clicked.connect(self.app.manufacturing_logic.clear_work_order)

class CloseWorkOrderUI(QWidget):
    def __init__(self, parent=None, app=None):
        super().__init__(parent)
        self.app = app
        self.setup_ui()

    def setup_ui(self):
        logger.info("Setting up Close Work Order UI")
        layout = QVBoxLayout(self)
        layout.setContentsMargins(10, 10, 10, 10)
        layout.setSpacing(10)

        # Header
        title_label = QLabel("Close Work Order", self)
        title_label.setStyleSheet("font-size: 16px; font-weight: bold;")
        layout.addWidget(title_label)

        # Work Order Selection
        work_order_frame = QWidget(self)
        work_order_layout = QHBoxLayout(work_order_frame)
        work_order_layout.setSpacing(5)

        work_order_label = QLabel("Select Work Order", self)
        work_order_label.setStyleSheet("font-size: 12px;")
        work_order_layout.addWidget(work_order_label)

        self.work_order_combo = QComboBox(self)
        self.work_order_combo.setFixedWidth(200)
        self.work_order_combo.setStyleSheet("padding: 5px;")
        work_order_layout.addWidget(self.work_order_combo)
        work_order_layout.addStretch()

        layout.addWidget(work_order_frame)

        # Buttons
        button_frame = QWidget(self)
        button_layout = QHBoxLayout(button_frame)
        button_layout.setSpacing(10)

        close_button = QPushButton("Close Work Order", self)
        close_button.setStyleSheet("padding: 5px 20px;")
        button_layout.addWidget(close_button)
        button_layout.addStretch()

        layout.addWidget(button_frame)
        layout.addStretch()

        # Connect signals
        close_button.clicked.connect(self.app.manufacturing_logic.close_selected_work_order)

class AddManufacturedProductDialog(QDialog):
    def __init__(self, parent=None, app=None):
        super().__init__(parent)
        self.app = app
        self.setWindowTitle("Add Manufactured Product")
        self.setFixedSize(400, 300)
        self.setup_ui()

    def setup_ui(self):
        layout = QVBoxLayout(self)
        layout.setContentsMargins(10, 10, 10, 10)
        layout.setSpacing(10)

        title_label = QLabel("Add Manufactured Product", self)
        title_label.setStyleSheet("font-size: 14px; font-weight: bold;")
        layout.addWidget(title_label)

        self.entries = {}
        fields = [("Name*", str), ("Unit*", str), ("Description", str)]
        for label, _ in fields:
            row_widget = QWidget(self)
            row_layout = QHBoxLayout(row_widget)
            row_layout.setSpacing(5)

            field_label = QLabel(label, self)
            field_label.setFixedWidth(100)
            row_layout.addWidget(field_label)

            if label == "Unit*":
                from src.core.utils.utils import UNITS
                combo = QComboBox(self)
                combo.addItems(UNITS)
                combo.setFixedWidth(200)
                combo.setStyleSheet("padding: 5px;")
                self.entries[label] = combo
            else:
                entry = QLineEdit(self)
                entry.setFixedWidth(200)
                entry.setStyleSheet("padding: 5px;")
                self.entries[label] = entry
            row_layout.addWidget(self.entries[label])
            layout.addWidget(row_widget)

        button_frame = QWidget(self)
        button_layout = QHBoxLayout(button_frame)
        button_layout.setSpacing(10)

        save_button = QPushButton("Save", self)
        save_button.setStyleSheet("padding: 5px 20px;")
        button_layout.addWidget(save_button)

        cancel_button = QPushButton("Cancel", self)
        cancel_button.setStyleSheet("padding: 5px 20px;")
        button_layout.addWidget(cancel_button)

        layout.addWidget(button_frame)
        layout.addStretch()

        save_button.clicked.connect(self.app.manufacturing_logic.save_product)
        cancel_button.clicked.connect(self.reject)