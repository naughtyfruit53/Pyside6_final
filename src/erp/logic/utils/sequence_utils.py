# Revised script: src/erp/logic/utils/sequence_utils.py

# src/erp/logic/utils/sequence_utils.py
# Converted to use SQLAlchemy.

import logging
import time
from datetime import datetime
from sqlalchemy import text
from src.erp.logic.database.session import engine, Session
from sqlalchemy.exc import OperationalError
from src.core.config import get_database_url, get_log_path
from src.erp.logic.database.models import DocSequence

logger = logging.getLogger(__name__)
if not logger.handlers:
    logging.basicConfig(
        filename=get_log_path(),
        level=logging.DEBUG,
        format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
    )

def get_fiscal_year():
    """Calculate the fiscal year (April 1 to March 31, e.g., '2526' for 2025-2026)."""
    try:
        today = datetime.now()
        year = today.year % 100
        if today.month >= 4:
            fiscal_year = f"{year:02d}{year + 1:02d}"
        else:
            fiscal_year = f"{year - 1:02d}{year:02d}"
        logger.debug(f"Calculated fiscal year: {fiscal_year}")
        return fiscal_year
    except Exception as e:
        logger.error(f"Error calculating fiscal year: {e}")
        raise

def get_next_doc_sequence(doc_type: str, fiscal_year: str, related_id: int = None):
    """
    Generate the next sequence number for a document type and fiscal year.
    Does not commit to prevent gaps until confirmed.
    
    Args:
        doc_type: Document type (e.g., 'SALES_INV', 'PO', 'GRN_PO123', 'SO').
        fiscal_year: Fiscal year (e.g., '2526').
        related_id: Optional ID for related documents (e.g., PO ID for GRN).
    
    Returns:
        int: Next sequence number, or None if failed.
    """
    with Session() as session:
        try:
            seq = session.query(DocSequence).filter_by(doc_type=doc_type, fiscal_year=fiscal_year).first()
            sequence = seq.last_sequence + 1 if seq else 1
            # Ensure the sequence exists in the table with a default value if new
            if not seq:
                new_seq = DocSequence(doc_type=doc_type, fiscal_year=fiscal_year, last_sequence=0)
                session.add(new_seq)
                session.commit()
                logger.debug(f"Initialized sequence for {doc_type}/{fiscal_year} with last_sequence=0")
            logger.debug(f"Generated sequence {sequence} for {doc_type}/{fiscal_year}")
            return sequence
        except Exception as e:
            session.rollback()
            logger.error(f"Failed to get sequence for {doc_type}/{fiscal_year}: {e}")
            return None

# Backward compatibility alias
get_next_sequence = get_next_doc_sequence

def commit_doc_sequence(doc_type: str, fiscal_year: str, sequence: int):
    """
    Commit a sequence number to the database after document save.
    
    Args:
        doc_type: Document type (e.g., 'SALES_INV', 'PO').
        fiscal_year: Fiscal year (e.g., '2526').
        sequence: Sequence number to commit.
    """
    retries = 5
    delay = 0.1  # seconds
    for attempt in range(retries):
        with Session() as session:
            try:
                seq = session.query(DocSequence).filter_by(doc_type=doc_type, fiscal_year=fiscal_year).first()
                if seq and seq.last_sequence >= sequence:
                    logger.debug(f"Sequence for {doc_type}/{fiscal_year} already at {seq.last_sequence}, no update needed")
                    return
                if seq:
                    seq.last_sequence = sequence
                else:
                    new_seq = DocSequence(doc_type=doc_type, fiscal_year=fiscal_year, last_sequence=sequence)
                    session.add(new_seq)
                session.commit()
                logger.info(f"Committed sequence {sequence} for {doc_type}/{fiscal_year}")
                return
            except OperationalError as e:
                session.rollback()
                if 'locked' in str(e) and attempt < retries - 1:
                    logger.warning(f"Database locked during commit for {doc_type}/{fiscal_year}, retrying in {delay}s...")
                    time.sleep(delay)
                    delay *= 2  # Exponential backoff
                else:
                    logger.error(f"Failed to commit sequence for {doc_type}/{fiscal_year}: {e}")
                    raise
            except Exception as e:
                session.rollback()
                logger.error(f"Failed to commit sequence for {doc_type}/{fiscal_year}: {e}")
                raise

# Backward compatibility alias
increment_sequence = commit_doc_sequence

