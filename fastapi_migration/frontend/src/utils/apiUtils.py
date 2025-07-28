// frontend/src/utils/apiUtils.ts

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