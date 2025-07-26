import logging
import os
from datetime import datetime
from PIL import Image as PILImage
from reportlab.lib import colors
from reportlab.lib.pagesizes import A4
from reportlab.lib.units import mm
from reportlab.platypus import SimpleDocTemplate, Table, TableStyle, Paragraph, Image, Spacer
from reportlab.lib.styles import ParagraphStyle
from src.core.config import get_log_path, get_static_path

logger = logging.getLogger(__name__)

if not logging.getLogger().handlers:
    logging.basicConfig(filename=get_log_path(), level=logging.DEBUG, format='%(asctime)s - %(name)s - %(levelname)s - %(message)s')

class CustomDocTemplate(SimpleDocTemplate):
    def afterPage(self):
        self.canv.saveState()
        self.canv.setLineWidth(1)
        self.canv.setStrokeColor(colors.black)
        self.canv.rect(25*mm, 15*mm, 170*mm, 267*mm, fill=0)
        self.canv.restoreState()

def get_paragraph_styles():
    return {
        'normal': ParagraphStyle(name='Normal', fontName='Helvetica', fontSize=12, alignment=1, leading=14),
        'company_name': ParagraphStyle(name='CompanyName', fontName='Helvetica-Bold', fontSize=20, alignment=1, leading=22),
        'small': ParagraphStyle(name='Small', fontName='Helvetica', fontSize=10, alignment=0, leading=12),
        'header': ParagraphStyle(name='Header', fontName='Helvetica-Bold', fontSize=10, alignment=0, leading=12),
        'title': ParagraphStyle(name='Title', fontName='Helvetica-Bold', fontSize=16, alignment=1, leading=18)
    }

def estimate_text_width(text, font_name, font_size):
    try:
        char_width = font_size * 0.5 / mm
        return len(str(text)) * char_width
    except Exception as e:
        logger.error(f"Error estimating text width: {e}")
        return 10 * mm

def create_logo(logo_path, max_width=34.4425*mm-2*mm, max_height=34.93*mm, style=None):
    if not style:
        style = get_paragraph_styles()['normal']
    logo = Paragraph("[Logo Placeholder]", style)
    logo_path = get_static_path("tritiq.png") if logo_path is None else logo_path
    if logo_path and os.path.exists(logo_path):
        try:
            img = PILImage.open(logo_path)
            img_width, img_height = img.size
            aspect = img_height / img_width if img_width else 1
            logo_width = min(max_width, img_width)
            logo_height = logo_width * aspect
            if logo_height > max_height:
                logo_height = max_height
                logo_width = logo_height / aspect
            logo = Image(logo_path, width=logo_width, height=logo_height)
            logo.hAlign = 'CENTER'
            logger.debug(f"Logo loaded: {logo_path}, size: {logo_width}x{logo_height}mm")
        except Exception as e:
            logger.warning(f"Failed to load logo from {logo_path}: {e}")
    else:
        logger.warning(f"Logo path {logo_path} does not exist")
    return logo

