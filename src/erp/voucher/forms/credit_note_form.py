# src/erp/voucher/forms/credit_note_form.py
# No DB, minimal change.

import os
from PySide6.QtWidgets import QMessageBox  # If any Qt used, but minimal
from ..base_voucher_form import BaseVoucherForm
from src.erp.logic.utils.sequence_utils import get_next_credit_note_sequence

class CreditNoteForm(BaseVoucherForm):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        qss_path = "src/static/qss/credit_note.qss"
        if os.path.exists(qss_path):
            with open(qss_path, "r") as f:
                self.setStyleSheet(f.read())
        self.is_item_based = True
        self.voucher_number = get_next_credit_note_sequence()  # Set voucher number using correct sequence