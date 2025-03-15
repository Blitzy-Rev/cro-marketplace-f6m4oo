/**
 * API client for library-related operations in the Molecular Data Management and CRO Integration Platform.
 * 
 * This file provides functions for interacting with the backend library API endpoints,
 * including CRUD operations, molecule management within libraries, and library filtering.
 * 
 * @version 1.0.0
 */

import { get, post, put, delete as deleteRequest } from './apiClient';
import { API_ENDPOINTS } from '../constants/apiEndpoints';
import { 
  Library, 
  LibraryCreate, 
  LibraryUpdate, 
  LibraryFilter, 
  LibraryWithMolecules,
  MoleculeAddRemove,
  LibraryResponse,
  LibraryShare,
  LibraryShareCreate,
  LibraryShareUpdate
} from '../types/library.types';
import { PaginationParams } from '../types/api.types';
import { AxiosRequestConfig } from 'axios'; // ^1.4.0

/**
 * Retrieves a paginated list of libraries with optional filtering
 * 
 * @param pagination - Pagination parameters (page, page_size, sort_by, sort_order)
 * @param filters - Optional filter criteria for libraries
 * @param config - Optional Axios request configuration
 * @returns Promise resolving to paginated libraries response
 */
export async function getLibraries(
  pagination: PaginationParams,
  filters?: LibraryFilter,
  config?: AxiosRequestConfig
): Promise<LibraryResponse> {
  // Construct query parameters from pagination and filters
  const queryParams = new URLSearchParams();
  
  // Add pagination parameters
  queryParams.append('page', pagination.page.toString());
  queryParams.append('page_size', pagination.page_size.toString());
  
  if (pagination.sort_by) {
    queryParams.append('sort_by', pagination.sort_by);
  }
  
  if (pagination.sort_order) {
    queryParams.append('sort_order', pagination.sort_order);
  }
  
  // Add filter parameters if provided
  if (filters) {
    if (filters.name) queryParams.append('name', filters.name);
    if (filters.category) queryParams.append('category', filters.category);
    if (filters.owner_id) queryParams.append('owner_id', filters.owner_id);
    if (filters.is_public !== null) queryParams.append('is_public', filters.is_public.toString());
    if (filters.contains_molecule_id) queryParams.append('contains_molecule_id', filters.contains_molecule_id);
  }
  
  const url = `${API_ENDPOINTS.LIBRARIES.LIST}?${queryParams.toString()}`;
  return get<LibraryResponse>(url, config);
}

/**
 * Retrieves libraries owned by the current user
 * 
 * @param pagination - Pagination parameters
 * @param config - Optional Axios request configuration
 * @returns Promise resolving to user's libraries response
 */
export async function getMyLibraries(
  pagination: PaginationParams,
  config?: AxiosRequestConfig
): Promise<LibraryResponse> {
  const queryParams = new URLSearchParams();
  
  queryParams.append('page', pagination.page.toString());
  queryParams.append('page_size', pagination.page_size.toString());
  
  if (pagination.sort_by) {
    queryParams.append('sort_by', pagination.sort_by);
  }
  
  if (pagination.sort_order) {
    queryParams.append('sort_order', pagination.sort_order);
  }
  
  const url = `${API_ENDPOINTS.LIBRARIES.MY_LIBRARIES}?${queryParams.toString()}`;
  return get<LibraryResponse>(url, config);
}

/**
 * Retrieves a single library by ID
 * 
 * @param id - Library ID to retrieve
 * @param config - Optional Axios request configuration
 * @returns Promise resolving to library data
 */
export async function getLibrary(
  id: string,
  config?: AxiosRequestConfig
): Promise<Library> {
  const url = API_ENDPOINTS.LIBRARIES.GET.replace('{id}', id);
  return get<Library>(url, config);
}

/**
 * Retrieves a library with its molecules included
 * 
 * @param id - Library ID to retrieve
 * @param pagination - Pagination parameters for molecules
 * @param config - Optional Axios request configuration
 * @returns Promise resolving to library with molecules data
 */
