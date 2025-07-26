from src.erp.logic.utils.document_utils import (
    CustomDocTemplate,
    get_paragraph_styles,
    create_logo,
    create_header_table,
    create_party_table,
    create_items_table,
    create_totals_and_terms_table,
    create_amount_in_words_table,
    create_signatory_table
)
from reportlab.lib.units import mm
from reportlab.platypus import Spacer, Paragraph, Table
from reportlab.lib import colors
from src.erp.logic.utils.utils import number_to_words
import logging

logger = logging.getLogger(__name__)

def generate_po_template(file_path, company_data, vendor_data, voucher_number, voucher_date, items, total_amount, cgst, sgst, igst, payment_terms=None, delivery_date=None, **kwargs):
    try:
        doc = CustomDocTemplate(file_path)
        styles = get_paragraph_styles()
        elements = []
        header_fields = [
            {"label": "Purchase Order No.", "value": voucher_number},
            {"label": "Date", "value": voucher_date},
            {"label": "Delivery Date", "value": delivery_date or "N/A"},
            {"label": "Payment Terms", "value": payment_terms or "N/A"}
        ]
        header_table = create_header_table(company_data, "Purchase Order", header_fields, styles)
        elements.append(header_table)
        elements.append(Spacer(1, 5.29 * mm))
        party_table = create_party_table(vendor_data, "Vendor", company_data, styles)
        elements.append(party_table)
        elements.append(Spacer(1, 5.29 * mm))
        headers = ["S.No.", "Description", "HSN Code", "Qty", "Unit", "Rate", "GST %", "Amount"]
        items_table, col_widths = create_items_table(headers, items, styles)
        elements.append(items_table)
        elements.append(Spacer(1, 5.29 * mm))
        totals = [
            [Paragraph("Total Amount:", styles['small']), Paragraph(f"{total_amount:.2f}", styles['small'])],
            [Paragraph("CGST:", styles['small']), Paragraph(f"{cgst:.2f}", styles['small'])],
            [Paragraph("SGST:", styles['small']), Paragraph(f"{sgst:.2f}", styles['small'])],
            [Paragraph("IGST:", styles['small']), Paragraph(f"{igst:.2f}", styles['small'])]
        ]
        terms = [payment_terms or "N/A"]
        totals_table = create_totals_and_terms_table(totals, terms, styles, col_widths)
        elements.append(totals_table)
        elements.append(Spacer(1, 5.29 * mm))
        amount_words_table = create_amount_in_words_table(total_amount, "Amount in Words", styles, number_to_words)
        elements.append(amount_words_table)
        elements.append(Spacer(1, 5.29 * mm))
        signatory_table = create_signatory_table(company_data[0], styles)
        elements.append(signatory_table)
        doc.elements = elements
        return doc
    except Exception as e:
        logger.error(f"Error generating Purchase Order PDF: {e}")
        raise

def generate_grn_template(file_path, company_data, vendor_data, voucher_number, voucher_date, po_number, items, **kwargs):
    try:
        doc = CustomDocTemplate(file_path)
        styles = get_paragraph_styles()
        elements = []
        header_fields = [
            {"label": "GRN No.", "value": voucher_number},
            {"label": "Date", "value": voucher_date},
            {"label": "PO No.", "value": po_number or "N/A"}
        ]
        header_table = create_header_table(company_data, "Goods Receipt Note", header_fields, styles)
        elements.append(header_table)
        elements.append(Spacer(1, 5.29 * mm))
        party_table = create_party_table(vendor_data, "Vendor", company_data, styles)
        elements.append(party_table)
        elements.append(Spacer(1, 5.29 * mm))
        headers = ["S.No.", "Description", "HSN Code", "Qty", "Unit", "Rate", "GST %", "Amount"]
        items_table, _ = create_items_table(headers, items, styles)
        elements.append(items_table)
        elements.append(Spacer(1, 5.29 * mm))
        signatory_table = create_signatory_table(company_data[0], styles)
        elements.append(signatory_table)
        doc.elements = elements
        return doc
    except Exception as e:
        logger.error(f"Error generating GRN PDF: {e}")
        raise

def generate_rejection_template(file_path, company_data, vendor_data, voucher_number, voucher_date, po_number, items, grn_number=None, **kwargs):
    try:
        doc = CustomDocTemplate(file_path)
        styles = get_paragraph_styles()
        elements = []
        header_fields = [
            {"label": "Rejection Slip No.", "value": voucher_number},
            {"label": "Date", "value": voucher_date},
            {"label": "GRN No.", "value": grn_number or "N/A"},
            {"label": "PO No.", "value": po_number or "N/A"}
        ]
        header_table = create_header_table(company_data, "Rejection Slip", header_fields, styles)
        elements.append(header_table)
        elements.append(Spacer(1, 5.29 * mm))
        party_table = create_party_table(vendor_data, "Vendor", company_data, styles)
        elements.append(party_table)
        elements.append(Spacer(1, 5.29 * mm))
        headers = ["S.No.", "Description", "HSN Code", "Qty", "Unit"]
        items_table, _ = create_items_table(headers, items, styles)
        elements.append(items_table)
        elements.append(Spacer(1, 5.29 * mm))
        signatory_table = create_signatory_table(company_data[0], styles)
        elements.append(signatory_table)
        doc.elements = elements
        return doc
    except Exception as e:
        logger.error(f"Error generating Rejection Slip PDF: {e}")
        raise

