"""
DocuSign Integration Exceptions

This module defines custom exception classes for handling errors that occur
during interactions with the DocuSign e-signature service. Each exception 
corresponds to a specific error scenario and includes appropriate status codes
and error messages for structured error handling.
"""

from typing import Dict, Optional, Any

from ...core.exceptions import IntegrationException, ServiceUnavailableException
from ...constants.error_messages import INTEGRATION_ERRORS, DOCUMENT_ERRORS


class DocuSignException(IntegrationException):
    """Base exception class for all DocuSign integration errors."""
    
    def __init__(
        self,
        message: str,
        error_code: Optional[str] = None,
        details: Optional[Dict[str, Any]] = None
    ):
        """Initialize DocuSign exception with error details.
        
        Args:
            message: Human-readable error message
            error_code: Machine-readable error code
            details: Additional error details
        """
        details = details or {}
        service_name = "DocuSign"
        
        if "service_name" not in details:
            details["service_name"] = service_name
        
        super().__init__(
            message=message,
            service_name=service_name,
            error_code=error_code,
            details=details
        )


class DocuSignConnectionError(DocuSignException):
    """Exception raised when connection to the DocuSign service fails."""
    
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
        message = message or INTEGRATION_ERRORS["DOCUSIGN_CONNECTION_FAILED"]
        
        super().__init__(
            message=message,
            error_code="docusign_connection_failed",
            details=details
        )
        self.status_code = 503  # Service Unavailable


class DocuSignTimeoutError(DocuSignException):
    """Exception raised when a request to DocuSign times out."""
    
    def __init__(
        self,
        message: str = None,
        timeout_seconds: Optional[int] = None,
        details: Optional[Dict[str, Any]] = None
    ):
        """Initialize timeout error exception.
        
        Args:
            message: Human-readable error message
            timeout_seconds: Timeout duration in seconds
            details: Additional error details
        """
        message = message or INTEGRATION_ERRORS["INTEGRATION_TIMEOUT"]
        details = details or {}
        
        if timeout_seconds is not None:
            details["timeout_seconds"] = timeout_seconds
            
        super().__init__(
            message=message,
            error_code="docusign_timeout",
            details=details
        )
        self.status_code = 504  # Gateway Timeout
        self.timeout_seconds = timeout_seconds


class DocuSignResponseError(DocuSignException):
    """Exception raised when DocuSign returns an error response."""
    
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
            response_status: HTTP status code from DocuSign
            response_body: Response body from DocuSign
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
            error_code="docusign_response_error",
            details=details
        )
        self.status_code = 502  # Bad Gateway
        self.response_status = response_status
        self.response_body = response_body


class EnvelopeCreationError(DocuSignException):
    """Exception raised when envelope creation fails."""
    
    def __init__(
        self,
        message: str = None,
        envelope_id: Optional[str] = None,
        details: Optional[Dict[str, Any]] = None
    ):
        """Initialize envelope creation error exception.
        
        Args:
            message: Human-readable error message
            envelope_id: ID of the envelope if partially created
            details: Additional error details
        """
        message = message or "Failed to create DocuSign envelope"
        details = details or {}
        
        if envelope_id is not None:
            details["envelope_id"] = envelope_id
            
        super().__init__(
            message=message,
            error_code="envelope_creation_failed",
            details=details
        )
        self.status_code = 400  # Bad Request
        self.envelope_id = envelope_id


class DocumentUploadError(DocuSignException):
    """Exception raised when document upload to DocuSign fails."""
    
    def __init__(
        self,
        message: str = None,
        document_id: Optional[str] = None,
        details: Optional[Dict[str, Any]] = None
    ):
        """Initialize document upload error exception.
        
        Args:
            message: Human-readable error message
            document_id: ID of the document if available
            details: Additional error details
        """
        message = message or DOCUMENT_ERRORS["DOCUMENT_UPLOAD_FAILED"]
        details = details or {}
        
        if document_id is not None:
            details["document_id"] = document_id
            
        super().__init__(
            message=message,
            error_code="document_upload_failed",
            details=details
        )
        self.status_code = 400  # Bad Request
        self.document_id = document_id