def parse_doc_number(doc_number: str, expected_prefix: str) -> tuple[str, int] | None:
    """
    Parse a document number to extract fiscal year and sequence.
    
    Args:
        doc_number: Document number (e.g., 'SALES_INV/2526/0001').
        expected_prefix: Expected prefix (e.g., 'SALES_INV').
    
    Returns:
        Tuple of (fiscal_year, sequence), or None if invalid.
    """
    try:
        parts = doc_number.split('/')
        if len(parts) != 3 or parts[0] != expected_prefix:
            logger.error(f"Invalid {expected_prefix} number format: {doc_number}")
            return None
        fiscal_year, sequence = parts[1], int(parts[2])
        return fiscal_year, sequence
    except ValueError as e:
        logger.error(f"Failed to parse {expected_prefix} number {doc_number}: {e}")
        return None
    except Exception as e:
        logger.error(f"Unexpected error in parse_doc_number for {doc_number}: {e}")
        return None

def get_next_sales_inv_sequence():
    """Generate the next Sales Invoice number (e.g., SALES_INV/2526/0001)."""
    try:
        fiscal_year = get_fiscal_year()
        sequence = get_next_doc_sequence("SALES_INV", fiscal_year)
        if sequence is None:
            logger.error("Failed to generate Sales Invoice sequence")
            return None
        return f"SALES_INV/{fiscal_year}/{sequence:08d}"
    except Exception as e:
        logger.error(f"Error in get_next_sales_inv_sequence: {e}")
        return None

def increment_sales_inv_sequence(sales_inv_number: str):
    """Commit Sales Invoice sequence after save."""
    try:
        result = parse_doc_number(sales_inv_number, "SALES_INV")
        if result:
            fiscal_year, sequence = result
            commit_doc_sequence("SALES_INV", fiscal_year, sequence)
        else:
            logger.error(f"Failed to increment Sales Invoice sequence for {sales_inv_number}")
    except Exception as e:
        logger.error(f"Error in increment_sales_inv_sequence for {sales_inv_number}: {e}")
        raise

def get_next_sales_order_sequence():
    """Generate the next Sales Order number (e.g., SO/2526/0001)."""
    try:
        fiscal_year = get_fiscal_year()
        sequence = get_next_doc_sequence("SO", fiscal_year)
        if sequence is None:
            logger.error("Failed to generate Sales Order sequence")
            return None
        return f"SO/{fiscal_year}/{sequence:08d}"
    except Exception as e:
        logger.error(f"Error in get_next_sales_order_sequence: {e}")
        return None

def increment_sales_order_sequence(sales_order_number: str):
    """Commit Sales Order sequence after save."""
    try:
        result = parse_doc_number(sales_order_number, "SO")
        if result:
            fiscal_year, sequence = result
            commit_doc_sequence("SO", fiscal_year, sequence)
        else:
            logger.error(f"Failed to increment Sales Order sequence for {sales_order_number}")
    except Exception as e:
        logger.error(f"Error in increment_sales_order_sequence for {sales_order_number}: {e}")
        raise

def get_next_purchase_order_sequence():
    """Generate the next Purchase Order number (e.g., PO/2526/0001)."""
    try:
        fiscal_year = get_fiscal_year()
        sequence = get_next_doc_sequence("PO", fiscal_year)
        if sequence is None:
            logger.error("Failed to generate Purchase Order sequence")
            return None
        return f"PO/{fiscal_year}/{sequence:08d}"
    except Exception as e:
        logger.error(f"Error in get_next_purchase_order_sequence: {e}")
        return None

def increment_purchase_order_sequence(po_number: str):
    """Commit Purchase Order sequence after save."""
    try:
        result = parse_doc_number(po_number, "PO")
        if result:
            fiscal_year, sequence = result
            commit_doc_sequence("PO", fiscal_year, sequence)
        else:
            logger.error(f"Failed to increment Purchase Order sequence for {po_number}")
    except Exception as e:
        logger.error(f"Error in increment_purchase_order_sequence for {po_number}: {e}")
        raise

def get_next_grn_sequence():
    """Generate the next GRN number (e.g., GRN/2526/0001)."""
    try:
        fiscal_year = get_fiscal_year()
        sequence = get_next_doc_sequence("GRN", fiscal_year)
        if sequence is None:
            logger.error("Failed to generate GRN sequence")
            return None
        return f"GRN/{fiscal_year}/{sequence:08d}"
    except Exception as e:
        logger.error(f"Error in get_next_grn_sequence: {e}")
        return None

