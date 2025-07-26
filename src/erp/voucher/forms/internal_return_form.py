# src/erp/voucher/forms/internal_return_form.py

import os
from PySide6.QtWidgets import QMessageBox  # If any Qt used, but minimal
from ..base_voucher_form import BaseVoucherForm
from src.erp.logic.utils.sequence_utils import get_next_internal_return_sequence

class InternalReturnForm(BaseVoucherForm):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        qss_path = "src/static/qss/internal_return.qss"
        if os.path.exists(qss_path):
            with open(qss_path, "r") as f:
                self.setStyleSheet(f.read())
        self.is_item_based = True
        self.voucher_number = get_next_internal_return_sequence()  # Set voucher number using correct sequence