def generate_purchase_inv_template(file_path, company_data, vendor_data, voucher_number, voucher_date, grn_number, po_number, items, total_amount, cgst, sgst, igst, voucher_data=None, **kwargs):
    try:
        doc = CustomDocTemplate(file_path)
        styles = get_paragraph_styles()
        elements = []
        header_fields = [
            {"label": "Invoice No.", "value": voucher_number},
            {"label": "Date", "value": voucher_date},
            {"label": "GRN No.", "value": grn_number or "N/A"},
            {"label": "PO No.", "value": po_number or "N/A"}
        ]
        header_table = create_header_table(company_data, "Purchase Invoice", header_fields, styles)
        elements.append(header_table)
        elements.append(Spacer(1, 5.29 * mm))
        party_table = create_party_table(vendor_data, "Vendor", company_data, styles)
        elements.append(party_table)
        elements.append(Spacer(1, 5.29 * mm))
        headers = ["S.No.", "Description", "HSN Code", "Qty", "Unit", "Rate", "GST %", "Amount"]
        items_table, col_widths = create_items_table(headers, items, styles)
        elements.append(items_table)
        elements.append(Spacer(1, 5.29 * mm))
        if voucher_data:
            voucher_items = [[Paragraph(f"{key}:", styles['small']), Paragraph(str(value), styles['small'])] for key, value in voucher_data.items()]
            voucher_col_widths = [82.885 * mm, 82.885 * mm]
            voucher_row_heights = [5.29 * mm] * len(voucher_items)
            voucher_table = Table(voucher_items, colWidths=voucher_col_widths, rowHeights=voucher_row_heights)
            voucher_table.hAlign = 'LEFT'
            voucher_table.setStyle(TableStyle([
                ('VALIGN', (0, 0), (-1, -1), 'MIDDLE'),
                ('ALIGN', (0, 0), (0, -1), 'RIGHT'),
                ('ALIGN', (1, 0), (1, -1), 'LEFT'),
                ('BOX', (0, 0), (-1, -1), 0.5, colors.black),
                ('INNERGRID', (0, 0), (-1, -1), 0.5, colors.black),
            ]))
            elements.append(voucher_table)
            elements.append(Spacer(1, 5.29 * mm))
        totals = [
            [Paragraph("Total Amount:", styles['small']), Paragraph(f"{total_amount:.2f}", styles['small'])],
            [Paragraph("CGST:", styles['small']), Paragraph(f"{cgst:.2f}", styles['small'])],
            [Paragraph("SGST:", styles['small']), Paragraph(f"{sgst:.2f}", styles['small'])],
            [Paragraph("IGST:", styles['small']), Paragraph(f"{igst:.2f}", styles['small'])]
        ]
        terms = ["N/A"]
        totals_table = create_totals_and_terms_table(totals, terms, styles, col_widths)
        elements.append(totals_table)
        elements.append(Spacer(1, 5.29 * mm))
        amount_words_table = create_amount_in_words_table(total_amount, "Amount in Words", styles, number_to_words)
        elements.append(amount_words_table)
        elements.append(Spacer(1, 5.29 * mm))
        signatory_table = create_signatory_table(company_data[0], styles)
        elements.append(signatory_table)
        doc.elements = elements
        return doc
    except Exception as e:
        logger.error(f"Error generating Purchase Invoice PDF: {e}")
        raise

def generate_credit_note_template(file_path, company_data, vendor_data, voucher_number, voucher_date, grn_number, po_number, items, total_amount, cgst, sgst, igst, **kwargs):
    try:
        doc = CustomDocTemplate(file_path)
        styles = get_paragraph_styles()
        elements = []
        header_fields = [
            {"label": "Credit Note No.", "value": voucher_number},
            {"label": "Date", "value": voucher_date},
            {"label": "GRN No.", "value": grn_number or "N/A"},
            {"label": "PO No.", "value": po_number or "N/A"}
        ]
        header_table = create_header_table(company_data, "Credit Note", header_fields, styles)
        elements.append(header_table)
        elements.append(Spacer(1, 5.29 * mm))
        party_table = create_party_table(vendor_data, "Vendor", company_data, styles)
        elements.append(party_table)
        elements.append(Spacer(1, 5.29 * mm))
        headers = ["S.No.", "Description", "HSN Code", "Qty", "Unit", "Rate", "GST %", "Amount"]
        items_table, col_widths = create_items_table(headers, items, styles)
        elements.append(items_table)
        elements.append(Spacer(1, 5.29 * mm))
        totals = [
            [Paragraph("Total Amount:", styles['small']), Paragraph(f"{total_amount:.2f}", styles['small'])],
            [Paragraph("CGST:", styles['small']), Paragraph(f"{cgst:.2f}", styles['small'])],
            [Paragraph("SGST:", styles['small']), Paragraph(f"{sgst:.2f}", styles['small'])],
            [Paragraph("IGST:", styles['small']), Paragraph(f"{igst:.2f}", styles['small'])]
        ]
        terms = ["N/A"]
        totals_table = create_totals_and_terms_table(totals, terms, styles, col_widths)
        elements.append(totals_table)
        elements.append(Spacer(1, 5.29 * mm))
        amount_words_table = create_amount_in_words_table(total_amount, "Amount in Words", styles, number_to_words)
        elements.append(amount_words_table)
        elements.append(Spacer(1, 5.29 * mm))
        signatory_table = create_signatory_table(company_data[0], styles)
        elements.append(signatory_table)
        doc.elements = elements
        return doc
    except Exception as e:
        logger.error(f"Error generating Credit Note PDF: {e}")
        raise

