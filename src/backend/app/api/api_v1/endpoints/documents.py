from typing import List, Dict, Any, Optional
from uuid import UUID, uuid4
import io

from fastapi import APIRouter, Depends, HTTPException, status, File, UploadFile, StreamingResponse
from fastapi.security import Security
from fastapi.responses import Response

from sqlalchemy.orm import Session

# Internal imports
from ...api.deps import get_db, get_current_user, get_current_active_user, get_submission_access
from ...services.document_service import DocumentService, DocumentServiceException
from ...schemas.document import (
    DocumentCreate, DocumentUpdate, DocumentFilter, 
    DocumentSignatureRequest, DocumentUploadResponse
)
from ...constants.document_types import DocumentType
from ...core.logging import get_logger
from ...models.user import User

# Initialize router and services
router = APIRouter(prefix="/documents", tags=["documents"])
logger = get_logger(__name__)
document_service = DocumentService()

@router.get("/{document_id}", response_model=Dict[str, Any])
def get_document(
    document_id: UUID,
    url_expiration: Optional[int] = None,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
) -> Dict[str, Any]:
    """
    Get a document by ID with optional presigned URL
    """
    logger.info(f"Attempting to retrieve document with ID: {document_id}")
    try:
        document_data = document_service.get_document(document_id, url_expiration=url_expiration)
        if not document_data:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND, 
                detail=f"Document not found with ID: {document_id}"
            )
        
        # Check if user has access to the document's submission
        get_submission_access(document_data['submission']['id'], current_user, db)
        
        logger.info(f"Successfully retrieved document with ID: {document_id}")
        return document_data
    except Exception as e:
        logger.error(f"Error retrieving document {document_id}: {str(e)}")
        raise

@router.get("/submission/{submission_id}", response_model=List[Dict[str, Any]])
def get_documents_by_submission(
    submission_id: UUID,
    url_expiration: Optional[int] = None,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
) -> List[Dict[str, Any]]:
    """
    Get all documents for a specific submission
    """
    logger.info(f"Attempting to retrieve documents for submission ID: {submission_id}")
    
    # Check if user has access to the submission
    get_submission_access(submission_id, current_user, db)
    
    try:
        documents = document_service.get_documents_by_submission(submission_id, url_expiration=url_expiration)
        logger.info(f"Successfully retrieved documents for submission ID: {submission_id}")
        return documents
    except Exception as e:
        logger.error(f"Error retrieving documents for submission {submission_id}: {str(e)}")
        raise

@router.get("/required/{submission_id}", response_model=List[Dict[str, Any]])
def get_required_documents(
    submission_id: UUID,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
) -> List[Dict[str, Any]]:
    """
    Get list of required documents for a submission
    """
    logger.info(f"Attempting to retrieve required documents for submission ID: {submission_id}")
    
    # Check if user has access to the submission
    get_submission_access(submission_id, current_user, db)
    
    try:
        required_documents = document_service.get_required_documents(submission_id)
        logger.info(f"Successfully retrieved required documents for submission ID: {submission_id}")
        return required_documents
    except Exception as e:
        logger.error(f"Error retrieving required documents for submission {submission_id}: {str(e)}")
        raise

@router.post("/filter", response_model=Dict[str, Any])
def filter_documents(
    filters: DocumentFilter,
    skip: int = 0,
    limit: int = 100,
    url_expiration: Optional[int] = None,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
) -> Dict[str, Any]:
    """
    Filter documents based on criteria with pagination
    """
    logger.info("Attempting to filter documents")
    
    # TODO: Implement organization-based filtering if user is not admin
    # if not current_user.is_superuser:
    #     filters.organization_id = current_user.organization_id
    
    try:
        filtered_documents = document_service.filter_documents(filters, skip, limit, url_expiration=url_expiration)
        logger.info("Successfully filtered documents")
        return filtered_documents
    except Exception as e:
        logger.error(f"Error filtering documents: {str(e)}")
        raise

