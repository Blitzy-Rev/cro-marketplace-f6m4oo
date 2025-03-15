from datetime import datetime
from typing import Any, Dict, List, Optional

from pydantic import BaseModel, Field, UUID4, constr, validator

from ..constants.document_types import (
    DocumentType, 
    DOCUMENT_STATUS, 
    DOCUMENT_TYPE_DESCRIPTIONS
)


def validate_document_type(cls, v):
    """Validates that the document type is a valid DocumentType"""
    if not isinstance(v, DocumentType):
        raise ValueError(f"Document type must be one of: {[t.name for t in DocumentType]}")
    return v


def validate_document_status(cls, v):
    """Validates that the document status is a valid status from DOCUMENT_STATUS"""
    if v not in DOCUMENT_STATUS:
        raise ValueError(f"Document status must be one of: {list(DOCUMENT_STATUS.keys())}")
    return v


class DocumentBase(BaseModel):
    """Base Pydantic model for document data with common fields"""
    name: constr(min_length=1, max_length=255) = Field(
        ..., description="Document name"
    )
    type: DocumentType = Field(
        ..., description="Type of document"
    )
    status: str = Field(
        ..., description="Current status of the document"
    )
    description: Optional[str] = Field(
        None, description="Optional description of the document"
    )
    url: Optional[str] = Field(
        None, description="URL where the document is stored"
    )
    version: Optional[str] = Field(
        None, description="Document version identifier"
    )
    signature_required: Optional[bool] = Field(
        None, description="Indicates if the document requires signatures"
    )
    is_signed: Optional[bool] = Field(
        None, description="Indicates if the document has been signed"
    )

    @validator('name')
    def validate_name(cls, v):
        """Validates that the document name meets requirements"""
        if not v or not v.strip():
            raise ValueError("Document name cannot be empty")
        if len(v) > 255:
            raise ValueError("Document name must be less than 255 characters")
        return v

    @validator('type')
    def validate_type(cls, v):
        """Validates that the document type is a valid DocumentType"""
        return validate_document_type(cls, v)

    @validator('status')
    def validate_status(cls, v):
        """Validates that the status is a valid document status"""
        return validate_document_status(cls, v)


class DocumentCreate(DocumentBase):
    """Schema for creating a new document"""
    submission_id: UUID4 = Field(
        ..., description="ID of the submission this document belongs to"
    )
    uploaded_by: UUID4 = Field(
        ..., description="ID of the user who uploaded the document"
    )
    content_type: Optional[str] = Field(
        None, description="MIME type of the document"
    )
    file_size: Optional[int] = Field(
        None, description="Size of the document file in bytes"
    )


class DocumentUpdate(BaseModel):
    """Schema for updating an existing document"""
    name: Optional[str] = Field(
        None, description="Document name"
    )
    type: Optional[DocumentType] = Field(
        None, description="Type of document"
    )
    status: Optional[str] = Field(
        None, description="Current status of the document"
    )
    description: Optional[str] = Field(
        None, description="Description of the document"
    )
    url: Optional[str] = Field(
        None, description="URL where the document is stored"
    )
    version: Optional[str] = Field(
        None, description="Document version identifier"
    )
    signature_required: Optional[bool] = Field(
        None, description="Indicates if the document requires signatures"
    )
    is_signed: Optional[bool] = Field(
        None, description="Indicates if the document has been signed"
    )
    signature_id: Optional[str] = Field(
        None, description="External signature/envelope ID from e-signature provider"
    )
    signed_at: Optional[datetime] = Field(
        None, description="Timestamp when the document was signed"
    )
    content_type: Optional[str] = Field(
        None, description="MIME type of the document"
    )
    file_size: Optional[int] = Field(
        None, description="Size of the document file in bytes"
    )

    @validator('name')
    def validate_name(cls, v):
        """Validates that the document name meets requirements if provided"""
        if v is None:
            return v
        if not v or not v.strip():
            raise ValueError("Document name cannot be empty")
        if len(v) > 255:
            raise ValueError("Document name must be less than 255 characters")
        return v

    @validator('type')
    def validate_type(cls, v):
        """Validates that the document type is a valid DocumentType if provided"""
        if v is None:
            return v
        return validate_document_type(cls, v)

    @validator('status')
    def validate_status(cls, v):
        """Validates that the status is a valid document status if provided"""
        if v is None:
            return v
        return validate_document_status(cls, v)


