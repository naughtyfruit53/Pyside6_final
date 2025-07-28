# revised fastapi_migration/app/models/vouchers.py

from sqlalchemy import Column, Integer, String, Float, DateTime, Text, ForeignKey
from sqlalchemy.orm import relationship, declared_attr
from sqlalchemy.sql import func
from app.core.database import Base

class BaseVoucher(Base):
    __abstract__ = True
    
    id = Column(Integer, primary_key=True, index=True)
    voucher_number = Column(String, unique=True, nullable=False, index=True)
    date = Column(DateTime(timezone=True), nullable=False)
    total_amount = Column(Float, nullable=False, default=0.0)
    cgst_amount = Column(Float, default=0.0)
    sgst_amount = Column(Float, default=0.0)
    igst_amount = Column(Float, default=0.0)
    discount_amount = Column(Float, default=0.0)
    status = Column(String, default="draft")
    notes = Column(Text)
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), onupdate=func.now())

    @declared_attr
    def created_by(cls):
        return Column(Integer, ForeignKey("users.id"))

    @declared_attr
    def created_by_user(cls):
        return relationship("User")

class VoucherItemBase(Base):
    __abstract__ = True
    
    id = Column(Integer, primary_key=True, index=True)
    product_id = Column(Integer, ForeignKey("products.id"), nullable=False)
    quantity = Column(Float, nullable=False)
    unit = Column(String, nullable=False)
    unit_price = Column(Float, nullable=False)
    discount_percentage = Column(Float, default=0.0)
    discount_amount = Column(Float, default=0.0)
    taxable_amount = Column(Float, nullable=False)
    gst_rate = Column(Float, default=0.0)
    cgst_amount = Column(Float, default=0.0)
    sgst_amount = Column(Float, default=0.0)
    igst_amount = Column(Float, default=0.0)
    total_amount = Column(Float, nullable=False)
    
    @declared_attr
    def product(cls):
        return relationship("Product")

class SimpleVoucherItemBase(Base):
    __abstract__ = True
    
    id = Column(Integer, primary_key=True, index=True)
    product_id = Column(Integer, ForeignKey("products.id"), nullable=False)
    quantity = Column(Float, nullable=False)
    unit = Column(String, nullable=False)
    unit_price = Column(Float, nullable=False)
    total_amount = Column(Float, nullable=False)
    
    @declared_attr
    def product(cls):
        return relationship("Product")

# Purchase Voucher
class PurchaseVoucher(BaseVoucher):
    __tablename__ = "purchase_vouchers"
    
    vendor_id = Column(Integer, ForeignKey("vendors.id"), nullable=False)
    purchase_order_id = Column(Integer, ForeignKey("purchase_orders.id"))
    invoice_number = Column(String)
    invoice_date = Column(DateTime(timezone=True))
    due_date = Column(DateTime(timezone=True))
    payment_terms = Column(String)
    transport_mode = Column(String)
    vehicle_number = Column(String)
    lr_rr_number = Column(String)
    e_way_bill_number = Column(String)
    
    vendor = relationship("Vendor")
    purchase_order = relationship("PurchaseOrder")
    items = relationship("PurchaseVoucherItem", back_populates="purchase_voucher")

class PurchaseVoucherItem(VoucherItemBase):
    __tablename__ = "purchase_voucher_items"
    
    purchase_voucher_id = Column(Integer, ForeignKey("purchase_vouchers.id"), nullable=False)
    purchase_voucher = relationship("PurchaseVoucher", back_populates="items")

# Sales Voucher
class SalesVoucher(BaseVoucher):
    __tablename__ = "sales_vouchers"
    
    customer_id = Column(Integer, ForeignKey("customers.id"), nullable=False)
    sales_order_id = Column(Integer, ForeignKey("sales_orders.id"))
    invoice_date = Column(DateTime(timezone=True))
    due_date = Column(DateTime(timezone=True))
    payment_terms = Column(String)
    place_of_supply = Column(String)
    transport_mode = Column(String)
    vehicle_number = Column(String)
    lr_rr_number = Column(String)
    e_way_bill_number = Column(String)
    
    customer = relationship("Customer")
    sales_order = relationship("SalesOrder")
    items = relationship("SalesVoucherItem", back_populates="sales_voucher")

class SalesVoucherItem(VoucherItemBase):
    __tablename__ = "sales_voucher_items"
    
    sales_voucher_id = Column(Integer, ForeignKey("sales_vouchers.id"), nullable=False)
    sales_voucher = relationship("SalesVoucher", back_populates="items")

# Purchase Order
class PurchaseOrder(BaseVoucher):
    __tablename__ = "purchase_orders"
    
    vendor_id = Column(Integer, ForeignKey("vendors.id"), nullable=False)
    delivery_date = Column(DateTime(timezone=True))
    payment_terms = Column(String)
    terms_conditions = Column(Text)
    
    vendor = relationship("Vendor")
    items = relationship("PurchaseOrderItem", back_populates="purchase_order")