def increment_grn_sequence(grn_number: str):
    """Commit GRN sequence after save."""
    try:
        result = parse_doc_number(grn_number, "GRN")
        if result:
            fiscal_year, sequence = result
            commit_doc_sequence("GRN", fiscal_year, sequence)
        else:
            logger.error(f"Failed to increment GRN sequence for {grn_number}")
    except Exception as e:
        logger.error(f"Error in increment_grn_sequence for {grn_number}: {e}")
        raise

def get_next_credit_note_sequence():
    """Generate the next Credit Note number (e.g., CN/2526/0001)."""
    try:
        fiscal_year = get_fiscal_year()
        sequence = get_next_doc_sequence("CN", fiscal_year)
        if sequence is None:
            logger.error("Failed to generate Credit Note sequence")
            return None
        return f"CN/{fiscal_year}/{sequence:08d}"
    except Exception as e:
        logger.error(f"Error in get_next_credit_note_sequence: {e}")
        return None

def increment_credit_note_sequence(cn_number: str):
    """Commit Credit Note sequence after save."""
    try:
        result = parse_doc_number(cn_number, "CN")
        if result:
            fiscal_year, sequence = result
            commit_doc_sequence("CN", fiscal_year, sequence)
        else:
            logger.error(f"Failed to increment Credit Note sequence for {cn_number}")
    except Exception as e:
        logger.error(f"Error in increment_credit_note_sequence for {cn_number}: {e}")
        raise

def get_next_purchase_voucher_sequence():
    """Generate the next Purchase Voucher number (e.g., PV/2526/0001)."""
    try:
        fiscal_year = get_fiscal_year()
        sequence = get_next_doc_sequence("PV", fiscal_year)
        if sequence is None:
            logger.error("Failed to generate Purchase Voucher sequence")
            return None
        return f"PV/{fiscal_year}/{sequence:08d}"
    except Exception as e:
        logger.error(f"Error in get_next_purchase_voucher_sequence: {e}")
        return None

def increment_purchase_voucher_sequence(pv_number: str):
    """Commit Purchase Voucher sequence after save."""
    try:
        result = parse_doc_number(pv_number, "PV")
        if result:
            fiscal_year, sequence = result
            commit_doc_sequence("PV", fiscal_year, sequence)
        else:
            logger.error(f"Failed to increment Purchase Voucher sequence for {pv_number}")
    except Exception as e:
        logger.error(f"Error in increment_purchase_voucher_sequence for {pv_number}: {e}")
        raise

def get_next_purchase_inv_sequence():
    """Generate the next Purchase Invoice number (e.g., PI/2526/0001)."""
    try:
        fiscal_year = get_fiscal_year()
        sequence = get_next_doc_sequence("PI", fiscal_year)
        if sequence is None:
            logger.error("Failed to generate Purchase Invoice sequence")
            return None
        return f"PI/{fiscal_year}/{sequence:08d}"
    except Exception as e:
        logger.error(f"Error in get_next_purchase_inv_sequence: {e}")
        return None

def increment_purchase_inv_sequence(purchase_inv_number: str):
    """Commit Purchase Invoice sequence after save."""
    try:
        result = parse_doc_number(purchase_inv_number, "PI")
        if result:
            fiscal_year, sequence = result
            commit_doc_sequence("PI", fiscal_year, sequence)
        else:
            logger.error(f"Failed to increment Purchase Invoice sequence for {purchase_inv_number}")
    except Exception as e:
        logger.error(f"Error in increment_purchase_inv_sequence for {purchase_inv_number}: {e}")
        raise

def get_next_quote_sequence():
    """Generate the next Quotation number (e.g., QT/2526/0001)."""
    try:
        fiscal_year = get_fiscal_year()
        sequence = get_next_doc_sequence("QT", fiscal_year)
        if sequence is None:
            logger.error("Failed to generate Quotation sequence")
            return None
        return f"QT/{fiscal_year}/{sequence:08d}"
    except Exception as e:
        logger.error(f"Error in get_next_quote_sequence: {e}")
        return None

