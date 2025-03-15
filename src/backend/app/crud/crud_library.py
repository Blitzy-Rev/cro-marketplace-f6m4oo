from typing import List, Dict, Optional, Any, Union
import uuid
from datetime import datetime

from sqlalchemy.orm import Session
from sqlalchemy import select, func, or_, and_, desc, asc

from .base import CRUDBase
from ..models.library import Library
from ..models.molecule import Molecule, library_molecule
from ..models.user import User
from ..schemas.library import LibraryCreate, LibraryUpdate, LibraryFilter
from ..constants.user_roles import PHARMA_ROLES
from ..core.logging import get_logger
from ..db.session import db_session

logger = get_logger(__name__)


class CRUDLibrary(CRUDBase):
    """CRUD operations for library data with specialized methods for library management."""

    def create_with_owner(
        self,
        obj_in: LibraryCreate,
        owner_id: uuid.UUID,
        db: Optional[Session] = None
    ) -> Library:
        """
        Create a new library with owner information.
        
        Args:
            obj_in: Library creation data
            owner_id: UUID of the user who will own the library
            db: Optional database session (uses default if not provided)
            
        Returns:
            Created library instance
        """
        db_session_local = db or db_session
        
        # Convert obj_in to dictionary if it's a Pydantic model
        if not isinstance(obj_in, dict):
            obj_in_data = obj_in.model_dump()
        else:
            obj_in_data = obj_in
        
        # Set owner_id and timestamps
        obj_in_data["owner_id"] = owner_id
        obj_in_data["created_at"] = datetime.utcnow()
        obj_in_data["updated_at"] = datetime.utcnow()
        
        # Create the library using parent create method
        db_obj = super().create(obj_in_data, db=db_session_local)
        
        return db_obj

    def get_by_owner(
        self,
        owner_id: uuid.UUID,
        db: Optional[Session] = None,
        skip: int = 0,
        limit: int = 100
    ) -> Dict[str, Any]:
        """
        Get libraries owned by a specific user with pagination.
        
        Args:
            owner_id: UUID of the owner
            db: Optional database session (uses default if not provided)
            skip: Number of records to skip (for pagination)
            limit: Maximum number of records to return (for pagination)
            
        Returns:
            Dictionary with libraries and pagination info
        """
        db_session_local = db or db_session
        
        # Query libraries filtered by owner_id
        query = db_session_local.query(self.model).filter(self.model.owner_id == owner_id)
        
        # Get total count for pagination
        total = query.count()
        
        # Apply pagination
        items = query.offset(skip).limit(limit).all()
        
        # Return items with pagination metadata
        return {
            "items": items,
            "total": total,
            "page": skip // limit + 1 if limit > 0 else 1,
            "size": limit,
            "pages": (total + limit - 1) // limit if limit > 0 else 1
        }

    def get_by_organization(
        self,
        organization_id: uuid.UUID,
        db: Optional[Session] = None,
        skip: int = 0,
        limit: int = 100
    ) -> Dict[str, Any]:
        """
        Get libraries belonging to a specific organization with pagination.
        
        Args:
            organization_id: UUID of the organization
            db: Optional database session (uses default if not provided)
            skip: Number of records to skip (for pagination)
            limit: Maximum number of records to return (for pagination)
            
        Returns:
            Dictionary with libraries and pagination info
        """
        db_session_local = db or db_session
        
        # Query libraries filtered by organization_id
        query = db_session_local.query(self.model).filter(self.model.organization_id == organization_id)
        
        # Get total count for pagination
        total = query.count()
        
        # Apply pagination
        items = query.offset(skip).limit(limit).all()
        
        # Return items with pagination metadata
        return {
            "items": items,
            "total": total,
            "page": skip // limit + 1 if limit > 0 else 1,
            "size": limit,
            "pages": (total + limit - 1) // limit if limit > 0 else 1
        }

    def get_accessible_libraries(
        self,
        user: User,
        db: Optional[Session] = None,
        skip: int = 0,
        limit: int = 100
    ) -> Dict[str, Any]:
        """
        Get libraries accessible to a specific user with pagination.
        
        Args:
            user: User to check access for
            db: Optional database session (uses default if not provided)
            skip: Number of records to skip (for pagination)
            limit: Maximum number of records to return (for pagination)
            
        Returns:
            Dictionary with libraries and pagination info
        """
        db_session_local = db or db_session
        
        # If user is superuser, return all libraries
        if user.is_superuser:
            return self.get_multi(db=db_session_local, skip=skip, limit=limit)
        
        # Create query for user's libraries
        query = db_session_local.query(self.model).filter(
            or_(
                # Libraries owned by the user
                self.model.owner_id == user.id,
                # Libraries in the user's organization
                and_(
                    self.model.organization_id == user.organization_id,
                    user.organization_id != None,
                    self.model.organization_id != None
                ),
                # Public libraries
                self.model.is_public == True
            )
        )
        
        # Get total count for pagination
        total = query.count()
        
        # Apply pagination
        items = query.offset(skip).limit(limit).all()
        
        # Return items with pagination metadata
        return {
            "items": items,
            "total": total,
            "page": skip // limit + 1 if limit > 0 else 1,
            "size": limit,
            "pages": (total + limit - 1) // limit if limit > 0 else 1
        }

    def check_user_access(
        self,
        library_id: uuid.UUID,
        user: User,
        db: Optional[Session] = None
    ) -> bool:
        """
        Check if a user has access to a specific library.
        
        Args:
            library_id: UUID of the library to check
            user: User to check access for
            db: Optional database session (uses default if not provided)
            
        Returns:
            True if user has access, False otherwise
        """
        db_session_local = db or db_session
        
        # Get the library
        library = self.get(library_id, db=db_session_local)
        
        # If library not found, no access
        if not library:
            return False
        
        # Use the library's check_user_access method
        return library.check_user_access(user)

    def add_molecule(
        self,
        library_id: uuid.UUID,
        molecule_id: uuid.UUID,
        added_by: uuid.UUID,
        db: Optional[Session] = None
    ) -> bool:
        """
        Add a molecule to a library.
        
        Args:
            library_id: UUID of the library
            molecule_id: UUID of the molecule to add
            added_by: UUID of the user adding the molecule
            db: Optional database session (uses default if not provided)
            
        Returns:
            True if added, False if already in library or error
        """
        db_session_local = db or db_session
        
        # Get library and molecule
        library = self.get(library_id, db=db_session_local)
        molecule = db_session_local.query(Molecule).filter(Molecule.id == molecule_id).first()
        
        # If library or molecule not found, return False
        if not library or not molecule:
            return False
        
        # Use library's add_molecule method
        result = library.add_molecule(molecule, added_by)
        
        # Commit changes if successful
        if result:
            db_session_local.commit()
        
        return result

    def add_molecules(
        self,
        library_id: uuid.UUID,
        molecule_ids: List[uuid.UUID],
        added_by: uuid.UUID,
        db: Optional[Session] = None
    ) -> Dict[str, int]:
        """
        Add multiple molecules to a library.
        
        Args:
            library_id: UUID of the library
            molecule_ids: List of molecule UUIDs to add
            added_by: UUID of the user adding the molecules
            db: Optional database session (uses default if not provided)
            
        Returns:
            Dictionary with counts of added and skipped molecules
        """
        db_session_local = db or db_session
        
        # Get the library
        library = self.get(library_id, db=db_session_local)
        
        # If library not found, return error counts
        if not library:
            return {"added": 0, "skipped": 0}
        
        # Initialize counters
        added_count = 0
        skipped_count = 0
        
        # Process each molecule ID
        for molecule_id in molecule_ids:
            # Get the molecule
            molecule = db_session_local.query(Molecule).filter(Molecule.id == molecule_id).first()
            
            # If molecule found, try to add it
            if molecule:
                # Use library's add_molecule method
                if library.add_molecule(molecule, added_by):
                    added_count += 1
                else:
                    skipped_count += 1
            else:
                skipped_count += 1
        
        # Commit changes if any molecules were added
        if added_count > 0:
            db_session_local.commit()
        
        return {"added": added_count, "skipped": skipped_count}

    def remove_molecule(
        self,
        library_id: uuid.UUID,
        molecule_id: uuid.UUID,
        db: Optional[Session] = None
    ) -> bool:
        """
        Remove a molecule from a library.
        
        Args:
            library_id: UUID of the library
            molecule_id: UUID of the molecule to remove
            db: Optional database session (uses default if not provided)
            
        Returns:
            True if removed, False if not in library or error
        """
        db_session_local = db or db_session
        
        # Get library and molecule
        library = self.get(library_id, db=db_session_local)
        molecule = db_session_local.query(Molecule).filter(Molecule.id == molecule_id).first()
        
        # If library or molecule not found, return False
        if not library or not molecule:
            return False
        
        # Use library's remove_molecule method
        result = library.remove_molecule(molecule)
        
        # Commit changes if successful
        if result:
            db_session_local.commit()
        
        return result

    def remove_molecules(
        self,
        library_id: uuid.UUID,
        molecule_ids: List[uuid.UUID],
        db: Optional[Session] = None
    ) -> Dict[str, int]:
        """
        Remove multiple molecules from a library.
        
        Args:
            library_id: UUID of the library
            molecule_ids: List of molecule UUIDs to remove
            db: Optional database session (uses default if not provided)
            
        Returns:
            Dictionary with counts of removed and skipped molecules
        """
        db_session_local = db or db_session
        
        # Get the library
        library = self.get(library_id, db=db_session_local)
        
        # If library not found, return error counts
        if not library:
            return {"removed": 0, "skipped": 0}
        
        # Initialize counters
        removed_count = 0
        skipped_count = 0
        
        # Process each molecule ID
        for molecule_id in molecule_ids:
            # Get the molecule
            molecule = db_session_local.query(Molecule).filter(Molecule.id == molecule_id).first()
            
            # If molecule found, try to remove it
            if molecule:
                # Use library's remove_molecule method
                if library.remove_molecule(molecule):
                    removed_count += 1
                else:
                    skipped_count += 1
            else:
                skipped_count += 1
        
        # Commit changes if any molecules were removed
        if removed_count > 0:
            db_session_local.commit()
        
        return {"removed": removed_count, "skipped": skipped_count}

    def get_molecules(
        self,
        library_id: uuid.UUID,
        filter_params: Optional[Dict[str, Any]] = None,
        db: Optional[Session] = None,
        skip: int = 0,
        limit: int = 100,
        sort_by: Optional[str] = None,
        descending: bool = False
    ) -> Dict[str, Any]:
        """
        Get molecules in a library with pagination and filtering.
        
        Args:
            library_id: UUID of the library
            filter_params: Optional dictionary with filter parameters
            db: Optional database session (uses default if not provided)
            skip: Number of records to skip (for pagination)
            limit: Maximum number of records to return (for pagination)
            sort_by: Optional field to sort by
            descending: Whether to sort in descending order
            
        Returns:
            Dictionary with molecules and pagination info
        """
        db_session_local = db or db_session
        
        # Get the library
        library = self.get(library_id, db=db_session_local)
        
        # If library not found, return empty result
        if not library:
            return {
                "items": [],
                "total": 0,
                "page": 1,
                "size": limit,
                "pages": 0
            }
        
        # Query molecules in the library
        query = db_session_local.query(Molecule).join(
            library_molecule,
            Molecule.id == library_molecule.c.molecule_id
        ).filter(
            library_molecule.c.library_id == library_id
        )
        
        # Apply filters if provided
        if filter_params:
            filter_conditions = []
            
            # Process each filter parameter
            for key, value in filter_params.items():
                if hasattr(Molecule, key):
                    # Handle different filter types
                    if isinstance(value, list):
                        filter_conditions.append(getattr(Molecule, key).in_(value))
                    elif isinstance(value, dict):
                        for op, op_value in value.items():
                            if op == "gt":
                                filter_conditions.append(getattr(Molecule, key) > op_value)
                            elif op == "lt":
                                filter_conditions.append(getattr(Molecule, key) < op_value)
                            elif op == "gte":
                                filter_conditions.append(getattr(Molecule, key) >= op_value)
                            elif op == "lte":
                                filter_conditions.append(getattr(Molecule, key) <= op_value)
                            elif op == "eq":
                                filter_conditions.append(getattr(Molecule, key) == op_value)
                            elif op == "neq":
                                filter_conditions.append(getattr(Molecule, key) != op_value)
                            elif op == "like":
                                filter_conditions.append(getattr(Molecule, key).like(f"%{op_value}%"))
                    else:
                        # Simple equality
                        filter_conditions.append(getattr(Molecule, key) == value)
            
            # Apply all filters
            if filter_conditions:
                query = query.filter(and_(*filter_conditions))
        
        # Apply sorting if provided
        if sort_by and hasattr(Molecule, sort_by):
            if descending:
                query = query.order_by(desc(getattr(Molecule, sort_by)))
            else:
                query = query.order_by(asc(getattr(Molecule, sort_by)))
        
        # Get total count for pagination
        total = query.count()
        
        # Apply pagination
        items = query.offset(skip).limit(limit).all()
        
        # Return items with pagination metadata
        return {
            "items": items,
            "total": total,
            "page": skip // limit + 1 if limit > 0 else 1,
            "size": limit,
            "pages": (total + limit - 1) // limit if limit > 0 else 1
        }

    def filter_libraries(
        self,
        filter_params: LibraryFilter,
        user: Optional[User] = None,
        db: Optional[Session] = None,
        skip: int = 0,
        limit: int = 100,
        sort_by: Optional[str] = None,
        descending: bool = False
    ) -> Dict[str, Any]:
        """
        Filter libraries based on various criteria.
        
        Args:
            filter_params: Filter parameters
            user: Optional user for access control
            db: Optional database session (uses default if not provided)
            skip: Number of records to skip (for pagination)
            limit: Maximum number of records to return (for pagination)
            sort_by: Optional field to sort by
            descending: Whether to sort in descending order
            
        Returns:
            Dictionary with filtered libraries and pagination info
        """
        db_session_local = db or db_session
        
        # Start with a base query
        query = db_session_local.query(Library)
        
        # Apply user access restrictions if user provided
        if user and not user.is_superuser:
            query = query.filter(
                or_(
                    # Libraries owned by the user
                    Library.owner_id == user.id,
                    # Libraries in the user's organization
                    and_(
                        Library.organization_id == user.organization_id,
                        user.organization_id != None,
                        Library.organization_id != None
                    ),
                    # Public libraries
                    Library.is_public == True
                )
            )
        
        # Apply name filter if provided
        if filter_params.name_contains:
            query = query.filter(Library.name.ilike(f"%{filter_params.name_contains}%"))
        
        # Apply owner filter if provided
        if filter_params.owner_id:
            query = query.filter(Library.owner_id == filter_params.owner_id)
        
        # Apply organization filter if provided
        if filter_params.organization_id:
            query = query.filter(Library.organization_id == filter_params.organization_id)
        
        # Apply public/private filter if provided
        if filter_params.is_public is not None:
            query = query.filter(Library.is_public == filter_params.is_public)
        
        # Apply molecule filter if provided
        if filter_params.contains_molecule_id:
            query = query.join(
                library_molecule,
                Library.id == library_molecule.c.library_id
            ).filter(
                library_molecule.c.molecule_id == filter_params.contains_molecule_id
            )
        
        # Apply sorting if provided
        if sort_by and hasattr(Library, sort_by):
            if descending:
                query = query.order_by(desc(getattr(Library, sort_by)))
            else:
                query = query.order_by(asc(getattr(Library, sort_by)))
        
        # Get total count for pagination
        total = query.count()
        
        # Apply pagination
        items = query.offset(skip).limit(limit).all()
        
        # Return items with pagination metadata
        return {
            "items": items,
            "total": total,
            "page": skip // limit + 1 if limit > 0 else 1,
            "size": limit,
            "pages": (total + limit - 1) // limit if limit > 0 else 1
        }

    def get_with_molecule_count(
        self,
        library_id: uuid.UUID,
        db: Optional[Session] = None
    ) -> Optional[Dict[str, Any]]:
        """
        Get a library by ID with molecule count.
        
        Args:
            library_id: UUID of the library
            db: Optional database session (uses default if not provided)
            
        Returns:
            Library with molecule count if found, None otherwise
        """
        db_session_local = db or db_session
        
        # Get the library
        library = self.get(library_id, db=db_session_local)
        
        # If library not found, return None
        if not library:
            return None
        
        # Convert library to dictionary
        library_dict = library.to_dict()
        
        # Add molecule count
        library_dict["molecule_count"] = library.get_molecule_count()
        
        return library_dict


# Create singleton instance for application-wide use
library = CRUDLibrary(Library)