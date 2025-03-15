/**
 * Submission Status Constants
 * 
 * Defines constants and enumerations for submission statuses, actions, and related helper functions
 * for the CRO submission workflow in the Molecular Data Management and CRO Integration Platform.
 */

/**
 * Enumeration of all possible submission statuses
 */
export enum SubmissionStatus {
  DRAFT = 'DRAFT',
  SUBMITTED = 'SUBMITTED',
  PENDING_REVIEW = 'PENDING_REVIEW',
  PRICING_PROVIDED = 'PRICING_PROVIDED',
  APPROVED = 'APPROVED',
  IN_PROGRESS = 'IN_PROGRESS',
  RESULTS_UPLOADED = 'RESULTS_UPLOADED',
  RESULTS_REVIEWED = 'RESULTS_REVIEWED',
  COMPLETED = 'COMPLETED',
  CANCELLED = 'CANCELLED',
  REJECTED = 'REJECTED'
}

/**
 * Enumeration of all possible actions that can be performed on submissions
 */
export enum SubmissionAction {
  SUBMIT = 'SUBMIT',
  PROVIDE_PRICING = 'PROVIDE_PRICING',
  APPROVE = 'APPROVE',
  REJECT = 'REJECT',
  CANCEL = 'CANCEL',
  START_EXPERIMENT = 'START_EXPERIMENT',
  UPLOAD_RESULTS = 'UPLOAD_RESULTS',
  REVIEW_RESULTS = 'REVIEW_RESULTS',
  COMPLETE = 'COMPLETE'
}

/**
 * List of submission statuses considered active (not terminal)
 */
export const ACTIVE_STATUSES: SubmissionStatus[] = [
  SubmissionStatus.DRAFT,
  SubmissionStatus.SUBMITTED,
  SubmissionStatus.PENDING_REVIEW,
  SubmissionStatus.PRICING_PROVIDED,
  SubmissionStatus.APPROVED,
  SubmissionStatus.IN_PROGRESS,
  SubmissionStatus.RESULTS_UPLOADED,
  SubmissionStatus.RESULTS_REVIEWED
];

/**
 * List of submission statuses considered terminal (no further actions possible)
 */
export const TERMINAL_STATUSES: SubmissionStatus[] = [
  SubmissionStatus.COMPLETED,
  SubmissionStatus.CANCELLED,
  SubmissionStatus.REJECTED
];

/**
 * List of submission statuses where submission details can be edited
 */
export const EDITABLE_STATUSES: SubmissionStatus[] = [
  SubmissionStatus.DRAFT
];

/**
 * Mapping of submission statuses to color codes for UI display
 */
export const STATUS_COLORS: Record<SubmissionStatus, string> = {
  [SubmissionStatus.DRAFT]: '#9e9e9e',
  [SubmissionStatus.SUBMITTED]: '#2196f3',
  [SubmissionStatus.PENDING_REVIEW]: '#ff9800',
  [SubmissionStatus.PRICING_PROVIDED]: '#673ab7',
  [SubmissionStatus.APPROVED]: '#4caf50',
  [SubmissionStatus.IN_PROGRESS]: '#3f51b5',
  [SubmissionStatus.RESULTS_UPLOADED]: '#009688',
  [SubmissionStatus.RESULTS_REVIEWED]: '#8bc34a',
  [SubmissionStatus.COMPLETED]: '#4caf50',
  [SubmissionStatus.CANCELLED]: '#f44336',
  [SubmissionStatus.REJECTED]: '#d32f2f'
};

/**
 * Mapping of submission statuses to user-friendly display names
 */
export const STATUS_DISPLAY_NAMES: Record<SubmissionStatus, string> = {
  [SubmissionStatus.DRAFT]: 'Draft',
  [SubmissionStatus.SUBMITTED]: 'Submitted',
  [SubmissionStatus.PENDING_REVIEW]: 'Pending Review',
  [SubmissionStatus.PRICING_PROVIDED]: 'Pricing Provided',
  [SubmissionStatus.APPROVED]: 'Approved',
  [SubmissionStatus.IN_PROGRESS]: 'In Progress',
  [SubmissionStatus.RESULTS_UPLOADED]: 'Results Uploaded',
  [SubmissionStatus.RESULTS_REVIEWED]: 'Results Reviewed',
  [SubmissionStatus.COMPLETED]: 'Completed',
  [SubmissionStatus.CANCELLED]: 'Cancelled',
  [SubmissionStatus.REJECTED]: 'Rejected'
};

/**
 * Mapping of submission statuses to detailed descriptions
 */
export const STATUS_DESCRIPTIONS: Record<SubmissionStatus, string> = {
  [SubmissionStatus.DRAFT]: 'Initial draft state, editable by pharma user',
  [SubmissionStatus.SUBMITTED]: 'Submitted to CRO but not yet reviewed',
  [SubmissionStatus.PENDING_REVIEW]: 'Under review by CRO',
  [SubmissionStatus.PRICING_PROVIDED]: 'CRO has provided pricing and timeline',
  [SubmissionStatus.APPROVED]: 'Pharma has approved pricing and timeline',
  [SubmissionStatus.IN_PROGRESS]: 'Experimental work in progress at CRO',
  [SubmissionStatus.RESULTS_UPLOADED]: 'CRO has uploaded experimental results',
  [SubmissionStatus.RESULTS_REVIEWED]: 'Pharma has reviewed experimental results',
  [SubmissionStatus.COMPLETED]: 'Submission workflow completed successfully',
  [SubmissionStatus.CANCELLED]: 'Submission cancelled by either party',
  [SubmissionStatus.REJECTED]: 'Submission rejected by CRO or pharma'
};

/**
 * Returns the color code associated with a submission status
 * 
 * @param status - The submission status
 * @returns The color code for the status
 */
export function getStatusColor(status: SubmissionStatus): string {
  return STATUS_COLORS[status] || '#9e9e9e'; // Default to gray if status not found
}

/**
 * Returns a user-friendly display name for a submission status
 * 
 * @param status - The submission status
 * @returns The display name for the status
 */
export function getStatusDisplayName(status: SubmissionStatus): string {
  return STATUS_DISPLAY_NAMES[status] || status;
}

/**
 * Returns a detailed description of a submission status
 * 
 * @param status - The submission status
 * @returns The description of the status
 */
export function getStatusDescription(status: SubmissionStatus): string {
  return STATUS_DESCRIPTIONS[status] || 'Unknown status';
}

/**
 * Determines if a submission can be edited based on its status
 * 
 * @param status - The submission status
 * @returns True if the submission is editable, false otherwise
 */
export function isSubmissionEditable(status: SubmissionStatus): boolean {
  return EDITABLE_STATUSES.includes(status);
}

/**
 * Determines if a submission is in an active state (not terminal)
 * 
 * @param status - The submission status
 * @returns True if the submission is active, false otherwise
 */
export function isSubmissionActive(status: SubmissionStatus): boolean {
  return ACTIVE_STATUSES.includes(status);
}