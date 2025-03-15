/**
 * TypeScript type definitions for submission-related data structures in the
 * Molecular Data Management and CRO Integration Platform.
 * 
 * This file defines interfaces and types for CRO submissions, including creation,
 * updating, filtering, and status management throughout the submission workflow.
 */

import { 
  SubmissionStatus, 
  SubmissionAction, 
  ACTIVE_STATUSES, 
  TERMINAL_STATUSES, 
  EDITABLE_STATUSES
} from '../constants/submissionStatus';

import { 
  DocumentType,
  REQUIRED_DOCUMENT_TYPES
} from '../constants/documentTypes';

import { Document } from './document.types';
import { Molecule } from './molecule.types';
import { CROService } from './cro.types';
import { User } from './user.types';

/**
 * Base interface for submission data with common fields
 */
export interface SubmissionBase {
  /** Name/title of the submission */
  name: string;
  
  /** ID of the CRO service being requested */
  cro_service_id: string;
  
  /** Optional description of the submission */
  description: string | null;
  
  /** Experimental specifications as a flexible JSON object */
  specifications: Record<string, any> | null;
  
  /** Array of molecule IDs included in the submission */
  molecule_ids: string[] | null;
  
  /** Current status of the submission */
  status: SubmissionStatus | null;
  
  /** Additional metadata as a flexible JSON object */
  metadata: Record<string, any> | null;
}

/**
 * Interface for creating a new submission
 */
export interface SubmissionCreate {
  /** Name/title of the submission */
  name: string;
  
  /** ID of the CRO service being requested */
  cro_service_id: string;
  
  /** Optional description of the submission */
  description: string | null;
  
  /** Experimental specifications as a flexible JSON object */
  specifications: Record<string, any> | null;
  
  /** Array of molecule IDs included in the submission */
  molecule_ids: string[] | null;
  
  /** ID of the user creating the submission */
  created_by: string;
}

/**
 * Interface for updating an existing submission with partial data
 */
export interface SubmissionUpdate {
  /** Updated name/title (optional) */
  name?: string;
  
  /** Updated CRO service ID (optional) */
  cro_service_id?: string;
  
  /** Updated description (optional) */
  description?: string | null;
  
  /** Updated experimental specifications (optional) */
  specifications?: Record<string, any> | null;
  
  /** Updated array of molecule IDs (optional) */
  molecule_ids?: string[] | null;
  
  /** Updated status (optional) */
  status?: SubmissionStatus;
  
  /** Updated metadata (optional) */
  metadata?: Record<string, any> | null;
}

/**
 * Interface for submission data with all fields including relationships
 */
export interface Submission {
  /** Unique identifier for the submission */
  id: string;
  
  /** Name/title of the submission */
  name: string;
  
  /** ID of the CRO service being requested */
  cro_service_id: string;
  
  /** Optional description of the submission */
  description: string | null;
  
  /** Experimental specifications as a flexible JSON object */
  specifications: Record<string, any> | null;
  
  /** Current status of the submission */
  status: SubmissionStatus;
  
  /** Additional metadata as a flexible JSON object */
  metadata: Record<string, any> | null;
  
  /** ID of the user who created the submission */
  created_by: string;
  
  /** ISO timestamp when the submission was created */
  created_at: string;
  
  /** ISO timestamp when the submission was last updated */
  updated_at: string;
  
  /** ISO timestamp when the submission was submitted to CRO */
  submitted_at: string | null;
  
  /** ISO timestamp when the submission was approved */
  approved_at: string | null;
  
  /** ISO timestamp when the submission was completed */
  completed_at: string | null;
  
  /** Price quoted by the CRO */
  price: number | null;
  
  /** Currency of the quoted price */
  price_currency: string | null;
  
  /** Estimated turnaround time in days */
  estimated_turnaround_days: number | null;
  
  /** Estimated completion date as ISO timestamp */
  estimated_completion_date: string | null;
  
  /** CRO service details (populated in responses) */
  cro_service: CROService | null;
  
  /** User who created the submission (populated in responses) */
  creator: User | null;
  
  /** Array of molecules included in the submission (populated in responses) */
  molecules: Molecule[] | null;
  
  /** Array of documents attached to the submission (populated in responses) */
  documents: Document[] | null;
  
  /** Array of experimental results (populated in responses) */
  results: SubmissionResult[] | null;
  
  /** User-friendly description of the current status */
  status_description: string | null;
  
  /** Number of documents attached to the submission */
  document_count: number | null;
  
  /** Number of molecules included in the submission */
  molecule_count: number | null;
  
  /** Whether the submission is in an editable state */
  is_editable: boolean;
  
  /** Whether the submission is in an active state */
  is_active: boolean;
}

/**
 * Interface for filtering submissions in API requests
 */
export interface SubmissionFilter {
  /** Filter by partial submission name */
  name_contains: string | null;
  
  /** Filter by creator user ID */
  created_by: string | null;
  
  /** Filter by CRO service ID */
  cro_service_id: string | null;
  
