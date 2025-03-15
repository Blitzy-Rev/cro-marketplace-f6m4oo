"""
CRO Service module for the Molecular Data Management and CRO Integration Platform.

This module implements service layer functions for managing Contract Research Organization (CRO)
services, including creating, retrieving, updating, and filtering services that can be selected
for experimental testing of molecules.
"""

import logging  # standard library
from typing import List, Dict, Any, Optional, Union  # standard library
from uuid import UUID  # standard library
from sqlalchemy.orm import Session  # sqlalchemy ^1.4.0

from ..crud.crud_cro_service import CRUDCROService, cro_service
from ..models.cro_service import ServiceType, CROService
from ..schemas.cro_service import CROServiceCreate, CROServiceUpdate, CROServiceFilter
from ..db.session import db_session
from ..core.exceptions import NotFoundException, ConflictException, ValidationException
from ..constants.error_messages import SUBMISSION_ERRORS

# Configure logger
logger = logging.getLogger(__name__)


def get_cro_service(service_id: UUID, db: Optional[Session] = None) -> CROService:
    """
    Get a CRO service by ID.
    
    Args:
        service_id: The service ID to retrieve
        db: Optional database session
        
    Returns:
        The CRO service if found
        
    Raises:
        NotFoundException: If the service is not found
    """
    db_session_local = db or db_session
    service = cro_service.get(service_id, db_session_local)
    
    if not service:
        raise NotFoundException(
            message=f"CRO service with ID {service_id} not found",
            resource_type="CROService"
        )
    
    logger.debug(f"Retrieved CRO service: {service_id}")
    return service


def get_cro_service_by_name(name: str, db: Optional[Session] = None) -> Optional[CROService]:
    """
    Get a CRO service by name.
    
    Args:
        name: The service name to retrieve
        db: Optional database session
        
    Returns:
        The CRO service if found, None otherwise
    """
    db_session_local = db or db_session
    filter_params = {"name": name}
    result = cro_service.filter(filter_params, db_session_local)
    
    if result["total"] > 0:
        logger.debug(f"Found CRO service by name: {name}")
        return result["items"][0]
    
    logger.debug(f"No CRO service found with name: {name}")
    return None


def list_cro_services(
    filter_params: Optional[CROServiceFilter] = None,
    db: Optional[Session] = None,
    skip: int = 0,
    limit: int = 100
) -> Dict[str, Any]:
    """
    List CRO services with optional filtering.
    
    Args:
        filter_params: Optional filtering parameters
        db: Optional database session
        skip: Number of records to skip for pagination
        limit: Maximum number of records to return
        
    Returns:
        Dictionary with services and pagination information
    """
    db_session_local = db or db_session
    
    if filter_params:
        logger.debug(f"Filtering CRO services with params: {filter_params}")
        return cro_service.filter_services(filter_params, db_session_local, skip, limit)
    
    logger.debug(f"Listing CRO services with pagination: skip={skip}, limit={limit}")
    return cro_service.get_multi(db_session_local, skip, limit)


def list_active_cro_services(
    db: Optional[Session] = None,
    skip: int = 0,
    limit: int = 100
) -> Dict[str, Any]:
    """
    List only active CRO services.
    
    Args:
        db: Optional database session
        skip: Number of records to skip for pagination
        limit: Maximum number of records to return
        
    Returns:
        Dictionary with active services and pagination information
    """
    db_session_local = db or db_session
    logger.debug(f"Listing active CRO services with pagination: skip={skip}, limit={limit}")
    return cro_service.get_active_services(db_session_local, skip, limit)


def create_cro_service(
    service_data: Union[CROServiceCreate, Dict[str, Any]],
    db: Optional[Session] = None
) -> CROService:
    """
    Create a new CRO service.
    
    Args:
        service_data: Data for the new service
        db: Optional database session
        
    Returns:
        The created CRO service
        
    Raises:
        ConflictException: If a service with the same name already exists
    """
    db_session_local = db or db_session
    
    # Check for existing service with same name
    service_name = service_data.name if hasattr(service_data, "name") else service_data.get("name")
    existing_service = get_cro_service_by_name(service_name, db_session_local)
    
    if existing_service:
        logger.warning(f"Attempted to create duplicate CRO service: {service_name}")
        raise ConflictException(
            message=f"CRO service with name '{service_name}' already exists"
        )
    
    logger.info(f"Creating new CRO service: {service_name}")
    return cro_service.create_service(service_data, db_session_local)


def update_cro_service(
    service_id: UUID,
    service_data: Union[CROServiceUpdate, Dict[str, Any]],
    db: Optional[Session] = None
) -> CROService:
    """
    Update an existing CRO service.
    
    Args:
        service_id: ID of the service to update
        service_data: Updated service data
        db: Optional database session
        
    Returns:
        The updated CRO service
        
    Raises:
        NotFoundException: If the service is not found
        ConflictException: If update would create a name conflict
    """
    db_session_local = db or db_session
    
    # Get the existing service
    db_obj = get_cro_service(service_id, db_session_local)
    
    # Check for name conflicts if name is being updated
    if (hasattr(service_data, "name") and service_data.name) or \
       (isinstance(service_data, dict) and service_data.get("name")):
        
        new_name = service_data.name if hasattr(service_data, "name") else service_data.get("name")
        existing_service = get_cro_service_by_name(new_name, db_session_local)
        
        if existing_service and existing_service.id != service_id:
            logger.warning(f"Name conflict when updating CRO service {service_id} to name '{new_name}'")
            raise ConflictException(
                message=f"Another CRO service with name '{new_name}' already exists"
            )
    
    logger.info(f"Updating CRO service: {service_id}")
    return cro_service.update_service(db_obj, service_data, db_session_local)