def create_header_table(company_data, document_title, fields, styles):
    logo = create_logo(company_data[9] if len(company_data) > 9 else None, style=styles['normal'])
    header_data = [
        [logo, Paragraph(company_data[0] or "[Company Name]", styles['company_name']), '', ''],
        [Paragraph("", styles['normal']), Paragraph(f"{company_data[1] or '[Address Line 1]'}, {company_data[2] or '[Address Line 2]'}", styles['normal']), '', ''],
        [Paragraph("", styles['normal']), Paragraph(f"{company_data[3] or '[City]'}, {company_data[4] or '[State]'} - {company_data[5] or '[Pin Code]'}", styles['normal']), '', ''],
        [Paragraph("", styles['normal']), Paragraph(f"GST No.: {company_data[6] or '[GST No]'}", styles['normal']), '', ''],
        [Paragraph("", styles['normal']), Paragraph(f"Contact: {company_data[7] or '[Contact No]'} | Email: {company_data[8] or '[Email]'}", styles['normal']), '', ''],
        [Paragraph(document_title, styles['title']), '', '', '']
    ]
    for field in fields:
        row = [Paragraph(field['label'], styles['small']), Paragraph(str(field['value']), styles['small'])]
        if 'label2' in field:
            row.extend([Paragraph(field['label2'], styles['small']), Paragraph(str(field['value2']), styles['small'])])
        else:
            row.extend(['', ''])
        header_data.append(row)
    
    col_widths = [34.4425 * mm, 30.744 * mm, 50.29175 * mm, 50.29175 * mm]
    row_heights = [16 * mm, 5.29 * mm, 5.29 * mm, 5.29 * mm, 5.29 * mm, 12.17 * mm] + [5.29 * mm] * len(fields)
    header_table = Table(header_data, colWidths=col_widths, rowHeights=row_heights)
    header_table.hAlign = 'LEFT'
    header_table.setStyle(TableStyle([
        ('VALIGN', (0, 0), (-1, -1), 'MIDDLE'),
        ('ALIGN', (0, 0), (-1, -1), 'CENTER'),
        ('BOX', (0, 0), (-1, -1), 0.5, colors.black),
        ('INNERGRID', (0, 0), (-1, -1), 0.5, colors.black),
        ('SPAN', (1, 0), (3, 0)),
        ('SPAN', (1, 1), (3, 1)),
        ('SPAN', (1, 2), (3, 2)),
        ('SPAN', (1, 3), (3, 3)),
        ('SPAN', (1, 4), (3, 4)),
        ('SPAN', (0, 5), (3, 5)),
        ('ALIGN', (0, 6), (0, -1), 'RIGHT'),
        ('ALIGN', (1, 6), (1, -1), 'LEFT'),
        ('ALIGN', (2, 6), (2, -1), 'RIGHT'),
        ('ALIGN', (3, 6), (3, -1), 'LEFT'),
    ]))
    return header_table

def create_party_table(party_data, party_label, company_data, styles, notes="[Specify if any]"):
    details_data = [
        [Paragraph(f"{party_label}: {party_data[0] or f'[{party_label} Name]'}", styles['small']), Paragraph(f"Ship To: {company_data[0] or '[Company Name]'}", styles['small'])],
        [Paragraph(f"{party_data[1] or '[Address Line 1]'}", styles['small']), Paragraph(f"{company_data[1] or '[Address Line 1]'}", styles['small'])],
        [Paragraph(f"{party_data[2] or '[Address Line 2]'}", styles['small']), Paragraph(f"{company_data[2] or '[Address Line 2]'}", styles['small'])],
        [Paragraph(f"{party_data[3] or '[City]'}, {party_data[4] or '[State]'} - {party_data[5] or '[Pin]'}", styles['small']), Paragraph(f"{company_data[3] or '[City]'}, {company_data[4] or '[State]'} - {company_data[5] or '[Pin]'}", styles['small'])],
        [Paragraph(f"GST: {party_data[6] or '[GST No]'}", styles['small']), Paragraph(f"Contact: {company_data[7] or '[Contact No]'}", styles['small'])],
        [Paragraph(f"Contact: {party_data[7] or '[Contact No]'}", styles['small']), Paragraph(f"Notes: {notes}", styles['small'])]
    ]
    details_col_widths = [82.885 * mm, 82.885 * mm]
    details_row_heights = [5.29 * mm] * 6
    details_table = Table(details_data, colWidths=details_col_widths, rowHeights=details_row_heights)
    details_table.hAlign = 'LEFT'
    details_table.setStyle(TableStyle([
        ('VALIGN', (0, 0), (-1, -1), 'MIDDLE'),
        ('ALIGN', (0, 0), (-1, -1), 'CENTER'),
        ('BOX', (0, 0), (-1, -1), 0.5, colors.black),
        ('INNERGRID', (0, 0), (-1, -1), 0.5, colors.black),
    ]))
    return details_table

