"""
API endpoints for managing CRO (Contract Research Organization) services in the 
Molecular Data Management and CRO Integration Platform.

This module implements RESTful endpoints for creating, retrieving, updating, and deleting 
CRO services, as well as specialized endpoints for service activation/deactivation and statistics.
"""

from typing import List, Dict, Any, Optional
from uuid import UUID

from fastapi import APIRouter, Depends, HTTPException, status, Query, Path, Body
from sqlalchemy.orm import Session

# Internal imports
from ....api.deps import get_db, get_current_admin, get_current_user, get_current_cro_user
from ....models.cro_service import ServiceType, CROService
from ....schemas.cro_service import CROServiceCreate, CROServiceUpdate, CROService as CROServiceSchema, CROServiceFilter
from ....services.cro_service import (
    get_cro_service, list_cro_services, list_active_cro_services, create_cro_service,
    update_cro_service, update_cro_service_specifications, activate_cro_service,
    deactivate_cro_service, delete_cro_service, get_service_types,
    search_cro_services, get_service_counts_by_type, get_service_counts_by_provider
)
from ....core.exceptions import NotFoundException, ConflictException, ValidationException
from ....core.logging import get_logger

# Create logger instance
logger = get_logger(__name__)

# Create API router for CRO endpoints
router = APIRouter()


@router.get('/', response_model=Dict[str, Any], status_code=status.HTTP_200_OK)
async def get_cro_services(
    name_contains: Optional[str] = None,
    provider: Optional[str] = None,
    service_type: Optional[ServiceType] = None,
    active_only: Optional[bool] = None,
    max_turnaround_days: Optional[int] = None,
    max_price: Optional[float] = None,
    skip: int = Query(0, ge=0),
    limit: int = Query(100, ge=1, le=100),
    db: Session = Depends(get_db)
) -> Dict[str, Any]:
    """
    Get a list of CRO services with optional filtering.
    
    Args:
        name_contains: Optional filter to search in service names
        provider: Optional filter for provider name
        service_type: Optional filter for service type
        active_only: Optional filter for active services only
        max_turnaround_days: Optional maximum turnaround days
        max_price: Optional maximum price
        skip: Number of records to skip for pagination
        limit: Maximum number of records to return
        db: Database session dependency
        
    Returns:
        Dictionary with services and pagination information
    """
    # Create filter parameters if any filters are provided
    filter_params = None
    if any([name_contains, provider, service_type, active_only is not None,
            max_turnaround_days is not None, max_price is not None]):
        filter_params = CROServiceFilter(
            name_contains=name_contains,
            provider=provider,
            service_type=service_type,
            active_only=active_only,
            max_turnaround_days=max_turnaround_days,
            max_price=max_price
        )
    
    # Get services with filtering
    if active_only:
        result = list_active_cro_services(db=db, skip=skip, limit=limit)
    else:
        result = list_cro_services(filter_params=filter_params, db=db, skip=skip, limit=limit)
    
    return result


@router.get('/active', response_model=Dict[str, Any], status_code=status.HTTP_200_OK)
async def get_active_cro_services(
    skip: int = Query(0, ge=0),
    limit: int = Query(100, ge=1, le=100),
    db: Session = Depends(get_db)
) -> Dict[str, Any]:
    """
    Get a list of active CRO services.
    
    Args:
        skip: Number of records to skip for pagination
        limit: Maximum number of records to return
        db: Database session dependency
        
    Returns:
        Dictionary with active services and pagination information
    """
    return list_active_cro_services(db=db, skip=skip, limit=limit)


@router.get('/search', response_model=Dict[str, Any], status_code=status.HTTP_200_OK)
async def search_services(
    q: str = Query(..., min_length=1),
    skip: int = Query(0, ge=0),
    limit: int = Query(100, ge=1, le=100),
    db: Session = Depends(get_db)
) -> Dict[str, Any]:
    """
    Search CRO services by name or description.
    
    Args:
        q: Search term
        skip: Number of records to skip for pagination
        limit: Maximum number of records to return
        db: Database session dependency
        
    Returns:
        Dictionary with matching services and pagination information
    """
    return search_cro_services(search_term=q, db=db, skip=skip, limit=limit)


