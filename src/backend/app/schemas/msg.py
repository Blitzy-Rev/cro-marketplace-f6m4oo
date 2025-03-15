from pydantic import BaseModel, Field
from typing import Optional, Dict, Any, List

class Msg(BaseModel):
    """
    Simple message response schema for basic API responses.
    
    This model provides a standardized format for simple message responses
    across all API endpoints.
    
    Attributes:
        message: A descriptive message to be returned to the client
    """
    message: str = Field(..., description="Response message")


class ResponseMsg(BaseModel):
    """
    Enhanced response schema with status and optional data payload.
    
    This model provides a standardized format for API responses that include
    a status indicator and optional data payload.
    
    Attributes:
        status: Status of the response (e.g., "success", "error", "warning")
        message: A descriptive message to be returned to the client
        data: Optional dictionary containing additional response data
    """
    status: str = Field(..., description="Response status")
    message: str = Field(..., description="Response message")
    data: Optional[Dict[str, Any]] = Field(None, description="Optional response data")


class ErrorResponseMsg(BaseModel):
    """
    Standardized error response schema for API error handling.
    
    This model provides a consistent format for error responses across all
    API endpoints, supporting detailed error information and validation errors.
    
    Attributes:
        error_code: A machine-readable error code
        message: A human-readable error message
        details: Optional dictionary containing additional error details
        validation_errors: Optional list of validation errors for form submissions
        error_id: Optional unique identifier for the error instance (for tracking)
    """
    error_code: str = Field(..., description="Machine-readable error code")
    message: str = Field(..., description="Human-readable error message")
    details: Optional[Dict[str, Any]] = Field(None, description="Additional error details")
    validation_errors: Optional[List[Dict[str, Any]]] = Field(None, description="Validation errors")
    error_id: Optional[str] = Field(None, description="Unique error identifier for tracking")