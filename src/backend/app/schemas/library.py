"""
Defines Pydantic schemas for library data validation and serialization in the Molecular Data Management and CRO Integration Platform. These schemas are used for API request/response validation, data transformation, and documentation for library-related operations.
"""

from datetime import datetime
from typing import Any, Dict, List, Optional

from pydantic import BaseModel, Field, validator, UUID4

from .user import User
from .molecule import Molecule


class LibraryBase(BaseModel):
    """Base Pydantic model for library data with common fields."""
    
    name: str = Field(..., description="Name of the library")
    description: Optional[str] = Field(None, description="Description of the library and its contents")
    is_public: Optional[bool] = Field(None, description="Whether the library is publicly accessible")
    metadata: Optional[Dict[str, Any]] = Field(None, description="Additional metadata for the library")
    
    def __init__(self, **data):
        """Initialize LibraryBase model with default values."""
        # Set is_public to False by default if not provided
        if 'is_public' not in data:
            data['is_public'] = False
        super().__init__(**data)
    
    @validator('name')
    def validate_name(cls, v):
        """Validates that the library name is not empty and has an appropriate length."""
        if v is None or v.strip() == "":
            raise ValueError("Library name cannot be empty")
        
        if len(v) > 100:
            raise ValueError("Library name cannot exceed 100 characters")
        
        return v


class LibraryCreate(LibraryBase):
    """Schema for creating a new library."""
    
    owner_id: Optional[UUID4] = Field(None, description="ID of the user who owns the library")
    organization_id: Optional[UUID4] = Field(None, description="ID of the organization the library belongs to")
    
    def __init__(self, **data):
        """Initialize LibraryCreate model."""
        super().__init__(**data)


class LibraryUpdate(BaseModel):
    """Schema for updating an existing library."""
    
    name: Optional[str] = Field(None, description="Updated name of the library")
    description: Optional[str] = Field(None, description="Updated description of the library")
    is_public: Optional[bool] = Field(None, description="Updated public access setting")
    metadata: Optional[Dict[str, Any]] = Field(None, description="Updated metadata for the library")
    
    def __init__(self, **data):
        """Initialize LibraryUpdate model."""
        super().__init__(**data)
    
    @validator('name')
    def validate_name(cls, v):
        """Validates that the library name is not empty and has an appropriate length if provided."""
        if v is None:
            return None
        
        if v.strip() == "":
            raise ValueError("Library name cannot be empty")
        
        if len(v) > 100:
            raise ValueError("Library name cannot exceed 100 characters")
        
        return v


class Library(LibraryBase):
    """Schema for library data with ID and timestamps."""
    
    id: UUID4 = Field(..., description="Unique identifier for the library")
    owner_id: UUID4 = Field(..., description="ID of the user who owns the library")
    organization_id: Optional[UUID4] = Field(None, description="ID of the organization the library belongs to")
    created_at: datetime = Field(..., description="Timestamp when the library was created")
    updated_at: datetime = Field(..., description="Timestamp when the library was last updated")
    owner: Optional[Dict[str, Any]] = Field(None, description="Information about the library owner")
    molecule_count: Optional[int] = Field(None, description="Number of molecules in the library")
    
    def __init__(self, **data):
        """Initialize Library model."""
        super().__init__(**data)


class LibraryWithMolecules(Library):
    """Extended library schema with molecule list."""
    
    molecules: List[Dict[str, Any]] = Field(..., description="List of molecules in the library")
    
    def __init__(self, **data):
        """Initialize LibraryWithMolecules model."""
        super().__init__(**data)


class LibraryFilter(BaseModel):
    """Schema for filtering libraries."""
    
    name_contains: Optional[str] = Field(None, description="Filter libraries by partial name match")
    owner_id: Optional[UUID4] = Field(None, description="Filter libraries by owner ID")
    organization_id: Optional[UUID4] = Field(None, description="Filter libraries by organization ID")
    is_public: Optional[bool] = Field(None, description="Filter libraries by public access setting")
    contains_molecule_id: Optional[UUID4] = Field(None, description="Filter libraries containing a specific molecule")
    
    def __init__(self, **data):
        """Initialize LibraryFilter model."""
        super().__init__(**data)


class MoleculeAddRemove(BaseModel):
    """Schema for adding or removing molecules from a library."""
    
    library_id: UUID4 = Field(..., description="ID of the library to modify")
    molecule_ids: List[UUID4] = Field(..., description="List of molecule IDs to add or remove")
    operation: str = Field(..., description="Operation to perform ('add' or 'remove')")
    
    def __init__(self, **data):
        """Initialize MoleculeAddRemove model."""
        super().__init__(**data)
    
    @validator('operation')
    def validate_operation(cls, v):
        """Validates that the operation is either 'add' or 'remove'."""
        if v not in ['add', 'remove']:
            raise ValueError("Operation must be either 'add' or 'remove'")
        return v
    
    @validator('molecule_ids')
    def validate_molecule_ids(cls, v):
        """Validates that the molecule_ids list is not empty."""
        if not v:
            raise ValueError("At least one molecule ID must be provided")
        return v