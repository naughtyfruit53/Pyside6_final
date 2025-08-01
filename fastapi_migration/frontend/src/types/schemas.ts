// Generated src/types/schemas.ts (new file in new types folder)

export interface StockBase {
  product_id: number;
  quantity: number;
  unit: string;
  location?: string | null;
}

export type StockCreate = StockBase;

export type StockUpdate = Partial<StockBase>;

export interface StockInDB extends StockBase {
  id: number;
  organization_id: number;
  last_updated: string; // ISO date string
}

export interface BulkStockRequest {
  items: Array<{
    product_name: string;  // Use product_name for frontend consistency
    hsn_code?: string | null;
    part_number?: string | null;
    unit: string;
    unit_price?: number | null;
    gst_rate?: number | null;
    reorder_level?: number | null;
    quantity: number;
    location?: string | null;
  }>;
}

export interface BulkImportResponse {
  message: string;
  total_processed: number;
  created: number;
  updated: number;
  errors: string[];
}