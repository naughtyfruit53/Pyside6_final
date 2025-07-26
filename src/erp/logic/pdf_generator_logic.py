# src/erp/logic/pdf_generator_logic.py
# No direct DB changes, but uses sqlite3, convert to SQLAlchemy.

import logging
from datetime import datetime
from sqlalchemy import text
from src.erp.logic.database.session import engine, Session
from src.core.config import get_database_url
from src.templates.document_templates_logic import (
    generate_po_template,
    generate_grn_template,
    generate_rejection_template,
    generate_purchase_inv_template,
    generate_credit_note_template,
    generate_material_out_template,
    generate_quotation_template,
    generate_sales_order_template,
    generate_proforma_invoice_template,
    generate_sales_inv_template,
    generate_delivery_challan_template,
    generate_debit_note_template,
    generate_non_sales_credit_note_template,
    generate_payment_voucher_template,
    generate_receipt_voucher_template,
    generate_contra_voucher_template,
    generate_journal_voucher_template
)

logger = logging.getLogger(__name__)

class PDFGeneratorLogic:
    def __init__(self, app):
        self.app = app

    def generate_pdf(self, template_type, doc_number):
        session = Session()
        try:
            transactions = session.execute(text("""
                SELECT mt.doc_number, mt.date, mt.type, p.name, mt.quantity, p.unit, mt.remarks
                FROM material_transactions mt
                JOIN products p ON mt.product_id = p.id
                WHERE mt.doc_number = :doc_number
            """), {"doc_number": doc_number}).fetchall()
            if not transactions:
                logger.error(f"No transactions found for document number: {doc_number}")
                return None

            items = [
                {
                    "s_no": idx + 1,
                    "description": row[3],
                    "quantity": row[4],
                    "unit": row[5],
                    "rate": 0,  # Placeholder, update if rate is stored
                    "gst": 0,   # Placeholder, update if GST is stored
                    "amount": 0 # Placeholder, update if amount is stored
                } for idx, row in enumerate(transactions)
            ]
            company_data = [("Company Name", "Your Company")]  # Placeholder
            party_data = [("Party Name", "Sample Party")]     # Placeholder
            voucher_date = transactions[0][1]
            total_amount = sum(item["quantity"] * item["rate"] for item in items)
            cgst = sgst = igst = 0  # Placeholder, update if GST is stored

            file_path = f"{template_type}_{doc_number.replace('/', '_')}.pdf"
            template_map = {
                "Purchase Order": generate_po_template,
                "Goods Receipt Note": generate_grn_template,
                "Rejection Slip": generate_rejection_template,
                "Purchase Invoice": generate_purchase_inv_template,
                "Credit Note": generate_credit_note_template,
                "Material Out": generate_material_out_template,
                "Quotation": generate_quotation_template,
                "Sales Order": generate_sales_order_template,
                "Proforma Invoice": generate_proforma_invoice_template,
                "Sales Invoice": generate_sales_inv_template,
                "Delivery Challan": generate_delivery_challan_template,
                "Debit Note": generate_debit_note_template,
                "Non-Sales Credit Note": generate_non_sales_credit_note_template,
                "Payment Voucher": generate_payment_voucher_template,
                "Receipt Voucher": generate_receipt_voucher_template,
                "Contra Voucher": generate_contra_voucher_template,
                "Journal Voucher": generate_journal_voucher_template
            }

            if template_type not in template_map:
                logger.error(f"Invalid template type: {template_type}")
                return None

            template_func = template_map[template_type]
            template_func(
                file_path,
                company_data,
                party_data,
                doc_number,
                voucher_date,
                items,
                total_amount=total_amount,
                cgst=cgst,
                sgst=sgst,
                igst=igst,
                **({"po_number": "N/A"} if template_type in ["Goods Receipt Note", "Rejection Slip", "Purchase Invoice", "Credit Note", "Debit Note"] else {}),
                **({"sales_order_number": "N/A"} if template_type == "Sales Invoice" else {}),
                **({"challan_number": doc_number, "delivery_date": voucher_date} if template_type == "Delivery Challan" else {}),
                **({"validity_date": voucher_date} if template_type in ["Quotation", "Proforma Invoice"] else {}),
                **({"payment_terms": "N/A"} if template_type in ["Purchase Order", "Sales Order", "Quotation", "Proforma Invoice"] else {}),
                **({"grn_number": "N/A"} if template_type in ["Purchase Invoice", "Credit Note", "Debit Note", "Rejection Slip"] else {})
            )
            logger.info(f"PDF generated at {file_path}")
            return file_path
        except Exception as e:
            logger.error(f"Failed to generate PDF for {template_type}: {e}")
            return None
        finally:
            session.close()