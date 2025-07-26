# src/erp/logic/vendors_logic.py
# Converted to use SQLAlchemy.

import logging
import pandas as pd
from datetime import datetime
from PySide6.QtWidgets import QFileDialog, QMessageBox, QTableWidgetItem
from sqlalchemy import text
from src.erp.logic.database.session import engine, Session
from src.core.config import get_database_url, get_log_path
from src.erp.logic.utils.utils import VENDOR_COLUMNS
from src.erp.ui.vendors_ui import AddVendorDialog

logger = logging.getLogger(__name__)

def load_vendors(widget):
    session = Session()
    try:
        result = session.execute(text("SELECT id, name, contact_no, city, state, gst_no FROM vendors")).fetchall()
        widget.vendor_table.setRowCount(0)
        widget.vendor_table.setRowCount(len(result))
        for row, vendor in enumerate(result):
            for col, value in enumerate(vendor):
                widget.vendor_table.setItem(row, col, QTableWidgetItem(str(value)))
        logger.debug("Vendors loaded successfully")
    except Exception as e:
        logger.error(f"Failed to load vendors: {e}")
        QMessageBox.critical(widget, "Error", f"Failed to load vendors: {e}")
    finally:
        session.close()

def add_vendor(app, parent=None, callback=None):
    if app.add_window_open:
        if app.add_window and not app.add_window.isHidden():
            app.add_window.raise_()
            app.add_window.activateWindow()
        return
    app.add_window = AddVendorDialog(parent, app, callback)
    app.add_window_open = True
    app.add_window.show()

def save_vendor(app, entries, window, callback=None):
    mandatory_fields = ["Name*", "Contact No*", "Address Line 1*", "City*", "State*", "State Code*", "PIN Code*"]
    if not all(entries[field].text() if field != "State*" else entries[field].currentText() for field in mandatory_fields):
        QMessageBox.critical(window, "Error", "All mandatory fields are required")
        return
    session = Session()
    try:
        insert_stmt = text("""INSERT INTO vendors (name, contact_no, address1, address2, city, state,
                        pin, state_code, gst_no, pan_no, email)
                        VALUES (:name, :contact_no, :address1, :address2, :city, :state,
                        :pin, :state_code, :gst_no, :pan_no, :email) RETURNING id""")
        result = session.execute(insert_stmt,
                        {
                            "name": entries["Name*"].text(),
                            "contact_no": entries["Contact No*"].text(),
                            "address1": entries["Address Line 1*"].text(),
                            "address2": entries["Address Line 2"].text(),
                            "city": entries["City*"].text(),
                            "state": entries["State*"].currentText(),
                            "pin": entries["PIN Code*"].text(),
                            "state_code": entries["State Code*"].text(),
                            "gst_no": entries["GST No"].text(),
                            "pan_no": entries["PAN No"].text(),
                            "email": entries["Email"].text()
                        })
        vendor_id = result.fetchone()[0]
        vendor_name = entries["Name*"].text()
        session.execute(text("INSERT INTO audit_log (table_name, record_id, action, username, timestamp) VALUES (:table_name, :record_id, :action, :username, :timestamp)"),
                        {"table_name": "vendors", "record_id": vendor_id, "action": "INSERT", "username": "system_user", "timestamp": datetime.now()})
        session.commit()
        QMessageBox.information(window, "Success", "Vendor saved successfully")
        close_window(window, app)
        if callback:
            callback(vendor_id, vendor_name)
    except Exception as e:
        session.rollback()
        logger.error(f"Failed to save vendor: {e}")
        QMessageBox.critical(window, "Error", f"Failed to save vendor: {e}")
    finally:
        session.close()

