import { DocumentType } from '../constants/documentTypes';

/**
 * Enum representing possible document statuses in the system
 */
export enum DocumentStatus {
  /**
   * Document is in draft state, not yet finalized
   */
  DRAFT = 'DRAFT',
  
  /**
   * Document is awaiting signature from one or more parties
   */
  PENDING_SIGNATURE = 'PENDING_SIGNATURE',
  
  /**
   * Document has been successfully signed by all required parties
   */
  SIGNED = 'SIGNED',
  
  /**
   * Document signature was rejected by one or more parties
   */
  REJECTED = 'REJECTED',
  
  /**
   * Document has expired and is no longer valid
   */
  EXPIRED = 'EXPIRED',
  
  /**
   * Document has been archived
   */
  ARCHIVED = 'ARCHIVED'
}

/**
 * Interface representing a document in the system
 */
export interface Document {
  /**
   * Unique identifier for the document
   */
  id: string;
  
  /**
   * Name of the document
   */
  name: string;
  
  /**
   * Type of document (e.g., NDA, MTA, etc.)
   */
  type: DocumentType;
  
  /**
   * Current status of the document
   */
  status: DocumentStatus;
  
  /**
   * Optional description of the document
   */
  description: string | null;
  
  /**
   * URL to access the document (may be null if not yet uploaded)
   */
  url: string | null;
  
  /**
   * Document version identifier
   */
  version: string | null;
  
  /**
   * Indicates if the document requires electronic signature
   */
  signature_required: boolean;
  
  /**
   * Indicates if the document has been signed
   */
  is_signed: boolean;
  
  /**
   * ID of the signature if document has been signed
   */
  signature_id: string | null;
  
  /**
   * ISO timestamp when the document was signed
   */
  signed_at: string | null;
  
  /**
   * ID of the submission this document is associated with
   */
  submission_id: string;
  
  /**
   * ID of the user who uploaded the document
   */
  uploaded_by: string;
  
  /**
   * ISO timestamp when the document was uploaded
   */
  uploaded_at: string;
  
  /**
   * ISO timestamp when the document was created
   */
  created_at: string;
  
  /**
   * ISO timestamp when the document was last updated
   */
  updated_at: string;
  
  /**
   * MIME type of the document
   */
  content_type: string | null;
  
  /**
   * Size of the file in bytes
   */
  file_size: number | null;
}

/**
 * Interface for document with temporary secure access URL
 */
export interface DocumentWithPresignedUrl {
  /**
   * The document details
   */
  document: Document;
  
  /**
   * Temporary URL for secure access to the document
   */
  presigned_url: string;
  
  /**
   * Expiration time for the presigned URL in seconds since epoch
   */
  expiration: number;
}

/**
 * Interface for creating a new document
 */
export interface DocumentCreateRequest {
  /**
   * Name of the document
   */
  name: string;
  
  /**
   * Type of document (e.g., NDA, MTA, etc.)
   */
  type: DocumentType;
  
  /**
   * ID of the submission this document is associated with
   */
  submission_id: string;
  
  /**
   * Optional description of the document
   */
  description: string | null;
  
  /**
   * Indicates if the document requires electronic signature
   */
  signature_required: boolean;
  
  /**
   * MIME type of the document
   */
  content_type: string | null;
  
  /**
   * Size of the file in bytes
   */
  file_size: number | null;
}

/**
 * Interface for updating an existing document
 */
export interface DocumentUpdateRequest {
  /**
   * Updated name (optional)
   */
  name: string | null;
  
  /**
   * Updated document type (optional)
   */
  type: DocumentType | null;
  
  /**
   * Updated document status (optional)
   */
  status: DocumentStatus | null;
  
  /**
   * Updated description (optional)
   */
  description: string | null;
  
  /**
   * Updated signature requirement (optional)
   */
  signature_required: boolean | null;
}

/**
 * Interface for filtering documents
 */
export interface DocumentFilterParams {
  /**
   * Filter by partial document name
   */
  name_contains: string | null;
  
  /**
   * Filter by submission ID
   */
  submission_id: string | null;
  
  /**
   * Filter by uploader
   */
  uploaded_by: string | null;
  
  /**
   * Filter by document types
   */
  type: DocumentType[] | null;
  
  /**
   * Filter by document statuses
   */
  status: DocumentStatus[] | null;
  
  /**
   * Filter by signed status
   */
  is_signed: boolean | null;
  
  /**
   * Filter by signature requirement
   */
  signature_required: boolean | null;
  
  /**
   * Filter by upload date (after)
   */
  uploaded_after: string | null;
  
  /**
   * Filter by upload date (before)
   */
  uploaded_before: string | null;
}

/**
 * Interface for document type metadata
 */
export interface DocumentTypeInfo {
  /**
   * The document type
   */
  type: DocumentType;
  
  /**
   * Human-readable description of the document type
   */
  description: string;
  
  /**
   * Indicates if the document type is required
   */
  required: boolean;
  
  /**
   * Indicates if the document type requires signature
   */
  signature_required: boolean;
}

/**
 * Interface for requesting document signatures
 */
export interface DocumentSignatureRequest {
  /**
   * ID of the document to be signed
   */
  document_id: string;
  
  /**
   * List of signers with their information
   */
  signers: Array<{
    name: string,
    email: string,
    role?: string
  }>;
  
  /**
   * Subject for the signature request email
   */
  email_subject: string | null;
  
  /**
   * Message body for the signature request email
   */
  email_message: string | null;
  
  /**
   * URL to redirect users after signing
   */
  redirect_url: string | null;
}

/**
 * Interface for document signature response
 */
export interface DocumentSignatureResponse {
  /**
   * ID of the document being signed
   */
  document_id: string;
  
  /**
   * ID of the signature envelope (from e-signature provider)
   */
  envelope_id: string;
  
  /**
   * URL for the signing process
   */
  signing_url: string;
  
  /**
   * Current status of the signature process
   */
  status: string;
}

/**
 * Interface for document upload result
 */
export interface DocumentUploadResult {
  /**
   * ID of the document
   */
  document_id: string;
  
  /**
   * Name of the document
   */
  name: string;
  
  /**
   * Type of document
   */
  type: DocumentType;
  
  /**
   * Current status of the document
   */
  status: DocumentStatus;
  
  /**
   * URL for uploading the document
   */
  upload_url: string;
  
  /**
   * Additional fields required for the upload
   */
  upload_fields: Record<string, string>;
}

/**
 * Interface for document signature status
 */
export interface DocumentSignatureStatus {
  /**
   * Current status of the signature process
   */
  status: string;
  
  /**
   * Indicates if the signature process is complete
   */
  completed: boolean;
  
  /**
   * Status of individual signers
   */
  signers: Array<{
    email: string,
    status: string,
    signed_at: string | null
  }>;
}