class DocumentInDB(DocumentBase):
    """Schema for document data from database including ID and timestamps"""
    id: UUID4 = Field(
        ..., description="Unique identifier for the document"
    )
    uploaded_by: UUID4 = Field(
        ..., description="ID of the user who uploaded the document"
    )
    uploaded_at: datetime = Field(
        ..., description="Timestamp when the document was uploaded"
    )
    created_at: datetime = Field(
        ..., description="Timestamp when the document was created"
    )
    updated_at: datetime = Field(
        ..., description="Timestamp when the document was last updated"
    )
    signature_id: Optional[str] = Field(
        None, description="External signature/envelope ID from e-signature provider"
    )
    signed_at: Optional[datetime] = Field(
        None, description="Timestamp when the document was signed"
    )
    content_type: Optional[str] = Field(
        None, description="MIME type of the document"
    )
    file_size: Optional[int] = Field(
        None, description="Size of the document file in bytes"
    )


class Document(DocumentInDB):
    """Schema for document data returned to clients"""
    submission: Optional[Dict[str, Any]] = Field(
        None, description="Related submission data"
    )
    uploader: Optional[Dict[str, Any]] = Field(
        None, description="Information about the user who uploaded the document"
    )
    presigned_url: Optional[str] = Field(
        None, description="Presigned URL for document download"
    )
    type_description: Optional[str] = Field(
        None, description="Human-readable description of the document type"
    )
    status_description: Optional[str] = Field(
        None, description="Human-readable description of the document status"
    )


class DocumentFilter(BaseModel):
    """Schema for filtering documents"""
    name_contains: Optional[str] = Field(
        None, description="Filter for documents with names containing this string"
    )
    submission_id: Optional[UUID4] = Field(
        None, description="Filter for documents belonging to a specific submission"
    )
    uploaded_by: Optional[UUID4] = Field(
        None, description="Filter for documents uploaded by a specific user"
    )
    type: Optional[List[DocumentType]] = Field(
        None, description="Filter for documents of specific types"
    )
    status: Optional[List[str]] = Field(
        None, description="Filter for documents with specific statuses"
    )
    is_signed: Optional[bool] = Field(
        None, description="Filter for signed or unsigned documents"
    )
    signature_required: Optional[bool] = Field(
        None, description="Filter for documents that require signatures"
    )
    uploaded_after: Optional[datetime] = Field(
        None, description="Filter for documents uploaded after this timestamp"
    )
    uploaded_before: Optional[datetime] = Field(
        None, description="Filter for documents uploaded before this timestamp"
    )


class DocumentSignatureRequest(BaseModel):
    """Schema for requesting document signatures"""
    document_id: UUID4 = Field(
        ..., description="ID of the document to be signed"
    )
    signers: List[Dict[str, Any]] = Field(
        ..., description="List of signers with their information"
    )
    email_subject: Optional[str] = Field(
        None, description="Subject line for signature request emails"
    )
    email_message: Optional[str] = Field(
        None, description="Message body for signature request emails"
    )
    redirect_url: Optional[str] = Field(
        None, description="URL to redirect to after signing is complete"
    )

    @validator('signers')
    def validate_signers(cls, v):
        """Validates that at least one signer is provided"""
        if not v:
            raise ValueError("At least one signer must be provided")
        
        for i, signer in enumerate(v):
            if not signer.get('name'):
                raise ValueError(f"Signer {i+1} is missing a name")
            if not signer.get('email'):
                raise ValueError(f"Signer {i+1} is missing an email")
        
        return v


class DocumentSignatureResponse(BaseModel):
    """Schema for document signature response"""
    document_id: UUID4 = Field(
        ..., description="ID of the document being signed"
    )
    envelope_id: str = Field(
        ..., description="DocuSign envelope ID for the signature request"
    )
    signing_url: str = Field(
        ..., description="URL where signers can access the document for signing"
    )
    status: str = Field(
        ..., description="Current status of the signature request"
    )


class DocumentTypeInfo(BaseModel):
    """Schema for document type information"""
    type: DocumentType = Field(
        ..., description="Document type"
    )
    description: str = Field(
        ..., description="Human-readable description of the document type"
    )
    signature_required: bool = Field(
        ..., description="Indicates if this document type requires signatures"
    )
    is_required_for_submission: bool = Field(
        ..., description="Indicates if this document type is required for submissions"
    )


class DocumentUploadResponse(BaseModel):
    """Schema for document upload response"""
    document_id: UUID4 = Field(
        ..., description="ID of the created document"
    )
    name: str = Field(
        ..., description="Document name"
    )
    type: DocumentType = Field(
        ..., description="Document type"
    )
    status: str = Field(
        ..., description="Current status of the document"
    )
    upload_url: str = Field(
        ..., description="Presigned URL for uploading the document file"
    )
    upload_fields: Dict[str, Any] = Field(
        ..., description="Additional fields required for the upload"
    )