import uuid
import datetime
import io
import base64
import mimetypes
from typing import Optional, List, Dict, Any, Union

from ..crud.crud_document import document
from ..models.document import Document
from ..schemas.document import (
    DocumentCreate, DocumentUpdate, DocumentFilter, 
    DocumentSignatureRequest, DocumentSignatureResponse, DocumentUploadResponse
)
from ..integrations.aws.s3 import S3Client
from ..integrations.docusign.client import DocuSignClient
from ..integrations.docusign.models import (
    EnvelopeCreate, Recipient, DocumentInfo
)
from ..integrations.docusign.exceptions import DocuSignException
from ..constants.document_types import DocumentType, DOCUMENT_STATUS, SIGNATURE_REQUIRED_TYPES
from ..core.logging import get_logger
from ..core.config import settings
from ..core.exceptions import ServiceException

# Initialize logger
logger = get_logger(__name__)

# Constants
DEFAULT_PRESIGNED_URL_EXPIRATION = 3600  # 1 hour
DOCUMENT_FOLDER = "documents"


class DocumentServiceException(ServiceException):
    """Exception class for document service errors"""
    def __init__(self, message: str):
        super().__init__(message)


class DocumentService:
    """Service for managing documents, including storage, retrieval, and e-signature workflows"""
    
    def __init__(self):
        """Initialize the DocumentService with S3 and DocuSign clients"""
        # Initialize S3 client for document storage
        self._s3_client = S3Client(bucket_name=settings.DOCUMENT_STORAGE_BUCKET)
        
        # Initialize DocuSign client with configuration from settings
        self._docusign_client = DocuSignClient(settings.DOCUSIGN_CONFIG)
        
        # Authenticate DocuSign client
        self._docusign_client.authenticate()
    
    def create_document(self, document_data: DocumentCreate, owner_id: uuid.UUID) -> Document:
        """Create a new document record in the database
        
        Args:
            document_data: Document creation data
            owner_id: ID of the user creating the document
            
        Returns:
            Created document instance
        """
        logger.info(f"Creating document: {document_data.name}")
        created_document = document.create_with_owner(document_data, owner_id)
        logger.info(f"Document created with ID: {created_document.id}")
        return created_document
    
    def get_document(self, document_id: uuid.UUID, url_expiration: Optional[int] = None) -> Optional[Dict[str, Any]]:
        """Get a document by ID with optional presigned URL
        
        Args:
            document_id: ID of the document to retrieve
            url_expiration: Expiration time for presigned URL in seconds
            
        Returns:
            Document with presigned URL or None if not found
        """
        # Set default URL expiration if not provided
        url_expiration = url_expiration or DEFAULT_PRESIGNED_URL_EXPIRATION
        
        # Get document with presigned URL
        return document.get_with_presigned_url(document_id, expiration_seconds=url_expiration)
    
    def get_documents_by_submission(self, submission_id: uuid.UUID, url_expiration: Optional[int] = None) -> List[Dict[str, Any]]:
        """Get all documents for a specific submission
        
        Args:
            submission_id: ID of the submission
            url_expiration: Expiration time for presigned URLs in seconds
            
        Returns:
            List of documents with presigned URLs
        """
        # Set default URL expiration if not provided
        url_expiration = url_expiration or DEFAULT_PRESIGNED_URL_EXPIRATION
        
        # Get documents for the submission
        documents_list = document.get_by_submission(submission_id)
        
        # Add presigned URLs to each document
        result = []
        for doc in documents_list:
            doc_dict = doc.to_dict()
            doc_dict['presigned_url'] = self._s3_client.get_download_url(doc.url, expiration=url_expiration)
            result.append(doc_dict)
        
        return result
    
    def filter_documents(self, filters: DocumentFilter, skip: int, limit: int, url_expiration: Optional[int] = None) -> Dict[str, Any]:
        """Filter documents based on criteria with pagination
        
        Args:
            filters: Filter criteria for documents
            skip: Number of records to skip (pagination)
            limit: Maximum number of records to return (pagination)
            url_expiration: Expiration time for presigned URLs in seconds
            
        Returns:
            Filtered documents with pagination metadata
        """
        # Set default URL expiration if not provided
        url_expiration = url_expiration or DEFAULT_PRESIGNED_URL_EXPIRATION
        
        # Filter documents using CRUD operations
        result = document.filter_documents(filters, skip=skip, limit=limit)
        
        # Add presigned URLs to each document
        items_with_urls = []
        for doc in result['items']:
            doc_dict = doc.to_dict()
            doc_dict['presigned_url'] = self._s3_client.get_download_url(doc.url, expiration=url_expiration)
            items_with_urls.append(doc_dict)
        
        # Update items in the result
        result['items'] = items_with_urls
        
        return result
    
    def update_document(self, document_id: uuid.UUID, document_data: DocumentUpdate) -> Optional[Document]:
        """Update an existing document
        
        Args:
            document_id: ID of the document to update
            document_data: Updated document data
            
        Returns:
            Updated document or None if not found
        """
        logger.info(f"Updating document: {document_id}")
        
        # Get the document
        doc = document.get(document_id)
        if not doc:
            logger.warning(f"Document not found for update: {document_id}")
            return None
        
        # Update the document
        updated_doc = document.update(doc, document_data)
        logger.info(f"Document updated: {document_id}")
        return updated_doc
    
    def delete_document(self, document_id: uuid.UUID) -> bool:
        """Delete a document and its associated file
        
        Args:
            document_id: ID of the document to delete
            
        Returns:
            True if deletion was successful, False otherwise
        """
        logger.info(f"Deleting document: {document_id}")
        
        # Get the document
        doc = document.get(document_id)
        if not doc:
            logger.warning(f"Document not found for deletion: {document_id}")
            return False
        
        # Delete file from S3
        try:
            self._s3_client.delete(doc.url)
        except Exception as e:
            logger.error(f"Error deleting document file from S3: {str(e)}")
            # Continue with document deletion even if file deletion fails
        
        # Delete document from database
        document.remove(document_id)
        logger.info(f"Document deleted: {document_id}")
        return True
    
    def generate_upload_url(self, filename: str, document_type: DocumentType, submission_id: uuid.UUID, 
                            owner_id: uuid.UUID, content_type: Optional[str] = None, 
                            expiration: Optional[int] = None) -> DocumentUploadResponse:
        """Generate a presigned URL for document upload
        
        Args:
            filename: Original filename
            document_type: Type of document (from DocumentType enum)
            submission_id: ID of the associated submission
            owner_id: ID of the user uploading the document
            content_type: MIME type of the document (optional)
            expiration: URL expiration time in seconds (optional)
            
        Returns:
            Upload response with document ID and upload URL
        """
        expiration = expiration or DEFAULT_PRESIGNED_URL_EXPIRATION
        
        # Determine content type if not provided
        if not content_type:
            content_type, _ = mimetypes.guess_type(filename)
            content_type = content_type or 'application/octet-stream'
        
        # Generate S3 key for document
        s3_key = self._s3_client.generate_key(DOCUMENT_FOLDER, filename)
        
        # Create document in database
        doc_data = DocumentCreate(
            name=filename,
            type=document_type,
            status="DRAFT",
            submission_id=submission_id,
            url=s3_key,
            content_type=content_type
        )
        
        created_doc = self.create_document(doc_data, owner_id)
        
        # Generate presigned upload URL
        upload_url = self._s3_client.get_upload_url(s3_key, content_type=content_type, expiration=expiration)
        
        return DocumentUploadResponse(
            document_id=created_doc.id,
            name=created_doc.name,
            type=created_doc.type,
            status=created_doc.status,
            upload_url=upload_url,
            upload_fields={}  # For direct S3 upload, no additional fields needed
        )
    
    def upload_document(self, content: bytes, filename: str, document_type: DocumentType, 
                       submission_id: uuid.UUID, owner_id: uuid.UUID, 
                       content_type: Optional[str] = None) -> Document:
        """Upload document content directly
        
        Args:
            content: Document content as bytes
            filename: Original filename
            document_type: Type of document (from DocumentType enum)
            submission_id: ID of the associated submission
            owner_id: ID of the user uploading the document
            content_type: MIME type of the document (optional)
            
        Returns:
            Created document instance
        """
        # Determine content type if not provided
        if not content_type:
            content_type, _ = mimetypes.guess_type(filename)
            content_type = content_type or 'application/octet-stream'
        
        # Generate S3 key for document
        s3_key = self._s3_client.generate_key(DOCUMENT_FOLDER, filename)
        
        # Upload content to S3
        self._s3_client.upload(content, s3_key, content_type=content_type)
        
        # Create document in database
        doc_data = DocumentCreate(
            name=filename,
            type=document_type,
            status="DRAFT",
            submission_id=submission_id,
            url=s3_key,
            content_type=content_type,
            file_size=len(content)
        )
        
        return self.create_document(doc_data, owner_id)
    
    def download_document(self, document_id: uuid.UUID) -> Optional[bytes]:
        """Download document content
        
        Args:
            document_id: ID of the document to download
            
        Returns:
            Document content as bytes or None if not found
        """
        # Get the document
        doc = document.get(document_id)
        if not doc:
            return None
        
        # Download content from S3
        return self._s3_client.download(doc.url)
    
    def request_signature(self, signature_request: DocumentSignatureRequest) -> DocumentSignatureResponse:
        """Request e-signatures for a document using DocuSign
        
        Args:
            signature_request: Signature request details
            
        Returns:
            Signature response with envelope ID and signing URL
            
        Raises:
            ServiceException: When signature request fails
        """
        logger.info(f"Requesting signature for document: {signature_request.document_id}")
        
        # Get document
        doc = document.get(signature_request.document_id)
        if not doc:
            raise ServiceException(f"Document not found: {signature_request.document_id}")
        
        # Check if document type requires signature
        if doc.type not in SIGNATURE_REQUIRED_TYPES:
            raise ServiceException(f"Document type does not require signature: {doc.type}")
        
        # Download document content
        content = self._s3_client.download(doc.url)
        if not content:
            raise ServiceException(f"Failed to download document content: {doc.url}")
        
        # Prepare document for DocuSign
        docusign_document = DocumentInfo(
            document_id="1",  # DocuSign uses 1-based indexing
            name=doc.name,
            file_extension=doc.url.split('.')[-1] if '.' in doc.url else None,
            document_base64=base64.b64encode(content).decode('utf-8')
        )
        
        # Prepare recipients
        docusign_recipients = []
        for i, signer in enumerate(signature_request.signers, 1):
            docusign_recipients.append(Recipient(
                email=signer['email'],
                name=signer['name'],
                recipient_id=str(i),
                recipient_type="SIGNER",
                routing_order=str(i)
            ))
        
        # Create envelope
        envelope_data = EnvelopeCreate(
            email_subject=signature_request.email_subject or f"Please sign document: {doc.name}",
            email_body=signature_request.email_message,
            documents=[docusign_document],
            recipients=docusign_recipients,
            status="sent"
        )
        
        # Send to DocuSign
        try:
            envelope = self._docusign_client.create_envelope(envelope_data)
            
            # Update document status
            document.update_status(doc.id, "PENDING_SIGNATURE")
            
            # Record signature ID
            document.record_signature(doc.id, envelope.envelope_id)
            
            # Create recipient view for first signer
            signing_url = self._docusign_client.create_recipient_view(
                envelope_id=envelope.envelope_id,
                recipient_email=signature_request.signers[0]['email'],
                recipient_name=signature_request.signers[0]['name'],
                return_url=signature_request.redirect_url
            )
            
            return DocumentSignatureResponse(
                document_id=doc.id,
                envelope_id=envelope.envelope_id,
                signing_url=signing_url.url,
                status=envelope.status
            )
        except DocuSignException as e:
            logger.error(f"DocuSign signature request failed: {str(e)}")
            raise ServiceException(f"Failed to create signature request: {str(e)}")
        except Exception as e:
            logger.error(f"Signature request failed: {str(e)}")
            raise ServiceException(f"Failed to create signature request: {str(e)}")
    
    def get_signing_url(self, document_id: uuid.UUID, recipient_email: str, recipient_name: str, 
                       return_url: Optional[str] = None) -> str:
        """Get a signing URL for a specific recipient
        
        Args:
            document_id: ID of the document to sign
            recipient_email: Email of the recipient
            recipient_name: Name of the recipient
            return_url: URL to redirect after signing (optional)
            
        Returns:
            URL for signing the document
            
        Raises:
            ServiceException: When URL generation fails
        """
        # Get document
        doc = document.get(document_id)
        if not doc:
            raise ServiceException(f"Document not found: {document_id}")
        
        # Check if document is in PENDING_SIGNATURE status
        if doc.status != "PENDING_SIGNATURE":
            raise ServiceException(f"Document is not pending signature: {document_id}")
        
        # Check if the document has a signature ID
        if not doc.signature_id:
            raise ServiceException(f"Document does not have a signature ID: {document_id}")
        
        # Create recipient view
        try:
            signing_url = self._docusign_client.create_recipient_view(
                envelope_id=doc.signature_id,
                recipient_email=recipient_email,
                recipient_name=recipient_name,
                return_url=return_url
            )
            
            return signing_url.url
        except Exception as e:
            logger.error(f"Failed to get signing URL: {str(e)}")
            raise ServiceException(f"Failed to generate signing URL: {str(e)}")
    
    def process_signature_webhook(self, webhook_data: Dict[str, Any]) -> bool:
        """Process DocuSign webhook events for signature updates
        
        Args:
            webhook_data: Webhook data from DocuSign
            
        Returns:
            True if webhook was processed successfully, False otherwise
        """
        logger.info("Processing DocuSign webhook event")
        
        try:
            # Process webhook event
            webhook_event = self._docusign_client.process_webhook_event(webhook_data)
            
            # Get envelope ID
            envelope_id = webhook_event.envelope_id
            if not envelope_id:
                logger.warning("Webhook event missing envelope ID")
                return False
            
            # Find document by signature ID
            doc = document.get_by_signature_id(envelope_id)
            if not doc:
                logger.warning(f"No document found for signature ID: {envelope_id}")
                return False
            
            # Get envelope status from DocuSign
            envelope = self._docusign_client.get_envelope(envelope_id)
            
            # Update document status based on envelope status
            if envelope.status.upper() == "COMPLETED":
                document.update_status(doc.id, "SIGNED")
                logger.info(f"Document {doc.id} marked as signed")
            elif envelope.status.upper() == "DECLINED":
                document.update_status(doc.id, "REJECTED")
                logger.info(f"Document {doc.id} signature was declined")
            elif envelope.status.upper() == "VOIDED":
                document.update_status(doc.id, "REJECTED")
                logger.info(f"Document {doc.id} envelope was voided")
            
            logger.info(f"Successfully processed webhook for document {doc.id}")
            return True
        except Exception as e:
            logger.error(f"Error processing DocuSign webhook: {str(e)}")
            return False
    
    def get_required_documents(self, submission_id: uuid.UUID) -> List[Dict[str, Any]]:
        """Get list of required documents for a submission
        
        Args:
            submission_id: ID of the submission
            
        Returns:
            List of required document types with metadata
        """
        return document.get_required_documents(submission_id)