@router.get('/{service_id}', response_model=CROServiceSchema, status_code=status.HTTP_200_OK)
async def get_service_by_id(
    service_id: UUID = Path(...),
    db: Session = Depends(get_db)
) -> CROServiceSchema:
    """
    Get a specific CRO service by ID.
    
    Args:
        service_id: ID of the service to retrieve
        db: Database session dependency
        
    Returns:
        The CRO service details
        
    Raises:
        HTTPException: If service not found
    """
    try:
        service = get_cro_service(service_id=service_id, db=db)
        return service
    except NotFoundException as e:
        logger.warning(f"CRO service not found: {service_id}")
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=e.message
        )


@router.post('/', response_model=CROServiceSchema, status_code=status.HTTP_201_CREATED, dependencies=[Depends(get_current_admin)])
async def create_service(
    service_data: CROServiceCreate,
    db: Session = Depends(get_db),
    current_user = Depends(get_current_user)
) -> CROServiceSchema:
    """
    Create a new CRO service.
    
    Args:
        service_data: Data for the new service
        db: Database session dependency
        current_user: Current authenticated user
        
    Returns:
        The created CRO service
        
    Raises:
        HTTPException: If service with same name exists or validation fails
    """
    logger.info(f"Creating new CRO service: {service_data.name}")
    
    try:
        service = create_cro_service(service_data=service_data, db=db)
        logger.info(f"Created CRO service with ID: {service.id}")
        return service
    except ConflictException as e:
        logger.warning(f"Conflict when creating CRO service: {e.message}")
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail=e.message
        )
    except ValidationException as e:
        logger.warning(f"Validation error when creating CRO service: {e.message}")
        raise HTTPException(
            status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
            detail=e.message
        )


@router.put('/{service_id}', response_model=CROServiceSchema, status_code=status.HTTP_200_OK, dependencies=[Depends(get_current_admin)])
async def update_service(
    service_id: UUID = Path(...),
    service_data: CROServiceUpdate = Body(...),
    db: Session = Depends(get_db),
    current_user = Depends(get_current_user)
) -> CROServiceSchema:
    """
    Update an existing CRO service.
    
    Args:
        service_id: ID of the service to update
        service_data: Updated service data
        db: Database session dependency
        current_user: Current authenticated user
        
    Returns:
        The updated CRO service
        
    Raises:
        HTTPException: If service not found, conflict occurs, or validation fails
    """
    logger.info(f"Updating CRO service: {service_id}")
    
    try:
        service = update_cro_service(service_id=service_id, service_data=service_data, db=db)
        logger.info(f"Updated CRO service: {service_id}")
        return service
    except NotFoundException as e:
        logger.warning(f"CRO service not found for update: {service_id}")
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=e.message
        )
    except ConflictException as e:
        logger.warning(f"Conflict when updating CRO service: {e.message}")
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail=e.message
        )
    except ValidationException as e:
        logger.warning(f"Validation error when updating CRO service: {e.message}")
        raise HTTPException(
            status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
            detail=e.message
        )


@router.patch('/{service_id}/specifications', response_model=CROServiceSchema, status_code=status.HTTP_200_OK, dependencies=[Depends(get_current_admin)])
async def update_service_specifications(
    service_id: UUID = Path(...),
    specifications: Dict[str, Any] = Body(...),
    db: Session = Depends(get_db),
    current_user = Depends(get_current_user)
) -> CROServiceSchema:
    """
    Update specifications for a CRO service.
    
    Args:
        service_id: ID of the service to update
        specifications: New service specifications
        db: Database session dependency
        current_user: Current authenticated user
        
    Returns:
        The updated CRO service
        
    Raises:
        HTTPException: If service not found or validation fails
    """
    logger.info(f"Updating specifications for CRO service: {service_id}")
    
    try:
        service = update_cro_service_specifications(
            service_id=service_id, 
            specifications=specifications, 
            db=db
        )
        logger.info(f"Updated specifications for CRO service: {service_id}")
        return service
    except NotFoundException as e:
        logger.warning(f"CRO service not found for specification update: {service_id}")
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=e.message
        )
    except ValidationException as e:
        logger.warning(f"Validation error when updating CRO service specifications: {e.message}")
        raise HTTPException(
            status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
            detail=e.message
        )