class DocumentDownloadError(DocuSignException):
    """Exception raised when document download from DocuSign fails."""
    
    def __init__(
        self,
        message: str = None,
        document_id: Optional[str] = None,
        envelope_id: Optional[str] = None,
        details: Optional[Dict[str, Any]] = None
    ):
        """Initialize document download error exception.
        
        Args:
            message: Human-readable error message
            document_id: ID of the document
            envelope_id: ID of the envelope containing the document
            details: Additional error details
        """
        message = message or DOCUMENT_ERRORS["DOCUMENT_DOWNLOAD_FAILED"]
        details = details or {}
        
        if document_id is not None:
            details["document_id"] = document_id
            
        if envelope_id is not None:
            details["envelope_id"] = envelope_id
            
        super().__init__(
            message=message,
            error_code="document_download_failed",
            details=details
        )
        self.status_code = 400  # Bad Request
        self.document_id = document_id
        self.envelope_id = envelope_id


class AuthenticationError(DocuSignException):
    """Exception raised when authentication with DocuSign fails."""
    
    def __init__(
        self,
        message: str = None,
        details: Optional[Dict[str, Any]] = None
    ):
        """Initialize authentication error exception.
        
        Args:
            message: Human-readable error message
            details: Additional error details
        """
        message = message or INTEGRATION_ERRORS["INTEGRATION_AUTHENTICATION_FAILED"]
        
        super().__init__(
            message=message,
            error_code="docusign_authentication_failed",
            details=details
        )
        self.status_code = 401  # Unauthorized


class WebhookError(DocuSignException):
    """Exception raised when processing DocuSign webhooks fails."""
    
    def __init__(
        self,
        message: str = None,
        envelope_id: Optional[str] = None,
        event_type: Optional[str] = None,
        details: Optional[Dict[str, Any]] = None
    ):
        """Initialize webhook error exception.
        
        Args:
            message: Human-readable error message
            envelope_id: ID of the envelope related to the webhook
            event_type: Type of webhook event
            details: Additional error details
        """
        message = message or "Failed to process DocuSign webhook"
        details = details or {}
        
        if envelope_id is not None:
            details["envelope_id"] = envelope_id
            
        if event_type is not None:
            details["event_type"] = event_type
            
        super().__init__(
            message=message,
            error_code="webhook_processing_failed",
            details=details
        )
        self.status_code = 400  # Bad Request
        self.envelope_id = envelope_id
        self.event_type = event_type


class TemplateError(DocuSignException):
    """Exception raised when DocuSign template operations fail."""
    
    def __init__(
        self,
        message: str = None,
        template_id: Optional[str] = None,
        details: Optional[Dict[str, Any]] = None
    ):
        """Initialize template error exception.
        
        Args:
            message: Human-readable error message
            template_id: ID of the template
            details: Additional error details
        """
        message = message or "DocuSign template operation failed"
        details = details or {}
        
        if template_id is not None:
            details["template_id"] = template_id
            
        super().__init__(
            message=message,
            error_code="template_operation_failed",
            details=details
        )
        self.status_code = 400  # Bad Request
        self.template_id = template_id


class RecipientError(DocuSignException):
    """Exception raised when recipient operations fail."""
    
    def __init__(
        self,
        message: str = None,
        envelope_id: Optional[str] = None,
        recipient_id: Optional[str] = None,
        recipient_email: Optional[str] = None,
        details: Optional[Dict[str, Any]] = None
    ):
        """Initialize recipient error exception.
        
        Args:
            message: Human-readable error message
            envelope_id: ID of the envelope
            recipient_id: ID of the recipient
            recipient_email: Email of the recipient
            details: Additional error details
        """
        message = message or "DocuSign recipient operation failed"
        details = details or {}
        
        if envelope_id is not None:
            details["envelope_id"] = envelope_id
            
        if recipient_id is not None:
            details["recipient_id"] = recipient_id
            
        if recipient_email is not None:
            details["recipient_email"] = recipient_email
            
        super().__init__(
            message=message,
            error_code="recipient_operation_failed",
            details=details
        )
        self.status_code = 400  # Bad Request
        self.envelope_id = envelope_id
        self.recipient_id = recipient_id
        self.recipient_email = recipient_email