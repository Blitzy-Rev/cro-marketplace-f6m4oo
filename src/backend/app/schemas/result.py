from datetime import datetime
from typing import Any, Dict, List, Optional, Union

from pydantic import BaseModel, Field, UUID4, validator, root_validator

from ..models.result import ResultStatus
from ..constants.molecule_properties import PropertySource, PROPERTY_UNITS, PROPERTY_RANGES
from ..utils.validators import validate_property_value


class ResultPropertyBase(BaseModel):
    """Base Pydantic model for result property data with common fields"""
    molecule_id: UUID4
    name: str
    value: float
    units: Optional[str] = None

    @root_validator(pre=False)
    def validate_property(cls, values):
        """Validates that the property value is within valid ranges"""
        name = values.get('name')
        value = values.get('value')
        
        # Validate property value if name is a known property
        if name in PROPERTY_RANGES and value is not None:
            prop_range = PROPERTY_RANGES[name]
            if "min" in prop_range and value < prop_range["min"]:
                raise ValueError(f"Value {value} is below minimum {prop_range['min']} for property {name}")
            if "max" in prop_range and value > prop_range["max"]:
                raise ValueError(f"Value {value} is above maximum {prop_range['max']} for property {name}")
        
        # Set default units if available and not provided
        if values.get('units') is None and name in PROPERTY_UNITS:
            values['units'] = PROPERTY_UNITS[name]
            
        return values


class ResultPropertyCreate(ResultPropertyBase):
    """Schema for creating a new result property"""
    
    class Config:
        schema_extra = {
            "example": {
                "molecule_id": "3fa85f64-5717-4562-b3fc-2c963f66afa6",
                "name": "binding_affinity",
                "value": 4.5,
                "units": "nM"
            }
        }


class ResultProperty(ResultPropertyBase):
    """Schema for result property with result_id"""
    result_id: UUID4


class ResultBase(BaseModel):
    """Base Pydantic model for result data with common fields"""
    submission_id: UUID4
    protocol_used: Optional[str] = None
    notes: Optional[str] = None
    metadata: Optional[Dict[str, Any]] = None
    status: Optional[str] = ResultStatus.PENDING.value
    quality_control_passed: Optional[bool] = None
    properties: Optional[List[ResultPropertyCreate]] = None
    
    @validator('status')
    def validate_status(cls, v):
        """Validates that the status is a valid ResultStatus"""
        if v is None:
            return None
            
        try:
            ResultStatus(v)
        except ValueError:
            allowed_values = [status.value for status in ResultStatus]
            raise ValueError(f"Invalid status: {v}. Allowed values: {allowed_values}")
        return v
        
    @validator('properties')
    def validate_properties(cls, v):
        """Validates that properties have unique molecule_id and name combinations"""
        if v is None:
            return None
            
        # Check for duplicate molecule_id/name combinations
        seen = set()
        duplicates = []
        
        for prop in v:
            key = (str(prop.molecule_id), prop.name)
            if key in seen:
                duplicates.append(key)
            seen.add(key)
            
        if duplicates:
            raise ValueError(f"Duplicate molecule_id/name combinations: {duplicates}")
            
        return v


class ResultCreate(ResultBase):
    """Schema for creating a new result"""
    uploaded_by: UUID4
    
    class Config:
        schema_extra = {
            "example": {
                "submission_id": "3fa85f64-5717-4562-b3fc-2c963f66afa6",
                "uploaded_by": "3fa85f64-5717-4562-b3fc-2c963f66afa6",
                "protocol_used": "Standard Protocol A",
                "notes": "Results from binding assay experiment",
                "metadata": {
                    "temperature": 25,
                    "ph": 7.4,
                    "incubation_time": "2h"
                },
                "quality_control_passed": True,
                "properties": [
                    {
                        "molecule_id": "3fa85f64-5717-4562-b3fc-2c963f66afa6",
                        "name": "binding_affinity",
                        "value": 4.5,
                        "units": "nM"
                    }
                ]
            }
        }


