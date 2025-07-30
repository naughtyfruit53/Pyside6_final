"""
Excel import utilities with enhanced validation and error handling
"""
import io
import pandas as pd
from typing import List, Dict, Any, Optional, Tuple
from fastapi import UploadFile, HTTPException
import logging

logger = logging.getLogger(__name__)

class ExcelImportError(Exception):
    """Custom exception for Excel import errors"""
    def __init__(self, message: str, row: int = None, field: str = None):
        self.message = message
        self.row = row
        self.field = field
        super().__init__(self.message)

class ExcelImportValidator:
    """Utility class for validating Excel import data"""
    
    @staticmethod
    def validate_required_columns(df: pd.DataFrame, required_columns: List[str]) -> List[str]:
        """
        Validate that all required columns are present in the DataFrame
        
        Args:
            df: DataFrame to validate
            required_columns: List of required column names
            
        Returns:
            List of missing column names
        """
        # Normalize column names (lowercase, strip spaces, replace spaces with underscores)
        df_columns = [col.lower().strip().replace(' ', '_') for col in df.columns]
        normalized_required = [col.lower().strip().replace(' ', '_') for col in required_columns]
        
        missing_columns = []
        for req_col in normalized_required:
            if req_col not in df_columns:
                # Find the original column name for the error
                original_name = required_columns[normalized_required.index(req_col)]
                missing_columns.append(original_name)
        
        return missing_columns
    
    @staticmethod
    def validate_data_types(df: pd.DataFrame, column_types: Dict[str, type]) -> List[Tuple[int, str, str]]:
        """
        Validate data types in DataFrame columns
        
        Args:
            df: DataFrame to validate
            column_types: Dictionary mapping column names to expected types
            
        Returns:
            List of tuples (row_index, column_name, error_message)
        """
        errors = []
        
        for col_name, expected_type in column_types.items():
            if col_name not in df.columns:
                continue
                
            for idx, value in enumerate(df[col_name]):
                if pd.isna(value):
                    continue
                    
                try:
                    if expected_type == float:
                        float(value)
                    elif expected_type == int:
                        int(value)
                    elif expected_type == str:
                        str(value)
                except (ValueError, TypeError):
                    errors.append((idx + 1, col_name, f"Expected {expected_type.__name__}, got {type(value).__name__}"))
        
        return errors
    
    @staticmethod
    def clean_dataframe(df: pd.DataFrame) -> pd.DataFrame:
        """
        Clean DataFrame by removing empty rows and normalizing column names
        
        Args:
            df: DataFrame to clean
            
        Returns:
            Cleaned DataFrame
        """
        # Remove completely empty rows
        df = df.dropna(how='all')
        
        # Normalize column names
        df.columns = df.columns.str.strip().str.lower().str.replace(' ', '_')
        
        # Clean string values
        for col in df.select_dtypes(include=['object']).columns:
            df[col] = df[col].astype(str).str.strip()
            df[col] = df[col].replace('nan', None)
            df[col] = df[col].replace('', None)
        
        return df

