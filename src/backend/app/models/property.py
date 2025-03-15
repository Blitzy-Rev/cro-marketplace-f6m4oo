"""
Property Model Module

This module defines the Property model for the Molecular Data Management and
CRO Integration Platform. It includes the SQLAlchemy ORM model for property definitions
and utilities for creating and managing standardized molecular properties.

The Property model is central to the system's ability to validate, filter, and predict
molecular properties across various workflows including CSV imports, library management,
and CRO submissions.
"""

from datetime import datetime
from sqlalchemy import Column, String, Text, Float, Boolean, JSON, Enum
from sqlalchemy.orm import relationship, validates

from ..db.base_class import Base
from ..constants.molecule_properties import (
    PropertyType,
    PropertyCategory,
    PROPERTY_UNITS,
    PROPERTY_RANGES
)
from ..utils.validators import validate_property_value


class Property(Base):
    """
    SQLAlchemy model representing a standard property definition for molecules.
    
    This model defines the metadata for molecular properties including their
    type, category, units, and validation ranges. It is used throughout the
    system for CSV import mapping, property validation, and AI prediction.
    
    Attributes:
        name (str): Unique identifier for the property (snake_case)
        display_name (str): Human-readable name for display in UI
        property_type (PropertyType): Data type of the property (string, numeric, etc.)
        category (PropertyCategory): Category of the property (physical, chemical, etc.)
        units (str): Units of measurement for the property (if applicable)
        min_value (float): Minimum valid value for the property (if applicable)
        max_value (float): Maximum valid value for the property (if applicable)
        description (str): Detailed description of the property
        is_required (bool): Whether the property is required for all molecules
        is_filterable (bool): Whether the property can be used for filtering molecules
        is_predictable (bool): Whether the property can be predicted by AI models
        metadata (dict): Additional metadata stored as JSON
    """
    
    # Basic property information
    name = Column(String(100), unique=True, nullable=False, index=True)
    display_name = Column(String(100), nullable=False)
    property_type = Column(Enum(PropertyType), nullable=False)
    category = Column(Enum(PropertyCategory), nullable=False)
    units = Column(String(50), nullable=True)
    
    # Validation range
    min_value = Column(Float, nullable=True)
    max_value = Column(Float, nullable=True)
    
    # Additional metadata
    description = Column(Text, nullable=True)
    is_required = Column(Boolean, default=False)
    is_filterable = Column(Boolean, default=False)
    is_predictable = Column(Boolean, default=False)
    metadata = Column(JSON, nullable=True)
    
    @validates('name')
    def validate_name(self, key, name):
        """
        Validates property name format.
        
        Property names must be non-empty and contain only lowercase alphanumeric
        characters and underscores (snake_case).
        
        Args:
            key (str): The attribute name being validated
            name (str): The property name value
            
        Returns:
            str: Validated property name
            
        Raises:
            ValueError: If the name is invalid
        """
        if name is None or not name.strip():
            raise ValueError("Property name cannot be empty")
        
        # Convert to lowercase with underscores (snake_case)
        name = name.strip().lower()
        
        # Ensure name contains only alphanumeric and underscore characters
        if not all(c.isalnum() or c == '_' for c in name):
            raise ValueError("Property name must contain only alphanumeric and underscore characters")
        
        return name
    
    @validates('min_value', 'max_value')
    def validate_range(self, key, value):
        """
        Validates that min_value is less than max_value if both are set.
        
        Args:
            key (str): The attribute name being validated
            value (float): The value to validate
            
        Returns:
            float: Validated value
            
        Raises:
            ValueError: If min_value >= max_value when both are set
        """
        if value is None:
            return value
        
        if key == 'max_value' and self.min_value is not None and value <= self.min_value:
            raise ValueError(f"max_value ({value}) must be greater than min_value ({self.min_value})")
        
        if key == 'min_value' and self.max_value is not None and value >= self.max_value:
            raise ValueError(f"min_value ({value}) must be less than max_value ({self.max_value})")
        
        return value
    
    def get_standard_units(self):
        """
        Gets standard units for this property if defined in PROPERTY_UNITS.
        
        Returns:
            str: Standard units string or empty string if not defined
        """
        return PROPERTY_UNITS.get(self.name, "")
    
    def get_value_range(self):
        """
        Gets the valid value range for this property.
        
        First checks if explicit min/max values are set on the property instance.
        If not, checks if standard ranges are defined in PROPERTY_RANGES.
        
        Returns:
            dict: Dictionary with min and max values
        """
        # If explicit min/max values are set on the property, use those
        if self.min_value is not None or self.max_value is not None:
            return {
                "min": self.min_value,
                "max": self.max_value
            }
        
        # Otherwise check if standard ranges are defined
        if self.name in PROPERTY_RANGES:
            return PROPERTY_RANGES[self.name]
        
        # If no ranges defined, return empty dict
        return {"min": None, "max": None}
    
    def validate_value(self, value):
        """
        Validates a value for this property based on its type and range.
        
        Uses the validate_property_value utility function to perform validation
        based on the property's type and value range.
        
        Args:
            value: The value to validate
            
        Returns:
            bool: True if value is valid, False otherwise
        """
        return validate_property_value(
            value, 
            self.name, 
            self.property_type, 
            raise_exception=False
        )
    
    def to_dict(self):
        """
        Converts property to dictionary representation.
        
        Extends the Base class to_dict method to handle enum serialization.
        
        Returns:
            dict: Dictionary representation of property
        """
        property_dict = super().to_dict()
        
        # Convert enum values to strings for JSON serialization
        if self.property_type:
            property_dict['property_type'] = self.property_type.value
        
        if self.category:
            property_dict['category'] = self.category.value
        
        return property_dict
    
    @classmethod
    def from_dict(cls, data, instance=None):
        """
        Creates or updates a Property instance from dictionary data.
        
        Handles converting string enum values to their respective Enum instances.
        
        Args:
            data (dict): Dictionary containing property attributes
            instance (Property, optional): Existing Property instance to update
            
        Returns:
            Property: Property instance with data applied
        """
        if instance is None:
            instance = cls()
        
        # Handle enum values
        if 'property_type' in data and isinstance(data['property_type'], str):
            data['property_type'] = PropertyType(data['property_type'])
            
        if 'category' in data and isinstance(data['category'], str):
            data['category'] = PropertyCategory(data['category'])
        
        return super(Property, cls).from_dict(data, instance)


