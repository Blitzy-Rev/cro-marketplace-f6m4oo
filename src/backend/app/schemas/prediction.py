from datetime import datetime
from typing import Optional, List, Dict, Any, Union

from pydantic import BaseModel, Field, validator, root_validator, UUID4  # pydantic version 2.0.0

from ..constants.molecule_properties import (
    PropertyType,
    PropertySource,
    PREDICTABLE_PROPERTIES,
    PROPERTY_UNITS
)
from ..models.prediction import PredictionStatus
from ..utils.validators import validate_property_value


class PredictionBase(BaseModel):
    """Base Pydantic model for prediction data with common fields"""
    molecule_id: UUID4
    property_name: str
    value: Union[str, int, float, bool]
    units: Optional[str] = None
    confidence: float
    model_name: str
    model_version: Optional[str] = None
    metadata: Optional[Dict[str, Any]] = None

    @validator('property_name')
    def validate_property_name(cls, v):
        """Validates that the property name is in the list of predictable properties"""
        if v not in PREDICTABLE_PROPERTIES:
            raise ValueError(f"Property '{v}' is not in the list of predictable properties")
        return v

    @validator('value')
    def validate_value(cls, v, values):
        """Validates property value based on property_type"""
        property_name = values.get('property_name')
        if not property_name:
            return v  # Skip validation if property_name is not available
        
        # Determine the property type based on the name and validate accordingly
        # We're using a simplified approach here as we don't have direct access to property types
        try:
            # For numeric properties (most predictable properties are numeric)
            if isinstance(v, (int, float)):
                validate_property_value(v, property_name, PropertyType.NUMERIC)
            elif isinstance(v, str):
                validate_property_value(v, property_name, PropertyType.STRING)
            elif isinstance(v, bool):
                validate_property_value(v, property_name, PropertyType.BOOLEAN)
        except Exception as e:
            raise ValueError(f"Invalid value for property {property_name}: {str(e)}")
        
        return v

    @validator('confidence')
    def validate_confidence(cls, v):
        """Validates that the confidence value is between 0 and 1"""
        if not 0 <= v <= 1:
            raise ValueError("Confidence score must be between 0 and 1")
        return v

    @root_validator(pre=True)
    def set_units(cls, values):
        """Sets units from PROPERTY_UNITS if not provided"""
        units = values.get('units')
        property_name = values.get('property_name')
        
        if units is None and property_name is not None:
            if property_name in PROPERTY_UNITS:
                values['units'] = PROPERTY_UNITS[property_name]
        
        return values


class PredictionCreate(PredictionBase):
    """Schema for creating a new prediction"""
    status: PredictionStatus = PredictionStatus.PENDING


class PredictionUpdate(BaseModel):
    """Schema for updating an existing prediction"""
    value: Optional[Union[str, int, float, bool]] = None
    confidence: Optional[float] = None
    status: Optional[PredictionStatus] = None
    error_message: Optional[str] = None
    metadata: Optional[Dict[str, Any]] = None

    @validator('confidence')
    def validate_confidence(cls, v):
        """Validates that the confidence value is between 0 and 1 if provided"""
        if v is not None and not 0 <= v <= 1:
            raise ValueError("Confidence score must be between 0 and 1")
        return v


class Prediction(PredictionBase):
    """Schema for prediction data with ID and timestamps"""
    id: UUID4
    created_at: datetime
    updated_at: Optional[datetime] = None
    status: PredictionStatus
    error_message: Optional[str] = None


class PredictionBatchBase(BaseModel):
    """Base schema for prediction batch operations"""
    molecule_ids: List[UUID4]
    properties: List[str]
    model_name: str
    model_version: Optional[str] = None
    options: Optional[Dict[str, Any]] = None

    @validator('molecule_ids')
    def validate_molecule_ids(cls, v):
        """Validates that the molecule_ids list is not empty"""
        if not v:
            raise ValueError("At least one molecule ID must be provided")
        return v

    @validator('properties')
    def validate_properties(cls, v):
        """Validates that all properties are in the list of predictable properties"""
        if not v:
            raise ValueError("At least one property must be specified")
        
        invalid_properties = [prop for prop in v if prop not in PREDICTABLE_PROPERTIES]
        if invalid_properties:
            raise ValueError(f"The following properties are not in the list of predictable properties: {', '.join(invalid_properties)}")
        
        return v


class PredictionBatchCreate(PredictionBatchBase):
    """Schema for creating a new prediction batch"""
    created_by: Optional[UUID4] = None
    external_job_id: Optional[str] = None


class PredictionBatchUpdate(BaseModel):
    """Schema for updating an existing prediction batch"""
    status: Optional[PredictionStatus] = None
    external_job_id: Optional[str] = None
    total_count: Optional[int] = None
    completed_count: Optional[int] = None
    failed_count: Optional[int] = None
    error_message: Optional[str] = None
    metadata: Optional[Dict[str, Any]] = None


class PredictionBatch(PredictionBatchBase):
    """Schema for prediction batch data with ID and timestamps"""
    id: UUID4
    status: PredictionStatus
    external_job_id: Optional[str] = None
    total_count: int
    completed_count: int
    failed_count: int
    error_message: Optional[str] = None
    metadata: Optional[Dict[str, Any]] = None
    created_by: Optional[UUID4] = None
    created_at: datetime
    updated_at: Optional[datetime] = None


class PredictionJobStatus(BaseModel):
    """Schema for prediction job status response"""
    batch_id: UUID4
    external_job_id: Optional[str] = None
    status: PredictionStatus
    total_count: int
    completed_count: int
    failed_count: int
    error_message: Optional[str] = None
    created_at: datetime
    updated_at: Optional[datetime] = None


class PredictionResponse(BaseModel):
    """Schema for prediction API response"""
    molecule_id: UUID4
    property_name: str
    value: Union[str, int, float, bool]
    units: Optional[str] = None
    confidence: float
    model_name: str
    model_version: Optional[str] = None
    status: PredictionStatus
    error_message: Optional[str] = None
    created_at: datetime


class PredictionFilter(BaseModel):
    """Schema for filtering predictions"""
    molecule_id: Optional[UUID4] = None
    property_names: Optional[List[str]] = None
    model_name: Optional[str] = None
    model_version: Optional[str] = None
    status: Optional[PredictionStatus] = None
    min_confidence: Optional[float] = None
    created_after: Optional[datetime] = None
    created_before: Optional[datetime] = None

    @validator('property_names')
    def validate_property_names(cls, v):
        """Validates that all property names are in the list of predictable properties"""
        if v is None:
            return v
            
        invalid_properties = [prop for prop in v if prop not in PREDICTABLE_PROPERTIES]
        if invalid_properties:
            raise ValueError(f"The following properties are not in the list of predictable properties: {', '.join(invalid_properties)}")
        
        return v

    @validator('min_confidence')
    def validate_min_confidence(cls, v):
        """Validates that min_confidence is between 0 and 1"""
        if v is not None and not 0 <= v <= 1:
            raise ValueError("Confidence threshold must be between 0 and 1")
        return v