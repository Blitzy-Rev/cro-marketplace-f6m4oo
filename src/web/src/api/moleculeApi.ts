/**
 * API client for molecule-related operations in the Molecular Data Management and CRO Integration Platform.
 * This file provides functions for interacting with the backend molecule API endpoints,
 * including CRUD operations, CSV uploads, library management, and AI predictions.
 */

import { 
  get, 
  post, 
  put, 
  delete as deleteRequest, 
  uploadFile, 
  downloadFile 
} from './apiClient';
import { API_ENDPOINTS } from '../constants/apiEndpoints';
import { 
  Molecule, 
  MoleculeCreate, 
  MoleculeUpdate, 
  MoleculeFilter, 
  MoleculeBatchCreate, 
  MoleculeCSVMapping, 
  MoleculeCSVProcessResult, 
  MoleculePredictionRequest, 
  MoleculePrediction 
} from '../types/molecule.types';
import { 
  ApiResponse, 
  PaginatedResponse, 
  FileUploadResponse, 
  BatchOperationResponse, 
  JobStatusResponse 
} from '../types/api.types';

/**
 * Retrieves a paginated list of molecules with optional filtering
 * @param page - Page number for pagination
 * @param pageSize - Number of items per page
 * @param filter - Optional filter criteria for molecules
 * @returns Paginated list of molecules
 */
export async function getMolecules(
  page = 1,
  pageSize = 25,
  filter?: MoleculeFilter
): Promise<ApiResponse<PaginatedResponse<Molecule>>> {
  // Construct query parameters from page, pageSize, and filter
  const queryParams: Record<string, any> = {
    page,
    page_size: pageSize,
  };

  // Add filter parameters if provided
  if (filter) {
    // Add simple filter properties to query params
    if (filter.search) queryParams.search = filter.search;
    if (filter.library_id) queryParams.library_id = filter.library_id;
    if (filter.status) queryParams.status = filter.status;
    if (filter.created_after) queryParams.created_after = filter.created_after;
    if (filter.created_before) queryParams.created_before = filter.created_before;
    if (filter.created_by) queryParams.created_by = filter.created_by;
    if (filter.sort_by) queryParams.sort_by = filter.sort_by;
    if (filter.sort_order) queryParams.sort_order = filter.sort_order;
    
    // If there are property filters, we need to handle them differently
    // as they might be more complex and require a POST request instead
    if (filter.properties && filter.properties.length > 0) {
      return filterMolecules(filter, page, pageSize);
    }
  }

  // Call get function with MOLECULES.LIST endpoint and query parameters
  return get<ApiResponse<PaginatedResponse<Molecule>>>(
    API_ENDPOINTS.MOLECULES.LIST,
    { params: queryParams }
  );
}

/**
 * Retrieves a single molecule by ID
 * @param id - Molecule ID
 * @returns Molecule data
 */
export async function getMolecule(id: string): Promise<ApiResponse<Molecule>> {
  // Replace {id} placeholder in MOLECULES.GET endpoint with the provided ID
  const endpoint = API_ENDPOINTS.MOLECULES.GET.replace('{id}', id);
  
  // Call get function with the constructed endpoint
  return get<ApiResponse<Molecule>>(endpoint);
}

/**
 * Creates a new molecule
 * @param molecule - Molecule data to create
 * @returns Created molecule data
 */
export async function createMolecule(
  molecule: MoleculeCreate
): Promise<ApiResponse<Molecule>> {
  // Call post function with MOLECULES.CREATE endpoint and molecule data
  return post<ApiResponse<Molecule>>(API_ENDPOINTS.MOLECULES.CREATE, molecule);
}

/**
 * Updates an existing molecule
 * @param id - Molecule ID
 * @param molecule - Molecule update data
 * @returns Updated molecule data
 */
export async function updateMolecule(
  id: string,
  molecule: MoleculeUpdate
): Promise<ApiResponse<Molecule>> {
  // Replace {id} placeholder in MOLECULES.UPDATE endpoint with the provided ID
  const endpoint = API_ENDPOINTS.MOLECULES.UPDATE.replace('{id}', id);
  
  // Call put function with the constructed endpoint and molecule update data
  return put<ApiResponse<Molecule>>(endpoint, molecule);
}

/**
 * Deletes a molecule by ID
 * @param id - Molecule ID
 * @returns Success response
 */
export async function deleteMolecule(id: string): Promise<ApiResponse<void>> {
  // Replace {id} placeholder in MOLECULES.DELETE endpoint with the provided ID
  const endpoint = API_ENDPOINTS.MOLECULES.DELETE.replace('{id}', id);
  
  // Call delete function with the constructed endpoint
  return deleteRequest<ApiResponse<void>>(endpoint);
}

/**
 * Filters molecules by complex criteria
 * @param filter - Filter criteria
 * @param page - Page number for pagination
 * @param pageSize - Number of items per page
 * @returns Filtered paginated list of molecules
 */
