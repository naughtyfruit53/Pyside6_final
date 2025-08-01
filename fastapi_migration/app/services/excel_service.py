"""
Excel service for handling import/export operations for all entities.
Provides reusable functions for parsing Excel files, creating templates, and exporting data.
"""

import io
import pandas as pd
from typing import List, Dict, Any, Tuple, Optional
from sqlalchemy.orm import Session
from openpyxl import Workbook
from openpyxl.styles import Font, PatternFill, Alignment
from fastapi import UploadFile, HTTPException
from fastapi.responses import StreamingResponse
import logging

logger = logging.getLogger(__name__)

class ExcelService:
    """Service class for Excel operations"""
    
    @staticmethod
    def create_streaming_response(excel_data: bytes, filename: str) -> StreamingResponse:
        """Create a streaming response for Excel file download"""
        return StreamingResponse(
            io.BytesIO(excel_data),
            media_type="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
            headers={"Content-Disposition": f"attachment; filename={filename}"}
        )
    
    @staticmethod
    async def parse_excel_file(file: UploadFile, expected_columns: List[str] = None) -> List[Dict[str, Any]]:
        """
        Parse uploaded Excel file and return list of dictionaries
        """
        try:
            # Read file content
            content = await file.read()
            
            # Try to read as Excel file
            try:
                df = pd.read_excel(io.BytesIO(content))
            except Exception as e:
                raise HTTPException(status_code=400, detail=f"Invalid Excel file format: {str(e)}")
            
            # Check if file is empty
            if df.empty:
                raise HTTPException(status_code=400, detail="Excel file is empty")
            
            # Clean column names (strip whitespace, normalize)
            df.columns = df.columns.str.strip().str.lower().str.replace(' ', '_')
            
            # Validate expected columns if provided
            if expected_columns:
                normalized_expected = [col.lower().replace(' ', '_') for col in expected_columns]
                missing_cols = set(normalized_expected) - set(df.columns)
                if missing_cols:
                    raise HTTPException(
                        status_code=400, 
                        detail=f"Missing required columns: {', '.join(missing_cols)}"
                    )
            
            # Convert to list of dictionaries, handling NaN values
            records = df.replace({pd.NA: None, float('nan'): None}).to_dict('records')
            
            # Clean up records - remove empty rows
            cleaned_records = []
            for record in records:
                # Skip rows where all values are empty/None
                if any(value is not None and str(value).strip() for value in record.values()):
                    # Clean values
                    cleaned_record = {}
                    for key, value in record.items():
                        if value is None or (isinstance(value, str) and not value.strip()):
                            cleaned_record[key] = None
                        elif isinstance(value, str):
                            cleaned_record[key] = value.strip()
                        else:
                            cleaned_record[key] = value
                    cleaned_records.append(cleaned_record)
            
            return cleaned_records
            
        except HTTPException:
            raise
        except Exception as e:
            logger.error(f"Error parsing Excel file: {str(e)}")
            raise HTTPException(status_code=500, detail=f"Error processing Excel file: {str(e)}")
    
    @staticmethod
    def create_template_excel(columns: List[Dict[str, Any]], filename: str) -> bytes:
        """
        Create Excel template with specified columns and formatting
        columns format: [{"name": "Column Name", "example": "Example Value", "width": 15}]
        """
        wb = Workbook()
        ws = wb.active
        ws.title = "Template"
        
        # Header style
        header_font = Font(bold=True, color="FFFFFF")
        header_fill = PatternFill(start_color="366092", end_color="366092", fill_type="solid")
        header_alignment = Alignment(horizontal="center", vertical="center")
        
        # Add headers
        for col_idx, col_info in enumerate(columns, 1):
            cell = ws.cell(row=1, column=col_idx, value=col_info["name"])
            cell.font = header_font
            cell.fill = header_fill
            cell.alignment = header_alignment
            
            # Set column width
            column_letter = chr(64 + col_idx)  # A, B, C, etc.
            ws.column_dimensions[column_letter].width = col_info.get("width", 15)
        
        # Add example row
        for col_idx, col_info in enumerate(columns, 1):
            example_value = col_info.get("example", "")
            ws.cell(row=2, column=col_idx, value=example_value)
        
        # Save to bytes
        excel_buffer = io.BytesIO()
        wb.save(excel_buffer)
        excel_buffer.seek(0)
        return excel_buffer.getvalue()
    
    @staticmethod
    def export_data_to_excel(data: List[Dict[str, Any]], columns: List[Dict[str, Any]], filename: str) -> bytes:
        """
        Export data to Excel with formatting
        """
        wb = Workbook()
        ws = wb.active
        ws.title = "Data"
        
        # Header style
        header_font = Font(bold=True, color="FFFFFF")
        header_fill = PatternFill(start_color="366092", end_color="366092", fill_type="solid")
        header_alignment = Alignment(horizontal="center", vertical="center")
        
        # Add headers
        for col_idx, col_info in enumerate(columns, 1):
            cell = ws.cell(row=1, column=col_idx, value=col_info["name"])
            cell.font = header_font
            cell.fill = header_fill
            cell.alignment = header_alignment
            
            # Set column width
            column_letter = chr(64 + col_idx)
            ws.column_dimensions[column_letter].width = col_info.get("width", 15)
        
        # Add data rows
        for row_idx, record in enumerate(data, 2):
            for col_idx, col_info in enumerate(columns, 1):
                field_name = col_info.get("field", col_info["name"].lower().replace(" ", "_"))
                value = record.get(field_name, "")
                ws.cell(row=row_idx, column=col_idx, value=value)
        
        # Save to bytes
        excel_buffer = io.BytesIO()
        wb.save(excel_buffer)
        excel_buffer.seek(0)
        return excel_buffer.getvalue()

