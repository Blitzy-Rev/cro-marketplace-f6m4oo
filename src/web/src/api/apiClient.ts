/**
 * Core API client implementation for the Molecular Data Management and CRO Integration Platform frontend
 * 
 * This file provides a centralized HTTP client with request/response interceptors,
 * authentication handling, error management, circuit breaker pattern, and
 * standardized API communication patterns.
 */

import axios, { AxiosInstance, AxiosRequestConfig, AxiosResponse, AxiosError } from 'axios'; // v1.4.0
import { ApiResponse, ApiError } from '../types/api.types';
import { AuthToken } from '../types/auth.types';
import { APP_CONFIG } from '../constants/appConfig';
import { API_ENDPOINTS } from '../constants/apiEndpoints';
import { getAuthToken, setAuthToken, removeAuthToken, isTokenExpired } from '../utils/auth';
import { handleApiError, isApiError } from '../utils/errorHandler';

// Circuit breaker state tracking
interface CircuitBreaker {
  failures: number;
  lastFailureTime: number;
  state: 'CLOSED' | 'OPEN' | 'HALF_OPEN';
}

// Circuit breaker configuration
const CIRCUIT_BREAKER_CONFIG = {
  failureThreshold: 5,        // Number of consecutive failures before opening circuit
  resetTimeout: 30000,        // Time in ms before trying again (30 seconds)
  halfOpenMaxRequests: 3      // Number of requests to try in HALF_OPEN state
};

// Track circuit breakers for different endpoints
const circuitBreakers: Record<string, CircuitBreaker> = {};

/**
 * Creates and configures an Axios instance with interceptors for API communication
 * @returns Configured Axios instance for API requests
 */
function createApiClient(): AxiosInstance {
  const instance = axios.create({
    baseURL: APP_CONFIG.api.baseUrl,
    timeout: APP_CONFIG.api.timeout,
    headers: {
      'Content-Type': 'application/json',
      'Accept': 'application/json',
    },
  });

  // Request interceptor for authentication and circuit breaker
  instance.interceptors.request.use(
    (config) => {
      // Check if circuit breaker is open for this endpoint
      const endpoint = config.url || '';
      if (isCircuitOpen(endpoint)) {
        return Promise.reject(new Error(`Circuit breaker open for endpoint: ${endpoint}`));
      }

      // Add authorization token if available
      const token = getAuthToken();
      if (token && !isTokenExpired()) {
        config.headers.Authorization = `Bearer ${token.access_token}`;
      }
      
      return config;
    },
    (error) => Promise.reject(error)
  );

  // Response interceptor for data extraction and error handling
  instance.interceptors.response.use(
    (response) => {
      // Reset circuit breaker on successful response
      resetCircuitBreaker(response.config.url || '');
      
      // Extract data from ApiResponse format if applicable
      const data = response.data;
      if (data && typeof data === 'object' && 'success' in data) {
        return data.data;
      }
      
      return data;
    },
    async (error: AxiosError) => {
      // Record failure in circuit breaker
      recordFailure(error.config?.url || '');
      
      // Handle token refresh if error is due to expired token
      if (error.response?.status === 401 && error.config) {
        try {
          return await handleTokenRefresh(error);
        } catch (refreshError) {
          // If token refresh fails, continue with original error
          handleApiError(refreshError, false);
        }
      }
      
      return Promise.reject(error);
    }
  );

  return instance;
}

/**
 * Attempts to refresh the authentication token using the refresh token
 * @returns New authentication token or null if refresh fails
 */
async function refreshAuthToken(): Promise<AuthToken | null> {
  const token = getAuthToken();
  
  if (!token || !token.refresh_token) {
    return null;
  }
  
  try {
    // Create a new axios instance for token refresh to avoid interceptors
    const refreshInstance = axios.create({
      baseURL: APP_CONFIG.api.baseUrl,
      timeout: APP_CONFIG.api.timeout,
    });
    
    const response = await refreshInstance.post<ApiResponse<AuthToken>>(
      API_ENDPOINTS.AUTH.REFRESH_TOKEN,
      { refresh_token: token.refresh_token }
    );
    
    if (response.data && response.data.success && response.data.data) {
      const newToken = response.data.data;
      setAuthToken(newToken);
      return newToken;
    }
    
    removeAuthToken();
    return null;
  } catch (error) {
    handleApiError(error, false);
    removeAuthToken();
    return null;
  }
}

