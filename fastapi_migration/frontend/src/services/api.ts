// frontend/src/services/api.ts

import axios from 'axios';

const api = axios.create({
  baseURL: '/api/v1',  // Adjust based on your API prefix in settings
  withCredentials: true,
  headers: {
    'Content-Type': 'application/json',
  },
});

// Optional: Add interceptors for auth or error handling
api.interceptors.request.use((config) => {
  // Add auth token if needed
  return config;
});

api.interceptors.response.use(
  (response) => response,
  (error) => {
    // Handle errors globally
    return Promise.reject(error);
  }
);

export default api;