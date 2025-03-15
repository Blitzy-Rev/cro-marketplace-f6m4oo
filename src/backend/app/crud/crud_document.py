from typing import Optional, List, Dict, Any, Union
from sqlalchemy import select, and_, or_
from sqlalchemy.orm import Session
import uuid
from datetime import datetime

from .base import CRUDBase
from ..models.document import Document
from ..schemas.document import DocumentCreate, DocumentUpdate, DocumentFilter
from ..db.session import db_session
from ..constants.document_types import DOCUMENT_STATUS, DocumentType
from ..core.logging import get_logger

# Initialize logger
logger = get_logger(__name__)


class CRUDDocument(CRUDBase[Document, DocumentCreate, DocumentUpdate]):
    """
    CRUD operations for Document model, extending the generic CRUDBase class
    with document-specific functionality for secure document exchange,
    e-signature workflows, and 21 CFR Part 11 compliance.
    """

    def __init__(self):
        """Initialize the CRUDDocument class with Document model"""
        super().__init__(Document)

    def create_with_owner(
        self, 
        obj_in: Union[DocumentCreate, Dict[str, Any]], 
        owner_id: Union[uuid.UUID, str],
        db: Optional[Session] = None
    ) -> Document:
        """
        Create a new document with owner information
        
        Args:
            obj_in: Document creation data
            owner_id: ID of the user creating the document
            db: Optional database session (uses default if not provided)
            
        Returns:
            Created document instance
        """
        db_session_local = db or db_session
        
        # Convert to dict if it's a Pydantic model
        if not isinstance(obj_in, dict):
            obj_in_data = obj_in.model_dump()
        else:
            obj_in_data = obj_in.copy()
        
        # Set owner ID
        obj_in_data["uploaded_by"] = owner_id
        
        # Set default status if not provided
        if "status" not in obj_in_data:
            obj_in_data["status"] = "DRAFT"
            
        # Set default signed status if not provided
        if "is_signed" not in obj_in_data:
            obj_in_data["is_signed"] = False
            
        # Set timestamps
        now = datetime.utcnow()
        obj_in_data["uploaded_at"] = now
        obj_in_data["created_at"] = now
        obj_in_data["updated_at"] = now
        
        # Create the document
        document = self.create(obj_in_data, db=db_session_local)
        return document

    def get_by_submission(
        self, 
        submission_id: Union[uuid.UUID, str],
        db: Optional[Session] = None
    ) -> List[Document]:
        """
        Get all documents for a specific submission
        
        Args:
            submission_id: ID of the submission
            db: Optional database session (uses default if not provided)
            
        Returns:
            List of documents for the submission
        """
        db_session_local = db or db_session
        
        # Query documents for the submission
        query = db_session_local.query(self.model).filter(self.model.submission_id == submission_id)
        results = query.all()
        
        return results

    def get_with_presigned_url(
        self,
        document_id: Union[uuid.UUID, str],
        db: Optional[Session] = None,
        expiration_seconds: int = 3600
    ) -> Optional[Dict[str, Any]]:
        """
        Get document with presigned URL for secure access
        
        Args:
            document_id: ID of the document to retrieve
            db: Optional database session (uses default if not provided)
            expiration_seconds: Expiration time for presigned URL in seconds
            
        Returns:
            Document with presigned URL or None if not found
        """
        db_session_local = db or db_session
        
        # Get the document
        document = self.get(document_id, db=db_session_local)
        if not document:
            return None
        
        try:
            # Create a dictionary representation of the document
            document_data = document.to_dict()
            
            # In a real implementation, this would call a document service method
            # that implements the URL generation rather than the placeholder method
            # in the model. The document service would interact with S3 to generate
            # a proper presigned URL with appropriate permissions and expiration.
            # For example:
            # from ..services.document import get_presigned_url
            # presigned_url = get_presigned_url(document.url, expiration_seconds)
            
            # Since we can't access the actual S3 service in this context,
            # create a mock URL for demonstration purposes
            document_data["presigned_url"] = f"{document.url}?expiry={expiration_seconds}"
            
            return document_data
        except Exception as e:
            logger.error(f"Error generating presigned URL for document {document_id}: {str(e)}")
            return None

    def update_status(
        self,
        document_id: Union[uuid.UUID, str],
        status: str,
        db: Optional[Session] = None
    ) -> Optional[Document]:
        """
        Update document status
        
        Args:
            document_id: ID of the document to update
            status: New status value (must be a valid document status)
            db: Optional database session (uses default if not provided)
            
        Returns:
            Updated document or None if not found
        """
        db_session_local = db or db_session
        
        # Get the document
        document = self.get(document_id, db=db_session_local)
        if not document:
            logger.warning(f"Attempted to update status for non-existent document {document_id}")
            return None
        
        # Update the status
        success = document.update_status(status)
        if not success:
            logger.warning(f"Failed to update document {document_id} status to {status}")
            return None
            
        # Commit changes
        db_session_local.add(document)
        db_session_local.commit()
        db_session_local.refresh(document)
        
        logger.info(f"Updated document {document_id} status to {status}")
        return document

    def record_signature(
        self,
        document_id: Union[uuid.UUID, str],
        signature_id: str,
        db: Optional[Session] = None
    ) -> Optional[Document]:
        """
        Record signature information for a document
        
        Args:
            document_id: ID of the document
            signature_id: External signature ID (e.g., DocuSign envelope ID)
            db: Optional database session (uses default if not provided)
            
        Returns:
            Updated document or None if not found
        """
        db_session_local = db or db_session
        
        # Get the document
        document = self.get(document_id, db=db_session_local)
        if not document:
            logger.warning(f"Attempted to record signature for non-existent document {document_id}")
            return None
        
        # Record the signature
        success = document.record_signature(signature_id)
        if not success:
            logger.warning(f"Failed to record signature {signature_id} for document {document_id}")
            return None
            
        # Commit changes
        db_session_local.add(document)
        db_session_local.commit()
        db_session_local.refresh(document)
        
        logger.info(f"Recorded signature {signature_id} for document {document_id}")
        return document

    def get_by_signature_id(
        self,
        signature_id: str,
        db: Optional[Session] = None
    ) -> Optional[Document]:
        """
        Get document by external signature ID (e.g., DocuSign envelope ID)
        
        Args:
            signature_id: External signature ID to search for
            db: Optional database session (uses default if not provided)
            
        Returns:
            Document or None if not found
        """
        db_session_local = db or db_session
        
        # Query document with the signature ID
        document = db_session_local.query(self.model).filter(self.model.signature_id == signature_id).first()
        
        return document

    def apply_filters(self, filters: DocumentFilter, query: Any) -> Any:
        """
        Apply filters to document query based on DocumentFilter schema
        
        Args:
            filters: Filter criteria
            query: SQLAlchemy query object
            
        Returns:
            Filtered query
        """
        if filters.name_contains:
            query = query.filter(self.model.name.ilike(f"%{filters.name_contains}%"))
            
        if filters.submission_id:
            query = query.filter(self.model.submission_id == filters.submission_id)
            
        if filters.uploaded_by:
            query = query.filter(self.model.uploaded_by == filters.uploaded_by)
            
        if filters.type:
            query = query.filter(self.model.type.in_(filters.type))
            
        if filters.status:
            query = query.filter(self.model.status.in_(filters.status))
            
        if filters.is_signed is not None:
            query = query.filter(self.model.is_signed == filters.is_signed)
            
        if filters.signature_required is not None:
            query = query.filter(self.model.signature_required == filters.signature_required)
            
        if filters.uploaded_after:
            query = query.filter(self.model.uploaded_at >= filters.uploaded_after)
            
        if filters.uploaded_before:
            query = query.filter(self.model.uploaded_at <= filters.uploaded_before)
            
        return query

    def filter_documents(
        self,
        filters: DocumentFilter,
        db: Optional[Session] = None,
        skip: int = 0,
        limit: int = 100
    ) -> Dict[str, Any]:
        """
        Filter documents based on DocumentFilter schema with pagination
        
        Args:
            filters: Filter criteria
            db: Optional database session (uses default if not provided)
            skip: Number of records to skip (for pagination)
            limit: Maximum number of records to return (for pagination)
            
        Returns:
            Dictionary with filtered documents and pagination metadata
        """
        db_session_local = db or db_session
        
        # Create base query for Document model
        base_query = db_session_local.query(self.model)
        
        # Apply filters
        filtered_query = self.apply_filters(filters, base_query)
        
        # Count total for pagination metadata
        total = filtered_query.count()
        
        # Apply pagination
        paginated_query = filtered_query.offset(skip).limit(limit)
        
        # Execute query to get filtered documents
        documents = paginated_query.all()
        
        # Return results with pagination metadata
        return {
            "items": documents,
            "total": total,
            "page": skip // limit + 1 if limit > 0 else 1,
            "size": limit,
            "pages": (total + limit - 1) // limit if limit > 0 else 1
        }

    def get_required_documents(
        self,
        submission_id: Union[uuid.UUID, str],
        db: Optional[Session] = None
    ) -> List[Dict[str, Any]]:
        """
        Get list of required documents for a submission based on CRO service type
        
        Args:
            submission_id: ID of the submission
            db: Optional database session (uses default if not provided)
            
        Returns:
            List of required document types with metadata
        """
        db_session_local = db or db_session
        
        try:
            # Get submission by ID to determine CRO service type
            from ..models.submission import Submission
            from ..constants.document_types import REQUIRED_DOCUMENT_TYPES, DOCUMENT_TYPE_DESCRIPTIONS
            
            submission = db_session_local.query(Submission).filter(Submission.id == submission_id).first()
            
            if not submission or not hasattr(submission, 'cro_service') or not hasattr(submission.cro_service, 'service_type'):
                logger.warning(f"Cannot determine required documents for submission {submission_id} - missing service type")
                return []
                
            # Get required document types for this service type
            service_type = submission.cro_service.service_type
            required_types = REQUIRED_DOCUMENT_TYPES.get(service_type, [])
            
            # Get existing documents for this submission
            existing_documents = self.get_by_submission(submission_id, db=db_session_local)
            
            # Create a list of required documents with their status
            result = []
            for doc_type in required_types:
                # Find if this document type already exists for the submission
                existing_doc = next((doc for doc in existing_documents if doc.type == doc_type), None)
                
                document_info = {
                    "type": doc_type,
                    "type_name": doc_type.name,
                    "description": DOCUMENT_TYPE_DESCRIPTIONS.get(doc_type, ""),
                    "required": True,
                    "completed": False
                }
                
                # If document exists and is signed, mark as completed
                if existing_doc and existing_doc.is_signed:
                    document_info["completed"] = True
                    document_info["document_id"] = str(existing_doc.id)
                    document_info["status"] = existing_doc.status
                elif existing_doc:
                    document_info["document_id"] = str(existing_doc.id)
                    document_info["status"] = existing_doc.status
                
                result.append(document_info)
                
            return result
        except Exception as e:
            logger.error(f"Error getting required documents for submission {submission_id}: {str(e)}")
            return []


# Create a singleton instance for use throughout the application
document = CRUDDocument()