/**
 * Handles token refresh when a request fails due to expired token
 * @param error - AxiosError from the failed request
 * @returns Response from retried request with new token
 */
async function handleTokenRefresh(error: AxiosError): Promise<AxiosResponse> {
  if (!error.config) {
    return Promise.reject(error);
  }
  
  const newToken = await refreshAuthToken();
  if (!newToken) {
    return Promise.reject(error);
  }
  
  // Retry the original request with the new token
  const originalRequest = error.config;
  originalRequest.headers.Authorization = `Bearer ${newToken.access_token}`;
  return axios(originalRequest);
}

/**
 * Checks if the circuit breaker is open for an endpoint
 * @param endpoint - The API endpoint URL
 * @returns True if circuit is open and requests should be blocked
 */
function isCircuitOpen(endpoint: string): boolean {
  const circuit = getCircuitBreaker(endpoint);
  
  switch (circuit.state) {
    case 'CLOSED':
      return false;
    
    case 'OPEN':
      const now = Date.now();
      if (now - circuit.lastFailureTime > CIRCUIT_BREAKER_CONFIG.resetTimeout) {
        // Move to half-open state and allow the request
        circuit.state = 'HALF_OPEN';
        return false;
      }
      return true;
    
    case 'HALF_OPEN':
      // Allow requests in half-open state to test if the service has recovered
      return false;
    
    default:
      return false;
  }
}

/**
 * Records a failure in the circuit breaker
 * @param endpoint - The API endpoint URL
 */
function recordFailure(endpoint: string): void {
  const circuit = getCircuitBreaker(endpoint);
  
  if (circuit.state === 'HALF_OPEN') {
    // Immediately open the circuit again on failure in half-open state
    circuit.state = 'OPEN';
    circuit.lastFailureTime = Date.now();
    return;
  }
  
  if (circuit.state === 'CLOSED') {
    circuit.failures++;
    circuit.lastFailureTime = Date.now();
    
    // Open circuit if threshold reached
    if (circuit.failures >= CIRCUIT_BREAKER_CONFIG.failureThreshold) {
      circuit.state = 'OPEN';
    }
  }
}

/**
 * Resets the circuit breaker after a successful request
 * @param endpoint - The API endpoint URL
 */
function resetCircuitBreaker(endpoint: string): void {
  const circuit = getCircuitBreaker(endpoint);
  
  if (circuit.state === 'HALF_OPEN') {
    // On success in half-open state, close the circuit
    circuit.state = 'CLOSED';
    circuit.failures = 0;
  } else if (circuit.state === 'CLOSED') {
    // Reset failure count in closed state
    circuit.failures = 0;
  }
}

/**
 * Gets or initializes a circuit breaker for an endpoint
 * @param endpoint - The API endpoint URL
 * @returns The circuit breaker state object
 */
function getCircuitBreaker(endpoint: string): CircuitBreaker {
  const baseEndpoint = endpoint.split('?')[0]; // Remove query parameters
  
  if (!circuitBreakers[baseEndpoint]) {
    circuitBreakers[baseEndpoint] = {
      failures: 0,
      lastFailureTime: 0,
      state: 'CLOSED',
    };
  }
  
  return circuitBreakers[baseEndpoint];
}

// Initialize the API client
const apiClient = createApiClient();

/**
 * Performs a GET request to the specified endpoint
 * @param url - The endpoint URL
 * @param config - Optional Axios request configuration
 * @returns Promise resolving to the response data
 */
async function get<T = any>(
  url: string, 
  config: AxiosRequestConfig = {}
): Promise<T> {
  try {
    return await apiClient.get<T>(url, config);
  } catch (error) {
    handleApiError(error);
    throw error;
  }
}

