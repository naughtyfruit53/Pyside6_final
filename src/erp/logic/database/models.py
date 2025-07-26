# src/erp/logic/database/models.py
# New file: Define all SQLAlchemy models here, consolidating schemas from schema.py and voucher.py

from sqlalchemy import Column, Integer, String, Float, Boolean, ForeignKey, DateTime, Text, CheckConstraint, func
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import relationship
from sqlalchemy import UniqueConstraint

Base = declarative_base()

class User(Base):
    __tablename__ = "users"
    id = Column(Integer, primary_key=True, autoincrement=True)
    username = Column(String, nullable=False, unique=True)
    password = Column(String, nullable=False)
    role = Column(String, CheckConstraint("role IN ('super_admin', 'admin', 'standard_user')"), nullable=False)
    created_at = Column(DateTime, nullable=False, default=func.now())
    active = Column(Boolean, default=True)
    must_change_password = Column(Boolean, default=False)

class PaymentTerm(Base):
    __tablename__ = "payment_terms"
    term = Column(String, primary_key=True)

class CompanyDetail(Base):
    __tablename__ = "company_details"
    id = Column(Integer, primary_key=True)
    company_name = Column(String, nullable=False)
    address1 = Column(String, nullable=False)
    address2 = Column(String)
    city = Column(String, nullable=False)
    state = Column(String, nullable=False)
    pin = Column(String, nullable=False)
    state_code = Column(String, nullable=False)
    gst_no = Column(String)
    pan_no = Column(String)
    contact_no = Column(String, nullable=False)
    email = Column(String)
    logo_path = Column(String)
    default_directory = Column(String)

class DefaultDirectory(Base):
    __tablename__ = "default_directory"
    id = Column(Integer, primary_key=True, autoincrement=True)
    directory_path = Column(String, nullable=False, unique=True)
    created_at = Column(DateTime, nullable=False, default=func.now())

class Vendor(Base):
    __tablename__ = "vendors"
    id = Column(Integer, primary_key=True, autoincrement=True)
    name = Column(String, nullable=False, unique=True)
    contact_no = Column(String, nullable=False)
    address1 = Column(String, nullable=False)
    address2 = Column(String)
    city = Column(String, nullable=False)
    state = Column(String, nullable=False)
    pin = Column(String, nullable=False)
    state_code = Column(String, nullable=False)
    gst_no = Column(String)
    pan_no = Column(String)
    email = Column(String)

class Customer(Base):
    __tablename__ = "customers"
    id = Column(Integer, primary_key=True, autoincrement=True)
    name = Column(String, nullable=False, unique=True)
    contact_no = Column(String, nullable=False)
    address1 = Column(String, nullable=False)
    address2 = Column(String)
    city = Column(String, nullable=False)
    state = Column(String, nullable=False)
    state_code = Column(String, nullable=False)
    pin = Column(String, nullable=False)
    gst_no = Column(String)
    pan_no = Column(String)
    email = Column(String)

class Product(Base):
    __tablename__ = "products"
    id = Column(Integer, primary_key=True, autoincrement=True)
    name = Column(String, nullable=False, unique=True)
    hsn_code = Column(String)
    part_no = Column(String)
    unit = Column(String, nullable=False)
    unit_price = Column(Float, nullable=False)
    gst_rate = Column(Float)
    is_gst_inclusive = Column(String, CheckConstraint("is_gst_inclusive IN ('Inclusive', 'Exclusive')"))
    reorder_level = Column(Integer, nullable=False)
    description = Column(String)
    created_at = Column(DateTime, nullable=False, default=func.now())
    is_manufactured = Column(Integer, default=0)
    drawings = Column(String)

class DocSequence(Base):
    __tablename__ = "doc_sequences"
    doc_type = Column(String, primary_key=True)
    fiscal_year = Column(String, primary_key=True)
    last_sequence = Column(Integer, nullable=False)

class UserPermission(Base):
    __tablename__ = "user_permissions"
    user_id = Column(Integer, ForeignKey("users.id"), primary_key=True)
    module_name = Column(String, primary_key=True)

