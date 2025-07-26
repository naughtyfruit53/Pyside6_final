# src/erp/ui/products_ui.py
# Converted to use SQLAlchemy in load_data and update_table.

from PySide6.QtWidgets import QWidget, QVBoxLayout, QHBoxLayout, QLabel, QLineEdit, QTableWidget, QTableWidgetItem, QHeaderView, QPushButton, QMenu, QMessageBox
from PySide6.QtCore import Qt, Signal
import logging
import os
from sqlalchemy import text
from src.erp.logic.database.session import engine, Session
from src.core.config import get_database_url

logger = logging.getLogger(__name__)

class ProductsWidget(QWidget):
    product_selected = Signal(int, str)  # Signal for product selection (id, name)

    def __init__(self, parent=None, app=None):
        super().__init__(parent)
        self.app = app
        self.setup_ui()

    def setup_ui(self):
        logger.info("Creating products widget")
        main_layout = QVBoxLayout(self)
        main_layout.setContentsMargins(10, 10, 10, 10)

        # Title
        title_label = QLabel("Products")
        title_label.setObjectName("titleLabel")
        title_label.setAlignment(Qt.AlignCenter)
        main_layout.addWidget(title_label)

        # Search bar
        search_layout = QHBoxLayout()
        search_label = QLabel("Search:")
        search_label.setObjectName("fieldLabel")
        self.search_entry = QLineEdit()
        self.search_entry.setObjectName("textEntry")
        self.search_entry.setPlaceholderText("Search products...")
        self.search_entry.textChanged.connect(self.update_table)
        search_layout.addWidget(search_label)
        search_layout.addWidget(self.search_entry)
        main_layout.addLayout(search_layout)

        # Table
        self.product_table = QTableWidget()
        self.product_table.setColumnCount(6)
        self.product_table.setHorizontalHeaderLabels(["ID", "Name", "HSN Code", "Unit", "Unit Price", "GST Rate"])
        self.product_table.setObjectName("productTable")
        self.product_table.horizontalHeader().setSectionResizeMode(QHeaderView.Stretch)
        self.product_table.setSelectionMode(QTableWidget.SingleSelection)
        self.product_table.setContextMenuPolicy(Qt.CustomContextMenu)
        self.product_table.customContextMenuRequested.connect(self.show_context_menu)
        self.product_table.doubleClicked.connect(self.edit_product)
        main_layout.addWidget(self.product_table)

        # Buttons
        button_layout = QHBoxLayout()
        add_button = QPushButton("Add Product")
        add_button.setObjectName("actionButton")
        add_button.clicked.connect(lambda: self.app.logic.products_logic.add_product(self.app, parent=self, callback=lambda id, name: self.load_data()))
        edit_button = QPushButton("Edit Product")
        edit_button.setObjectName("actionButton")
        edit_button.clicked.connect(self.edit_product)
        delete_button = QPushButton("Delete Product")
        delete_button.setObjectName("actionButton")
        delete_button.clicked.connect(self.delete_product)

        import_export_btn = QPushButton("Import/Export")
        import_export_btn.setObjectName("actionButton")
        menu = QMenu(self)
        menu.addAction("Import Products", lambda: self.app.logic.products_logic.import_products(self.app, self.load_data))
        menu.addAction("Export Products", lambda: self.app.logic.products_logic.export_products())
        menu.addAction("Download Sample", lambda: self.app.logic.products_logic.download_sample())
        import_export_btn.setMenu(menu)

        button_layout.addWidget(add_button)
        button_layout.addWidget(edit_button)
        button_layout.addWidget(delete_button)
        button_layout.addWidget(import_export_btn)
        main_layout.addLayout(button_layout)

        # Load stylesheet
        style_path = os.path.join("static", "qss", "products.qss")
        if os.path.exists(style_path):
            with open(style_path, "r") as f:
                self.setStyleSheet(f.read())

        self.load_data()

    def load_data(self):
        session = Session()
        try:
            result = session.execute(text("SELECT id, name, hsn_code, unit, unit_price, gst_rate FROM products")).fetchall()
            self.product_table.setRowCount(0)
            self.product_table.setRowCount(len(result))
            for row, product in enumerate(result):
                for col, value in enumerate(product):
                    self.product_table.setItem(row, col, QTableWidgetItem(str(value)))
            logger.debug(f"Loaded {len(result)} products into table")
        except Exception as e:
            logger.error(f"Error loading products: {e}")
            QMessageBox.critical(self, "Error", f"Failed to load products: {e}")
        finally:
            session.close()

    def update_table(self):
        session = Session()
        try:
            search_term = self.search_entry.text().lower()
            self.product_table.setRowCount(0)
            result = session.execute(text("SELECT id, name, hsn_code, unit, unit_price, gst_rate FROM products")).fetchall()
            filtered_products = [
                p for p in result if not search_term or any(search_term in str(val).lower() for val in p)
            ]
            self.product_table.setRowCount(len(filtered_products))
            for row, product in enumerate(filtered_products):
                for col, value in enumerate(product):
                    self.product_table.setItem(row, col, QTableWidgetItem(str(value)))
            logger.debug(f"Updated table with search term: {search_term}")
        except Exception as e:
            logger.error(f"Error updating products: {e}")
            QMessageBox.critical(self, "Error", f"Failed to update products: {e}")
        finally:
            session.close()

    def show_context_menu(self, pos):
        if self.product_table.selectedItems():
            menu = QMenu()
            edit_action = menu.addAction("Edit")
            delete_action = menu.addAction("Delete")
            edit_action.triggered.connect(self.edit_product)
            delete_action.triggered.connect(self.delete_product)
            menu.exec(self.product_table.viewport().mapToGlobal(pos))

    def edit_product(self):
        if not self.product_table.selectedItems():
            QMessageBox.warning(self, "Warning", "Select a product")
            return
        product_id = self.product_table.item(self.product_table.currentRow(), 0).text()
        self.app.logic.products_logic.edit_product(self.app, product_id, lambda id, name: self.load_data(), parent=self)

    def delete_product(self):
        if not self.product_table.selectedItems():
            QMessageBox.warning(self, "Warning", "Select a product")
            return
        product_id = self.product_table.item(self.product_table.currentRow(), 0).text()
        self.app.logic.products_logic.delete_product(self.app, product_id, self.load_data)