def generate_material_out_template(file_path, company_data, customer_data, voucher_number, voucher_date, items, **kwargs):
    try:
        doc = CustomDocTemplate(file_path)
        styles = get_paragraph_styles()
        elements = []
        header_fields = [
            {"label": "Material Out No.", "value": voucher_number},
            {"label": "Date", "value": voucher_date}
        ]
        header_table = create_header_table(company_data, "Material Out", header_fields, styles)
        elements.append(header_table)
        elements.append(Spacer(1, 5.29 * mm))
        party_table = create_party_table(customer_data, "Customer", company_data, styles)
        elements.append(party_table)
        elements.append(Spacer(1, 5.29 * mm))
        headers = ["S.No.", "Description", "HSN Code", "Qty", "Unit"]
        items_table, _ = create_items_table(headers, items, styles)
        elements.append(items_table)
        elements.append(Spacer(1, 5.29 * mm))
        signatory_table = create_signatory_table(company_data[0], styles)
        elements.append(signatory_table)
        doc.elements = elements
        return doc
    except Exception as e:
        logger.error(f"Error generating Material Out PDF: {e}")
        raise

def generate_quotation_template(file_path, company_data, customer_data, voucher_number, voucher_date, validity_date, items, total_amount, cgst, sgst, igst, payment_terms=None, **kwargs):
    try:
        doc = CustomDocTemplate(file_path)
        styles = get_paragraph_styles()
        elements = []
        header_fields = [
            {"label": "Quotation No.", "value": voucher_number},
            {"label": "Date", "value": voucher_date},
            {"label": "Validity Date", "value": validity_date or "N/A"}
        ]
        header_table = create_header_table(company_data, "Quotation", header_fields, styles)
        elements.append(header_table)
        elements.append(Spacer(1, 5.29 * mm))
        party_table = create_party_table(customer_data, "Customer", company_data, styles)
        elements.append(party_table)
        elements.append(Spacer(1, 5.29 * mm))
        headers = ["S.No.", "Description", "HSN Code", "Qty", "Unit", "Rate", "GST %", "Amount"]
        items_table, col_widths = create_items_table(headers, items, styles)
        elements.append(items_table)
        elements.append(Spacer(1, 5.29 * mm))
        totals = [
            [Paragraph("Total Amount:", styles['small']), Paragraph(f"{total_amount:.2f}", styles['small'])],
            [Paragraph("CGST:", styles['small']), Paragraph(f"{cgst:.2f}", styles['small'])],
            [Paragraph("SGST:", styles['small']), Paragraph(f"{sgst:.2f}", styles['small'])],
            [Paragraph("IGST:", styles['small']), Paragraph(f"{igst:.2f}", styles['small'])]
        ]
        terms = [payment_terms or "N/A"]
        totals_table = create_totals_and_terms_table(totals, terms, styles, col_widths)
        elements.append(totals_table)
        elements.append(Spacer(1, 5.29 * mm))
        amount_words_table = create_amount_in_words_table(total_amount, "Amount in Words", styles, number_to_words)
        elements.append(amount_words_table)
        elements.append(Spacer(1, 5.29 * mm))
        signatory_table = create_signatory_table(company_data[0], styles)
        elements.append(signatory_table)
        doc.elements = elements
        return doc
    except Exception as e:
        logger.error(f"Error generating Quotation PDF: {e}")
        raise

def generate_sales_order_template(file_path, company_data, customer_data, voucher_number, voucher_date, delivery_date, items, total_amount, cgst, sgst, igst, payment_terms=None, **kwargs):
    try:
        doc = CustomDocTemplate(file_path)
        styles = get_paragraph_styles()
        elements = []
        header_fields = [
            {"label": "Sales Order No.", "value": voucher_number},
            {"label": "Date", "value": voucher_date},
            {"label": "Delivery Date", "value": delivery_date or "N/A"},
            {"label": "Payment Terms", "value": payment_terms or "N/A"}
        ]
        header_table = create_header_table(company_data, "Sales Order", header_fields, styles)
        elements.append(header_table)
        elements.append(Spacer(1, 5.29 * mm))
        party_table = create_party_table(customer_data, "Customer", company_data, styles)
        elements.append(party_table)
        elements.append(Spacer(1, 5.29 * mm))
        headers = ["S.No.", "Description", "HSN Code", "Qty", "Unit", "Rate", "GST %", "Amount"]
        items_table, col_widths = create_items_table(headers, items, styles)
        elements.append(items_table)
        elements.append(Spacer(1, 5.29 * mm))
        totals = [
            [Paragraph("Total Amount:", styles['small']), Paragraph(f"{total_amount:.2f}", styles['small'])],
            [Paragraph("CGST:", styles['small']), Paragraph(f"{cgst:.2f}", styles['small'])],
            [Paragraph("SGST:", styles['small']), Paragraph(f"{sgst:.2f}", styles['small'])],
            [Paragraph("IGST:", styles['small']), Paragraph(f"{igst:.2f}", styles['small'])]
        ]
        terms = [payment_terms or "N/A"]
        totals_table = create_totals_and_terms_table(totals, terms, styles, col_widths)
        elements.append(totals_table)
        elements.append(Spacer(1, 5.29 * mm))
        amount_words_table = create_amount_in_words_table(total_amount, "Amount in Words", styles, number_to_words)
        elements.append(amount_words_table)
        elements.append(Spacer(1, 5.29 * mm))
        signatory_table = create_signatory_table(company_data[0], styles)
        elements.append(signatory_table)
        doc.elements = elements
        return doc
    except Exception as e:
        logger.error(f"Error generating Sales Order PDF: {e}")
        raise