def increment_quote_sequence(quotation_number: str):
    """Commit Quotation sequence after save."""
    try:
        result = parse_doc_number(quotation_number, "QT")
        if result:
            fiscal_year, sequence = result
            commit_doc_sequence("QT", fiscal_year, sequence)
        else:
            logger.error(f"Failed to increment Quotation sequence for {quotation_number}")
    except Exception as e:
        logger.error(f"Error in increment_quote_sequence for {quotation_number}: {e}")
        raise

def get_next_proforma_sequence():
    """Generate the next Proforma Invoice number (e.g., PF/2526/0001)."""
    try:
        fiscal_year = get_fiscal_year()
        sequence = get_next_doc_sequence("PF", fiscal_year)
        if sequence is None:
            logger.error("Failed to generate Proforma Invoice sequence")
            return None
        return f"PF/{fiscal_year}/{sequence:08d}"
    except Exception as e:
        logger.error(f"Error in get_next_proforma_sequence: {e}")
        return None

def increment_proforma_sequence(proforma_number: str):
    """Commit Proforma Invoice sequence after save."""
    try:
        result = parse_doc_number(proforma_number, "PF")
        if result:
            fiscal_year, sequence = result
            commit_doc_sequence("PF", fiscal_year, sequence)
        else:
            logger.error(f"Failed to increment Proforma Invoice sequence for {proforma_number}")
    except Exception as e:
        logger.error(f"Error in increment_proforma_sequence for {proforma_number}: {e}")
        raise

def get_next_delivery_challan_sequence(prefix: str = "DC"):
    """Generate the next Delivery Challan number (e.g., DC/2526/0001, RP/2526/0001)."""
    try:
        fiscal_year = get_fiscal_year()
        doc_type = f"DC_{prefix}"
        sequence = get_next_doc_sequence(doc_type, fiscal_year)
        if sequence is None:
            logger.error(f"Failed to generate Delivery Challan sequence for prefix {prefix}")
            return None
        return f"{prefix}/{fiscal_year}/{sequence:08d}"
    except Exception as e:
        logger.error(f"Error in get_next_delivery_challan_sequence for prefix {prefix}: {e}")
        return None

def increment_delivery_challan_sequence(delivery_challan_number: str):
    """Commit Delivery Challan sequence after save."""
    try:
        parts = delivery_challan_number.split('/')
        if len(parts) != 3:
            logger.error(f"Invalid Delivery Challan number format: {delivery_challan_number}")
            return
        prefix, fiscal_year, sequence = parts[0], parts[1], int(parts[2])
        commit_doc_sequence(f"DC_{prefix}", fiscal_year, sequence)
    except ValueError as e:
        logger.error(f"Failed to parse Delivery Challan number {delivery_challan_number}: {e}")
        return
    except Exception as e:
        logger.error(f"Error in increment_delivery_challan_sequence for {delivery_challan_number}: {e}")
        raise

def get_next_internal_return_sequence():
    """Generate the next Internal Return number (e.g., IR/2526/0001)."""
    try:
        fiscal_year = get_fiscal_year()
        sequence = get_next_doc_sequence("IR", fiscal_year)
        if sequence is None:
            logger.error("Failed to generate Internal Return sequence")
            return None
        return f"IR/{fiscal_year}/{sequence:08d}"
    except Exception as e:
        logger.error(f"Error in get_next_internal_return_sequence: {e}")
        return None

def increment_internal_return_sequence(ir_number: str):
    """Commit Internal Return sequence after save."""
    try:
        result = parse_doc_number(ir_number, "IR")
        if result:
            fiscal_year, sequence = result
            commit_doc_sequence("IR", fiscal_year, sequence)
        else:
            logger.error(f"Failed to increment Internal Return sequence for {ir_number}")
    except Exception as e:
        logger.error(f"Error in increment_internal_return_sequence for {ir_number}: {e}")
        raise

def get_next_rejection_in_out_sequence():
    """Generate the next Rejection In/Out number (e.g., RIO/2526/0001)."""
    try:
        fiscal_year = get_fiscal_year()
        sequence = get_next_doc_sequence("RIO", fiscal_year)
        if sequence is None:
            logger.error("Failed to generate Rejection In/Out sequence")
            return None
        return f"RIO/{fiscal_year}/{sequence:08d}"
    except Exception as e:
        logger.error(f"Error in get_next_rejection_in_out_sequence: {e}")
        return None