def create_items_table(headers, items, styles, total_width=165.77*mm, item_formatter=None):
    try:
        items_data = [[Paragraph(cell, styles['header']) for cell in headers]]
        for idx, item in enumerate(items, 1):
            row = [str(idx)] + (item_formatter(item) if item_formatter else [str(x) for x in item])
            items_data.append([Paragraph(cell, styles['small']) for cell in row])

        col_widths = [0] * len(headers)
        for row in items_data:
            for i, cell in enumerate(row):
                width = estimate_text_width(cell.text if isinstance(cell, Paragraph) else cell, 'Helvetica', 10) + 2 * mm
                col_widths[i] = max(col_widths[i], width)
        
        current_total = sum(col_widths)
        if current_total > 0:
            scale = total_width / current_total
            col_widths = [w * scale for w in col_widths]
        else:
            col_widths = [total_width / len(headers)] * len(headers)

        row_heights = []
        for row in items_data:
            max_height = 5.29 * mm
            for i, cell in enumerate(row):
                w = col_widths[i] - 2 * mm
                h = cell.wrap(w, 1000 * mm)[1] + 2 * mm if isinstance(cell, Paragraph) else 5.29 * mm
                max_height = max(max_height, h)
            row_heights.append(max_height)

        items_table = Table(items_data, colWidths=col_widths, rowHeights=row_heights)
        items_table.hAlign = 'LEFT'
        items_table.setStyle(TableStyle([
            ('VALIGN', (0, 0), (-1, -1), 'MIDDLE'),
            ('ALIGN', (0, 0), (-1, -1), 'CENTER'),
            ('BOX', (0, 0), (-1, -1), 0.5, colors.black),
            ('INNERGRID', (0, 0), (-1, -1), 0.5, colors.black),
        ]))
        return items_table, col_widths
    except Exception as e:
        logger.error(f"Error creating items table: {e}")
        raise

def create_totals_and_terms_table(totals, terms, styles, col_widths, separator_width=10.58*mm, total_width=165.77*mm):
    try:
        totals_width = sum(col_widths[-2:]) if col_widths else total_width / 3
        terms_width = total_width - totals_width - separator_width
        terms_data = [[Paragraph("Terms & Conditions", styles['header'])]]
        for idx, term in enumerate(terms, 1):
            terms_data.append([Paragraph(f"{idx}. {term}", styles['small'])])
        while len(terms_data) < len(totals):
            terms_data.append([Paragraph("", styles['small'])])

        combined_data = [
            [terms_data[i][0], Paragraph("", styles['small']), totals[i][0], totals[i][1]]
            for i in range(len(totals))
        ]
        combined_col_widths = [terms_width, separator_width, col_widths[-2] if col_widths else total_width/6, col_widths[-1] if col_widths else total_width/6]
        combined_row_heights = [5.29 * mm] * len(totals)
        combined_table = Table(combined_data, colWidths=combined_col_widths, rowHeights=combined_row_heights)
        combined_table.hAlign = 'LEFT'
        combined_table.setStyle(TableStyle([
            ('VALIGN', (0, 0), (-1, -1), 'MIDDLE'),
            ('ALIGN', (0, 0), (0, -1), 'LEFT'),
            ('ALIGN', (2, 0), (-1, -1), 'CENTER'),
            ('BOX', (0, 0), (0, -1), 0.5, colors.black),
            ('BOX', (2, 0), (-1, -1), 0.5, colors.black),
            ('INNERGRID', (0, 0), (0, -1), 0.5, colors.black),
            ('INNERGRID', (2, 0), (-1, -1), 0.5, colors.black),
            ('SPAN', (0, 0), (0, 0)),
        ]))
        return combined_table
    except Exception as e:
        logger.error(f"Error creating totals and terms table: {e}")
        raise

