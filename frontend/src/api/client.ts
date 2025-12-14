/**
 * Axios client for API communication
 */

import axios, { AxiosError } from 'axios';
import type { ApiError } from './types';

// Create axios instance with base configuration
export const apiClient = axios.create({
  baseURL: '/api/v1',
  headers: {
    'Content-Type': 'application/json',
  },
  timeout: 10000,
});

// Response interceptor for error handling
apiClient.interceptors.response.use(
  (response) => response,
  (error: AxiosError<ApiError>) => {
    // Extract error message from response
    const message = error.response?.data?.detail || error.message || 'An unknown error occurred';

    // Log error for debugging
    console.error('API Error:', {
      status: error.response?.status,
      message,
      url: error.config?.url,
    });

    // Re-throw with parsed message
    return Promise.reject(new Error(message));
  }
);

export default apiClient;
