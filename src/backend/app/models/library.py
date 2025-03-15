"""
Library Model Module

This module defines the Library model for the Molecular Data Management and CRO Integration Platform.
It represents user-defined collections of molecules with metadata, ownership, and organization capabilities.
It enables researchers to organize molecules into logical groups for analysis, collaboration, and CRO submissions.
"""

from sqlalchemy import Column, String, Text, Boolean, DateTime, ForeignKey, UUID
from sqlalchemy.orm import relationship, validates
from datetime import datetime

from ..db.base_class import Base
from .molecule import library_molecule
from ..constants.user_roles import PHARMA_ROLES


class Library(Base):
    """SQLAlchemy model representing a user-defined collection of molecules with metadata and ownership information."""
    
    # Basic library attributes
    name = Column(String(100), nullable=False)
    description = Column(Text)
    
    # Ownership and permissions
    owner_id = Column(UUID, ForeignKey('user.id'), nullable=False)
    organization_id = Column(UUID, ForeignKey('organization.id'))
    is_public = Column(Boolean, default=False)
    
    # Relationships
    owner = relationship("User", back_populates="libraries")
    molecules = relationship("Molecule", secondary=library_molecule, back_populates="libraries")
    
    @validates('name')
    def validate_name(self, key, name):
        """Validates that the library name is not empty and has an appropriate length."""
        if not name or not name.strip():
            raise ValueError("Library name cannot be empty")
        
        if len(name) > 100:
            raise ValueError("Library name cannot exceed 100 characters")
        
        return name.strip()
    
    def add_molecule(self, molecule, added_by):
        """
        Adds a molecule to the library.
        
        Args:
            molecule: The molecule to add
            added_by: User ID of the user adding the molecule
            
        Returns:
            True if molecule was added, False if already in library
        """
        # Check if molecule is already in the library
        if molecule in self.molecules:
            return False
        
        # Add molecule to the library
        self.molecules.append(molecule)
        
        # Update the library's updated_at timestamp
        self.updated_at = datetime.utcnow()
        
        return True
    
    def remove_molecule(self, molecule):
        """
        Removes a molecule from the library.
        
        Args:
            molecule: The molecule to remove
            
        Returns:
            True if molecule was removed, False if not in library
        """
        if molecule not in self.molecules:
            return False
        
        self.molecules.remove(molecule)
        self.updated_at = datetime.utcnow()
        
        return True
    
    def get_molecule_count(self):
        """Gets the count of molecules in the library."""
        return len(self.molecules)
    
    def check_user_access(self, user):
        """
        Checks if a user has access to this library.
        
        Args:
            user: The user to check access for
            
        Returns:
            True if user has access, False otherwise
        """
        # Public libraries are accessible to all
        if self.is_public:
            return True
        
        # No user means no access
        if user is None:
            return False
        
        # System admins have access to everything
        if user.role == "system_admin":
            return True
        
        # Library owner has access
        if user.id == self.owner_id:
            return True
        
        # Users in the same organization have access (if both user and library have organization)
        if self.organization_id and user.organization_id and user.organization_id == self.organization_id:
            return True
            
        # Users with pharma roles may have additional access controls
        if user.role in PHARMA_ROLES:
            # Could implement additional pharma-specific access rules here
            pass
        
        # Default: no access
        return False
    
    def to_dict(self, include_molecules=False):
        """
        Converts library to dictionary representation.
        
        Args:
            include_molecules: Whether to include the list of molecule IDs
            
        Returns:
            Dictionary representation of library
        """
        # Get basic attributes using Base.to_dict
        result = super().to_dict()
        
        # Add owner information if available
        if self.owner:
            result["owner"] = {
                "id": str(self.owner.id),
                "name": self.owner.name,
                "email": self.owner.email
            }
        
        # Add molecule IDs if requested
        if include_molecules:
            result["molecules"] = [str(m.id) for m in self.molecules]
        else:
            result["molecule_count"] = self.get_molecule_count()
        
        return result
    
    @classmethod
    def from_dict(cls, data, instance=None):
        """
        Creates or updates a Library instance from dictionary data.
        
        Args:
            cls: The class being instantiated
            data: Dictionary with library attributes
            instance: Optional existing library instance to update
            
        Returns:
            Library instance with data applied
        """
        if instance is None:
            instance = cls()
        
        # Update basic attributes that are safe to set directly
        for key in ["name", "description", "owner_id", "organization_id", "is_public"]:
            if key in data:
                setattr(instance, key, data[key])
        
        return instance