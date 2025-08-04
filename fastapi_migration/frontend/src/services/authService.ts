// frontend/src/services/authService.ts (Revised for detailed error handling in companyService)
import axios from 'axios';

const API_BASE_URL = process.env.NEXT_PUBLIC_API_URL || 'http://localhost:8000';

const api = axios.create({
  baseURL: `${API_BASE_URL}/api`,
  headers: {
    'Content-Type': 'application/json',
  },
});

// Add token to requests
api.interceptors.request.use(
  (config) => {
    const token = localStorage.getItem('token');
    if (token) {
      config.headers.Authorization = `Bearer ${token}`;
    }
    return config;
  },
  (error) => {
    return Promise.reject(error);
  }
);

// Handle token expiration
api.interceptors.response.use(
  (response) => response,
  (error) => {
    if (error.response?.status === 401) {
      localStorage.removeItem('token');
      window.location.href = '/';
    }
    
    // Extract error message with proper handling for arrays and objects
    let errorMessage = 'An unexpected error occurred';
    
    const detail = error.response?.data?.detail;
    const message = error.response?.data?.message;
    const status = error.response?.status;
    
    if (typeof detail === 'string' && detail) {
      errorMessage = detail;
    } else if (typeof message === 'string' && message) {
      errorMessage = message;
    } else if (Array.isArray(detail) && detail.length > 0) {
      // Handle Pydantic validation errors (array of objects)
      const messages = detail.map(err => err.msg || `${err.loc?.join(' -> ')}: ${err.type}`).filter(Boolean);
      errorMessage = messages.length > 0 ? messages.join(', ') : 'Validation error';
    } else if (detail && typeof detail === 'object') {
      // Handle object error details
      errorMessage = detail.error || detail.message || JSON.stringify(detail);
    } else if (typeof error.message === 'string' && error.message && !error.message.includes('[object Object]')) {
      errorMessage = error.message;
    } else if (status === 422) {
      errorMessage = 'Invalid request data. Please check your input and try again.';
    } else if (status === 404) {
      errorMessage = 'Service not found. Please check your connection.';
    } else if (status >= 500) {
      errorMessage = 'Server error. Please try again later or contact support.';
    }
    
    console.error('API Error:', errorMessage, 'Status:', status);
    return Promise.reject({
      ...error,
      userMessage: errorMessage,
      status: error.response?.status
    });
  }
);

export const authService = {
  login: async (username: string, password: string) => {
    try {
      const formData = new FormData();
      formData.append('username', username);
      formData.append('password', password);
      const response = await api.post('/auth/login', formData, {
        headers: {
          'Content-Type': 'application/x-www-form-urlencoded',
        },
      });
      return response.data;
    } catch (error: any) {
      throw new Error(error.userMessage || 'Login failed');
    }
  },
  loginWithEmail: async (email: string, password: string) => {
    try {
      const response = await api.post('/auth/login/email', { email, password });
      return response.data;
    } catch (error: any) {
      throw new Error(error.userMessage || 'Email login failed');
    }
  },
  getCurrentUser: async () => {
    try {
      const response = await api.get('/users/me');
      return response.data;
    } catch (error: any) {
      throw new Error(error.userMessage || 'Failed to get user information');
    }
  },
  logout: () => {
    localStorage.removeItem('token');
    window.location.href = '/';
  },
  // OTP Authentication
  requestOTP: async (email: string, purpose: string = 'login') => {
    try {
      const response = await api.post('/auth/otp/request', { email, purpose });
      return response.data;
    } catch (error: any) {
      throw new Error(error.userMessage || 'Failed to send OTP');
    }
  },
  verifyOTP: async (email: string, otp: string, purpose: string = 'login') => {
    try {
      const response = await api.post('/auth/otp/verify', { email, otp, purpose });
      return response.data;
    } catch (error: any) {
      throw new Error(error.userMessage || 'OTP verification failed');
    }
  },
  setupAdminAccount: async () => {
    try {
      const response = await api.post('/auth/admin/setup');
      return response.data;
    } catch (error: any) {
      throw new Error(error.userMessage || 'Admin setup failed');
    }
  },
};

