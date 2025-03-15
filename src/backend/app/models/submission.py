from datetime import datetime, timedelta
import uuid

from sqlalchemy import Column, String, Text, Float, Integer, Boolean, ForeignKey, Table, UUID, JSON, DateTime
from sqlalchemy.orm import relationship, validates

from ..db.base_class import Base
from ..constants.submission_status import (
    SubmissionStatus, STATUS_TRANSITIONS, ACTIVE_STATUSES, EDITABLE_STATUSES
)

# Association table for the many-to-many relationship between submissions and molecules
submission_molecule = Table(
    'submission_molecule',
    Base.metadata,
    Column('submission_id', UUID, ForeignKey('submission.id'), primary_key=True),
    Column('molecule_id', UUID, ForeignKey('molecule.id'), primary_key=True),
    Column('added_at', DateTime, default=datetime.utcnow),
    Column('concentration', Float, nullable=True),
    Column('notes', Text, nullable=True)
)


class Submission(Base):
    """
    SQLAlchemy model representing a submission to a Contract Research Organization (CRO)
    for experimental testing of molecules.
    
    This model tracks the complete workflow from submission creation through pricing,
    approval, experimental execution, and result delivery.
    """
    
    # Basic information
    name = Column(String(255), nullable=False)
    status = Column(String(50), nullable=False, default=SubmissionStatus.DRAFT.value)
    cro_service_id = Column(UUID, ForeignKey('cro_service.id'), nullable=False)
    created_by = Column(UUID, ForeignKey('user.id'), nullable=False)
    description = Column(Text, nullable=True)
    
    # Pricing and timeline information
    price = Column(Float, nullable=True)
    price_currency = Column(String(3), nullable=True, default='USD')
    estimated_turnaround_days = Column(Integer, nullable=True)
    estimated_completion_date = Column(DateTime, nullable=True)
    
    # Experiment specifications stored as JSON
    specifications = Column(JSON, nullable=True)
    
    # Workflow timestamps
    submitted_at = Column(DateTime, nullable=True)
    approved_at = Column(DateTime, nullable=True)
    completed_at = Column(DateTime, nullable=True)
    
    # Relationships
    creator = relationship("User", back_populates="submissions", foreign_keys=[created_by])
    cro_service = relationship("CROService", back_populates="submissions")
    molecules = relationship("Molecule", secondary=submission_molecule, back_populates="submissions")
    documents = relationship("Document", back_populates="submission")
    results = relationship("Result", back_populates="submission")
    
    @validates('status')
    def validate_status(self, key, status):
        """
        Validates that the status is one of the allowed submission statuses.
        
        Args:
            key: The attribute name being validated
            status: The status value to validate
            
        Returns:
            The validated status
            
        Raises:
            ValueError: If the status is not a valid SubmissionStatus value
        """
        if status not in [s.value for s in SubmissionStatus]:
            valid_statuses = ", ".join([s.value for s in SubmissionStatus])
            raise ValueError(f"Invalid submission status. Must be one of: {valid_statuses}")
        return status
    
    @classmethod
    def create(cls, name, created_by, cro_service_id, description=None):
        """
        Creates a new submission instance.
        
        Args:
            name: Name of the submission
            created_by: UUID of the user creating the submission
            cro_service_id: UUID of the CRO service for this submission
            description: Optional description of the submission
            
        Returns:
            A new Submission instance
        """
        submission = cls(
            name=name,
            created_by=created_by,
            cro_service_id=cro_service_id,
            description=description,
            status=SubmissionStatus.DRAFT.value,
            created_at=datetime.utcnow(),
            updated_at=datetime.utcnow()
        )
        return submission
    
    def update_status(self, new_status):
        """
        Updates the submission status if the transition is valid.
        
        Args:
            new_status: The new status to set
            
        Returns:
            True if status was updated, False if invalid transition
        """
        # Verify the new status is valid
        if new_status not in [s.value for s in SubmissionStatus]:
            return False
        
        # Check if the transition is allowed
        if new_status not in STATUS_TRANSITIONS.get(self.status, []):
            return False
        
        # Update status and related timestamps
        self.status = new_status
        
        # Update workflow timestamps based on status
        now = datetime.utcnow()
        if new_status == SubmissionStatus.SUBMITTED.value:
            self.submitted_at = now
        elif new_status == SubmissionStatus.APPROVED.value:
            self.approved_at = now
        elif new_status == SubmissionStatus.COMPLETED.value:
            self.completed_at = now
        
        # Update the updated_at timestamp
        self.updated_at = now
        
        return True
    
    def add_molecule(self, molecule_id, concentration=None, notes=None):
        """
        Adds a molecule to the submission.
        
        Args:
            molecule_id: UUID of the molecule to add
            concentration: Optional concentration for testing
            notes: Optional notes about this molecule in the submission
            
        Returns:
            True if molecule was added, False if already exists or submission not editable
        """
        # Check if submission is editable
        if self.status not in EDITABLE_STATUSES:
            return False
        
        # Check if molecule is already in this submission
        for mol in self.molecules:
            if mol.id == molecule_id:
                return False
        
        # Create the association with optional parameters
        # Note: This requires a Session to be active, so we return True
        # and let the caller handle the actual association creation
        # with the appropriate Session handling
        self.updated_at = datetime.utcnow()
        return True
    
    def remove_molecule(self, molecule_id):
        """
        Removes a molecule from the submission.
        
        Args:
            molecule_id: UUID of the molecule to remove
            
        Returns:
            True if molecule was removed, False if not found or submission not editable
        """
        # Check if submission is editable
        if self.status not in EDITABLE_STATUSES:
            return False
        
        # Find the molecule in the submission
        molecule_to_remove = None
        for mol in self.molecules:
            if mol.id == molecule_id:
                molecule_to_remove = mol
                break
        
        if not molecule_to_remove:
            return False
        
        # Remove the molecule and update timestamp
        # Note: This requires a Session to be active, so we return True
        # and let the caller handle the actual removal
        # with the appropriate Session handling
        self.updated_at = datetime.utcnow()
        return True
    
    def set_pricing(self, price, price_currency='USD', estimated_turnaround_days=None):
        """
        Sets the pricing and timeline information for the submission.
        
        Args:
            price: The price for conducting the experiments
            price_currency: The currency code for the price (default: USD)
            estimated_turnaround_days: Estimated number of days to complete the experiments
            
        Returns:
            True if pricing was set, False if submission not in appropriate status
        """
        # Check if status allows pricing updates
        if self.status not in [SubmissionStatus.PENDING_REVIEW.value, SubmissionStatus.PRICING_PROVIDED.value]:
            return False
        
        # Update pricing information
        self.price = price
        self.price_currency = price_currency
        self.estimated_turnaround_days = estimated_turnaround_days
        
        # Calculate estimated completion date if turnaround days is provided
        if estimated_turnaround_days:
            self.estimated_completion_date = datetime.utcnow() + timedelta(days=estimated_turnaround_days)
        
        # Update timestamp
        self.updated_at = datetime.utcnow()
        
        return True
    
    def set_specifications(self, specifications):
        """
        Sets the experiment specifications for the submission.
        
        Args:
            specifications: Dictionary containing experiment specifications
            
        Returns:
            True if specifications were set, False if submission not editable
        """
        # Check if submission is editable
        if self.status not in EDITABLE_STATUSES:
            return False
        
        # Update specifications and timestamp
        self.specifications = specifications
        self.updated_at = datetime.utcnow()
        
        return True
    
    def get_specifications(self):
        """
        Gets the experiment specifications as a dictionary.
        
        Returns:
            Experiment specifications as a dictionary
        """
        if self.specifications is None:
            return {}
        
        if isinstance(self.specifications, dict):
            return self.specifications
        
        # If stored as JSON string, parse to dict
        try:
            import json
            return json.loads(self.specifications)
        except (TypeError, json.JSONDecodeError):
            return {}
    
    def submit(self):
        """
        Submits the submission to the CRO.
        
        Returns:
            True if submission was successful, False if requirements not met
        """
        # Check if submission is in DRAFT status
        if self.status != SubmissionStatus.DRAFT.value:
            return False
        
        # Check if submission has molecules
        if not self.molecules or len(self.molecules) == 0:
            return False
        
        # Check if required documents are attached
        if not self.has_required_documents():
            return False
        
        # Update status to SUBMITTED
        return self.update_status(SubmissionStatus.SUBMITTED.value)
    
    def approve(self):
        """
        Approves the submission pricing and timeline.
        
        Returns:
            True if approval was successful, False if not in appropriate status
        """
        # Check if submission is in PRICING_PROVIDED status
        if self.status != SubmissionStatus.PRICING_PROVIDED.value:
            return False
        
        # Check if price and timeline are set
        if self.price is None or self.estimated_turnaround_days is None:
            return False
        
        # Update status to APPROVED
        return self.update_status(SubmissionStatus.APPROVED.value)
    
    def complete(self):
        """
        Marks the submission as completed.
        
        Returns:
            True if completion was successful, False if not in appropriate status
        """
        # Check if submission is in RESULTS_REVIEWED status
        if self.status != SubmissionStatus.RESULTS_REVIEWED.value:
            return False
        
        # Update status to COMPLETED
        return self.update_status(SubmissionStatus.COMPLETED.value)
    
    def cancel(self):
        """
        Cancels the submission.
        
        Returns:
            True if cancellation was successful, False if in terminal status
        """
        # Check if submission is in an active status
        if self.status not in ACTIVE_STATUSES:
            return False
        
        # Update status to CANCELLED
        return self.update_status(SubmissionStatus.CANCELLED.value)
    
    def is_editable(self):
        """
        Checks if the submission is in an editable state.
        
        Returns:
            True if submission is editable, False otherwise
        """
        return self.status in EDITABLE_STATUSES
    
    def is_active(self):
        """
        Checks if the submission is in an active state.
        
        Returns:
            True if submission is active, False otherwise
        """
        return self.status in ACTIVE_STATUSES
    
    def has_required_documents(self):
        """
        Checks if the submission has all required documents.
        
        Returns:
            True if all required documents are present, False otherwise
        """
        # Get required document types for this CRO service
        required_document_types = []
        
        # First check for required_document_types attribute
        if hasattr(self.cro_service, 'required_document_types'):
            required_document_types = self.cro_service.required_document_types
        # Then try get_required_document_types method
        elif hasattr(self.cro_service, 'get_required_document_types'):
            required_document_types = self.cro_service.get_required_document_types()
        
        # If we still don't have required document types, assume none are required
        if not required_document_types:
            return True
        
        # Check if all required document types are present
        if not self.documents:
            return False
        
        present_document_types = set(doc.document_type for doc in self.documents)
        return set(required_document_types).issubset(present_document_types)
    
    def to_dict(self, include_relationships=False):
        """
        Converts submission to dictionary representation.
        
        Args:
            include_relationships: Whether to include related entities in the dictionary
            
        Returns:
            Dictionary representation of submission
        """
        # Start with the base to_dict method from Base
        result = super().to_dict()
        
        # Add specifications as parsed dictionary
        result['specifications'] = self.get_specifications()
        
        # Add relationships if requested
        if include_relationships:
            # Handle molecules relationship
            if hasattr(self, 'molecules') and self.molecules:
                result['molecules'] = [
                    mol.to_dict() if hasattr(mol, 'to_dict') else {'id': str(mol.id)}
                    for mol in self.molecules
                ]
            else:
                result['molecules'] = []
                
            # Handle documents relationship
            if hasattr(self, 'documents') and self.documents:
                result['documents'] = [
                    doc.to_dict() if hasattr(doc, 'to_dict') else {'id': str(doc.id)}
                    for doc in self.documents
                ]
            else:
                result['documents'] = []
                
            # Handle results relationship
            if hasattr(self, 'results') and self.results:
                result['results'] = [
                    res.to_dict() if hasattr(res, 'to_dict') else {'id': str(res.id)}
                    for res in self.results
                ]
            else:
                result['results'] = []
        
        return result