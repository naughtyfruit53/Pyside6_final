# revised fastapi_migration/app/schemas/vouchers.py

from pydantic import BaseModel
from typing import Optional, List
from datetime import datetime

class VoucherItemBase(BaseModel):
    product_id: int
    quantity: float
    unit: str
    unit_price: float

class VoucherItemWithTax(VoucherItemBase):
    discount_percentage: float = 0.0
    discount_amount: float = 0.0
    taxable_amount: float
    gst_rate: float = 0.0
    cgst_amount: float = 0.0
    sgst_amount: float = 0.0
    igst_amount: float = 0.0
    total_amount: float

class SimpleVoucherItem(VoucherItemBase):
    total_amount: float

class VoucherBase(BaseModel):
    voucher_number: str
    date: datetime
    total_amount: float = 0.0
    cgst_amount: float = 0.0
    sgst_amount: float = 0.0
    igst_amount: float = 0.0
    discount_amount: float = 0.0
    status: str = "draft"
    notes: Optional[str] = None

class VoucherInDBBase(VoucherBase):
    id: int
    created_by: int
    created_at: datetime
    updated_at: Optional[datetime] = None
    
    class Config:
        from_attributes = True

# Purchase Voucher
class PurchaseVoucherItemCreate(VoucherItemWithTax):
    pass

class PurchaseVoucherItemInDB(PurchaseVoucherItemCreate):
    id: int
    purchase_voucher_id: int

class PurchaseVoucherCreate(VoucherBase):
    vendor_id: int
    purchase_order_id: Optional[int] = None
    invoice_number: Optional[str] = None
    invoice_date: Optional[datetime] = None
    due_date: Optional[datetime] = None
    payment_terms: Optional[str] = None
    transport_mode: Optional[str] = None
    vehicle_number: Optional[str] = None
    lr_rr_number: Optional[str] = None
    e_way_bill_number: Optional[str] = None
    items: List[PurchaseVoucherItemCreate] = []

class PurchaseVoucherUpdate(BaseModel):
    vendor_id: Optional[int] = None
    purchase_order_id: Optional[int] = None
    invoice_number: Optional[str] = None
    invoice_date: Optional[datetime] = None
    due_date: Optional[datetime] = None
    payment_terms: Optional[str] = None
    transport_mode: Optional[str] = None
    vehicle_number: Optional[str] = None
    lr_rr_number: Optional[str] = None
    e_way_bill_number: Optional[str] = None
    total_amount: Optional[float] = None
    cgst_amount: Optional[float] = None
    sgst_amount: Optional[float] = None
    igst_amount: Optional[float] = None
    discount_amount: Optional[float] = None
    status: Optional[str] = None
    notes: Optional[str] = None
    items: Optional[List[PurchaseVoucherItemCreate]] = None

class PurchaseVoucherInDB(VoucherInDBBase):
    vendor_id: int
    purchase_order_id: Optional[int]
    invoice_number: Optional[str]
    invoice_date: Optional[datetime]
    due_date: Optional[datetime]
    payment_terms: Optional[str]
    transport_mode: Optional[str]
    vehicle_number: Optional[str]
    lr_rr_number: Optional[str]
    e_way_bill_number: Optional[str]
    items: List[PurchaseVoucherItemInDB]

# Sales Voucher
class SalesVoucherItemCreate(VoucherItemWithTax):
    pass

class SalesVoucherItemInDB(SalesVoucherItemCreate):
    id: int
    sales_voucher_id: int

class SalesVoucherCreate(VoucherBase):
    customer_id: int
    sales_order_id: Optional[int] = None
    invoice_date: Optional[datetime] = None
    due_date: Optional[datetime] = None
    payment_terms: Optional[str] = None
    place_of_supply: Optional[str] = None
    transport_mode: Optional[str] = None
    vehicle_number: Optional[str] = None
    lr_rr_number: Optional[str] = None
    e_way_bill_number: Optional[str] = None
    items: List[SalesVoucherItemCreate] = []