def increment_rejection_in_out_sequence(rio_number: str):
    """Commit Rejection In/Out sequence after save."""
    try:
        result = parse_doc_number(rio_number, "RIO")
        if result:
            fiscal_year, sequence = result
            commit_doc_sequence("RIO", fiscal_year, sequence)
        else:
            logger.error(f"Failed to increment Rejection In/Out sequence for {rio_number}")
    except Exception as e:
        logger.error(f"Error in increment_rejection_in_out_sequence for {rio_number}: {e}")
        raise

def get_next_debit_note_sequence():
    """Generate the next Debit Note number (e.g., DN/2526/0001)."""
    try:
        fiscal_year = get_fiscal_year()
        sequence = get_next_doc_sequence("DN", fiscal_year)
        if sequence is None:
            logger.error("Failed to generate Debit Note sequence")
            return None
        return f"DN/{fiscal_year}/{sequence:08d}"
    except Exception as e:
        logger.error(f"Error in get_next_debit_note_sequence: {e}")
        return None

def increment_debit_note_sequence(dn_number: str):
    """Commit Debit Note sequence after save."""
    try:
        result = parse_doc_number(dn_number, "DN")
        if result:
            fiscal_year, sequence = result
            commit_doc_sequence("DN", fiscal_year, sequence)
        else:
            logger.error(f"Failed to increment Debit Note sequence for {dn_number}")
    except Exception as e:
        logger.error(f"Error in increment_debit_note_sequence for {dn_number}: {e}")
        raise

def get_next_contra_voucher_sequence():
    """Generate the next Contra Voucher number (e.g., CV/2526/0001)."""
    try:
        fiscal_year = get_fiscal_year()
        sequence = get_next_doc_sequence("CV", fiscal_year)
        if sequence is None:
            logger.error("Failed to generate Contra Voucher sequence")
            return None
        return f"CV/{fiscal_year}/{sequence:08d}"
    except Exception as e:
        logger.error(f"Error in get_next_contra_voucher_sequence: {e}")
        return None

def increment_contra_voucher_sequence(cv_number: str):
    """Commit Contra Voucher sequence after save."""
    try:
        result = parse_doc_number(cv_number, "CV")
        if result:
            fiscal_year, sequence = result
            commit_doc_sequence("CV", fiscal_year, sequence)
        else:
            logger.error(f"Failed to increment Contra Voucher sequence for {cv_number}")
    except Exception as e:
        logger.error(f"Error in increment_contra_voucher_sequence for {cv_number}: {e}")
        raise

def get_next_inter_department_voucher_sequence():
    """Generate the next Inter Department Voucher number (e.g., IDV/2526/0001)."""
    try:
        fiscal_year = get_fiscal_year()
        sequence = get_next_doc_sequence("IDV", fiscal_year)
        if sequence is None:
            logger.error("Failed to generate Inter Department Voucher sequence")
            return None
        return f"IDV/{fiscal_year}/{sequence:08d}"
    except Exception as e:
        logger.error(f"Error in get_next_inter_department_voucher_sequence: {e}")
        return None

def increment_inter_department_voucher_sequence(idv_number: str):
    """Commit Inter Department Voucher sequence after save."""
    try:
        result = parse_doc_number(idv_number, "IDV")
        if result:
            fiscal_year, sequence = result
            commit_doc_sequence("IDV", fiscal_year, sequence)
        else:
            logger.error(f"Failed to increment Inter Department Voucher sequence for {idv_number}")
    except Exception as e:
        logger.error(f"Error in increment_inter_department_voucher_sequence for {idv_number}: {e}")
        raise

def get_next_journal_voucher_sequence():
    """Generate the next Journal Voucher number (e.g., JV/2526/0001)."""
    try:
        fiscal_year = get_fiscal_year()
        sequence = get_next_doc_sequence("JV", fiscal_year)
        if sequence is None:
            logger.error("Failed to generate Journal Voucher sequence")
            return None
        return f"JV/{fiscal_year}/{sequence:08d}"
    except Exception as e:
        logger.error(f"Error in get_next_journal_voucher_sequence: {e}")
        return None

def increment_journal_voucher_sequence(jv_number: str):
    """Commit Journal Voucher sequence after save."""
    try:
        result = parse_doc_number(jv_number, "JV")
        if result:
            fiscal_year, sequence = result
            commit_doc_sequence("JV", fiscal_year, sequence)
        else:
            logger.error(f"Failed to increment Journal Voucher sequence for {jv_number}")
    except Exception as e:
        logger.error(f"Error in increment_journal_voucher_sequence for {jv_number}: {e}")
        raise

