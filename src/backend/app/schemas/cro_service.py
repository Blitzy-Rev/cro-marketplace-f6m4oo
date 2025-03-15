"""
Defines Pydantic schemas for CRO (Contract Research Organization) services in the
Molecular Data Management and CRO Integration Platform.

These schemas are used for data validation, serialization, and documentation of API
endpoints related to CRO services.
"""

from typing import Optional, List, Dict, Any
from uuid import UUID
from pydantic import BaseModel, Field, validator, constr, confloat, conint

from ..models.cro_service import ServiceType


class CROServiceBase(BaseModel):
    """
    Base Pydantic model for CRO services with common fields.
    
    Defines the data structure and validation rules for CRO service attributes
    that are shared across create and update operations.
    """
    name: constr(min_length=1, max_length=100)
    description: Optional[str] = None
    provider: constr(min_length=1, max_length=255)
    service_type: ServiceType
    base_price: confloat(gt=0)
    price_currency: constr(min_length=3, max_length=3) = "USD"
    typical_turnaround_days: conint(gt=0)
    specifications: Optional[Dict[str, Any]] = None
    active: bool = True
    
    @validator('base_price', pre=True)
    def validate_base_price(cls, v):
        """
        Validates that the base price is positive.
        
        Args:
            v: The price value to validate
            
        Returns:
            Validated price value
            
        Raises:
            ValueError: If price is not positive
        """
        if v <= 0:
            raise ValueError("Base price must be greater than zero")
        return v
    
    @validator('typical_turnaround_days', pre=True)
    def validate_turnaround_days(cls, v):
        """
        Validates that the turnaround days is positive.
        
        Args:
            v: The number of days to validate
            
        Returns:
            Validated days value
            
        Raises:
            ValueError: If days is not positive
        """
        if v <= 0:
            raise ValueError("Turnaround days must be greater than zero")
        return v


class CROServiceCreate(CROServiceBase):
    """
    Schema for creating a new CRO service.
    
    Extends the base schema with any fields specific to service creation.
    """
    class Config:
        pass


class CROServiceUpdate(BaseModel):
    """
    Schema for updating an existing CRO service.
    
    All fields are optional to allow partial updates.
    """
    name: Optional[constr(min_length=1, max_length=100)] = None
    description: Optional[str] = None
    provider: Optional[constr(min_length=1, max_length=255)] = None
    service_type: Optional[ServiceType] = None
    base_price: Optional[confloat(gt=0)] = None
    price_currency: Optional[constr(min_length=3, max_length=3)] = None
    typical_turnaround_days: Optional[conint(gt=0)] = None
    specifications: Optional[Dict[str, Any]] = None
    active: Optional[bool] = None
    
    class Config:
        pass


class CROService(CROServiceBase):
    """
    Schema for CRO service responses, including ID and timestamps.
    
    Extends the base schema with database-generated fields.
    """
    id: UUID
    created_at: str
    updated_at: str
    
    class Config:
        orm_mode = True


class CROServiceFilter(BaseModel):
    """
    Schema for filtering CRO services in list endpoints.
    
    Defines the parameters that can be used to filter CRO services.
    """
    name_contains: Optional[str] = None
    provider: Optional[str] = None
    service_type: Optional[ServiceType] = None
    active_only: Optional[bool] = True
    max_turnaround_days: Optional[int] = None
    max_price: Optional[float] = None
    
    class Config:
        pass