export const voucherService = {
  // Generic function for CRUD
  getVouchers: async (type: string, params?: any) => {
    try {
      const response = await api.get(`/vouchers/${type}`, { params });
      return response.data;
    } catch (error: any) {
      throw new Error(error.userMessage || `Failed to fetch ${type}`);
    }
  },
  createVoucher: async (type: string, data: any, sendEmail = false) => {
    try {
      const response = await api.post(`/vouchers/${type}?send_email=${sendEmail}`, data);
      return response.data;
    } catch (error: any) {
      throw new Error(error.userMessage || `Failed to create ${type}`);
    }
  },
  getVoucherById: async (type: string, id: number) => {
    try {
      const response = await api.get(`/vouchers/${type}/${id}`);
      return response.data;
    } catch (error: any) {
      throw new Error(error.userMessage || `Failed to fetch ${type}`);
    }
  },
  updateVoucher: async (type: string, id: number, data: any) => {
    try {
      const response = await api.put(`/vouchers/${type}/${id}`, data);
      return response.data;
    } catch (error: any) {
      throw new Error(error.userMessage || `Failed to update ${type}`);
    }
  },
  deleteVoucher: async (type: string, id: number) => {
    try {
      const response = await api.delete(`/vouchers/${type}/${id}`);
      return response.data;
    } catch (error: any) {
      throw new Error(error.userMessage || `Failed to delete ${type}`);
    }
  },
  sendVoucherEmail: async (voucherType: string, voucherId: number, customEmail?: string) => {
    const params = customEmail ? `?custom_email=${customEmail}` : '';
    try {
      const response = await api.post(`/vouchers/send-email/${voucherType}/${voucherId}${params}`);
      return response.data;
    } catch (error: any) {
      throw new Error(error.userMessage || 'Failed to send email');
    }
  },
  getSalesVouchers: async (params?: any) => {
    return voucherService.getVouchers('sales', params);
  },
  // Purchase Order specific methods
  getPurchaseOrders: async (params?: any) => {
    return voucherService.getVouchers('purchase_order', params);
  },
  getPurchaseOrderById: async (id: number) => {
    return voucherService.getVoucherById('purchase_order', id);
  },
  createPurchaseOrder: async (data: any, sendEmail = false) => {
    return voucherService.createVoucher('purchase_order', data, sendEmail);
  },
  updatePurchaseOrder: async (id: number, data: any) => {
    return voucherService.updateVoucher('purchase_order', id, data);
  },
  // GRN specific methods
  getGrns: async (params?: any) => {
    return voucherService.getVouchers('grn', params);
  },
  getGrnById: async (id: number) => {
    return voucherService.getVoucherById('grn', id);
  },
  createGrn: async (data: any, sendEmail = false) => {
    return voucherService.createVoucher('grn', data, sendEmail);
  },
  updateGrn: async (id: number, data: any) => {
    return voucherService.updateVoucher('grn', id, data);
  },
  // Access to master data for vouchers
  getVendors: async (params?: any) => {
    return masterDataService.getVendors(params);
  },
  getProducts: async (params?: any) => {
    return masterDataService.getProducts(params);
  },
  getCustomers: async (params?: any) => {
    return masterDataService.getCustomers(params);
  },
};