class ProductExcelService:
    """Excel service specifically for Products"""
    
    COLUMNS = [
        {"name": "Product Name", "field": "product_name", "example": "Steel Bolt M8x50", "width": 20},
        {"name": "HSN Code", "field": "hsn_code", "example": "73181590", "width": 12},
        {"name": "Part Number", "field": "part_number", "example": "SB-M8-50", "width": 15},
        {"name": "Unit", "field": "unit", "example": "PCS", "width": 10},
        {"name": "Unit Price", "field": "unit_price", "example": "25.50", "width": 12},
        {"name": "GST Rate", "field": "gst_rate", "example": "18.0", "width": 12},
        {"name": "Is GST Inclusive", "field": "is_gst_inclusive", "example": "FALSE", "width": 15},
        {"name": "Reorder Level", "field": "reorder_level", "example": "50", "width": 15},
        {"name": "Description", "field": "description", "example": "High quality steel bolt", "width": 25},
        {"name": "Is Manufactured", "field": "is_manufactured", "example": "FALSE", "width": 15},
        {"name": "Initial Quantity", "field": "initial_quantity", "example": "100", "width": 15},
        {"name": "Initial Location", "field": "initial_location", "example": "Warehouse A", "width": 15},
    ]
    
    REQUIRED_COLUMNS = ["Product Name", "Unit", "Unit Price"]
    
    @staticmethod
    def create_template() -> bytes:
        return ExcelService.create_template_excel(ProductExcelService.COLUMNS, "products_template.xlsx")
    
    @staticmethod
    def export_products(products: List[Dict[str, Any]]) -> bytes:
        return ExcelService.export_data_to_excel(products, ProductExcelService.COLUMNS, "products_export.xlsx")

