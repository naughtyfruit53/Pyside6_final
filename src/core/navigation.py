# navigation.py
from PySide6.QtWidgets import QFrame, QLabel, QHBoxLayout, QMenu, QApplication, QMessageBox
from PySide6.QtCore import Qt, QEvent, QTimer
from PySide6.QtGui import QCursor
import logging
from src.core.config import get_log_path
from src.erp.logic.utils.navigation_utils import show_frame
from src.erp.logic.user_management_logic import get_user_permissions
from src.erp.logic.database.voucher import get_voucher_types_by_module
from src.erp.voucher.custom_voucher import create_custom_voucher_type
from src.core.frames import add_voucher_frame, refresh_vouchers

logging.basicConfig(
    filename=get_log_path(),
    level=logging.DEBUG,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

def populate_mega_menu(app):
    if not app.current_user:
        logger.error("No user logged in, skipping mega menu population")
        return

    app.mega_menu.setObjectName("megaMenu")

    if app.mega_menu.layout():
        while app.mega_menu.layout().count():
            item = app.mega_menu.layout().takeAt(0)
            if item.widget():
                item.widget().deleteLater()
    else:
        app.mega_menu.setLayout(QHBoxLayout())

    tab_frame = QFrame(app.mega_menu)
    tab_frame.setObjectName("tabFrame")
    tab_frame.setMouseTracking(True)
    tab_layout = QHBoxLayout(tab_frame)
    tab_layout.setContentsMargins(10, 5, 10, 5)
    tab_layout.setSpacing(0)

    module_map = {
        "Purchase Vouchers": "purchase",
        "Sales Vouchers": "sales",
        "Financial Vouchers": "financial",
        "Internal Vouchers": "internal"
    }

    all_modules = [
        ("Home", "home", "🏠", [("Home", "home")]),
        ("Dashboard", "dashboard", "📊", [("Dashboard", "dashboard")]),
        ("Master", "master", "🗂", [
            ("Company Details", "company"),
            ("Vendors", "vendors"),
            ("Products", "products"),
            ("Customer Details", "customers"),
            ("Default Directory", "default_directory"),
            ("User Management", "user_management")
        ]),
        ("Vouchers", "vouchers", "📜", [
            ("Purchase Vouchers", None, [
                (voucher_type, f"vouchers-{voucher_type.lower().replace(' ', '_').replace('_(goods_receipt_note)', '')}")
                for voucher_type in get_voucher_types_by_module("purchase")
            ]),
            ("Sales Vouchers", None, [
                (voucher_type, f"vouchers-{voucher_type.lower().replace(' ', '_').replace('_(goods_receipt_note)', '')}")
                for voucher_type in get_voucher_types_by_module("sales")
            ]),
            ("Financial Vouchers", None, [
                (voucher_type, f"vouchers-{voucher_type.lower().replace(' ', '_').replace('_(goods_receipt_note)', '')}")
                for voucher_type in get_voucher_types_by_module("financial")
            ]),
            ("Internal Vouchers", None, [
                (voucher_type, f"vouchers-{voucher_type.lower().replace(' ', '_').replace('_(goods_receipt_note)', '')}")
                for voucher_type in get_voucher_types_by_module("internal")
            ])
        ]),
        ("Inventory", "stock", "📈", [("Stock", "stock")]),
        ("Manufacturing", "manufacturing", "🏭", [
            ("Create BOM", "create_bom"),
            ("Create Work Order", "create_work_order"),
            ("Close Work Order", "close_work_order")
        ]),
        ("Service", "service", "🔧", [("Service", "service")]),
        ("HR Management", "hr_management", "👩‍💼", [("HR Management", "hr_management")]),
        ("Backup & Restore", "backup_boss", "💾", [
            ("Backup", "backup"),
            ("Restore", "restore"),
            ("Auto Backup", "auto_backup"),
            ("Reset Database", "reset")
        ]),
    ]

    permitted_modules = []
    if app.current_user['username'] == "admins":
        permitted_modules = [("User Management", "user_management", "🛠", [("User Management", "user_management")])]
    else:
        user_permissions = get_user_permissions(app.current_user['id'])
        for module in all_modules:
            module_name = module[1]
            if module_name in user_permissions or module_name in ["vouchers", "stock", "backup_boss"]:
                if module[3]:
                    permitted_children = []
                    for child in module[3]:
                        if len(child) == 2:
                            child_name, child_frame = child
                            if child_name.replace(' ', '_').lower() in user_permissions or module_name in ['vouchers', 'stock', 'backup_boss']:
                                permitted_children.append((child_name, child_frame, []))
                        elif len(child) == 3:
                            child_name, child_frame, sub_children = child
                            permitted_sub_children = []
                            for sub_child_name, sub_child_frame in sub_children:
                                if sub_child_frame in user_permissions or module_name == 'vouchers':
                                    permitted_sub_children.append((sub_child_name, sub_child_frame))
                            if permitted_sub_children:
                                permitted_children.append((child_name, child_frame, permitted_sub_children))
                    if permitted_children or module_name in ['vouchers', 'stock', 'manufacturing', 'backup_boss']:
                        permitted_modules.append((module[0], module[1], module[2], permitted_children))
                else:
                    permitted_modules.append(module)

    active_menu = [None]
    close_timer = QTimer(app)
    close_timer.setSingleShot(True)
    close_timer.setInterval(200)

    def close_active_menu():
        if active_menu[0]:
            active_menu[0].close()
            active_menu[0] = None

    close_timer.timeout.connect(close_active_menu)

    def is_over_menu_or_tab():
        hovered_widget = QApplication.widgetAt(QCursor.pos())
        return hovered_widget and ( (isinstance(hovered_widget, QLabel) and hovered_widget.objectName() == "tabLabel") or isinstance(hovered_widget, QMenu) or hovered_widget.objectName() == "tabFrame" )

    def start_close_timer_if_outside(event):
        try:
            if active_menu[0] and not is_over_menu_or_tab():
                close_timer.start()
            event.accept()
        except Exception as e:
            logger.error(f"Error in start_close_timer_if_outside: {e}")
            event.accept()

    def stop_close_timer(event):
        close_timer.stop()
        event.accept()

    tab_frame.enterEvent = stop_close_timer
    tab_frame.leaveEvent = start_close_timer_if_outside

    for idx, (module_name, frame_name, icon, children) in enumerate(permitted_modules):
        tab_label = QLabel(f"{icon} {module_name}")
        tab_label.setObjectName("tabLabel")
        tab_label.setCursor(QCursor(Qt.PointingHandCursor))
        has_submenu = len(children) > 1 or (len(children) == 1 and len(children[0]) == 3)
        tab_label.setProperty("hasSubmenu", has_submenu)
        tab_label.setMouseTracking(True)
        tab_layout.addWidget(tab_label)

        has_single_matching_child = len(children) == 1 and len(children[0]) >= 2 and children[0][1] == frame_name

        tab_label.leaveEvent = start_close_timer_if_outside
        tab_label.enterEvent = stop_close_timer

        if has_submenu and not has_single_matching_child:
            dropdown_menu = QMenu(app)
            dropdown_menu.setObjectName("dropdownMenu")
            dropdown_menu.setMinimumWidth(200)
            for child in children:
                child_name, child_frame, sub_children = child if len(child) == 3 else (child[0], child[1], [])
                if sub_children:
                    sub_menu = QMenu(child_name, app)
                    sub_menu.setObjectName("dropdownMenu")
                    for sub_child_name, sub_child_frame in sub_children:
                        sub_menu.addAction(sub_child_name, lambda f=sub_child_frame: show_frame(app, f))
                    sub_menu.addSeparator()
                    module = module_map.get(child_name, "")
                    if module:
                        sub_menu.addAction("Create Custom Voucher", lambda m=module: create_custom_voucher_type(app, None, None, m, lambda id, n: add_voucher_frame(app, n), lambda msg: QMessageBox.critical(app, "Error", msg), lambda: refresh_vouchers(app)))
                    dropdown_menu.addMenu(sub_menu)
                else:
                    dropdown_menu.addAction(child_name, lambda f=child_frame: show_frame(app, f))

            dropdown_menu.leaveEvent = start_close_timer_if_outside
            dropdown_menu.enterEvent = stop_close_timer

            def show_dropdown(event, label=tab_label, menu=dropdown_menu):
                try:
                    if active_menu[0] and active_menu[0] != menu:
                        active_menu[0].close()
                    pos = label.mapToGlobal(label.rect().bottomLeft())
                    menu.popup(pos)
                    active_menu[0] = menu
                except Exception as e:
                    logger.error(f"Error showing dropdown menu: {e}")

            def handle_enter(event, label=tab_label, menu=dropdown_menu):
                try:
                    close_timer.stop()
                    if active_menu[0] != menu:
                        show_dropdown(None, label, menu)
                    event.accept()
                except Exception as e:
                    logger.error(f"Error in handle_enter: {e}")
                    event.accept()

            tab_label.mousePressEvent = lambda e, l=tab_label, m=dropdown_menu: show_dropdown(e, l, m)
            tab_label.enterEvent = lambda e, l=tab_label, m=dropdown_menu: handle_enter(e, l, m)
        else:
            def handle_enter_no_sub(event):
                try:
                    close_timer.stop()
                    if active_menu[0]:
                        close_timer.start()
                    event.accept()
                except Exception as e:
                    logger.error(f"Error in handle_enter_no_sub: {e}")
                    event.accept()

            tab_label.enterEvent = handle_enter_no_sub
            tab_label.mousePressEvent = lambda e, f=frame_name: show_frame(app, f)

    tab_layout.addStretch()
    tab_frame.setLayout(tab_layout)
    app.mega_menu.layout().addWidget(tab_frame)
    tab_frame.setVisible(True)
    app.mega_menu.setVisible(True)