class SalesVoucherUpdate(BaseModel):
    customer_id: Optional[int] = None
    sales_order_id: Optional[int] = None
    invoice_date: Optional[datetime] = None
    due_date: Optional[datetime] = None
    payment_terms: Optional[str] = None
    place_of_supply: Optional[str] = None
    transport_mode: Optional[str] = None
    vehicle_number: Optional[str] = None
    lr_rr_number: Optional[str] = None
    e_way_bill_number: Optional[str] = None
    total_amount: Optional[float] = None
    cgst_amount: Optional[float] = None
    sgst_amount: Optional[float] = None
    igst_amount: Optional[float] = None
    discount_amount: Optional[float] = None
    status: Optional[str] = None
    notes: Optional[str] = None
    items: Optional[List[SalesVoucherItemCreate]] = None

class SalesVoucherInDB(VoucherInDBBase):
    customer_id: int
    sales_order_id: Optional[int]
    invoice_date: Optional[datetime]
    due_date: Optional[datetime]
    payment_terms: Optional[str]
    place_of_supply: Optional[str]
    transport_mode: Optional[str]
    vehicle_number: Optional[str]
    lr_rr_number: Optional[str]
    e_way_bill_number: Optional[str]
    items: List[SalesVoucherItemInDB]

# Purchase Order
class PurchaseOrderItemCreate(SimpleVoucherItem):
    pass

class PurchaseOrderItemInDB(PurchaseOrderItemCreate):
    id: int
    purchase_order_id: int
    delivered_quantity: float = 0.0
    pending_quantity: float

class PurchaseOrderCreate(VoucherBase):
    vendor_id: int
    delivery_date: Optional[datetime] = None
    payment_terms: Optional[str] = None
    terms_conditions: Optional[str] = None
    items: List[PurchaseOrderItemCreate] = []

class PurchaseOrderUpdate(BaseModel):
    vendor_id: Optional[int] = None
    delivery_date: Optional[datetime] = None
    payment_terms: Optional[str] = None
    terms_conditions: Optional[str] = None
    total_amount: Optional[float] = None
    status: Optional[str] = None
    notes: Optional[str] = None
    items: Optional[List[PurchaseOrderItemCreate]] = None

class PurchaseOrderInDB(VoucherInDBBase):
    vendor_id: int
    delivery_date: Optional[datetime]
    payment_terms: Optional[str]
    terms_conditions: Optional[str]
    items: List[PurchaseOrderItemInDB]

class PurchaseOrderAutoPopulateResponse(BaseModel):
    vendor_id: int
    purchase_order_id: int
    delivery_date: Optional[datetime] = None
    payment_terms: Optional[str] = None
    terms_conditions: Optional[str] = None
    items: List[PurchaseVoucherItemCreate]

# Sales Order
class SalesOrderItemCreate(SimpleVoucherItem):
    pass

class SalesOrderItemInDB(SalesOrderItemCreate):
    id: int
    sales_order_id: int
    delivered_quantity: float = 0.0
    pending_quantity: float

class SalesOrderCreate(VoucherBase):
    customer_id: int
    delivery_date: Optional[datetime] = None
    payment_terms: Optional[str] = None
    terms_conditions: Optional[str] = None
    items: List[SalesOrderItemCreate] = []

class SalesOrderUpdate(BaseModel):
    customer_id: Optional[int] = None
    delivery_date: Optional[datetime] = None
    payment_terms: Optional[str] = None
    terms_conditions: Optional[str] = None
    total_amount: Optional[float] = None
    status: Optional[str] = None
    notes: Optional[str] = None
    items: Optional[List[SalesOrderItemCreate]] = None

class SalesOrderInDB(VoucherInDBBase):
    customer_id: int
    delivery_date: Optional[datetime]
    payment_terms: Optional[str]
    terms_conditions: Optional[str]
    items: List[SalesOrderItemInDB]

class SalesOrderAutoPopulateResponse(BaseModel):
    customer_id: int
    sales_order_id: int
    delivery_date: Optional[datetime] = None
    payment_terms: Optional[str] = None
    terms_conditions: Optional[str] = None
    place_of_supply: Optional[str] = None
    items: List[SalesVoucherItemCreate]

# GRN
class GRNItemCreate(BaseModel):
    product_id: int
    po_item_id: Optional[int] = None
    ordered_quantity: float
    received_quantity: float
    accepted_quantity: float
    rejected_quantity: float = 0.0
    unit: str
    unit_price: float
    total_cost: float
    remarks: Optional[str] = None

class GRNItemInDB(GRNItemCreate):
    id: int
    grn_id: int

