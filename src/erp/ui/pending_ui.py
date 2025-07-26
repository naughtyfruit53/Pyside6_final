from PySide6.QtWidgets import QWidget, QVBoxLayout, QHBoxLayout, QLabel, QLineEdit, QTableWidget, QTableWidgetItem, QHeaderView
from PySide6.QtCore import Qt
import logging
import os

logger = logging.getLogger(__name__)

class PendingUI(QWidget):
    def __init__(self, parent=None, app=None):
        super().__init__(parent)
        self.app = app
        self.setup_ui()

    def setup_ui(self):
        logger.info("Setting up Pending UI")
        layout = QVBoxLayout(self)
        layout.setContentsMargins(10, 10, 10, 10)
        layout.setSpacing(10)

        # Header
        title_label = QLabel("Pending Materials", self)
        title_label.setStyleSheet("font-size: 24px; font-weight: bold;")
        layout.addWidget(title_label)

        description_label = QLabel(
            "View pending material transactions, including purchase orders and goods receipt notes.",
            self)
        description_label.setWordWrap(True)
        description_label.setStyleSheet("font-size: 14px;")
        layout.addWidget(description_label)

        # Search Bar
        search_frame = QWidget(self)
        search_layout = QHBoxLayout(search_frame)
        search_layout.setSpacing(5)

        search_label = QLabel("Search:", self)
        search_layout.addWidget(search_label)

        self.search_input = QLineEdit(self)
        self.search_input.setPlaceholderText("Enter product or document number...")
        self.search_input.setStyleSheet("padding: 5px;")
        search_layout.addWidget(self.search_input)
        search_layout.addStretch()

        layout.addWidget(search_frame)

        # Pending Table
        self.pending_table = QTableWidget(self)
        self.pending_table.setRowCount(0)
        self.pending_table.setColumnCount(5)
        self.pending_table.setHorizontalHeaderLabels(["Document Number", "Type", "Date", "Product", "Quantity"])
        self.pending_table.horizontalHeader().setSectionResizeMode(QHeaderView.Stretch)
        self.pending_table.setStyleSheet("QTableWidget { border: 1px solid #ccc; }")
        layout.addWidget(self.pending_table)

        layout.addStretch()

        # Load stylesheet
        style_path = os.path.join("static", "qss", "pending.qss")
        if os.path.exists(style_path):
            with open(style_path, "r") as f:
                self.setStyleSheet(f.read())

        # Connect signals
        self.search_input.textChanged.connect(self.app.pending_logic.filter_pending)