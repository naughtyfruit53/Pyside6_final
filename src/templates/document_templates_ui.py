from PySide6.QtWidgets import QDialog, QVBoxLayout, QComboBox, QPushButton, QLabel
from PySide6.QtCore import Qt
import os

class DocumentTemplatesDialog(QDialog):
    def __init__(self, parent=None):
        super().__init__(parent)
        self.setWindowTitle("Generate Document Template")
        self.setFixedSize(400, 200)
        self.setup_ui()

    def setup_ui(self):
        layout = QVBoxLayout(self)
        
        # Template selection
        self.template_label = QLabel("Select Template:", self)
        layout.addWidget(self.template_label)
        
        self.template_combo = QComboBox(self)
        self.template_combo.addItems([
            "Purchase Order",
            "Goods Receipt Note",
            "Rejection Slip",
            "Purchase Invoice",
            "Credit Note",
            "Material Out",
            "Quotation",
            "Sales Order",
            "Proforma Invoice",
            "Sales Invoice",
            "Delivery Challan",
            "Debit Note",
            "Non-Sales Credit Note",
            "Payment Voucher",
            "Receipt Voucher",
            "Contra Voucher",
            "Journal Voucher"
        ])
        layout.addWidget(self.template_combo)
        
        # Generate button
        self.generate_button = QPushButton("Generate PDF", self)
        self.generate_button.setObjectName("generateButton")
        layout.addWidget(self.generate_button)
        
        # Cancel button
        self.cancel_button = QPushButton("Cancel", self)
        self.cancel_button.clicked.connect(self.reject)
        layout.addWidget(self.cancel_button)
        
        layout.addStretch()
        
        # Load stylesheet
        style_path = os.path.join("static", "qss", "templates.qss")
        if os.path.exists(style_path):
            with open(style_path, "r") as f:
                self.setStyleSheet(f.read())

    def get_selected_template(self):
        return self.template_combo.currentText()