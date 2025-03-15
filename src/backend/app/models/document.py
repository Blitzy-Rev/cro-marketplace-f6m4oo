from sqlalchemy import Column, String, Text, Boolean, ForeignKey, Enum, UUID, DateTime
from sqlalchemy.orm import relationship, validates
from uuid import uuid4
from datetime import datetime

from ..db.base_class import Base
from ..constants.document_types import DocumentType, DOCUMENT_STATUS, REQUIRED_DOCUMENT_TYPES

class Document(Base):
    """
    SQLAlchemy model representing a document in the system.
    
    Documents include legal agreements, specifications, and result reports 
    that are exchanged between pharmaceutical companies and CROs as part of
    the experiment submission and results workflow.
    
    This model supports secure document exchange, e-signature workflows,
    and complies with 21 CFR Part 11 requirements for electronic records.
    """
    
    # Basic document information
    name = Column(String(255), nullable=False)
    type = Column(Enum(DocumentType), nullable=False)
    status = Column(String(50), nullable=False)
    description = Column(Text, nullable=True)
    url = Column(String(255), nullable=False)  # S3 or other storage URL
    version = Column(String(50), nullable=True)
    
    # Signature-related fields
    signature_required = Column(Boolean, default=False)
    is_signed = Column(Boolean, default=False)
    signature_id = Column(String(255), nullable=True)  # DocuSign envelope ID or similar
    signed_at = Column(DateTime, nullable=True)
    
    # Relationships
    submission_id = Column(UUID, ForeignKey("submission.id"), nullable=True)
    uploaded_by = Column(UUID, ForeignKey("user.id"), nullable=False)
    uploaded_at = Column(DateTime, nullable=False)
    
    # Relationship definitions
    submission = relationship("Submission", back_populates="documents")
    uploader = relationship("User", foreign_keys=[uploaded_by])
    
    @validates('status')
    def validate_status(self, key, status):
        """
        Validates that the status is one of the allowed document statuses.
        
        Args:
            key: The field name being validated
            status: The status value to validate
            
        Returns:
            The validated status
            
        Raises:
            ValueError: If status is not a valid DOCUMENT_STATUS key
        """
        if status not in DOCUMENT_STATUS:
            allowed_statuses = list(DOCUMENT_STATUS.keys())
            raise ValueError(f"Invalid document status: {status}. Allowed statuses: {allowed_statuses}")
        return status
    
    @validates('type')
    def validate_type(self, key, type_value):
        """
        Validates that the document type is a valid DocumentType.
        
        Args:
            key: The field name being validated
            type_value: The document type value to validate
            
        Returns:
            The validated document type
            
        Raises:
            ValueError: If type_value is not a valid DocumentType
        """
        if not isinstance(type_value, DocumentType):
            allowed_types = [t.name for t in DocumentType]
            raise ValueError(f"Invalid document type: {type_value}. Allowed types: {allowed_types}")
        return type_value
    
    @classmethod
    def create(cls, name, type, submission_id, uploaded_by, url, 
               signature_required=False, description=None, version="1.0"):
        """
        Creates a new document instance.
        
        Args:
            name: Document name
            type: DocumentType enum value
            submission_id: UUID of associated submission
            uploaded_by: UUID of user who uploaded the document
            url: Storage URL for the document
            signature_required: Whether document requires signatures
            description: Optional document description
            version: Document version string, defaults to "1.0"
            
        Returns:
            New Document instance
        """
        now = datetime.utcnow()
        return cls(
            name=name,
            type=type,
            status="DRAFT",  # Default to DRAFT status
            submission_id=submission_id,
            uploaded_by=uploaded_by,
            url=url,
            signature_required=signature_required,
            description=description,
            version=version,
            is_signed=False,
            uploaded_at=now,
            created_at=now,
            updated_at=now
        )
    
    def update_status(self, new_status):
        """
        Updates the document status.
        
        Args:
            new_status: New status value, must be a key in DOCUMENT_STATUS
            
        Returns:
            True if status was updated, False otherwise
        """
        if new_status not in DOCUMENT_STATUS:
            return False
        
        self.status = new_status
        self.updated_at = datetime.utcnow()
        
        # If the document is being marked as signed, update signature fields
        if new_status == "SIGNED":
            self.is_signed = True
            self.signed_at = datetime.utcnow()
            
        return True
    
    def record_signature(self, signature_id):
        """
        Records signature information for the document.
        
        Args:
            signature_id: Identifier for the signature (e.g., DocuSign envelope ID)
            
        Returns:
            True if signature was recorded, False otherwise
        """
        self.signature_id = signature_id
        self.is_signed = True
        self.signed_at = datetime.utcnow()
        self.status = "SIGNED"
        self.updated_at = datetime.utcnow()
        return True
    
    def get_presigned_url(self, expiration_seconds=3600):
        """
        Gets a presigned URL for secure document access.
        
        This is a placeholder that should be implemented by the service layer
        that handles S3 or other storage integration.
        
        Args:
            expiration_seconds: URL expiration time in seconds
            
        Returns:
            Presigned URL for document access
        """
        # Implementation would be in the service layer, not the model
        raise NotImplementedError("This method should be implemented by the document service")
    
    def is_required_for_submission(self):
        """
        Checks if this document type is required for the associated submission.
        
        Returns:
            True if document is required, False otherwise
        """
        if not self.submission or not hasattr(self.submission, 'cro_service') or not hasattr(self.submission.cro_service, 'service_type'):
            return False
            
        # Get the service type from the submission's CRO service
        service_type = self.submission.cro_service.service_type
        
        # Check if this document type is in the required documents for this service
        required_docs = REQUIRED_DOCUMENT_TYPES.get(service_type, [])
        return self.type in required_docs
    
    def to_dict(self, include_relationships=False):
        """
        Converts document to dictionary representation.
        
        Args:
            include_relationships: Whether to include related entities
            
        Returns:
            Dictionary representation of document
        """
        result = super().to_dict()
        
        # Convert enum to string for serialization
        if self.type:
            result['type'] = self.type.name
            
        # Add document status description
        result['status_description'] = DOCUMENT_STATUS.get(self.status, "")
        
        # Add relationship data if requested
        if include_relationships and self.submission:
            submission_data = {'id': str(self.submission.id)}
            
            # Safely add submission name if available
            if hasattr(self.submission, 'name'):
                submission_data['name'] = self.submission.name
                
            result['submission'] = submission_data
            
        return result