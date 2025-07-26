from pydantic import BaseModel, EmailStr, validator
from typing import Optional, List
from datetime import datetime
from enum import Enum

# Base voucher schemas
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

# Purchase Voucher schemas
class PurchaseVoucherItemCreate(VoucherItemWithTax):
    pass

class PurchaseVoucherItemInDB(VoucherItemWithTax):
    id: int
    purchase_voucher_id: int
    
    class Config:
        orm_mode = True

class PurchaseVoucherBase(VoucherBase):
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

class PurchaseVoucherCreate(PurchaseVoucherBase):
    items: List[PurchaseVoucherItemCreate] = []

class PurchaseVoucherUpdate(BaseModel):
    vendor_id: Optional[int] = None
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

class PurchaseVoucherInDB(PurchaseVoucherBase):
    id: int
    created_by: int
    created_at: datetime
    updated_at: Optional[datetime] = None
    items: List[PurchaseVoucherItemInDB] = []
    
    class Config:
        orm_mode = True

# Sales Voucher schemas
class SalesVoucherItemCreate(VoucherItemWithTax):
    pass

class SalesVoucherItemInDB(VoucherItemWithTax):
    id: int
    sales_voucher_id: int
    
    class Config:
        orm_mode = True

class SalesVoucherBase(VoucherBase):
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

class SalesVoucherCreate(SalesVoucherBase):
    items: List[SalesVoucherItemCreate] = []

class SalesVoucherUpdate(BaseModel):
    customer_id: Optional[int] = None
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

class SalesVoucherInDB(SalesVoucherBase):
    id: int
    created_by: int
    created_at: datetime
    updated_at: Optional[datetime] = None
    items: List[SalesVoucherItemInDB] = []
    
    class Config:
        orm_mode = True

# Purchase Order schemas
class PurchaseOrderItemCreate(VoucherItemBase):
    total_amount: float
    pending_quantity: Optional[float] = None

class PurchaseOrderItemInDB(VoucherItemBase):
    id: int
    purchase_order_id: int
    total_amount: float
    delivered_quantity: float = 0.0
    pending_quantity: float
    
    class Config:
        orm_mode = True

class PurchaseOrderBase(VoucherBase):
    vendor_id: int
    delivery_date: Optional[datetime] = None
    payment_terms: Optional[str] = None
    terms_conditions: Optional[str] = None

class PurchaseOrderCreate(PurchaseOrderBase):
    items: List[PurchaseOrderItemCreate] = []

class PurchaseOrderUpdate(BaseModel):
    vendor_id: Optional[int] = None
    delivery_date: Optional[datetime] = None
    payment_terms: Optional[str] = None
    terms_conditions: Optional[str] = None
    total_amount: Optional[float] = None
    status: Optional[str] = None
    notes: Optional[str] = None

class PurchaseOrderInDB(PurchaseOrderBase):
    id: int
    created_by: int
    created_at: datetime
    updated_at: Optional[datetime] = None
    items: List[PurchaseOrderItemInDB] = []
    
    class Config:
        orm_mode = True

# Sales Order schemas
class SalesOrderItemCreate(VoucherItemBase):
    total_amount: float
    pending_quantity: Optional[float] = None

class SalesOrderItemInDB(VoucherItemBase):
    id: int
    sales_order_id: int
    total_amount: float
    delivered_quantity: float = 0.0
    pending_quantity: float
    
    class Config:
        orm_mode = True

class SalesOrderBase(VoucherBase):
    customer_id: int
    delivery_date: Optional[datetime] = None
    payment_terms: Optional[str] = None
    terms_conditions: Optional[str] = None

class SalesOrderCreate(SalesOrderBase):
    items: List[SalesOrderItemCreate] = []

class SalesOrderUpdate(BaseModel):
    customer_id: Optional[int] = None
    delivery_date: Optional[datetime] = None
    payment_terms: Optional[str] = None
    terms_conditions: Optional[str] = None
    total_amount: Optional[float] = None
    status: Optional[str] = None
    notes: Optional[str] = None

