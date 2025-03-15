"""
Pydantic schemas for molecule data validation and serialization.

This module defines the data models used for molecule-related operations in the
Molecular Data Management and CRO Integration Platform, including creation,
validation, filtering, and bulk operations.
"""

from datetime import datetime
from typing import Any, Dict, List, Optional, Union

from pydantic import BaseModel, Field, validator, root_validator, UUID4, constr

from ..constants.molecule_properties import (
    PropertyType, 
    PropertySource, 
    STANDARD_PROPERTIES,
    PROPERTY_RANGES
)
from ..utils.validators import validate_smiles_string, validate_property_value
from .property import MoleculePropertyBase, MoleculeProperty, MoleculePropertyCreate


class MoleculeBase(BaseModel):
    """Base Pydantic model for molecule data with common fields."""
    
    smiles: constr(min_length=1, max_length=1000) = Field(
        ..., 
        description="SMILES representation of the molecular structure"
    )
    inchi_key: Optional[str] = Field(
        None, 
        description="InChI Key for the molecule"
    )
    formula: Optional[str] = Field(
        None, 
        description="Molecular formula"
    )
    molecular_weight: Optional[float] = Field(
        None, 
        description="Molecular weight in g/mol"
    )
    metadata: Optional[Dict[str, Any]] = Field(
        None, 
        description="Additional metadata for the molecule"
    )
    status: Optional[str] = Field(
        None, 
        description="Current status of the molecule"
    )
    properties: Optional[List[MoleculePropertyCreate]] = Field(
        None, 
        description="List of molecular properties"
    )
    
    @validator('smiles')
    def validate_smiles(cls, v):
        """Validates that the SMILES string is chemically valid."""
        if not v or not isinstance(v, str):
            raise ValueError("SMILES string is required")
        
        if not validate_smiles_string(v, raise_exception=False):
            raise ValueError("Invalid SMILES string format or chemical structure")
        
        return v
    
    @validator('properties')
    def validate_properties(cls, v):
        """Validates that property values are appropriate for their types."""
        if v is None:
            return None
        
        for prop in v:
            if prop.name in STANDARD_PROPERTIES:
                property_type = STANDARD_PROPERTIES[prop.name]["property_type"]
                try:
                    validate_property_value(
                        prop.value, 
                        prop.name, 
                        property_type, 
                        raise_exception=True
                    )
                except Exception as e:
                    raise ValueError(f"Invalid value for property {prop.name}: {str(e)}")
        
        return v


class MoleculeCreate(MoleculeBase):
    """Schema for creating a new molecule."""
    
    created_by: Optional[UUID4] = Field(
        None, 
        description="User ID who created the molecule"
    )
    
    @root_validator(pre=False)
    def generate_derived_properties(cls, values):
        """Generates derived properties like inchi_key and formula from SMILES if not provided.
        
        Note: This validator only checks for missing values. The actual property
        generation is performed in the service layer using RDKit.
        """
        smiles = values.get('smiles')
        if not smiles:
            return values
        
        # In the actual implementation, the service layer would use RDKit to:
        # 1. Generate InChI Key if not provided
        # 2. Calculate molecular formula if not provided
        # 3. Calculate molecular weight if not provided
        # This validator just serves as a placeholder and documentation
        
        return values


class MoleculeUpdate(BaseModel):
    """Schema for updating an existing molecule."""
    
    smiles: Optional[str] = Field(
        None, 
        description="SMILES representation of the molecular structure"
    )
    status: Optional[str] = Field(
        None, 
        description="Current status of the molecule"
    )
    metadata: Optional[Dict[str, Any]] = Field(
        None, 
        description="Additional metadata for the molecule"
    )
    properties: Optional[List[MoleculePropertyCreate]] = Field(
        None, 
        description="List of molecular properties"
    )
    
    @validator('smiles')
    def validate_smiles(cls, v):
        """Validates that the SMILES string is chemically valid if provided."""
        if v is None:
            return None
        
        if not validate_smiles_string(v, raise_exception=False):
            raise ValueError("Invalid SMILES string format or chemical structure")
        
        return v
    
    @validator('properties')
    def validate_properties(cls, v):
        """Validates that property values are appropriate for their types if provided."""
        if v is None:
            return None
        
        for prop in v:
            if prop.name in STANDARD_PROPERTIES:
                property_type = STANDARD_PROPERTIES[prop.name]["property_type"]
                try:
                    validate_property_value(
                        prop.value, 
                        prop.name, 
                        property_type, 
                        raise_exception=True
                    )
                except Exception as e:
                    raise ValueError(f"Invalid value for property {prop.name}: {str(e)}")
        
        return v


class Molecule(MoleculeBase):
    """Schema for molecule data with ID and timestamps."""
    
    id: UUID4 = Field(
        ..., 
        description="Unique identifier for the molecule"
    )
    created_by: Optional[UUID4] = Field(
        None, 
        description="User ID who created the molecule"
    )
    created_at: datetime = Field(
        ..., 
        description="Timestamp when the molecule was created"
    )
    updated_at: datetime = Field(
        ..., 
        description="Timestamp when the molecule was last updated"
    )
    properties: Optional[List[MoleculeProperty]] = Field(
        None, 
        description="List of molecular properties with their values"
    )
    library_ids: Optional[List[UUID4]] = Field(
        None, 
        description="List of library IDs this molecule belongs to"
    )


