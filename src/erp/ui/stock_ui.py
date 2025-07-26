# stock_ui.py (revised)

from PySide6.QtWidgets import QWidget, QVBoxLayout, QHBoxLayout, QLabel, QLineEdit, QTableWidget, QTableWidgetItem, QHeaderView, QPushButton, QMenu, QMessageBox, QCheckBox
from PySide6.QtGui import QAction
from PySide6.QtCore import Qt
import logging
import os

logger = logging.getLogger(__name__)

class StockUI(QWidget):
    def __init__(self, parent=None, app=None):
        super().__init__(parent)
        self.app = app
        self.setup_ui()
        # Call set_ui to initialize and load stock data
        if self.app and self.app.stock_logic:
            self.app.stock_logic.set_ui(self)

    def setup_ui(self):
        logger.info("Setting up Stock UI")
        layout = QVBoxLayout(self)
        layout.setContentsMargins(10, 10, 10, 10)
        layout.setSpacing(10)

        # Header
        title_label = QLabel("Stock Management", self)
        title_label.setStyleSheet("font-size: 24px; font-weight: bold; border: none; background-color: transparent;")
        title_label.setAlignment(Qt.AlignCenter)
        layout.addWidget(title_label)

        # Search Bar with Checkbox
        search_frame = QWidget(self)
        search_layout = QHBoxLayout(search_frame)
        search_layout.setSpacing(5)

        search_label = QLabel("Search:", self)
        search_layout.addWidget(search_label)

        self.search_input = QLineEdit(self)
        self.search_input.setPlaceholderText("Enter product name...")
        self.search_input.setStyleSheet("padding: 5px;")
        self.search_input.setFixedWidth(300)  # Decreased size
        search_layout.addWidget(self.search_input)

        search_layout.addStretch()

        self.show_zero_chk = QCheckBox("Show Zero Stock", self)
        self.show_zero_chk.stateChanged.connect(lambda state: self.app.stock_logic.load_stock(show_zero=bool(state)))
        search_layout.addWidget(self.show_zero_chk)

        layout.addWidget(search_frame)

        # Stock Table (rearranged columns, merged Quantity and Unit)
        self.stock_table = QTableWidget(self)
        self.stock_table.setRowCount(0)
        self.stock_table.setColumnCount(6)
        self.stock_table.setHorizontalHeaderLabels([
            "Product Name", "Quantity", "Unit Price", "Total Value", "Reorder Level", "Last Updated"
        ])
        self.stock_table.horizontalHeader().setSectionResizeMode(QHeaderView.ResizeToContents)
        self.stock_table.setStyleSheet("QTableWidget { border: 1px solid #ccc; }")
        self.stock_table.setContextMenuPolicy(Qt.CustomContextMenu)
        self.stock_table.setSortingEnabled(True)
        layout.addWidget(self.stock_table, stretch=1)

        # Button Frame (below table)
        button_frame = QHBoxLayout()

        physical_audit_btn = QPushButton("Physical Audit", self)
        physical_audit_btn.clicked.connect(lambda: QMessageBox.information(self, "Info", "Physical Audit feature coming soon!"))
        button_frame.addWidget(physical_audit_btn)

        manual_entry_btn = QPushButton("Manual Entry", self)
        manual_entry_btn.clicked.connect(self.app.stock_logic.manual_entry)
        button_frame.addWidget(manual_entry_btn)

        import_export_btn = QPushButton("Import/Export", self)
        menu = QMenu(self)
        menu.addAction("Import Stock", self.app.stock_logic.import_stock)
        menu.addAction("Export Stock", self.app.stock_logic.export_stock)
        menu.addAction("Download Sample", self.app.stock_logic.download_sample)
        import_export_btn.setMenu(menu)
        button_frame.addWidget(import_export_btn)

        button_frame.addStretch()

        print_stock_button = QPushButton("Print Stock", self)
        button_frame.addWidget(print_stock_button)

        layout.addLayout(button_frame)

        # Load stylesheet
        style_path = os.path.join("static", "qss", "stock.qss")
        if os.path.exists(style_path):
            with open(style_path, "r") as f:
                self.setStyleSheet(f.read())

        # Connect signals
        self.search_input.textChanged.connect(lambda: self.app.stock_logic.filter_stock(show_zero=self.show_zero_chk.isChecked()))
        self.stock_table.customContextMenuRequested.connect(self.show_context_menu)
        print_stock_button.clicked.connect(self.app.stock_logic.generate_stock_pdf)

    def show_context_menu(self, position):
        menu = QMenu(self)
        view_action = QAction("View Details", self)
        edit_product_action = QAction("Edit Product", self)
        edit_stock_action = QAction("Edit Stock", self)
        menu.addAction(view_action)
        menu.addAction(edit_product_action)
        menu.addAction(edit_stock_action)
        view_action.triggered.connect(self.app.stock_logic.view_product_details)
        edit_product_action.triggered.connect(self.app.stock_logic.edit_product)
        edit_stock_action.triggered.connect(self.app.stock_logic.edit_stock)
        menu.exec(self.stock_table.viewport().mapToGlobal(position))