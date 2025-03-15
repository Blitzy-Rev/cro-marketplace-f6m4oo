/**
 * TypeScript type definitions for experimental results-related data structures
 * used throughout the frontend application.
 */

import { Molecule } from './molecule.types';
import { PropertySource } from './molecule.types';
import { Document } from './document.types';

/**
 * Enumeration of possible result statuses in the workflow
 */
export enum ResultStatus {
  PENDING = 'PENDING',       // Result is pending processing
  PROCESSING = 'PROCESSING', // Result is being processed
  COMPLETED = 'COMPLETED',   // Result processing is complete
  FAILED = 'FAILED',         // Result processing failed
  REJECTED = 'REJECTED'      // Result was rejected during review
}

/**
 * Interface for experimental result property data
 */
export interface ResultProperty {
  /** ID of the molecule this property applies to */
  molecule_id: string;
  /** Name of the property (e.g., 'binding_affinity', 'ic50') */
  name: string;
  /** Experimental value of the property */
  value: number | string | boolean;
  /** Units for the property value (e.g., 'nM', '%') */
  units?: string | null;
}

/**
 * Core interface for experimental result data
 */
export interface Result {
  /** Unique identifier for the result */
  id: string;
  /** ID of the CRO submission this result belongs to */
  submission_id: string;
  /** Current status of the result in the workflow */
  status: ResultStatus;
  /** Experimental protocol used for generating results */
  protocol_used: string;
  /** Whether the result passed quality control checks */
  quality_control_passed?: boolean | null;
  /** Additional notes about the result */
  notes?: string | null;
  /** Additional metadata for the result */
  metadata?: Record<string, any> | null;
  /** Array of experimental property results */
  properties: ResultProperty[];
  /** Array of molecules included in this result */
  molecules?: Molecule[];
  /** Array of documents associated with this result */
  documents?: Document[];
  /** ID of the user who uploaded the result */
  uploaded_by: string;
  /** ISO timestamp when the result was uploaded */
  uploaded_at: string;
  /** ISO timestamp when the result was processed */
  processed_at?: string | null;
  /** ISO timestamp when the result was reviewed */
  reviewed_at?: string | null;
  /** ISO timestamp when the result was created */
  created_at: string;
  /** ISO timestamp when the result was last updated */
  updated_at: string;
}

/**
 * Interface for creating a new experimental result
 */
export interface ResultCreate {
  /** ID of the CRO submission this result belongs to */
  submission_id: string;
  /** Experimental protocol used for generating results */
  protocol_used: string;
  /** Additional notes about the result */
  notes?: string | null;
  /** Additional metadata for the result */
  metadata?: Record<string, any> | null;
}

/**
 * Interface for updating an existing experimental result
 */
export interface ResultUpdate {
  /** Updated experimental protocol */
  protocol_used?: string;
  /** Updated notes about the result */
  notes?: string | null | undefined;
  /** Updated metadata for the result */
  metadata?: Record<string, any> | null | undefined;
}

/**
 * Interface for updating the status of an experimental result
 */
export interface ResultStatusUpdate {
  /** New status for the result */
  status: ResultStatus;
  /** Whether the result passed quality control checks */
  quality_control_passed?: boolean;
  /** Reason for rejection if status is REJECTED */
  rejection_reason?: string;
}

/**
 * Interface for filtering experimental results
 */
export interface ResultFilter {
  /** Filter by submission ID */
  submission_id?: string | null;
  /** Filter by molecule ID */
  molecule_id?: string | null;
  /** Filter by result status */
  status?: ResultStatus | ResultStatus[] | null;
  /** Filter by uploader user ID */
  uploaded_by?: string | null;
  /** Filter results uploaded after this ISO timestamp */
  uploaded_after?: string | null;
  /** Filter results uploaded before this ISO timestamp */
  uploaded_before?: string | null;
}

/**
 * Interface for mapping CSV columns to result properties
 */
export interface CSVColumnMapping {
  /** Column name in the CSV file */
  csv_column: string;
  /** Property name to map to */
  property_name: string;
  /** Whether this mapping is required */
  is_required?: boolean;
}

/**
 * Interface for CSV column mapping configuration
 */
export interface ResultCSVMapping {
  /** Array of column to property mappings */
  column_mappings: CSVColumnMapping[];
  /** CSV column containing molecule IDs */
  molecule_id_column: string;
  /** Whether to skip the header row */
  skip_header?: boolean;
}

/**
 * Interface for CSV processing results
 */
export interface ResultCSVProcessResult {
  /** Total number of rows in the CSV */
  total_rows: number;
  /** Number of rows successfully processed */
  processed_rows: number;
  /** Number of rows that failed processing */
  failed_rows: number;
  /** Map of row numbers to error messages */
  errors?: Record<string, string[]>;
  /** Status of the CSV processing job */
  status: 'completed' | 'processing' | 'failed';
}

/**
 * Interface for processing a result and marking it as processed
 */
export interface ResultProcessRequest {
  /** ID of the result to process */
  result_id: string;
  /** Whether the result passed quality control checks */
  quality_control_passed: boolean;
  /** Additional notes about the processing */
  notes?: string | null;
}

/**
 * Interface for reviewing a result and optionally applying to molecules
 */
export interface ResultReviewRequest {
  /** ID of the result to review */
  result_id: string;
  /** Whether to apply result properties to molecules */
  apply_to_molecules: boolean;
  /** Additional notes about the review */
  notes?: string | null;
}

/**
 * Interface for paginated API responses for results
 */
export interface ResultResponse {
  /** Array of result items */
  items: Result[];
  /** Total number of results matching the query */
  total: number;
  /** Current page number */
  page: number;
  /** Page size */
  size: number;
  /** Total number of pages */
  pages: number;
}

/**
 * Interface for result state in Redux store
 */
export interface ResultState {
  /** Array of results in the current view */
  results: Result[];
  /** Array of selected result IDs */
  selectedResults: string[];
  /** Currently active result */
  currentResult: Result | null;
  /** Whether results are currently loading */
  loading: boolean;
  /** Error message if loading failed */
  error: string | null;
  /** Total number of results matching the current filter */
  totalCount: number;
  /** Current page number */
  currentPage: number;
  /** Number of results per page */
  pageSize: number;
  /** Total number of pages */
  totalPages: number;
  /** Current filter criteria */
  filters: ResultFilter;
}