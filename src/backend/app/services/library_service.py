# src/backend/app/services/library_service.py
"""
Service layer implementation for library-related operations in the Molecular Data Management and CRO Integration Platform.
This service provides high-level business logic for library management, including creation, organization, molecule association, and access control.
"""

import typing
from typing import List, Dict, Optional, Any, Union
import uuid

from sqlalchemy.orm import Session

from ..models.library import Library
from ..models.molecule import Molecule
from ..crud import crud_library
from ..utils.csv_parser import CSVProcessor, process_csv_in_chunks
from ..utils.smiles import validate_smiles
from ..integrations.ai_engine.client import AIEngineClient  # version: check in ai_engine/client.py
from ..integrations.ai_engine.models import PredictionRequest, BatchPredictionRequest  # version: check in ai_engine/models.py
from ..constants.molecule_properties import PropertySource, PREDICTABLE_PROPERTIES
from ..schemas import library
from ..schemas.library import LibraryCreate, LibraryUpdate, LibraryFilter
from ..db.session import get_db
from ..core.exceptions import LibraryException, NotFoundException, AuthorizationException
from ..core.logging import get_logger
from ..constants.error_messages import LIBRARY_ERRORS

# Initialize logger
logger = get_logger(__name__)

class LibraryService:
    """Service class for library-related operations with business logic"""

    def __init__(self, ai_client: Optional[AIEngineClient] = None):
        """Initialize the library service

        Args:
            ai_client: Optional AI engine client for property predictions
        """
        self._ai_client = ai_client or AIEngineClient()
        logger.info("LibraryService initialized")

    def create_library(
        self,
        library_data: Union[LibraryCreate, Dict[str, Any]],
        owner_id: uuid.UUID,
        organization_id: Optional[uuid.UUID] = None,
        db: Optional[Session] = None
    ) -> Dict[str, Any]:
        """Create a new library with owner information

        Args:
            library_data: Library creation data
            owner_id: UUID of the user who will own the library
            organization_id: Optional organization ID for the library
            db: Optional database session

        Returns:
            Created library data as dictionary
        """
        db_session = db or get_db()

        # Convert library_data to dictionary if it's a Pydantic model
        if isinstance(library_data, library.LibraryCreate):
            library_data = library_data.model_dump()
        
        # Set organization_id in library_data if provided
        if organization_id:
            library_data["organization_id"] = organization_id

        # Create library using library.create_with_owner
        library_obj = crud_library.library.create_with_owner(obj_in=library_data, owner_id=owner_id, db=db_session)

        logger.info(f"Created library with ID: {library_obj.id}, name: {library_obj.name}, owner: {owner_id}")
        return library_obj.to_dict()

    def get_library(self, library_id: uuid.UUID, db: Optional[Session] = None) -> Dict[str, Any]:
        """Get a library by ID with molecule count

        Args:
            library_id: UUID of the library
            db: Optional database session

        Returns:
            Library data with molecule count
        """
        db_session = db or get_db()

        # Get library with molecule count using library.get_with_molecule_count
        library_data = crud_library.library.get_with_molecule_count(library_id=library_id, db=db_session)

        # If library not found, raise NotFoundException
        if not library_data:
            logger.warning(f"Library not found: {library_id}")
            raise NotFoundException(message=LIBRARY_ERRORS["LIBRARY_NOT_FOUND"], library_id=str(library_id))

        return library_data

    def update_library(
        self,
        library_id: uuid.UUID,
        library_data: Union[LibraryUpdate, Dict[str, Any]],
        db: Optional[Session] = None
    ) -> Dict[str, Any]:
        """Update an existing library

        Args:
            library_id: UUID of the library to update
            library_data: Library update data
            db: Optional database session

        Returns:
            Updated library data
        """
        db_session = db or get_db()

        # Get library by ID
        library_obj = crud_library.library.get(library_id, db=db_session)

        # If library not found, raise NotFoundException
        if not library_obj:
            logger.warning(f"Library not found: {library_id}")
            raise NotFoundException(message=LIBRARY_ERRORS["LIBRARY_NOT_FOUND"], library_id=str(library_id))

        # Convert library_data to dictionary if it's a Pydantic model
        if isinstance(library_data, library.LibraryUpdate):
            library_data = library_data.model_dump()

        # Update library with new data
        library_obj = crud_library.library.update(db_obj=library_obj, obj_in=library_data, db=db_session)

        logger.info(f"Updated library with ID: {library_id}")
        return library_obj.to_dict()

    def delete_library(self, library_id: uuid.UUID, db: Optional[Session] = None) -> bool:
        """Delete a library by ID

        Args:
            library_id: UUID of the library to delete
            db: Optional database session

        Returns:
            True if deleted successfully
        """
        db_session = db or get_db()

        # Get library by ID
        library_obj = crud_library.library.get(library_id, db=db_session)

        # If library not found, raise NotFoundException
        if not library_obj:
            logger.warning(f"Library not found: {library_id}")
            raise NotFoundException(message=LIBRARY_ERRORS["LIBRARY_NOT_FOUND"], library_id=str(library_id))

        # Delete library
        crud_library.library.remove(id=library_id, db=db_session)

        logger.info(f"Deleted library with ID: {library_id}")
        return True

    def get_libraries_by_owner(
        self,
        owner_id: uuid.UUID,
        skip: int = 0,
        limit: int = 100,
        db: Optional[Session] = None
    ) -> Dict[str, Any]:
        """Get libraries owned by a specific user with pagination

        Args:
            owner_id: UUID of the owner
            skip: Number of records to skip
            limit: Maximum number of records to return
            db: Optional database session

        Returns:
            Libraries with pagination info
        """
        db_session = db or get_db()

        # Get libraries by owner with pagination
        libraries = crud_library.library.get_by_owner(owner_id=owner_id, db=db_session, skip=skip, limit=limit)

        return libraries

    def get_libraries_by_organization(
        self,
        organization_id: uuid.UUID,
        skip: int = 0,
        limit: int = 100,
        db: Optional[Session] = None
    ) -> Dict[str, Any]:
        """Get libraries belonging to a specific organization with pagination

        Args:
            organization_id: UUID of the organization
            skip: Number of records to skip
            limit: Maximum number of records to return
            db: Optional database session

        Returns:
            Libraries with pagination info
        """
        db_session = db or get_db()

        # Get libraries by organization with pagination
        libraries = crud_library.library.get_by_organization(organization_id=organization_id, db=db_session, skip=skip, limit=limit)

        return libraries

    def get_accessible_libraries(
        self,
        user: Dict[str, Any],
        skip: int = 0,
        limit: int = 100,
        db: Optional[Session] = None
    ) -> Dict[str, Any]:
        """Get libraries accessible to a specific user with pagination

        Args:
            user: User to check access for
            skip: Number of records to skip
            limit: Maximum number of records to return
            db: Optional database session

        Returns:
            Libraries with pagination info
        """
        db_session = db or get_db()

        # Get accessible libraries for user with pagination
        libraries = crud_library.library.get_accessible_libraries(user=user, db=db_session, skip=skip, limit=limit)

        return libraries

    def filter_libraries(
        self,
        filter_params: Union[LibraryFilter, Dict[str, Any]],
        user: Optional[Dict[str, Any]] = None,
        skip: int = 0,
        limit: int = 100,
        sort_by: Optional[str] = None,
        descending: bool = False,
        db: Optional[Session] = None
    ) -> Dict[str, Any]:
        """Filter libraries based on various criteria

        Args:
            filter_params: Filter parameters
            user: Optional user for access control
            skip: Number of records to skip
            limit: Maximum number of records to return
            sort_by: Field to sort by
            descending: Whether to sort in descending order
            db: Optional database session

        Returns:
            Filtered libraries with pagination info
        """
        db_session = db or get_db()

        # Convert filter_params to dictionary if it's a Pydantic model
        if isinstance(filter_params, library.LibraryFilter):
            filter_params = filter_params.model_dump()

        # Filter libraries based on criteria
        libraries = crud_library.library.filter_libraries(filter_params=filter_params, user=user, db=db_session, skip=skip, limit=limit, sort_by=sort_by, descending=descending)

        return libraries

    def check_library_access(self, library_id: uuid.UUID, user: Dict[str, Any], db: Optional[Session] = None) -> bool:
        """Check if a user has access to a specific library

        Args:
            library_id: UUID of the library to check
            user: User to check access for
            db: Optional database session

        Returns:
            True if user has access, False otherwise
        """
        db_session = db or get_db()

        # Check user access to library
        has_access = crud_library.library.check_user_access(library_id=library_id, user=user, db=db_session)

        return has_access

    def add_molecule_to_library(
        self,
        library_id: uuid.UUID,
        molecule_id: uuid.UUID,
        added_by: uuid.UUID,
        db: Optional[Session] = None
    ) -> bool:
        """Add a molecule to a library

        Args:
            library_id: UUID of the library
            molecule_id: UUID of the molecule to add
            added_by: UUID of the user adding the molecule
            db: Optional database session

        Returns:
            True if added, False if already in library
        """
        db_session = db or get_db()

        # Check if user has access to library
        user = crud_library.library.get(library_id, db=db_session).owner
        if not crud_library.library.check_user_access(library_id=library_id, user=user, db=db_session):
            raise AuthorizationException(message=LIBRARY_ERRORS["INSUFFICIENT_LIBRARY_PERMISSIONS"], library_id=str(library_id))

        # Add molecule to library using molecule_service.add_to_library
        result = crud_library.library.add_molecule(library_id=library_id, molecule_id=molecule_id, added_by=added_by, db=db_session)

        logger.info(f"Added molecule {molecule_id} to library {library_id} by user {added_by}")
        return result

    def add_molecules_to_library(
        self,
        library_id: uuid.UUID,
        molecule_ids: List[uuid.UUID],
        added_by: uuid.UUID,
        db: Optional[Session] = None
    ) -> Dict[str, int]:
        """Add multiple molecules to a library

        Args:
            library_id: UUID of the library
            molecule_ids: List of molecule UUIDs to add
            added_by: UUID of the user adding the molecules
            db: Optional database session

        Returns:
            Dictionary with counts of added and skipped molecules
        """
        db_session = db or get_db()

        # Check if user has access to library
        user = crud_library.library.get(library_id, db=db_session).owner
        if not crud_library.library.check_user_access(library_id=library_id, user=user, db=db_session):
            raise AuthorizationException(message=LIBRARY_ERRORS["INSUFFICIENT_LIBRARY_PERMISSIONS"], library_id=str(library_id))

        # Add molecules to library using library.add_molecules
        results = crud_library.library.add_molecules(library_id=library_id, molecule_ids=molecule_ids, added_by=added_by, db=db_session)

        logger.info(f"Added {results['added']} molecules to library {library_id} by user {added_by}, skipped {results['skipped']} molecules")
        return results

    def remove_molecule_from_library(
        self,
        library_id: uuid.UUID,
        molecule_id: uuid.UUID,
        user: Dict[str, Any],
        db: Optional[Session] = None
    ) -> bool:
        """Remove a molecule from a library

        Args:
            library_id: UUID of the library
            molecule_id: UUID of the molecule to remove
            user: User removing the molecule
            db: Optional database session

        Returns:
            True if removed, False if not in library
        """
        db_session = db or get_db()

        # Check if user has access to library
        if not crud_library.library.check_user_access(library_id=library_id, user=user, db=db_session):
            raise AuthorizationException(message=LIBRARY_ERRORS["INSUFFICIENT_LIBRARY_PERMISSIONS"], library_id=str(library_id))

        # Remove molecule from library using molecule_service.remove_from_library
        result = crud_library.library.remove_molecule(library_id=library_id, molecule_id=molecule_id, db=db_session)

        logger.info(f"Removed molecule {molecule_id} from library {library_id} by user {user['id']}")
        return result

    def remove_molecules_from_library(
        self,
        library_id: uuid.UUID,
        molecule_ids: List[uuid.UUID],
        user: Dict[str, Any],
        db: Optional[Session] = None
    ) -> Dict[str, int]:
        """Remove multiple molecules from a library

        Args:
            library_id: UUID of the library
            molecule_ids: List of molecule UUIDs to remove
            user: User removing the molecules
            db: Optional database session

        Returns:
            Dictionary with counts of removed and skipped molecules
        """
        db_session = db or get_db()

        # Check if user has access to library
        if not crud_library.library.check_user_access(library_id=library_id, user=user, db=db_session):
            raise AuthorizationException(message=LIBRARY_ERRORS["INSUFFICIENT_LIBRARY_PERMISSIONS"], library_id=str(library_id))

        # Remove molecules from library using library.remove_molecules
        results = crud_library.library.remove_molecules(library_id=library_id, molecule_ids=molecule_ids, db=db_session)

        logger.info(f"Removed {results['removed']} molecules from library {library_id} by user {user['id']}, skipped {results['skipped']} molecules")
        return results

    def get_library_molecules(
        self,
        library_id: uuid.UUID,
        user: Dict[str, Any],
        filter_params: Optional[Dict[str, Any]] = None,
        skip: int = 0,
        limit: int = 100,
        sort_by: Optional[str] = None,
        descending: bool = False,
        db: Optional[Session] = None
    ) -> Dict[str, Any]:
        """Get molecules in a library with pagination and filtering

        Args:
            library_id: UUID of the library
            user: User accessing the library
            filter_params: Optional filter parameters
            skip: Number of records to skip
            limit: Maximum number of records to return
            sort_by: Field to sort by
            descending: Whether to sort in descending order
            db: Optional database session

        Returns:
            Molecules with pagination info
        """
        db_session = db or get_db()

        # Check if user has access to library
        if not crud_library.library.check_user_access(library_id=library_id, user=user, db=db_session):
            raise AuthorizationException(message=LIBRARY_ERRORS["INSUFFICIENT_LIBRARY_PERMISSIONS"], library_id=str(library_id))

        # Get molecules from library with filtering and pagination
        molecules = crud_library.library.get_molecules(library_id=library_id, filter_params=filter_params, db=db_session, skip=skip, limit=limit, sort_by=sort_by, descending=descending)

        return molecules

# Create singleton instance for application-wide use
library_service = LibraryService()