@router.post('/{service_id}/activate', response_model=CROServiceSchema, status_code=status.HTTP_200_OK, dependencies=[Depends(get_current_admin)])
async def activate_service(
    service_id: UUID = Path(...),
    db: Session = Depends(get_db),
    current_user = Depends(get_current_user)
) -> CROServiceSchema:
    """
    Activate a CRO service.
    
    Args:
        service_id: ID of the service to activate
        db: Database session dependency
        current_user: Current authenticated user
        
    Returns:
        The activated CRO service
        
    Raises:
        HTTPException: If service not found
    """
    logger.info(f"Activating CRO service: {service_id}")
    
    try:
        service = activate_cro_service(service_id=service_id, db=db)
        logger.info(f"Activated CRO service: {service_id}")
        return service
    except NotFoundException as e:
        logger.warning(f"CRO service not found for activation: {service_id}")
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=e.message
        )


@router.post('/{service_id}/deactivate', response_model=CROServiceSchema, status_code=status.HTTP_200_OK, dependencies=[Depends(get_current_admin)])
async def deactivate_service(
    service_id: UUID = Path(...),
    db: Session = Depends(get_db),
    current_user = Depends(get_current_user)
) -> CROServiceSchema:
    """
    Deactivate a CRO service.
    
    Args:
        service_id: ID of the service to deactivate
        db: Database session dependency
        current_user: Current authenticated user
        
    Returns:
        The deactivated CRO service
        
    Raises:
        HTTPException: If service not found
    """
    logger.info(f"Deactivating CRO service: {service_id}")
    
    try:
        service = deactivate_cro_service(service_id=service_id, db=db)
        logger.info(f"Deactivated CRO service: {service_id}")
        return service
    except NotFoundException as e:
        logger.warning(f"CRO service not found for deactivation: {service_id}")
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=e.message
        )


@router.delete('/{service_id}', status_code=status.HTTP_200_OK, dependencies=[Depends(get_current_admin)])
async def delete_service(
    service_id: UUID = Path(...),
    db: Session = Depends(get_db),
    current_user = Depends(get_current_user)
) -> Dict[str, str]:
    """
    Delete a CRO service if it has no associated submissions.
    
    Args:
        service_id: ID of the service to delete
        db: Database session dependency
        current_user: Current authenticated user
        
    Returns:
        Success message
        
    Raises:
        HTTPException: If service not found or has associated submissions
    """
    logger.info(f"Deleting CRO service: {service_id}")
    
    try:
        delete_cro_service(service_id=service_id, db=db)
        logger.info(f"Deleted CRO service: {service_id}")
        return {"message": "CRO service deleted successfully"}
    except NotFoundException as e:
        logger.warning(f"CRO service not found for deletion: {service_id}")
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=e.message
        )
    except ConflictException as e:
        logger.warning(f"Conflict when deleting CRO service: {e.message}")
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail=e.message
        )


@router.get('/types', response_model=List[Dict[str, str]], status_code=status.HTTP_200_OK)
async def get_service_types_list() -> List[Dict[str, str]]:
    """
    Get a list of available CRO service types.
    
    Returns:
        List of service types with ID and name
    """
    return get_service_types()


@router.get('/stats/by-type', response_model=List[Dict[str, Any]], status_code=status.HTTP_200_OK)
async def get_service_type_counts(
    db: Session = Depends(get_db)
) -> List[Dict[str, Any]]:
    """
    Get count of services grouped by service type.
    
    Args:
        db: Database session dependency
        
    Returns:
        List of service type counts
    """
    return get_service_counts_by_type(db=db)


@router.get('/stats/by-provider', response_model=List[Dict[str, Any]], status_code=status.HTTP_200_OK)
async def get_service_provider_counts(
    db: Session = Depends(get_db)
) -> List[Dict[str, Any]]:
    """
    Get count of services grouped by provider.
    
    Args:
        db: Database session dependency
        
    Returns:
        List of provider counts
    """
    return get_service_counts_by_provider(db=db)