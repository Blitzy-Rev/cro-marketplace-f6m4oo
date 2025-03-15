from typing import List, Dict, Optional, Any, Union
from sqlalchemy.orm import Session
from sqlalchemy import select, and_, or_

from .base import CRUDBase
from ..models.property import Property, PropertyDefinition
from ..schemas.property import PropertyCreate, PropertyUpdate, PropertyFilter
from ..constants.molecule_properties import PropertyType, PropertyCategory
from ..db.session import db_session
from ..utils.validators import validate_property_value


class CRUDProperty(CRUDBase[Property, PropertyCreate, PropertyUpdate]):
    """CRUD operations for Property model"""

    def __init__(self):
        """Initialize the CRUD property class"""
        super().__init__(Property)

    def get_by_name(self, name: str, db: Optional[Session] = None) -> Optional[Property]:
        """
        Get a property by its name
        
        Args:
            name: The name of the property to get
            db: Optional database session (uses default if not provided)
            
        Returns:
            Property instance if found, None otherwise
        """
        db_session_local = db or db_session
        return db_session_local.query(Property).filter(Property.name == name).first()
    
    def get_by_names(self, names: List[str], db: Optional[Session] = None) -> List[Property]:
        """
        Get multiple properties by their names
        
        Args:
            names: List of property names to get
            db: Optional database session (uses default if not provided)
            
        Returns:
            List of found Property instances
        """
        db_session_local = db or db_session
        return db_session_local.query(Property).filter(Property.name.in_(names)).all()
    
    def get_by_category(self, category: PropertyCategory, db: Optional[Session] = None) -> List[Property]:
        """
        Get properties by category
        
        Args:
            category: The PropertyCategory to filter by
            db: Optional database session (uses default if not provided)
            
        Returns:
            List of Property instances in the category
        """
        db_session_local = db or db_session
        return db_session_local.query(Property).filter(Property.category == category).all()
    
    def get_filterable(self, db: Optional[Session] = None) -> List[Property]:
        """
        Get properties that are filterable
        
        Args:
            db: Optional database session (uses default if not provided)
            
        Returns:
            List of filterable Property instances
        """
        db_session_local = db or db_session
        return db_session_local.query(Property).filter(Property.is_filterable == True).all()
    
    def get_predictable(self, db: Optional[Session] = None) -> List[Property]:
        """
        Get properties that can be predicted by AI
        
        Args:
            db: Optional database session (uses default if not provided)
            
        Returns:
            List of predictable Property instances
        """
        db_session_local = db or db_session
        return db_session_local.query(Property).filter(Property.is_predictable == True).all()
    
    def get_required(self, db: Optional[Session] = None) -> List[Property]:
        """
        Get properties that are required for molecules
        
        Args:
            db: Optional database session (uses default if not provided)
            
        Returns:
            List of required Property instances
        """
        db_session_local = db or db_session
        return db_session_local.query(Property).filter(Property.is_required == True).all()
    
    def create_standard_properties(self, db: Optional[Session] = None) -> List[Property]:
        """
        Create standard property definitions if they don't exist
        
        Args:
            db: Optional database session (uses default if not provided)
            
        Returns:
            List of created Property instances
        """
        db_session_local = db or db_session
        return PropertyDefinition.create_standard_properties(db_session_local)
    
    def filter_properties(
        self,
        filter_params: PropertyFilter,
        db: Optional[Session] = None,
        skip: int = 0,
        limit: int = 100
    ) -> Dict[str, Any]:
        """
        Filter properties based on criteria
        
        Args:
            filter_params: Filtering parameters
            db: Optional database session (uses default if not provided)
            skip: Number of records to skip (for pagination)
            limit: Maximum number of records to return (for pagination)
            
        Returns:
            Dictionary with filtered items and pagination metadata
        """
        db_session_local = db or db_session
        
        # Start with a base query
        query = db_session_local.query(Property)
        
        # Apply filters
        if filter_params.name:
            query = query.filter(Property.name.ilike(f"%{filter_params.name}%"))
        
        if filter_params.property_type:
            query = query.filter(Property.property_type == filter_params.property_type)
        
        if filter_params.category:
            query = query.filter(Property.category == filter_params.category)
        
        if filter_params.is_required is not None:
            query = query.filter(Property.is_required == filter_params.is_required)
        
        if filter_params.is_filterable is not None:
            query = query.filter(Property.is_filterable == filter_params.is_filterable)
        
        if filter_params.is_predictable is not None:
            query = query.filter(Property.is_predictable == filter_params.is_predictable)
        
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
    
    def validate_property(self, property_name: str, value: Any, db: Optional[Session] = None) -> bool:
        """
        Validate a property value against its definition
        
        Args:
            property_name: Name of the property to validate
            value: Value to validate
            db: Optional database session (uses default if not provided)
            
        Returns:
            True if value is valid, False otherwise
        """
        db_session_local = db or db_session
        
        # Get property definition
        property_def = self.get_by_name(property_name, db=db_session_local)
        
        if not property_def:
            return False
        
        # Validate using the property's validate_value method
        return property_def.validate_value(value)


# Create a singleton instance for application-wide use
property = CRUDProperty()