def get_next_non_sales_credit_note_sequence():
    """Generate the next Non-Sales Credit Note number (e.g., NSCN/2526/0001)."""
    try:
        fiscal_year = get_fiscal_year()
        sequence = get_next_doc_sequence("NSCN", fiscal_year)
        if sequence is None:
            logger.error("Failed to generate Non-Sales Credit Note sequence")
            return None
        return f"NSCN/{fiscal_year}/{sequence:08d}"
    except Exception as e:
        logger.error(f"Error in get_next_non_sales_credit_note_sequence: {e}")
        return None

def increment_non_sales_credit_note_sequence(nscn_number: str):
    """Commit Non-Sales Credit Note sequence after save."""
    try:
        result = parse_doc_number(nscn_number, "NSCN")
        if result:
            fiscal_year, sequence = result
            commit_doc_sequence("NSCN", fiscal_year, sequence)
        else:
            logger.error(f"Failed to increment Non-Sales Credit Note sequence for {nscn_number}")
    except Exception as e:
        logger.error(f"Error in increment_non_sales_credit_note_sequence for {nscn_number}: {e}")
        raise

def get_next_payment_voucher_sequence():
    """Generate the next Payment Voucher number (e.g., PMT/2526/0001)."""
    try:
        fiscal_year = get_fiscal_year()
        sequence = get_next_doc_sequence("PMT", fiscal_year)
        if sequence is None:
            logger.error("Failed to generate Payment Voucher sequence")
            return None
        return f"PMT/{fiscal_year}/{sequence:08d}"
    except Exception as e:
        logger.error(f"Error in get_next_payment_voucher_sequence: {e}")
        return None

def increment_payment_voucher_sequence(pmt_number: str):
    """Commit Payment Voucher sequence after save."""
    try:
        result = parse_doc_number(pmt_number, "PMT")
        if result:
            fiscal_year, sequence = result
            commit_doc_sequence("PMT", fiscal_year, sequence)
        else:
            logger.error(f"Failed to increment Payment Voucher sequence for {pmt_number}")
    except Exception as e:
        logger.error(f"Error in increment_payment_voucher_sequence for {pmt_number}: {e}")
        raise

def get_next_receipt_voucher_sequence():
    """Generate the next Receipt Voucher number (e.g., RCT/2526/0001)."""
    try:
        fiscal_year = get_fiscal_year()
        sequence = get_next_doc_sequence("RCT", fiscal_year)
        if sequence is None:
            logger.error("Failed to generate Receipt Voucher sequence")
            return None
        return f"RCT/{fiscal_year}/{sequence:08d}"
    except Exception as e:
        logger.error(f"Error in get_next_receipt_voucher_sequence: {e}")
        return None

def increment_receipt_voucher_sequence(rct_number: str):
    """Commit Receipt Voucher sequence after save."""
    try:
        result = parse_doc_number(rct_number, "RCT")
        if result:
            fiscal_year, sequence = result
            commit_doc_sequence("RCT", fiscal_year, sequence)
        else:
            logger.error(f"Failed to increment Receipt Voucher sequence for {rct_number}")
    except Exception as e:
        logger.error(f"Error in increment_receipt_voucher_sequence for {rct_number}: {e}")
        raise

def get_next_revision_number(doc_type: str, doc_id: int):
    """Generate the next revision number for a document (e.g., PO, SO, QT)."""
    try:
        fiscal_year = get_fiscal_year()
        revision_doc_type = f"{doc_type}_REV_{doc_id}"
        sequence = get_next_doc_sequence(revision_doc_type, fiscal_year)
        if sequence is None:
            logger.error(f"Failed to generate revision number for {doc_type} ID {doc_id}")
            return None
        return sequence
    except Exception as e:
        logger.error(f"Error in get_next_revision_number for {doc_type} ID {doc_id}: {e}")
        return None

def commit_revision_number(doc_type: str, doc_id: int, revision_number: int):
    """Commit revision number after save."""
    try:
        fiscal_year = get_fiscal_year()
        revision_doc_type = f"{doc_type}_REV_{doc_id}"
        commit_doc_sequence(revision_doc_type, fiscal_year, revision_number)
    except Exception as e:
        logger.error(f"Error in commit_revision_number for {doc_type} ID {doc_id}: {e}")
        raise