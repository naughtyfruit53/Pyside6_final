# app.py
from PySide6.QtWidgets import QMainWindow, QVBoxLayout, QHBoxLayout, QFrame, QLabel, QWidget, QStackedWidget, QApplication, QMessageBox
from PySide6.QtGui import QPixmap, QImage, QIcon, QCursor
from PySide6.QtCore import Qt
import logging
import os
from PIL import Image
import io
import sys
from src.core.config import get_static_path, get_log_path, get_database_url  # Updated to use get_database_url
from src.erp.ui.user_management_ui import UserManagementWidget
from src.erp.ui.company_details_ui import CompanyDetailsWidget
from src.erp.ui.default_directory_ui import show_default_directory_setup
from src.erp.logic.database.db_utils import initialize_database
from src.erp.logic.user_management_logic import show_first_run_screen, show_login_screen, handle_login, show_password_change_screen, handle_password_change, logout, check_first_run, get_user_permissions
from src.erp.logic.company_details_logic import show_company_setup
from src.core.navigation import populate_mega_menu
from src.erp.logic.utils.voucher_utils import VOUCHER_TYPES
from src.erp.voucher.column_management import ColumnManagement
from src.erp.logic.default_directory import get_default_directory
import src.erp.logic.vendors_logic as vendors_logic
import src.erp.logic.products_logic as products_logic
import src.erp.logic.customers_logic as customers_logic
import src.erp.logic.stock_logic as stock_logic
import src.erp.logic.manufacturing_logic as manufacturing_logic
from src.core.frames import initialize_frames
from src.erp.logic.utils.utils import filter_combobox, update_state_code, STATES  # Import utils here
from sqlalchemy import text
from src.erp.logic.database.session import engine, Session