class PurchaseOrder(Base):
    __tablename__ = "purchase_orders"
    id = Column(Integer, primary_key=True, autoincrement=True)
    po_number = Column(String, nullable=False, unique=True)
    vendor_id = Column(Integer, ForeignKey("vendors.id"), nullable=False)
    po_date = Column(DateTime)
    delivery_date = Column(DateTime)
    total_amount = Column(Float, nullable=False)
    cgst_amount = Column(Float)
    sgst_amount = Column(Float)
    igst_amount = Column(Float)
    grn_status = Column(String)
    is_deleted = Column(Integer, default=0)
    payment_terms = Column(String, ForeignKey("payment_terms.term"))

class PoItem(Base):
    __tablename__ = "po_items"
    id = Column(Integer, primary_key=True, autoincrement=True)
    po_id = Column(Integer, ForeignKey("purchase_orders.id"), nullable=False)
    product_id = Column(Integer, ForeignKey("products.id"), nullable=False)
    quantity = Column(Float, nullable=False)
    unit = Column(String, nullable=False)
    unit_price = Column(Float, nullable=False)
    gst_rate = Column(Float, nullable=False)
    amount = Column(Float, nullable=False)

class Grn(Base):
    __tablename__ = "grn"
    id = Column(Integer, primary_key=True, autoincrement=True)
    po_id = Column(Integer, ForeignKey("purchase_orders.id"), nullable=False)
    grn_number = Column(String, nullable=False, unique=True)
    description = Column(String)
    created_at = Column(DateTime, nullable=False, default=func.now())
    status = Column(String, nullable=False)

class GrnItem(Base):
    __tablename__ = "grn_items"
    id = Column(Integer, primary_key=True, autoincrement=True)
    grn_id = Column(Integer, ForeignKey("grn.id"), nullable=False)
    product_id = Column(Integer, ForeignKey("products.id"), nullable=False)
    po_item_id = Column(Integer, ForeignKey("po_items.id"), nullable=False)
    quantity = Column(Float, nullable=False)
    accepted_quantity = Column(Float, nullable=False)
    rejected_quantity = Column(Float, nullable=False)
    unit = Column(String, nullable=False)
    unit_price = Column(Float, nullable=False)
    total_cost = Column(Float, nullable=False)
    remarks = Column(String)

class Stock(Base):
    __tablename__ = "stock"
    id = Column(Integer, primary_key=True, autoincrement=True)
    product_id = Column(Integer, ForeignKey("products.id"), nullable=False)
    quantity = Column(Float, nullable=False)
    unit = Column(String, nullable=False)
    location = Column(String)
    last_updated = Column(DateTime, nullable=False, default=func.now())
    __table_args__ = (UniqueConstraint('product_id', name='uq_stock_product_id'),)

class AuditLog(Base):
    __tablename__ = "audit_log"
    id = Column(Integer, primary_key=True, autoincrement=True)
    table_name = Column(String, nullable=False)
    record_id = Column(Integer, nullable=False)
    action = Column(String, nullable=False)
    username = Column(String, nullable=False)
    timestamp = Column(DateTime, nullable=False, default=func.now())
    details = Column(String)

class Rejection(Base):
    __tablename__ = "rejections"
    id = Column(Integer, primary_key=True, autoincrement=True)
    grn_id = Column(Integer, ForeignKey("grn.id"), nullable=False)
    po_item_id = Column(Integer, ForeignKey("po_items.id"), nullable=False)
    product_id = Column(Integer, ForeignKey("products.id"), nullable=False)
    vendor_id = Column(Integer, ForeignKey("vendors.id"), nullable=False)
    quantity = Column(Float, nullable=False)
    unit = Column(String, nullable=False)
    created_at = Column(DateTime, nullable=False, default=func.now())