def generate_proforma_invoice_template(file_path, company_data, customer_data, voucher_number, voucher_date, validity_date, items, total_amount, cgst, sgst, igst, payment_terms=None, **kwargs):
    try:
        doc = CustomDocTemplate(file_path)
        styles = get_paragraph_styles()
        elements = []
        header_fields = [
            {"label": "Proforma Invoice No.", "value": voucher_number},
            {"label": "Date", "value": voucher_date},
            {"label": "Validity Date", "value": validity_date or "N/A"}
        ]
        header_table = create_header_table(company_data, "Proforma Invoice", header_fields, styles)
        elements.append(header_table)
        elements.append(Spacer(1, 5.29 * mm))
        party_table = create_party_table(customer_data, "Customer", company_data, styles)
        elements.append(party_table)
        elements.append(Spacer(1, 5.29 * mm))
        headers = ["S.No.", "Description", "HSN Code", "Qty", "Unit", "Rate", "GST %", "Amount"]
        items_table, col_widths = create_items_table(headers, items, styles)
        elements.append(items_table)
        elements.append(Spacer(1, 5.29 * mm))
        totals = [
            [Paragraph("Total Amount:", styles['small']), Paragraph(f"{total_amount:.2f}", styles['small'])],
            [Paragraph("CGST:", styles['small']), Paragraph(f"{cgst:.2f}", styles['small'])],
            [Paragraph("SGST:", styles['small']), Paragraph(f"{sgst:.2f}", styles['small'])],
            [Paragraph("IGST:", styles['small']), Paragraph(f"{igst:.2f}", styles['small'])]
        ]
        terms = [payment_terms or "N/A"]
        totals_table = create_totals_and_terms_table(totals, terms, styles, col_widths)
        elements.append(totals_table)
        elements.append(Spacer(1, 5.29 * mm))
        amount_words_table = create_amount_in_words_table(total_amount, "Amount in Words", styles, number_to_words)
        elements.append(amount_words_table)
        elements.append(Spacer(1, 5.29 * mm))
        signatory_table = create_signatory_table(company_data[0], styles)
        elements.append(signatory_table)
        doc.elements = elements
        return doc
    except Exception as e:
        logger.error(f"Error generating Proforma Invoice PDF: {e}")
        raise

def generate_sales_inv_template(file_path, company_data, customer_data, voucher_number, voucher_date, sales_order_number, items, total_amount, cgst, sgst, igst, voucher_data=None, **kwargs):
    try:
        doc = CustomDocTemplate(file_path)
        styles = get_paragraph_styles()
        elements = []
        header_fields = [
            {"label": "Invoice No.", "value": voucher_number},
            {"label": "Date", "value": voucher_date},
            {"label": "Sales Order No.", "value": sales_order_number or "N/A"}
        ]
        header_table = create_header_table(company_data, "Sales Invoice", header_fields, styles)
        elements.append(header_table)
        elements.append(Spacer(1, 5.29 * mm))
        party_table = create_party_table(customer_data, "Customer", company_data, styles)
        elements.append(party_table)
        elements.append(Spacer(1, 5.29 * mm))
        headers = ["S.No.", "Description", "HSN Code", "Qty", "Unit", "Rate", "GST %", "Amount"]
        items_table, col_widths = create_items_table(headers, items, styles)
        elements.append(items_table)
        elements.append(Spacer(1, 5.29 * mm))
        if voucher_data:
            voucher_items = [[Paragraph(f"{key}:", styles['small']), Paragraph(str(value), styles['small'])] for key, value in voucher_data.items()]
            voucher_col_widths = [82.885 * mm, 82.885 * mm]
            voucher_row_heights = [5.29 * mm] * len(voucher_items)
            voucher_table = Table(voucher_items, colWidths=voucher_col_widths, rowHeights=voucher_row_heights)
            voucher_table.hAlign = 'LEFT'
            voucher_table.setStyle(TableStyle([
                ('VALIGN', (0, 0), (-1, -1), 'MIDDLE'),
                ('ALIGN', (0, 0), (0, -1), 'RIGHT'),
                ('ALIGN', (1, 0), (1, -1), 'LEFT'),
                ('BOX', (0, 0), (-1, -1), 0.5, colors.black),
                ('INNERGRID', (0, 0), (-1, -1), 0.5, colors.black),
            ]))
            elements.append(voucher_table)
            elements.append(Spacer(1, 5.29 * mm))
        totals = [
            [Paragraph("Total Amount:", styles['small']), Paragraph(f"{total_amount:.2f}", styles['small'])],
            [Paragraph("CGST:", styles['small']), Paragraph(f"{cgst:.2f}", styles['small'])],
            [Paragraph("SGST:", styles['small']), Paragraph(f"{sgst:.2f}", styles['small'])],
            [Paragraph("IGST:", styles['small']), Paragraph(f"{igst:.2f}", styles['small'])]
        ]
        terms = ["N/A"]
        totals_table = create_totals_and_terms_table(totals, terms, styles, col_widths)
        elements.append(totals_table)
        elements.append(Spacer(1, 5.29 * mm))
        amount_words_table = create_amount_in_words_table(total_amount, "Amount in Words", styles, number_to_words)
        elements.append(amount_words_table)
        elements.append(Spacer(1, 5.29 * mm))
        signatory_table = create_signatory_table(company_data[0], styles)
        elements.append(signatory_table)
        doc.elements = elements
        return doc
    except Exception as e:
        logger.error(f"Error generating Sales Invoice PDF: {e}")
        raise

