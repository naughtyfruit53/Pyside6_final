# src/erp/logic/customers_logic.py
# Converted to SQLAlchemy.

import logging
import pandas as pd
from datetime import datetime
from PySide6.QtWidgets import QFileDialog, QMessageBox
from sqlalchemy import text
from src.erp.logic.database.session import engine, Session
from src.core.config import get_database_url, get_log_path
from src.erp.logic.utils.utils import CUSTOMER_COLUMNS

logger = logging.getLogger(__name__)

def load_customers(widget):
    session = Session()
    try:
        result = session.execute(text("SELECT id, name, contact_no, city, state, gst_no FROM customers")).fetchall()
        widget.customer_tree.setRowCount(0)
        widget.customer_tree.setRowCount(len(result))
        for row, customer in enumerate(result):
            for col, value in enumerate(customer):
                widget.customer_tree.setItem(row, col, QTableWidgetItem(str(value)))
        logger.debug("Customers loaded successfully")
    except Exception as e:
        logger.error(f"Failed to load customers: {e}")
        QMessageBox.critical(widget, "Error", f"Failed to load customers: {e}")
    finally:
        session.close()

def add_customer(app, callback=None):
    if app.add_window_open:
        if app.add_window and not app.add_window.isHidden():
            app.add_window.raise_()
            app.add_window.activateWindow()
        return
    app.add_window = AddCustomerDialog(app.root, app, callback)
    app.add_window_open = True
    app.add_window.show()

def save_customer(app, entries, window, callback=None, refresh_callback=None):
    session = Session()
    mandatory_fields = ["Name*", "Contact No*", "Address Line 1*", "City*", "State*", "State Code*", "PIN Code*"]
    try:
        if not all(entries[field].text() if field != "State*" else entries[field].currentText() for field in mandatory_fields):
            QMessageBox.critical(window, "Error", "All mandatory fields are required")
            return
        insert_stmt = text("""INSERT INTO customers (name, contact_no, address1, address2, city, state,
                    state_code, pin, gst_no, pan_no, email)
                    VALUES (:name, :contact_no, :address1, :address2, :city, :state,
                    :state_code, :pin, :gst_no, :pan_no, :email) RETURNING id""")
        result = session.execute(insert_stmt,
                    {
                        "name": entries["Name*"].text(),
                        "contact_no": entries["Contact No*"].text(),
                        "address1": entries["Address Line 1*"].text(),
                        "address2": entries["Address Line 2"].text(),
                        "city": entries["City*"].text(),
                        "state": entries["State*"].currentText(),
                        "state_code": entries["State Code*"].text(),
                        "pin": entries["PIN Code*"].text(),
                        "gst_no": entries["GST No"].text(),
                        "pan_no": entries["PAN No"].text(),
                        "email": entries["Email"].text()
                    })
        customer_id = result.fetchone()[0]
        customer_name = entries["Name*"].text()
        session.execute(text("INSERT INTO audit_log (table_name, record_id, action, user, timestamp) VALUES ('customers', :customer_id, 'INSERT', 'system_user', :timestamp)"),
                    {"customer_id": customer_id, "timestamp": datetime.now().strftime("%Y-%m-%d %H:%M:%S")})
        session.commit()
        QMessageBox.information(window, "Success", "Customer saved successfully")
        close_window(window, app)
        if callback:
            callback(customer_id, customer_name)
        if refresh_callback:
            refresh_callback()
    except Exception as e:
        session.rollback()
        logger.error(f"Failed to save customer: {e}")
        QMessageBox.critical(window, "Error", f"Failed to save customer: {e}")
    finally:
        session.close()