class CreditNote(Base):
    __tablename__ = "credit_notes"
    id = Column(Integer, primary_key=True, autoincrement=True)
    cn_number = Column(String, nullable=False, unique=True)
    grn_id = Column(Integer, ForeignKey("grn.id"), nullable=False)
    po_id = Column(Integer, ForeignKey("purchase_orders.id"), nullable=False)
    vendor_id = Column(Integer, ForeignKey("vendors.id"), nullable=False)
    cn_date = Column(DateTime, nullable=False)
    total_amount = Column(Float, nullable=False)
    cgst_amount = Column(Float)
    sgst_amount = Column(Float)
    igst_amount = Column(Float)
    created_at = Column(DateTime, nullable=False, default=func.now())
    voucher_type_id = Column(Integer, ForeignKey("voucher_types.id"))

class CnItem(Base):
    __tablename__ = "cn_items"
    id = Column(Integer, primary_key=True, autoincrement=True)
    cn_id = Column(Integer, ForeignKey("credit_notes.id"), nullable=False)
    product_id = Column(Integer, ForeignKey("products.id"), nullable=False)
    quantity = Column(Float, nullable=False)
    unit = Column(String, nullable=False)
    unit_price = Column(Float, nullable=False)
    gst_rate = Column(Float, nullable=False)
    amount = Column(Float, nullable=False)

class PurchaseInv(Base):
    __tablename__ = "purchase_inv"
    id = Column(Integer, primary_key=True, autoincrement=True)
    pur_inv_number = Column(String, nullable=False, unique=True)
    invoice_number = Column(String)
    invoice_date = Column(DateTime)
    grn_id = Column(Integer, ForeignKey("grn.id"), nullable=False)
    po_id = Column(Integer, ForeignKey("purchase_orders.id"), nullable=False)
    vendor_id = Column(Integer, ForeignKey("vendors.id"), nullable=False)
    pur_inv_date = Column(DateTime, nullable=False)
    total_amount = Column(Float, nullable=False)
    cgst_amount = Column(Float)
    sgst_amount = Column(Float)
    igst_amount = Column(Float)
    created_at = Column(DateTime, nullable=False, default=func.now())
    voucher_type_id = Column(Integer, ForeignKey("voucher_types.id"))

class PurchaseInvItem(Base):
    __tablename__ = "purchase_inv_items"
    id = Column(Integer, primary_key=True, autoincrement=True)
    pur_inv_id = Column(Integer, ForeignKey("purchase_inv.id"), nullable=False)
    product_id = Column(Integer, ForeignKey("products.id"), nullable=False)
    quantity = Column(Float, nullable=False)
    unit = Column(String, nullable=False)
    unit_price = Column(Float, nullable=False)
    gst_rate = Column(Float, nullable=False)
    amount = Column(Float, nullable=False)

class SalesInvoice(Base):
    __tablename__ = "sales_invoices"
    id = Column(Integer, primary_key=True, autoincrement=True)
    sales_inv_number = Column(String, nullable=False, unique=True)
    invoice_date = Column(DateTime)
    sales_order_id = Column(Integer, ForeignKey("sales_orders.id"))
    customer_id = Column(Integer, ForeignKey("customers.id"), nullable=False)
    total_amount = Column(Float, nullable=False)
    cgst_amount = Column(Float)
    sgst_amount = Column(Float)
    igst_amount = Column(Float)
    created_at = Column(DateTime, nullable=False, default=func.now())
    voucher_type_id = Column(Integer, ForeignKey("voucher_types.id"))
    voucher_data = Column(String)

class SalesInvItem(Base):
    __tablename__ = "sales_inv_items"
    id = Column(Integer, primary_key=True, autoincrement=True)
    sales_inv_id = Column(Integer, ForeignKey("sales_invoices.id"), nullable=False)
    product_id = Column(Integer, ForeignKey("products.id"), nullable=False)
    quantity = Column(Float, nullable=False)
    unit = Column(String, nullable=False)
    unit_price = Column(Float, nullable=False)
    gst_rate = Column(Float, nullable=False)
    amount = Column(Float, nullable=False)

class Quote(Base):
    __tablename__ = "quotes"
    id = Column(Integer, primary_key=True, autoincrement=True)
    quotation_number = Column(String, nullable=False, unique=True)
    customer_id = Column(Integer, ForeignKey("customers.id"), nullable=False)
    quotation_date = Column(DateTime)
    validity_date = Column(DateTime)
    total_amount = Column(Float, nullable=False)
    cgst_amount = Column(Float)
    sgst_amount = Column(Float)
    igst_amount = Column(Float)
    is_deleted = Column(Integer, default=0)
    payment_terms = Column(String)
    voucher_type_id = Column(Integer, ForeignKey("voucher_types.id"))