export const masterDataService = {
  getVendors: async (params?: any) => {
    try {
      const response = await api.get('/vendors/', { params });
      return response.data;
    } catch (error: any) {
      throw new Error(error.userMessage || 'Failed to fetch vendors');
    }
  },
  createVendor: async (data: any) => {
    try {
      const response = await api.post('/vendors/', data);
      return response.data;
    } catch (error: any) {
      throw new Error(error.userMessage || 'Failed to create vendor');
    }
  },
  updateVendor: async (id: number, data: any) => {
    try {
      const response = await api.put(`/vendors/${id}`, data);
      return response.data;
    } catch (error: any) {
      throw new Error(error.userMessage || 'Failed to update vendor');
    }
  },
  deleteVendor: async (id: number) => {
    try {
      const response = await api.delete('/vendors/' + id);
      return response.data;
    } catch (error: any) {
      throw new Error(error.userMessage || 'Failed to delete vendor');
    }
  },
  getCustomers: async (params?: any) => {
    try {
      const response = await api.get('/customers/', { params });
      return response.data;
    } catch (error: any) {
      throw new Error(error.userMessage || 'Failed to fetch customers');
    }
  },
  createCustomer: async (data: any) => {
    try {
      const response = await api.post('/customers/', data);
      return response.data;
    } catch (error: any) {
      throw new Error(error.userMessage || 'Failed to create customer');
    }
  },
  updateCustomer: async (id: number, data: any) => {
    try {
      const response = await api.put(`/customers/${id}`, data);
      return response.data;
    } catch (error: any) {
      throw new Error(error.userMessage || 'Failed to update customer');
    }
  },
  deleteCustomer: async (id: number) => {
    try {
      const response = await api.delete('/customers/' + id);
      return response.data;
    } catch (error: any) {
      throw new Error(error.userMessage || 'Failed to delete customer');
    }
  },
  getProducts: async (params?: any) => {
    try {
      const response = await api.get('/products/', { params });
      return response.data;
    } catch (error: any) {
      throw new Error(error.userMessage || 'Failed to fetch products');
    }
  },
  createProduct: async (data: any) => {
    try {
      const response = await api.post('/products/', data);
      return response.data;
    } catch (error: any) {
      throw new Error(error.userMessage || 'Failed to create product');
    }
  },
  updateProduct: async (id: number, data: any) => {
    try {
      const response = await api.put(`/products/${id}`, data);
      return response.data;
    } catch (error: any) {
      throw new Error(error.userMessage || 'Failed to update product');
    }
  },
  deleteProduct: async (id: number) => {
    try {
      const response = await api.delete('/products/' + id);
      return response.data;
    } catch (error: any) {
      throw new Error(error.userMessage || 'Failed to delete product');
    }
  },
  getStock: async (params?: any) => {
    try {
      const response = await api.get('/stock/', { params });
      return response.data;
    } catch (error: any) {
      throw new Error(error.userMessage || 'Failed to fetch stock data');
    }
  },
  getLowStock: async () => {
    try {
      const response = await api.get('/stock/low-stock');
      return response.data;
    } catch (error: any) {
      throw new Error(error.userMessage || 'Failed to fetch low stock data');
    }
  },
  updateStock: async (productId: number, data: any) => {
    try {
      const response = await api.put(`/stock/product/${productId}`, data);
      return response.data;
    } catch (error: any) {
      throw new Error(error.userMessage || 'Failed to update stock');
    }
  },
  adjustStock: async (productId: number, quantityChange: number, reason: string) => {
    try {
      const response = await api.post(`/stock/adjust/${productId}`, null, {
        params: { quantity_change: quantityChange, reason }
      });
      return response.data;
    } catch (error: any) {
      throw new Error(error.userMessage || 'Failed to adjust stock');
    }
  },
  bulkImportStock: async (file: File) => {
    try {
      const formData = new FormData();
      formData.append('file', file);
      const response = await api.post('/stock/bulk', formData, {
        headers: {
          'Content-Type': undefined,
        },
        transformRequest: (data) => data,
      });
      return response.data;
    } catch (error: any) {
      throw new Error(error.userMessage || 'Failed to bulk import stock');
    }
  },
};

export const companyService = {
  getCurrentCompany: async () => {
    try {
      const response = await api.get('/companies/current');
      return response.data;
    } catch (error: any) {
      if (error.status === 404) {
        return null;
      }
      throw new Error(error.userMessage || 'Failed to get current company');
    }
  },
  createCompany: async (data: any) => {
    try {
      const response = await api.post('/companies/', data);
      return response.data;
    } catch (error: any) {
      throw new Error(error.userMessage || 'Failed to create company');
    }
  },
  updateCompany: async (id: number, data: any) => {
    try {
      const response = await api.put(`/companies/${id}`, data);
      return response.data;
    } catch (error: any) {
      throw new Error(error.userMessage || 'Failed to update company');
    }
  },
};