@router.post("/upload-url", response_model=DocumentUploadResponse)
def create_upload_url(
    filename: str,
    document_type: DocumentType,
    submission_id: UUID,
    content_type: Optional[str] = None,
    expiration: Optional[int] = None,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
) -> DocumentUploadResponse:
    """
    Generate a presigned URL for document upload
    """
    logger.info(f"Attempting to generate upload URL for document: {filename}")
    
    # Check if user has access to the submission
    get_submission_access(submission_id, current_user, db)
    
    try:
        upload_response = document_service.generate_upload_url(
            filename=filename,
            document_type=document_type,
            submission_id=submission_id,
            owner_id=current_user.id,
            content_type=content_type,
            expiration=expiration
        )
        logger.info(f"Successfully generated upload URL for document: {filename}")
        return upload_response
    except Exception as e:
        logger.error(f"Error generating upload URL for document {filename}: {str(e)}")
        raise

@router.post("/upload", response_model=Dict[str, Any])
def upload_document(
    file: UploadFile = File(...),
    document_type: DocumentType = Depends(),
    submission_id: UUID = Depends(),
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
) -> Dict[str, Any]:
    """
    Upload document content directly
    """
    logger.info(f"Attempting to upload document: {file.filename}")
    
    # Check if user has access to the submission
    get_submission_access(submission_id, current_user, db)
    
    try:
        content = await file.read()
        created_document = document_service.upload_document(
            content=content,
            filename=file.filename,
            document_type=document_type,
            submission_id=submission_id,
            owner_id=current_user.id,
            content_type=file.content_type
        )
        logger.info(f"Successfully uploaded document: {file.filename}")
        return created_document.to_dict()
    except Exception as e:
        logger.error(f"Error uploading document {file.filename}: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to upload document: {str(e)}"
        )

@router.get("/{document_id}/download")
def download_document(
    document_id: UUID,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
) -> StreamingResponse:
    """
    Download document content
    """
    logger.info(f"Attempting to download document with ID: {document_id}")
    
    try:
        # Get document details to check access and get metadata
        document_data = document_service.get_document(document_id)
        if not document_data:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND, 
                detail=f"Document not found with ID: {document_id}"
            )
        
        # Check if user has access to the document's submission
        get_submission_access(document_data['submission']['id'], current_user, db)
        
        # Download document content
        content = document_service.download_document(document_id)
        if not content:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND, 
                detail=f"Document content not found for ID: {document_id}"
            )
        
        # Create BytesIO object from content
        file_stream = io.BytesIO(content)
        
        # Determine content type
        content_type = document_data.get('content_type', 'application/octet-stream')
        
        logger.info(f"Successfully downloaded document with ID: {document_id}")
        return StreamingResponse(
            file_stream,
            media_type=content_type,
            headers={"Content-Disposition": f"attachment;filename={document_data['name']}"}
        )
    except Exception as e:
        logger.error(f"Error downloading document {document_id}: {str(e)}")
        raise

@router.put("/{document_id}", response_model=Dict[str, Any])
def update_document(
    document_id: UUID,
    document_data: DocumentUpdate,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
) -> Dict[str, Any]:
    """
    Update an existing document
    """
    logger.info(f"Attempting to update document with ID: {document_id}")
    
    try:
        # Get document details to check access
        document_data_before_update = document_service.get_document(document_id)
        if not document_data_before_update:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND, 
                detail=f"Document not found with ID: {document_id}"
            )
        
        # Check if user has access to the document's submission
        get_submission_access(document_data_before_update['submission']['id'], current_user, db)
        
        # Update document
        updated_document = document_service.update_document(document_id, document_data)
        if not updated_document:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND, 
                detail=f"Document not found with ID: {document_id}"
            )
        
        logger.info(f"Successfully updated document with ID: {document_id}")
        return updated_document.to_dict()
    except Exception as e:
        logger.error(f"Error updating document {document_id}: {str(e)}")
        raise