def edit_vendor(app, parent, vendor_id, refresh_callback):
    session = Session()
    try:
        vendor = session.execute(text("SELECT * FROM vendors WHERE id = :vendor_id"), {"vendor_id": vendor_id}).fetchone()
    except Exception as e:
        logger.error(f"Failed to fetch vendor {vendor_id}: {e}")
        QMessageBox.critical(parent, "Error", f"Failed to fetch vendor: {e}")
        session.close()
        return
    finally:
        session.close()
    if app.add_window_open:
        if app.add_window and not app.add_window.isHidden():
            app.add_window.raise_()
        return
    fields = [
        ("Name*", vendor[1]),
        ("Contact No*", vendor[2]),
        ("Address Line 1*", vendor[3]),
        ("Address Line 2", vendor[4] or ""),
        ("City*", vendor[5]),
        ("State*", vendor[6]),
        ("State Code*", vendor[7]),
        ("PIN Code*", vendor[8]),
        ("GST No", vendor[9] or ""),
        ("PAN No", vendor[10] or ""),
        ("Email", vendor[11] or ""),
    ]
    dialog = AddVendorDialog(parent, app, refresh_callback, None, True, vendor_id)
    for label, value in fields:
        if label == "State*":
            dialog.entries[label].setCurrentText(value)
        else:
            dialog.entries[label].setText(str(value))
    dialog.setWindowTitle("Edit Vendor")
    app.add_window = dialog
    app.add_window_open = True
    dialog.show()

def save_edit_vendor(app, entries, window, vendor_id, refresh_callback):
    mandatory_fields = ["Name*", "Contact No*", "Address Line 1*", "City*", "State*", "State Code*", "PIN Code*"]
    if not all(entries[field].text() if field != "State*" else entries[field].currentText() for field in mandatory_fields):
        QMessageBox.critical(window, "Error", "All mandatory fields are required")
        return
    session = Session()
    try:
        session.execute(text("""UPDATE vendors SET name = :name, contact_no = :contact_no, address1 = :address1, address2 = :address2,
                      city = :city, state = :state, pin = :pin, state_code = :state_code, gst_no = :gst_no, pan_no = :pan_no, email = :email
                      WHERE id = :vendor_id"""),
                      {
                          "name": entries["Name*"].text(),
                          "contact_no": entries["Contact No*"].text(),
                          "address1": entries["Address Line 1*"].text(),
                          "address2": entries["Address Line 2"].text(),
                          "city": entries["City*"].text(),
                          "state": entries["State*"].currentText(),
                          "pin": entries["PIN Code*"].text(),
                          "state_code": entries["State Code*"].text(),
                          "gst_no": entries["GST No"].text(),
                          "pan_no": entries["PAN No"].text(),
                          "email": entries["Email"].text(),
                          "vendor_id": vendor_id
                      })
        session.execute(text("INSERT INTO audit_log (table_name, record_id, action, username, timestamp) VALUES (:table_name, :record_id, :action, :username, :timestamp)"),
                        {"table_name": "vendors", "record_id": vendor_id, "action": "UPDATE", "username": "system_user", "timestamp": datetime.now()})
        session.commit()
        QMessageBox.information(window, "Success", "Vendor updated successfully")
        close_window(window, app)
        refresh_callback()
    except Exception as e:
        session.rollback()
        logger.error(f"Failed to update vendor: {e}")
        QMessageBox.critical(window, "Error", f"Failed to update vendor: {e}")
    finally:
        session.close()

def delete_vendor(app, parent, vendor_id, refresh_callback):
    if QMessageBox.question(parent, "Confirm", f"Delete vendor ID {vendor_id}?") != QMessageBox.Yes:
        return
    session = Session()
    try:
        session.execute(text("DELETE FROM vendors WHERE id = :vendor_id"), {"vendor_id": vendor_id})
        session.execute(text("INSERT INTO audit_log (table_name, record_id, action, username, timestamp) VALUES (:table_name, :record_id, :action, :username, :timestamp)"),
                        {"table_name": "vendors", "record_id": vendor_id, "action": "DELETE", "username": "system_user", "timestamp": datetime.now()})
        session.commit()
        QMessageBox.information(parent, "Success", f"Vendor {vendor_id} deleted")
        refresh_callback()
    except Exception as e:
        session.rollback()
        logger.error(f"Failed to delete vendor: {e}")
        QMessageBox.critical(parent, "Error", f"Failed to delete vendor: {e}")
    finally:
        session.close()