def generate_delivery_challan_template(file_path, company_data, customer_data, voucher_number, voucher_date, delivery_date, challan_number, items, total_amount, cgst, sgst, igst, **kwargs):
    try:
        doc = CustomDocTemplate(file_path)
        styles = get_paragraph_styles()
        elements = []
        header_fields = [
            {"label": "Challan No.", "value": challan_number},
            {"label": "Date", "value": voucher_date},
            {"label": "Delivery Date", "value": delivery_date or "N/A"}
        ]
        header_table = create_header_table(company_data, "Delivery Challan", header_fields, styles)
        elements.append(header_table)
        elements.append(Spacer(1, 5.29 * mm))
        party_table = create_party_table(customer_data, "Customer", company_data, styles)
        elements.append(party_table)
        elements.append(Spacer(1, 5.29 * mm))
        headers = ["S.No.", "Description", "HSN Code", "Qty", "Unit", "Rate", "GST %", "Amount"]
        items_table, col_widths = create_items_table(headers, items, styles)
        elements.append(items_table)
        elements.append(Spacer(1, 5.29 * mm))
        totals = [
            [Paragraph("Total Amount:", styles['small']), Paragraph(f"{total_amount:.2f}", styles['small'])],
            [Paragraph("CGST:", styles['small']), Paragraph(f"{cgst:.2f}", styles['small'])],
            [Paragraph("SGST:", styles['small']), Paragraph(f"{sgst:.2f}", styles['small'])],
            [Paragraph("IGST:", styles['small']), Paragraph(f"{igst:.2f}", styles['small'])]
        ]
        terms = ["N/A"]
        totals_table = create_totals_and_terms_table(totals, terms, styles, col_widths)
        elements.append(totals_table)
        elements.append(Spacer(1, 5.29 * mm))
        amount_words_table = create_amount_in_words_table(total_amount, "Amount in Words", styles, number_to_words)
        elements.append(amount_words_table)
        elements.append(Spacer(1, 5.29 * mm))
        signatory_table = create_signatory_table(company_data[0], styles)
        elements.append(signatory_table)
        doc.elements = elements
        return doc
    except Exception as e:
        logger.error(f"Error generating Delivery Challan PDF: {e}")
        raise

def generate_debit_note_template(file_path, company_data, vendor_data, voucher_number, voucher_date, grn_number, po_number, items, total_amount, cgst, sgst, igst, voucher_data=None, **kwargs):
    try:
        doc = CustomDocTemplate(file_path)
        styles = get_paragraph_styles()
        elements = []
        header_fields = [
            {"label": "Debit Note No.", "value": voucher_number},
            {"label": "Date", "value": voucher_date},
            {"label": "GRN No.", "value": grn_number or "N/A"},
            {"label": "PO No.", "value": po_number or "N/A"}
        ]
        header_table = create_header_table(company_data, "Debit Note", header_fields, styles)
        elements.append(header_table)
        elements.append(Spacer(1, 5.29 * mm))
        party_table = create_party_table(vendor_data, "Vendor", company_data, styles)
        elements.append(party_table)
        elements.append(Spacer(1, 5.29 * mm))
        headers = ["S.No.", "Description", "HSN Code", "Qty", "Unit", "Rate", "GST %", "Amount"]
        items_table, col_widths = create_items_table(headers, items, styles)
        elements.append(items_table)
        elements.append(Spacer(1, 5.29 * mm))
        if voucher_data:
            voucher_items = [[Paragraph(f"{key}:", styles['small']), Paragraph(str(value), styles['small'])] for key, value in voucher_data.items()]
            voucher_col_widths = [82.885 * mm, 82.885 * mm]
            voucher_row_heights = [5.29 * mm] * len(voucher_items)
            voucher_table = Table(voucher_items, colWidths=voucher_col_widths, rowHeights=voucher_row_heights)
            voucher_table.hAlign = 'LEFT'
            voucher_table.setStyle(TableStyle([
                ('VALIGN', (0, 0), (-1, -1), 'MIDDLE'),
                ('ALIGN', (0, 0), (0, -1), 'RIGHT'),
                ('ALIGN', (1, 0), (1, -1), 'LEFT'),
                ('BOX', (0, 0), (-1, -1), 0.5, colors.black),
                ('INNERGRID', (0, 0), (-1, -1), 0.5, colors.black),
            ]))
            elements.append(voucher_table)
            elements.append(Spacer(1, 5.29 * mm))
        totals = [
            [Paragraph("Total Amount:", styles['small']), Paragraph(f"{total_amount:.2f}", styles['small'])],
            [Paragraph("CGST:", styles['small']), Paragraph(f"{cgst:.2f}", styles['small'])],
            [Paragraph("SGST:", styles['small']), Paragraph(f"{sgst:.2f}", styles['small'])],
            [Paragraph("IGST:", styles['small']), Paragraph(f"{igst:.2f}", styles['small'])]
        ]
        terms = ["N/A"]
        totals_table = create_totals_and_terms_table(totals, terms, styles, col_widths)
        elements.append(totals_table)
        elements.append(Spacer(1, 5.29 * mm))
        amount_words_table = create_amount_in_words_table(total_amount, "Amount in Words", styles, number_to_words)
        elements.append(amount_words_table)
        elements.append(Spacer(1, 5.29 * mm))
        signatory_table = create_signatory_table(company_data[0], styles)
        elements.append(signatory_table)
        doc.elements = elements
        return doc
    except Exception as e:
        logger.error(f"Error generating Debit Note PDF: {e}")
        raise

