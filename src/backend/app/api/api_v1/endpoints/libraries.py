"""
FastAPI endpoint handlers for library-related operations in the Molecular Data Management and CRO Integration Platform. This file implements RESTful API endpoints for library creation, retrieval, filtering, and molecule management within libraries.
"""
from typing import List, Dict, Any, Optional
import uuid

# FastAPI
from fastapi import APIRouter, Depends, HTTPException, status, Query, Path, Body

# SQLAlchemy
from sqlalchemy.orm import Session

# Internal imports
from ..deps import get_db, get_current_user, get_current_pharma_user, get_library_access
from ..models.user import User
from ..schemas.library import LibraryBase, LibraryCreate, LibraryUpdate, Library, LibraryWithMolecules, LibraryFilter, MoleculeAddRemove
from ..crud.crud_library import library
from ..core.logging import get_logger

# Initialize logger
logger = get_logger(__name__)

# Define router
router = APIRouter(prefix="/libraries", tags=["libraries"])


@router.post("/", response_model=Library, status_code=status.HTTP_201_CREATED)
def create_library(
    library_data: LibraryCreate,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
) -> Library:
    """
    Create a new library for the current user
    """
    try:
        logger.info(f"User {current_user.id} attempting to create a new library")
        created_library = library.create_with_owner(library_data, current_user.id, db=db)
        logger.info(f"Library {created_library.id} created successfully by user {current_user.id}")
        return created_library
    except Exception as e:
        logger.error(f"Error creating library: {e}", exc_info=True)
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail=str(e))


@router.get("/{library_id}", response_model=Library)
def get_library(
    library_id: uuid.UUID,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
) -> Library:
    """
    Get a library by ID
    """
    try:
        logger.info(f"User {current_user.id} attempting to retrieve library {library_id}")
        if not library.check_user_access(library_id, current_user, db=db):
            logger.warning(f"User {current_user.id} does not have access to library {library_id}")
            raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Insufficient permissions")
        
        library_data = library.get_with_molecule_count(library_id, db=db)
        if not library_data:
            logger.warning(f"Library {library_id} not found")
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Library not found")
        
        logger.info(f"Library {library_id} retrieved successfully by user {current_user.id}")
        return library_data
    except HTTPException:
        raise  # Re-raise HTTPExceptions to prevent them from being caught in the generic exception handler
    except Exception as e:
        logger.error(f"Error retrieving library {library_id}: {e}", exc_info=True)
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail=str(e))


@router.get("/{library_id}/molecules", response_model=Dict[str, Any])
def get_library_with_molecules(
    library_id: uuid.UUID,
    skip: int = Query(0, description="Number of records to skip"),
    limit: int = Query(100, description="Maximum number of records to return"),
    sort_by: Optional[str] = Query(None, description="Field to sort by"),
    descending: bool = Query(False, description="Sort in descending order"),
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
) -> Dict[str, Any]:
    """
    Get a library by ID with its molecules
    """
    try:
        logger.info(f"User {current_user.id} attempting to retrieve library {library_id} with molecules")
        if not library.check_user_access(library_id, current_user, db=db):
            logger.warning(f"User {current_user.id} does not have access to library {library_id}")
            raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Insufficient permissions")
        
        library_data = library.get(library_id, db=db)
        if not library_data:
            logger.warning(f"Library {library_id} not found")
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Library not found")
        
        molecules = library.get_molecules(library_id, db=db, skip=skip, limit=limit, sort_by=sort_by, descending=descending)
        
        logger.info(f"Library {library_id} with molecules retrieved successfully by user {current_user.id}")
        return {
            "library": library_data,
            "molecules": molecules["items"],
            "total": molecules["total"],
            "page": molecules["page"],
            "size": molecules["size"],
            "pages": molecules["pages"]
        }
    except HTTPException:
        raise  # Re-raise HTTPExceptions to prevent them from being caught in the generic exception handler
    except Exception as e:
        logger.error(f"Error retrieving library {library_id} with molecules: {e}", exc_info=True)
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail=str(e))