export const reportsService = {
  getDashboardStats: async () => {
    try {
      const response = await api.get('/reports/dashboard-stats');
      return response.data;
    } catch (error: any) {
      throw new Error(error.userMessage || 'Failed to get dashboard stats');
    }
  },
  getSalesReport: async (params?: any) => {
    try {
      const response = await api.get('/reports/sales-report', { params });
      return response.data;
    } catch (error: any) {
      throw new Error(error.userMessage || 'Failed to get sales report');
    }
  },
  getPurchaseReport: async (params?: any) => {
    try {
      const response = await api.get('/reports/purchase-report', { params });
      return response.data;
    } catch (error: any) {
      throw new Error(error.userMessage || 'Failed to get purchase report');
    }
  },
  getInventoryReport: async (lowStockOnly = false) => {
    try {
      const response = await api.get('/reports/inventory-report', {
        params: { low_stock_only: lowStockOnly }
      });
      return response.data;
    } catch (error: any) {
      throw new Error(error.userMessage || 'Failed to get inventory report');
    }
  },
  getPendingOrders: async (orderType = 'all') => {
    try {
      const response = await api.get('/reports/pending-orders', {
        params: { order_type: orderType }
      });
      return response.data;
    } catch (error: any) {
      throw new Error(error.userMessage || 'Failed to get pending orders');
    }
  },
};

export const organizationService = {
  createLicense: async (data: { organization_name: string; superadmin_email: string }) => {
    try {
      const response = await api.post('/organizations/license/create', data);
      return response.data;
    } catch (error: any) {
      throw new Error(error.userMessage || 'Failed to create organization license');
    }
  },
  getCurrentOrganization: async () => {
    try {
      const response = await api.get('/organizations/current');
      return response.data;
    } catch (error: any) {
      throw new Error(error.userMessage || 'Failed to get current organization');
    }
  },
  updateOrganization: async (data: any) => {
    try {
      const response = await api.put('/organizations/current', data);
      return response.data;
    } catch (error: any) {
      throw new Error(error.userMessage || 'Failed to update organization');
    }
  },
  // Admin-only endpoints
  getAllOrganizations: async (params?: any) => {
    try {
      const response = await api.get('/organizations/', { params });
      return response.data;
    } catch (error: any) {
      throw new Error(error.userMessage || 'Failed to get organizations');
    }
  },
  getOrganization: async (id: number) => {
    try {
      const response = await api.get(`/organizations/${id}`);
      return response.data;
    } catch (error: any) {
      throw new Error(error.userMessage || 'Failed to get organization');
    }
  },
  updateOrganizationById: async (id: number, data: any) => {
    try {
      const response = await api.put(`/organizations/${id}`, data);
      return response.data;
    } catch (error: any) {
      throw new Error(error.userMessage || 'Failed to update organization');
    }
  },
};

export const passwordService = {
  changePassword: async (currentPassword: string | null, newPassword: string, confirmPassword?: string) => {
    try {
      console.log('🔐 passwordService.changePassword called with:', {
        currentPassword: currentPassword ? 'PROVIDED' : 'NOT_PROVIDED',
        newPassword: 'PROVIDED',
        confirmPassword: confirmPassword ? 'PROVIDED' : 'NOT_PROVIDED'
      });
      
      const payload: { new_password: string; current_password?: string; confirm_password?: string } = {
        new_password: newPassword
      };
      
      if (currentPassword) {
        payload.current_password = currentPassword;
      }
      
      if (confirmPassword) {
        payload.confirm_password = confirmPassword;
      }
      
      console.log('📤 Sending password change request with payload structure:', {
        has_new_password: !!payload.new_password,
        has_current_password: !!payload.current_password,
        has_confirm_password: !!payload.confirm_password
      });
      
      const response = await api.post('/auth/password/change', payload);
      console.log('✅ Password change request successful:', response.data);
      return response.data;
    } catch (error: any) {
      console.error('❌ Password change request failed:', error);
      throw new Error(error.userMessage || 'Failed to change password');
    }
  },
  forgotPassword: async (email: string) => {
    try {
      const response = await api.post('/auth/password/forgot', { email });
      return response.data;
    } catch (error: any) {
      throw new Error(error.userMessage || 'Failed to send password reset email');
    }
  },
  resetPassword: async (email: string, otp: string, newPassword: string) => {
    try {
      const response = await api.post('/auth/password/reset', {
        email,
        otp,
        new_password: newPassword
      });
      return response.data;
    } catch (error: any) {
      throw new Error(error.userMessage || 'Failed to reset password');
    }
  },
};

export default api;