class GRNCreate(VoucherBase):
    purchase_order_id: int
    vendor_id: int
    grn_date: datetime
    challan_number: Optional[str] = None
    challan_date: Optional[datetime] = None
    transport_mode: Optional[str] = None
    vehicle_number: Optional[str] = None
    lr_rr_number: Optional[str] = None
    items: List[GRNItemCreate] = []

class GRNUpdate(BaseModel):
    purchase_order_id: Optional[int] = None
    vendor_id: Optional[int] = None
    grn_date: Optional[datetime] = None
    challan_number: Optional[str] = None
    challan_date: Optional[datetime] = None
    transport_mode: Optional[str] = None
    vehicle_number: Optional[str] = None
    lr_rr_number: Optional[str] = None
    total_amount: Optional[float] = None
    status: Optional[str] = None
    notes: Optional[str] = None
    items: Optional[List[GRNItemCreate]] = None

class GRNInDB(VoucherInDBBase):
    purchase_order_id: int
    vendor_id: int
    grn_date: datetime
    challan_number: Optional[str]
    challan_date: Optional[datetime]
    transport_mode: Optional[str]
    vehicle_number: Optional[str]
    lr_rr_number: Optional[str]
    items: List[GRNItemInDB]

class GRNAutoPopulateResponse(BaseModel):
    vendor_id: int
    purchase_order_id: int
    invoice_number: Optional[str] = None
    invoice_date: Optional[datetime] = None
    transport_mode: Optional[str] = None
    vehicle_number: Optional[str] = None
    lr_rr_number: Optional[str] = None
    items: List[PurchaseVoucherItemCreate]

# Delivery Challan
class DeliveryChallanItemCreate(SimpleVoucherItem):
    pass

class DeliveryChallanItemInDB(DeliveryChallanItemCreate):
    id: int
    delivery_challan_id: int

class DeliveryChallanCreate(VoucherBase):
    customer_id: int
    sales_order_id: Optional[int] = None
    delivery_date: Optional[datetime] = None
    transport_mode: Optional[str] = None
    vehicle_number: Optional[str] = None
    lr_rr_number: Optional[str] = None
    destination: Optional[str] = None
    items: List[DeliveryChallanItemCreate] = []

class DeliveryChallanUpdate(BaseModel):
    customer_id: Optional[int] = None
    sales_order_id: Optional[int] = None
    delivery_date: Optional[datetime] = None
    transport_mode: Optional[str] = None
    vehicle_number: Optional[str] = None
    lr_rr_number: Optional[str] = None
    destination: Optional[str] = None
    total_amount: Optional[float] = None
    status: Optional[str] = None
    notes: Optional[str] = None
    items: Optional[List[DeliveryChallanItemCreate]] = None

class DeliveryChallanInDB(VoucherInDBBase):
    customer_id: int
    sales_order_id: Optional[int]
    delivery_date: Optional[datetime]
    transport_mode: Optional[str]
    vehicle_number: Optional[str]
    lr_rr_number: Optional[str]
    destination: Optional[str]
    items: List[DeliveryChallanItemInDB]

class DeliveryChallanAutoPopulateResponse(BaseModel):
    customer_id: int
    sales_order_id: int
    delivery_date: Optional[datetime] = None
    transport_mode: Optional[str] = None
    vehicle_number: Optional[str] = None
    lr_rr_number: Optional[str] = None
    destination: Optional[str] = None
    items: List[SalesVoucherItemCreate]

# Proforma Invoice
class ProformaInvoiceItemCreate(VoucherItemWithTax):
    pass

class ProformaInvoiceItemInDB(ProformaInvoiceItemCreate):
    id: int
    proforma_invoice_id: int

class ProformaInvoiceCreate(VoucherBase):
    customer_id: int
    valid_until: Optional[datetime] = None
    payment_terms: Optional[str] = None
    terms_conditions: Optional[str] = None
    items: List[ProformaInvoiceItemCreate] = []

class ProformaInvoiceUpdate(BaseModel):
    customer_id: Optional[int] = None
    valid_until: Optional[datetime] = None
    payment_terms: Optional[str] = None
    terms_conditions: Optional[str] = None
    total_amount: Optional[float] = None
    cgst_amount: Optional[float] = None
    sgst_amount: Optional[float] = None
    igst_amount: Optional[float] = None
    discount_amount: Optional[float] = None
    status: Optional[str] = None
    notes: Optional[str] = None
    items: Optional[List[ProformaInvoiceItemCreate]] = None

