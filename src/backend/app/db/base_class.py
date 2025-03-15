from sqlalchemy.ext.declarative import declarative_base, as_declarative, declared_attr
from sqlalchemy import Column, UUID, DateTime
from sqlalchemy.sql import func
import uuid
import datetime

@as_declarative()
class Base:
    """
    Base class for all database models in the Molecular Data Management and CRO Integration Platform.
    
    Provides common functionality for:
    - Automatic UUID primary key generation
    - Timestamp tracking (created_at, updated_at)
    - JSON serialization through to_dict/from_dict methods
    """
    
    # Automatically generate table name from class name
    @declared_attr
    @classmethod
    def __tablename__(cls):
        """
        Derives the table name from the class name.
        
        Returns:
            Lowercase version of the class name as the table name.
        """
        return cls.__name__.lower()
    
    # Common model attributes
    id = Column(UUID, primary_key=True, default=uuid.uuid4, index=True)
    created_at = Column(DateTime, default=func.now(), nullable=False)
    updated_at = Column(DateTime, default=func.now(), onupdate=func.now(), nullable=False)
    
    def to_dict(self):
        """
        Converts model instance to a dictionary representation.
        
        Returns:
            Dictionary with column names as keys and column values as values.
        """
        result = {}
        for column in self.__table__.columns:
            value = getattr(self, column.name)
            # Handle datetime conversion for JSON serialization
            if isinstance(value, (datetime.date, datetime.datetime)):
                value = value.isoformat()
            # Handle UUID conversion for JSON serialization
            elif isinstance(value, uuid.UUID):
                value = str(value)
            result[column.name] = value
        return result
    
    @classmethod
    def from_dict(cls, data, instance=None):
        """
        Creates or updates a model instance from dictionary data.
        
        Args:
            data: Dictionary containing model attributes
            instance: Optional existing instance to update (if None, creates new instance)
            
        Returns:
            Model instance with data applied
        """
        if instance is None:
            instance = cls()
        
        for key, value in data.items():
            if hasattr(instance, key):
                setattr(instance, key, value)
        
        return instance