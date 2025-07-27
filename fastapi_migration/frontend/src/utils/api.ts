// fastapi_migration/frontend/src/utils/api.ts

import axios from 'axios';

const API_BASE_URL = process.env.NEXT_PUBLIC_API_URL || 'http://localhost:8000';

const api = axios.create({
  baseURL: `${API_BASE_URL}/api/v1`,
  headers: {
    'Content-Type': 'application/json',
  },
});

// Add token and organization context to requests
api.interceptors.request.use(
  (config) => {
    const token = localStorage.getItem('token');
    const orgId = localStorage.getItem('orgId');
    if (token) {
      config.headers.Authorization = `Bearer ${token}`;
    }
    if (orgId && orgId !== 'null') {
      config.headers['X-Organization-ID'] = orgId;
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
      localStorage.removeItem('orgId');
      window.location.href = '/login';
    }
    return Promise.reject(error);
  }
);

export default api;