class VendorExcelService:
    """Excel service specifically for Vendors"""
    
    COLUMNS = [
        {"name": "Name", "field": "name", "example": "ABC Suppliers Pvt Ltd", "width": 25},
        {"name": "Contact Number", "field": "contact_number", "example": "+91 9876543210", "width": 18},
        {"name": "Email", "field": "email", "example": "contact@abcsuppliers.com", "width": 25},
        {"name": "Address Line 1", "field": "address1", "example": "123 Industrial Area", "width": 25},
        {"name": "Address Line 2", "field": "address2", "example": "Sector 5", "width": 20},
        {"name": "City", "field": "city", "example": "Mumbai", "width": 15},
        {"name": "State", "field": "state", "example": "Maharashtra", "width": 15},
        {"name": "Pin Code", "field": "pin_code", "example": "400001", "width": 12},
        {"name": "State Code", "field": "state_code", "example": "27", "width": 12},
        {"name": "GST Number", "field": "gst_number", "example": "27ABCCS1234A1Z5", "width": 18},
        {"name": "PAN Number", "field": "pan_number", "example": "ABCCS1234A", "width": 15},
    ]
    
    REQUIRED_COLUMNS = ["Name", "Contact Number", "Address Line 1", "City", "State", "Pin Code", "State Code"]
    
    @staticmethod
    def create_template() -> bytes:
        return ExcelService.create_template_excel(VendorExcelService.COLUMNS, "vendors_template.xlsx")
    
    @staticmethod
    def export_vendors(vendors: List[Dict[str, Any]]) -> bytes:
        return ExcelService.export_data_to_excel(vendors, VendorExcelService.COLUMNS, "vendors_export.xlsx")

class CustomerExcelService:
    """Excel service specifically for Customers"""
    
    COLUMNS = [
        {"name": "Name", "field": "name", "example": "XYZ Manufacturing Ltd", "width": 25},
        {"name": "Contact Number", "field": "contact_number", "example": "+91 9876543210", "width": 18},
        {"name": "Email", "field": "email", "example": "orders@xyzmanuf.com", "width": 25},
        {"name": "Address Line 1", "field": "address1", "example": "456 Business Park", "width": 25},
        {"name": "Address Line 2", "field": "address2", "example": "Phase 2", "width": 20},
        {"name": "City", "field": "city", "example": "Delhi", "width": 15},
        {"name": "State", "field": "state", "example": "Delhi", "width": 15},
        {"name": "Pin Code", "field": "pin_code", "example": "110001", "width": 12},
        {"name": "State Code", "field": "state_code", "example": "07", "width": 12},
        {"name": "GST Number", "field": "gst_number", "example": "07XYZCS1234B1Z6", "width": 18},
        {"name": "PAN Number", "field": "pan_number", "example": "XYZCS1234B", "width": 15},
    ]
    
    REQUIRED_COLUMNS = ["Name", "Contact Number", "Address Line 1", "City", "State", "Pin Code", "State Code"]
    
    @staticmethod
    def create_template() -> bytes:
        return ExcelService.create_template_excel(CustomerExcelService.COLUMNS, "customers_template.xlsx")
    
    @staticmethod
    def export_customers(customers: List[Dict[str, Any]]) -> bytes:
        return ExcelService.export_data_to_excel(customers, CustomerExcelService.COLUMNS, "customers_export.xlsx")

class StockExcelService:
    """Excel service specifically for Stock/Inventory"""
    
    COLUMNS = [
        {"name": "Product Name", "field": "product_name", "example": "Steel Bolt M8x50", "width": 25},
        {"name": "Quantity", "field": "quantity", "example": "100", "width": 12},
        {"name": "Unit", "field": "unit", "example": "PCS", "width": 10},
        {"name": "HSN Code", "field": "hsn_code", "example": "73181590", "width": 12},
        {"name": "Part Number", "field": "part_number", "example": "SB-M8-50", "width": 15},
        {"name": "Unit Price", "field": "unit_price", "example": "25.50", "width": 12},
        {"name": "GST Rate", "field": "gst_rate", "example": "18.0", "width": 12},
        {"name": "Reorder Level", "field": "reorder_level", "example": "50", "width": 15},
        {"name": "Location", "field": "location", "example": "Warehouse A-1", "width": 18},
    ]
    
    REQUIRED_COLUMNS = ["Product Name", "Unit", "Quantity"]
    
    @staticmethod
    def create_template() -> bytes:
        return ExcelService.create_template_excel(StockExcelService.COLUMNS, "stock_template.xlsx")
    
    @staticmethod
    def export_stock(stock_items: List[Dict[str, Any]]) -> bytes:
        return ExcelService.export_data_to_excel(stock_items, StockExcelService.COLUMNS, "stock_export.xlsx")