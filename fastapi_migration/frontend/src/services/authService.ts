import axios from 'axios';

const API_BASE_URL = process.env.NEXT_PUBLIC_API_URL || 'http://localhost:8000';

const api = axios.create({
  baseURL: `${API_BASE_URL}/api/v1`,
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
    return Promise.reject(error);
  }
);

export const authService = {
  login: async (username: string, password: string) => {
    const formData = new FormData();
    formData.append('username', username);
    formData.append('password', password);
    
    const response = await api.post('/auth/login', formData, {
      headers: {
        'Content-Type': 'application/x-www-form-urlencoded',
      },
    });
    return response.data;
  },

  loginWithEmail: async (email: string, password: string) => {
    const response = await api.post('/auth/login/email', { email, password });
    return response.data;
  },

  getCurrentUser: async () => {
    const response = await api.get('/users/me');
    return response.data;
  },

  logout: () => {
    localStorage.removeItem('token');
    window.location.href = '/';
  },

  // OTP Authentication
  requestOTP: async (email: string, purpose: string = 'login') => {
    const response = await api.post('/auth/otp/request', { email, purpose });
    return response.data;
  },

  verifyOTP: async (email: string, otp: string, purpose: string = 'login') => {
    const response = await api.post('/auth/otp/verify', { email, otp, purpose });
    return response.data;
  },

  setupAdminAccount: async () => {
    const response = await api.post('/auth/admin/setup');
    return response.data;
  },
};

export const voucherService = {
  // Purchase Vouchers
  getPurchaseVouchers: async (params?: any) => {
    const response = await api.get('/vouchers/purchase-vouchers/', { params });
    return response.data;
  },

  createPurchaseVoucher: async (data: any, sendEmail = false) => {
    const response = await api.post(`/vouchers/purchase-vouchers/?send_email=${sendEmail}`, data);
    return response.data;
  },

  // Sales Vouchers
  getSalesVouchers: async (params?: any) => {
    const response = await api.get('/vouchers/sales-vouchers/', { params });
    return response.data;
  },

  createSalesVoucher: async (data: any, sendEmail = false) => {
    const response = await api.post(`/vouchers/sales-vouchers/?send_email=${sendEmail}`, data);
    return response.data;
  },

  // Email
  sendVoucherEmail: async (voucherType: string, voucherId: number, customEmail?: string) => {
    const params = customEmail ? `?custom_email=${customEmail}` : '';
    const response = await api.post(`/vouchers/send-email/${voucherType}/${voucherId}${params}`);
    return response.data;
  },
};

export const masterDataService = {
  // Vendors
  getVendors: async (params?: any) => {
    const response = await api.get('/vendors/', { params });
    return response.data;
  },

  createVendor: async (data: any) => {
    const response = await api.post('/vendors/', data);
    return response.data;
  },

  updateVendor: async (id: number, data: any) => {
    const response = await api.put(`/vendors/${id}`, data);
    return response.data;
  },

  // Customers
  getCustomers: async (params?: any) => {
    const response = await api.get('/customers/', { params });
    return response.data;
  },

  createCustomer: async (data: any) => {
    const response = await api.post('/customers/', data);
    return response.data;
  },

  updateCustomer: async (id: number, data: any) => {
    const response = await api.put(`/customers/${id}`, data);
    return response.data;
  },

  // Products
  getProducts: async (params?: any) => {
    const response = await api.get('/products/', { params });
    return response.data;
  },

  createProduct: async (data: any) => {
    const response = await api.post('/products/', data);
    return response.data;
  },

  updateProduct: async (id: number, data: any) => {
    const response = await api.put(`/products/${id}`, data);
    return response.data;
  },

  // Stock
  getStock: async (params?: any) => {
    const response = await api.get('/stock/', { params });
    return response.data;
  },

  getLowStock: async () => {
    const response = await api.get('/stock/low-stock');
    return response.data;
  },

  updateStock: async (productId: number, data: any) => {
    const response = await api.put(`/stock/product/${productId}`, data);
    return response.data;
  },

  adjustStock: async (productId: number, quantityChange: number, reason: string) => {
    const response = await api.post(`/stock/adjust/${productId}`, null, {
      params: { quantity_change: quantityChange, reason }
    });
    return response.data;
  },
};

export const companyService = {
  getCurrentCompany: async () => {
    const response = await api.get('/companies/current');
    return response.data;
  },

  createCompany: async (data: any) => {
    const response = await api.post('/companies/', data);
    return response.data;
  },

  updateCompany: async (id: number, data: any) => {
    const response = await api.put(`/companies/${id}`, data);
    return response.data;
  },
};

export default api;