export async function getLibraryWithMolecules(
  id: string,
  pagination: PaginationParams,
  config?: AxiosRequestConfig
): Promise<LibraryWithMolecules> {
  const queryParams = new URLSearchParams();
  
  queryParams.append('include_molecules', 'true');
  queryParams.append('page', pagination.page.toString());
  queryParams.append('page_size', pagination.page_size.toString());
  
  if (pagination.sort_by) {
    queryParams.append('sort_by', pagination.sort_by);
  }
  
  if (pagination.sort_order) {
    queryParams.append('sort_order', pagination.sort_order);
  }
  
  const url = `${API_ENDPOINTS.LIBRARIES.GET.replace('{id}', id)}?${queryParams.toString()}`;
  return get<LibraryWithMolecules>(url, config);
}

/**
 * Creates a new molecule library
 * 
 * @param library - Library creation data
 * @param config - Optional Axios request configuration
 * @returns Promise resolving to created library data
 */
export async function createLibrary(
  library: LibraryCreate,
  config?: AxiosRequestConfig
): Promise<Library> {
  return post<Library>(API_ENDPOINTS.LIBRARIES.CREATE, library, config);
}

/**
 * Updates an existing library's properties
 * 
 * @param id - Library ID to update
 * @param library - Library update data
 * @param config - Optional Axios request configuration
 * @returns Promise resolving to updated library data
 */
export async function updateLibrary(
  id: string,
  library: LibraryUpdate,
  config?: AxiosRequestConfig
): Promise<Library> {
  const url = API_ENDPOINTS.LIBRARIES.UPDATE.replace('{id}', id);
  return put<Library>(url, library, config);
}

/**
 * Deletes a library by ID
 * 
 * @param id - Library ID to delete
 * @param config - Optional Axios request configuration
 * @returns Promise resolving when deletion is complete
 */
export async function deleteLibrary(
  id: string,
  config?: AxiosRequestConfig
): Promise<void> {
  const url = API_ENDPOINTS.LIBRARIES.DELETE.replace('{id}', id);
  return deleteRequest<void>(url, config);
}

/**
 * Filters libraries by complex criteria
 * 
 * @param filters - Filter criteria for libraries
 * @param pagination - Pagination parameters
 * @param config - Optional Axios request configuration
 * @returns Promise resolving to filtered libraries response
 */
export async function filterLibraries(
  filters: LibraryFilter,
  pagination: PaginationParams,
  config?: AxiosRequestConfig
): Promise<LibraryResponse> {
  // Combine filters and pagination into a single request body
  const requestBody = {
    ...filters,
    page: pagination.page,
    page_size: pagination.page_size,
    sort_by: pagination.sort_by,
    sort_order: pagination.sort_order
  };
  
  return post<LibraryResponse>(API_ENDPOINTS.LIBRARIES.FILTER, requestBody, config);
}

/**
 * Adds a single molecule to a library
 * 
 * @param libraryId - Library ID to add molecule to
 * @param moleculeId - Molecule ID to add
 * @param config - Optional Axios request configuration
 * @returns Promise resolving to updated library data
 */
export async function addMoleculeToLibrary(
  libraryId: string,
  moleculeId: string,
  config?: AxiosRequestConfig
): Promise<Library> {
  const url = API_ENDPOINTS.LIBRARIES.ADD_MOLECULE
    .replace('{library_id}', libraryId)
    .replace('{molecule_id}', moleculeId);
  
  return post<Library>(url, {}, config);
}

/**
 * Removes a single molecule from a library
 * 
 * @param libraryId - Library ID to remove molecule from
 * @param moleculeId - Molecule ID to remove
 * @param config - Optional Axios request configuration
 * @returns Promise resolving to updated library data
 */
export async function removeMoleculeFromLibrary(
  libraryId: string,
  moleculeId: string,
  config?: AxiosRequestConfig
): Promise<Library> {
  const url = API_ENDPOINTS.LIBRARIES.REMOVE_MOLECULE
    .replace('{library_id}', libraryId)
    .replace('{molecule_id}', moleculeId);
  
  return deleteRequest<Library>(url, config);
}

/**
 * Adds multiple molecules to a library in a single request
 * 
 * @param libraryId - Library ID to add molecules to
 * @param molecules - Object containing array of molecule IDs to add
 * @param config - Optional Axios request configuration
 * @returns Promise resolving to updated library data
 */
