from typing import Generic, TypeVar, Type, List, Dict, Optional, Any, Union
from sqlalchemy.orm import Session
from sqlalchemy import select, func, or_, and_

from ..db.base_class import Base
from ..db.session import db_session

# Define type variables for generic typing
ModelType = TypeVar('ModelType', bound=Base)
CreateSchemaType = TypeVar('CreateSchemaType')
UpdateSchemaType = TypeVar('UpdateSchemaType')


class CRUDBase(Generic[ModelType, CreateSchemaType, UpdateSchemaType]):
    """
    Base class for CRUD operations.
    
    Provides generic Create, Read, Update, Delete operations on SQLAlchemy models.
    This class is designed to be extended by model-specific CRUD classes to provide
    a consistent interface for database operations across the application.
    """

    def __init__(self, model: Type[ModelType]):
        """
        Initialize CRUD base class with a SQLAlchemy model.
        
        Args:
            model: The SQLAlchemy model class
        """
        self.model = model

    def get(self, id: Any, db: Optional[Session] = None) -> Optional[ModelType]:
        """
        Get a single record by ID.
        
        Args:
            id: The ID of the record to get
            db: Optional database session (uses default if not provided)
            
        Returns:
            The model instance if found, None otherwise
        """
        db_session_local = db or db_session
        return db_session_local.query(self.model).filter(self.model.id == id).first()
    
    def get_multi(
        self, 
        db: Optional[Session] = None, 
        skip: int = 0, 
        limit: int = 100
    ) -> Dict[str, Any]:
        """
        Get multiple records with pagination.
        
        Args:
            db: Optional database session (uses default if not provided)
            skip: Number of records to skip (for pagination)
            limit: Maximum number of records to return (for pagination)
            
        Returns:
            Dictionary with items and pagination metadata
        """
        db_session_local = db or db_session
        
        # Get items with pagination
        query = db_session_local.query(self.model)
        total = query.count()
        items = query.offset(skip).limit(limit).all()
        
        # Return items with pagination metadata
        return {
            "items": items,
            "total": total,
            "page": skip // limit + 1 if limit > 0 else 1,
            "size": limit,
            "pages": (total + limit - 1) // limit if limit > 0 else 1
        }
    
    def create(
        self, 
        obj_in: Union[CreateSchemaType, Dict[str, Any]], 
        db: Optional[Session] = None
    ) -> ModelType:
        """
        Create a new record.
        
        Args:
            obj_in: Input data for the new record (Pydantic model or dict)
            db: Optional database session (uses default if not provided)
            
        Returns:
            The created model instance
        """
        db_session_local = db or db_session
        
        # Convert to dict if it's a Pydantic model
        if not isinstance(obj_in, dict):
            obj_in_data = obj_in.model_dump()
        else:
            obj_in_data = obj_in
        
        # Create model instance from data
        db_obj = self.model.from_dict(obj_in_data)
        
        # Add to session and commit
        db_session_local.add(db_obj)
        db_session_local.commit()
        db_session_local.refresh(db_obj)
        
        return db_obj
    
    def update(
        self,
        db_obj: ModelType,
        obj_in: Union[UpdateSchemaType, Dict[str, Any]],
        db: Optional[Session] = None
    ) -> ModelType:
        """
        Update an existing record.
        
        Args:
            db_obj: Existing model instance to update
            obj_in: Input data with updates (Pydantic model or dict)
            db: Optional database session (uses default if not provided)
            
        Returns:
            The updated model instance
        """
        db_session_local = db or db_session
        
        # Convert to dict if it's a Pydantic model
        if not isinstance(obj_in, dict):
            obj_in_data = obj_in.model_dump()
        else:
            obj_in_data = obj_in
        
        # Update model instance from data
        for key, value in obj_in_data.items():
            if hasattr(db_obj, key):
                setattr(db_obj, key, value)
        
        # Commit changes
        db_session_local.add(db_obj)
        db_session_local.commit()
        db_session_local.refresh(db_obj)
        
        return db_obj
    
    def remove(self, id: Any, db: Optional[Session] = None) -> ModelType:
        """
        Delete a record.
        
        Args:
            id: The ID of the record to delete
            db: Optional database session (uses default if not provided)
            
        Returns:
            The deleted model instance
        """
        db_session_local = db or db_session
        
        # Get the object
        db_obj = db_session_local.query(self.model).get(id)
        
        if db_obj:
            # Delete the object
            db_session_local.delete(db_obj)
            db_session_local.commit()
        
        return db_obj
    
    def filter(
        self,
        filter_params: Dict[str, Any],
        db: Optional[Session] = None,
        skip: int = 0,
        limit: int = 100
    ) -> Dict[str, Any]:
        """
        Filter records based on criteria.
        
        Args:
            filter_params: Dictionary with filter parameters
            db: Optional database session (uses default if not provided)
            skip: Number of records to skip (for pagination)
            limit: Maximum number of records to return (for pagination)
            
        Returns:
            Dictionary with filtered items and pagination metadata
        """
        db_session_local = db or db_session
        
        # Start with a base query
        query = db_session_local.query(self.model)
        
        # Apply filters
        filter_conditions = []
        for key, value in filter_params.items():
            if hasattr(self.model, key):
                # Handle different filter types
                if isinstance(value, list):
                    # If value is a list, use "in" operator
                    filter_conditions.append(getattr(self.model, key).in_(value))
                elif isinstance(value, dict):
                    # If value is a dict, handle operators like gt, lt, etc.
                    for op, op_value in value.items():
                        if op == "gt":
                            filter_conditions.append(getattr(self.model, key) > op_value)
                        elif op == "lt":
                            filter_conditions.append(getattr(self.model, key) < op_value)
                        elif op == "gte":
                            filter_conditions.append(getattr(self.model, key) >= op_value)
                        elif op == "lte":
                            filter_conditions.append(getattr(self.model, key) <= op_value)
                        elif op == "eq":
                            filter_conditions.append(getattr(self.model, key) == op_value)
                        elif op == "neq":
                            filter_conditions.append(getattr(self.model, key) != op_value)
                        elif op == "like":
                            filter_conditions.append(getattr(self.model, key).like(f"%{op_value}%"))
                else:
                    # Simple equality
                    filter_conditions.append(getattr(self.model, key) == value)
        
        # Apply all filters
        if filter_conditions:
            query = query.filter(and_(*filter_conditions))
        
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
    
    def count(self, db: Optional[Session] = None) -> int:
        """
        Count total records.
        
        Args:
            db: Optional database session (uses default if not provided)
            
        Returns:
            Total count of records
        """
        db_session_local = db or db_session
        return db_session_local.query(self.model).count()
    
    def exists(self, id: Any, db: Optional[Session] = None) -> bool:
        """
        Check if a record exists by ID.
        
        Args:
            id: The ID to check for existence
            db: Optional database session (uses default if not provided)
            
        Returns:
            True if record exists, False otherwise
        """
        db_session_local = db or db_session
        query = select(func.count()).select_from(self.model).where(self.model.id == id)
        result = db_session_local.execute(query).scalar()
        return result > 0