export async function filterMolecules(
  filter: MoleculeFilter,
  page = 1,
  pageSize = 25
): Promise<ApiResponse<PaginatedResponse<Molecule>>> {
  // Create request body with filter and pagination
  const requestBody = {
    ...filter,
    page,
    page_size: pageSize
  };
  
  // Call post function with MOLECULES.FILTER endpoint and filter criteria
  return post<ApiResponse<PaginatedResponse<Molecule>>>(
    API_ENDPOINTS.MOLECULES.FILTER,
    requestBody
  );
}

/**
 * Searches molecules by structural similarity
 * @param smiles - SMILES string to use as the search query
 * @param threshold - Similarity threshold (0-1)
 * @param page - Page number for pagination
 * @param pageSize - Number of items per page
 * @returns Paginated list of similar molecules
 */
export async function searchMoleculesBySimilarity(
  smiles: string,
  threshold = 0.7,
  page = 1,
  pageSize = 25
): Promise<ApiResponse<PaginatedResponse<Molecule>>> {
  // Construct request body with SMILES, threshold, and pagination
  const requestBody = {
    smiles,
    threshold,
    page,
    page_size: pageSize
  };
  
  // Call post function with MOLECULES.SEARCH_SIMILARITY endpoint and request body
  return post<ApiResponse<PaginatedResponse<Molecule>>>(
    API_ENDPOINTS.MOLECULES.SEARCH_SIMILARITY,
    requestBody
  );
}

/**
 * Searches molecules by substructure
 * @param smiles - SMILES string representing the substructure to search for
 * @param page - Page number for pagination
 * @param pageSize - Number of items per page
 * @returns Paginated list of molecules containing the substructure
 */
export async function searchMoleculesBySubstructure(
  smiles: string,
  page = 1,
  pageSize = 25
): Promise<ApiResponse<PaginatedResponse<Molecule>>> {
  // Construct request body with SMILES and pagination parameters
  const requestBody = {
    smiles,
    page,
    page_size: pageSize
  };
  
  // Call post function with MOLECULES.SEARCH_SUBSTRUCTURE endpoint and request body
  return post<ApiResponse<PaginatedResponse<Molecule>>>(
    API_ENDPOINTS.MOLECULES.SEARCH_SUBSTRUCTURE,
    requestBody
  );
}

/**
 * Uploads a CSV file containing molecular data
 * @param file - The CSV file to upload
 * @returns Upload response with storage key
 */
export async function uploadMoleculeCSV(
  file: File
): Promise<ApiResponse<FileUploadResponse>> {
  // Call uploadFile function with MOLECULES.UPLOAD_CSV endpoint and file
  return uploadFile<ApiResponse<FileUploadResponse>>(
    API_ENDPOINTS.MOLECULES.UPLOAD_CSV,
    file
  );
}

/**
 * Gets a preview of CSV file contents for column mapping
 * @param storageKey - Storage key from the file upload response
 * @returns CSV preview data
 */
export async function getCSVPreview(
  storageKey: string
): Promise<ApiResponse<{headers: string[], rows: string[][]}>> {
  // Replace {storage_key} placeholder in MOLECULES.CSV_PREVIEW endpoint
  const endpoint = API_ENDPOINTS.MOLECULES.CSV_PREVIEW.replace(
    '{storage_key}',
    storageKey
  );
  
  // Call get function with the constructed endpoint
  return get<ApiResponse<{headers: string[], rows: string[][]}>>(endpoint);
}

/**
 * Imports molecules from a previously uploaded CSV file
 * @param storageKey - Storage key from the file upload response
 * @param mapping - Column mapping configuration
 * @returns CSV processing result
 */
export async function importMoleculesFromCSV(
  storageKey: string,
  mapping: MoleculeCSVMapping
): Promise<ApiResponse<MoleculeCSVProcessResult>> {
  // Replace {storage_key} placeholder in MOLECULES.IMPORT_CSV endpoint
  const endpoint = API_ENDPOINTS.MOLECULES.IMPORT_CSV.replace(
    '{storage_key}',
    storageKey
  );
  
  // Call post function with the constructed endpoint and mapping data
  return post<ApiResponse<MoleculeCSVProcessResult>>(endpoint, mapping);
}

/**
 * Creates multiple molecules in a single request
 * @param batch - Batch creation data containing multiple molecules
 * @returns Batch operation result
 */
export async function batchCreateMolecules(
  batch: MoleculeBatchCreate
): Promise<ApiResponse<BatchOperationResponse>> {
  // Call post function with MOLECULES.BATCH_CREATE endpoint and batch data
  return post<ApiResponse<BatchOperationResponse>>(
    API_ENDPOINTS.MOLECULES.BATCH_CREATE,
    batch
  );
}

/**
 * Adds a molecule to a library
 * @param moleculeId - Molecule ID
 * @param libraryId - Library ID
 * @returns Success response
 */