class ProformaInvoiceInDB(VoucherInDBBase):
    customer_id: int
    valid_until: Optional[datetime]
    payment_terms: Optional[str]
    terms_conditions: Optional[str]
    items: List[ProformaInvoiceItemInDB]

# Quotation
class QuotationItemCreate(SimpleVoucherItem):
    pass

class QuotationItemInDB(QuotationItemCreate):
    id: int
    quotation_id: int

class QuotationCreate(VoucherBase):
    customer_id: int
    valid_until: Optional[datetime] = None
    payment_terms: Optional[str] = None
    terms_conditions: Optional[str] = None
    items: List[QuotationItemCreate] = []

class QuotationUpdate(BaseModel):
    customer_id: Optional[int] = None
    valid_until: Optional[datetime] = None
    payment_terms: Optional[str] = None
    terms_conditions: Optional[str] = None
    total_amount: Optional[float] = None
    status: Optional[str] = None
    notes: Optional[str] = None
    items: Optional[List[QuotationItemCreate]] = None

class QuotationInDB(VoucherInDBBase):
    customer_id: int
    valid_until: Optional[datetime]
    payment_terms: Optional[str]
    terms_conditions: Optional[str]
    items: List[QuotationItemInDB]

# Credit Note
class CreditNoteItemCreate(SimpleVoucherItem):
    pass

class CreditNoteItemInDB(CreditNoteItemCreate):
    id: int
    credit_note_id: int

class CreditNoteCreate(VoucherBase):
    customer_id: Optional[int] = None
    vendor_id: Optional[int] = None
    reference_voucher_type: Optional[str] = None
    reference_voucher_id: Optional[int] = None
    reason: str
    items: List[CreditNoteItemCreate] = []

class CreditNoteUpdate(BaseModel):
    customer_id: Optional[int] = None
    vendor_id: Optional[int] = None
    reference_voucher_type: Optional[str] = None
    reference_voucher_id: Optional[int] = None
    reason: Optional[str] = None
    total_amount: Optional[float] = None
    status: Optional[str] = None
    notes: Optional[str] = None
    items: Optional[List[CreditNoteItemCreate]] = None

class CreditNoteInDB(VoucherInDBBase):
    customer_id: Optional[int]
    vendor_id: Optional[int]
    reference_voucher_type: Optional[str]
    reference_voucher_id: Optional[int]
    reason: str
    items: List[CreditNoteItemInDB]

# Debit Note
class DebitNoteItemCreate(SimpleVoucherItem):
    pass

class DebitNoteItemInDB(DebitNoteItemCreate):
    id: int
    debit_note_id: int

class DebitNoteCreate(VoucherBase):
    customer_id: Optional[int] = None
    vendor_id: Optional[int] = None
    reference_voucher_type: Optional[str] = None
    reference_voucher_id: Optional[int] = None
    reason: str
    items: List[DebitNoteItemCreate] = []

class DebitNoteUpdate(BaseModel):
    customer_id: Optional[int] = None
    vendor_id: Optional[int] = None
    reference_voucher_type: Optional[str] = None
    reference_voucher_id: Optional[int] = None
    reason: Optional[str] = None
    total_amount: Optional[float] = None
    status: Optional[str] = None
    notes: Optional[str] = None
    items: Optional[List[DebitNoteItemCreate]] = None

class DebitNoteInDB(VoucherInDBBase):
    customer_id: Optional[int]
    vendor_id: Optional[int]
    reference_voucher_type: Optional[str]
    reference_voucher_id: Optional[int]
    reason: str
    items: List[DebitNoteItemInDB]

# Payment Voucher
class PaymentVoucherCreate(VoucherBase):
    vendor_id: int
    payment_method: Optional[str] = None
    reference: Optional[str] = None

class PaymentVoucherUpdate(BaseModel):
    vendor_id: Optional[int] = None
    payment_method: Optional[str] = None
    reference: Optional[str] = None
    total_amount: Optional[float] = None
    status: Optional[str] = None
    notes: Optional[str] = None

class PaymentVoucherInDB(VoucherInDBBase):
    vendor_id: int
    payment_method: Optional[str]
    reference: Optional[str]

# Receipt Voucher
class ReceiptVoucherCreate(VoucherBase):
    customer_id: int
    receipt_method: Optional[str] = None
    reference: Optional[str] = None

