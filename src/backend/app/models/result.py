from enum import Enum
from datetime import datetime
from uuid import uuid4

from sqlalchemy import Column, String, Text, Float, ForeignKey, Table, UUID, JSON, DateTime, Boolean
from sqlalchemy.orm import relationship, validates

from ..db.base_class import Base
from ..constants.submission_status import SubmissionStatus
from ..constants.molecule_properties import PropertySource
from ..constants.document_types import DocumentType


class ResultStatus(Enum):
    """Enumeration of possible result statuses in the workflow"""
    PENDING = "PENDING"
    PROCESSING = "PROCESSING"
    COMPLETED = "COMPLETED"
    FAILED = "FAILED"
    REJECTED = "REJECTED"


# Association table for result properties
result_property = Table(
    'result_property', 
    Base.metadata,
    Column('result_id', UUID, ForeignKey('result.id'), primary_key=True),
    Column('molecule_id', UUID, ForeignKey('molecule.id'), primary_key=True),
    Column('name', String(100), primary_key=True),
    Column('value', Float),
    Column('units', String(50)),
    Column('created_at', DateTime, default=datetime.utcnow)
)


class Result(Base):
    """SQLAlchemy model representing experimental results from a CRO submission"""
    
    # Primary columns
    id = Column(UUID, primary_key=True, default=uuid4)
    submission_id = Column(UUID, ForeignKey('submission.id'), nullable=False)
    uploaded_by = Column(UUID, ForeignKey('user.id'), nullable=False)
    status = Column(String(50), nullable=False, default=ResultStatus.PENDING.value)
    notes = Column(Text)
    metadata = Column(JSON)
    protocol_used = Column(String(255))
    quality_control_passed = Column(Boolean)
    
    # Timestamp columns
    uploaded_at = Column(DateTime)
    processed_at = Column(DateTime)
    reviewed_at = Column(DateTime)
    
    # Relationships
    submission = relationship("Submission", back_populates="results")
    uploader = relationship("User")
    # This creates a many-to-many relationship using the result_property table
    molecules = relationship("Molecule", secondary=result_property)
    # Documents related to this result (like result reports, QC documentation)
    documents = relationship("Document", 
                           primaryjoin="and_(Document.entity_id==Result.id, "
                                      "or_(Document.type=='" + DocumentType.RESULTS_REPORT.name + "', "
                                      "Document.type=='" + DocumentType.QUALITY_CONTROL.name + "'))")
    
    @validates('status')
    def validate_status(self, key, status):
        """Validates that the status is one of the allowed result statuses
        
        Args:
            key: The attribute being validated (status)
            status: The status value to validate
            
        Returns:
            str: Validated status
            
        Raises:
            ValueError: If status is not a valid ResultStatus value
        """
        try:
            ResultStatus(status)
        except ValueError:
            allowed_values = [s.value for s in ResultStatus]
            raise ValueError(f"Invalid status: {status}. Allowed values: {allowed_values}")
        return status
    
    @classmethod
    def create(cls, submission_id, uploaded_by, protocol_used=None, notes=None, metadata=None):
        """Creates a new result instance
        
        Args:
            submission_id: UUID of the submission this result belongs to
            uploaded_by: UUID of the user who uploaded the result
            protocol_used: Optional protocol information
            notes: Optional notes about the result
            metadata: Optional metadata as a dictionary
            
        Returns:
            Result: New result instance
        """
        result = cls(
            submission_id=submission_id,
            uploaded_by=uploaded_by,
            status=ResultStatus.PENDING.value,
            protocol_used=protocol_used,
            notes=notes,
            metadata=metadata or {},
            uploaded_at=datetime.utcnow()
        )
        return result
    
    def update_status(self, new_status):
        """Updates the result status
        
        Args:
            new_status: The new status to set (must be a valid ResultStatus value)
            
        Returns:
            bool: True if status was updated, False if invalid status
        """
        try:
            status_enum = ResultStatus(new_status)
            self.status = status_enum.value
            
            # Update timestamp fields based on new status
            now = datetime.utcnow()
            if status_enum == ResultStatus.PROCESSING:
                # No timestamp update for PROCESSING
                pass
            elif status_enum == ResultStatus.COMPLETED:
                self.processed_at = now
            
            self.updated_at = now
            return True
        except ValueError:
            return False
    
    def add_property(self, molecule_id, property_name, value, units=None):
        """Adds a property result for a molecule
        
        Note: This method requires session support from a service layer
        to execute the insert operation on the result_property table.
        
        Args:
            molecule_id: UUID of the molecule
            property_name: Name of the property
            value: Numeric value of the property
            units: Optional units for the property
            
        Returns:
            bool: True if property was added, False if already exists
        """
        # In practice, this would be implemented in a service layer with session access
        # with code similar to:
        # 
        # from sqlalchemy import select, insert
        # 
        # # Check if property already exists
        # exists_stmt = select(1).where(
        #     result_property.c.result_id == self.id,
        #     result_property.c.molecule_id == molecule_id,
        #     result_property.c.name == property_name
        # ).exists()
        # 
        # exists = session.query(exists_stmt).scalar()
        # if exists:
        #     return False
        # 
        # # Add the property
        # stmt = insert(result_property).values(
        #     result_id=self.id,
        #     molecule_id=molecule_id,
        #     name=property_name,
        #     value=value,
        #     units=units,
        #     created_at=datetime.utcnow()
        # )
        # session.execute(stmt)
        # self.updated_at = datetime.utcnow()
        # return True
        return True  # Simplified for model definition
    
    def get_property(self, molecule_id, property_name):
        """Gets a specific property value for a molecule
        
        Note: This method requires session support from a service layer
        to execute the select operation on the result_property table.
        
        Args:
            molecule_id: UUID of the molecule
            property_name: Name of the property
            
        Returns:
            float: Property value or None if not found
        """
        # In practice, this would be implemented in a service layer with session access
        # with code similar to:
        # 
        # from sqlalchemy import select
        # stmt = select(result_property.c.value).where(
        #     result_property.c.result_id == self.id,
        #     result_property.c.molecule_id == molecule_id,
        #     result_property.c.name == property_name
        # )
        # return session.execute(stmt).scalar_one_or_none()
        return None  # Simplified for model definition
    
    def get_molecule_properties(self, molecule_id):
        """Gets all properties for a specific molecule
        
        Note: This method requires session support from a service layer
        to execute the select operation on the result_property table.
        
        Args:
            molecule_id: UUID of the molecule
            
        Returns:
            dict: Dictionary of property names and values
        """
        # In practice, this would be implemented in a service layer with session access
        # with code similar to:
        # 
        # from sqlalchemy import select
        # stmt = select(
        #     result_property.c.name, 
        #     result_property.c.value,
        #     result_property.c.units
        # ).where(
        #     result_property.c.result_id == self.id,
        #     result_property.c.molecule_id == molecule_id
        # )
        # results = session.execute(stmt).fetchall()
        # return {row[0]: {'value': row[1], 'units': row[2]} for row in results}
        return {}  # Simplified for model definition
    
    def update_submission_status(self):
        """Updates the associated submission status based on result status
        
        Returns:
            bool: True if submission status was updated, False otherwise
        """
        if not self.submission:
            return False
        
        status = ResultStatus(self.status)
        if status == ResultStatus.COMPLETED:
            self.submission.status = SubmissionStatus.RESULTS_UPLOADED.value
            return True
        return False
    
    def apply_to_molecules(self):
        """Applies result properties to the associated molecules
        
        Note: This method requires session support from a service layer
        to access and update molecule properties.
        
        Returns:
            int: Number of molecules updated
        """
        if ResultStatus(self.status) != ResultStatus.COMPLETED:
            return 0
        
        # In practice, this would be implemented in a service layer with session access
        # with code similar to:
        # 
        # count = 0
        # for molecule in self.molecules:
        #     properties = self.get_molecule_properties(molecule.id)
        #     for name, details in properties.items():
        #         molecule.set_property(
        #             name,
        #             details['value'],
        #             PropertySource.EXPERIMENTAL.value,
        #             details['units']
        #         )
        #         count += 1
        # return count
        return 0  # Simplified for model definition
    
    def mark_as_processed(self, quality_control_passed):
        """Marks the result as processed
        
        Args:
            quality_control_passed: Boolean indicating if quality control checks passed
            
        Returns:
            bool: True if result was marked as processed, False otherwise
        """
        current_status = ResultStatus(self.status)
        if current_status not in [ResultStatus.PENDING, ResultStatus.PROCESSING]:
            return False
        
        self.quality_control_passed = quality_control_passed
        new_status = ResultStatus.COMPLETED if quality_control_passed else ResultStatus.FAILED
        self.status = new_status.value
        self.processed_at = datetime.utcnow()
        self.updated_at = datetime.utcnow()
        
        # Update submission status if needed
        if quality_control_passed:
            self.update_submission_status()
        
        return True
    
    def mark_as_reviewed(self):
        """Marks the result as reviewed
        
        Returns:
            bool: True if result was marked as reviewed, False otherwise
        """
        if ResultStatus(self.status) != ResultStatus.COMPLETED:
            return False
        
        self.reviewed_at = datetime.utcnow()
        self.updated_at = datetime.utcnow()
        
        # Update submission status
        if self.submission:
            self.submission.status = SubmissionStatus.RESULTS_REVIEWED.value
        
        # Apply result properties to molecules
        self.apply_to_molecules()
        
        return True
    
    def reject(self, rejection_reason):
        """Rejects the result
        
        Args:
            rejection_reason: Optional reason for rejection
            
        Returns:
            bool: True if result was rejected, False otherwise
        """
        if ResultStatus(self.status) == ResultStatus.REJECTED:
            return False
        
        self.status = ResultStatus.REJECTED.value
        if rejection_reason:
            if self.notes:
                self.notes += f"\n\nRejection reason: {rejection_reason}"
            else:
                self.notes = f"Rejection reason: {rejection_reason}"
        
        self.updated_at = datetime.utcnow()
        return True
    
    def to_dict(self, include_properties=False, include_relationships=False):
        """Converts result to dictionary representation
        
        Args:
            include_properties: Whether to include property data
            include_relationships: Whether to include related entities
            
        Returns:
            dict: Dictionary representation of result
        """
        result = super().to_dict()
        
        # Ensure metadata is a dictionary
        if result.get('metadata') and isinstance(result['metadata'], str):
            import json
            try:
                result['metadata'] = json.loads(result['metadata'])
            except json.JSONDecodeError:
                result['metadata'] = {}
        
        # Add properties if requested
        if include_properties:
            # In practice, this would retrieve properties from database
            # Simplified placeholder
            result['properties'] = {}
        
        # Add relationships if requested
        if include_relationships:
            if self.submission:
                result['submission'] = {
                    'id': str(self.submission.id),
                    'status': self.submission.status
                }
            
            result['molecules'] = [str(m.id) for m in self.molecules]
            
            if self.documents:
                result['documents'] = [
                    {
                        'id': str(doc.id),
                        'type': doc.type,
                        'name': doc.name
                    }
                    for doc in self.documents
                ]
        
        return result