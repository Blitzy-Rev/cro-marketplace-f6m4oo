"""
Defines Pydantic schemas for CRO submission data validation and serialization in the
Molecular Data Management and CRO Integration Platform. These schemas support the entire
submission workflow from creation to completion, including status transitions and document
requirements.
"""

from datetime import datetime
from typing import Any, Dict, List, Optional, Union

from pydantic import BaseModel, Field, validator, root_validator, UUID4, constr, confloat, conint

from ..constants.submission_status import (
    SubmissionStatus, 
    SubmissionAction as ActionEnum, 
    STATUS_TRANSITIONS,
    ACTIVE_STATUSES, 
    TERMINAL_STATUSES, 
    EDITABLE_STATUSES
)
from ..constants.document_types import DocumentType, REQUIRED_DOCUMENT_TYPES
from .molecule import Molecule
from .cro_service import CROService 
from .document import Document


def validate_status_transition(current_status: str, new_status: str) -> bool:
    """
    Validates that a status transition is allowed based on STATUS_TRANSITIONS.
    
    Args:
        current_status: The current status of the submission
        new_status: The new status to transition to
        
    Returns:
        True if the transition is valid, False otherwise
    """
    if current_status not in STATUS_TRANSITIONS:
        return False
    
    return new_status in STATUS_TRANSITIONS[current_status]


def get_required_documents(service_type: str) -> List[DocumentType]:
    """
    Returns the list of required document types for a given service type.
    
    Args:
        service_type: The type of service (from CROService.service_type)
        
    Returns:
        List of required document types
    """
    if service_type in REQUIRED_DOCUMENT_TYPES:
        return REQUIRED_DOCUMENT_TYPES[service_type]
    return []


class SubmissionBase(BaseModel):
    """Base Pydantic model for submission data with common fields."""
    
    name: constr(min_length=1, max_length=255) = Field(
        ..., description="Name of the submission"
    )
    cro_service_id: UUID4 = Field(
        ..., description="ID of the CRO service for this submission"
    )
    description: Optional[str] = Field(
        None, description="Detailed description of the submission"
    )
    specifications: Optional[Dict[str, Any]] = Field(
        None, description="Experiment specifications"
    )
    molecule_ids: Optional[List[UUID4]] = Field(
        None, description="List of molecule IDs included in this submission"
    )
    status: Optional[str] = Field(
        None, description="Current status of the submission"
    )
    metadata: Optional[Dict[str, Any]] = Field(
        None, description="Additional metadata for the submission"
    )
    
    @validator('name')
    def validate_name(cls, v):
        """Validates that the submission name meets requirements."""
        if not v or not v.strip():
            raise ValueError("Submission name cannot be empty")
        
        if len(v) > 255:
            raise ValueError("Submission name must be at most 255 characters")
        
        return v
    
    @validator('status')
    def validate_status(cls, v):
        """Validates that the status is a valid SubmissionStatus."""
        if v is None:
            return v
        
        try:
            # Try to convert to enum
            status_enum = SubmissionStatus(v)
            return v
        except ValueError:
            valid_statuses = [status.value for status in SubmissionStatus]
            raise ValueError(f"Invalid status. Must be one of: {', '.join(valid_statuses)}")


class SubmissionCreate(SubmissionBase):
    """Schema for creating a new submission."""
    
    created_by: UUID4 = Field(
        ..., description="ID of the user creating the submission"
    )
    
    class Config:
        schema_extra = {
            "example": {
                "name": "Binding Assay Submission Q3 2023",
                "cro_service_id": "3fa85f64-5717-4562-b3fc-2c963f66afa6",
                "created_by": "3fa85f64-5717-4562-b3fc-2c963f66afa6",
                "description": "Submission for binding assay of 5 candidate molecules",
                "specifications": {
                    "assay_type": "radioligand",
                    "target": "5-HT2A receptor",
                    "concentrations": [1, 10, 100]
                },
                "molecule_ids": [
                    "3fa85f64-5717-4562-b3fc-2c963f66afa6",
                    "4fa85f64-5717-4562-b3fc-2c963f66afa7"
                ]
            }
        }