class PurchaseOrderItem(SimpleVoucherItemBase):
    __tablename__ = "purchase_order_items"
    
    purchase_order_id = Column(Integer, ForeignKey("purchase_orders.id"), nullable=False)
    delivered_quantity = Column(Float, default=0.0)
    pending_quantity = Column(Float, nullable=False)
    
    purchase_order = relationship("PurchaseOrder", back_populates="items")

# Sales Order
class SalesOrder(BaseVoucher):
    __tablename__ = "sales_orders"
    
    customer_id = Column(Integer, ForeignKey("customers.id"), nullable=False)
    delivery_date = Column(DateTime(timezone=True))
    payment_terms = Column(String)
    terms_conditions = Column(Text)
    
    customer = relationship("Customer")
    items = relationship("SalesOrderItem", back_populates="sales_order")

class SalesOrderItem(SimpleVoucherItemBase):
    __tablename__ = "sales_order_items"
    
    sales_order_id = Column(Integer, ForeignKey("sales_orders.id"), nullable=False)
    delivered_quantity = Column(Float, default=0.0)
    pending_quantity = Column(Float, nullable=False)
    
    sales_order = relationship("SalesOrder", back_populates="items")

# Goods Receipt Note (GRN)
class GoodsReceiptNote(BaseVoucher):
    __tablename__ = "goods_receipt_notes"
    
    purchase_order_id = Column(Integer, ForeignKey("purchase_orders.id"), nullable=False)
    vendor_id = Column(Integer, ForeignKey("vendors.id"), nullable=False)
    grn_date = Column(DateTime(timezone=True), nullable=False)
    challan_number = Column(String)
    challan_date = Column(DateTime(timezone=True))
    transport_mode = Column(String)
    vehicle_number = Column(String)
    lr_rr_number = Column(String)
    
    purchase_order = relationship("PurchaseOrder")
    vendor = relationship("Vendor")
    items = relationship("GoodsReceiptNoteItem", back_populates="grn")

class GoodsReceiptNoteItem(Base):
    __tablename__ = "goods_receipt_note_items"
    
    id = Column(Integer, primary_key=True, index=True)
    grn_id = Column(Integer, ForeignKey("goods_receipt_notes.id"), nullable=False)
    product_id = Column(Integer, ForeignKey("products.id"), nullable=False)
    po_item_id = Column(Integer, ForeignKey("purchase_order_items.id"))
    ordered_quantity = Column(Float, nullable=False)
    received_quantity = Column(Float, nullable=False)
    accepted_quantity = Column(Float, nullable=False)
    rejected_quantity = Column(Float, default=0.0)
    unit = Column(String, nullable=False)
    unit_price = Column(Float, nullable=False)
    total_cost = Column(Float, nullable=False)
    remarks = Column(Text)
    
    grn = relationship("GoodsReceiptNote", back_populates="items")
    product = relationship("Product")
    po_item = relationship("PurchaseOrderItem")

# Delivery Challan
class DeliveryChallan(BaseVoucher):
    __tablename__ = "delivery_challans"
    
    customer_id = Column(Integer, ForeignKey("customers.id"), nullable=False)
    sales_order_id = Column(Integer, ForeignKey("sales_orders.id"))
    delivery_date = Column(DateTime(timezone=True))
    transport_mode = Column(String)
    vehicle_number = Column(String)
    lr_rr_number = Column(String)
    destination = Column(String)
    
    customer = relationship("Customer")
    sales_order = relationship("SalesOrder")
    items = relationship("DeliveryChallanItem", back_populates="delivery_challan")

class DeliveryChallanItem(SimpleVoucherItemBase):
    __tablename__ = "delivery_challan_items"
    
    delivery_challan_id = Column(Integer, ForeignKey("delivery_challans.id"), nullable=False)
    delivery_challan = relationship("DeliveryChallan", back_populates="items")

# Proforma Invoice
class ProformaInvoice(BaseVoucher):
    __tablename__ = "proforma_invoices"
    
    customer_id = Column(Integer, ForeignKey("customers.id"), nullable=False)
    valid_until = Column(DateTime(timezone=True))
    payment_terms = Column(String)
    terms_conditions = Column(Text)
    
    customer = relationship("Customer")
    items = relationship("ProformaInvoiceItem", back_populates="proforma_invoice")

class ProformaInvoiceItem(VoucherItemBase):
    __tablename__ = "proforma_invoice_items"
    
    proforma_invoice_id = Column(Integer, ForeignKey("proforma_invoices.id"), nullable=False)
    proforma_invoice = relationship("ProformaInvoice", back_populates="items")

# Quotation
class Quotation(BaseVoucher):
    __tablename__ = "quotations"
    
    customer_id = Column(Integer, ForeignKey("customers.id"), nullable=False)
    valid_until = Column(DateTime(timezone=True))
    payment_terms = Column(String)
    terms_conditions = Column(Text)
    
    customer = relationship("Customer")
    items = relationship("QuotationItem", back_populates="quotation")