@router.delete("/{document_id}", response_model=Dict[str, str])
def delete_document(
    document_id: UUID,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
) -> Dict[str, str]:
    """
    Delete a document and its associated file
    """
    logger.info(f"Attempting to delete document with ID: {document_id}")
    
    try:
        # Get document details to check access
        document_data = document_service.get_document(document_id)
        if not document_data:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND, 
                detail=f"Document not found with ID: {document_id}"
            )
        
        # Check if user has access to the document's submission
        get_submission_access(document_data['submission']['id'], current_user, db)
        
        # Delete document
        success = document_service.delete_document(document_id)
        if not success:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND, 
                detail=f"Document not found with ID: {document_id}"
            )
        
        logger.info(f"Successfully deleted document with ID: {document_id}")
        return {"message": "Document deleted successfully"}
    except Exception as e:
        logger.error(f"Error deleting document {document_id}: {str(e)}")
        raise

@router.post("/signature/request", response_model=Dict[str, Any])
def request_signature(
    signature_request: DocumentSignatureRequest,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
) -> Dict[str, Any]:
    """
    Request e-signatures for a document using DocuSign
    """
    logger.info(f"Attempting to request signature for document: {signature_request.document_id}")
    
    try:
        # Get document details to check access
        document_data = document_service.get_document(signature_request.document_id)
        if not document_data:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND, 
                detail=f"Document not found with ID: {signature_request.document_id}"
            )
        
        # Check if user has access to the document's submission
        get_submission_access(document_data['submission']['id'], current_user, db)
        
        # Request signature
        signature_response = document_service.request_signature(signature_request)
        logger.info(f"Successfully requested signature for document: {signature_request.document_id}")
        return signature_response.model_dump()
    except DocumentServiceException as e:
        logger.error(f"Error requesting signature for document {signature_request.document_id}: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(e)
        )
    except Exception as e:
        logger.error(f"Error requesting signature for document {signature_request.document_id}: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to request signature: {str(e)}"
        )

@router.get("/{document_id}/signing-url", response_model=Dict[str, str])
def get_signing_url(
    document_id: UUID,
    recipient_email: str,
    recipient_name: str,
    return_url: Optional[str] = None,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
) -> Dict[str, str]:
    """
    Get a signing URL for a specific recipient
    """
    logger.info(f"Attempting to get signing URL for document: {document_id}, recipient: {recipient_email}")
    
    try:
        # Get document details to check access
        document_data = document_service.get_document(document_id)
        if not document_data:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND, 
                detail=f"Document not found with ID: {document_id}"
            )
        
        # Check if user has access to the document's submission
        get_submission_access(document_data['submission']['id'], current_user, db)
        
        # Get signing URL
        signing_url = document_service.get_signing_url(
            document_id=document_id,
            recipient_email=recipient_email,
            recipient_name=recipient_name,
            return_url=return_url
        )
        logger.info(f"Successfully retrieved signing URL for document: {document_id}, recipient: {recipient_email}")
        return {"signing_url": signing_url}
    except DocumentServiceException as e:
        logger.error(f"Error getting signing URL for document {document_id}, recipient {recipient_email}: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(e)
        )
    except Exception as e:
        logger.error(f"Error getting signing URL for document {document_id}, recipient {recipient_email}: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to get signing URL: {str(e)}"
        )

@router.post("/signature/webhook", response_model=Dict[str, str])
def process_signature_webhook(
    webhook_data: Dict[str, Any]
) -> Dict[str, str]:
    """
    Process DocuSign webhook events for signature updates
    """
    logger.info("Received DocuSign webhook event")
    
    try:
        # Process webhook
        success = document_service.process_signature_webhook(webhook_data)
        if success:
            logger.info("Successfully processed DocuSign webhook event")
            return {"message": "Webhook processed successfully"}
        else:
            logger.warning("Failed to process DocuSign webhook event")
            return {"message": "Webhook processing failed"}
    except Exception as e:
        logger.error(f"Error processing DocuSign webhook: {str(e)}")
        return {"message": f"Webhook processing failed: {str(e)}"}