export async function addMoleculeToLibrary(
  moleculeId: string,
  libraryId: string
): Promise<ApiResponse<void>> {
  // Replace {molecule_id} and {library_id} placeholders in endpoint
  const endpoint = API_ENDPOINTS.MOLECULES.ADD_TO_LIBRARY
    .replace('{molecule_id}', moleculeId)
    .replace('{library_id}', libraryId);
  
  // Call post function with the constructed endpoint
  return post<ApiResponse<void>>(endpoint);
}

/**
 * Removes a molecule from a library
 * @param moleculeId - Molecule ID
 * @param libraryId - Library ID
 * @returns Success response
 */
export async function removeMoleculeFromLibrary(
  moleculeId: string,
  libraryId: string
): Promise<ApiResponse<void>> {
  // Replace {molecule_id} and {library_id} placeholders in endpoint
  const endpoint = API_ENDPOINTS.MOLECULES.REMOVE_FROM_LIBRARY
    .replace('{molecule_id}', moleculeId)
    .replace('{library_id}', libraryId);
  
  // Call delete function with the constructed endpoint
  return deleteRequest<ApiResponse<void>>(endpoint);
}

/**
 * Gets molecules in a specific library
 * @param libraryId - Library ID
 * @param page - Page number for pagination
 * @param pageSize - Number of items per page
 * @param filter - Optional filter criteria for molecules
 * @returns Paginated list of molecules in the library
 */
export async function getMoleculesByLibrary(
  libraryId: string,
  page = 1,
  pageSize = 25,
  filter?: MoleculeFilter
): Promise<ApiResponse<PaginatedResponse<Molecule>>> {
  // Replace {library_id} placeholder in GET_BY_LIBRARY endpoint
  const endpoint = API_ENDPOINTS.MOLECULES.GET_BY_LIBRARY.replace(
    '{library_id}',
    libraryId
  );
  
  // Construct query parameters from page, pageSize, and filter
  const queryParams: Record<string, any> = {
    page,
    page_size: pageSize,
  };
  
  // Add filter parameters if provided
  if (filter) {
    if (filter.search) queryParams.search = filter.search;
    if (filter.status) queryParams.status = filter.status;
    if (filter.created_after) queryParams.created_after = filter.created_after;
    if (filter.created_before) queryParams.created_before = filter.created_before;
    if (filter.created_by) queryParams.created_by = filter.created_by;
    if (filter.sort_by) queryParams.sort_by = filter.sort_by;
    if (filter.sort_order) queryParams.sort_order = filter.sort_order;
  }
  
  // Call get function with the constructed endpoint and query parameters
  return get<ApiResponse<PaginatedResponse<Molecule>>>(endpoint, {
    params: queryParams
  });
}

/**
 * Requests AI property predictions for molecules
 * @param request - Prediction request with molecules and properties to predict
 * @returns Prediction job status
 */
export async function requestMoleculePredictions(
  request: MoleculePredictionRequest
): Promise<ApiResponse<JobStatusResponse>> {
  // Call post function with PREDICTIONS.REQUEST endpoint and prediction request data
  return post<ApiResponse<JobStatusResponse>>(
    API_ENDPOINTS.PREDICTIONS.REQUEST,
    request
  );
}

/**
 * Checks the status of a prediction job
 * @param jobId - Prediction job ID
 * @returns Current job status
 */
export async function getPredictionStatus(
  jobId: string
): Promise<ApiResponse<JobStatusResponse>> {
  // Replace {job_id} placeholder in PREDICTIONS.STATUS endpoint
  const endpoint = API_ENDPOINTS.PREDICTIONS.STATUS.replace(
    '{job_id}',
    jobId
  );
  
  // Call get function with the constructed endpoint
  return get<ApiResponse<JobStatusResponse>>(endpoint);
}

/**
 * Gets the results of a completed prediction job
 * @param jobId - Prediction job ID
 * @returns Prediction results
 */
export async function getPredictionResults(
  jobId: string
): Promise<ApiResponse<MoleculePrediction[]>> {
  // Replace {job_id} placeholder in PREDICTIONS.RESULTS endpoint
  const endpoint = API_ENDPOINTS.PREDICTIONS.RESULTS.replace(
    '{job_id}',
    jobId
  );
  
  // Call get function with the constructed endpoint
  return get<ApiResponse<MoleculePrediction[]>>(endpoint);
}

/**
 * Gets all predictions for a specific molecule
 * @param moleculeId - Molecule ID
 * @returns Molecule predictions
 */
export async function getMoleculePredictions(
  moleculeId: string
): Promise<ApiResponse<MoleculePrediction[]>> {
  // Replace {molecule_id} placeholder in PREDICTIONS.BY_MOLECULE endpoint
  const endpoint = API_ENDPOINTS.PREDICTIONS.BY_MOLECULE.replace(
    '{molecule_id}',
    moleculeId
  );
  
  // Call get function with the constructed endpoint
  return get<ApiResponse<MoleculePrediction[]>>(endpoint);
}