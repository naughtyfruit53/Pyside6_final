# src/erp/voucher/callbacks.py
# No direct DB access, but calls functions that do; no change needed.

import logging
from src.erp.logic.vendors_logic import add_vendor
from src.erp.logic.customers_logic import add_customer
from src.erp.logic.products_logic import add_product, close_window
from src.core.config import get_database_url, get_log_path
from src.erp.logic.utils.voucher_utils import get_products, get_vendors, get_customers

logging.basicConfig(filename=get_log_path(), level=logging.DEBUG, format='%(asctime)s - %(name)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

def add_vendor_callback(form, vendor_combo, management=None):
    def vendor_added_callback(vendor_id, vendor_name):
        vendor_combo.clear()
        vendor_combo.addItems(get_vendors() or ["No vendors available"])
        vendor_combo.setCurrentText(vendor_name)
        logger.debug(f"Vendor combobox updated, selected: {vendor_name}")
    add_vendor(form.app, parent=form, callback=vendor_added_callback)
    form.app.add_window_open = False  # Reset flag after dialog closes

def add_customer_callback(form, customer_combo, management=None):
    def customer_added_callback(customer_id, customer_name):
        customer_combo.clear()
        customer_combo.addItems(get_customers() or ["No customers available"])
        customer_combo.setCurrentText(customer_name)
        logger.debug(f"Customer combobox updated, selected: {customer_name}")
    add_customer(form.app, parent=form, callback=customer_added_callback)
    form.app.add_window_open = False  # Reset flag after dialog closes

def add_product_callback(form, product_combo, management=None, voucher_type_id=None, products=None, font=None, col_widths=None, update_product_frame_position=None, populate_callback=None):
    def product_added_callback(product_id, product_name):
        products[:] = get_products()
        product_combo.clear()
        product_combo.addItems([p[1] for p in products] or ["No products available"])
        product_combo.setCurrentText(product_name)
        logger.debug(f"Product combobox updated, selected: {product_name}")
        from src.erp.voucher.voucher_operations import handle_product_selection
        handle_product_selection(form, voucher_type_id, product_name, products, font, col_widths, update_product_frame_position)
        if populate_callback:
            populate_callback(form.item_table)
    add_product(form.app, callback=product_added_callback)
    form.app.add_window_open = False  # Reset flag after dialog closes

def close_window_item(form, window):
    close_window(window, form.app)