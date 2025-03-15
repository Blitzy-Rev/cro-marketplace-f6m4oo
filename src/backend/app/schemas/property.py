"""
Pydantic schemas for molecular property data validation and serialization.

This module defines the data models used for property-related operations in the
Molecular Data Management and CRO Integration Platform, including property creation,
validation, AI predictions, and filtering.
"""

from datetime import datetime
from typing import Any, Dict, Optional, Union

from pydantic import BaseModel, Field, validator, UUID4

from ..constants.molecule_properties import (
    PropertyType, 
    PropertySource, 
    PropertyCategory,
    PROPERTY_RANGES,
    STANDARD_PROPERTIES
)
from ..utils.validators import validate_property_value


class MoleculePropertyBase(BaseModel):
    """Base Pydantic model for molecular property data with common fields."""
    
    name: str = Field(
        ..., 
        description="Unique identifier for the property (lowercase, alphanumeric with underscores)"
    )
    display_name: Optional[str] = Field(
        None, 
        description="Human-readable name for display purposes"
    )
    property_type: PropertyType = Field(
        ..., 
        description="Data type of the property (string, numeric, integer, boolean)"
    )
    category: Optional[PropertyCategory] = Field(
        None, 
        description="Category of the property (physical, chemical, biological, etc.)"
    )
    units: Optional[str] = Field(
        None, 
        description="Units of measurement for the property value"
    )
    description: Optional[str] = Field(
        None, 
        description="Detailed description of the property and its significance"
    )
    value: Union[str, int, float, bool, None] = Field(
        None, 
        description="Value of the property, type must match property_type"
    )
    source: PropertySource = Field(
        ..., 
        description="Source of the property value (calculated, imported, predicted, experimental)"
    )
    confidence: Optional[float] = Field(
        None, 
        description="Confidence score for predicted values (0-1)",
        ge=0,
        le=1
    )
    metadata: Optional[Dict[str, Any]] = Field(
        None, 
        description="Additional metadata associated with the property"
    )
    
    @validator('name')
    def validate_name(cls, v):
        """Validates property name format."""
        if v is None or not v:
            raise ValueError("Property name cannot be empty")
        
        # Check format: lowercase, no spaces, alphanumeric with underscores
        if not all(c.isalnum() or c == '_' for c in v) or not v.islower():
            raise ValueError(
                "Property name must be lowercase, contain only alphanumeric characters and underscores"
            )
        
        return v
    
    @validator('value')
    def validate_value(cls, v, values):
        """Validates property value based on property_type."""
        if v is None:
            return None
        
        property_type = values.get('property_type')
        if property_type is None:
            return v
        
        # Type validation
        if property_type == PropertyType.STRING and not isinstance(v, str):
            raise ValueError(f"Value must be a string for property type {property_type}")
        elif property_type == PropertyType.NUMERIC and not isinstance(v, (int, float)):
            raise ValueError(f"Value must be a number for property type {property_type}")
        elif property_type == PropertyType.INTEGER and not isinstance(v, int):
            raise ValueError(f"Value must be an integer for property type {property_type}")
        elif property_type == PropertyType.BOOLEAN and not isinstance(v, bool):
            raise ValueError(f"Value must be a boolean for property type {property_type}")
        
        # Use the utility validator to check value constraints
        property_name = values.get('name')
        if property_name:
            validate_property_value(v, property_name, property_type, raise_exception=True)
        
        return v
    
    @validator('confidence')
    def validate_confidence(cls, v):
        """Validates confidence score is between 0 and 1."""
        if v is None:
            return None
        
        if not 0 <= v <= 1:
            raise ValueError("Confidence score must be between 0 and 1")
        
        return v


class MoleculePropertyCreate(MoleculePropertyBase):
    """Schema for creating a new molecular property."""
    
    @validator('display_name', pre=True, always=True)
    def set_display_name(cls, v, values):
        """Sets display_name from name if not provided."""
        if v is None and 'name' in values:
            # Convert name_like_this to Name Like This
            return ' '.join(word.capitalize() for word in values['name'].split('_'))
        return v
    
    @validator('units', pre=True, always=True)
    def set_standard_units(cls, v, values):
        """Sets units from standard units if not provided."""
        if v is None and 'name' in values:
            name = values['name']
            if name in STANDARD_PROPERTIES:
                return STANDARD_PROPERTIES[name].get('units', '')
        return v


class MoleculeProperty(MoleculePropertyBase):
    """Schema for molecular property with ID and timestamps."""
    
    id: UUID4 = Field(
        ..., 
        description="Unique identifier for the property"
    )
    molecule_id: Optional[UUID4] = Field(
        None, 
        description="ID of the molecule this property belongs to"
    )
    created_at: datetime = Field(
        ..., 
        description="Timestamp when the property was created"
    )
    updated_at: Optional[datetime] = Field(
        None, 
        description="Timestamp when the property was last updated"
    )


