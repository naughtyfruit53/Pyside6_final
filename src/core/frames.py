# frames.py
from PySide6.QtWidgets import QWidget, QVBoxLayout, QLabel, QPushButton, QMessageBox, QHBoxLayout
from PySide6.QtCore import Qt
from PySide6.QtGui import QPixmap, QImage
import logging
import os
from PIL import Image
import io
from src.core.config import get_static_path, get_log_path
from src.erp.ui.company_details_ui import CompanyDetailsWidget
from src.erp.ui.user_management_ui import UserManagementWidget
from src.erp.ui.vendors_ui import VendorsWidget
from src.erp.ui.products_ui import ProductsWidget
from src.erp.ui.customers_ui import CustomersWidget
from src.erp.ui.stock_ui import StockUI
from src.erp.ui.manufacturing_ui import ManufacturingUI, BOMUI, WorkOrderUI, CloseWorkOrderUI
from src.erp.ui.backup_restore_ui import create_backup_frame, create_restore_frame, create_auto_backup_frame
from src.erp.ui.default_directory_ui import create_default_directory_frame
from src.erp.voucher.voucher_ui import VoucherUI
from src.erp.logic.database.voucher import get_voucher_types, get_voucher_types_by_module
from src.erp.voucher.custom_voucher import create_custom_voucher_type