def generate_non_sales_credit_note_template(file_path, company_data, customer_data, voucher_number, voucher_date, items, total_amount, cgst, sgst, igst, voucher_data=None, **kwargs):
    try:
        doc = CustomDocTemplate(file_path)
        styles = get_paragraph_styles()
        elements = []
        header_fields = [
            {"label": "Non-Sales Credit Note No.", "value": voucher_number},
            {"label": "Date", "value": voucher_date}
        ]
        header_table = create_header_table(company_data, "Non-Sales Credit Note", header_fields, styles)
        elements.append(header_table)
        elements.append(Spacer(1, 5.29 * mm))
        party_table = create_party_table(customer_data, "Customer", company_data, styles)
        elements.append(party_table)
        elements.append(Spacer(1, 5.29 * mm))
        headers = ["S.No.", "Description", "HSN Code", "Qty", "Unit", "Rate", "GST %", "Amount"]
        items_table, col_widths = create_items_table(headers, items, styles)
        elements.append(items_table)
        elements.append(Spacer(1, 5.29 * mm))
        if voucher_data:
            voucher_items = [[Paragraph(f"{key}:", styles['small']), Paragraph(str(value), styles['small'])] for key, value in voucher_data.items()]
            voucher_col_widths = [82.885 * mm, 82.885 * mm]
            voucher_row_heights = [5.29 * mm] * len(voucher_items)
            voucher_table = Table(voucher_items, colWidths=voucher_col_widths, rowHeights=voucher_row_heights)
            voucher_table.hAlign = 'LEFT'
            voucher_table.setStyle(TableStyle([
                ('VALIGN', (0, 0), (-1, -1), 'MIDDLE'),
                ('ALIGN', (0, 0), (0, -1), 'RIGHT'),
                ('ALIGN', (1, 0), (1, -1), 'LEFT'),
                ('BOX', (0, 0), (-1, -1), 0.5, colors.black),
                ('INNERGRID', (0, 0), (-1, -1), 0.5, colors.black),
            ]))
            elements.append(voucher_table)
            elements.append(Spacer(1, 5.29 * mm))
        totals = [
            [Paragraph("Total Amount:", styles['small']), Paragraph(f"{total_amount:.2f}", styles['small'])],
            [Paragraph("CGST:", styles['small']), Paragraph(f"{cgst:.2f}", styles['small'])],
            [Paragraph("SGST:", styles['small']), Paragraph(f"{sgst:.2f}", styles['small'])],
            [Paragraph("IGST:", styles['small']), Paragraph(f"{igst:.2f}", styles['small'])]
        ]
        terms = ["N/A"]
        totals_table = create_totals_and_terms_table(totals, terms, styles, col_widths)
        elements.append(totals_table)
        elements.append(Spacer(1, 5.29 * mm))
        amount_words_table = create_amount_in_words_table(total_amount, "Amount in Words", styles, number_to_words)
        elements.append(amount_words_table)
        elements.append(Spacer(1, 5.29 * mm))
        signatory_table = create_signatory_table(company_data[0], styles)
        elements.append(signatory_table)
        doc.elements = elements
        return doc
    except Exception as e:
        logger.error(f"Error generating Non-Sales Credit Note PDF: {e}")
        raise

def generate_payment_voucher_template(file_path, company_data, vendor_data, voucher_number, voucher_date, items, total_amount, cgst, sgst, igst, voucher_data=None, **kwargs):
    try:
        doc = CustomDocTemplate(file_path)
        styles = get_paragraph_styles()
        elements = []
        header_fields = [
            {"label": "Payment Voucher No.", "value": voucher_number},
            {"label": "Date", "value": voucher_date}
        ]
        header_table = create_header_table(company_data, "Payment Voucher", header_fields, styles)
        elements.append(header_table)
        elements.append(Spacer(1, 5.29 * mm))
        party_table = create_party_table(vendor_data, "Payee", company_data, styles)
        elements.append(party_table)
        elements.append(Spacer(1, 5.29 * mm))
        headers = ["S.No.", "Description", "Amount"]
        items_table, col_widths = create_items_table(headers, items, styles)
        elements.append(items_table)
        elements.append(Spacer(1, 5.29 * mm))
        if voucher_data:
            voucher_items = [[Paragraph(f"{key}:", styles['small']), Paragraph(str(value), styles['small'])] for key, value in voucher_data.items()]
            voucher_col_widths = [82.885 * mm, 82.885 * mm]
            voucher_row_heights = [5.29 * mm] * len(voucher_items)
            voucher_table = Table(voucher_items, colWidths=voucher_col_widths, rowHeights=voucher_row_heights)
            voucher_table.hAlign = 'LEFT'
            voucher_table.setStyle(TableStyle([
                ('VALIGN', (0, 0), (-1, -1), 'MIDDLE'),
                ('ALIGN', (0, 0), (0, -1), 'RIGHT'),
                ('ALIGN', (1, 0), (1, -1), 'LEFT'),
                ('BOX', (0, 0), (-1, -1), 0.5, colors.black),
                ('INNERGRID', (0, 0), (-1, -1), 0.5, colors.black),
            ]))
            elements.append(voucher_table)
            elements.append(Spacer(1, 5.29 * mm))
        totals = [
            [Paragraph("Total Amount:", styles['small']), Paragraph(f"{total_amount:.2f}", styles['small'])],
            [Paragraph("CGST:", styles['small']), Paragraph(f"{cgst:.2f}", styles['small'])],
            [Paragraph("SGST:", styles['small']), Paragraph(f"{sgst:.2f}", styles['small'])],
            [Paragraph("IGST:", styles['small']), Paragraph(f"{igst:.2f}", styles['small'])]
        ]
        terms = ["N/A"]
        totals_table = create_totals_and_terms_table(totals, terms, styles, col_widths)
        elements.append(totals_table)
        elements.append(Spacer(1, 5.29 * mm))
        amount_words_table = create_amount_in_words_table(total_amount, "Amount in Words", styles, number_to_words)
        elements.append(amount_words_table)
        elements.append(Spacer(1, 5.29 * mm))
        signatory_table = create_signatory_table(company_data[0], styles)
        elements.append(signatory_table)
        doc.elements = elements
        return doc
    except Exception as e:
        logger.error(f"Error generating Payment Voucher PDF: {e}")
        raise

