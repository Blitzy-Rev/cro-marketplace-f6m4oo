/**
 * API client for interacting with the AI prediction engine.
 * This file provides functions for requesting property predictions, checking prediction status,
 * and retrieving prediction results for molecules.
 * 
 * The AI prediction engine (integrated external service) provides molecular property predictions
 * based on SMILES structures or molecule IDs. Predictions can be requested individually or in 
 * batches, with results delivered either synchronously or asynchronously depending on complexity.
 * 
 * @version 1.0.0
 */

import { get, post } from './apiClient'; // v1.4.0
import { API_ENDPOINTS } from '../constants/apiEndpoints';
import { PREDICTABLE_PROPERTIES } from '../constants/moleculeProperties';
import {
  PredictionRequest,
  BatchPredictionRequest,
  PredictionResponse,
  BatchPredictionResponse,
  PredictionJobStatus,
  PredictionFilter,
  PredictionModel,
  DEFAULT_MODEL_NAME,
  DEFAULT_MODEL_VERSION,
  MAX_BATCH_SIZE
} from '../types/prediction.types';

/**
 * Requests property predictions for a single molecule
 * 
 * This function sends a request to the AI engine to predict properties for a
 * single molecule identified by either molecule_id or SMILES. It can be configured
 * to wait for results or return immediately with a job ID for asynchronous processing.
 * 
 * @param request - The prediction request parameters
 * @returns Promise resolving to prediction response or job status
 * @throws Error if neither molecule_id nor SMILES is provided
 * @throws Error if properties array is empty
 * @throws Error if requested properties are not predictable
 */
export async function requestPrediction(
  request: PredictionRequest
): Promise<PredictionResponse | BatchPredictionResponse> {
  // Validate that either molecule_id or smiles is provided
  if (!request.molecule_id && !request.smiles) {
    throw new Error('Either molecule_id or smiles must be provided');
  }

  // Validate that properties array is not empty and contains only predictable properties
  if (!request.properties || request.properties.length === 0) {
    throw new Error('At least one property must be specified for prediction');
  }

  // Check if all requested properties are predictable
  const invalidProperties = request.properties.filter(
    prop => !PREDICTABLE_PROPERTIES.includes(prop)
  );
  
  if (invalidProperties.length > 0) {
    throw new Error(`The following properties cannot be predicted: ${invalidProperties.join(', ')}`);
  }

  // Set default model name and version if not provided
  const payload = {
    ...request,
    model_name: request.model_name || DEFAULT_MODEL_NAME,
    model_version: request.model_version || DEFAULT_MODEL_VERSION
  };

  // Send POST request to prediction endpoint
  return post<PredictionResponse | BatchPredictionResponse>(API_ENDPOINTS.PREDICTIONS.REQUEST, payload);
}

/**
 * Requests property predictions for multiple molecules in batch
 * 
 * This function sends a batch request to the AI engine to predict properties for
 * multiple molecules identified by their IDs. Batch processing is more efficient
 * for large numbers of molecules but is always asynchronous.
 * 
 * @param request - The batch prediction request parameters
 * @returns Promise resolving to batch prediction job status
 * @throws Error if molecule_ids array is empty
 * @throws Error if molecule_ids array exceeds maximum batch size
 * @throws Error if properties array is empty
 * @throws Error if requested properties are not predictable
 */
export async function requestBatchPrediction(
  request: BatchPredictionRequest
): Promise<BatchPredictionResponse> {
  // Validate that molecule_ids array is not empty
  if (!request.molecule_ids || request.molecule_ids.length === 0) {
    throw new Error('At least one molecule_id must be provided for batch prediction');
  }

  // Validate that molecule_ids array does not exceed MAX_BATCH_SIZE
  if (request.molecule_ids.length > MAX_BATCH_SIZE) {
    throw new Error(`Batch size exceeds maximum limit of ${MAX_BATCH_SIZE} molecules`);
  }

  // Validate that properties array is not empty and contains only predictable properties
  if (!request.properties || request.properties.length === 0) {
    throw new Error('At least one property must be specified for prediction');
  }

  // Check if all requested properties are predictable
  const invalidProperties = request.properties.filter(
    prop => !PREDICTABLE_PROPERTIES.includes(prop)
  );
  
  if (invalidProperties.length > 0) {
    throw new Error(`The following properties cannot be predicted: ${invalidProperties.join(', ')}`);
  }

  // Set default model name and version if not provided
  const payload = {
    ...request,
    model_name: request.model_name || DEFAULT_MODEL_NAME,
    model_version: request.model_version || DEFAULT_MODEL_VERSION,
    batch: true // Explicitly mark as batch request
  };

  // Send POST request to prediction endpoint with batch flag
  return post<BatchPredictionResponse>(API_ENDPOINTS.PREDICTIONS.REQUEST, payload);
}