logging.basicConfig(
    filename=get_log_path(),
    level=logging.DEBUG,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

def initialize_frames(app):
    frames = {}
    frame_classes = {
        "home": create_home_frame,
        "dashboard": create_dashboard_frame,
        "company": company_details,
        "vendors": lambda parent, app: VendorsWidget(parent, app),
        "products": lambda parent, app: ProductsWidget(parent, app),
        "customers": lambda parent, app: CustomersWidget(parent, app),
        "stock": stock_management,
        "manufacturing": manufacturing,
        "create_bom": create_bom,
        "create_work_order": create_work_order,
        "close_work_order": close_work_order,
        "master": create_master_frame,
        "vouchers": create_vouchers_frame,
        "backup_boss": create_backup_boss_frame,
        "backup": create_backup_frame,
        "restore": create_restore_frame,
        "auto_backup": create_auto_backup_frame,
        "default_directory": create_default_directory_frame,
        "user_management": user_management,
        "reset": create_reset_frame,
    }
    voucher_types = get_voucher_types() or []
    for voucher_type in voucher_types:
        frame_name = f"vouchers-{voucher_type[1].lower().replace(' ', '_').replace('_(goods_received_note)', '')}"
        frame_classes[frame_name] = lambda parent, app, fn=frame_name: VoucherUI(app).create_voucher_frame(parent, app, None, fn)

    for name, frame_func in frame_classes.items():
        try:
            frame = frame_func(app.right_pane, app)
            if frame is None or not isinstance(frame, QWidget):
                logger.error(f"Frame function {name} returned invalid frame: {frame}")
                QMessageBox.critical(app, "Error", f"Failed to initialize {name}: Frame returned invalid or None")
                continue
            if name == "stock" and hasattr(app, 'stock_logic') and hasattr(app.stock_logic, 'set_ui'):
                app.stock_logic.set_ui(frame)
            elif name == "manufacturing" and hasattr(app, 'manufacturing_logic') and hasattr(app.manufacturing_logic, 'set_manufacturing_ui'):
                app.manufacturing_logic.set_manufacturing_ui(frame)
            elif name == "create_bom" and hasattr(app, 'manufacturing_logic') and hasattr(app.manufacturing_logic, 'set_bom_ui'):
                app.manufacturing_logic.set_bom_ui(frame)
            elif name == "create_work_order" and hasattr(app, 'manufacturing_logic') and hasattr(app.manufacturing_logic, 'set_work_order_ui'):
                app.manufacturing_logic.set_work_order_ui(frame)
            elif name == "close_work_order" and hasattr(app, 'manufacturing_logic') and hasattr(app.manufacturing_logic, 'set_close_work_order_ui'):
                app.manufacturing_logic.set_close_work_order_ui(frame)
            app.right_pane.addWidget(frame)
            frames[name] = frame
        except AttributeError as e:
            logger.error(f"Failed to initialize frame {name}: {e}")
            QMessageBox.warning(app, "Warning", f"Failed to initialize {name} due to missing logic or method. Frame will be loaded without logic.")
            app.right_pane.addWidget(frame)
            frames[name] = frame
            continue
        except Exception as e:
            logger.error(f"Failed to initialize frame {name}: {e}")
            QMessageBox.critical(app, "Error", f"Failed to initialize {name}: {str(e)}")
            continue
    return frames

def add_voucher_frame(app, voucher_type):
    frame_name = f"vouchers-{voucher_type.lower().replace(' ', '_').replace('_(goods_receipt_note)', '')}"
    if frame_name in app.frames:
        return
    frame = VoucherUI(app).create_voucher_frame(app.right_pane, app, None, frame_name)
    app.right_pane.addWidget(frame)
    app.frames[frame_name] = frame

def refresh_vouchers(app):
    if "vouchers" in app.frames:
        app.frames["vouchers"].deleteLater()
        del app.frames["vouchers"]
    frame = create_vouchers_frame(app.right_pane, app)
    app.right_pane.addWidget(frame)
    app.frames["vouchers"] = frame
    if app.current_frame_name == "vouchers":
        app.show_frame("vouchers", add_to_history=False)

def create_home_frame(parent, app):
    frame = QWidget(parent)
    layout = QVBoxLayout(frame)
    layout.setAlignment(Qt.AlignCenter)

    logo_path = get_static_path("tritiq.png")
    if os.path.exists(logo_path):
        try:
            image = Image.open(logo_path)
            image = image.convert("RGB")
            max_height = int(0.25 * app.screen().size().height())
            image = image.resize((int(max_height * image.width / image.height), max_height), Image.Resampling.LANCZOS)
            buffer = io.BytesIO()
            image.save(buffer, format="PNG")
            qimage = QImage()
            qimage.loadFromData(buffer.getvalue())
            pixmap = QPixmap.fromImage(qimage)
            logo_label = QLabel()
            logo_label.setPixmap(pixmap)
            logo_label.setStyleSheet("background-color: #ffffff; border: none;")
            layout.addWidget(logo_label)
        except Exception as e:
            logger.error(f"Failed to load logo in home frame: {e}")
            logo_label = QLabel("Error Loading Logo")
            logo_label.setObjectName("errorLabel")
            layout.addWidget(logo_label)
    else:
        logger.error(f"Logo file not found at: {logo_path}")
        logo_label = QLabel("TRITIQ Logo Not Found")
        logo_label.setObjectName("errorLabel")
        layout.addWidget(logo_label)

    title_label = QLabel("TRITIQ ERP System")
    title_label.setObjectName("titleLabel")
    layout.addWidget(title_label)

    subtitle_label = QLabel("Welcome to your ERP Dashboard")
    subtitle_label.setObjectName("subtitleLabel")
    layout.addWidget(subtitle_label)

    frame.setLayout(layout)
    return frame

def create_dashboard_frame(parent, app):
    frame = QWidget(parent)
    layout = QVBoxLayout(frame)
    layout.setAlignment(Qt.AlignCenter)

    title_label = QLabel("Dashboard - Overview")
    title_label.setObjectName("titleLabel")
    layout.addWidget(title_label)

    subtitle_label = QLabel("Key metrics and analytics will be displayed here.")
    subtitle_label.setObjectName("subtitleLabel")
    layout.addWidget(subtitle_label)

    frame.setLayout(layout)
    return frame

def create_master_frame(parent, app):
    frame = QWidget(parent)
    layout = QVBoxLayout(frame)
    layout.setAlignment(Qt.AlignCenter)

    title_label = QLabel("Master Data Management")
    title_label.setObjectName("titleLabel")
    layout.addWidget(title_label)

    buttons = [
        ("Company Details", lambda: app.show_frame("company")),
        ("Vendors", lambda: app.show_frame("vendors")),
        ("Products", lambda: app.show_frame("products")),
        ("Customers", lambda: app.show_frame("customers")),
        ("User Management", lambda: app.show_frame("user_management"))
    ]
    for text, command in buttons:
        btn = QPushButton(text)
        btn.setObjectName("actionButton")
        btn.clicked.connect(command)
        layout.addWidget(btn)

    frame.setLayout(layout)
    return frame

def create_vouchers_frame(parent, app):
    frame = QWidget(parent)
    layout = QVBoxLayout(frame)
    layout.setAlignment(Qt.AlignTop)

    title_label = QLabel("Voucher Management")
    title_label.setObjectName("titleLabel")
    layout.addWidget(title_label)

    category_map = {
        "Purchase Vouchers": "purchase",
        "Sales Vouchers": "sales",
        "Financial Vouchers": "financial",
        "Internal Vouchers": "internal"
    }

    for cat_title, module in category_map.items():
        cat_label = QLabel(cat_title)
        cat_label.setObjectName("subtitleLabel")
        layout.addWidget(cat_label)

        voucher_types = get_voucher_types_by_module(module)
        for vt in sorted(voucher_types):
            btn = QPushButton(vt)
            btn.setObjectName("actionButton")
            frame_name = f"vouchers-{vt.lower().replace(' ', '_').replace('_(goods_receipt_note)', '')}"
            btn.clicked.connect(lambda checked, f=frame_name: app.show_frame(f))
            layout.addWidget(btn)

        custom_btn = QPushButton("Create Custom Voucher")
        custom_btn.setObjectName("actionButton")
        custom_btn.clicked.connect(lambda checked, m=module: create_custom_voucher_type(app, frame, None, m, lambda id, n: add_voucher_frame(app, n), lambda msg: QMessageBox.critical(frame, "Error", msg), lambda: refresh_vouchers(app)))
        layout.addWidget(custom_btn)

    layout.addStretch()
    frame.setLayout(layout)
    return frame

def create_service_frame(parent, app):
    frame = QWidget(parent)
    layout = QVBoxLayout(frame)
    layout.setAlignment(Qt.AlignCenter)

    title_label = QLabel("Service Management")
    title_label.setObjectName("titleLabel")
    layout.addWidget(title_label)

    subtitle_label = QLabel("Service-related features will be implemented here.")
    subtitle_label.setObjectName("subtitleLabel")
    layout.addWidget(subtitle_label)

    frame.setLayout(layout)
    return frame

def create_hr_management_frame(parent, app):
    frame = QWidget(parent)
    layout = QVBoxLayout(frame)
    layout.setAlignment(Qt.AlignCenter)

    title_label = QLabel("HR Management")
    title_label.setObjectName("titleLabel")
    layout.addWidget(title_label)

    subtitle_label = QLabel("HR-related features will be implemented here.")
    subtitle_label.setObjectName("subtitleLabel")
    layout.addWidget(subtitle_label)

    frame.setLayout(layout)
    return frame

def create_backup_boss_frame(parent, app):
    frame = QWidget(parent)
    layout = QVBoxLayout(frame)
    layout.setAlignment(Qt.AlignCenter)

    title_label = QLabel("Backup and Restore")
    title_label.setObjectName("titleLabel")
    layout.addWidget(title_label)

    buttons = [
        ("Backup", lambda: app.show_frame("backup")),
        ("Restore", lambda: app.show_frame("restore")),
        ("Auto Backup Settings", lambda: app.show_frame("auto_backup")),
        ("Set Default Directory", lambda: app.show_frame("default_directory")),
        ("Reset Database", lambda: app.show_frame("reset"))
    ]
    for text, command in buttons:
        btn = QPushButton(text)
        btn.setObjectName("actionButton")
        btn.clicked.connect(command)
        layout.addWidget(btn)

    frame.setLayout(layout)
    return frame

def create_reset_frame(parent, app):
    frame = QWidget(parent)
    layout = QVBoxLayout(frame)
    layout.setAlignment(Qt.AlignCenter)

    title_label = QLabel("Reset Database")
    title_label.setObjectName("titleLabel")
    layout.addWidget(title_label)

    warning_label = QLabel("Warning: This will delete all data and reset the database to its initial state.")
    warning_label.setObjectName("warningLabel")
    warning_label.setWordWrap(True)
    layout.addWidget(warning_label)

    reset_button = QPushButton("Reset Database")
    reset_button.setObjectName("dangerButton")
    reset_button.clicked.connect(lambda: handle_reset(app))
    layout.addWidget(reset_button)

    frame.setLayout(layout)
    return frame

def handle_reset(app):
    from PySide6.QtWidgets import QMessageBox, QInputDialog
    reply = QMessageBox.question(app, "Confirm Reset", "Are you sure you want to reset the database? This action cannot be undone.", QMessageBox.Yes | QMessageBox.No)
    if reply == QMessageBox.Yes:
        text, ok = QInputDialog.getText(app, "Confirmation", "Type 'RESET' in all caps to confirm:")
        if ok and text.strip() == "RESET":
            from src.erp.logic.database.db_utils import reset_database
            try:
                reset_database(confirm=True)
                QMessageBox.information(app, "Success", "Database has been reset. The application will now restart.")
                app.restart_app()
            except Exception as e:
                QMessageBox.critical(app, "Error", f"Failed to reset database: {str(e)}")
        else:
            QMessageBox.warning(app, "Cancelled", "Reset cancelled. Confirmation text did not match.")
    else:
        QMessageBox.information(app, "Cancelled", "Reset cancelled.")

def company_details(parent, app):
    return CompanyDetailsWidget(parent, app)

def stock_management(parent, app):
    return StockUI(parent, app)

def manufacturing(parent, app):
    return ManufacturingUI(parent, app)

def create_bom(parent, app):
    return BOMUI(parent, app)

def create_work_order(parent, app):
    return WorkOrderUI(parent, app)

def close_work_order(parent, app):
    return CloseWorkOrderUI(parent, app)

def user_management(parent, app):
    return UserManagementWidget(parent, app)