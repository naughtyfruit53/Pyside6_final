# Excel Import/Export Enhancements

## Overview

The Excel import/export functionality has been enhanced with robust validation, error handling, and user feedback mechanisms. This document outlines the improvements and provides usage guidelines.

## Enhanced Features

### 1. Comprehensive Column Mapping

**Automatic Column Normalization:**
- Column names are automatically normalized (lowercase, spaces to underscores)
- Case-insensitive matching for flexible Excel headers
- Supports variations like "Product Name", "product_name", "Product_Name"

**Missing Column Detection:**
- Clear error messages for required missing columns
- Validation occurs before processing any data
- Returns specific list of missing columns

### 2. Advanced Data Validation

**Row-by-Row Validation:**
- Each row is validated independently
- Processing continues even if individual rows fail
- Detailed error tracking with row numbers and field names

**Data Type Validation:**
- Automatic type conversion with error handling
- Validates numeric fields (quantities, prices, rates)
- Email format validation where applicable
- GST number format checking

**Business Logic Validation:**
- Negative quantity/price validation
- GST rate bounds checking (0-100%)
- Required field presence validation
- Logical consistency checks

### 3. Enhanced Error Reporting

**Detailed Error Structure:**
```json
{
  "total_processed": 10,
  "successful": 8,
  "failed": 2,
  "errors": [
    {
      "row": 5,
      "field": "unit_price",
      "value": "-10.50",
      "error": "Unit price cannot be negative",
      "error_code": "NEGATIVE_VALUE"
    }
  ],
  "warnings": [
    "Row 3: GST rate not provided, using default 18%"
  ],
  "message": "8 products created successfully, 2 errors encountered"
}
```

**Error Categories:**
- `REQUIRED_FIELD_MISSING` - Required field is empty
- `INVALID_DATA_TYPE` - Data type conversion failed  
- `NEGATIVE_VALUE` - Negative value in positive-only field
- `INVALID_RANGE` - Value outside acceptable range
- `DUPLICATE_ENTRY` - Duplicate record detected
- `BUSINESS_LOGIC_ERROR` - Violates business rules

### 4. Automatic Product Creation

**Smart Product Handling:**
- Automatically creates products during stock import if they don't exist
- Extracts product information from stock data
- Maintains referential integrity
- Reports both product and stock creation counts

**Product Auto-Creation Logic:**
```python
# When importing stock, if product doesn't exist:
product = Product(
    organization_id=org_id,
    name=record["product_name"],
    unit=record["unit"],
    unit_price=record.get("unit_price", 0.0),
    gst_rate=record.get("gst_rate", 18.0),
    hsn_code=record.get("hsn_code"),
    part_number=record.get("part_number"),
    is_active=True
)
```

### 5. Robust File Processing

**File Validation:**
- Validates file extension (.xlsx, .xls)
- Checks file size limits
- Verifies file is not corrupted
- Handles empty files gracefully

**Memory Efficient Processing:**
- Streams large files without loading entirely into memory
- Processes rows incrementally
- Proper resource cleanup

## API Endpoints

### Stock Import/Export

| Method | Endpoint | Description |
|--------|----------|-------------|
| POST | `/api/v1/stock/import/excel` | Import stock from Excel |
| POST | `/api/v1/stock/bulk` | Bulk import (alias) |
| GET | `/api/v1/stock/template/excel` | Download template |
| GET | `/api/v1/stock/export/excel` | Export stock to Excel |

### Products Import/Export

| Method | Endpoint | Description |
|--------|----------|-------------|
| POST | `/api/v1/products/import/excel` | Import products from Excel |
| GET | `/api/v1/products/template/excel` | Download template |
| GET | `/api/v1/products/export/excel` | Export products to Excel |

### Vendors/Customers Import/Export

Similar patterns available for vendors and customers with respective endpoints.

## Excel Template Structure

### Stock Import Template

| Column | Required | Type | Example | Notes |
|--------|----------|------|---------|--------|
| Product Name | Yes | String | "Steel Bolt M8x50" | Product identifier |
| Unit | Yes | String | "PCS" | Unit of measurement |
| Quantity | Yes | Number | 100 | Stock quantity |
| HSN Code | No | String | "73181590" | Tax classification |
| Part Number | No | String | "SB-M8-50" | Internal part number |
| Unit Price | No | Number | 25.50 | Price per unit |
| GST Rate | No | Number | 18.0 | GST percentage (0-100) |
| Reorder Level | No | Integer | 50 | Minimum stock level |
| Location | No | String | "Warehouse A-1" | Storage location |

### Advanced Features in Templates

**Auto-Formatting:**
- Headers are formatted with colors and fonts
- Column widths are auto-adjusted
- Example data row included
- Data validation rules embedded