@router.get("/", response_model=Dict[str, Any])
def get_libraries(
    skip: int = Query(0, description="Number of records to skip"),
    limit: int = Query(100, description="Maximum number of records to return"),
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
) -> Dict[str, Any]:
    """
    Get all libraries accessible to the current user
    """
    try:
        logger.info(f"User {current_user.id} attempting to retrieve all accessible libraries")
        libraries = library.get_accessible_libraries(current_user, db=db, skip=skip, limit=limit)
        logger.info(f"Accessible libraries retrieved successfully by user {current_user.id}")
        return libraries
    except Exception as e:
        logger.error(f"Error retrieving accessible libraries: {e}", exc_info=True)
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail=str(e))


@router.get("/user/{user_id}", response_model=Dict[str, Any])
def get_user_libraries(
    user_id: uuid.UUID,
    skip: int = Query(0, description="Number of records to skip"),
    limit: int = Query(100, description="Maximum number of records to return"),
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
) -> Dict[str, Any]:
    """
    Get libraries owned by a specific user
    """
    try:
        logger.info(f"User {current_user.id} attempting to retrieve libraries for user {user_id}")
        user_libraries = library.get_by_owner(user_id, db=db, skip=skip, limit=limit)
        logger.info(f"Libraries for user {user_id} retrieved successfully by user {current_user.id}")
        return user_libraries
    except Exception as e:
        logger.error(f"Error retrieving libraries for user {user_id}: {e}", exc_info=True)
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail=str(e))


@router.get("/organization/{organization_id}", response_model=Dict[str, Any])
def get_organization_libraries(
    organization_id: uuid.UUID,
    skip: int = Query(0, description="Number of records to skip"),
    limit: int = Query(100, description="Maximum number of records to return"),
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
) -> Dict[str, Any]:
    """
    Get libraries belonging to a specific organization
    """
    try:
        logger.info(f"User {current_user.id} attempting to retrieve libraries for organization {organization_id}")
        # Check if the current user has access to the organization
        # This is a placeholder; implement actual organization access check in the dependency
        if current_user.organization_id != organization_id and not current_user.is_superuser:
            logger.warning(f"User {current_user.id} does not have access to organization {organization_id}")
            raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Insufficient permissions")
        
        organization_libraries = library.get_by_organization(organization_id, db=db, skip=skip, limit=limit)
        logger.info(f"Libraries for organization {organization_id} retrieved successfully by user {current_user.id}")
        return organization_libraries
    except HTTPException:
        raise  # Re-raise HTTPExceptions to prevent them from being caught in the generic exception handler
    except Exception as e:
        logger.error(f"Error retrieving libraries for organization {organization_id}: {e}", exc_info=True)
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail=str(e))


@router.put("/{library_id}", response_model=Library)
def update_library(
    library_id: uuid.UUID,
    library_data: LibraryUpdate,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
) -> Library:
    """
    Update an existing library
    """
    try:
        logger.info(f"User {current_user.id} attempting to update library {library_id}")
        if not library.check_user_access(library_id, current_user, db=db):
            logger.warning(f"User {current_user.id} does not have access to library {library_id}")
            raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Insufficient permissions")
        
        existing_library = library.get(library_id, db=db)
        if not existing_library:
            logger.warning(f"Library {library_id} not found")
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Library not found")
        
        updated_library = library.update(existing_library, library_data, db=db)
        logger.info(f"Library {library_id} updated successfully by user {current_user.id}")
        return updated_library
    except HTTPException:
        raise  # Re-raise HTTPExceptions to prevent them from being caught in the generic exception handler
    except Exception as e:
        logger.error(f"Error updating library {library_id}: {e}", exc_info=True)
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail=str(e))


