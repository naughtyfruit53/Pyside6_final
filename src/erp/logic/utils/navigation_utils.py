# logic.utils.navigation_utils.py

from PySide6.QtWidgets import QFrame, QMessageBox
import logging
from src.core.config import get_database_url, get_log_path
from src.core.frames import (
    create_home_frame, create_dashboard_frame, create_master_frame, create_vouchers_frame,
    create_service_frame, create_hr_management_frame, create_backup_boss_frame, create_reset_frame
)
from src.erp.ui.company_details_ui import CompanyDetailsWidget
from src.erp.ui.vendors_ui import VendorsWidget
from src.erp.ui.products_ui import ProductsWidget
from src.erp.ui.customers_ui import CustomersWidget
from src.erp.ui.default_directory_ui import create_default_directory_frame
from src.erp.ui.user_management_ui import UserManagementWidget
from src.erp.ui.backup_restore_ui import create_backup_frame, create_restore_frame, create_auto_backup_frame
from src.erp.ui.stock_ui import StockUI
from src.erp.ui.manufacturing_ui import ManufacturingUI, BOMUI, WorkOrderUI, CloseWorkOrderUI
from src.erp.voucher.voucher_ui import VoucherUI
from src.erp.logic.database.voucher import get_voucher_types, get_voucher_types_by_module
from src.erp.logic.user_management_logic import get_user_permissions

logging.basicConfig(
    filename=get_log_path(),
    level=logging.DEBUG,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

frame_classes = {
    "home": create_home_frame,
    "dashboard": create_dashboard_frame,
    "company": CompanyDetailsWidget,
    "vendors": VendorsWidget,
    "products": ProductsWidget,
    "customers": CustomersWidget,
    "stock": StockUI,
    "manufacturing": ManufacturingUI,
    "create_bom": BOMUI,
    "create_work_order": WorkOrderUI,
    "close_work_order": CloseWorkOrderUI,
    "master": create_master_frame,
    "vouchers": create_vouchers_frame,
    "service": create_service_frame,
    "hr_management": create_hr_management_frame,
    "backup_boss": create_backup_boss_frame,
    "backup": create_backup_frame,
    "restore": create_restore_frame,
    "auto_backup": create_auto_backup_frame,
    "default_directory": create_default_directory_frame,
    "user_management": UserManagementWidget,
    "reset": create_reset_frame,  # Added reset frame
}

# Dynamically add voucher-specific frames
for voucher_type in get_voucher_types():
    frame_name = f"vouchers-{voucher_type[1].lower().replace(' ', '_')}"
    frame_classes[frame_name] = lambda parent, app, fn=frame_name: VoucherUI(app).create_voucher_frame(parent, app, None, fn)

def show_frame(app, name, add_to_history=True):
    """Show a specific frame based on the name."""
    logger.debug(f"Attempting to show frame: {name}, frame_history: {app.frame_history}, add_to_history={add_to_history}")
    
    login_frames = ["login", "first_run", "password_change"]
    if not app.current_user and name not in login_frames:
        logger.warning(f"No user logged in, cannot show frame: {name}")
        QMessageBox.critical(None, "Error", "Please log in to access this feature")
        return
    
    if app.current_user and app.current_user['username'] == "admins" and name != "user_management":
        logger.warning(f"Admins attempted to access restricted frame: {name}")
        QMessageBox.critical(None, "Access Denied", "Admins account access is restricted to User Management")
        return
    
    if app.current_user and name not in login_frames + ["company", "user_management"]:
        if not app.company_details_exist and app.current_user['username'] != "admins":
            logger.warning(f"Company details not set, redirecting to company setup from frame: {name}")
            QMessageBox.warning(None, "Setup Required", "Please complete company setup before proceeding")
            name = "company"

    if app.current_user and name not in login_frames + ["company"]:
        permitted = get_user_permissions(app.current_user['id'])
        logger.debug(f"Checking permissions for frame {name}. Permitted frames: {permitted}")
        if name not in frame_classes:
            logger.error(f"Frame {name} not found in frame_classes")
            QMessageBox.critical(None, "Error", f"Frame {name} not found")
            app.show_frame("home", add_to_history=False)
            return
        if name not in permitted and app.current_user['role'] not in ['super_admin', 'admin']:
            logger.error(f"User {app.current_user['id']} (username: {app.current_user['username']}, role: {app.current_user['role']}) attempted to access restricted frame: {name}")
            QMessageBox.critical(None, "Access Denied", f"You do not have permission to access {name.replace('_', ' ').title()}")
            return

    try:
        # Clean up deleted frames
        new_frames = {}
        for k, v in app.frames.items():
            try:
                if v and not v.isHidden():
                    new_frames[k] = v
            except RuntimeError as e:
                logger.warning(f"Skipping frame {k} due to deletion: {e}")
                continue
        app.frames = new_frames
        
        if name not in app.frames:
            frame_func = frame_classes.get(name)
            if frame_func:
                logger.debug(f"Initializing frame: {name}")
                frame = frame_func(app.right_pane, app)
                if frame is None:
                    logger.error(f"Failed to initialize frame {name}: Function returned None")
                    QMessageBox.critical(None, "Error", f"Failed to initialize {name.replace('_', ' ').title()}")
                    app.show_frame("home", add_to_history=False)
                    return
                app.frames[name] = frame
                app.right_pane.addWidget(frame)
            else:
                logger.error(f"Frame {name} not found in frame_classes")
                QMessageBox.critical(None, "Error", f"Frame {name} not found")
                app.show_frame("home", add_to_history=False)
                return

        app.right_pane.setCurrentWidget(app.frames[name])
        app.current_frame_name = name
        app.setWindowTitle(f"TRITIQ - {name.replace('_', ' ').title()}")
        if add_to_history and (not app.frame_history or app.frame_history[-1] != name):
            app.frame_history.append(name)
            logger.debug(f"Frame history updated: {app.frame_history}")
        app.update()
        logger.info(f"Successfully displayed frame: {name}")

    except Exception as e:
        logger.error(f"Unexpected error displaying frame {name}: {e}", exc_info=True)
        QMessageBox.critical(None, "Error", f"Failed to display {name.replace('_', ' ').title()}: {e}")
        app.show_frame("home", add_to_history=False)

def go_back(app):
    """Navigate back to the previous frame or quit the application."""
    logger.debug(f"Attempting to go back, frame_history: {app.frame_history}")
    if not app.current_user:
        logger.warning("No user logged in, cannot go back")
        return
    if app.current_user['username'] == "admins":
        logger.debug("go_back disabled for admins")
        return
    if not app.company_details_exist and app.current_frame_name != "company":
        logger.warning("Company details not set, redirecting to company setup")
        QMessageBox.warning(None, "Setup Required", "Please complete company setup before proceeding")
        app.show_frame("company", add_to_history=False)
        return
    if len(app.frame_history) > 1:
        app.frame_history.pop()
        previous_frame = app.frame_history[-1]
        try:
            app.show_frame(previous_frame, add_to_history=False)
            logger.debug(f"Navigated back to {previous_frame}")
        except Exception as e:
            logger.error(f"Failed to navigate back to {previous_frame}: {e}")
            QMessageBox.critical(None, "Navigation Error", f"Failed to navigate back: {e}")
            app.show_frame("home", add_to_history=False)
    else:
        if QMessageBox.question(None, "Quit", "Do you want to quit TRITIQ?") == QMessageBox.Yes:
            logger.info("Application quit via go_back")
            app.close()
        else:
            logger.debug("Quit cancelled by user")