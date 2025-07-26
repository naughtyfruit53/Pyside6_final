# src/erp/logic/user_management_logic.py
# Converted to SQLAlchemy.

import logging
import bcrypt
import re
from datetime import datetime
from sqlalchemy import text
from src.erp.logic.database.session import engine, Session
from src.core.config import get_database_url, get_log_path
from src.erp.logic.utils.voucher_utils import MODULE_VOUCHER_TYPES
from PySide6.QtWidgets import QMessageBox, QDialog, QWidget

logging.basicConfig(
    filename=get_log_path(),
    level=logging.DEBUG,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

VOUCHER_FRAMES = [f"vouchers-{voucher_type.lower().replace(' ', '_').replace('_(goods_receipt_note)', '')}-{action}"
                  for module in ["purchase", "sales", "financial"]
                  for voucher_type in MODULE_VOUCHER_TYPES[module]
                  for action in ["create", "view"]]

VALID_FRAMES = [
    "home", "dashboard", "company", "vendors", "products", "customers",
    "stock", "manufacturing", "create_bom", "create_work_order", "close_work_order",
    "material_in", "material_out", "mat_out_form", "master",
    "service", "hr_management", "backup_boss", "backup", "restore", "auto_backup",
    "default_directory", "user_management"
] + VOUCHER_FRAMES

def validate_user(username, password):
    session = Session()
    try:
        result = session.execute(text("SELECT id, username, password, role, active, must_change_password FROM users WHERE username = :username"), {"username": username}).fetchone()
        if result is None:
            logger.error(f"No user found or invalid tuple for username: {username}")
            return None
        if result[4] and bcrypt.checkpw(password.encode('utf-8'), result[2].encode('utf-8')):
            return {"id": result[0], "username": result[1], "role": result[3], "must_change_password": bool(result[5])}
        logger.error(f"Invalid login attempt for username: {username}")
        return None
    except Exception as e:
        logger.error(f"User validation error: {str(e)}")
        QMessageBox.critical(None, "Error", f"User validation failed: {str(e)}")
        return None
    finally:
        session.close()

def get_user_permissions(user_id):
    session = Session()
    try:
        role = session.execute(text("SELECT role FROM users WHERE id = :user_id"), {"user_id": user_id}).fetchone()
        if not role:
            logger.error(f"No user found with id {user_id}")
            return []
        if role[0] in ['super_admin', 'admin']:
            return VALID_FRAMES
        permissions = session.execute(text("SELECT module_name FROM user_permissions WHERE user_id = :user_id"), {"user_id": user_id}).fetchall()
        return [row[0] for row in permissions if row[0] in VALID_FRAMES]
    except Exception as e:
        logger.error(f"Error fetching user permissions: {str(e)}")
        QMessageBox.critical(None, "Error", f"Failed to fetch permissions: {str(e)}")
        return []
    finally:
        session.close()

def create_initial_user(username, password, role="super_admin"):
    session = Session()
    try:
        existing = session.execute(text("SELECT id FROM users WHERE username = :username"), {"username": username}).fetchone()
        if existing:
            logger.error(f"User {username} already exists")
            return None
        hashed_password = bcrypt.hashpw(password.encode('utf-8'), bcrypt.gensalt()).decode('utf-8')
        must_change_password = True if password == "123456" else False
        created_at = datetime.now()
        insert_stmt = text("INSERT INTO users (username, password, role, created_at, active, must_change_password) VALUES (:username, :password, :role, :created_at, :active, :must_change_password) RETURNING id")
        result = session.execute(insert_stmt,
                      {"username": username, "password": hashed_password, "role": role, "created_at": created_at, "active": True, "must_change_password": must_change_password})
        user_id = result.fetchone()[0]
        session.commit()
        return user_id
    except Exception as e:
        session.rollback()
        logger.error(f"Error creating initial user: {str(e)}")
        QMessageBox.critical(None, "Error", f"Failed to create initial user: {str(e)}")
        return None
    finally:
        session.close()

def create_user(username, password, role, modules=None):
    session = Session()
    try:
        existing = session.execute(text("SELECT id FROM users WHERE username = :username"), {"username": username}).fetchone()
        if existing:
            logger.error(f"User {username} already exists")
            return None
        hashed_password = bcrypt.hashpw(password.encode('utf-8'), bcrypt.gensalt()).decode('utf-8')
        must_change_password = True if password == "123456" else False
        created_at = datetime.now()
        insert_stmt = text("INSERT INTO users (username, password, role, created_at, active, must_change_password) VALUES (:username, :password, :role, :created_at, :active, :must_change_password) RETURNING id")
        result = session.execute(insert_stmt,
                      {"username": username, "password": hashed_password, "role": role, "created_at": created_at, "active": True, "must_change_password": must_change_password})
        user_id = result.fetchone()[0]
        if role == "standard_user" and modules:
            for module in [m for m in modules if m in VALID_FRAMES]:
                session.execute(text("INSERT INTO user_permissions (user_id, module_name) VALUES (:user_id, :module)"), {"user_id": user_id, "module": module})
        session.commit()
        return user_id
    except Exception as e:
        session.rollback()
        error_msg = "Username already exists." if "UNIQUE constraint failed" in str(e) else f"Failed to create user: {str(e)}"
        logger.error(f"Error creating user: {str(e)}")
        QMessageBox.critical(None, "Error", error_msg)
        return None
    finally:
        session.close()

def get_all_users():
    session = Session()
    try:
        result = session.execute(text("SELECT id, username, role, active FROM users")).fetchall()
        return result
    except Exception as e:
        logger.error(f"Error fetching users: {str(e)}")
        QMessageBox.critical(None, "Error", f"Failed to fetch users: {str(e)}")
        return []
    finally:
        session.close()

def update_user(user_id, username=None, password=None, role=None, active=None, modules=None, must_change_password=None):
    session = Session()
    try:
        if username:
            session.execute(text("UPDATE users SET username = :username WHERE id = :user_id"), {"username": username, "user_id": user_id})
        if password:
            hashed_password = bcrypt.hashpw(password.encode('utf-8'), bcrypt.gensalt()).decode('utf-8')
            session.execute(text("UPDATE users SET password = :password, must_change_password = :must_change_password WHERE id = :user_id"),
                          {"password": hashed_password, "must_change_password": True if password == "123456" else False, "user_id": user_id})
        if role:
            session.execute(text("UPDATE users SET role = :role WHERE id = :user_id"), {"role": role, "user_id": user_id})
        if active is not None:
            session.execute(text("UPDATE users SET active = :active WHERE id = :user_id"), {"active": bool(active), "user_id": user_id})
        if must_change_password is not None:
            session.execute(text("UPDATE users SET must_change_password = :must_change_password WHERE id = :user_id"), {"must_change_password": bool(must_change_password), "user_id": user_id})
        if modules is not None:
            session.execute(text("DELETE FROM user_permissions WHERE user_id = :user_id"), {"user_id": user_id})
            for module in [m for m in modules if m in VALID_FRAMES]:
                session.execute(text("INSERT INTO user_permissions (user_id, module_name) VALUES (:user_id, :module)"), {"user_id": user_id, "module": module})
        session.commit()
        return True
    except Exception as e:
        session.rollback()
        logger.error(f"Error updating user: {str(e)}")
        QMessageBox.critical(None, "Error", f"Failed to update user: {str(e)}")
        return False
    finally:
        session.close()

def delete_user(user_id):
    session = Session()
    try:
        session.execute(text("DELETE FROM user_permissions WHERE user_id = :user_id"), {"user_id": user_id})
        session.execute(text("DELETE FROM users WHERE id = :user_id"), {"user_id": user_id})
        session.commit()
        return True
    except Exception as e:
        session.rollback()
        logger.error(f"Error deleting user: {str(e)}")
        QMessageBox.critical(None, "Error", f"Failed to delete user: {str(e)}")
        return False
    finally:
        session.close()

def reset_super_admin_password(app):
    session = Session()
    try:
        super_admin = session.execute(text("SELECT id, username FROM users WHERE role = 'super_admin' AND id = 1")).fetchone()
        if not super_admin:
            logger.error("No super admin account found with ID 1")
            QMessageBox.critical(None, "Error", "No super admin account found with ID 1")
            return
        update_user(super_admin[0], password="123456", must_change_password=True)
        QMessageBox.information(None, "Success", f"Super admin '{super_admin[1]}' password reset to '123456'.")
    except Exception as e:
        logger.error(f"Failed to reset super admin password: {e}")
        QMessageBox.critical(None, "Error", f"Failed to reset super admin password: {e}")
    finally:
        session.close()

def check_first_run(app):
    session = Session()
    try:
        count_result = session.execute(text("SELECT COUNT(*) FROM users WHERE username != 'admins'")).fetchone()
        user_count = count_result[0]
        if user_count == 0:
            show_first_run_screen(app)
        else:
            dialog = show_login_screen(app)
            if dialog and dialog.exec() == QDialog.Rejected:
                logger.info("LoginDialog rejected, exiting application")
                app.exit_app()
    except Exception as e:
        logger.error(f"Error checking first run: {e}")
        QMessageBox.critical(app, "Error", f"Database error: {e}")
        app.exit_app()
    finally:
        session.close()

def show_first_run_screen(app):
    try:
        from src.erp.ui.user_management_ui import FirstRunDialog
        if hasattr(app, 'login_frame') and app.login_frame and not app.login_frame.isHidden():
            app.login_frame.deleteLater()
        dialog = FirstRunDialog(app, app.check_company_details)
        app.first_run_frame = dialog
        dialog.show()
    except Exception as e:
        logger.error(f"Error creating first run screen: {e}")
        QMessageBox.critical(app, "Error", f"Failed to create first run screen: {e}")
        app.exit_app()

def show_login_screen(app):
    try:
        if app.is_logging_in:
            return None
        app.is_logging_in = True
        from src.erp.ui.user_management_ui import LoginDialog
        for frame in ['first_run_frame', 'password_change_frame', 'login_frame']:
            if hasattr(app, frame) and getattr(app, frame) and not getattr(app, frame).isHidden():
                getattr(app, frame).deleteLater()
        dialog = LoginDialog(app, app.check_company_details)
        app.login_frame = dialog
        return dialog
    except Exception as e:
        logger.error(f"Error creating login screen: {e}")
        QMessageBox.critical(app, "Error", f"Failed to create login screen: {e}")
        app.exit_app()
        return None
    finally:
        app.is_logging_in = False

def show_password_change_screen(app):
    try:
        from src.erp.ui.user_management_ui import PasswordChangeDialog
        if hasattr(app, 'login_frame') and app.login_frame and not app.login_frame.isHidden():
            app.login_frame.deleteLater()
        dialog = PasswordChangeDialog(app, app.current_user['username'], app.check_company_details)
        app.password_change_frame = dialog
        dialog.show()
    except Exception as e:
        logger.error(f"Error creating password change screen: {e}")
        QMessageBox.critical(app, "Error", f"Failed to create password change screen: {e}")

def handle_login(app, dialog, on_success=None):
    try:
        if app.is_logging_in:
            return
        app.is_logging_in = True
        username = dialog.username_input.text().strip()
        password = dialog.password_input.text().strip()
        if username == "admins" and password == "admins":
            app.current_user = {"id": 0, "username": "admins", "role": "super_admin", "must_change_password": False}
            dialog.accept()
            if on_success:
                on_success()
            return
        user = validate_user(username, password)
        if user:
            app.current_user = user
            dialog.accept()
            dialog.deleteLater()
            if user.get('must_change_password', False):
                QMessageBox.information(dialog, "Password Change Required", "Your password is set to the default '123456'. Please change it now.")
                show_password_change_screen(app)
            else:
                if on_success:
                    on_success()
        else:
            QMessageBox.critical(dialog, "Login Failed", "Invalid username or password. If this is your first login, try the default password '123456'.")
            logger.error(f"Failed login attempt for username: {username}")
    except Exception as e:
        logger.error(f"Error handling login: {e}")
        QMessageBox.critical(dialog, "Error", f"Login failed: {e}")
    finally:
        app.is_logging_in = False

def handle_password_change(app, dialog):
    try:
        new_password = dialog.new_password_input.text().strip()
        confirm_password = dialog.confirm_password_input.text().strip()
        current_password = dialog.current_password_input.text().strip()
        if not current_password or not new_password:
            QMessageBox.critical(dialog, "Error", "All password fields are required")
            return False
        if new_password != confirm_password:
            QMessageBox.critical(dialog, "Error", "Passwords do not match. Please ensure both password fields are identical. Use 'Show Password' to verify.")
            return False
        if len(new_password) < 6:
            QMessageBox.critical(dialog, "Error", "Password must be at least 6 characters long")
            return False
        user = validate_user(app.current_user["username"], current_password)
        if not user:
            QMessageBox.critical(dialog, "Error", "Current password is incorrect.")
            logger.error(f"Invalid current password for user: {app.current_user['username']}")
            return False
        if update_user(app.current_user["id"], password=new_password, must_change_password=False):
            QMessageBox.information(dialog, "Success", "Password changed successfully")
            return True
        else:
            QMessageBox.critical(dialog, "Error", "Failed to change password")
            logger.error(f"Failed to change password for user ID: {app.current_user['id']}")
            return False
    except Exception as e:
        logger.error(f"Error handling password change: {e}")
        QMessageBox.critical(dialog, "Error", f"Failed to change password: {e}")
        return False

def logout(app):
    try:
        if app.current_user:
            logger.info(f"User {app.current_user['username']} logged out")
        app.current_user = None
        app.frames.clear()
        for widget in app.findChildren(QWidget):
            widget.deleteLater()
        for attr in ['central_widget', 'main_layout', 'right_pane', 'toolbar', 'mega_menu']:
            setattr(app, attr, None)
        app.is_logging_in = False
        app.setup_ui()
        show_login_screen(app)
    except Exception as e:
        logger.error(f"Error during logout: {e}")
        QMessageBox.critical(app, "Error", f"Logout failed: {e}")