class PropertyDefinition:
    """
    Helper class for creating standard property definitions.
    
    This utility class provides methods for initializing the standard
    property definitions in the database and retrieving properties
    based on various criteria.
    """
    
    @classmethod
    def create_standard_properties(cls, session):
        """
        Creates standard property definitions from STANDARD_PROPERTIES.
        
        Checks if each standard property already exists in the database
        and creates it if not. This ensures that the system has all required
        standard properties available.
        
        Args:
            session: SQLAlchemy database session
            
        Returns:
            list: List of created Property instances
        """
        from ..constants.molecule_properties import STANDARD_PROPERTIES
        
        created_properties = []
        
        for name, prop_data in STANDARD_PROPERTIES.items():
            # Check if property already exists
            existing_property = session.query(Property).filter(Property.name == name).first()
            
            if not existing_property:
                # Create new property
                prop_data = prop_data.copy()  # Create a copy to avoid modifying the original
                prop_data['name'] = name
                new_property = Property.from_dict(prop_data)
                session.add(new_property)
                created_properties.append(new_property)
        
        # Commit changes to DB
        if created_properties:
            session.commit()
        
        return created_properties
    
    @classmethod
    def get_property_by_name(cls, session, name):
        """
        Gets a property definition by name.
        
        Args:
            session: SQLAlchemy database session
            name (str): Property name
            
        Returns:
            Property: Property instance or None if not found
        """
        return session.query(Property).filter(Property.name == name).first()
    
    @classmethod
    def get_properties_by_category(cls, session, category):
        """
        Gets property definitions by category.
        
        Args:
            session: SQLAlchemy database session
            category (PropertyCategory): PropertyCategory enum value
            
        Returns:
            list: List of Property instances in the category
        """
        return session.query(Property).filter(Property.category == category).all()
    
    @classmethod
    def get_filterable_properties(cls, session):
        """
        Gets property definitions that are filterable.
        
        Filterable properties can be used in molecule search and filtering.
        
        Args:
            session: SQLAlchemy database session
            
        Returns:
            list: List of filterable Property instances
        """
        return session.query(Property).filter(Property.is_filterable == True).all()
    
    @classmethod
    def get_predictable_properties(cls, session):
        """
        Gets property definitions that are predictable by AI.
        
        Predictable properties can be calculated using the AI prediction engine.
        
        Args:
            session: SQLAlchemy database session
            
        Returns:
            list: List of predictable Property instances
        """
        return session.query(Property).filter(Property.is_predictable == True).all()