export async function addMoleculesToLibrary(
  libraryId: string,
  molecules: MoleculeAddRemove,
  config?: AxiosRequestConfig
): Promise<Library> {
  const url = API_ENDPOINTS.LIBRARIES.ADD_MOLECULES.replace('{library_id}', libraryId);
  return post<Library>(url, molecules, config);
}

/**
 * Removes multiple molecules from a library in a single request
 * 
 * @param libraryId - Library ID to remove molecules from
 * @param molecules - Object containing array of molecule IDs to remove
 * @param config - Optional Axios request configuration
 * @returns Promise resolving to updated library data
 */
export async function removeMoleculesFromLibrary(
  libraryId: string,
  molecules: MoleculeAddRemove,
  config?: AxiosRequestConfig
): Promise<Library> {
  const url = API_ENDPOINTS.LIBRARIES.REMOVE_MOLECULES.replace('{library_id}', libraryId);
  return post<Library>(url, molecules, config);
}

/**
 * Retrieves molecules belonging to a specific library
 * 
 * @param libraryId - Library ID to get molecules from
 * @param pagination - Pagination parameters for the molecules
 * @param config - Optional Axios request configuration
 * @returns Promise resolving to molecules in the library
 */
export async function getLibraryMolecules(
  libraryId: string,
  pagination: PaginationParams,
  config?: AxiosRequestConfig
): Promise<any> {
  const queryParams = new URLSearchParams();
  
  queryParams.append('page', pagination.page.toString());
  queryParams.append('page_size', pagination.page_size.toString());
  
  if (pagination.sort_by) {
    queryParams.append('sort_by', pagination.sort_by);
  }
  
  if (pagination.sort_order) {
    queryParams.append('sort_order', pagination.sort_order);
  }
  
  const url = `${API_ENDPOINTS.LIBRARIES.GET_MOLECULES.replace('{library_id}', libraryId)}?${queryParams.toString()}`;
  return get(url, config);
}

/**
 * Checks if the current user has access to a specific library
 * 
 * @param libraryId - Library ID to check access for
 * @param config - Optional Axios request configuration
 * @returns Promise resolving to access information
 */
export async function checkLibraryAccess(
  libraryId: string,
  config?: AxiosRequestConfig
): Promise<{ access: boolean, access_level: string }> {
  const url = API_ENDPOINTS.LIBRARIES.CHECK_ACCESS.replace('{library_id}', libraryId);
  return get<{ access: boolean, access_level: string }>(url, config);
}

/**
 * Shares a library with another user
 * 
 * @param libraryId - Library ID to share
 * @param shareData - Data for creating the share (user ID and access level)
 * @param config - Optional Axios request configuration
 * @returns Promise resolving to library sharing data
 */
export async function shareLibrary(
  libraryId: string,
  shareData: LibraryShareCreate,
  config?: AxiosRequestConfig
): Promise<LibraryShare> {
  const url = `${API_ENDPOINTS.LIBRARIES.GET.replace('{id}', libraryId)}/share`;
  return post<LibraryShare>(url, shareData, config);
}

/**
 * Updates sharing permissions for a library
 * 
 * @param libraryId - Library ID to update sharing for
 * @param userId - User ID whose permissions to update
 * @param shareData - Updated sharing permissions
 * @param config - Optional Axios request configuration
 * @returns Promise resolving to updated library sharing data
 */
export async function updateLibraryShare(
  libraryId: string,
  userId: string,
  shareData: LibraryShareUpdate,
  config?: AxiosRequestConfig
): Promise<LibraryShare> {
  const url = `${API_ENDPOINTS.LIBRARIES.GET.replace('{id}', libraryId)}/share/${userId}`;
  return put<LibraryShare>(url, shareData, config);
}

/**
 * Removes sharing permissions for a library
 * 
 * @param libraryId - Library ID to remove sharing from
 * @param userId - User ID whose permissions to remove
 * @param config - Optional Axios request configuration
 * @returns Promise resolving when sharing is removed
 */
export async function removeLibraryShare(
  libraryId: string,
  userId: string,
  config?: AxiosRequestConfig
): Promise<void> {
  const url = `${API_ENDPOINTS.LIBRARIES.GET.replace('{id}', libraryId)}/share/${userId}`;
  return deleteRequest<void>(url, config);
}