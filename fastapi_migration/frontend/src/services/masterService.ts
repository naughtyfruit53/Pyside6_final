// services/masterService.ts
// masterService.ts - Service to fetch master data like vendors, customers, products

// Assuming you have a base API URL or use relative paths
const API_BASE = '/api'; // Adjust if needed

export const getVendors = async () => {
  const response = await fetch(`${API_BASE}/vendors`);
  if (!response.ok) {
    throw new Error('Failed to fetch vendors');
  }
  return response.json();
};

export const getCustomers = async () => {
  const response = await fetch(`${API_BASE}/customers`);
  if (!response.ok) {
    throw new Error('Failed to fetch customers');
  }
  return response.json();
};

export const getProducts = async () => {
  const response = await fetch(`${API_BASE}/products`);
  if (!response.ok) {
    throw new Error('Failed to fetch products');
  }
  return response.json();
};

export const bulkImportVendors = async (data: any[]) => {
  const response = await fetch(`${API_BASE}/vendors/bulk`, {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify(data),
  });
  if (!response.ok) {
    throw new Error('Failed to import vendors');
  }
  return response.json();
};

export const bulkImportCustomers = async (data: any[]) => {
  const response = await fetch(`${API_BASE}/customers/bulk`, {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify(data),
  });
  if (!response.ok) {
    throw new Error('Failed to import customers');
  }
  return response.json();
};

export const bulkImportProducts = async (data: any[]) => {
  const response = await fetch(`${API_BASE}/products/bulk`, {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify(data),
  });
  if (!response.ok) {
    throw new Error('Failed to import products');
  }
  return response.json();
};

export const bulkImportStock = async (data: any[]) => {
  const response = await fetch(`${API_BASE}/stock/bulk`, {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify(data),
  });
  if (!response.ok) {
    throw new Error('Failed to import stock');
  }
  return response.json();
};