class SubmissionUpdate(BaseModel):
    """Schema for updating an existing submission."""
    
    name: Optional[constr(min_length=1, max_length=255)] = Field(
        None, description="Name of the submission"
    )
    cro_service_id: Optional[UUID4] = Field(
        None, description="ID of the CRO service for this submission"
    )
    description: Optional[str] = Field(
        None, description="Detailed description of the submission"
    )
    specifications: Optional[Dict[str, Any]] = Field(
        None, description="Experiment specifications"
    )
    molecule_ids: Optional[List[UUID4]] = Field(
        None, description="List of molecule IDs included in this submission"
    )
    status: Optional[str] = Field(
        None, description="Current status of the submission"
    )
    metadata: Optional[Dict[str, Any]] = Field(
        None, description="Additional metadata for the submission"
    )
    
    @validator('name')
    def validate_name(cls, v):
        """Validates that the submission name meets requirements if provided."""
        if v is None:
            return v
            
        if not v or not v.strip():
            raise ValueError("Submission name cannot be empty")
        
        if len(v) > 255:
            raise ValueError("Submission name must be at most 255 characters")
        
        return v
    
    @validator('status')
    def validate_status(cls, v):
        """Validates that the status is a valid SubmissionStatus if provided."""
        if v is None:
            return v
        
        try:
            # Try to convert to enum
            status_enum = SubmissionStatus(v)
            return v
        except ValueError:
            valid_statuses = [status.value for status in SubmissionStatus]
            raise ValueError(f"Invalid status. Must be one of: {', '.join(valid_statuses)}")


class SubmissionInDB(SubmissionBase):
    """Schema for submission data from database including ID and timestamps."""
    
    id: UUID4 = Field(
        ..., description="Unique identifier for the submission"
    )
    created_by: UUID4 = Field(
        ..., description="ID of the user who created the submission"
    )
    created_at: datetime = Field(
        ..., description="Timestamp when the submission was created"
    )
    updated_at: datetime = Field(
        ..., description="Timestamp when the submission was last updated"
    )
    submitted_at: Optional[datetime] = Field(
        None, description="Timestamp when the submission was submitted to CRO"
    )
    approved_at: Optional[datetime] = Field(
        None, description="Timestamp when the submission was approved by pharma"
    )
    completed_at: Optional[datetime] = Field(
        None, description="Timestamp when the submission was completed"
    )
    price: Optional[confloat(gt=0)] = Field(
        None, description="Price provided by CRO for this submission"
    )
    price_currency: Optional[str] = Field(
        None, description="Currency code for the price"
    )
    estimated_turnaround_days: Optional[conint(gt=0)] = Field(
        None, description="Estimated number of days to complete the work"
    )
    
    class Config:
        orm_mode = True


class Submission(SubmissionInDB):
    """Schema for submission data returned to clients."""
    
    cro_service: Optional[Dict[str, Any]] = Field(
        None, description="CRO service details"
    )
    creator: Optional[Dict[str, Any]] = Field(
        None, description="User who created the submission"
    )
    molecules: Optional[List[Dict[str, Any]]] = Field(
        None, description="Molecules included in this submission"
    )
    documents: Optional[List[Dict[str, Any]]] = Field(
        None, description="Documents associated with this submission"
    )
    results: Optional[List[Dict[str, Any]]] = Field(
        None, description="Experimental results for this submission"
    )
    status_description: Optional[str] = Field(
        None, description="Human-readable description of the current status"
    )
    document_count: Optional[int] = Field(
        None, description="Count of associated documents"
    )
    molecule_count: Optional[int] = Field(
        None, description="Count of included molecules"
    )
    is_editable: Optional[bool] = Field(
        None, description="Whether the submission can be edited"
    )