def import_excel_vendors(callback):
    file_path, _ = QFileDialog.getOpenFileName(None, "Select File", "", "Excel files (*.xlsx *.xls);;CSV files (*.csv)")
    if not file_path:
        return
    try:
        df = pd.read_excel(file_path) if file_path.endswith(('.xlsx', '.xls')) else pd.read_csv(file_path)
        mandatory_columns = ["Name", "Contact No", "Address Line 1", "City", "State", "State Code", "PIN Code"]
        if not all(col in df.columns for col in mandatory_columns):
            QMessageBox.critical(None, "Error", f"Excel file must contain columns: {', '.join(VENDOR_COLUMNS)}")
            return
        session = Session()
        try:
            for _, row in df.iterrows():
                if not all(pd.notna(row[col]) for col in mandatory_columns):
                    continue
                insert_stmt = text("""INSERT INTO vendors (name, contact_no, address1, address2, city, state,
                    state_code, pin, gst_no, pan_no, email)
                    VALUES (:name, :contact_no, :address1, :address2, :city, :state,
                    :state_code, :pin, :gst_no, :pan_no, :email) RETURNING id""")
                result = session.execute(insert_stmt,
                    {
                        "name": row["Name"], "contact_no": row["Contact No"], "address1": row["Address Line 1"], "address2": row.get("Address Line 2", ""),
                        "city": row["City"], "state": row["State"], "state_code": row["State Code"], "pin": row["PIN Code"],
                        "gst_no": row.get("GST No", ""), "pan_no": row.get("PAN No", ""), "email": row.get("Email", "")
                    })
                vendor_id = result.fetchone()[0]
                session.execute(text("INSERT INTO audit_log (table_name, record_id, action, username, timestamp) VALUES (:table_name, :record_id, :action, :username, :timestamp)"),
                                {"table_name": "vendors", "record_id": vendor_id, "action": "INSERT", "username": "system_user", "timestamp": datetime.now()})
            session.commit()
            QMessageBox.information(None, "Success", f"Imported {len(df)} vendors")
            callback()
        except Exception as e:
            session.rollback()
            raise e
    except Exception as e:
        logger.error(f"Failed to import vendors: {e}")
        QMessageBox.critical(None, "Error", f"Failed to import vendors: {e}")
    finally:
        session.close()

def export_excel_vendors():
    file_path, _ = QFileDialog.getSaveFileName(None, "Save File", "vendors.xlsx", "Excel files (*.xlsx)")
    if not file_path:
        return
    try:
        session = Session()
        query = text("""SELECT name AS "Name", contact_no AS "Contact No", address1 AS "Address Line 1",
                              address2 AS "Address Line 2", city AS "City", state AS "State",
                              state_code AS "State Code", pin AS "PIN Code", gst_no AS "GST No",
                              pan_no AS "PAN No", email AS "Email"
                       FROM vendors""")
        df = pd.read_sql_query(query, session.connection())
        df.to_excel(file_path, index=False)
        QMessageBox.information(None, "Success", f"Exported vendors to {file_path}")
    except Exception as e:
        logger.error(f"Failed to export vendors: {e}")
        QMessageBox.critical(None, "Error", f"Failed to export vendors: {e}")
    finally:
        session.close()

def download_sample_excel():
    file_path, _ = QFileDialog.getSaveFileName(None, "Save Sample File", "sample_vendors.xlsx", "Excel files (*.xlsx)")
    if not file_path:
        return
    try:
        df = pd.DataFrame(columns=VENDOR_COLUMNS)
        df.to_excel(file_path, index=False)
        QMessageBox.information(None, "Success", f"Sample Excel file saved to {file_path}")
    except Exception as e:
        logger.error(f"Failed to generate sample Excel: {e}")
        QMessageBox.critical(None, "Error", f"Failed to generate sample Excel: {e}")

def close_window(window, app):
    window.reject()
    app.add_window = None
    app.add_window_open = False

def add_vendor_dialog(app, parent, callback=None):
    logger.debug("Opening add vendor dialog")
    if app.add_window_open:
        if app.add_window and not app.add_window.isHidden():
            app.add_window.raise_()
            app.add_window.activateWindow()
        logger.debug("Vendor dialog already open")
        return
    dialog = AddVendorDialog(parent, app, callback)
    app.add_window = dialog
    app.add_window_open = True
    dialog.show()