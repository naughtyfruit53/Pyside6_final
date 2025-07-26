# src/erp/logic/pending_logic.py
# Converted to SQLAlchemy.

import logging
from PySide6.QtWidgets import QMessageBox
from sqlalchemy import text
from src.core.config import get_database_url

logger = logging.getLogger(__name__)

class PendingLogic:
    def __init__(self, app):
        self.app = app
        self.pending_ui = None

    def set_ui(self, pending_ui):
        self.pending_ui = pending_ui
        self.load_pending()

    def load_pending(self):
        session = Session()
        try:
            result = session.execute(text("""
                SELECT mt.doc_number, mt.type, mt.date, p.name, mt.quantity
                FROM material_transactions mt
                JOIN products p ON mt.product_id = p.id
                WHERE mt.type IN ('Purchase Order', 'Goods Receipt Note')
                ORDER BY mt.date DESC
            """)).fetchall()
            self.pending_ui.pending_table.setRowCount(0)
            for row_idx, row_data in enumerate(result):
                self.pending_ui.pending_table.insertRow(row_idx)
                for col_idx, value in enumerate(row_data):
                    self.pending_ui.pending_table.setItem(row_idx, col_idx, QTableWidgetItem(str(value)))
        except Exception as e:
            logger.error(f"Failed to load pending transactions: {e}")
            QMessageBox.critical(self.pending_ui, "Error", f"Failed to load pending transactions: {e}")
        finally:
            session.close()

    def filter_pending(self):
        search_text = self.pending_ui.search_input.text().lower()
        session = Session()
        try:
            query = text("""
                SELECT mt.doc_number, mt.type, mt.date, p.name, mt.quantity
                FROM material_transactions mt
                JOIN products p ON mt.product_id = p.id
                WHERE mt.type IN ('Purchase Order', 'Goods Receipt Note')
                AND (p.name LIKE :search_text OR mt.doc_number LIKE :search_text)
                ORDER BY mt.date DESC
            """)
            result = session.execute(query, {"search_text": f"%{search_text}%"}).fetchall()
            self.pending_ui.pending_table.setRowCount(0)
            for row_idx, row_data in enumerate(result):
                self.pending_ui.pending_table.insertRow(row_idx)
                for col_idx, value in enumerate(row_data):
                    self.pending_ui.pending_table.setItem(row_idx, col_idx, QTableWidgetItem(str(value)))
        except Exception as e:
            logger.error(f"Failed to filter pending transactions: {e}")
            QMessageBox.critical(self.pending_ui, "Error", f"Failed to filter pending transactions: {e}")
        finally:
            session.close()