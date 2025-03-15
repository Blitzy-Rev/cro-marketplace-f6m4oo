"""
AI Engine Integration Exceptions

This module defines custom exception classes for the AI Engine integration module.
These exceptions handle specific error scenarios that can occur when interacting
with the external AI prediction service, providing structured error handling and
appropriate status codes.
"""

from typing import Dict, Optional, Any

from ...core.exceptions import IntegrationException, ServiceUnavailableException
from ...constants.error_messages import INTEGRATION_ERRORS, PREDICTION_ERRORS


class AIEngineException(IntegrationException):
    """Base exception class for all AI Engine integration errors."""

    def __init__(
        self,
        message: str,
        error_code: Optional[str] = None,
        details: Optional[Dict[str, Any]] = None
    ):
        """Initialize AI Engine exception with error details.
        
        Args:
            message: Human-readable error message
            error_code: Machine-readable error code
            details: Additional error details
        """
        details = details or {}
        self.service_name = "AI Engine"
        if "service_name" not in details:
            details["service_name"] = self.service_name
            
        super().__init__(
            message=message,
            error_code=error_code,
            details=details,
            service_name=self.service_name
        )


class AIEngineConnectionError(AIEngineException):
    """Exception raised when connection to the AI Engine fails."""

    def __init__(
        self,
        message: str = None,
        details: Optional[Dict[str, Any]] = None
    ):
        """Initialize connection error exception.
        
        Args:
            message: Human-readable error message
            details: Additional error details
        """
        message = message or INTEGRATION_ERRORS["AI_ENGINE_CONNECTION_FAILED"]
        super().__init__(
            message=message,
            error_code="ai_engine_connection_failed",
            details=details
        )
        self.status_code = 503  # Service Unavailable


class AIEngineTimeoutError(AIEngineException):
    """Exception raised when a request to the AI Engine times out."""

    def __init__(
        self,
        message: str = None,
        timeout_seconds: Optional[int] = None,
        details: Optional[Dict[str, Any]] = None
    ):
        """Initialize timeout error exception.
        
        Args:
            message: Human-readable error message
            timeout_seconds: Number of seconds before timeout occurred
            details: Additional error details
        """
        message = message or INTEGRATION_ERRORS["INTEGRATION_TIMEOUT"]
        details = details or {}
        if timeout_seconds is not None:
            details["timeout_seconds"] = timeout_seconds
            
        super().__init__(
            message=message,
            error_code="ai_engine_timeout",
            details=details
        )
        self.status_code = 504  # Gateway Timeout
        self.timeout_seconds = timeout_seconds


class AIEngineResponseError(AIEngineException):
    """Exception raised when the AI Engine returns an error response."""

    def __init__(
        self,
        message: str = None,
        response_status: Optional[int] = None,
        response_body: Optional[Dict[str, Any]] = None,
        details: Optional[Dict[str, Any]] = None
    ):
        """Initialize response error exception.
        
        Args:
            message: Human-readable error message
            response_status: HTTP status code from the AI Engine
            response_body: Response body from the AI Engine
            details: Additional error details
        """
        message = message or INTEGRATION_ERRORS["EXTERNAL_API_ERROR"]
        details = details or {}
        if response_status is not None:
            details["response_status"] = response_status
        if response_body is not None:
            details["response_body"] = response_body
            
        super().__init__(
            message=message,
            error_code="ai_engine_response_error",
            details=details
        )
        self.status_code = 502  # Bad Gateway
        self.response_status = response_status
        self.response_body = response_body


class AIServiceUnavailableError(ServiceUnavailableException):
    """Exception raised when the AI Engine service is unavailable."""

    def __init__(
        self,
        message: str = None,
        details: Optional[Dict[str, Any]] = None
    ):
        """Initialize service unavailable exception.
        
        Args:
            message: Human-readable error message
            details: Additional error details
        """
        message = message or PREDICTION_ERRORS["PREDICTION_SERVICE_UNAVAILABLE"]
        super().__init__(
            message=message,
            service_name="AI Engine",
            error_code="ai_service_unavailable",
            details=details
        )


class BatchSizeExceededError(AIEngineException):
    """Exception raised when the batch size for prediction exceeds the maximum allowed."""

    def __init__(
        self,
        message: str = None,
        batch_size: int = 0,
        max_batch_size: int = 0,
        details: Optional[Dict[str, Any]] = None
    ):
        """Initialize batch size exceeded exception.
        
        Args:
            message: Human-readable error message
            batch_size: Actual batch size that was provided
            max_batch_size: Maximum allowed batch size
            details: Additional error details
        """
        message = message or PREDICTION_ERRORS["PREDICTION_LIMIT_EXCEEDED"]
        details = details or {}
        details.update({
            "batch_size": batch_size,
            "max_batch_size": max_batch_size
        })
            
        super().__init__(
            message=message,
            error_code="batch_size_exceeded",
            details=details
        )
        self.status_code = 400  # Bad Request
        self.batch_size = batch_size
        self.max_batch_size = max_batch_size


class UnsupportedPropertyError(AIEngineException):
    """Exception raised when a requested property is not supported by the AI Engine."""

    def __init__(
        self,
        message: str = None,
        property_name: Optional[str] = None,
        details: Optional[Dict[str, Any]] = None
    ):
        """Initialize unsupported property exception.
        
        Args:
            message: Human-readable error message
            property_name: Name of the unsupported property
            details: Additional error details
        """
        message = message or PREDICTION_ERRORS["UNSUPPORTED_PROPERTY"]
        details = details or {}
        if property_name is not None:
            details["property_name"] = property_name
            
        super().__init__(
            message=message,
            error_code="unsupported_property",
            details=details
        )
        self.status_code = 400  # Bad Request
        self.property_name = property_name


class PredictionJobNotFoundError(AIEngineException):
    """Exception raised when a prediction job cannot be found."""

    def __init__(
        self,
        message: str = None,
        job_id: str = None,
        details: Optional[Dict[str, Any]] = None
    ):
        """Initialize prediction job not found exception.
        
        Args:
            message: Human-readable error message
            job_id: ID of the prediction job that wasn't found
            details: Additional error details
        """
        message = message or PREDICTION_ERRORS["PREDICTION_JOB_NOT_FOUND"]
        details = details or {}
        details["job_id"] = job_id
            
        super().__init__(
            message=message,
            error_code="prediction_job_not_found",
            details=details
        )
        self.status_code = 404  # Not Found
        self.job_id = job_id


class InvalidPredictionParametersError(AIEngineException):
    """Exception raised when prediction parameters are invalid."""

    def __init__(
        self,
        message: str = None,
        invalid_parameters: Optional[Dict[str, Any]] = None,
        details: Optional[Dict[str, Any]] = None
    ):
        """Initialize invalid prediction parameters exception.
        
        Args:
            message: Human-readable error message
            invalid_parameters: Dictionary of invalid parameters
            details: Additional error details
        """
        message = message or PREDICTION_ERRORS["INVALID_PREDICTION_PARAMETERS"]
        details = details or {}
        if invalid_parameters is not None:
            details["invalid_parameters"] = invalid_parameters
            
        super().__init__(
            message=message,
            error_code="invalid_prediction_parameters",
            details=details
        )
        self.status_code = 400  # Bad Request
        self.invalid_parameters = invalid_parameters