@router.delete("/{library_id}", status_code=status.HTTP_200_OK)
def delete_library(
    library_id: uuid.UUID,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
) -> Dict[str, bool]:
    """
    Delete a library by ID
    """
    try:
        logger.info(f"User {current_user.id} attempting to delete library {library_id}")
        if not library.check_user_access(library_id, current_user, db=db):
            logger.warning(f"User {current_user.id} does not have access to library {library_id}")
            raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Insufficient permissions")
        
        existing_library = library.get(library_id, db=db)
        if not existing_library:
            logger.warning(f"Library {library_id} not found")
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Library not found")
        
        library.remove(library_id, db=db)
        logger.info(f"Library {library_id} deleted successfully by user {current_user.id}")
        return {"success": True}
    except HTTPException:
        raise  # Re-raise HTTPExceptions to prevent them from being caught in the generic exception handler
    except Exception as e:
        logger.error(f"Error deleting library {library_id}: {e}", exc_info=True)
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail=str(e))


@router.post("/filter/", response_model=Dict[str, Any])
def filter_libraries(
    filter_params: LibraryFilter,
    skip: int = Query(0, description="Number of records to skip"),
    limit: int = Query(100, description="Maximum number of records to return"),
    sort_by: Optional[str] = Query(None, description="Field to sort by"),
    descending: bool = Query(False, description="Sort in descending order"),
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
) -> Dict[str, Any]:
    """
    Filter libraries based on various criteria
    """
    try:
        logger.info(f"User {current_user.id} attempting to filter libraries")
        filtered_libraries = library.filter_libraries(filter_params, current_user, db=db, skip=skip, limit=limit, sort_by=sort_by, descending=descending)
        logger.info(f"Libraries filtered successfully by user {current_user.id}")
        return filtered_libraries
    except Exception as e:
        logger.error(f"Error filtering libraries: {e}", exc_info=True)
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail=str(e))


@router.post("/molecules/add", status_code=status.HTTP_200_OK)
def add_molecules_to_library(
    data: MoleculeAddRemove,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
) -> Dict[str, int]:
    """
    Add molecules to a library
    """
    try:
        logger.info(f"User {current_user.id} attempting to add molecules to library {data.library_id}")
        if not library.check_user_access(data.library_id, current_user, db=db):
            logger.warning(f"User {current_user.id} does not have access to library {data.library_id}")
            raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Insufficient permissions")
        
        if data.operation != "add":
            logger.warning(f"Invalid operation: {data.operation}")
            raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Invalid operation. Use 'add'.")
        
        results = library.add_molecules(data.library_id, data.molecule_ids, current_user.id, db=db)
        logger.info(f"Molecules added to library {data.library_id} successfully by user {current_user.id}")
        return results
    except HTTPException:
        raise  # Re-raise HTTPExceptions to prevent them from being caught in the generic exception handler
    except Exception as e:
        logger.error(f"Error adding molecules to library {data.library_id}: {e}", exc_info=True)
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail=str(e))


@router.post("/molecules/remove", status_code=status.HTTP_200_OK)
def remove_molecules_from_library(
    data: MoleculeAddRemove,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
) -> Dict[str, int]:
    """
    Remove molecules from a library
    """
    try:
        logger.info(f"User {current_user.id} attempting to remove molecules from library {data.library_id}")
        if not library.check_user_access(data.library_id, current_user, db=db):
            logger.warning(f"User {current_user.id} does not have access to library {data.library_id}")
            raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Insufficient permissions")
        
        if data.operation != "remove":
            logger.warning(f"Invalid operation: {data.operation}")
            raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Invalid operation. Use 'remove'.")
        
        results = library.remove_molecules(data.library_id, data.molecule_ids, db=db)
        logger.info(f"Molecules removed from library {data.library_id} successfully by user {current_user.id}")
        return results
    except HTTPException:
        raise  # Re-raise HTTPExceptions to prevent them from being caught in the generic exception handler
    except Exception as e:
        logger.error(f"Error removing molecules from library {data.library_id}: {e}", exc_info=True)
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail=str(e))