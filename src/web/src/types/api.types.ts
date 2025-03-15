/**
 * API Types for the Molecular Data Management and CRO Integration Platform
 * 
 * This file contains common TypeScript interfaces and types for API communication
 * between the frontend and backend services. These types enforce consistent
 * data structures for requests and responses throughout the application.
 */

/**
 * Generic interface for successful API responses with typed data payload
 */
export interface ApiResponse<T = any> {
  success: boolean;
  message: string;
  data: T;
}

/**
 * Interface for API error responses with error code and detailed validation errors
 */
export interface ApiError {
  success: boolean;
  message: string;
  error_code: string;
  details: Record<string, string[]>;
}

/**
 * Generic interface for paginated API responses
 */
export interface PaginatedResponse<T> {
  items: T[];
  total: number;
  page: number;
  page_size: number;
  total_pages: number;
}

/**
 * Interface for pagination parameters in API requests
 */
export interface PaginationParams {
  page: number;
  page_size: number;
  sort_by: string | null;
  sort_order: SortOrder | null;
}

/**
 * Enumeration for sort order options in API requests
 */
export enum SortOrder {
  ASC = 'asc',
  DESC = 'desc'
}

/**
 * Interface for API health check response
 */
export interface ApiStatus {
  status: string;
  version: string;
  uptime: number;
}

/**
 * Interface for field-level validation errors in API responses
 */
export interface ApiValidationError {
  field: string;
  message: string;
}

/**
 * Enumeration of error codes returned by the API
 */
export enum ApiErrorCode {
  VALIDATION_ERROR = 'validation_error',
  AUTHENTICATION_ERROR = 'authentication_error',
  AUTHORIZATION_ERROR = 'authorization_error',
  RESOURCE_NOT_FOUND = 'resource_not_found',
  RESOURCE_CONFLICT = 'resource_conflict',
  INTERNAL_SERVER_ERROR = 'internal_server_error',
  SERVICE_UNAVAILABLE = 'service_unavailable',
  RATE_LIMIT_EXCEEDED = 'rate_limit_exceeded'
}

/**
 * Interface for file upload response data
 */
export interface FileUploadResponse {
  file_id: string;
  filename: string;
  storage_key: string;
  size: number;
  mime_type: string;
  upload_date: string;
}

/**
 * Interface for batch operation response data
 */
export interface BatchOperationResponse {
  total: number;
  successful: number;
  failed: number;
  errors: Array<{ id: string; error: string }>;
}

/**
 * Enumeration of background job status values
 */
export enum JobStatus {
  PENDING = 'pending',
  PROCESSING = 'processing',
  COMPLETED = 'completed',
  FAILED = 'failed'
}

/**
 * Interface for background job status response
 */
export interface JobStatusResponse {
  job_id: string;
  status: JobStatus;
  progress: number;
  message: string;
  created_at: string;
  updated_at: string;
}

/**
 * Interface for search parameters in API requests
 */
export interface SearchParams {
  query: string;
  fields: string[];
  page: number;
  page_size: number;
}

/**
 * Enumeration of filter operators for advanced filtering
 */
export enum FilterOperator {
  EQ = 'eq',
  NEQ = 'neq',
  GT = 'gt',
  GTE = 'gte',
  LT = 'lt',
  LTE = 'lte',
  CONTAINS = 'contains',
  IN = 'in'
}

/**
 * Interface for filter conditions in advanced filtering
 */
export interface FilterCondition {
  field: string;
  operator: FilterOperator;
  value: any;
}

/**
 * Enumeration of logical operators for combining filter conditions
 */
export enum LogicalOperator {
  AND = 'and',
  OR = 'or'
}

/**
 * Interface for advanced filtering parameters in API requests
 */
export interface AdvancedFilterParams {
  conditions: FilterCondition[];
  logical_operator: LogicalOperator;
  page: number;
  page_size: number;
  sort_by: string | null;
  sort_order: SortOrder | null;
}