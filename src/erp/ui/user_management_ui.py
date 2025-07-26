# src/erp/ui/user_management_ui.py
# Converted to use SQLAlchemy in load_users.

import logging
import os
from PySide6.QtWidgets import QDialog, QVBoxLayout, QHBoxLayout, QLabel, QLineEdit, QCheckBox, QPushButton, QTableWidget, QTableWidgetItem, QWidget, QMessageBox, QApplication
from PySide6.QtCore import Qt
from PySide6.QtGui import QPixmap
from sqlalchemy import text
from src.erp.logic.database.session import engine, Session
from src.core.config import get_static_path, get_database_url

logging.basicConfig(
    filename=os.path.join(os.path.dirname(__file__), '..', '..', 'logs', 'app.log'),
    level=logging.ERROR,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

class UserManagementWidget(QWidget):
    def __init__(self, parent, app):
        super().__init__(parent)
        self.main_window = parent
        self.app = app
        self.setup_ui()

    def setup_ui(self):
        layout = QVBoxLayout(self)
        layout.setContentsMargins(10, 10, 10, 10)
        layout.setSpacing(10)

        self.table = QTableWidget()
        self.table.setColumnCount(2)
        self.table.setHorizontalHeaderLabels(["Username", "Actions"])
        layout.addWidget(self.table)

        self.add_user_button = QPushButton("Add User")
        self.add_user_button.clicked.connect(self.show_add_user_dialog)
        layout.addWidget(self.add_user_button)

        self.load_users()

    def load_users(self):
        session = Session()
        try:
            from src.erp.logic.user_management_logic import get_all_users
            users = get_all_users()
            self.table.setRowCount(len(users))
            for row, (user_id, username, role, active) in enumerate(users):
                if active:  # Only show active users
                    self.table.setItem(row, 0, QTableWidgetItem(username))
                    edit_button = QPushButton("Edit")
                    edit_button.clicked.connect(lambda _, uid=user_id, uname=username: self.show_edit_user_dialog(uid, uname))
                    delete_button = QPushButton("Delete")
                    delete_button.clicked.connect(lambda _, uid=user_id, uname=username: self.delete_user(uid, uname))
                    actions_widget = QWidget()
                    actions_layout = QHBoxLayout(actions_widget)
                    actions_layout.addWidget(edit_button)
                    actions_layout.addWidget(delete_button)
                    actions_layout.setContentsMargins(0, 0, 0, 0)
                    self.table.setCellWidget(row, 1, actions_widget)
        except Exception as e:
            logger.error(f"Failed to load users: {e}")
            QMessageBox.critical(self, "Error", f"Failed to load users: {str(e)}")
        finally:
            session.close()

    def show_add_user_dialog(self):
        dialog = AddUserDialog(self.main_window)
        if dialog.exec() == QDialog.Accepted:
            self.load_users()

    def show_edit_user_dialog(self, user_id, username):
        dialog = EditUserDialog(self.main_window, user_id, username)
        if dialog.exec() == QDialog.Accepted:
            self.load_users()

    def delete_user(self, user_id, username):
        reply = QMessageBox.question(self, "Confirm Delete", f"Are you sure you want to delete user '{username}'?",
                                     QMessageBox.Yes | QMessageBox.No, QMessageBox.No)
        if reply == QMessageBox.Yes:
            try:
                from src.erp.logic.user_management_logic import delete_user
                if delete_user(user_id):
                    self.load_users()
                else:
                    QMessageBox.critical(self, "Error", f"Failed to delete user: {username}")
            except Exception as e:
                logger.error(f"Failed to delete user {username}: {e}")
                QMessageBox.critical(self, "Error", f"Failed to delete user: {str(e)}")

class AuthDialogBase(QDialog):
    def __init__(self, parent, title, size=(400, 309)):
        super().__init__(parent)
        self.setWindowTitle(title)
        self.setFixedSize(*size)
        self.load_stylesheet()
        self.center_on_screen()

    def load_stylesheet(self):
        try:
            with open(get_static_path("qss/login.qss"), "r") as f:
                self.setStyleSheet(f.read())
        except Exception as e:
            logger.error(f"Failed to load login.qss: {e}")

    def center_on_screen(self):
        screen = QApplication.primaryScreen().availableGeometry()
        size = self.size()
        x = (screen.width() - size.width()) // 2
        y = (screen.height() - size.height()) // 2
        self.move(x, y)

    def add_logo(self, layout):
        logo_label = QLabel(self)
        logo_pixmap = QPixmap(get_static_path("tritiq.png")).scaled(100, 100, Qt.KeepAspectRatio, Qt.SmoothTransformation)
        logo_label.setPixmap(logo_pixmap)
        logo_label.setAlignment(Qt.AlignCenter)
        logo_label.setObjectName("logoLabel")
        layout.addWidget(logo_label)

    def add_show_password_checkbox(self, layout, inputs):
        self.show_password = QCheckBox("Show Password")
        self.show_password.setObjectName("moduleCheckbox")
        self.show_password.toggled.connect(lambda checked: self.toggle_password_visibility(checked, inputs))
        layout.addWidget(self.show_password, alignment=Qt.AlignRight)

    def toggle_password_visibility(self, checked, inputs):
        mode = QLineEdit.Normal if checked else QLineEdit.Password
        for input_field in inputs:
            input_field.setEchoMode(mode)

class LoginDialog(AuthDialogBase):
    def __init__(self, parent, on_success):
        super().__init__(parent, "TRITIQ ERP - Login")
        self.on_success = on_success
        self.setup_ui()

    def setup_ui(self):
        layout = QVBoxLayout(self)
        layout.setContentsMargins(20, 20, 20, 20)
        layout.setSpacing(15)

        self.add_logo(layout)

        username_layout = QHBoxLayout()
        username_label = QLabel("Username:")
        username_label.setObjectName("fieldLabel")
        username_label.setFixedWidth(100)
        self.username_input = QLineEdit()
        self.username_input.setPlaceholderText("Enter username")
        self.username_input.setObjectName("textEntry")
        username_layout.addWidget(username_label)
        username_layout.addWidget(self.username_input)
        layout.addLayout(username_layout)

        password_layout = QHBoxLayout()
        password_label = QLabel("Password:")
        password_label.setObjectName("fieldLabel")
        password_label.setFixedWidth(100)
        self.password_input = QLineEdit()
        self.password_input.setPlaceholderText("Enter password")
        self.password_input.setEchoMode(QLineEdit.Password)
        self.password_input.setObjectName("textEntry")
        password_layout.addWidget(password_label)
        password_layout.addWidget(self.password_input)
        layout.addLayout(password_layout)

        self.add_show_password_checkbox(layout, [self.password_input])

        button_layout = QHBoxLayout()
        button_layout.setSpacing(10)
        login_button = QPushButton("Login")
        login_button.setObjectName("confirmButton")
        login_button.clicked.connect(self.handle_login)
        cancel_button = QPushButton("Cancel")
        cancel_button.setObjectName("cancelButton")
        cancel_button.clicked.connect(self.reject)
        button_layout.addWidget(login_button)
        button_layout.addWidget(cancel_button)
        layout.addLayout(button_layout)

    def closeEvent(self, event):
        super().closeEvent(event)
        self.parent().exit_app()

    def handle_login(self):
        from src.erp.logic.user_management_logic import handle_login
        try:
            handle_login(self.parent(), self, self.on_success)
        except Exception as e:
            logger.error(f"Login failed: {e}")
            QMessageBox.critical(self, "Error", f"Login failed: {str(e)}")

class FirstRunDialog(AuthDialogBase):
    def __init__(self, parent, on_success):
        super().__init__(parent, "TRITIQ ERP - First Run Setup", (400, 350))
        self.on_success = on_success
        self.setup_ui()

    def setup_ui(self):
        layout = QVBoxLayout(self)
        layout.setContentsMargins(20, 20, 20, 20)
        layout.setSpacing(15)

        self.add_logo(layout)

        username_layout = QHBoxLayout()
        username_label = QLabel("Username:")
        username_label.setObjectName("fieldLabel")
        username_label.setFixedWidth(100)
        self.username_input = QLineEdit()
        self.username_input.setPlaceholderText("Enter username")
        self.username_input.setObjectName("textEntry")
        username_layout.addWidget(username_label)
        username_layout.addWidget(self.username_input)
        layout.addLayout(username_layout)

        password_layout = QHBoxLayout()
        password_label = QLabel("Password:")
        password_label.setObjectName("fieldLabel")
        password_label.setFixedWidth(100)
        self.password_input = QLineEdit()
        self.password_input.setPlaceholderText("Enter password")
        self.password_input.setEchoMode(QLineEdit.Password)
        self.password_input.setObjectName("textEntry")
        password_layout.addWidget(password_label)
        password_layout.addWidget(self.password_input)
        layout.addLayout(password_layout)

        confirm_password_layout = QHBoxLayout()
        confirm_password_label = QLabel("Confirm Password:")
        confirm_password_label.setObjectName("fieldLabel")
        confirm_password_label.setFixedWidth(100)
        self.confirm_password_input = QLineEdit()
        self.confirm_password_input.setPlaceholderText("Confirm password")
        self.confirm_password_input.setEchoMode(QLineEdit.Password)
        self.confirm_password_input.setObjectName("textEntry")
        confirm_password_layout.addWidget(confirm_password_label)
        confirm_password_layout.addWidget(self.confirm_password_input)
        layout.addLayout(confirm_password_layout)

        self.add_show_password_checkbox(layout, [self.password_input, self.confirm_password_input])

        button_layout = QHBoxLayout()
        button_layout.setSpacing(10)
        save_button = QPushButton("Save")
        save_button.setObjectName("confirmButton")
        save_button.clicked.connect(self.handle_save)
        cancel_button = QPushButton("Cancel")
        cancel_button.setObjectName("cancelButton")
        cancel_button.clicked.connect(self.reject)
        button_layout.addWidget(save_button)
        button_layout.addWidget(cancel_button)
        layout.addLayout(button_layout)

    def handle_save(self):
        from src.erp.logic.user_management_logic import create_initial_user, validate_user
        username = self.username_input.text().strip()
        password = self.password_input.text()
        confirm_password = self.confirm_password_input.text()
        if not username or not password:
            QMessageBox.warning(self, "Error", "Username and password are required.")
            return
        if password != confirm_password:
            QMessageBox.warning(self, "Error", "Passwords do not match.")
            return
        try:
            user_id = create_initial_user(username, password, "super_admin")
            if user_id:
                # Automatically log in the new user
                user = validate_user(username, password)
                if user:
                    self.parent().current_user = user
                    self.on_success()
                    self.accept()
                else:
                    QMessageBox.warning(self, "Error", "Failed to log in after user creation.")
            else:
                QMessageBox.warning(self, "Error", "Failed to create initial user.")
        except Exception as e:
            logger.error(f"Failed to create initial user: {e}")
            QMessageBox.critical(self, "Error", f"Failed to create user: {str(e)}")

class PasswordChangeDialog(AuthDialogBase):
    def __init__(self, parent, username, on_success):
        super().__init__(parent, "TRITIQ ERP - Change Password", (400, 350))
        self.username = username
        self.on_success = on_success
        self.setup_ui()

    def setup_ui(self):
        layout = QVBoxLayout(self)
        layout.setContentsMargins(20, 20, 20, 20)
        layout.setSpacing(15)

        self.add_logo(layout)

        username_layout = QHBoxLayout()
        username_label = QLabel("Username:")
        username_label.setObjectName("fieldLabel")
        username_label.setFixedWidth(100)
        self.username_input = QLineEdit(self.username)
        self.username_input.setReadOnly(True)
        self.username_input.setObjectName("textEntry")
        username_layout.addWidget(username_label)
        username_layout.addWidget(self.username_input)
        layout.addLayout(username_layout)

        current_password_layout = QHBoxLayout()
        current_password_label = QLabel("Current Password:")
        current_password_label.setObjectName("fieldLabel")
        current_password_label.setFixedWidth(100)
        self.current_password_input = QLineEdit()
        self.current_password_input.setPlaceholderText("Enter current password")
        self.current_password_input.setEchoMode(QLineEdit.Password)
        self.current_password_input.setObjectName("textEntry")
        current_password_layout.addWidget(current_password_label)
        current_password_layout.addWidget(self.current_password_input)
        layout.addLayout(current_password_layout)

        new_password_layout = QHBoxLayout()
        new_password_label = QLabel("New Password:")
        new_password_label.setObjectName("fieldLabel")
        new_password_label.setFixedWidth(100)
        self.new_password_input = QLineEdit()
        self.new_password_input.setPlaceholderText("Enter new password")
        self.new_password_input.setEchoMode(QLineEdit.Password)
        self.new_password_input.setObjectName("textEntry")
        new_password_layout.addWidget(new_password_label)
        new_password_layout.addWidget(self.new_password_input)
        layout.addLayout(new_password_layout)

        confirm_password_layout = QHBoxLayout()
        confirm_password_label = QLabel("Confirm New Password:")
        confirm_password_label.setObjectName("fieldLabel")
        confirm_password_label.setFixedWidth(100)
        self.confirm_password_input = QLineEdit()
        self.confirm_password_input.setPlaceholderText("Confirm new password")
        self.confirm_password_input.setEchoMode(QLineEdit.Password)
        self.confirm_password_input.setObjectName("textEntry")
        confirm_password_layout.addWidget(confirm_password_label)
        confirm_password_layout.addWidget(self.confirm_password_input)
        layout.addLayout(confirm_password_layout)

        self.add_show_password_checkbox(layout, [self.current_password_input, self.new_password_input, self.confirm_password_input])

        button_layout = QHBoxLayout()
        button_layout.setSpacing(10)
        save_button = QPushButton("Save")
        save_button.setObjectName("confirmButton")
        save_button.clicked.connect(self.handle_save)
        cancel_button = QPushButton("Cancel")
        cancel_button.setObjectName("cancelButton")
        cancel_button.clicked.connect(self.reject)
        button_layout.addWidget(save_button)
        button_layout.addWidget(cancel_button)
        layout.addLayout(button_layout)

    def handle_save(self):
        from src.erp.logic.user_management_logic import handle_password_change
        current_password = self.current_password_input.text()
        new_password = self.new_password_input.text()
        confirm_password = self.confirm_password_input.text()
        if not current_password or not new_password:
            QMessageBox.warning(self, "Error", "All password fields are required.")
            return
        if new_password != confirm_password:
            QMessageBox.warning(self, "Error", "New passwords do not match.")
            return
        try:
            if handle_password_change(self.parent(), self):
                self.on_success()
                self.accept()
            else:
                QMessageBox.warning(self, "Error", "Failed to change password.")
        except Exception as e:
            logger.error(f"Failed to change password: {e}")
            QMessageBox.critical(self, "Error", f"Failed to change password: {str(e)}")

class AddUserDialog(AuthDialogBase):
    def __init__(self, parent):
        super().__init__(parent, "TRITIQ ERP - Add User", (400, 400))
        self.setup_ui()

    def setup_ui(self):
        layout = QVBoxLayout(self)
        layout.setContentsMargins(20, 20, 20, 20)
        layout.setSpacing(15)

        self.add_logo(layout)

        username_layout = QHBoxLayout()
        username_label = QLabel("Username:")
        username_label.setObjectName("fieldLabel")
        username_label.setFixedWidth(100)
        self.username_input = QLineEdit()
        self.username_input.setPlaceholderText("Enter username")
        self.username_input.setObjectName("textEntry")
        username_layout.addWidget(username_label)
        username_layout.addWidget(self.username_input)
        layout.addLayout(username_layout)

        password_layout = QHBoxLayout()
        password_label = QLabel("Password:")
        password_label.setObjectName("fieldLabel")
        password_label.setFixedWidth(100)
        self.password_input = QLineEdit()
        self.password_input.setPlaceholderText("Enter password")
        self.password_input.setEchoMode(QLineEdit.Password)
        self.password_input.setObjectName("textEntry")
        password_layout.addWidget(password_label)
        password_layout.addWidget(self.password_input)
        layout.addLayout(password_layout)

        confirm_password_layout = QHBoxLayout()
        confirm_password_label = QLabel("Confirm Password:")
        confirm_password_label.setObjectName("fieldLabel")
        confirm_password_label.setFixedWidth(100)
        self.confirm_password_input = QLineEdit()
        self.confirm_password_input.setPlaceholderText("Confirm password")
        self.confirm_password_input.setEchoMode(QLineEdit.Password)
        self.confirm_password_input.setObjectName("textEntry")
        confirm_password_layout.addWidget(confirm_password_label)
        confirm_password_layout.addWidget(self.confirm_password_input)
        layout.addLayout(confirm_password_layout)

        permissions_label = QLabel("Permissions:")
        permissions_label.setObjectName("fieldLabel")
        layout.addWidget(permissions_label)
        self.permissions = {}
        for perm in ["vendors", "products", "customers", "stock", "manufacturing"]:
            checkbox = QCheckBox(perm.capitalize())
            checkbox.setObjectName("moduleCheckbox")
            self.permissions[perm] = checkbox
            layout.addWidget(checkbox)

        self.add_show_password_checkbox(layout, [self.password_input, self.confirm_password_input])

        button_layout = QHBoxLayout()
        button_layout.setSpacing(10)
        save_button = QPushButton("Save")
        save_button.setObjectName("confirmButton")
        save_button.clicked.connect(self.handle_save)
        cancel_button = QPushButton("Cancel")
        cancel_button.setObjectName("cancelButton")
        cancel_button.clicked.connect(self.reject)
        button_layout.addWidget(save_button)
        button_layout.addWidget(cancel_button)
        layout.addLayout(button_layout)

    def handle_save(self):
        from src.erp.logic.user_management_logic import create_user
        username = self.username_input.text().strip()
        password = self.password_input.text()
        confirm_password = self.confirm_password_input.text()
        if not username or not password:
            QMessageBox.warning(self, "Error", "Username and password are required.")
            return
        if password != confirm_password:
            QMessageBox.warning(self, "Error", "Passwords do not match.")
            return
        permissions = [perm for perm, checkbox in self.permissions.items() if checkbox.isChecked()]
        try:
            user_id = create_user(username, password, "standard_user", permissions)
            if user_id:
                self.parent().load_users()
                self.accept()
            else:
                QMessageBox.warning(self, "Error", "Failed to create user.")
        except Exception as e:
            logger.error(f"Failed to create user: {e}")
            QMessageBox.critical(self, "Error", f"Failed to create user: {str(e)}")

class EditUserDialog(AuthDialogBase):
    def __init__(self, parent, user_id, username):
        super().__init__(parent, f"TRITIQ ERP - Edit User: {username}", (400, 400))
        self.user_id = user_id
        self.username = username
        self.setup_ui()

    def setup_ui(self):
        layout = QVBoxLayout(self)
        layout.setContentsMargins(20, 20, 20, 20)
        layout.setSpacing(15)

        self.add_logo(layout)

        username_layout = QHBoxLayout()
        username_label = QLabel(f"Username: {self.username}")
        username_label.setObjectName("fieldLabel")
        username_layout.addWidget(username_label)
        layout.addLayout(username_layout)

        new_password_layout = QHBoxLayout()
        new_password_label = QLabel("New Password (leave blank to keep unchanged):")
        new_password_label.setObjectName("fieldLabel")
        new_password_label.setFixedWidth(100)
        self.new_password_input = QLineEdit()
        self.new_password_input.setPlaceholderText("Enter new password")
        self.new_password_input.setEchoMode(QLineEdit.Password)
        self.new_password_input.setObjectName("textEntry")
        new_password_layout.addWidget(new_password_label)
        new_password_layout.addWidget(self.new_password_input)
        layout.addLayout(new_password_layout)

        confirm_password_layout = QHBoxLayout()
        confirm_password_label = QLabel("Confirm New Password:")
        confirm_password_label.setObjectName("fieldLabel")
        confirm_password_label.setFixedWidth(100)
        self.confirm_password_input = QLineEdit()
        self.confirm_password_input.setPlaceholderText("Confirm new password")
        self.confirm_password_input.setEchoMode(QLineEdit.Password)
        self.confirm_password_input.setObjectName("textEntry")
        confirm_password_layout.addWidget(confirm_password_label)
        confirm_password_layout.addWidget(self.confirm_password_input)
        layout.addLayout(confirm_password_layout)

        permissions_label = QLabel("Permissions:")
        permissions_label.setObjectName("fieldLabel")
        layout.addWidget(permissions_label)
        self.permissions = {}
        for perm in ["vendors", "products", "customers", "stock", "manufacturing"]:
            checkbox = QCheckBox(perm.capitalize())
            checkbox.setObjectName("moduleCheckbox")
            self.permissions[perm] = checkbox
            layout.addWidget(checkbox)

        try:
            from src.erp.logic.user_management_logic import get_user_permissions
            current_permissions = get_user_permissions(self.user_id)
            for perm, checkbox in self.permissions.items():
                checkbox.setChecked(perm in current_permissions)
        except Exception as e:
            logger.error(f"Failed to load permissions for user {self.username}: {e}")
            QMessageBox.critical(self, "Error", f"Failed to load permissions: {str(e)}")

        self.add_show_password_checkbox(layout, [self.new_password_input, self.confirm_password_input])

        button_layout = QHBoxLayout()
        button_layout.setSpacing(10)
        save_button = QPushButton("Save")
        save_button.setObjectName("confirmButton")
        save_button.clicked.connect(self.handle_save)
        cancel_button = QPushButton("Cancel")
        cancel_button.setObjectName("cancelButton")
        cancel_button.clicked.connect(self.reject)
        button_layout.addWidget(save_button)
        button_layout.addWidget(cancel_button)
        layout.addLayout(button_layout)

    def handle_save(self):
        from src.erp.logic.user_management_logic import update_user
        new_password = self.new_password_input.text()
        confirm_password = self.confirm_password_input.text()
        if new_password and new_password != confirm_password:
            QMessageBox.warning(self, "Error", "New passwords do not match.")
            return
        permissions = [perm for perm, checkbox in self.permissions.items() if checkbox.isChecked()]
        try:
            if update_user(self.user_id, password=new_password or None, modules=permissions):
                self.parent().load_users()
                self.accept()
            else:
                QMessageBox.warning(self, "Error", "Failed to update user.")
        except Exception as e:
            logger.error(f"Failed to update user {self.username}: {e}")
            QMessageBox.critical(self, "Error", f"Failed to update user: {str(e)}")