/**
 * Performs a POST request to the specified endpoint
 * @param url - The endpoint URL
 * @param data - The request payload
 * @param config - Optional Axios request configuration
 * @returns Promise resolving to the response data
 */
async function post<T = any>(
  url: string, 
  data: any = {}, 
  config: AxiosRequestConfig = {}
): Promise<T> {
  try {
    return await apiClient.post<T>(url, data, config);
  } catch (error) {
    handleApiError(error);
    throw error;
  }
}

/**
 * Performs a PUT request to the specified endpoint
 * @param url - The endpoint URL
 * @param data - The request payload
 * @param config - Optional Axios request configuration
 * @returns Promise resolving to the response data
 */
async function put<T = any>(
  url: string, 
  data: any = {}, 
  config: AxiosRequestConfig = {}
): Promise<T> {
  try {
    return await apiClient.put<T>(url, data, config);
  } catch (error) {
    handleApiError(error);
    throw error;
  }
}

/**
 * Performs a PATCH request to the specified endpoint
 * @param url - The endpoint URL
 * @param data - The request payload
 * @param config - Optional Axios request configuration
 * @returns Promise resolving to the response data
 */
async function patch<T = any>(
  url: string, 
  data: any = {}, 
  config: AxiosRequestConfig = {}
): Promise<T> {
  try {
    return await apiClient.patch<T>(url, data, config);
  } catch (error) {
    handleApiError(error);
    throw error;
  }
}

/**
 * Performs a DELETE request to the specified endpoint
 * @param url - The endpoint URL
 * @param config - Optional Axios request configuration
 * @returns Promise resolving to the response data
 */
async function deleteRequest<T = any>(
  url: string, 
  config: AxiosRequestConfig = {}
): Promise<T> {
  try {
    return await apiClient.delete<T>(url, config);
  } catch (error) {
    handleApiError(error);
    throw error;
  }
}

/**
 * Uploads a file to the specified endpoint
 * @param url - The endpoint URL
 * @param file - The file to upload
 * @param additionalData - Additional form data to include with the file
 * @param config - Optional Axios request configuration
 * @returns Promise resolving to the response data
 */
async function uploadFile<T = any>(
  url: string, 
  file: File, 
  additionalData: Record<string, any> = {}, 
  config: AxiosRequestConfig = {}
): Promise<T> {
  try {
    const formData = new FormData();
    formData.append('file', file);
    
    // Add any additional data to the form data
    Object.entries(additionalData).forEach(([key, value]) => {
      formData.append(key, value instanceof Object ? JSON.stringify(value) : String(value));
    });
    
    const uploadConfig: AxiosRequestConfig = {
      ...config,
      headers: {
        ...config.headers,
        'Content-Type': 'multipart/form-data',
      },
    };
    
    return await apiClient.post<T>(url, formData, uploadConfig);
  } catch (error) {
    handleApiError(error);
    throw error;
  }
}

/**
 * Downloads a file from the specified endpoint
 * @param url - The endpoint URL
 * @param filename - The name to save the file as
 * @param config - Optional Axios request configuration
 * @returns Promise resolving to the file blob
 */
async function downloadFile(
  url: string, 
  filename: string, 
  config: AxiosRequestConfig = {}
): Promise<Blob> {
  try {
    const downloadConfig: AxiosRequestConfig = {
      ...config,
      responseType: 'blob',
    };
    
    const response = await apiClient.get(url, downloadConfig);
    const blob = new Blob([response], { type: response.type });
    
    // Create a download link and trigger the download
    const downloadUrl = window.URL.createObjectURL(blob);
    const link = document.createElement('a');
    link.href = downloadUrl;
    link.download = filename;
    document.body.appendChild(link);
    link.click();
    document.body.removeChild(link);
    window.URL.revokeObjectURL(downloadUrl);
    
    return blob;
  } catch (error) {
    handleApiError(error);
    throw error;
  }
}

// Export the API client and utility methods
export {
  apiClient,
  get,
  post,
  put,
  patch,
  deleteRequest as delete,
  uploadFile,
  downloadFile,
};