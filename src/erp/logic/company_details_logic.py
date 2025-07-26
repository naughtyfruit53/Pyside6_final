# src/erp/logic/company_details_logic.py
# Converted to SQLAlchemy.

from PySide6.QtWidgets import QDialog, QMessageBox, QLineEdit, QComboBox, QPushButton
import logging
import os
from datetime import datetime
from sqlalchemy import text
from src.erp.logic.database.session import engine, Session
from src.core.config import get_database_url, get_log_path
from src.erp.ui.default_directory_ui import show_default_directory_setup
from src.erp.logic.default_directory import get_default_directory
from src.erp.logic.utils.utils import update_state_code

logging.basicConfig(
    filename=get_log_path(),
    level=logging.DEBUG,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

def load_company_details(widget, app):
    session = Session()
    try:
        result = session.execute(text("""
            SELECT company_name, address1, address2, city, state, state_code, pin, gst_no, pan_no, contact_no, email, logo_path 
            FROM company_details WHERE id = 1
        """)).fetchone()
        logger.debug(f"Company details loaded: {result}")
        if result:
            fields = ["Company Name*", "Address Line 1*", "Address Line 2", "City*", "State*", "State Code*", "PIN Code*", "GST No", "PAN No", "Contact No*", "Email", "Logo Path"]
            for field, value in zip(fields, result):
                widget.entries[field].setText(value or "")
            if result[4]:
                update_state_code(result[4], widget.entries["State Code*"])
            app.company_details_exist = True
        else:
            logger.info("No company details found")
            for field in widget.entries:
                widget.entries[field].setText("")
            app.company_details_exist = False
    except Exception as e:
        logger.error(f"Failed to load company details: {e}")
        QMessageBox.critical(widget, "Error", f"Failed to load company details: {e}")
        app.company_details_exist = False
    finally:
        session.close()

def save_company_details(widget, app, data):
    session = Session()
    try:
        mandatory_fields = ["company_name", "address1", "city", "state", "state_code", "pin", "contact_no"]
        logger.debug(f"Attempting to save company details: {data}")
        if not all(data[field] for field in mandatory_fields):
            empty_fields = [field for field in mandatory_fields if not data[field]]
            logger.warning(f"Mandatory fields empty: {empty_fields}")
            QMessageBox.critical(widget, "Error", f"All mandatory fields must be filled. Missing: {', '.join(empty_fields)}")
            return False
        default_dir = get_default_directory()
        logger.debug(f"Current default directory before save: {default_dir}")
        session.execute(text("""INSERT INTO company_details (
            id, company_name, address1, address2, city, state, pin, state_code,
            gst_no, pan_no, contact_no, email, logo_path, default_directory
        ) VALUES (1, :company_name, :address1, :address2, :city, :state, :pin, :state_code,
            :gst_no, :pan_no, :contact_no, :email, :logo_path, :default_directory)
        ON CONFLICT (id) DO UPDATE SET
            company_name = EXCLUDED.company_name, address1 = EXCLUDED.address1, address2 = EXCLUDED.address2, city = EXCLUDED.city, 
            state = EXCLUDED.state, pin = EXCLUDED.pin, state_code = EXCLUDED.state_code,
            gst_no = EXCLUDED.gst_no, pan_no = EXCLUDED.pan_no, contact_no = EXCLUDED.contact_no, 
            email = EXCLUDED.email, logo_path = EXCLUDED.logo_path, default_directory = EXCLUDED.default_directory"""),
            {
                "company_name": data["company_name"],
                "address1": data["address1"],
                "address2": data.get("address2", ""),
                "city": data["city"],
                "state": data["state"],
                "pin": data["pin"],
                "state_code": data["state_code"],
                "gst_no": data.get("gst_no", ""),
                "pan_no": data.get("pan_no", ""),
                "contact_no": data["contact_no"],
                "email": data.get("email", ""),
                "logo_path": data.get("logo_path", ""),
                "default_directory": default_dir
            })
        session.execute(text('INSERT INTO audit_log (table_name, record_id, action, username, timestamp) VALUES (:table_name, :record_id, :action, :username, :timestamp)'),
            {"table_name": 'company_details', "record_id": 1, "action": 'UPDATE', "username": 'system_user', "timestamp": datetime.now().strftime("%Y-%m-%d %H:%M:%S")})
        session.commit()
        # Verify
        saved_data = session.execute(text("SELECT * FROM company_details WHERE id = 1")).fetchone()
        logger.debug(f"Company details saved and verified: {saved_data}")
        QMessageBox.information(widget, "Success", "Company details saved successfully")
        app.company_details_exist = True
        app.default_directory_set = bool(default_dir)
        logger.debug(f"Default directory after save: {default_dir}, default_directory_set: {app.default_directory_set}")
        if not app.default_directory_set:
            logger.info("No default directory set, prompting setup")
            try:
                if app.dir_win is None:
                    app.dir_win = show_default_directory_setup(app)
                    if app.dir_win:
                        app.dir_win.finished.connect(app.on_default_directory_dialog_finished)
                        app.dir_win.show()
                        app.dir_win.raise_()
                        app.dir_win.activateWindow()
                        logger.debug("Default directory dialog shown")
                    else:
                        logger.error("Default directory dialog returned None")
                        return False
            except Exception as e:
                logger.error(f"Error showing default directory setup: {e}")
                QMessageBox.critical(widget, "Error", f"Failed to show default directory setup: {e}")
                return False
        else:
            from src.core.frames import initialize_frames
            app.frames = initialize_frames(app)
            target_frame = "home"
            logger.debug(f"Navigating to target frame after save: {target_frame}")
            app.show_frame(target_frame, add_to_history=False)
        return True
    except Exception as e:
        session.rollback()
        logger.error(f"Failed to save company details: {e}")
        QMessageBox.critical(widget, "Error", f"Failed to save company details: {e}")
        return False
    finally:
        session.close()

def cancel_company_details(widget, app):
    try:
        logger.debug(f"Cancel button clicked, frame history: {app.frame_history}")
        load_company_details(widget, app)
        target_frame = "home" if not app.frame_history or len(app.frame_history) <= 1 else app.frame_history[-2]
        if target_frame not in app.frames:
            logger.warning(f"Target frame {target_frame} not found, falling back to home")
            target_frame = "home"
        logger.debug(f"Navigating to target frame on cancel: {target_frame}")
        app.show_frame(target_frame, add_to_history=False)
    except Exception as e:
        logger.error(f"Failed to navigate to {target_frame}: {e}")
        QMessageBox.critical(widget, "Navigation Error", f"Failed to navigate back: {e}")
        app.show_frame("home", add_to_history=False)

def show_company_setup(app):
    from src.erp.ui.company_details_ui import CompanySetupDialog
    try:
        if app.setup_shown or app.setup_win is not None:
            logger.debug("Company setup window already open, focusing existing window")
            if app.setup_win and not app.setup_win.isHidden():
                app.setup_win.raise_()
                app.setup_win.activateWindow()
            return
        app.setup_shown = True
        app.setup_win = CompanySetupDialog(app, app)
        app.setup_win.setEnabled(True)
        for widget_type in [QLineEdit, QComboBox, QPushButton]:
            for widget in app.setup_win.findChildren(widget_type):
                widget.setEnabled(True)
                logger.debug(f"Widget {widget.objectName()} enabled: {widget.isEnabled()}")
        app.setup_win.finished.connect(lambda: on_dialog_finished(app))
        logger.debug(f"Showing CompanySetupDialog, enabled: {app.setup_win.isEnabled()}")
        app.setup_win.show()
        app.setup_win.raise_()
        app.setup_win.activateWindow()
    except Exception as e:
        logger.error(f"Error creating company setup window: {e}")
        QMessageBox.critical(app, "Error", f"Failed to create company setup: {e}")
        app.setup_shown = False
        app.setup_win = None

def on_dialog_finished(app):
    try:
        logger.debug("Company setup dialog closed")
        app.setup_shown = False
        app.setup_win = None
        if app.company_details_exist:
            default_dir = get_default_directory()
            app.default_directory_set = bool(default_dir)
            if not app.default_directory_set:
                logger.info("No default directory set, prompting setup")
                if app.dir_win is None:
                    app.dir_win = show_default_directory_setup(app)
                    if app.dir_win:
                        app.dir_win.finished.connect(app.on_default_directory_dialog_finished)
                        app.dir_win.show()
                        app.dir_win.raise_()
                        app.dir_win.activateWindow()
                        logger.debug("Default directory dialog shown")
                    else:
                        logger.error("Default directory dialog returned None")
                        app.frames = initialize_frames(app)
                        app.show_frame("home", add_to_history=False)
            else:
                from src.core.frames import initialize_frames
                app.frames = initialize_frames(app)
                logger.debug("Navigating to home after dialog close")
                app.show_frame("home", add_to_history=False)
        else:
            logger.info("No company details exist, prompting setup again")
            show_company_setup(app)
    except Exception as e:
        logger.error(f"Error in on_dialog_finished: {e}")
        app.frames = initialize_frames(app)
        app.show_frame("home", add_to_history=False)