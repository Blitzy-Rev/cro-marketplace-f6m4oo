/**
 * API client for submission-related operations in the Molecular Data Management and CRO Integration Platform.
 * This file provides functions for creating, retrieving, updating, and managing CRO submissions,
 * including document requirements and status transitions.
 */

import { get, post, put, delete as deleteRequest, uploadFile } from './apiClient';
import { API_ENDPOINTS } from '../constants/apiEndpoints';
import { 
  SubmissionCreate, 
  SubmissionUpdate, 
  Submission, 
  SubmissionFilter, 
  SubmissionResponse, 
  SubmissionActionRequest,
  SubmissionWithDocumentRequirements,
  SubmissionStatusCount,
  SubmissionPricingUpdate
} from '../types/submission.types';
import { SubmissionAction } from '../constants/submissionStatus';

/**
 * Retrieves a paginated list of submissions with optional filtering
 * 
 * @param page - Page number for pagination (0-based)
 * @param size - Number of items per page
 * @param filter - Optional filter criteria for submissions
 * @returns Promise resolving to paginated submission response
 */
export async function getSubmissions(
  page: number = 0,
  size: number = 25,
  filter: SubmissionFilter = {}
): Promise<SubmissionResponse> {
  // Construct query parameters
  const queryParams = new URLSearchParams();
  queryParams.append('page', page.toString());
  queryParams.append('size', size.toString());
  
  // Add filter parameters if provided
  if (filter.name_contains) queryParams.append('name_contains', filter.name_contains);
  if (filter.created_by) queryParams.append('created_by', filter.created_by);
  if (filter.cro_service_id) queryParams.append('cro_service_id', filter.cro_service_id);
  if (filter.status && filter.status.length > 0) {
    filter.status.forEach(status => queryParams.append('status', status));
  }
  if (filter.active_only !== null && filter.active_only !== undefined) {
    queryParams.append('active_only', filter.active_only.toString());
  }
  if (filter.molecule_id) queryParams.append('molecule_id', filter.molecule_id);
  if (filter.created_after) queryParams.append('created_after', filter.created_after);
  if (filter.created_before) queryParams.append('created_before', filter.created_before);
  
  // Make API request
  return get<SubmissionResponse>(`${API_ENDPOINTS.SUBMISSIONS.LIST}?${queryParams.toString()}`);
}

/**
 * Retrieves a single submission by ID
 * 
 * @param id - Submission ID
 * @returns Promise resolving to submission details
 */
export async function getSubmission(id: string): Promise<Submission> {
  const url = API_ENDPOINTS.SUBMISSIONS.GET.replace('{id}', id);
  return get<Submission>(url);
}

/**
 * Creates a new submission
 * 
 * @param submission - Submission data for creation
 * @returns Promise resolving to created submission details
 */
export async function createSubmission(submission: SubmissionCreate): Promise<Submission> {
  return post<Submission>(API_ENDPOINTS.SUBMISSIONS.CREATE, submission);
}

/**
 * Updates an existing submission
 * 
 * @param id - Submission ID
 * @param submission - Updated submission data
 * @returns Promise resolving to updated submission details
 */
export async function updateSubmission(id: string, submission: SubmissionUpdate): Promise<Submission> {
  const url = API_ENDPOINTS.SUBMISSIONS.UPDATE.replace('{id}', id);
  return put<Submission>(url, submission);
}

/**
 * Deletes a submission by ID
 * 
 * @param id - Submission ID
 * @returns Promise resolving when deletion is complete
 */
export async function deleteSubmission(id: string): Promise<void> {
  const url = API_ENDPOINTS.SUBMISSIONS.GET.replace('{id}', id);
  return deleteRequest<void>(url);
}

/**
 * Retrieves document requirements for a submission
 * 
 * @param id - Submission ID
 * @returns Promise resolving to submission with document requirements
 */
export async function getSubmissionDocumentRequirements(id: string): Promise<SubmissionWithDocumentRequirements> {
  const url = API_ENDPOINTS.SUBMISSIONS.DOCUMENT_REQUIREMENTS.replace('{id}', id);
  return get<SubmissionWithDocumentRequirements>(url);
}

/**
 * Performs an action on a submission (submit, approve, reject, etc.)
 * 
 * @param id - Submission ID
 * @param actionRequest - Action request data with action type and optional data
 * @returns Promise resolving to updated submission after action
 */
export async function performSubmissionAction(
  id: string, 
  actionRequest: SubmissionActionRequest
): Promise<Submission> {
  const url = API_ENDPOINTS.SUBMISSIONS.PERFORM_ACTION.replace('{id}', id);
  return post<Submission>(url, actionRequest);
}

/**
 * Retrieves counts of submissions by status
 * 
 * @param filter - Optional filter criteria to limit the counts
 * @returns Promise resolving to array of status counts
 */
