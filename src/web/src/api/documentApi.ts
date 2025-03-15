/**
 * API client for document-related operations in the Molecular Data Management and CRO Integration Platform.
 * 
 * This file provides functions to interact with the backend document endpoints for uploading,
 * retrieving, updating, and managing documents, including e-signature workflows that comply with
 * 21 CFR Part 11 requirements for electronic records in pharmaceutical environments.
 */

import { get, post, put, delete as deleteRequest, uploadFile, downloadFile } from './apiClient'; // v1.4.0
import { API_ENDPOINTS } from '../constants/apiEndpoints';
import {
  Document,
  DocumentWithPresignedUrl,
  DocumentCreateRequest,
  DocumentUpdateRequest,
  DocumentFilterParams,
  DocumentSignatureRequest,
  DocumentSignatureResponse,
  DocumentSignatureStatus,
  DocumentUploadResult,
  DocumentTypeInfo
} from '../types/document.types';

/**
 * Retrieves a paginated list of documents with optional filtering
 * @param filters - Optional filter parameters
 * @param page - Page number (1-based)
 * @param size - Number of documents per page
 * @returns Promise resolving to paginated document data
 */
export async function getDocuments(
  filters: DocumentFilterParams = {},
  page: number = 1,
  size: number = 25
): Promise<{ documents: Document[], total: number }> {
  const queryParams = new URLSearchParams();
  
  // Add pagination parameters
  queryParams.append('page', page.toString());
  queryParams.append('size', size.toString());
  
  // Add filter parameters if provided
  if (filters.name_contains) queryParams.append('name_contains', filters.name_contains);
  if (filters.submission_id) queryParams.append('submission_id', filters.submission_id);
  if (filters.uploaded_by) queryParams.append('uploaded_by', filters.uploaded_by);
  
  if (filters.type && filters.type.length > 0) {
    filters.type.forEach(type => queryParams.append('type', type));
  }
  
  if (filters.status && filters.status.length > 0) {
    filters.status.forEach(status => queryParams.append('status', status));
  }
  
  if (filters.is_signed !== null) queryParams.append('is_signed', filters.is_signed.toString());
  if (filters.signature_required !== null) queryParams.append('signature_required', filters.signature_required.toString());
  if (filters.uploaded_after) queryParams.append('uploaded_after', filters.uploaded_after);
  if (filters.uploaded_before) queryParams.append('uploaded_before', filters.uploaded_before);
  
  const url = `${API_ENDPOINTS.DOCUMENTS.LIST}?${queryParams.toString()}`;
  return get<{ documents: Document[], total: number }>(url);
}

/**
 * Retrieves a single document by ID
 * @param id - Document ID
 * @returns Promise resolving to document details
 */
export async function getDocument(id: string): Promise<Document> {
  const url = API_ENDPOINTS.DOCUMENTS.GET.replace('{id}', id);
  return get<Document>(url);
}

/**
 * Retrieves a document with a presigned download URL
 * @param id - Document ID
 * @returns Promise resolving to document with download URL
 */
export async function getDocumentWithDownloadUrl(id: string): Promise<DocumentWithPresignedUrl> {
  const url = API_ENDPOINTS.DOCUMENTS.DOWNLOAD.replace('{id}', id);
  return get<DocumentWithPresignedUrl>(url);
}

/**
 * Downloads a document file
 * @param id - Document ID
 * @param filename - The name to save the file as
 * @returns Promise resolving to document file blob
 */
export async function downloadDocument(id: string, filename: string): Promise<Blob> {
  const url = API_ENDPOINTS.DOCUMENTS.DOWNLOAD.replace('{id}', id);
  return downloadFile(url, filename);
}

/**
 * Creates a document upload request and gets upload URL
 * @param documentRequest - Document metadata
 * @returns Promise resolving to upload details
 */
export async function createDocumentUploadRequest(
  documentRequest: DocumentCreateRequest
): Promise<DocumentUploadResult> {
  return post<DocumentUploadResult>(API_ENDPOINTS.DOCUMENTS.UPLOAD, documentRequest);
}

/**
 * Uploads a document file using pre-signed URL
 * @param uploadResult - Upload details from createDocumentUploadRequest
 * @param file - The file to upload
 * @returns Promise resolving to the created document
 */
export async function uploadDocumentFile(
  uploadResult: DocumentUploadResult, 
  file: File
): Promise<Document> {
  // Create FormData with the fields from the upload result
  const formData = new FormData();
  
  // Add all fields from the upload_fields to the form data
  Object.entries(uploadResult.upload_fields).forEach(([key, value]) => {
    formData.append(key, value);
  });
  
  // Add the file as the last field
  formData.append('file', file);
  
  // Upload directly to the provided URL
  await fetch(uploadResult.upload_url, {
    method: 'POST',
    body: formData,
  });
  
  // Retrieve the document details after successful upload
  return getDocument(uploadResult.document_id);
}

/**
 * Updates an existing document's metadata
 * @param id - Document ID
 * @param document - Updated document data
 * @returns Promise resolving to updated document
 */
export async function updateDocument(
  id: string, 
  document: DocumentUpdateRequest
): Promise<Document> {
  const url = API_ENDPOINTS.DOCUMENTS.UPDATE.replace('{id}', id);
  return put<Document>(url, document);
}

/**
 * Deletes a document
 * @param id - Document ID
 * @returns Promise resolving when document is deleted
 */
export async function deleteDocument(id: string): Promise<void> {
  const url = API_ENDPOINTS.DOCUMENTS.DELETE.replace('{id}', id);
  return deleteRequest<void>(url);
}

/**
 * Retrieves documents associated with a submission
 * @param submissionId - Submission ID
 * @param page - Page number (1-based)
 * @param size - Number of documents per page
 * @returns Promise resolving to paginated document data
 */
export async function getDocumentsBySubmission(
  submissionId: string,
  page: number = 1,
  size: number = 25
): Promise<{ documents: Document[], total: number }> {
  const queryParams = new URLSearchParams();
  queryParams.append('page', page.toString());
  queryParams.append('size', size.toString());
  
  const url = `${API_ENDPOINTS.DOCUMENTS.BY_SUBMISSION.replace('{submission_id}', submissionId)}?${queryParams.toString()}`;
  return get<{ documents: Document[], total: number }>(url);
}

/**
 * Requests electronic signature for a document
 * @param documentId - Document ID
 * @param signatureRequest - Signature request details
 * @returns Promise resolving to signature request details
 */
export async function requestDocumentSignature(
  documentId: string,
  signatureRequest: DocumentSignatureRequest
): Promise<DocumentSignatureResponse> {
  const url = API_ENDPOINTS.DOCUMENTS.SIGNATURE_REQUEST.replace('{id}', documentId);
  return post<DocumentSignatureResponse>(url, signatureRequest);
}

/**
 * Checks the status of a document signature request
 * @param documentId - Document ID
 * @returns Promise resolving to signature status
 */
export async function getDocumentSignatureStatus(
  documentId: string
): Promise<DocumentSignatureStatus> {
  const url = API_ENDPOINTS.DOCUMENTS.SIGNATURE_STATUS.replace('{id}', documentId);
  return get<DocumentSignatureStatus>(url);
}

export {
  getDocuments,
  getDocument,
  getDocumentWithDownloadUrl,
  downloadDocument,
  createDocumentUploadRequest,
  uploadDocumentFile,
  updateDocument,
  deleteDocument,
  getDocumentsBySubmission,
  requestDocumentSignature,
  getDocumentSignatureStatus
};