class ReceiptVoucherUpdate(BaseModel):
    customer_id: Optional[int] = None
    receipt_method: Optional[str] = None
    reference: Optional[str] = None
    total_amount: Optional[float] = None
    status: Optional[str] = None
    notes: Optional[str] = None

class ReceiptVoucherInDB(VoucherInDBBase):
    customer_id: int
    receipt_method: Optional[str]
    reference: Optional[str]

# Contra Voucher
class ContraVoucherCreate(VoucherBase):
    from_account: str
    to_account: str

class ContraVoucherUpdate(BaseModel):
    from_account: Optional[str] = None
    to_account: Optional[str] = None
    total_amount: Optional[float] = None
    status: Optional[str] = None
    notes: Optional[str] = None

class ContraVoucherInDB(VoucherInDBBase):
    from_account: str
    to_account: str

# Journal Voucher
class JournalVoucherCreate(VoucherBase):
    entries: str  # JSON string

class JournalVoucherUpdate(BaseModel):
    entries: Optional[str] = None
    total_amount: Optional[float] = None
    status: Optional[str] = None
    notes: Optional[str] = None

class JournalVoucherInDB(VoucherInDBBase):
    entries: str

# Inter Department Voucher
class InterDepartmentVoucherItemCreate(SimpleVoucherItem):
    pass

class InterDepartmentVoucherItemInDB(InterDepartmentVoucherItemCreate):
    id: int
    inter_department_voucher_id: int

class InterDepartmentVoucherCreate(VoucherBase):
    from_department: str
    to_department: str
    items: List[InterDepartmentVoucherItemCreate] = []

class InterDepartmentVoucherUpdate(BaseModel):
    from_department: Optional[str] = None
    to_department: Optional[str] = None
    total_amount: Optional[float] = None
    status: Optional[str] = None
    notes: Optional[str] = None
    items: Optional[List[InterDepartmentVoucherItemCreate]] = None

class InterDepartmentVoucherInDB(VoucherInDBBase):
    from_department: str
    to_department: str
    items: List[InterDepartmentVoucherItemInDB]

# Purchase Return
class PurchaseReturnItemCreate(VoucherItemWithTax):
    pass

class PurchaseReturnItemInDB(PurchaseReturnItemCreate):
    id: int
    purchase_return_id: int

class PurchaseReturnCreate(VoucherBase):
    vendor_id: int
    reference_voucher_id: Optional[int] = None
    reason: Optional[str] = None
    items: List[PurchaseReturnItemCreate] = []

class PurchaseReturnUpdate(BaseModel):
    vendor_id: Optional[int] = None
    reference_voucher_id: Optional[int] = None
    reason: Optional[str] = None
    total_amount: Optional[float] = None
    cgst_amount: Optional[float] = None
    sgst_amount: Optional[float] = None
    igst_amount: Optional[float] = None
    discount_amount: Optional[float] = None
    status: Optional[str] = None
    notes: Optional[str] = None
    items: Optional[List[PurchaseReturnItemCreate]] = None

class PurchaseReturnInDB(VoucherInDBBase):
    vendor_id: int
    reference_voucher_id: Optional[int]
    reason: Optional[str]
    items: List[PurchaseReturnItemInDB]

# Sales Return
class SalesReturnItemCreate(VoucherItemWithTax):
    pass

class SalesReturnItemInDB(SalesReturnItemCreate):
    id: int
    sales_return_id: int

class SalesReturnCreate(VoucherBase):
    customer_id: int
    reference_voucher_id: Optional[int] = None
    reason: Optional[str] = None
    items: List[SalesReturnItemCreate] = []

class SalesReturnUpdate(BaseModel):
    customer_id: Optional[int] = None
    reference_voucher_id: Optional[int] = None
    reason: Optional[str] = None
    total_amount: Optional[float] = None
    cgst_amount: Optional[float] = None
    sgst_amount: Optional[float] = None
    igst_amount: Optional[float] = None
    discount_amount: Optional[float] = None
    status: Optional[str] = None
    notes: Optional[str] = None
    items: Optional[List[SalesReturnItemCreate]] = None

class SalesReturnInDB(VoucherInDBBase):
    customer_id: int
    reference_voucher_id: Optional[int]
    reason: Optional[str]
    items: List[SalesReturnItemInDB]