logging.basicConfig(filename=get_log_path(), level=logging.DEBUG, format='%(asctime)s - %(name)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

class ERPApp(QMainWindow):
    def __init__(self):
        super().__init__()
        self.setWindowTitle("TRITIQ - Login")
        self.company_details_exist = False
        self.default_directory_set = False
        self.add_window = None
        self.add_window_open = False
        self.setup_shown = False
        self.setup_win = None
        self.dir_win = None
        self.frames = {}
        self.current_frame_name = None
        self.frame_history = []
        self.current_user = None
        self.is_logging_in = False
        self.column_management = ColumnManagement(self)
        self.utils = type('Utils', (), {})()  # Create a utils namespace
        self.utils.filter_combobox = filter_combobox
        self.utils.update_state_code = update_state_code
        self.utils.STATES = STATES
        try:
            self.logic = type('Logic', (), {})()
            self.logic.vendors_logic = vendors_logic
            self.logic.products_logic = products_logic
            self.logic.customers_logic = customers_logic
            self.logic.stock_logic = stock_logic
            self.logic.manufacturing_logic = manufacturing_logic
            self.stock_logic = stock_logic.StockLogic(self) if hasattr(stock_logic, 'StockLogic') else None
            self.manufacturing_logic = manufacturing_logic.ManufacturingLogic(self) if hasattr(manufacturing_logic, 'ManufacturingLogic') else None
        except AttributeError as e:
            logger.error(f"Failed to initialize logic modules: {e}")
            QMessageBox.critical(self, "Error", f"Failed to initialize logic modules: {str(e)}")
            self.close()
            return
        try:
            initialize_database()
        except Exception as e:
            logger.error(f"Failed to initialize database: {e}")
            QMessageBox.critical(self, "Error", f"Failed to initialize database: {e}")
            self.close()
            return
        self.setup_ui()
        self.setFocusPolicy(Qt.StrongFocus)
        check_first_run(self)

    def setup_ui(self):
        screen = QApplication.primaryScreen().availableGeometry()
        window_width = screen.width()
        window_height = min(screen.height(), 1000)
        self.setMinimumSize(800, min(800, int(screen.height() * 0.8)))
        self.showMaximized()

        central_widget = QWidget()
        self.setCentralWidget(central_widget)
        main_layout = QVBoxLayout(central_widget)
        main_layout.setContentsMargins(0, 0, 0, 0)

        self.toolbar = QFrame()
        self.toolbar.setObjectName("toolbar")
        toolbar_layout = QHBoxLayout(self.toolbar)
        toolbar_layout.setContentsMargins(15, 8, 15, 8)

        logo_path = get_static_path("tritiq.png")
        if os.path.exists(logo_path):
            try:
                image = Image.open(logo_path)
                image = image.convert("RGBA")
                max_height = int(0.1 * self.screen().size().height())
                image = image.resize((int(max_height * image.width / image.height), max_height), Image.Resampling.LANCZOS)
                buffer = io.BytesIO()
                image.save(buffer, format="PNG")
                qimage = QImage()
                qimage.loadFromData(buffer.getvalue())
                pixmap = QPixmap.fromImage(qimage)
                logo_label = QLabel()
                logo_label.setPixmap(pixmap)
                logo_label.setStyleSheet("background-color: #0D47A1;")
                toolbar_layout.addWidget(logo_label)
            except Exception as e:
                logger.error(f"Failed to load logo: {e}")
                logo_label = QLabel("TRITIQ ERP")
                logo_label.setObjectName("toolbarLogo")
                toolbar_layout.addWidget(logo_label)
        else:
            logger.error(f"Logo file not found at: {logo_path}")
            logo_label = QLabel("TRITIQ ERP")
            logo_label.setObjectName("toolbarLogo")
            toolbar_layout.addWidget(logo_label)

        self.mega_menu = QFrame()
        self.mega_menu.setObjectName("menuFrame")
        self.mega_menu.setLayout(QHBoxLayout())
        toolbar_layout.addWidget(self.mega_menu)
        toolbar_layout.addStretch()

        logout_label = QLabel("Logout")
        logout_label.setObjectName("logoutLabel")
        logout_label.setCursor(Qt.PointingHandCursor)
        logout_label.mousePressEvent = lambda e: logout(self)
        toolbar_layout.addWidget(logout_label)

        main_layout.addWidget(self.toolbar)

        self.right_pane = QStackedWidget()
        self.right_pane.setObjectName("rightPane")
        main_layout.addWidget(self.right_pane)

        self.right_pane.setContentsMargins(15, 10, 15, 10)
        self.frames = initialize_frames(self)
        self.load_stylesheet()

    def load_stylesheet(self):
        try:
            self.setStyleSheet("")
            style_dir = os.path.join(get_static_path(""), "qss")
            qss_files = [
                'utils.qss', 'customers.qss', 'database.qss', 'manufacturing.qss',
                'pending.qss', 'products.qss', 'stock.qss', 'templates.qss',
                'users.qss', 'vendors.qss', 'style.qss', 'company.qss', 'default_directory.qss', 'mega_menu.qss',
                'purchase_order_form.qss', 'purchase_voucher_form.qss', 'grn_form.qss',
                'sales_order_form.qss', 'sales_voucher_form.qss', 'proforma_invoice_form.qss',
                'delivery_challan_form.qss'  # Add all new QSS files here
            ]
            stylesheet = ""
            for qss_file in qss_files:
                file_path = os.path.join(style_dir, qss_file)
                if os.path.exists(file_path):
                    with open(file_path, "r") as f:
                        stylesheet += f.read() + "\n"
                else:
                    logger.error(f"Stylesheet not found: {qss_file}")
            if stylesheet:
                self.setStyleSheet(stylesheet)
            else:
                logger.error("No stylesheets loaded from src/static/qss/")
        except Exception as e:
            logger.error(f"Failed to load stylesheets: {e}")

    def keyPressEvent(self, event):
        if event.key() == Qt.Key_Escape:
            self.handle_escape()

    def handle_escape(self):
        try:
            if self.setup_shown and (self.setup_win or self.dir_win):
                if self.setup_win:
                    self.setup_win.close()
                    self.setup_win = None
                if self.dir_win:
                    self.dir_win.close()
                    self.dir_win = None
                self.setup_shown = False
                return
            if self.add_window_open and self.add_window:
                self.add_window.close()
                self.add_window_open = False
                self.add_window = None
                return
            from src.erp.logic.utils.navigation_utils import go_back
            go_back(self)
        except Exception as e:
            logger.error(f"Failed to handle ESC key: {e}")
            QMessageBox.critical(self, "Error", f"Error navigating back: {e}")

    def show_frame(self, frame_name, add_to_history=True):
        from src.erp.logic.utils.navigation_utils import show_frame as nav_show_frame
        try:
            nav_show_frame(self, frame_name, add_to_history)
            populate_mega_menu(self)
            self.mega_menu.setVisible(True)
            self.toolbar.setVisible(True)
        except Exception as e:
            logger.error(f"Failed to show frame {frame_name}: {e}")
            QMessageBox.critical(self, "Error", f"Failed to navigate to {frame_name}: {e}")

    def get_permitted(self):
        if not self.current_user:
            logger.error("No user logged in, returning empty permissions")
            return []
        if self.current_user['username'] == "admins":
            return ["user_management"]
        return get_user_permissions(self.current_user['id'])

    def check_company_details(self):
        if not self.current_user:
            logger.error("No user logged in during company details check, skipping")
            return
        if self.current_user['username'] == "admins":
            self.company_details_exist = True
            self.default_directory_set = True
            self.show_frame("user_management", add_to_history=False)
            return
        session = Session()
        try:
            result = session.execute(text("""
                SELECT company_name, address1, city, state, pin, state_code, contact_no 
                FROM company_details WHERE id = 1
            """)).fetchone()
            if result:
                mandatory_fields = result
                default_dir = get_default_directory()
                empty_fields = [field for i, field in enumerate(['company_name', 'address1', 'city', 'state', 'pin', 'state_code', 'contact_no']) if not (mandatory_fields[i] and str(mandatory_fields[i]).strip())]
                if not empty_fields:
                    self.company_details_exist = True
                    self.default_directory_set = bool(default_dir)
                    if not self.default_directory_set:
                        try:
                            self.dir_win = show_default_directory_setup(self)
                            if self.dir_win:
                                self.dir_win.finished.connect(self.on_default_directory_dialog_finished)
                                self.dir_win.show()
                                self.dir_win.raise_()
                                self.dir_win.activateWindow()
                            else:
                                logger.error("Default directory dialog returned None")
                                self.show_frame("home", add_to_history=False)
                        except Exception as e:
                            logger.error(f"Failed to show default directory setup: {e}")
                            QMessageBox.critical(self, "Error", f"Failed to show default directory setup: {e}")
                            self.show_frame("home", add_to_history=False)
                    else:
                        self.show_frame("home", add_to_history=False)
                else:
                    self.company_details_exist = False
                    show_company_setup(self)
            else:
                self.company_details_exist = False
                show_company_setup(self)
        except Exception as e:
            logger.error(f"Database error during company check: {e}")
            QMessageBox.critical(self, "Error", f"Database error: {str(e)}")
            self.show_frame("home", add_to_history=False)
        finally:
            session.close()

    def on_default_directory_dialog_finished(self):
        try:
            self.dir_win = None
            self.setup_shown = False
            if self.company_details_exist and self.default_directory_set:
                self.show_frame("home", add_to_history=False)
            else:
                self.dir_win = show_default_directory_setup(self)
                if self.dir_win:
                    self.dir_win.finished.connect(self.on_default_directory_dialog_finished)
                    self.dir_win.show()
                    self.dir_win.raise_()
                    self.dir_win.activateWindow()
                else:
                    logger.error("Default directory dialog returned None")
                    self.show_frame("home", add_to_history=False)
        except Exception as e:
            logger.error(f"Error in on_default_directory_dialog_finished: {e}")
            self.show_frame("home", add_to_history=False)

    def exit_app(self, window=None):
        try:
            if window:
                window.close()
            self.setup_win = None
            self.dir_win = None
            self.setup_shown = False
            self.frames.clear()
            self.close()
            logger.info("Application exited")
        except Exception as e:
            logger.error(f"Error exiting application: {e}")

    def restart_app(self):
        python = sys.executable
        os.execl(python, python, *sys.argv)