def generate_receipt_voucher_template(file_path, company_data, customer_data, voucher_number, voucher_date, items, total_amount, cgst, sgst, igst, voucher_data=None, **kwargs):
    try:
        doc = CustomDocTemplate(file_path)
        styles = get_paragraph_styles()
        elements = []
        header_fields = [
            {"label": "Receipt Voucher No.", "value": voucher_number},
            {"label": "Date", "value": voucher_date}
        ]
        header_table = create_header_table(company_data, "Receipt Voucher", header_fields, styles)
        elements.append(header_table)
        elements.append(Spacer(1, 5.29 * mm))
        party_table = create_party_table(customer_data, "Received From", company_data, styles)
        elements.append(party_table)
        elements.append(Spacer(1, 5.29 * mm))
        headers = ["S.No.", "Description", "Amount"]
        items_table, col_widths = create_items_table(headers, items, styles)
        elements.append(items_table)
        elements.append(Spacer(1, 5.29 * mm))
        if voucher_data:
            voucher_items = [[Paragraph(f"{key}:", styles['small']), Paragraph(str(value), styles['small'])] for key, value in voucher_data.items()]
            voucher_col_widths = [82.885 * mm, 82.885 * mm]
            voucher_row_heights = [5.29 * mm] * len(voucher_items)
            voucher_table = Table(voucher_items, colWidths=voucher_col_widths, rowHeights=voucher_row_heights)
            voucher_table.hAlign = 'LEFT'
            voucher_table.setStyle(TableStyle([
                ('VALIGN', (0, 0), (-1, -1), 'MIDDLE'),
                ('ALIGN', (0, 0), (0, -1), 'RIGHT'),
                ('ALIGN', (1, 0), (1, -1), 'LEFT'),
                ('BOX', (0, 0), (-1, -1), 0.5, colors.black),
                ('INNERGRID', (0, 0), (-1, -1), 0.5, colors.black),
            ]))
            elements.append(voucher_table)
            elements.append(Spacer(1, 5.29 * mm))
        totals = [
            [Paragraph("Total Amount:", styles['small']), Paragraph(f"{total_amount:.2f}", styles['small'])],
            [Paragraph("CGST:", styles['small']), Paragraph(f"{cgst:.2f}", styles['small'])],
            [Paragraph("SGST:", styles['small']), Paragraph(f"{sgst:.2f}", styles['small'])],
            [Paragraph("IGST:", styles['small']), Paragraph(f"{igst:.2f}", styles['small'])]
        ]
        terms = ["N/A"]
        totals_table = create_totals_and_terms_table(totals, terms, styles, col_widths)
        elements.append(totals_table)
        elements.append(Spacer(1, 5.29 * mm))
        amount_words_table = create_amount_in_words_table(total_amount, "Amount in Words", styles, number_to_words)
        elements.append(amount_words_table)
        elements.append(Spacer(1, 5.29 * mm))
        signatory_table = create_signatory_table(company_data[0], styles)
        elements.append(signatory_table)
        doc.elements = elements
        return doc
    except Exception as e:
        logger.error(f"Error generating Receipt Voucher PDF: {e}")
        raise