class ResultUpdate(BaseModel):
    """Schema for updating an existing result"""
    protocol_used: Optional[str] = None
    notes: Optional[str] = None
    metadata: Optional[Dict[str, Any]] = None
    status: Optional[str] = None
    quality_control_passed: Optional[bool] = None
    properties: Optional[List[ResultPropertyCreate]] = None
    
    @validator('status')
    def validate_status(cls, v):
        """Validates that the status is a valid ResultStatus if provided"""
        if v is None:
            return None
            
        try:
            ResultStatus(v)
        except ValueError:
            allowed_values = [status.value for status in ResultStatus]
            raise ValueError(f"Invalid status: {v}. Allowed values: {allowed_values}")
        return v
        
    @validator('properties')
    def validate_properties(cls, v):
        """Validates that properties have unique molecule_id and name combinations if provided"""
        if v is None:
            return None
            
        # Check for duplicate molecule_id/name combinations
        seen = set()
        duplicates = []
        
        for prop in v:
            key = (str(prop.molecule_id), prop.name)
            if key in seen:
                duplicates.append(key)
            seen.add(key)
            
        if duplicates:
            raise ValueError(f"Duplicate molecule_id/name combinations: {duplicates}")
            
        return v


class Result(BaseModel):
    """Schema for result data with ID and timestamps"""
    id: UUID4
    submission_id: UUID4
    uploaded_by: UUID4
    uploaded_at: datetime
    processed_at: Optional[datetime] = None
    reviewed_at: Optional[datetime] = None
    created_at: datetime
    updated_at: datetime
    protocol_used: Optional[str] = None
    notes: Optional[str] = None
    metadata: Optional[Dict[str, Any]] = None
    status: Optional[str] = ResultStatus.PENDING.value
    quality_control_passed: Optional[bool] = None
    submission: Optional[Dict[str, Any]] = None
    uploader: Optional[Dict[str, Any]] = None
    properties: Optional[List[ResultProperty]] = None
    molecules: Optional[List[Dict[str, Any]]] = None
    documents: Optional[List[Dict[str, Any]]] = None
    property_count: Optional[int] = None
    molecule_count: Optional[int] = None
    status_description: Optional[str] = None
    
    class Config:
        orm_mode = True


class ResultFilter(BaseModel):
    """Schema for filtering results"""
    submission_id: Optional[UUID4] = None
    uploaded_by: Optional[UUID4] = None
    status: Optional[List[str]] = None
    quality_control_passed: Optional[bool] = None
    molecule_id: Optional[UUID4] = None
    uploaded_after: Optional[datetime] = None
    uploaded_before: Optional[datetime] = None
    
    @validator('status')
    def validate_status(cls, v):
        """Validates that all statuses are valid ResultStatus values"""
        if v is None:
            return None
            
        invalid_statuses = []
        allowed_values = [status.value for status in ResultStatus]
        
        for status in v:
            if status not in allowed_values:
                invalid_statuses.append(status)
                
        if invalid_statuses:
            raise ValueError(f"Invalid statuses: {invalid_statuses}. Allowed values: {allowed_values}")
            
        return v


class ResultCSVMapping(BaseModel):
    """Schema for mapping CSV columns to result properties"""
    column_mapping: Dict[str, str]
    has_header: Optional[bool] = True
    delimiter: Optional[str] = ","
    
    @validator('column_mapping')
    def validate_column_mapping(cls, v):
        """Validates that the column mapping includes required fields"""
        if 'molecule_id' not in v.values():
            raise ValueError("Column mapping must include a column mapped to 'molecule_id'")
            
        # Ensure at least one property column is mapped
        property_columns = [col for col in v.values() if col != 'molecule_id']
        if not property_columns:
            raise ValueError("Column mapping must include at least one property column")
            
        return v


class ResultProcessRequest(BaseModel):
    """Schema for requesting result processing"""
    result_id: UUID4
    quality_control_passed: bool
    notes: Optional[str] = None


class ResultReviewRequest(BaseModel):
    """Schema for requesting result review"""
    result_id: UUID4
    notes: Optional[str] = None