class SalesOrderInDB(SalesOrderBase):
    id: int
    created_by: int
    created_at: datetime
    updated_at: Optional[datetime] = None
    items: List[SalesOrderItemInDB] = []
    
    class Config:
        orm_mode = True

# GRN schemas
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
    
    class Config:
        orm_mode = True

class GRNBase(VoucherBase):
    purchase_order_id: int
    vendor_id: int
    grn_date: datetime
    challan_number: Optional[str] = None
    challan_date: Optional[datetime] = None
    transport_mode: Optional[str] = None
    vehicle_number: Optional[str] = None
    lr_rr_number: Optional[str] = None

class GRNCreate(GRNBase):
    items: List[GRNItemCreate] = []

class GRNUpdate(BaseModel):
    grn_date: Optional[datetime] = None
    challan_number: Optional[str] = None
    challan_date: Optional[datetime] = None
    transport_mode: Optional[str] = None
    vehicle_number: Optional[str] = None
    lr_rr_number: Optional[str] = None
    total_amount: Optional[float] = None
    status: Optional[str] = None
    notes: Optional[str] = None

class GRNInDB(GRNBase):
    id: int
    created_by: int
    created_at: datetime
    updated_at: Optional[datetime] = None
    items: List[GRNItemInDB] = []
    
    class Config:
        orm_mode = True

# Delivery Challan schemas
class DeliveryChallanItemCreate(VoucherItemBase):
    total_amount: float

class DeliveryChallanItemInDB(DeliveryChallanItemCreate):
    id: int
    delivery_challan_id: int
    
    class Config:
        orm_mode = True

class DeliveryChallanBase(VoucherBase):
    customer_id: int
    sales_order_id: Optional[int] = None
    delivery_date: Optional[datetime] = None
    transport_mode: Optional[str] = None
    vehicle_number: Optional[str] = None
    lr_rr_number: Optional[str] = None
    destination: Optional[str] = None

class DeliveryChallanCreate(DeliveryChallanBase):
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

class DeliveryChallanInDB(DeliveryChallanBase):
    id: int
    created_by: int
    created_at: datetime
    updated_at: Optional[datetime] = None
    items: List[DeliveryChallanItemInDB] = []
    
    class Config:
        orm_mode = True

# Proforma Invoice schemas
class ProformaInvoiceItemCreate(VoucherItemWithTax):
    pass

class ProformaInvoiceItemInDB(VoucherItemWithTax):
    id: int
    proforma_invoice_id: int
    
    class Config:
        orm_mode = True

class ProformaInvoiceBase(VoucherBase):
    customer_id: int
    valid_until: Optional[datetime] = None
    payment_terms: Optional[str] = None
    terms_conditions: Optional[str] = None

class ProformaInvoiceCreate(ProformaInvoiceBase):
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

class ProformaInvoiceInDB(ProformaInvoiceBase):
    id: int
    created_by: int
    created_at: datetime
    updated_at: Optional[datetime] = None
    items: List[ProformaInvoiceItemInDB] = []
    
    class Config:
        orm_mode = True

# Quotation schemas
class QuotationItemCreate(VoucherItemBase):
    total_amount: float

class QuotationItemInDB(QuotationItemCreate):
    id: int
    quotation_id: int
    
    class Config:
        orm_mode = True

class QuotationBase(VoucherBase):
    customer_id: int
    valid_until: Optional[datetime] = None
    payment_terms: Optional[str] = None
    terms_conditions: Optional[str] = None

class QuotationCreate(QuotationBase):
    items: List[QuotationItemCreate] = []

class QuotationUpdate(BaseModel):
    customer_id: Optional[int] = None
    valid_until: Optional[datetime] = None
    payment_terms: Optional[str] = None
    terms_conditions: Optional[str] = None
    total_amount: Optional[float] = None
    status: Optional[str] = None
    notes: Optional[str] = None

class QuotationInDB(QuotationBase):
    id: int
    created_by: int
    created_at: datetime
    updated_at: Optional[datetime] = None
    items: List[QuotationItemInDB] = []
    
    class Config:
        orm_mode = True