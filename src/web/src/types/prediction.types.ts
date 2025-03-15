/**
 * TypeScript type definitions for AI prediction-related data structures.
 * This file defines interfaces for prediction requests, responses, job status tracking, and batch operations.
 */

// Default values for AI prediction operations
export const DEFAULT_MODEL_NAME = 'ai-engine-v2';
export const DEFAULT_MODEL_VERSION = '2.1.0';
export const MAX_BATCH_SIZE = 100;

/**
 * Enumeration of prediction workflow statuses
 */
export enum PredictionStatus {
  PENDING = 'PENDING',
  PROCESSING = 'PROCESSING',
  COMPLETED = 'COMPLETED',
  FAILED = 'FAILED'
}

/**
 * Interface for single molecule prediction request
 */
export interface PredictionRequest {
  /**
   * ID of the molecule to predict properties for
   */
  molecule_id?: string | null;
  
  /**
   * SMILES string of the molecule to predict properties for
   */
  smiles?: string | null;
  
  /**
   * Array of property names to predict
   */
  properties: string[];
  
  /**
   * AI model name to use for predictions
   */
  model_name?: string;
  
  /**
   * Specific AI model version to use
   */
  model_version?: string | null;
  
  /**
   * Whether to wait for prediction results or return immediately
   */
  wait_for_results?: boolean;
}

/**
 * Interface for batch prediction request
 */
export interface BatchPredictionRequest {
  /**
   * Array of molecule IDs to predict properties for
   */
  molecule_ids: string[];
  
  /**
   * Array of property names to predict
   */
  properties: string[];
  
  /**
   * AI model name to use for predictions
   */
  model_name?: string;
  
  /**
   * Specific AI model version to use
   */
  model_version?: string | null;
  
  /**
   * Additional options for the prediction request
   */
  options?: Record<string, any> | null;
}

/**
 * Interface for predicted property with value and confidence
 */
export interface PredictionProperty {
  /**
   * Name of the predicted property
   */
  property_name: string;
  
  /**
   * Predicted property value
   */
  value: number | string | boolean;
  
  /**
   * Units for the predicted value
   */
  units?: string | null;
  
  /**
   * Confidence score (0-1) for the prediction
   */
  confidence: number;
}

/**
 * Interface for prediction response with result data
 */
export interface PredictionResponse {
  /**
   * Unique identifier for the prediction
   */
  id: string;
  
  /**
   * ID of the molecule the prediction is for
   */
  molecule_id: string;
  
  /**
   * Name of the predicted property
   */
  property_name: string;
  
  /**
   * Predicted property value
   */
  value: number | string | boolean;
  
  /**
   * Units for the predicted value
   */
  units?: string | null;
  
  /**
   * Confidence score (0-1) for the prediction
   */
  confidence: number;
  
  /**
   * AI model name used for the prediction
   */
  model_name: string;
  
  /**
   * AI model version used for the prediction
   */
  model_version?: string | null;
  
  /**
   * Status of the prediction
   */
  status: PredictionStatus;
  
  /**
   * Error message if prediction failed
   */
  error_message?: string | null;
  
  /**
   * ISO timestamp when the prediction was created
   */
  created_at: string;
}

/**
 * Interface for batch prediction response with job information
 */
export interface BatchPredictionResponse {
  /**
   * Unique identifier for the batch prediction job
   */
  batch_id: string;
  
  /**
   * Current status of the batch prediction job
   */
  status: PredictionStatus;
  
  /**
   * Total number of predictions in the batch
   */
  total_count: number;
  
  /**
   * Number of completed predictions
   */
  completed_count: number;
  
  /**
   * Number of failed predictions
   */
  failed_count: number;
  
  /**
   * External job ID in the AI prediction engine
   */
  external_job_id?: string | null;
  
  /**
   * Error message if batch job failed
   */
  error_message?: string | null;
  
  /**
   * ISO timestamp when the batch job was created
   */
  created_at: string;
}

/**
 * Interface for prediction job status information
 */
export interface PredictionJobStatus {
  /**
   * Unique identifier for the batch prediction job
   */
  batch_id: string;
  
  /**
   * External job ID in the AI prediction engine
   */
  external_job_id?: string | null;
  
  /**
   * Current status of the prediction job
   */
  status: PredictionStatus;
  
  /**
   * Total number of predictions in the job
   */
  total_count: number;
  
  /**
   * Number of completed predictions
   */
  completed_count: number;
  
  /**
   * Number of failed predictions
   */
  failed_count: number;
  
  /**
   * Error message if job failed
   */
  error_message?: string | null;
  
  /**
   * ISO timestamp when the job was created
   */
  created_at: string;
  
  /**
   * ISO timestamp when the job was last updated
   */
  updated_at?: string | null;
}

/**
 * Interface for filtering predictions
 */
export interface PredictionFilter {
  /**
   * Filter by molecule ID
   */
  molecule_id?: string | null;
  
  /**
   * Filter by property names
   */
  property_names?: string[] | null;
  
  /**
   * Filter by AI model name
   */
  model_name?: string | null;
  
  /**
   * Filter by AI model version
   */
  model_version?: string | null;
  
  /**
   * Filter by prediction status
   */
  status?: PredictionStatus | null;
  
  /**
   * Filter by minimum confidence threshold
   */
  min_confidence?: number | null;
  
  /**
   * Filter by creation date (after)
   */
  created_after?: string | null;
  
  /**
   * Filter by creation date (before)
   */
  created_before?: string | null;
}

/**
 * Interface for AI prediction model information
 */
export interface PredictionModel {
  /**
   * Name of the AI prediction model
   */
  name: string;
  
  /**
   * Version of the AI prediction model
   */
  version: string;
  
  /**
   * Description of the AI prediction model
   */
  description: string;
  
  /**
   * List of properties supported by this model
   */
  supported_properties: string[];
}