**Helper Features:**
- Dropdown lists for common values
- Conditional formatting for validation
- Protected header rows
- Comments with field descriptions

## Usage Examples

### 1. Stock Import with Error Handling

```python
import requests

# Prepare Excel file
files = {
    'file': ('stock_data.xlsx', open('stock_data.xlsx', 'rb'), 
             'application/vnd.openxmlformats-officedocument.spreadsheetml.sheet')
}

headers = {'Authorization': f'Bearer {token}'}

response = requests.post(
    'http://localhost:8000/api/v1/stock/import/excel',
    files=files,
    headers=headers
)

if response.status_code == 200:
    result = response.json()
    print(f"Success: {result['successful']} records processed")
    print(f"Failed: {result['failed']} records had errors")
    
    if result['errors']:
        print("Errors encountered:")
        for error in result['errors']:
            print(f"  Row {error['row']}: {error['error']}")
            
    if result['warnings']:
        print("Warnings:")
        for warning in result['warnings']:
            print(f"  {warning}")
else:
    print(f"Import failed: {response.json()['detail']}")
```

### 2. Template Generation

```python
# Download template for stock import
response = requests.get(
    'http://localhost:8000/api/v1/stock/template/excel',
    headers={'Authorization': f'Bearer {token}'}
)

if response.status_code == 200:
    with open('stock_template.xlsx', 'wb') as f:
        f.write(response.content)
    print("Template downloaded successfully")
```

### 3. Bulk Export

```python
# Export all stock data
response = requests.get(
    'http://localhost:8000/api/v1/stock/export/excel',
    headers={'Authorization': f'Bearer {token}'}
)

if response.status_code == 200:
    with open('stock_export.xlsx', 'wb') as f:
        f.write(response.content)
    print("Stock data exported successfully")
```

## Error Handling Best Practices

### Client-Side Validation

Before uploading, validate:
- File format (.xlsx or .xls)
- File size (< 10MB recommended)
- Required columns present
- Basic data format consistency

### Server Response Handling

```python
def handle_import_response(response):
    if response.status_code == 200:
        data = response.json()
        
        # Check for partial success
        if data['failed'] > 0:
            print(f"Partial success: {data['successful']}/{data['total_processed']}")
            
            # Log detailed errors
            for error in data.get('errors', []):
                log_error(f"Row {error['row']}: {error['error']}")
        else:
            print(f"Complete success: {data['successful']} records imported")
            
    elif response.status_code == 400:
        # Client error - fix file format or data
        print(f"Client error: {response.json()['detail']}")
        
    elif response.status_code == 401:
        # Authentication error
        print("Authentication required or expired")
        
    else:
        # Server error
        print(f"Server error: {response.status_code}")
```

## Performance Considerations

### Large File Handling

- **Batch Processing:** Large files are processed in chunks
- **Memory Management:** Streaming approach prevents memory overflow
- **Timeout Handling:** Long imports have extended timeout limits
- **Progress Tracking:** Future enhancement for progress reporting

### Optimization Tips

1. **Pre-validate files** before uploading
2. **Split large files** into smaller batches (< 1000 rows recommended)
3. **Remove empty rows** and columns
4. **Use consistent data formats** across all fields
5. **Test with small samples** before bulk imports

## Logging and Monitoring

### Import Logging

All imports are logged with:
- User who performed import
- File name and size
- Processing time
- Success/failure counts
- Error details
- Organization context

### Audit Trail

- Import operations create audit log entries
- Track data changes and modifications
- Compliance and tracking support
- User attribution for all changes

## Future Enhancements

### Planned Improvements

1. **Progress Tracking:** Real-time import progress for large files
2. **Background Processing:** Async import with email notifications
3. **Data Mapping UI:** Visual column mapping interface
4. **Import History:** Track and retry previous imports
5. **Bulk Edit:** Excel-like editing interface for imported data

### Advanced Features

1. **Custom Validators:** Organization-specific validation rules
2. **Import Scheduling:** Automated recurring imports
3. **Data Transformation:** Custom field transformation rules
4. **Integration APIs:** Direct integration with external systems

## Troubleshooting

### Common Issues

1. **Column Name Mismatches:** Use template for correct format
2. **Data Type Errors:** Ensure numeric fields contain valid numbers
3. **Missing Required Data:** Check error messages for specific fields
4. **File Corruption:** Re-save Excel file and try again
5. **Large File Timeouts:** Split into smaller files

### Debug Mode

Enable detailed logging by setting environment variable:
```bash
export LOG_LEVEL=DEBUG
```

This provides additional information about:
- Row-by-row processing details
- Data transformation steps
- Database operation timings
- Memory usage statistics