class StockExcelImporter:
    """Specialized Excel importer for stock data"""
    
    REQUIRED_COLUMNS = ["Product Name", "Unit", "Quantity"]
    OPTIONAL_COLUMNS = ["HSN Code", "Part Number", "Unit Price", "GST Rate", "Reorder Level", "Location"]
    
    COLUMN_TYPES = {
        "quantity": float,
        "unit_price": float,
        "gst_rate": float,
        "reorder_level": int
    }
    
    @classmethod
    async def import_from_file(cls, file: UploadFile) -> Tuple[List[Dict[str, Any]], List[str]]:
        """
        Import stock data from Excel file with comprehensive validation
        
        Args:
            file: Uploaded Excel file
            
        Returns:
            Tuple of (records, errors)
            
        Raises:
            HTTPException: For critical import errors
        """
        errors = []
        
        # Validate file type
        if not file.filename.endswith(('.xlsx', '.xls')):
            raise HTTPException(
                status_code=400,
                detail="Invalid file type. Only Excel files (.xlsx, .xls) are allowed."
            )
        
        try:
            # Read file content
            content = await file.read()
            
            # Parse Excel file
            try:
                df = pd.read_excel(io.BytesIO(content))
            except Exception as e:
                raise HTTPException(
                    status_code=400,
                    detail=f"Failed to parse Excel file: {str(e)}"
                )
            
            # Check if file is empty
            if df.empty:
                raise HTTPException(
                    status_code=400,
                    detail="Excel file is empty or contains no data."
                )
            
            # Clean the DataFrame
            df = ExcelImportValidator.clean_dataframe(df)
            
            # Validate required columns
            missing_columns = ExcelImportValidator.validate_required_columns(df, cls.REQUIRED_COLUMNS)
            if missing_columns:
                raise HTTPException(
                    status_code=400,
                    detail=f"Missing required columns: {', '.join(missing_columns)}"
                )
            
            # Validate data types
            type_errors = ExcelImportValidator.validate_data_types(df, cls.COLUMN_TYPES)
            for row, col, error in type_errors:
                errors.append(f"Row {row}: {col} - {error}")
            
            # Convert to records
            records = []
            for idx, row in df.iterrows():
                try:
                    record = cls._process_row(row, idx + 1)
                    records.append(record)
                except ExcelImportError as e:
                    errors.append(f"Row {e.row}: {e.message}")
                except Exception as e:
                    errors.append(f"Row {idx + 1}: Unexpected error - {str(e)}")
            
            return records, errors
            
        except HTTPException:
            raise
        except Exception as e:
            logger.error(f"Unexpected error during Excel import: {str(e)}")
            raise HTTPException(
                status_code=500,
                detail=f"Internal error during file processing: {str(e)}"
            )
    
    @classmethod
    def _process_row(cls, row: pd.Series, row_number: int) -> Dict[str, Any]:
        """
        Process a single row of Excel data
        
        Args:
            row: Pandas Series representing a row
            row_number: Row number for error reporting
            
        Returns:
            Dictionary of processed data
            
        Raises:
            ExcelImportError: For row-specific validation errors
        """
        record = {}
        
        # Required fields
        product_name = row.get('product_name')
        if not product_name or pd.isna(product_name) or str(product_name).strip() == '':
            raise ExcelImportError("Product Name is required and cannot be empty", row_number, "product_name")
        record['product_name'] = str(product_name).strip()
        
        unit = row.get('unit')
        if not unit or pd.isna(unit) or str(unit).strip() == '':
            raise ExcelImportError("Unit is required and cannot be empty", row_number, "unit")
        record['unit'] = str(unit).strip().upper()
        
        # Quantity validation
        quantity = row.get('quantity')
        if pd.isna(quantity):
            record['quantity'] = 0.0
        else:
            try:
                quantity_val = float(quantity)
                if quantity_val < 0:
                    raise ExcelImportError("Quantity cannot be negative", row_number, "quantity")
                record['quantity'] = quantity_val
            except (ValueError, TypeError):
                raise ExcelImportError(f"Invalid quantity value: {quantity}", row_number, "quantity")
        
        # Optional fields with validation
        optional_fields = {
            'hsn_code': str,
            'part_number': str,
            'location': str
        }
        
        for field, field_type in optional_fields.items():
            value = row.get(field)
            if not pd.isna(value) and str(value).strip() != '' and str(value).strip().lower() != 'nan':
                record[field] = field_type(value).strip()
            else:
                record[field] = None
        
        # Numeric optional fields
        numeric_fields = {
            'unit_price': (float, 0.0),
            'gst_rate': (float, 18.0),
            'reorder_level': (int, 10)
        }
        
        for field, (field_type, default_value) in numeric_fields.items():
            value = row.get(field)
            if pd.isna(value) or str(value).strip() == '' or str(value).strip().lower() == 'nan':
                record[field] = default_value
            else:
                try:
                    parsed_value = field_type(value)
                    if field in ['unit_price', 'gst_rate'] and parsed_value < 0:
                        raise ExcelImportError(f"{field} cannot be negative", row_number, field)
                    if field == 'gst_rate' and parsed_value > 100:
                        raise ExcelImportError("GST rate cannot exceed 100%", row_number, field)
                    record[field] = parsed_value
                except (ValueError, TypeError):
                    raise ExcelImportError(f"Invalid {field} value: {value}", row_number, field)
        
        return record

class CompanyExcelImporter:
    """Specialized Excel importer for company data"""
    
    REQUIRED_COLUMNS = ["Name", "Address1", "City", "State", "Pin Code", "State Code", "Contact Number"]
    OPTIONAL_COLUMNS = ["Address2", "GST Number", "PAN Number", "Email"]
    
    @classmethod
    async def import_from_file(cls, file: UploadFile) -> Tuple[List[Dict[str, Any]], List[str]]:
        """
        Import company data from Excel file
        
        Args:
            file: Uploaded Excel file
            
        Returns:
            Tuple of (records, errors)
        """
        errors = []
        
        # Similar implementation to StockExcelImporter but for company data
        # This would include company-specific validation rules
        
        # Placeholder implementation
        raise NotImplementedError("Company Excel import not yet implemented")

def validate_excel_file_type(filename: str) -> bool:
    """
    Validate that the file is an Excel file
    
    Args:
        filename: Name of the file
        
    Returns:
        True if valid Excel file, False otherwise
    """
    return filename.lower().endswith(('.xlsx', '.xls'))

def get_excel_template_data(entity_type: str) -> List[Dict[str, Any]]:
    """
    Get template data for Excel file generation
    
    Args:
        entity_type: Type of entity (stock, company, etc.)
        
    Returns:
        List of dictionaries representing template data
    """
    templates = {
        'stock': [
            {
                'Product Name': 'Sample Product 1',
                'HSN Code': '12345678',
                'Part Number': 'SP001',
                'Unit': 'PCS',
                'Unit Price': 100.00,
                'GST Rate': 18.0,
                'Reorder Level': 50,
                'Quantity': 100,
                'Location': 'Warehouse A'
            }
        ],
        'company': [
            {
                'Name': 'Sample Company Ltd',
                'Address1': '123 Business Street',
                'Address2': 'Business District',
                'City': 'Mumbai',
                'State': 'Maharashtra',
                'Pin Code': '400001',
                'State Code': '27',
                'Contact Number': '+91 9876543210',
                'Email': 'contact@sample.com',
                'GST Number': '27ABCDE1234F1Z5',
                'PAN Number': 'ABCDE1234F'
            }
        ]
    }
    
    return templates.get(entity_type, [])