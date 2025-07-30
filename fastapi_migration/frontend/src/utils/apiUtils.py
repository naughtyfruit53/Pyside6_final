// frontend/src/utils/apiUtils.ts

import axios from 'axios';

export const handleApiError = (error: any): string => {
  if (error.response) {
    return error.response.data?.message || error.response.data?.detail || 'An error occurred';
  } else if (error.request) {
    return 'No response received from server';
  } else {
    return error.message || 'Unknown error';
  }
};

export const getApiParams = (params: any): URLSearchParams => {
  const searchParams = new URLSearchParams();
  Object.entries(params).forEach(([key, value]) => {
    if (value !== undefined && value !== null) {
      searchParams.append(key, String(value));
    }
  });
  return searchParams;
};

export const uploadStockBulk = async (file: File, token: string): Promise<any> => {
  try {
    const formData = new FormData();
    formData.append('file', file); // Ensure field name matches backend expectation ('file')

    const response = await axios.post(
      'http://localhost:8000/api/v1/stock/bulk',
      formData,
      {
        headers: {
          'Authorization': `Bearer ${token}`,
          'Content-Type': 'multipart/form-data',
        },
      }
    );
    return response.data;
  } catch (error) {
    throw new Error(handleApiError(error));
  }
};