export async function getSubmissionStatusCounts(
  filter: SubmissionFilter = {}
): Promise<SubmissionStatusCount[]> {
  // Construct query parameters
  const queryParams = new URLSearchParams();
  
  // Add filter parameters if provided
  if (filter.created_by) queryParams.append('created_by', filter.created_by);
  if (filter.cro_service_id) queryParams.append('cro_service_id', filter.cro_service_id);
  if (filter.molecule_id) queryParams.append('molecule_id', filter.molecule_id);
  if (filter.created_after) queryParams.append('created_after', filter.created_after);
  if (filter.created_before) queryParams.append('created_before', filter.created_before);
  
  // Make API request
  return get<SubmissionStatusCount[]>(`${API_ENDPOINTS.SUBMISSIONS.STATUS_COUNTS}?${queryParams.toString()}`);
}

/**
 * Retrieves submissions that include a specific molecule
 * 
 * @param moleculeId - Molecule ID
 * @param page - Page number for pagination (0-based)
 * @param size - Number of items per page
 * @returns Promise resolving to paginated submission response
 */
export async function getSubmissionsByMolecule(
  moleculeId: string,
  page: number = 0,
  size: number = 25
): Promise<SubmissionResponse> {
  // Construct query parameters
  const queryParams = new URLSearchParams();
  queryParams.append('page', page.toString());
  queryParams.append('size', size.toString());
  
  // Construct URL
  const url = API_ENDPOINTS.SUBMISSIONS.BY_MOLECULE.replace('{molecule_id}', moleculeId);
  
  // Make API request
  return get<SubmissionResponse>(`${url}?${queryParams.toString()}`);
}

/**
 * Submits pricing information for a submission (CRO user)
 * 
 * @param id - Submission ID
 * @param pricingData - Pricing and timeline information
 * @returns Promise resolving to updated submission with pricing information
 */
export async function submitPricing(
  id: string, 
  pricingData: SubmissionPricingUpdate
): Promise<Submission> {
  // Create action request with PROVIDE_PRICING action
  const actionRequest: SubmissionActionRequest = {
    action: SubmissionAction.PROVIDE_PRICING,
    data: pricingData,
    comment: pricingData.comment || null
  };
  
  // Use the performSubmissionAction function
  return performSubmissionAction(id, actionRequest);
}

/**
 * Approves a submission with pricing (Pharma user)
 * 
 * @param id - Submission ID
 * @param comment - Optional comment for approval
 * @returns Promise resolving to updated submission with approved status
 */
export async function approveSubmission(
  id: string, 
  comment: string = ''
): Promise<Submission> {
  // Create action request with APPROVE action
  const actionRequest: SubmissionActionRequest = {
    action: SubmissionAction.APPROVE,
    data: null,
    comment: comment || null
  };
  
  // Use the performSubmissionAction function
  return performSubmissionAction(id, actionRequest);
}

/**
 * Rejects a submission (either party)
 * 
 * @param id - Submission ID
 * @param comment - Comment explaining rejection reason (required)
 * @returns Promise resolving to updated submission with rejected status
 */
export async function rejectSubmission(
  id: string, 
  comment: string
): Promise<Submission> {
  // Create action request with REJECT action
  const actionRequest: SubmissionActionRequest = {
    action: SubmissionAction.REJECT,
    data: null,
    comment: comment // Comment is required for rejection
  };
  
  // Use the performSubmissionAction function
  return performSubmissionAction(id, actionRequest);
}

/**
 * Cancels a submission (either party)
 * 
 * @param id - Submission ID
 * @param comment - Comment explaining cancellation reason (required)
 * @returns Promise resolving to updated submission with cancelled status
 */
export async function cancelSubmission(
  id: string, 
  comment: string
): Promise<Submission> {
  // Create action request with CANCEL action
  const actionRequest: SubmissionActionRequest = {
    action: SubmissionAction.CANCEL,
    data: null,
    comment: comment // Comment is required for cancellation
  };
  
  // Use the performSubmissionAction function
  return performSubmissionAction(id, actionRequest);
}

/**
 * Marks a submission as in progress (CRO user)
 * 
 * @param id - Submission ID
 * @param comment - Optional comment about the experiment
 * @returns Promise resolving to updated submission with in progress status
 */
export async function startExperiment(
  id: string, 
  comment: string = ''
): Promise<Submission> {
  // Create action request with START_EXPERIMENT action
  const actionRequest: SubmissionActionRequest = {
    action: SubmissionAction.START_EXPERIMENT,
    data: null,
    comment: comment || null
  };
  
  // Use the performSubmissionAction function
  return performSubmissionAction(id, actionRequest);
}

/**
 * Marks a submission as completed (CRO user)
 * 
 * @param id - Submission ID
 * @param comment - Optional comment about the completed work
 * @returns Promise resolving to updated submission with completed status
 */
export async function completeSubmission(
  id: string, 
  comment: string = ''
): Promise<Submission> {
  // Create action request with COMPLETE action
  const actionRequest: SubmissionActionRequest = {
    action: SubmissionAction.COMPLETE,
    data: null,
    comment: comment || null
  };
  
  // Use the performSubmissionAction function
  return performSubmissionAction(id, actionRequest);
}