class SubmissionFilter(BaseModel):
    """Schema for filtering submissions."""
    
    name_contains: Optional[str] = Field(
        None, description="Filter by name containing this substring"
    )
    created_by: Optional[UUID4] = Field(
        None, description="Filter by creator user ID"
    )
    cro_service_id: Optional[UUID4] = Field(
        None, description="Filter by CRO service ID"
    )
    status: Optional[List[str]] = Field(
        None, description="Filter by status (list of status values)"
    )
    active_only: Optional[bool] = Field(
        None, description="Filter to show only active submissions"
    )
    molecule_id: Optional[UUID4] = Field(
        None, description="Filter for submissions containing this molecule"
    )
    created_after: Optional[datetime] = Field(
        None, description="Filter for submissions created after this time"
    )
    created_before: Optional[datetime] = Field(
        None, description="Filter for submissions created before this time"
    )
    
    @validator('status')
    def validate_status(cls, v):
        """Validates that all statuses are valid SubmissionStatus values."""
        if v is None:
            return v
            
        valid_statuses = [status.value for status in SubmissionStatus]
        invalid_statuses = [status for status in v if status not in valid_statuses]
        
        if invalid_statuses:
            raise ValueError(
                f"Invalid statuses: {', '.join(invalid_statuses)}. "
                f"Must be one of: {', '.join(valid_statuses)}"
            )
        
        return v


class SubmissionAction(BaseModel):
    """Schema for performing actions on a submission."""
    
    action: ActionEnum = Field(
        ..., description="Action to perform on the submission"
    )
    data: Optional[Dict[str, Any]] = Field(
        None, description="Additional data for the action"
    )
    comment: Optional[str] = Field(
        None, description="Comment associated with the action"
    )
    
    @validator('action')
    def validate_action(cls, v):
        """Validates that the action is a valid SubmissionAction."""
        try:
            # Try to convert to enum
            action_enum = ActionEnum(v)
            return v
        except ValueError:
            valid_actions = [action.value for action in ActionEnum]
            raise ValueError(f"Invalid action. Must be one of: {', '.join(valid_actions)}")


class SubmissionWithDocumentRequirements(Submission):
    """Schema for submission with document requirements."""
    
    required_documents: List[Dict[str, Any]] = Field(
        ..., description="List of required document types for this submission"
    )
    optional_documents: List[Dict[str, Any]] = Field(
        ..., description="List of optional document types for this submission"
    )
    existing_documents: List[Dict[str, Any]] = Field(
        ..., description="List of documents already associated with this submission"
    )


class SubmissionStatusCount(BaseModel):
    """Schema for submission status counts."""
    
    status: str = Field(
        ..., description="Submission status"
    )
    count: int = Field(
        ..., description="Number of submissions in this status"
    )


class SubmissionPricingUpdate(BaseModel):
    """Schema for updating submission pricing by CRO."""
    
    price: confloat(gt=0) = Field(
        ..., description="Price for the submission"
    )
    price_currency: constr(min_length=3, max_length=3) = Field(
        ..., description="Currency code for the price (ISO 4217)"
    )
    estimated_turnaround_days: conint(gt=0) = Field(
        ..., description="Estimated number of days to complete the work"
    )
    comment: Optional[str] = Field(
        None, description="Comment regarding the pricing"
    )
    
    @validator('price')
    def validate_price(cls, v):
        """Validates that the price is positive."""
        if v <= 0:
            raise ValueError("Price must be greater than zero")
        return v
    
    @validator('price_currency')
    def validate_currency(cls, v):
        """Validates that the currency code is valid."""
        if len(v) != 3:
            raise ValueError("Currency code must be 3 characters (ISO 4217)")
        
        if not v.isupper():
            raise ValueError("Currency code must be uppercase (ISO 4217)")
        
        return v
    
    @validator('estimated_turnaround_days')
    def validate_turnaround_days(cls, v):
        """Validates that the turnaround days is positive."""
        if v <= 0:
            raise ValueError("Estimated turnaround days must be greater than zero")
        return v