def update_cro_service_specifications(
    service_id: UUID,
    specifications: Dict[str, Any],
    db: Optional[Session] = None
) -> CROService:
    """
    Update specifications for a CRO service.
    
    Args:
        service_id: ID of the service to update
        specifications: New service specifications
        db: Optional database session
        
    Returns:
        The updated CRO service
        
    Raises:
        NotFoundException: If the service is not found
    """
    db_session_local = db or db_session
    
    # Get the existing service
    service = get_cro_service(service_id, db_session_local)
    
    logger.info(f"Updating specifications for CRO service: {service_id}")
    return cro_service.update_specifications(service, specifications, db_session_local)


def activate_cro_service(
    service_id: UUID,
    db: Optional[Session] = None
) -> CROService:
    """
    Activate a CRO service.
    
    Args:
        service_id: ID of the service to activate
        db: Optional database session
        
    Returns:
        The activated CRO service
        
    Raises:
        NotFoundException: If the service is not found
    """
    db_session_local = db or db_session
    
    # Get the existing service
    service = get_cro_service(service_id, db_session_local)
    
    logger.info(f"Activating CRO service: {service_id}")
    return cro_service.activate_service(service, db_session_local)


def deactivate_cro_service(
    service_id: UUID,
    db: Optional[Session] = None
) -> CROService:
    """
    Deactivate a CRO service.
    
    Args:
        service_id: ID of the service to deactivate
        db: Optional database session
        
    Returns:
        The deactivated CRO service
        
    Raises:
        NotFoundException: If the service is not found
    """
    db_session_local = db or db_session
    
    # Get the existing service
    service = get_cro_service(service_id, db_session_local)
    
    logger.info(f"Deactivating CRO service: {service_id}")
    return cro_service.deactivate_service(service, db_session_local)


def delete_cro_service(
    service_id: UUID,
    db: Optional[Session] = None
) -> bool:
    """
    Delete a CRO service if it has no associated submissions.
    
    Args:
        service_id: ID of the service to delete
        db: Optional database session
        
    Returns:
        True if the service was deleted successfully
        
    Raises:
        NotFoundException: If the service is not found
        ConflictException: If the service has associated submissions
    """
    db_session_local = db or db_session
    
    # Get the existing service
    service = get_cro_service(service_id, db_session_local)
    
    # Check if service has associated submissions
    if service.submissions and len(service.submissions) > 0:
        logger.warning(f"Cannot delete CRO service {service_id} with existing submissions")
        raise ConflictException(
            message="Cannot delete service with existing submissions",
            details={"submission_count": len(service.submissions)}
        )
    
    logger.info(f"Deleting CRO service: {service_id}")
    deleted_service = cro_service.remove(service_id, db_session_local)
    return bool(deleted_service)


def get_service_types() -> List[Dict[str, str]]:
    """
    Get a list of available CRO service types.
    
    Returns:
        List of service types with ID and name
    """
    service_types = []
    
    for service_type in ServiceType:
        service_types.append({
            "id": service_type.value,
            "name": service_type.name
        })
    
    logger.debug(f"Retrieved {len(service_types)} service types")
    return service_types


def search_cro_services(
    search_term: str,
    db: Optional[Session] = None,
    skip: int = 0,
    limit: int = 100
) -> Dict[str, Any]:
    """
    Search CRO services by name or description.
    
    Args:
        search_term: Term to search for
        db: Optional database session
        skip: Number of records to skip for pagination
        limit: Maximum number of records to return
        
    Returns:
        Dictionary with matching services and pagination information
    """
    db_session_local = db or db_session
    logger.debug(f"Searching CRO services with term: '{search_term}'")
    return cro_service.search_services(search_term, db_session_local, skip, limit)


def get_service_counts_by_type(
    db: Optional[Session] = None
) -> List[Dict[str, Any]]:
    """
    Get count of services grouped by service type.
    
    Args:
        db: Optional database session
        
    Returns:
        List of service type counts
    """
    db_session_local = db or db_session
    logger.debug("Getting service counts by type")
    return cro_service.get_service_counts_by_type(db_session_local)


def get_service_counts_by_provider(
    db: Optional[Session] = None
) -> List[Dict[str, Any]]:
    """
    Get count of services grouped by provider.
    
    Args:
        db: Optional database session
        
    Returns:
        List of provider counts
    """
    db_session_local = db or db_session
    logger.debug("Getting service counts by provider")
    return cro_service.get_service_counts_by_provider(db_session_local)