/**
 * Gets the status of a prediction job
 * 
 * This function checks the current status of an asynchronous prediction job.
 * It can be used to poll for completion of batch predictions or single predictions
 * that were submitted with wait_for_results=false.
 * 
 * @param jobId - The prediction job ID
 * @returns Promise resolving to prediction job status
 * @throws Error if jobId is not provided
 */
export async function getPredictionStatus(jobId: string): Promise<PredictionJobStatus> {
  // Validate that jobId is provided
  if (!jobId) {
    throw new Error('Job ID must be provided');
  }

  // Send GET request to prediction status endpoint with jobId
  const endpoint = API_ENDPOINTS.PREDICTIONS.STATUS.replace('{job_id}', jobId);
  return get<PredictionJobStatus>(endpoint);
}

/**
 * Gets the results of a completed prediction job
 * 
 * This function retrieves the results of a completed prediction job.
 * It should only be called after the job status is COMPLETED.
 * 
 * @param jobId - The prediction job ID
 * @returns Promise resolving to array of prediction results
 * @throws Error if jobId is not provided
 */
export async function getPredictionResults(jobId: string): Promise<PredictionResponse[]> {
  // Validate that jobId is provided
  if (!jobId) {
    throw new Error('Job ID must be provided');
  }

  // Send GET request to prediction results endpoint with jobId
  const endpoint = API_ENDPOINTS.PREDICTIONS.RESULTS.replace('{job_id}', jobId);
  return get<PredictionResponse[]>(endpoint);
}

/**
 * Gets all predictions for a specific molecule
 * 
 * This function retrieves all predictions that have been made for a specific molecule,
 * with optional filtering by property, model, status, and other criteria.
 * 
 * @param moleculeId - The molecule ID
 * @param filter - Optional filter parameters for predictions
 * @returns Promise resolving to array of prediction results for the molecule
 * @throws Error if moleculeId is not provided
 */
export async function getMoleculePredictions(
  moleculeId: string,
  filter?: PredictionFilter
): Promise<PredictionResponse[]> {
  // Validate that moleculeId is provided
  if (!moleculeId) {
    throw new Error('Molecule ID must be provided');
  }

  // Prepare query parameters from filter object
  const queryParams: Record<string, string> = {};
  
  if (filter) {
    if (filter.property_names && filter.property_names.length > 0) {
      queryParams.property_names = filter.property_names.join(',');
    }
    
    if (filter.model_name) {
      queryParams.model_name = filter.model_name;
    }
    
    if (filter.model_version) {
      queryParams.model_version = filter.model_version;
    }
    
    if (filter.status) {
      queryParams.status = filter.status;
    }
    
    if (filter.min_confidence !== undefined && filter.min_confidence !== null) {
      queryParams.min_confidence = filter.min_confidence.toString();
    }
    
    if (filter.created_after) {
      queryParams.created_after = filter.created_after;
    }
    
    if (filter.created_before) {
      queryParams.created_before = filter.created_before;
    }
  }

  // Send GET request to molecule predictions endpoint with moleculeId and query parameters
  const endpoint = API_ENDPOINTS.PREDICTIONS.BY_MOLECULE.replace('{molecule_id}', moleculeId);
  return get<PredictionResponse[]>(endpoint, { params: queryParams });
}

/**
 * Gets available AI prediction models and their supported properties
 * 
 * This function retrieves information about all available AI prediction models,
 * including their names, versions, and the molecular properties they can predict.
 * 
 * @returns Promise resolving to array of available prediction models
 */
export async function getPredictionModels(): Promise<PredictionModel[]> {
  // Send GET request to prediction models endpoint
  return get<PredictionModel[]>(API_ENDPOINTS.PREDICTIONS.MODELS);
}