class QuoteItem(Base):
    __tablename__ = "quote_items"
    id = Column(Integer, primary_key=True, autoincrement=True)
    quote_id = Column(Integer, ForeignKey("quotes.id"), nullable=False)
    product_id = Column(Integer, ForeignKey("products.id"), nullable=False)
    quantity = Column(Float, nullable=False)
    unit = Column(String, nullable=False)
    unit_price = Column(Float, nullable=False)
    gst_rate = Column(Float, nullable=False)
    amount = Column(Float, nullable=False)

class Bom(Base):
    __tablename__ = "bom"
    id = Column(Integer, primary_key=True, autoincrement=True)
    manufactured_product_id = Column(Integer, ForeignKey("products.id"), nullable=False)
    created_at = Column(DateTime, nullable=False, default=func.now())

class BomComponent(Base):
    __tablename__ = "bom_components"
    id = Column(Integer, primary_key=True, autoincrement=True)
    bom_id = Column(Integer, ForeignKey("bom.id"), nullable=False)
    component_id = Column(Integer, ForeignKey("products.id"), nullable=False)
    quantity = Column(Float, nullable=False)

class WorkOrder(Base):
    __tablename__ = "work_orders"
    id = Column(Integer, primary_key=True, autoincrement=True)
    bom_id = Column(Integer, ForeignKey("bom.id"), nullable=False)
    quantity = Column(Float, nullable=False)
    status = Column(String, nullable=False, default='Open')
    created_at = Column(DateTime, nullable=False, default=func.now())
    closed_at = Column(DateTime)

class MaterialTransaction(Base):
    __tablename__ = "material_transactions"
    id = Column(Integer, primary_key=True, autoincrement=True)
    doc_number = Column(String, nullable=False, unique=True)
    delivery_challan_number = Column(String)
    type = Column(String, CheckConstraint("type IN ('Inflow', 'Outflow')"), nullable=False)
    date = Column(DateTime, nullable=False)
    product_id = Column(Integer, ForeignKey("products.id"), nullable=False)
    quantity = Column(Float, nullable=False)
    purpose = Column(String)
    remarks = Column(String)

class SalesOrder(Base):
    __tablename__ = "sales_orders"
    id = Column(Integer, primary_key=True, autoincrement=True)
    sales_order_number = Column(String, nullable=False, unique=True)
    customer_id = Column(Integer, ForeignKey("customers.id"), nullable=False)
    sales_order_date = Column(DateTime, nullable=False)
    delivery_date = Column(DateTime)
    payment_terms = Column(String)
    total_amount = Column(Float, nullable=False)
    cgst_amount = Column(Float)
    sgst_amount = Column(Float)
    igst_amount = Column(Float)
    created_at = Column(DateTime, nullable=False, default=func.now())
    updated_at = Column(DateTime, nullable=False, default=func.now())
    is_deleted = Column(Integer, default=0)
    voucher_type_id = Column(Integer, ForeignKey("voucher_types.id"))

class SalesOrderItem(Base):
    __tablename__ = "sales_order_items"
    id = Column(Integer, primary_key=True, autoincrement=True)
    sales_order_id = Column(Integer, ForeignKey("sales_orders.id"), nullable=False)
    product_id = Column(Integer, ForeignKey("products.id"), nullable=False)
    product_name = Column(String, nullable=False)
    hsn_code = Column(String)
    quantity = Column(Float, nullable=False)
    unit = Column(String, nullable=False)
    unit_price = Column(Float, nullable=False)
    gst_rate = Column(Float, nullable=False)
    amount = Column(Float, nullable=False)

