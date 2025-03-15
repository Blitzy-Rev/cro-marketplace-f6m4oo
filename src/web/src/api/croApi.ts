/**
 * API client module for Contract Research Organization (CRO) related operations in the
 * Molecular Data Management and CRO Integration Platform.
 * 
 * This file provides functions to interact with the CRO service endpoints, enabling
 * listing, creation, retrieval, updating, and deletion of CRO services.
 */

import { get, post, put, delete as deleteRequest } from './apiClient';
import { API_ENDPOINTS } from '../constants/apiEndpoints';
import { 
  CROService, 
  CROServiceCreate, 
  CROServiceUpdate, 
  CROServiceFilter,
  CROServiceResponse,
  CROServicesResponse
} from '../types/cro.types';

/**
 * Fetches a paginated list of CRO services with optional filtering
 * 
 * @param page - Page number for pagination (1-based)
 * @param pageSize - Number of items per page
 * @param filters - Optional filter criteria for CRO services
 * @returns Promise resolving to paginated CRO services response
 */
export async function getCROServices(
  page: number = 1,
  pageSize: number = 10,
  filters: CROServiceFilter = {}
): Promise<CROServicesResponse> {
  // Build query parameters
  const queryParams = new URLSearchParams();
  queryParams.append('page', page.toString());
  queryParams.append('size', pageSize.toString());
  
  // Add filter parameters if they exist
  if (filters.name_contains) queryParams.append('name_contains', filters.name_contains);
  if (filters.provider_contains) queryParams.append('provider_contains', filters.provider_contains);
  if (filters.service_type) queryParams.append('service_type', filters.service_type);
  if (filters.price_min !== null && filters.price_min !== undefined) {
    queryParams.append('price_min', filters.price_min.toString());
  }
  if (filters.price_max !== null && filters.price_max !== undefined) {
    queryParams.append('price_max', filters.price_max.toString());
  }
  if (filters.turnaround_max !== null && filters.turnaround_max !== undefined) {
    queryParams.append('turnaround_max', filters.turnaround_max.toString());
  }
  if (filters.active_only !== null && filters.active_only !== undefined) {
    queryParams.append('active_only', filters.active_only.toString());
  }
  
  // Build URL with query parameters
  const url = `${API_ENDPOINTS.CRO.LIST}?${queryParams.toString()}`;
  
  // Make API request
  return get<CROServicesResponse>(url);
}

/**
 * Fetches a single CRO service by ID
 * 
 * @param id - Unique identifier of the CRO service
 * @returns Promise resolving to a single CRO service response
 */
export async function getCROService(id: string): Promise<CROServiceResponse> {
  const url = API_ENDPOINTS.CRO.GET.replace('{id}', id);
  return get<CROServiceResponse>(url);
}

/**
 * Creates a new CRO service
 * 
 * @param serviceData - Data for the new CRO service
 * @returns Promise resolving to the created CRO service
 */
export async function createCROService(
  serviceData: CROServiceCreate
): Promise<CROServiceResponse> {
  return post<CROServiceResponse>(API_ENDPOINTS.CRO.CREATE, serviceData);
}

/**
 * Updates an existing CRO service
 * 
 * @param id - Unique identifier of the CRO service to update
 * @param serviceData - Updated service data
 * @returns Promise resolving to the updated CRO service
 */
export async function updateCROService(
  id: string,
  serviceData: CROServiceUpdate
): Promise<CROServiceResponse> {
  const url = API_ENDPOINTS.CRO.UPDATE.replace('{id}', id);
  return put<CROServiceResponse>(url, serviceData);
}

/**
 * Deletes a CRO service by ID
 * 
 * @param id - Unique identifier of the CRO service to delete
 * @returns Promise resolving when the service is deleted
 */
export async function deleteCROService(id: string): Promise<void> {
  const url = API_ENDPOINTS.CRO.DELETE.replace('{id}', id);
  return deleteRequest<void>(url);
}

/**
 * Activates a CRO service that was previously deactivated
 * 
 * @param id - Unique identifier of the CRO service to activate
 * @returns Promise resolving to the activated CRO service
 */
export async function activateCROService(id: string): Promise<CROServiceResponse> {
  const url = API_ENDPOINTS.CRO.UPDATE.replace('{id}', id);
  return put<CROServiceResponse>(url, { active: true });
}

/**
 * Deactivates a CRO service without deleting it
 * 
 * @param id - Unique identifier of the CRO service to deactivate
 * @returns Promise resolving to the deactivated CRO service
 */
export async function deactivateCROService(id: string): Promise<CROServiceResponse> {
  const url = API_ENDPOINTS.CRO.UPDATE.replace('{id}', id);
  return put<CROServiceResponse>(url, { active: false });
}