def edit_customer(app, customer_id, refresh_callback):
    session = Session()
    try:
        result = session.execute(text("SELECT * FROM customers WHERE id = :customer_id"), {"customer_id": customer_id}).fetchone()
        if app.add_window_open:
            if app.add_window and not app.add_window.isHidden():
                app.add_window.raise_()
            return
        entries = {}
        fields = [
            ("Name*", result[1]),
            ("Contact No*", result[2]),
            ("Address Line 1*", result[3]),
            ("Address Line 2", result[4] or ""),
            ("City*", result[5]),
            ("State*", result[6]),
            ("State Code*", result[7]),
            ("PIN Code*", result[8]),
            ("GST No", result[9] or ""),
            ("PAN No", result[10] or ""),
            ("Email", result[11] or "")
        ]
        dialog = AddCustomerDialog(app.root, app, refresh_callback)
        for label, value in fields:
            if label == "State*":
                dialog.entries[label].setCurrentText(value)
            else:
                dialog.entries[label].setText(value)
        dialog.setWindowTitle("Edit Customer")
        dialog.accepted.connect(lambda: save_edit_customer(app, dialog.entries, dialog, customer_id, refresh_callback))
        app.add_window = dialog
        app.add_window_open = True
        dialog.show()
    except Exception as e:
        logger.error(f"Failed to edit customer {customer_id}: {e}")
        QMessageBox.critical(app.root, "Error", f"Failed to fetch customer: {e}")
    finally:
        session.close()

def save_edit_customer(app, entries, window, customer_id, refresh_callback):
    mandatory_fields = ["Name*", "Contact No*", "Address Line 1*", "City*", "State*", "State Code*", "PIN Code*"]
    if not all(entries[field].text() if field != "State*" else entries[field].currentText() for field in mandatory_fields):
        QMessageBox.critical(window, "Error", "All mandatory fields are required")
        return
    session = Session()
    try:
        session.execute(text("""UPDATE customers SET name = :name, contact_no = :contact_no, address1 = :address1, address2 = :address2,
                      city = :city, state = :state, pin = :pin, state_code = :state_code, gst_no = :gst_no, pan_no = :pan_no, email = :email
                      WHERE id = :customer_id"""),
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
                          "customer_id": customer_id
                      })
        session.execute(text("INSERT INTO audit_log (table_name, record_id, action, user, timestamp) VALUES ('customers', :customer_id, 'UPDATE', 'system_user', :timestamp)"),
                      {"customer_id": customer_id, "timestamp": datetime.now().strftime("%Y-%m-%d %H:%M:%S")})
        session.commit()
        QMessageBox.information(window, "Success", "Customer updated successfully")
        close_window(window, app)
        refresh_callback()
    except Exception as e:
        session.rollback()
        logger.error(f"Failed to update customer: {e}")
        QMessageBox.critical(window, "Error", f"Failed to update customer: {e}")
    finally:
        session.close()

def delete_customer(app, customer_id, refresh_callback):
    session = Session()
    if QMessageBox.question(app.root, "Confirm Delete", f"Delete customer ID {customer_id}?") != QMessageBox.Yes:
        return
    try:
        session.execute(text("DELETE FROM customers WHERE id = :customer_id"), {"customer_id": customer_id})
        session.execute(text("INSERT INTO audit_log (table_name, record_id, action, user, timestamp) VALUES ('customers', :customer_id, 'DELETE', 'system_user', :timestamp)"),
                      {"customer_id": customer_id, "timestamp": datetime.now().strftime("%Y-%m-%d %H:%M:%S")})
        session.commit()
        QMessageBox.information(app.root, "Success", f"Customer {customer_id} deleted")
        refresh_callback()
    except Exception as e:
        session.rollback()
        logger.error(f"Failed to delete customer: {e}")
        QMessageBox.critical(app.root, "Error", f"Failed to delete customer: {e}")
    finally:
        session.close()

