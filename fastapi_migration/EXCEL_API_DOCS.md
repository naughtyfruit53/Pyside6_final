# Excel Import/Export API Documentation

This document describes the new Excel import, export, and template download endpoints for Products, Vendors, Customers, and Stock (Inventory) in the FastAPI backend.

## Overview

Each entity (products, vendors, customers, stock) now has three new endpoints:
- **Template Download**: GET endpoint that returns an Excel template file
- **Export**: GET endpoint that exports existing data to Excel format
- **Import**: POST endpoint that accepts Excel files for bulk data import

## Authentication

All endpoints require authentication. Use the existing authentication system:
- Bearer token in Authorization header
- Multi-tenant support: Operations are scoped to the user's organization

## Endpoints

### Products

#### Download Template
```
GET /api/v1/products/template/excel
```
Downloads an Excel template file for products bulk import.

**Response**: Excel file (.xlsx) with proper column headers and example data

**Template Columns**:
- Name* (required)
- HSN Code
- Part Number  
- Unit* (required)
- Unit Price* (required)
- GST Rate
- Is GST Inclusive (TRUE/FALSE)
- Reorder Level
- Description
- Is Manufactured (TRUE/FALSE)

#### Export Products
```
GET /api/v1/products/export/excel?skip=0&limit=1000&search=&active_only=true
```
Exports products to Excel format.

**Query Parameters**:
- `skip`: Number of records to skip (default: 0)
- `limit`: Maximum records to export (default: 1000)
- `search`: Search term for filtering
- `active_only`: Export only active products (default: true)

**Response**: Excel file (.xlsx) with product data

#### Import Products
```
POST /api/v1/products/import/excel
Content-Type: multipart/form-data
```
Imports products from Excel file.

**Request Body**: 
- `file`: Excel file (.xlsx or .xls)

**Response**:
```json
{
  "message": "Import completed successfully. X products created, Y updated.",
  "total_processed": 10,
  "created": 7,
  "updated": 3,
  "errors": []
}
```

### Vendors

#### Download Template
```
GET /api/v1/vendors/template/excel
```

**Template Columns**:
- Name* (required)
- Contact Number* (required)
- Email
- Address Line 1* (required)
- Address Line 2
- City* (required)
- State* (required)
- Pin Code* (required)
- State Code* (required)
- GST Number
- PAN Number

#### Export Vendors
```
GET /api/v1/vendors/export/excel?skip=0&limit=1000&search=&active_only=true
```

#### Import Vendors
```
POST /api/v1/vendors/import/excel
```

### Customers

#### Download Template
```
GET /api/v1/customers/template/excel
```

**Template Columns**: Same as Vendors

#### Export Customers
```
GET /api/v1/customers/export/excel?skip=0&limit=1000&search=&active_only=true
```

#### Import Customers
```
POST /api/v1/customers/import/excel
```

### Stock (Inventory)

#### Download Template
```
GET /api/v1/stock/template/excel
```

**Template Columns**:
- Product Name* (required)
- HSN Code
- Part Number
- Unit* (required)
- Unit Price
- GST Rate
- Reorder Level
- Quantity* (required)
- Location

#### Export Stock
```
GET /api/v1/stock/export/excel?skip=0&limit=1000&product_id=&low_stock_only=false
```

**Query Parameters**:
- `skip`: Number of records to skip
- `limit`: Maximum records to export
- `product_id`: Filter by specific product ID
- `low_stock_only`: Export only low stock items

#### Import Stock
```
POST /api/v1/stock/import/excel
```

**Special Feature**: Auto-creates products if they don't exist during stock import.

## Error Handling

Import endpoints return detailed error information:

```json
{
  "message": "Import completed with errors",
  "total_processed": 10,
  "created": 5,
  "updated": 3,
  "errors": [
    "Row 2: Name is required",
    "Row 5: Invalid data format - could not convert string to float: 'abc'",
    "Row 8: Product with this name already exists in organization"
  ]
}
```

## File Format Requirements

- **Supported formats**: .xlsx, .xls
- **Required columns**: Must match template exactly (case-sensitive)
- **Empty rows**: Automatically skipped
- **Data validation**: Type checking and required field validation
- **Examples**: Template files include example rows

## Multi-Tenancy

All operations are automatically scoped to the user's organization:
- Users can only import/export data within their organization
- Product auto-creation during stock import respects organization boundaries
- Duplicate checking is performed within organization scope

## Usage Examples

### Using curl

```bash
# Download template
curl -H "Authorization: Bearer <token>" \
     -o products_template.xlsx \
     http://localhost:8000/api/v1/products/template/excel

# Export data
curl -H "Authorization: Bearer <token>" \
     -o products_export.xlsx \
     "http://localhost:8000/api/v1/products/export/excel?limit=100"

# Import data
curl -H "Authorization: Bearer <token>" \
     -F "file=@products_import.xlsx" \
     http://localhost:8000/api/v1/products/import/excel
```

### Using Python requests

```python
import requests

headers = {"Authorization": "Bearer <your-token>"}
base_url = "http://localhost:8000/api/v1"

# Download template
response = requests.get(f"{base_url}/products/template/excel", headers=headers)
with open("template.xlsx", "wb") as f:
    f.write(response.content)

# Import data
with open("data.xlsx", "rb") as f:
    files = {"file": f}
    response = requests.post(f"{base_url}/products/import/excel", 
                           headers=headers, files=files)
    print(response.json())
```

## Implementation Details

- **Service Layer**: `app/services/excel_service.py` handles all Excel operations
- **Template Files**: Stored in `app/templates/excel/`
- **Dependencies**: Uses pandas and openpyxl for Excel processing
- **Streaming**: Large exports use StreamingResponse for memory efficiency
- **Validation**: Comprehensive input validation and error reporting