import os
from PySide6.QtWidgets import QMessageBox  # If any Qt used, but minimal
from ..base_voucher_form import BaseVoucherForm

REJECTION_PRODUCT_COLUMNS = [
    ("Product Name", "text", True),
    ("Quantity", "real", True),
    ("Unit", "text", True),
    ("Reason", "text", False)
]

class RejectionInOutForm(BaseVoucherForm):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        qss_path = "src/static/qss/rejection_in_out.qss"
        if os.path.exists(qss_path):
            with open(qss_path, "r") as f:
                self.setStyleSheet(f.read())
        self.is_item_based = True
        self.product_columns = REJECTION_PRODUCT_COLUMNS