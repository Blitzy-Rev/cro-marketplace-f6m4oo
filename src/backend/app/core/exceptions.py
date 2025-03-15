"""
Exception Module

This module defines a comprehensive exception hierarchy for the Molecular Data Management 
and CRO Integration Platform. It implements domain-specific exceptions with standardized 
error handling, status codes, and error message formatting to ensure consistent error 
responses across the application.

The exception system:
- Provides a base exception class that all application exceptions inherit from
- Defines specific exception types for different error categories
- Includes domain-specific exceptions for molecular data, CRO submissions, etc.
- Supports detailed error messages with additional context
- Facilitates consistent HTTP status codes for API responses
"""

from typing import Dict, Any, Optional, List
from fastapi import HTTPException, status

# Import error message dictionaries from constants
from ..constants.error_messages import (
    AUTH_ERRORS,
    VALIDATION_ERRORS,
    MOLECULE_ERRORS,
    CSV_ERRORS,
    LIBRARY_ERRORS,
    SUBMISSION_ERRORS,
    DOCUMENT_ERRORS,
    RESULT_ERRORS,
    PREDICTION_ERRORS,
    INTEGRATION_ERRORS,
    SYSTEM_ERRORS
)


class BaseAppException(Exception):
    """Base exception class for all application-specific exceptions."""
    
    def __init__(
        self,
        message: str,
        error_code: Optional[str] = None,
        details: Optional[Dict[str, Any]] = None,
        status_code: int = 500
    ):
        """Initialize the base exception with error details.
        
        Args:
            message: Human-readable error message
            error_code: Machine-readable error code
            details: Additional error details
            status_code: HTTP status code
        """
        super().__init__(message)
        self.status_code = status_code
        self.error_code = error_code or "internal_error"
        self.message = message
        self.details = details or {}
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert exception to a dictionary for JSON response.
        
        Returns:
            Dictionary representation of the exception
        """
        error_dict = {
            "error_code": self.error_code,
            "message": self.message,
            "status_code": self.status_code
        }
        
        if self.details:
            error_dict["details"] = self.details
            
        return error_dict


class ValidationException(BaseAppException):
    """Exception for data validation errors."""
    
    def __init__(
        self,
        message: str,
        validation_errors: Optional[List[Dict[str, Any]]] = None,
        error_code: Optional[str] = None
    ):
        """Initialize validation exception with specific validation errors.
        
        Args:
            message: Human-readable error message
            validation_errors: List of validation errors
            error_code: Machine-readable error code
        """
        details = {}
        if validation_errors:
            details["validation_errors"] = validation_errors
            
        super().__init__(
            message=message,
            error_code=error_code or "validation_error",
            details=details,
            status_code=status.HTTP_422_UNPROCESSABLE_ENTITY
        )
        self.validation_errors = validation_errors or []


class AuthenticationException(BaseAppException):
    """Exception for authentication failures."""
    
    def __init__(
        self,
        message: str,
        error_code: Optional[str] = None,
        details: Optional[Dict[str, Any]] = None
    ):
        """Initialize authentication exception.
        
        Args:
            message: Human-readable error message
            error_code: Machine-readable error code
            details: Additional error details
        """
        super().__init__(
            message=message,
            error_code=error_code or "authentication_error",
            details=details,
            status_code=status.HTTP_401_UNAUTHORIZED
        )


class AuthorizationException(BaseAppException):
    """Exception for authorization failures."""
    
    def __init__(
        self,
        message: str,
        error_code: Optional[str] = None,
        details: Optional[Dict[str, Any]] = None
    ):
        """Initialize authorization exception.
        
        Args:
            message: Human-readable error message
            error_code: Machine-readable error code
            details: Additional error details
        """
        super().__init__(
            message=message,
            error_code=error_code or "authorization_error",
            details=details,
            status_code=status.HTTP_403_FORBIDDEN
        )


class NotFoundException(BaseAppException):
    """Exception for resource not found errors."""
    
    def __init__(
        self,
        message: str,
        resource_type: Optional[str] = None,
        error_code: Optional[str] = None,
        details: Optional[Dict[str, Any]] = None
    ):
        """Initialize not found exception.
        
        Args:
            message: Human-readable error message
            resource_type: Type of resource that was not found
            error_code: Machine-readable error code
            details: Additional error details
        """
        details = details or {}
        if resource_type:
            details["resource_type"] = resource_type
            
        super().__init__(
            message=message,
            error_code=error_code or "not_found",
            details=details,
            status_code=status.HTTP_404_NOT_FOUND
        )
        self.resource_type = resource_type


class ConflictException(BaseAppException):
    """Exception for resource conflicts."""
    
    def __init__(
        self,
        message: str,
        error_code: Optional[str] = None,
        details: Optional[Dict[str, Any]] = None
    ):
        """Initialize conflict exception.
        
        Args:
            message: Human-readable error message
            error_code: Machine-readable error code
            details: Additional error details
        """
        super().__init__(
            message=message,
            error_code=error_code or "conflict",
            details=details,
            status_code=status.HTTP_409_CONFLICT
        )


class RateLimitException(BaseAppException):
    """Exception for rate limiting."""
    
    def __init__(
        self,
        message: str,
        retry_after: Optional[int] = None,
        error_code: Optional[str] = None,
        details: Optional[Dict[str, Any]] = None
    ):
        """Initialize rate limit exception.
        
        Args:
            message: Human-readable error message
            retry_after: Seconds until retry is allowed
            error_code: Machine-readable error code
            details: Additional error details
        """
        details = details or {}
        if retry_after is not None:
            details["retry_after"] = retry_after
            
        super().__init__(
            message=message,
            error_code=error_code or "rate_limit_exceeded",
            details=details,
            status_code=status.HTTP_429_TOO_MANY_REQUESTS
        )
        self.retry_after = retry_after


class ServiceUnavailableException(BaseAppException):
    """Exception for service unavailability."""
    
    def __init__(
        self,
        message: str,
        service_name: Optional[str] = None,
        error_code: Optional[str] = None,
        details: Optional[Dict[str, Any]] = None
    ):
        """Initialize service unavailable exception.
        
        Args:
            message: Human-readable error message
            service_name: Name of the unavailable service
            error_code: Machine-readable error code
            details: Additional error details
        """
        details = details or {}
        if service_name:
            details["service_name"] = service_name
            
        super().__init__(
            message=message,
            error_code=error_code or "service_unavailable",
            details=details,
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE
        )
        self.service_name = service_name


class InternalServerException(BaseAppException):
    """Exception for internal server errors."""
    
    def __init__(
        self,
        message: str,
        error_id: Optional[str] = None,
        error_code: Optional[str] = None,
        details: Optional[Dict[str, Any]] = None
    ):
        """Initialize internal server exception.
        
        Args:
            message: Human-readable error message
            error_id: Unique identifier for tracking the error
            error_code: Machine-readable error code
            details: Additional error details
        """
        details = details or {}
        if error_id:
            details["error_id"] = error_id
            
        super().__init__(
            message=message,
            error_code=error_code or "internal_server_error",
            details=details,
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR
        )
        self.error_id = error_id


class MoleculeException(BaseAppException):
    """Exception for molecule-specific errors."""
    
    def __init__(
        self,
        message: str,
        molecule_id: Optional[str] = None,
        error_code: Optional[str] = None,
        details: Optional[Dict[str, Any]] = None,
        status_code: int = status.HTTP_400_BAD_REQUEST
    ):
        """Initialize molecule exception.
        
        Args:
            message: Human-readable error message
            molecule_id: ID of the molecule
            error_code: Machine-readable error code
            details: Additional error details
            status_code: HTTP status code
        """
        details = details or {}
        if molecule_id:
            details["molecule_id"] = molecule_id
            
        super().__init__(
            message=message,
            error_code=error_code or "molecule_error",
            details=details,
            status_code=status_code
        )
        self.molecule_id = molecule_id


class CSVException(BaseAppException):
    """Exception for CSV processing errors."""
    
    def __init__(
        self,
        message: str,
        file_name: Optional[str] = None,
        line_number: Optional[int] = None,
        error_code: Optional[str] = None,
        details: Optional[Dict[str, Any]] = None
    ):
        """Initialize CSV exception.
        
        Args:
            message: Human-readable error message
            file_name: Name of the CSV file
            line_number: Line number where the error occurred
            error_code: Machine-readable error code
            details: Additional error details
        """
        details = details or {}
        if file_name:
            details["file_name"] = file_name
        if line_number is not None:
            details["line_number"] = line_number
            
        super().__init__(
            message=message,
            error_code=error_code or "csv_error",
            details=details,
            status_code=status.HTTP_400_BAD_REQUEST
        )
        self.file_name = file_name
        self.line_number = line_number


class LibraryException(BaseAppException):
    """Exception for library management errors."""
    
    def __init__(
        self,
        message: str,
        library_id: Optional[str] = None,
        error_code: Optional[str] = None,
        details: Optional[Dict[str, Any]] = None
    ):
        """Initialize library exception.
        
        Args:
            message: Human-readable error message
            library_id: ID of the library
            error_code: Machine-readable error code
            details: Additional error details
        """
        details = details or {}
        if library_id:
            details["library_id"] = library_id
            
        super().__init__(
            message=message,
            error_code=error_code or "library_error",
            details=details,
            status_code=status.HTTP_400_BAD_REQUEST
        )
        self.library_id = library_id


class SubmissionException(BaseAppException):
    """Exception for CRO submission errors."""
    
    def __init__(
        self,
        message: str,
        submission_id: Optional[str] = None,
        error_code: Optional[str] = None,
        details: Optional[Dict[str, Any]] = None
    ):
        """Initialize submission exception.
        
        Args:
            message: Human-readable error message
            submission_id: ID of the submission
            error_code: Machine-readable error code
            details: Additional error details
        """
        details = details or {}
        if submission_id:
            details["submission_id"] = submission_id
            
        super().__init__(
            message=message,
            error_code=error_code or "submission_error",
            details=details,
            status_code=status.HTTP_400_BAD_REQUEST
        )
        self.submission_id = submission_id


class DocumentException(BaseAppException):
    """Exception for document management errors."""
    
    def __init__(
        self,
        message: str,
        document_id: Optional[str] = None,
        error_code: Optional[str] = None,
        details: Optional[Dict[str, Any]] = None
    ):
        """Initialize document exception.
        
        Args:
            message: Human-readable error message
            document_id: ID of the document
            error_code: Machine-readable error code
            details: Additional error details
        """
        details = details or {}
        if document_id:
            details["document_id"] = document_id
            
        super().__init__(
            message=message,
            error_code=error_code or "document_error",
            details=details,
            status_code=status.HTTP_400_BAD_REQUEST
        )
        self.document_id = document_id


class ResultException(BaseAppException):
    """Exception for result processing errors."""
    
    def __init__(
        self,
        message: str,
        result_id: Optional[str] = None,
        error_code: Optional[str] = None,
        details: Optional[Dict[str, Any]] = None
    ):
        """Initialize result exception.
        
        Args:
            message: Human-readable error message
            result_id: ID of the result
            error_code: Machine-readable error code
            details: Additional error details
        """
        details = details or {}
        if result_id:
            details["result_id"] = result_id
            
        super().__init__(
            message=message,
            error_code=error_code or "result_error",
            details=details,
            status_code=status.HTTP_400_BAD_REQUEST
        )
        self.result_id = result_id


class PredictionException(BaseAppException):
    """Exception for AI prediction errors."""
    
    def __init__(
        self,
        message: str,
        job_id: Optional[str] = None,
        error_code: Optional[str] = None,
        details: Optional[Dict[str, Any]] = None
    ):
        """Initialize prediction exception.
        
        Args:
            message: Human-readable error message
            job_id: ID of the prediction job
            error_code: Machine-readable error code
            details: Additional error details
        """
        details = details or {}
        if job_id:
            details["job_id"] = job_id
            
        super().__init__(
            message=message,
            error_code=error_code or "prediction_error",
            details=details,
            status_code=status.HTTP_400_BAD_REQUEST
        )
        self.job_id = job_id


class IntegrationException(BaseAppException):
    """Exception for external integration errors."""
    
    def __init__(
        self,
        message: str,
        service_name: Optional[str] = None,
        error_code: Optional[str] = None,
        details: Optional[Dict[str, Any]] = None
    ):
        """Initialize integration exception.
        
        Args:
            message: Human-readable error message
            service_name: Name of the external service
            error_code: Machine-readable error code
            details: Additional error details
        """
        details = details or {}
        if service_name:
            details["service_name"] = service_name
            
        super().__init__(
            message=message,
            error_code=error_code or "integration_error",
            details=details,
            status_code=status.HTTP_502_BAD_GATEWAY
        )
        self.service_name = service_name