def import_excel_customers(callback):
    file_path, _ = QFileDialog.getOpenFileName(None, "Select File", "", "Excel files (*.xlsx *.xls);;CSV files (*.csv)")
    if not file_path:
        return
    try:
        df = pd.read_excel(file_path) if file_path.endswith(('.xlsx', '.xls')) else pd.read_csv(file_path)
        mandatory_columns = ["Name", "Contact No", "Address Line 1", "City", "State", "State Code", "PIN Code"]
        if not all(col in df.columns for col in mandatory_columns):
            QMessageBox.critical(None, "Error", f"Excel file must contain columns: {', '.join(CUSTOMER_COLUMNS)}")
            return
        session = Session()
        for _, row in df.iterrows():
            if not all(pd.notna(row[col]) for col in mandatory_columns):
                continue
            insert_stmt = text("""INSERT INTO customers (name, contact_no, address1, address2, city, state,
                state_code, pin, gst_no, pan_no, email)
                VALUES (:name, :contact_no, :address1, :address2, :city, :state,
                :state_code, :pin, :gst_no, :pan_no, :email) RETURNING id""")
            result = session.execute(insert_stmt,
                {
                    "name": row["Name"],
                    "contact_no": row["Contact No"],
                    "address1": row["Address Line 1"],
                    "address2": row.get("Address Line 2", ""),
                    "city": row["City"],
                    "state": row["State"],
                    "state_code": row["State Code"],
                    "pin": row["PIN Code"],
                    "gst_no": row.get("GST No", ""),
                    "pan_no": row.get("PAN No", ""),
                    "email": row.get("Email", "")
                })
            customer_id = result.fetchone()[0]
            session.execute(text("INSERT INTO audit_log (table_name, record_id, action, user, timestamp) VALUES ('customers', :customer_id, 'INSERT', 'system_user', :timestamp)"),
                          {"customer_id": customer_id, "timestamp": datetime.now().strftime("%Y-%m-%d %H:%M:%S")})
        session.commit()
        QMessageBox.information(None, "Success", f"Imported {len(df)} customers")
        callback()
    except Exception as e:
        session.rollback()
        logger.error(f"Failed to import customers: {e}")
        QMessageBox.critical(None, "Error", f"Failed to import customers: {e}")
    finally:
        session.close()

def export_excel_customers():
    file_path, _ = QFileDialog.getSaveFileName(None, "Save File", "customers.xlsx", "Excel files (*.xlsx)")
    if not file_path:
        return
    try:
        session = Session()
        query = text("""SELECT name AS "Name", contact_no AS "Contact No", address1 AS "Address Line 1",
                              address2 AS "Address Line 2", city AS "City", state AS "State",
                              state_code AS "State Code", pin AS "PIN Code", gst_no AS "GST No",
                              pan_no AS "PAN No", email AS "Email"
                       FROM customers""")
        df = pd.read_sql_query(query, session.connection())
        df.to_excel(file_path, index=False)
        QMessageBox.information(None, "Success", f"Exported customers to {file_path}")
    except Exception as e:
        logger.error(f"Failed to export customers: {e}")
        QMessageBox.critical(None, "Error", f"Failed to export customers: {e}")
    finally:
        session.close()

def download_sample_excel():
    file_path, _ = QFileDialog.getSaveFileName(None, "Save Sample File", "sample_customers.xlsx", "Excel files (*.xlsx)")
    if not file_path:
        return
    try:
        df = pd.DataFrame(columns=CUSTOMER_COLUMNS)
        df.to_excel(file_path, index=False)
        QMessageBox.information(None, "Success", f"Sample Excel file saved to {file_path}")
    except Exception as e:
        logger.error(f"Failed to generate sample Excel: {e}")
        QMessageBox.critical(None, "Error", f"Failed to generate sample Excel: {e}")

def close_window(window, app):
    window.reject()
    app.add_window = None
    app.add_window_open = False

def add_customer_dialog(app, parent, callback=None):
    logger.debug("Opening add customer dialog for quotation")
    if app.add_window_open:
        if app.add_window and not app.add_window.isHidden():
            app.add_window.raise_()
            app.add_window.activateWindow()
        logger.debug("Customer dialog already open")
        return
    dialog = AddCustomerDialog(parent, app, callback)
    app.add_window = dialog
    app.add_window_open = True
    dialog.show()