def create_amount_in_words_table(amount, label, styles, number_to_words):
    try:
        amount_words = number_to_words(float(amount))
        table = Table(
            [[Paragraph(f"{label}: {amount_words}", styles['small'])]],
            colWidths=[165.77 * mm],
            rowHeights=[5.29 * mm]
        )
        table.hAlign = 'LEFT'
        table.setStyle(TableStyle([
            ('VALIGN', (0, 0), (-1, -1), 'MIDDLE'),
            ('ALIGN', (0, 0), (-1, -1), 'LEFT'),
            ('BOX', (0, 0), (-1, -1), 0.5, colors.black),
        ]))
        return table
    except Exception as e:
        logger.error(f"Error creating amount in words table: {e}")
        raise

def create_signatory_table(company_name, styles, designation="[Name/Designation]"):
    try:
        signatory_data = [
            [Paragraph("Authorised Signatory", styles['header']), Paragraph("", styles['small'])],
            [Paragraph("", styles['small']), Paragraph("", styles['small'])],
            [Paragraph("", styles['small']), Paragraph("", styles['small'])],
            [Paragraph("", styles['small']), Paragraph("", styles['small'])],
            [Paragraph("", styles['small']), Paragraph("", styles['small'])],
            [Paragraph(designation, styles['small']), Paragraph("", styles['small'])]
        ]
        signatory_col_widths = [41.4425 * mm] * 2
        signatory_row_heights = [5.29 * mm] * 6
        signatory_table = Table(signatory_data, colWidths=signatory_col_widths, rowHeights=signatory_row_heights)
        signatory_table.hAlign = 'LEFT'
        signatory_table.setStyle(TableStyle([
            ('VALIGN', (0, 0), (-1, -1), 'MIDDLE'),
            ('ALIGN', (0, 0), (-1, -1), 'CENTER'),
            ('BOX', (0, 0), (-1, -1), 0.5, colors.black),
            ('SPAN', (0, 0), (1, 0)),
            ('SPAN', (0, 5), (1, 5)),
        ]))
        return signatory_table
    except Exception as e:
        logger.error(f"Error creating signatory table: {e}")
        raise

def generate_stock_report(file_path, company_data, items):
    """
    Generate a stock report PDF with company details and stock items.
    
    Args:
        file_path (str): Path where the PDF will be saved.
        company_data (list): List containing company details (name, address1, address2, city, state, pin, gst_no, contact_no, email, logo_path).
        items (list): List of dictionaries containing stock items with keys: s_no, description, unit, quantity, unit_price, reorder_level.
    """
    try:
        if not file_path:
            raise ValueError("File path cannot be empty")
        if not company_data or not items:
            raise ValueError("Company data and items list cannot be empty")
        
        styles = get_paragraph_styles()
        doc = CustomDocTemplate(file_path, pagesize=A4)
        elements = []

        # Header table
        fields = [
            {'label': 'Report Date', 'value': datetime.now().strftime('%Y-%m-%d')},
        ]
        header_table = create_header_table(company_data, "Stock Report", fields, styles)
        elements.append(header_table)
        elements.append(Spacer(1, 10 * mm))

        # Stock items table
        headers = ["S.No", "Description", "Unit", "Quantity", "Unit Price", "Reorder Level"]
        def item_formatter(item):
            return [
                item["description"],
                item["unit"],
                str(item["quantity"]),
                f"{item['unit_price']:.2f}",
                str(item["reorder_level"])
            ]
        items_table, col_widths = create_items_table(headers, items, styles, item_formatter=item_formatter)
        elements.append(items_table)
        elements.append(Spacer(1, 10 * mm))

        # Signatory table
        signatory_table = create_signatory_table(company_data[0] if company_data else "[Company Name]", styles)
        elements.append(signatory_table)

        # Build the PDF
        doc.build(elements)
        logger.info(f"Stock report generated successfully at {file_path}")
    except Exception as e:
        logger.error(f"Failed to generate stock report at {file_path}: {e}")
        raise