# src/erp/logic/utils/utils.py
# Converted DB parts: get_default_directory, fetch_company_name.

import os
import re
import json
import logging
from typing import List, Tuple
from PySide6.QtWidgets import QComboBox
from sqlalchemy import text
from src.erp.logic.database.session import engine, Session
from src.core.config import get_database_url, get_log_path

logging.basicConfig(filename=get_log_path(), level=logging.DEBUG, format='%(asctime)s - %(name)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

UNITS: List[str] = [
    "pcs", "g", "kg", "m", "l", "ml",
    "cm", "mm", "sqm", "cft", "unit"
]

STATES: List[Tuple[str, str]] = [
    ("Andaman and Nicobar Islands", "35"), ("Andhra Pradesh", "37"),
    ("Arunachal Pradesh", "12"), ("Assam", "18"),
    ("Bihar", "10"), ("Chandigarh", "04"),
    ("Chhattisgarh", "22"), ("Dadra and Nagar Haveli", "26"),
    ("Daman and Diu", "25"), ("Delhi", "07"),
    ("Goa", "30"), ("Gujarat", "24"),
    ("Haryana", "06"), ("Himachal Pradesh", "02"),
    ("Jammu and Kashmir", "01"), ("Jharkhand", "20"),
    ("Karnataka", "29"), ("Kerala", "32"),
    ("Lakshadweep", "31"), ("Madhya Pradesh", "23"),
    ("Maharashtra", "27"), ("Manipur", "14"),
    ("Meghalaya", "17"), ("Mizoram", "15"),
    ("Nagaland", "13"), ("Odisha", "21"),
    ("Puducherry", "34"), ("Punjab", "03"),
    ("Rajasthan", "08"), ("Sikkim", "11"),
    ("Tamil Nadu", "33"), ("Telangana", "36"),
    ("Tripura", "16"), ("Uttar Pradesh", "09"),
    ("Uttarakhand", "05"), ("West Bengal", "19")
]

VENDOR_COLUMNS: List[str] = [
    "Name", "Contact No", "Address Line 1", "Address Line 2",
    "City", "State", "State Code", "PIN Code",
    "GST No", "PAN No", "Email"
]

CUSTOMER_COLUMNS: List[str] = [
    "Name", "Contact No", "Address Line 1", "Address Line 2",
    "City", "State", "State Code", "PIN Code",
    "GST No", "PAN No", "Email"
]

LEDGER_COLUMNS = [
    "Ledger Name", "Ledger Group", "Opening Balance", "Address", "City", "State",
    "State Code", "PIN Code", "GSTIN", "PAN Number", "Contact Number", "Email",
    "Bank Account Number", "IFSC Code", "Bank Name", "Credit Limit", "Credit Period",
    "Tax Type", "MSME Registration", "LUT Number", "Vendor Code", "Customer Code",
    "Taxable Amount", "Discount Percentage", "Discount Amount", "CGST Amount",
    "SGST Amount", "IGST Amount", "Cess Amount", "Total Amount", "Round Off",
    "Net Amount", "Narration", "Terms of Payment", "Delivery Terms", "Freight Charges",
    "Insurance Charges", "Place of Supply", "Reverse Charge Applicable", "E-Way Bill Number",
    "Transport Mode", "Vehicle Number", "LR/RR Number", "Project Code", "Cost Center",
    "Due Date", "TDS Amount", "TCS Amount", "Invoice Number", "Reference Number",
    "Payment Status", "Tax Rate", "HSN/SAC Code", "Item Description", "Quantity",
    "Unit of Measure", "Unit Price"
]

PREDEFINED_COLUMNS = [
    "Sales Invoice Number", "Invoice Number", "Invoice Date", "Sales Order Number",
    "Customer Name", "Total Amount", "CGST Amount", "SGST Amount", "IGST Amount"
]

def filter_combobox(combo: QComboBox, text: str) -> None:
    """No longer used for CompanySetupDialog; kept for other modules."""
    try:
        text = text.strip().lower()
        combo.blockSignals(True)
        combo.clear()
        combo.addItems([s[0] for s in STATES])
        if not text:
            combo.setCurrentIndex(-1)
            combo.showPopup()
            logger.debug(f"Reset QComboBox, text cleared: {text}")
            combo.blockSignals(False)
            return
        filtered_items = [s[0] for s in STATES if text in s[0].lower()]
        combo.clear()
        combo.addItems(filtered_items)
        combo.setCurrentText(text)
        combo.showPopup()
        logger.debug(f"Filtered QComboBox with text: {text}, items: {filtered_items}")
    except Exception as e:
        logger.error(f"Error filtering combobox: {e}")
    finally:
        combo.blockSignals(False)

def number_to_words(num: float) -> str:
    try:
        num = float(num)
        if num < 0:
            logger.warning(f"Negative number provided to number_to_words: {num}")
            return "Negative Amount"
        if num == 0:
            return "Zero"
        units = ["", "One", "Two", "Three", "Four", "Five", "Six", "Seven", "Eight", "Nine"]
        teens = ["Ten", "Eleven", "Twelve", "Thirteen", "Fourteen", "Fifteen", "Sixteen", "Seventeen", "Eighteen", "Nineteen"]
        tens = ["", "", "Twenty", "Thirty", "Forty", "Fifty", "Sixty", "Seventy", "Eighty", "Ninety"]
        thousands = ["", "Thousand", "Lakh", "Crore"]
        def convert_less_than_thousand(n: int) -> str:
            if n == 0:
                return ""
            elif n < 10:
                return units[n]
            elif n < 20:
                return teens[n - 10]
            elif n < 100:
                return tens[n // 10] + (" " + units[n % 10] if n % 10 else "")
            else:
                return units[n // 100] + " Hundred" + (" " + convert_less_than_thousand(n % 100) if n % 100 else "")
        parts = []
        i = 0
        whole = int(num)
        while whole > 0:
            if whole % 1000 != 0:
                part = convert_less_than_thousand(whole % 1000)
                if i > 0:
                    part += " " + thousands[i]
                parts.append(part)
            whole //= 1000
            i += 1
        words = " ".join(reversed(parts)).strip() or "Zero"
        decimal = round((num - int(num)) * 100)
        if decimal > 0:
            words += " and " + convert_less_than_thousand(decimal) + " Paise"
        return words + " Only"
    except ValueError as e:
        logger.error(f"Error converting number to words: {e}")
        return "Invalid Amount"

def update_state_code(state: str, state_code_widget=None) -> str | None:
    try:
        state = state.strip().lower()
        for s, code in STATES:
            if s.lower() == state:
                if state_code_widget:
                    state_code_widget.setText(code)
                    logger.debug(f"State code updated for {state}: {code}")
                    return None
                else:
                    return code
        if state_code_widget:
            state_code_widget.setText("")
            logger.debug(f"No state code found for {state}")
            return None
        else:
            return ""
    except Exception as e:
        logger.error(f"Error updating state code: {e}")
        if state_code_widget:
            return None
        else:
            return ""

def add_unit(unit: str):
    try:
        global UNITS
        unit = unit.strip().lower()
        if unit and unit not in UNITS:
            UNITS.append(unit)
            logger.info(f"Added unit: {unit}")
    except Exception as e:
        logger.error(f"Error adding unit: {e}")

def get_default_directory():
    session = Session()
    try:
        result = session.execute(text("SELECT default_directory FROM company_details WHERE id = 1")).fetchone()
        return result[0] if result else os.path.expanduser("~/Documents/ERP")
    except Exception as e:
        logger.error(f"Error fetching default directory: {e}")
        return os.path.expanduser("~/Documents/ERP")
    finally:
        session.close()

def create_module_directory(module_name: str) -> str:
    try:
        default_dir = get_default_directory()
        if not default_dir:
            raise ValueError("Default directory not set")
        module_dir = os.path.join(default_dir, module_name.replace(" ", "_"))
        os.makedirs(module_dir, exist_ok=True)
        logger.debug(f"Created module directory: {module_dir}")
        return module_dir
    except (OSError, ValueError) as e:
        logger.error(f"Error creating module directory {module_name}: {e}")
        return None

def fetch_company_name():
    session = Session()
    try:
        result = session.execute(text("SELECT company_name FROM company_details WHERE id = 1")).fetchone()
        return result[0] if result else "Your Company"
    except Exception as e:
        logger.error(f"Error fetching company name: {e}")
        return "Your Company"
    finally:
        session.close()

def suggest_data_type(column_name: str) -> str:
    try:
        column_name = column_name.lower()
        if any(kw in column_name for kw in ['amount', 'price', 'rate', 'percentage', 'discount', 'tax', 'charges', 'balance', 'limit']):
            return 'REAL'
        elif 'date' in column_name:
            return 'DATE'
        elif any(kw in column_name for kw in ['quantity', 'qty']):
            return 'INTEGER'
        return 'TEXT'
    except Exception as e:
        logger.error(f"Error suggesting data type for {column_name}: {e}")
        return 'TEXT'

def suggest_calculation_logic(column_name: str) -> tuple[dict | None, bool]:
    try:
        column_name = column_name.lower()
        if 'discount %' in column_name or 'discount percentage' in column_name:
            return {
                'type': 'discount_percentage',
                'inputs': ['Unit Price', 'Qty', 'Discount Percentage'],
                'output': 'Discount Amount'
            }, True
        elif 'tax amount' in column_name:
            return {
                'type': 'tax_amount',
                'inputs': ['Unit Price', 'Qty', 'Tax Rate'],
                'output': 'Tax Amount'
            }, True
        elif 'net amount' in column_name:
            return {
                'type': 'net_amount',
                'inputs': ['Total Amount', 'Discount Amount', 'Tax Amount'],
                'output': 'Net Amount'
            }, True
        elif 'round off' in column_name:
            return {
                'type': 'round_off',
                'inputs': ['Net Amount'],
                'output': 'Round Off'
            }, True
        elif 'cgst amount' in column_name:
            return {
                'type': 'cgst_amount',
                'inputs': ['Taxable Amount', 'GST Rate'],
                'output': 'CGST Amount'
            }, True
        elif 'sgst amount' in column_name:
            return {
                'type': 'sgst_amount',
                'inputs': ['Taxable Amount', 'GST Rate'],
                'output': 'SGST Amount'
            }, True
        elif 'igst amount' in column_name:
            return {
                'type': 'igst_amount',
                'inputs': ['Taxable Amount', 'GST Rate'],
                'output': 'IGST Amount'
            }, True
        elif 'amount' in column_name:
            return {
                'type': 'amount',
                'inputs': ['Unit Price', 'Qty'],
                'output': 'Amount'
            }, True
        return None, False
    except Exception as e:
        logger.error(f"Error suggesting calculation logic for {column_name}: {e}")
        return None, False