  /** Filter by submission status */
  status: SubmissionStatus[] | null;
  
  /** Filter for active submissions only */
  active_only: boolean | null;
  
  /** Filter by molecule ID */
  molecule_id: string | null;
  
  /** Filter by creation date (after) */
  created_after: string | null;
  
  /** Filter by creation date (before) */
  created_before: string | null;
}

/**
 * Interface for performing actions on a submission
 */
export interface SubmissionActionRequest {
  /** Action to perform on the submission */
  action: SubmissionAction;
  
  /** Additional data for the action (e.g., pricing info) */
  data: Record<string, any> | null;
  
  /** Optional comment explaining the action */
  comment: string | null;
}

/**
 * Interface for submission with document requirements information
 */
export interface SubmissionWithDocumentRequirements {
  /** The submission object */
  submission: Submission;
  
  /** Array of required document types with status */
  required_documents: Array<{ 
    type: DocumentType, 
    description: string, 
    exists: boolean 
  }>;
  
  /** Array of optional document types with status */
  optional_documents: Array<{ 
    type: DocumentType, 
    description: string, 
    exists: boolean 
  }>;
  
  /** Array of existing documents attached to the submission */
  existing_documents: Document[];
}

/**
 * Interface for submission status counts
 */
export interface SubmissionStatusCount {
  /** Submission status */
  status: SubmissionStatus;
  
  /** Count of submissions in this status */
  count: number;
}

/**
 * Interface for updating submission pricing by CRO
 */
export interface SubmissionPricingUpdate {
  /** Price quoted by the CRO */
  price: number;
  
  /** Currency of the quoted price */
  price_currency: string;
  
  /** Estimated turnaround time in days */
  estimated_turnaround_days: number;
  
  /** Optional comment explaining the pricing */
  comment: string | null;
}

/**
 * Interface for experimental results from CRO
 */
export interface SubmissionResult {
  /** Unique identifier for the result */
  id: string;
  
  /** ID of the submission these results belong to */
  submission_id: string;
  
  /** Status of the result (e.g., "complete", "preliminary") */
  status: string;
  
  /** Raw result data as a flexible JSON object */
  data: Record<string, any>;
  
  /** ISO timestamp when the results were uploaded */
  uploaded_at: string;
  
  /** ID of the user who uploaded the results */
  uploaded_by: string;
  
  /** Array of molecule-specific result properties */
  molecule_results: Array<{
    molecule_id: string,
    properties: Record<string, any>
  }>;
}

/**
 * Interface for paginated submission API response
 */
export interface SubmissionResponse {
  /** Array of submission objects */
  items: Submission[];
  
  /** Total number of submissions matching the filter criteria */
  total: number;
  
  /** Current page number */
  page: number;
  
  /** Number of items per page */
  size: number;
  
  /** Total number of pages */
  pages: number;
}

/**
 * Interface for submission state in Redux store
 */
export interface SubmissionState {
  /** Array of loaded submissions */
  submissions: Submission[];
  
  /** Currently selected submission */
  selectedSubmission: Submission | null;
  
  /** Loading state */
  loading: boolean;
  
  /** Error message, if any */
  error: string | null;
  
  /** Total count of submissions matching current filters */
  totalCount: number;
  
  /** Current page number */
  currentPage: number;
  
  /** Number of submissions per page */
  pageSize: number;
  
  /** Total number of pages */
  totalPages: number;
  
  /** Current filter criteria */
  filters: SubmissionFilter;
  
  /** Counts of submissions by status */
  statusCounts: SubmissionStatusCount[];
}

/**
 * Helper function to check if a submission is in an editable state
 * 
 * @param submission - The submission to check
 * @returns True if the submission is editable, false otherwise
 */
export function isSubmissionEditable(submission: Submission): boolean {
  return EDITABLE_STATUSES.includes(submission.status);
}

/**
 * Helper function to check if a submission is in an active state
 * 
 * @param submission - The submission to check
 * @returns True if the submission is active, false otherwise
 */
export function isSubmissionActive(submission: Submission): boolean {
  return ACTIVE_STATUSES.includes(submission.status);
}

/**
 * Helper function to check if a submission has all required documents
 * 
 * @param submission - The submission to check
 * @param existingDocuments - Array of documents attached to the submission
 * @returns True if all required documents are attached, false otherwise
 */
export function hasRequiredDocuments(
  submission: Submission, 
  existingDocuments: Document[]
): boolean {
  // Get service type from the CRO service
  const serviceType = submission.cro_service?.service_type;
  
  // If we don't have service type or required document types, return false
  if (!serviceType || !REQUIRED_DOCUMENT_TYPES[serviceType]) {
    return false;
  }
  
  // Get required document types for this service
  const requiredTypes = REQUIRED_DOCUMENT_TYPES[serviceType];
  
  // Get document types that exist in the submission
  const existingTypes = existingDocuments.map(doc => doc.type);
  
  // Check if all required document types exist
  return requiredTypes.every(requiredType => existingTypes.includes(requiredType));
}