class QuotationItem(SimpleVoucherItemBase):
    __tablename__ = "quotation_items"
    
    quotation_id = Column(Integer, ForeignKey("quotations.id"), nullable=False)
    quotation = relationship("Quotation", back_populates="items")

# Credit Note
class CreditNote(BaseVoucher):
    __tablename__ = "credit_notes"
    
    customer_id = Column(Integer, ForeignKey("customers.id"))
    vendor_id = Column(Integer, ForeignKey("vendors.id"))
    reference_voucher_type = Column(String)
    reference_voucher_id = Column(Integer)
    reason = Column(String, nullable=False)
    
    customer = relationship("Customer")
    vendor = relationship("Vendor")
    items = relationship("CreditNoteItem", back_populates="credit_note")

class CreditNoteItem(SimpleVoucherItemBase):
    __tablename__ = "credit_note_items"
    
    credit_note_id = Column(Integer, ForeignKey("credit_notes.id"), nullable=False)
    credit_note = relationship("CreditNote", back_populates="items")

# Debit Note
class DebitNote(BaseVoucher):
    __tablename__ = "debit_notes"
    
    customer_id = Column(Integer, ForeignKey("customers.id"))
    vendor_id = Column(Integer, ForeignKey("vendors.id"))
    reference_voucher_type = Column(String)
    reference_voucher_id = Column(Integer)
    reason = Column(String, nullable=False)
    
    customer = relationship("Customer")
    vendor = relationship("Vendor")
    items = relationship("DebitNoteItem", back_populates="debit_note")

class DebitNoteItem(SimpleVoucherItemBase):
    __tablename__ = "debit_note_items"
    
    debit_note_id = Column(Integer, ForeignKey("debit_notes.id"), nullable=False)
    debit_note = relationship("DebitNote", back_populates="items")

# Payment Voucher
class PaymentVoucher(BaseVoucher):
    __tablename__ = "payment_vouchers"
    
    vendor_id = Column(Integer, ForeignKey("vendors.id"), nullable=False)
    payment_method = Column(String)
    reference = Column(String)
    
    vendor = relationship("Vendor")

# Receipt Voucher
class ReceiptVoucher(BaseVoucher):
    __tablename__ = "receipt_vouchers"
    
    customer_id = Column(Integer, ForeignKey("customers.id"), nullable=False)
    receipt_method = Column(String)
    reference = Column(String)
    
    customer = relationship("Customer")

# Contra Voucher
class ContraVoucher(BaseVoucher):
    __tablename__ = "contra_vouchers"
    
    from_account = Column(String)
    to_account = Column(String)

# Journal Voucher
class JournalVoucher(BaseVoucher):
    __tablename__ = "journal_vouchers"
    
    entries = Column(Text)  # JSON string of entries

# Inter Department Voucher
class InterDepartmentVoucher(BaseVoucher):
    __tablename__ = "inter_department_vouchers"
    
    from_department = Column(String)
    to_department = Column(String)
    items = relationship("InterDepartmentVoucherItem", back_populates="inter_department_voucher")

class InterDepartmentVoucherItem(SimpleVoucherItemBase):
    __tablename__ = "inter_department_voucher_items"
    
    inter_department_voucher_id = Column(Integer, ForeignKey("inter_department_vouchers.id"), nullable=False)
    inter_department_voucher = relationship("InterDepartmentVoucher", back_populates="items")

# Rejection In (Purchase Return)
class PurchaseReturn(BaseVoucher):
    __tablename__ = "purchase_returns"
    
    vendor_id = Column(Integer, ForeignKey("vendors.id"), nullable=False)
    reference_voucher_id = Column(Integer, ForeignKey("purchase_vouchers.id"))
    reason = Column(Text)
    
    vendor = relationship("Vendor")
    reference_voucher = relationship("PurchaseVoucher")
    items = relationship("PurchaseReturnItem", back_populates="purchase_return")

class PurchaseReturnItem(VoucherItemBase):
    __tablename__ = "purchase_return_items"
    
    purchase_return_id = Column(Integer, ForeignKey("purchase_returns.id"), nullable=False)
    purchase_return = relationship("PurchaseReturn", back_populates="items")

# Rejection Out (Sales Return)
class SalesReturn(BaseVoucher):
    __tablename__ = "sales_returns"
    
    customer_id = Column(Integer, ForeignKey("customers.id"), nullable=False)
    reference_voucher_id = Column(Integer, ForeignKey("sales_vouchers.id"))
    reason = Column(Text)
    
    customer = relationship("Customer")
    reference_voucher = relationship("SalesVoucher")
    items = relationship("SalesReturnItem", back_populates="sales_return")

class SalesReturnItem(VoucherItemBase):
    __tablename__ = "sales_return_items"
    
    sales_return_id = Column(Integer, ForeignKey("sales_returns.id"), nullable=False)
    sales_return = relationship("SalesReturn", back_populates="items")