class MoleculeDetail(Molecule):
    """Schema for detailed molecule data including properties and relationships."""
    
    predictions: Optional[List[Dict[str, Any]]] = Field(
        None, 
        description="AI-predicted properties"
    )
    results: Optional[List[Dict[str, Any]]] = Field(
        None, 
        description="Experimental results"
    )
    libraries: Optional[List[Dict[str, Any]]] = Field(
        None, 
        description="Libraries this molecule belongs to"
    )
    submissions: Optional[List[Dict[str, Any]]] = Field(
        None, 
        description="CRO submissions including this molecule"
    )


class MoleculeFilter(BaseModel):
    """Schema for filtering molecules."""
    
    smiles_contains: Optional[str] = Field(
        None, 
        description="Filter by SMILES containing this substring"
    )
    formula_contains: Optional[str] = Field(
        None, 
        description="Filter by formula containing this substring"
    )
    status: Optional[str] = Field(
        None, 
        description="Filter by molecule status"
    )
    created_by: Optional[UUID4] = Field(
        None, 
        description="Filter by creator user ID"
    )
    library_id: Optional[UUID4] = Field(
        None, 
        description="Filter by library ID"
    )
    property_ranges: Optional[Dict[str, Dict[str, float]]] = Field(
        None, 
        description="Filter by property value ranges, e.g. {'logp': {'min': 1.0, 'max': 5.0}}"
    )
    
    @validator('property_ranges')
    def validate_property_ranges(cls, v):
        """Validates that property ranges are valid."""
        if v is None:
            return None
        
        for prop_name, range_dict in v.items():
            min_value = range_dict.get('min')
            max_value = range_dict.get('max')
            
            if min_value is not None and max_value is not None:
                if min_value > max_value:
                    raise ValueError(f"Min value must be less than or equal to max value for property {prop_name}")
            
            # Check if the property exists in standard properties
            if prop_name not in STANDARD_PROPERTIES and not prop_name.startswith('custom_'):
                raise ValueError(f"Unknown property: {prop_name}")
            
            # Check if values are within allowed ranges for standard properties
            if prop_name in PROPERTY_RANGES:
                std_min = PROPERTY_RANGES[prop_name].get("min")
                std_max = PROPERTY_RANGES[prop_name].get("max")
                
                if min_value is not None and std_min is not None and min_value < std_min:
                    raise ValueError(f"Min value for {prop_name} cannot be less than {std_min}")
                
                if max_value is not None and std_max is not None and max_value > std_max:
                    raise ValueError(f"Max value for {prop_name} cannot be greater than {std_max}")
        
        return v


class MoleculeBulkOperation(BaseModel):
    """Schema for bulk operations on molecules."""
    
    molecule_ids: List[UUID4] = Field(
        ..., 
        description="List of molecule IDs to operate on"
    )
    operation: Optional[str] = Field(
        None, 
        description="Operation to perform (add_to_library, remove_from_library, update_status, etc.)"
    )
    parameters: Optional[Dict[str, Any]] = Field(
        None, 
        description="Operation-specific parameters"
    )
    
    @validator('molecule_ids')
    def validate_molecule_ids(cls, v):
        """Validates that the molecule_ids list is not empty."""
        if not v:
            raise ValueError("At least one molecule ID must be provided")
        
        return v
    
    @validator('operation')
    def validate_operation(cls, v):
        """Validates that the operation is supported."""
        if v is None:
            return None
        
        supported_operations = [
            "add_to_library", 
            "remove_from_library", 
            "update_status", 
            "delete", 
            "predict_properties"
        ]
        
        if v not in supported_operations:
            raise ValueError(f"Unsupported operation. Must be one of: {', '.join(supported_operations)}")
        
        return v


class MoleculeCSVMapping(BaseModel):
    """Schema for mapping CSV columns to molecule properties."""
    
    column_mapping: Dict[str, str] = Field(
        ..., 
        description="Mapping of CSV column names to property names"
    )
    has_header: Optional[bool] = Field(
        True, 
        description="Whether the CSV file has a header row"
    )
    delimiter: Optional[str] = Field(
        ",", 
        description="CSV delimiter character"
    )
    
    @validator('column_mapping')
    def validate_column_mapping(cls, v):
        """Validates that the column mapping includes required fields."""
        if 'smiles' not in v.values():
            raise ValueError("SMILES column mapping is required")
        
        # Check that mapped properties exist in standard properties or are custom properties
        for csv_col, prop_name in v.items():
            if prop_name != 'smiles' and prop_name not in STANDARD_PROPERTIES and not prop_name.startswith('custom_'):
                raise ValueError(f"Unknown property: {prop_name}")
        
        return v