def generate_contra_voucher_template(file_path, company_data, vendor_data, voucher_number, voucher_date, items, total_amount, cgst, sgst, igst, voucher_data=None, **kwargs):
    try:
        doc = CustomDocTemplate(file_path)
        styles = get_paragraph_styles()
        elements = []
        header_fields = [
            {"label": "Contra Voucher No.", "value": voucher_number},
            {"label": "Date", "value": voucher_date}
        ]
        header_table = create_header_table(company_data, "Contra Voucher", header_fields, styles)
        elements.append(header_table)
        elements.append(Spacer(1, 5.29 * mm))
        party_table = create_party_table(vendor_data, "Party", company_data, styles)
        elements.append(party_table)
        elements.append(Spacer(1, 5.29 * mm))
        headers = ["S.No.", "Description", "Amount"]
        items_table, col_widths = create_items_table(headers, items, styles)
        elements.append(items_table)
        elements.append(Spacer(1, 5.29 * mm))
        if voucher_data:
            voucher_items = [[Paragraph(f"{key}:", styles['small']), Paragraph(str(value), styles['small'])] for key, value in voucher_data.items()]
            voucher_col_widths = [82.885 * mm, 82.885 * mm]
            voucher_row_heights = [5.29 * mm] * len(voucher_items)
            voucher_table = Table(voucher_items, colWidths=voucher_col_widths, rowHeights=voucher_row_heights)
            voucher_table.hAlign = 'LEFT'
            voucher_table.setStyle(TableStyle([
                ('VALIGN', (0, 0), (-1, -1), 'MIDDLE'),
                ('ALIGN', (0, 0), (0, -1), 'RIGHT'),
                ('ALIGN', (1, 0), (1, -1), 'LEFT'),
                ('BOX', (0, 0), (-1, -1), 0.5, colors.black),
                ('INNERGRID', (0, 0), (-1, -1), 0.5, colors.black),
            ]))
            elements.append(voucher_table)
            elements.append(Spacer(1, 5.29 * mm))
        totals = [
            [Paragraph("Total Amount:", styles['small']), Paragraph(f"{total_amount:.2f}", styles['small'])],
            [Paragraph("CGST:", styles['small']), Paragraph(f"{cgst:.2f}", styles['small'])],
            [Paragraph("SGST:", styles['small']), Paragraph(f"{sgst:.2f}", styles['small'])],
            [Paragraph("IGST:", styles['small']), Paragraph(f"{igst:.2f}", styles['small'])]
        ]
        terms = ["N/A"]
        totals_table = create_totals_and_terms_table(totals, terms, styles, col_widths)
        elements.append(totals_table)
        elements.append(Spacer(1, 5.29 * mm))
        amount_words_table = create_amount_in_words_table(total_amount, "Amount in Words", styles, number_to_words)
        elements.append(amount_words_table)
        elements.append(Spacer(1, 5.29 * mm))
        signatory_table = create_signatory_table(company_data[0], styles)
        elements.append(signatory_table)
        doc.elements = elements
        return doc
    except Exception as e:
        logger.error(f"Error generating Contra Voucher PDF: {e}")
        raise

def generate_journal_voucher_template(file_path, company_data, party_data, voucher_number, voucher_date, items, total_amount, cgst, sgst, igst, voucher_data=None, **kwargs):
    try:
        doc = CustomDocTemplate(file_path)
        styles = get_paragraph_styles()
        elements = []
        header_fields = [
            {"label": "Journal Voucher No.", "value": voucher_number},
            {"label": "Date", "value": voucher_date}
        ]
        header_table = create_header_table(company_data, "Journal Voucher", header_fields, styles)
        elements.append(header_table)
        elements.append(Spacer(1, 5.29 * mm))
        party_table = create_party_table(party_data, "Party", company_data, styles)
        elements.append(party_table)
        elements.append(Spacer(1, 5.29 * mm))
        headers = ["S.No.", "Account", "Description", "Debit", "Credit"]
        items_table, col_widths = create_items_table(headers, items, styles)
        elements.append(items_table)
        elements.append(Spacer(1, 5.29 * mm))
        if voucher_data:
            voucher_items = [[Paragraph(f"{key}:", styles['small']), Paragraph(str(value), styles['small'])] for key, value in voucher_data.items()]
            voucher_col_widths = [82.885 * mm, 82.885 * mm]
            voucher_row_heights = [5.29 * mm] * len(voucher_items)
            voucher_table = Table(voucher_items, colWidths=voucher_col_widths, rowHeights=voucher_row_heights)
            voucher_table.hAlign = 'LEFT'
            voucher_table.setStyle(TableStyle([
                ('VALIGN', (0, 0), (-1, -1), 'MIDDLE'),
                ('ALIGN', (0, 0), (0, -1), 'RIGHT'),
                ('ALIGN', (1, 0), (1, -1), 'LEFT'),
                ('BOX', (0, 0), (-1, -1), 0.5, colors.black),
                ('INNERGRID', (0, 0), (-1, -1), 0.5, colors.black),
            ]))
            elements.append(voucher_table)
            elements.append(Spacer(1, 5.29 * mm))
        totals = [
            [Paragraph("Total Amount:", styles['small']), Paragraph(f"{total_amount:.2f}", styles['small'])],
            [Paragraph("CGST:", styles['small']), Paragraph(f"{cgst:.2f}", styles['small'])],
            [Paragraph("SGST:", styles['small']), Paragraph(f"{sgst:.2f}", styles['small'])],
            [Paragraph("IGST:", styles['small']), Paragraph(f"{igst:.2f}", styles['small'])]
        ]
        terms = ["N/A"]
        totals_table = create_totals_and_terms_table(totals, terms, styles, col_widths)
        elements.append(totals_table)
        elements.append(Spacer(1, 5.29 * mm))
        amount_words_table = create_amount_in_words_table(total_amount, "Amount in Words", styles, number_to_words)
        elements.append(amount_words_table)
        elements.append(Spacer(1, 5.29 * mm))
        signatory_table = create_signatory_table(company_data[0], styles)
        elements.append(signatory_table)
        doc.elements = elements
        return doc
    except Exception as e:
        logger.error(f"Error generating Journal Voucher PDF: {e}")
        raise