class ProformaInvoice(Base):
    __tablename__ = "proforma_invoices"
    id = Column(Integer, primary_key=True, autoincrement=True)
    proforma_number = Column(String, nullable=False, unique=True)
    quotation_id = Column(Integer, ForeignKey("quotes.id"))
    customer_id = Column(Integer, ForeignKey("customers.id"))
    proforma_date = Column(DateTime)
    validity_date = Column(DateTime)
    total_amount = Column(Float)
    cgst_amount = Column(Float)
    sgst_amount = Column(Float)
    igst_amount = Column(Float)
    is_deleted = Column(Integer, default=0)
    payment_terms = Column(String)
    voucher_type_id = Column(Integer, ForeignKey("voucher_types.id"))

class ProformaInvoiceItem(Base):
    __tablename__ = "proforma_invoice_items"
    id = Column(Integer, primary_key=True, autoincrement=True)
    proforma_id = Column(Integer, ForeignKey("proforma_invoices.id"))
    product_id = Column(Integer, ForeignKey("products.id"))
    quantity = Column(Float)
    unit = Column(String)
    unit_price = Column(Float)
    gst_rate = Column(Float)
    amount = Column(Float)

class VoucherItem(Base):
    __tablename__ = "voucher_items"
    id = Column(Integer, primary_key=True, autoincrement=True)
    voucher_id = Column(Integer, ForeignKey("voucher_instances.id"), nullable=False)
    name = Column(String, nullable=False)
    hsn_code = Column(String)
    qty = Column(Float, nullable=False)
    unit = Column(String, nullable=False)
    unit_price = Column(Float, nullable=False)
    gst_rate = Column(Float, nullable=False)
    amount = Column(Float, nullable=False)
    ordered_qty = Column(Float, nullable=True, default=0.0)  # Added for GRN compatibility
    received_qty = Column(Float, nullable=True, default=0.0)  # Added for GRN compatibility
    accepted_qty = Column(Float, nullable=True, default=0.0)  # Added for GRN compatibility
    rejected_qty = Column(Float, nullable=True, default=0.0)  # Added for GRN compatibility
    remarks = Column(String, nullable=True, default='')  # Added for GRN compatibility

# Voucher-related models from voucher.py

class VoucherType(Base):
    __tablename__ = "voucher_types"
    id = Column(Integer, primary_key=True, autoincrement=True)
    voucher_name = Column(String, nullable=False, unique=True)
    type_code = Column(String, nullable=False, unique=True)
    category = Column(String, CheckConstraint("category IN ('purchase', 'sales', 'financial', 'internal', 'inward', 'outward')"), nullable=False)
    is_active = Column(Integer, nullable=False, default=1)

class VoucherColumn(Base):
    __tablename__ = "voucher_columns"
    id = Column(Integer, primary_key=True, autoincrement=True)
    voucher_type_id = Column(Integer, ForeignKey("voucher_types.id"), nullable=False)
    column_name = Column(String, nullable=False)
    data_type = Column(String, CheckConstraint("data_type IN ('TEXT', 'INTEGER', 'REAL', 'DATE')"), nullable=False)
    is_mandatory = Column(Integer, nullable=False, default=0)
    display_order = Column(Integer, nullable=False)
    is_calculated = Column(Integer, nullable=False, default=0)
    calculation_logic = Column(String)

class VoucherInstance(Base):
    __tablename__ = "voucher_instances"
    id = Column(Integer, primary_key=True, autoincrement=True)
    voucher_type_id = Column(Integer, ForeignKey("voucher_types.id"), nullable=False)
    voucher_number = Column(String, nullable=False, unique=True)
    created_at = Column(DateTime, nullable=False, default=func.now())
    date = Column(DateTime, nullable=False)
    data = Column(Text, nullable=False)
    module_name = Column(String, nullable=False)
    record_id = Column(Integer)
    total_amount = Column(Float)
    cgst_amount = Column(Float)
    sgst_amount = Column(Float)
    igst_amount = Column(Float)

class VoucherSequence(Base):
    __tablename__ = "voucher_sequence"
    fiscal_year = Column(String, primary_key=True)
    voucher_type_id = Column(Integer, ForeignKey("voucher_types.id"), primary_key=True)
    last_sequence = Column(Integer, nullable=False)