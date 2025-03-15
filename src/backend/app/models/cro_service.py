"""
CRO Service model definition for the Molecular Data Management and CRO Integration Platform.

This module defines the data model for CRO (Contract Research Organization) services 
that can be selected by pharmaceutical users when submitting molecules for experimental testing.
"""

from enum import Enum
import json

from sqlalchemy import Column, String, Float, Integer, Text, Boolean, JSON, Enum as SQLAlchemyEnum
from sqlalchemy.orm import relationship, validates

from ..db.base_class import Base


class ServiceType(Enum):
    """
    Enumeration of available CRO service types.
    
    Defines the categorization of services offered by Contract Research Organizations (CROs).
    These types help in organizing and filtering available services for molecule testing.
    """
    BINDING_ASSAY = "BINDING_ASSAY"
    ADME = "ADME"
    SOLUBILITY = "SOLUBILITY"
    PERMEABILITY = "PERMEABILITY"
    METABOLIC_STABILITY = "METABOLIC_STABILITY"
    TOXICITY = "TOXICITY"
    CUSTOM = "CUSTOM"


class CROService(Base):
    """
    SQLAlchemy model representing a service offered by a Contract Research Organization.
    
    This model stores details about experimental services that can be selected
    during the CRO submission process, including pricing, turnaround time, and
    service specifications.
    """
    # Basic information
    name = Column(String(100), nullable=False, index=True)
    description = Column(Text, nullable=True)
    provider = Column(String(255), nullable=False, index=True)
    service_type = Column(SQLAlchemyEnum(ServiceType), nullable=False, index=True)
    
    # Pricing and timing
    base_price = Column(Float, nullable=False)
    price_currency = Column(String(3), nullable=False, default="USD")
    typical_turnaround_days = Column(Integer, nullable=False)
    
    # Additional details
    specifications = Column(JSON, nullable=True)
    active = Column(Boolean, nullable=False, default=True)
    
    # Relationships
    submissions = relationship("Submission", back_populates="cro_service")
    
    @validates("base_price")
    def validate_base_price(self, key, price):
        """
        Validates that the base price is positive.
        
        Args:
            key: The attribute name being validated
            price: The price value to validate
            
        Returns:
            Validated price value
            
        Raises:
            ValueError: If price is not positive
        """
        if price <= 0:
            raise ValueError("Base price must be greater than zero")
        return price
    
    @validates("typical_turnaround_days")
    def validate_turnaround_days(self, key, days):
        """
        Validates that the turnaround days is positive.
        
        Args:
            key: The attribute name being validated
            days: The number of days to validate
            
        Returns:
            Validated days value
            
        Raises:
            ValueError: If days is not positive
        """
        if days <= 0:
            raise ValueError("Turnaround days must be greater than zero")
        return days
    
    @classmethod
    def create(cls, name, provider, service_type, base_price, typical_turnaround_days, 
               description=None, price_currency="USD", specifications=None, active=True):
        """
        Creates a new CRO service instance.
        
        Args:
            name: Name of the service
            provider: Name of the CRO provider offering this service
            service_type: Type of service (from ServiceType enum)
            base_price: Base price for the service
            typical_turnaround_days: Typical number of days for results
            description: Optional detailed description of the service
            price_currency: Currency code for the price (default: USD)
            specifications: Optional dictionary of service specifications
            active: Whether the service is currently active (default: True)
            
        Returns:
            New CROService instance
        """
        return cls(
            name=name,
            provider=provider,
            service_type=service_type,
            base_price=base_price,
            typical_turnaround_days=typical_turnaround_days,
            description=description,
            price_currency=price_currency,
            specifications=specifications,
            active=active
        )
    
    def update(self, data):
        """
        Updates an existing CRO service with new values.
        
        Args:
            data: Dictionary of attributes to update
            
        Returns:
            Updated CROService instance
        """
        for key, value in data.items():
            # Skip protected attributes
            if key not in ("id", "created_at", "updated_at") and hasattr(self, key):
                setattr(self, key, value)
        return self
    
    def get_specifications(self):
        """
        Gets the service specifications as a dictionary.
        
        Returns:
            Service specifications as a dictionary
        """
        if self.specifications is None:
            return {}
        
        if isinstance(self.specifications, dict):
            return self.specifications
        
        try:
            # Handle case where specifications might be stored as JSON string
            return json.loads(self.specifications)
        except (TypeError, json.JSONDecodeError):
            return {}
    
    def set_specifications(self, specifications):
        """
        Sets the service specifications from a dictionary.
        
        Args:
            specifications: Dictionary of specifications to set
        """
        self.specifications = specifications
    
    def activate(self):
        """
        Activates the CRO service.
        """
        self.active = True
    
    def deactivate(self):
        """
        Deactivates the CRO service.
        """
        self.active = False
    
    def to_dict(self, include_relationships=False):
        """
        Converts CRO service to dictionary representation.
        
        Args:
            include_relationships: Whether to include related objects
            
        Returns:
            Dictionary representation of the CRO service
        """
        # Get base dictionary from parent class
        result = super().to_dict()
        
        # Convert enum to string
        if self.service_type is not None:
            result["service_type"] = self.service_type.value
        
        # Include parsed specifications
        result["specifications"] = self.get_specifications()
        
        # Include relationships if requested
        if include_relationships and self.submissions:
            result["submissions"] = [str(submission.id) for submission in self.submissions]
        
        return result