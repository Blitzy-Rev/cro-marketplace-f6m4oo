from typing import List, Dict, Optional, Any, Union
from sqlalchemy.orm import Session
from sqlalchemy import select, func, or_

from .base import CRUDBase
from ..models.cro_service import CROService, ServiceType
from ..schemas.cro_service import CROServiceCreate, CROServiceUpdate, CROServiceFilter
from ..db.session import db_session

class CRUDCROService(CRUDBase[CROService, CROServiceCreate, CROServiceUpdate]):
    """
    CRUD operations for CROService model with service-specific functionality.
    """

    def __init__(self):
        """
        Initialize the CRUDCROService class.
        """
        super().__init__(CROService)

    def create_service(self, obj_in: Union[CROServiceCreate, Dict[str, Any]], db: Optional[Session] = None) -> CROService:
        """
        Create a new CRO service with validation.
        
        Args:
            obj_in: Service data (schema or dict)
            db: Optional database session (uses default if not provided)
            
        Returns:
            The created CRO service instance
        """
        db_session_local = db or db_session
        
        # Convert to dict if it's a Pydantic model
        if not isinstance(obj_in, dict):
            obj_in_data = obj_in.model_dump()
        else:
            obj_in_data = obj_in
        
        # Extract service parameters
        service_params = {k: v for k, v in obj_in_data.items() if k != 'specifications'}
        specifications = obj_in_data.get('specifications')
        
        # Create service instance
        db_obj = CROService.create(**service_params)
        
        # Set specifications if provided
        if specifications:
            db_obj.set_specifications(specifications)
        
        # Add to session and commit
        db_session_local.add(db_obj)
        db_session_local.commit()
        db_session_local.refresh(db_obj)
        
        return db_obj

    def update_service(self, db_obj: CROService, obj_in: Union[CROServiceUpdate, Dict[str, Any]], db: Optional[Session] = None) -> CROService:
        """
        Update an existing CRO service.
        
        Args:
            db_obj: The CRO service instance to update
            obj_in: Updated data (schema or dict)
            db: Optional database session (uses default if not provided)
            
        Returns:
            The updated CRO service instance
        """
        db_session_local = db or db_session
        
        # Update basic attributes
        db_obj = super().update(db_obj, obj_in, db_session_local)
        
        # Update specifications if provided
        if isinstance(obj_in, dict) and 'specifications' in obj_in:
            db_obj.set_specifications(obj_in['specifications'])
        elif hasattr(obj_in, 'specifications') and obj_in.specifications is not None:
            db_obj.set_specifications(obj_in.specifications)
        
        # Commit changes
        db_session_local.add(db_obj)
        db_session_local.commit()
        db_session_local.refresh(db_obj)
        
        return db_obj

    def get_services_by_provider(self, provider: str, db: Optional[Session] = None, skip: int = 0, limit: int = 100) -> Dict[str, Any]:
        """
        Get services filtered by provider.
        
        Args:
            provider: The CRO provider name
            db: Optional database session (uses default if not provided)
            skip: Number of records to skip (for pagination)
            limit: Maximum number of records to return (for pagination)
            
        Returns:
            Dictionary with services and pagination metadata
        """
        db_session_local = db or db_session
        
        # Create filter with provider
        filter_params = {"provider": provider}
        
        # Call filter method with provider filter
        return self.filter(filter_params, db_session_local, skip, limit)

    def get_services_by_type(self, service_type: ServiceType, db: Optional[Session] = None, skip: int = 0, limit: int = 100) -> Dict[str, Any]:
        """
        Get services filtered by service type.
        
        Args:
            service_type: The service type to filter by
            db: Optional database session (uses default if not provided)
            skip: Number of records to skip (for pagination)
            limit: Maximum number of records to return (for pagination)
            
        Returns:
            Dictionary with services and pagination metadata
        """
        db_session_local = db or db_session
        
        # Create filter with service_type
        filter_params = {"service_type": service_type}
        
        # Call filter method with service_type filter
        return self.filter(filter_params, db_session_local, skip, limit)

    def get_active_services(self, db: Optional[Session] = None, skip: int = 0, limit: int = 100) -> Dict[str, Any]:
        """
        Get only active services.
        
        Args:
            db: Optional database session (uses default if not provided)
            skip: Number of records to skip (for pagination)
            limit: Maximum number of records to return (for pagination)
            
        Returns:
            Dictionary with active services and pagination metadata
        """
        db_session_local = db or db_session
        
        # Create filter with active=True
        filter_params = {"active": True}
        
        # Call filter method with active filter
        return self.filter(filter_params, db_session_local, skip, limit)

    def search_services(self, search_term: str, db: Optional[Session] = None, skip: int = 0, limit: int = 100) -> Dict[str, Any]:
        """
        Search services by name or description.
        
        Args:
            search_term: Term to search for in name and description
            db: Optional database session (uses default if not provided)
            skip: Number of records to skip (for pagination)
            limit: Maximum number of records to return (for pagination)
            
        Returns:
            Dictionary with matching services and pagination metadata
        """
        db_session_local = db or db_session
        
        # Create query with LIKE conditions on name and description
        query = db_session_local.query(self.model).filter(
            or_(
                self.model.name.ilike(f"%{search_term}%"),
                self.model.description.ilike(f"%{search_term}%")
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

    def filter_services(self, filter_params: CROServiceFilter, db: Optional[Session] = None, skip: int = 0, limit: int = 100) -> Dict[str, Any]:
        """
        Filter services based on multiple criteria.
        
        Args:
            filter_params: Filtering parameters
            db: Optional database session (uses default if not provided)
            skip: Number of records to skip (for pagination)
            limit: Maximum number of records to return (for pagination)
            
        Returns:
            Dictionary with filtered services and pagination metadata
        """
        db_session_local = db or db_session
        
        # Convert filter_params to dict
        filter_dict = filter_params.model_dump() if hasattr(filter_params, "model_dump") else filter_params
        
        # Build filter conditions
        filter_conditions = {}
        
        if filter_dict.get("name_contains"):
            filter_conditions["name"] = {"like": filter_dict["name_contains"]}
        
        if filter_dict.get("provider"):
            filter_conditions["provider"] = filter_dict["provider"]
        
        if filter_dict.get("service_type"):
            filter_conditions["service_type"] = filter_dict["service_type"]
        
        if filter_dict.get("active_only") is not None:
            filter_conditions["active"] = filter_dict["active_only"]
        
        if filter_dict.get("max_turnaround_days") is not None:
            filter_conditions["typical_turnaround_days"] = {"lte": filter_dict["max_turnaround_days"]}
        
        if filter_dict.get("max_price") is not None:
            filter_conditions["base_price"] = {"lte": filter_dict["max_price"]}
        
        # Call filter method with constructed filter
        return self.filter(filter_conditions, db_session_local, skip, limit)

    def activate_service(self, service: CROService, db: Optional[Session] = None) -> CROService:
        """
        Activate a CRO service.
        
        Args:
            service: The service to activate
            db: Optional database session (uses default if not provided)
            
        Returns:
            The activated service instance
        """
        db_session_local = db or db_session
        
        # Activate service
        service.activate()
        
        # Commit changes
        db_session_local.add(service)
        db_session_local.commit()
        db_session_local.refresh(service)
        
        return service

    def deactivate_service(self, service: CROService, db: Optional[Session] = None) -> CROService:
        """
        Deactivate a CRO service.
        
        Args:
            service: The service to deactivate
            db: Optional database session (uses default if not provided)
            
        Returns:
            The deactivated service instance
        """
        db_session_local = db or db_session
        
        # Deactivate service
        service.deactivate()
        
        # Commit changes
        db_session_local.add(service)
        db_session_local.commit()
        db_session_local.refresh(service)
        
        return service

    def update_specifications(self, service: CROService, specifications: Dict[str, Any], db: Optional[Session] = None) -> CROService:
        """
        Update specifications for a CRO service.
        
        Args:
            service: The service to update
            specifications: New specifications dictionary
            db: Optional database session (uses default if not provided)
            
        Returns:
            The updated service instance
        """
        db_session_local = db or db_session
        
        # Update specifications
        service.set_specifications(specifications)
        
        # Commit changes
        db_session_local.add(service)
        db_session_local.commit()
        db_session_local.refresh(service)
        
        return service

    def get_service_counts_by_type(self, db: Optional[Session] = None) -> List[Dict[str, Any]]:
        """
        Get count of services grouped by service type.
        
        Args:
            db: Optional database session (uses default if not provided)
            
        Returns:
            List of service type counts
        """
        db_session_local = db or db_session
        
        # Query to count services grouped by service_type
        query = (
            db_session_local.query(
                self.model.service_type,
                func.count(self.model.id)
            )
            .group_by(self.model.service_type)
        )
        
        # Execute query and format results
        result = [
            {
                "service_type": service_type.value if hasattr(service_type, "value") else str(service_type),
                "count": count
            }
            for service_type, count in query.all()
        ]
        
        return result

    def get_service_counts_by_provider(self, db: Optional[Session] = None) -> List[Dict[str, Any]]:
        """
        Get count of services grouped by provider.
        
        Args:
            db: Optional database session (uses default if not provided)
            
        Returns:
            List of provider counts
        """
        db_session_local = db or db_session
        
        # Query to count services grouped by provider
        query = (
            db_session_local.query(
                self.model.provider,
                func.count(self.model.id)
            )
            .group_by(self.model.provider)
        )
        
        # Execute query and format results
        result = [
            {
                "provider": provider,
                "count": count
            }
            for provider, count in query.all()
        ]
        
        return result


# Create an instance of CRUDCROService for use throughout the application
cro_service = CRUDCROService()