class MoleculePropertyUpdate(BaseModel):
    """Schema for updating an existing molecular property."""
    
    display_name: Optional[str] = Field(
        None, 
        description="Human-readable name for display purposes"
    )
    category: Optional[PropertyCategory] = Field(
        None, 
        description="Category of the property (physical, chemical, biological, etc.)"
    )
    units: Optional[str] = Field(
        None, 
        description="Units of measurement for the property value"
    )
    description: Optional[str] = Field(
        None, 
        description="Detailed description of the property and its significance"
    )
    value: Optional[Union[str, int, float, bool]] = Field(
        None, 
        description="Value of the property, type must match property_type"
    )
    source: Optional[PropertySource] = Field(
        None, 
        description="Source of the property value (calculated, imported, predicted, experimental)"
    )
    confidence: Optional[float] = Field(
        None, 
        description="Confidence score for predicted values (0-1)",
        ge=0,
        le=1
    )
    metadata: Optional[Dict[str, Any]] = Field(
        None, 
        description="Additional metadata associated with the property"
    )
    
    @validator('value')
    def validate_value(cls, v, values):
        """Validates property value if provided."""
        if v is None:
            return None
        
        # If we know the property_type (from context), we could validate here
        # Otherwise, we'll rely on the service layer to handle validation
        return v


class PropertyDefinition(BaseModel):
    """Schema for standard property definition."""
    
    name: str = Field(
        ..., 
        description="Unique identifier for the property"
    )
    display_name: str = Field(
        ..., 
        description="Human-readable name for display purposes"
    )
    property_type: PropertyType = Field(
        ..., 
        description="Data type of the property (string, numeric, integer, boolean)"
    )
    category: PropertyCategory = Field(
        ..., 
        description="Category of the property (physical, chemical, biological, etc.)"
    )
    units: Optional[str] = Field(
        None, 
        description="Units of measurement for the property value"
    )
    description: Optional[str] = Field(
        None, 
        description="Detailed description of the property and its significance"
    )
    min_value: Optional[float] = Field(
        None, 
        description="Minimum allowed value for the property"
    )
    max_value: Optional[float] = Field(
        None, 
        description="Maximum allowed value for the property"
    )
    is_required: bool = Field(
        ..., 
        description="Whether the property is required for all molecules"
    )
    is_filterable: bool = Field(
        ..., 
        description="Whether the property can be used for filtering molecules"
    )
    is_predictable: bool = Field(
        ..., 
        description="Whether the property can be predicted by AI"
    )
    
    @validator('max_value')
    def validate_range(cls, values):
        """Validates that min_value is less than max_value if both are set."""
        min_value = values.get('min_value')
        max_value = values.get('max_value')
        
        if min_value is not None and max_value is not None:
            if min_value >= max_value:
                raise ValueError("min_value must be less than max_value")
        
        return values
    
    @classmethod
    def from_standard_properties(cls):
        """Creates PropertyDefinition instances from STANDARD_PROPERTIES."""
        definitions = []
        for name, props in STANDARD_PROPERTIES.items():
            property_def = cls(
                name=name,
                display_name=props['display_name'],
                property_type=props['property_type'],
                category=props['category'],
                units=props.get('units'),
                description=props.get('description'),
                is_required=props.get('is_required', False),
                is_filterable=props.get('is_filterable', False),
                is_predictable=props.get('is_predictable', False)
            )
            
            # Set range values if available
            if name in PROPERTY_RANGES:
                ranges = PROPERTY_RANGES[name]
                property_def.min_value = ranges.get('min')
                property_def.max_value = ranges.get('max')
            
            definitions.append(property_def)
        
        return definitions


class PropertyPrediction(BaseModel):
    """Schema for AI-predicted property with confidence score."""
    
    name: str = Field(
        ..., 
        description="Name of the predicted property"
    )
    value: Union[str, int, float, bool] = Field(
        ..., 
        description="Predicted property value"
    )
    confidence: float = Field(
        ..., 
        description="Confidence score for the prediction (0-1)",
        ge=0,
        le=1
    )
    model_version: Optional[str] = Field(
        None, 
        description="Version of the AI model used for prediction"
    )
    prediction_time: Optional[datetime] = Field(
        None, 
        description="Timestamp when the prediction was made"
    )
    metadata: Optional[Dict[str, Any]] = Field(
        None, 
        description="Additional metadata about the prediction"
    )
    
    @validator('confidence')
    def validate_confidence(cls, v):
        """Validates confidence score is between 0 and 1."""
        if not 0 <= v <= 1:
            raise ValueError("Confidence score must be between 0 and 1")
        return v


class PropertyFilter(BaseModel):
    """Schema for filtering properties."""
    
    name: Optional[str] = Field(
        None, 
        description="Filter by property name"
    )
    property_type: Optional[PropertyType] = Field(
        None, 
        description="Filter by property type"
    )
    category: Optional[PropertyCategory] = Field(
        None, 
        description="Filter by property category"
    )
    source: Optional[PropertySource] = Field(
        None, 
        description="Filter by property source"
    )
    is_required: Optional[bool] = Field(
        None, 
        description="Filter by required status"
    )
    is_filterable: Optional[bool] = Field(
        None, 
        description="Filter by filterable status"
    )
    is_predictable: Optional[bool] = Field(
        None, 
        description="Filter by predictable status"
    )