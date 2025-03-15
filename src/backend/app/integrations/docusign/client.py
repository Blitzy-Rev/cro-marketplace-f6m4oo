import os
import base64
import json
import datetime
from typing import Dict, List, Optional, Any, Union, Tuple

import requests  # version ^2.28.0
import jwt  # version ^2.6.0
from cryptography.hazmat.backends import default_backend  # version ^39.0.0
from cryptography.hazmat.primitives.serialization import load_pem_private_key

from .models import (
    DocuSignConfig, EnvelopeCreate, EnvelopeStatusUpdate, Envelope, 
    Recipient, DocumentInfo, SigningUrl, TemplateInfo, WebhookEvent,
    ENVELOPE_STATUS, RECIPIENT_TYPES
)
from .exceptions import (
    DocuSignException, DocuSignConnectionError, DocuSignTimeoutError,
    DocuSignResponseError, AuthenticationError, EnvelopeCreationError, 
    TemplateError, RecipientError
)
from ...core.logging import get_logger

# Configure logger
logger = get_logger(__name__)

# Constants
DEFAULT_TOKEN_EXPIRATION_SECONDS = 3600  # 1 hour
API_VERSION = "v2.1"
DEFAULT_REQUEST_TIMEOUT = 30  # seconds


class DocuSignClient:
    """Client for interacting with DocuSign e-signature API to create and manage electronic signature workflows."""

    def __init__(self, config: DocuSignConfig):
        """Initialize the DocuSign client with configuration.
        
        Args:
            config: Configuration for DocuSign integration
        """
        self._config = config
        self._access_token = None
        self._token_expiration = None
        self._base_url = f"{self._config.base_path}/{API_VERSION}/accounts/{self._config.account_id}"
        self._account_id = self._config.account_id
        
        logger.info(f"DocuSign client initialized with base URL: {self._base_url}")

    def authenticate(self) -> bool:
        """Authenticate with DocuSign API using JWT or OAuth.
        
        Returns:
            bool: True if authentication was successful
        """
        # Check if we already have a valid token
        if self._is_token_valid():
            logger.debug("Using existing valid DocuSign access token")
            return True
            
        try:
            if self._config.use_jwt_auth:
                # JWT authentication flow
                logger.debug("Using JWT authentication for DocuSign")
                
                # Read private key
                with open(self._config.private_key_path, 'rb') as key_file:
                    private_key_data = key_file.read()
                
                # Load private key
                private_key = load_pem_private_key(
                    private_key_data,
                    password=None,
                    backend=default_backend()
                )
                
                # Create JWT token
                current_time = datetime.datetime.utcnow()
                token_expiration = current_time + datetime.timedelta(seconds=DEFAULT_TOKEN_EXPIRATION_SECONDS)
                
                jwt_payload = {
                    'iss': self._config.client_id,
                    'sub': self._config.user_id,
                    'iat': current_time,
                    'exp': token_expiration,
                    'aud': self._config.authorization_server,
                    'scope': 'signature impersonation'
                }
                
                # Sign JWT token
                token = jwt.encode(jwt_payload, private_key, algorithm='RS256')
                
                # Exchange JWT for access token
                url = f"{self._config.authorization_server}/oauth/token"
                headers = {
                    'Content-Type': 'application/x-www-form-urlencoded'
                }
                data = {
                    'grant_type': 'urn:ietf:params:oauth:grant-type:jwt-bearer',
                    'assertion': token
                }
                
                response = requests.post(url, headers=headers, data=data, timeout=DEFAULT_REQUEST_TIMEOUT)
                response.raise_for_status()
                
                token_data = response.json()
                self._access_token = token_data.get('access_token')
                expiration_seconds = token_data.get('expires_in', DEFAULT_TOKEN_EXPIRATION_SECONDS)
                self._token_expiration = datetime.datetime.utcnow() + datetime.timedelta(seconds=expiration_seconds)
                
                logger.info("DocuSign JWT authentication successful")
                return True
                
            else:
                # OAuth client credentials flow
                logger.debug("Using OAuth client credentials for DocuSign")
                
                url = f"{self._config.authorization_server}/oauth/token"
                headers = {
                    'Content-Type': 'application/x-www-form-urlencoded'
                }
                data = {
                    'grant_type': 'client_credentials',
                    'client_id': self._config.client_id,
                    'client_secret': self._config.client_secret,
                    'scope': 'signature'
                }
                
                response = requests.post(url, headers=headers, data=data, timeout=DEFAULT_REQUEST_TIMEOUT)
                response.raise_for_status()
                
                token_data = response.json()
                self._access_token = token_data.get('access_token')
                expiration_seconds = token_data.get('expires_in', DEFAULT_TOKEN_EXPIRATION_SECONDS)
                self._token_expiration = datetime.datetime.utcnow() + datetime.timedelta(seconds=expiration_seconds)
                
                logger.info("DocuSign OAuth authentication successful")
                return True
                
        except requests.exceptions.ConnectionError as e:
            logger.exception("DocuSign authentication connection error")
            raise DocuSignConnectionError(details={"error": str(e)})
        except requests.exceptions.Timeout as e:
            logger.exception("DocuSign authentication timeout")
            raise DocuSignTimeoutError(timeout_seconds=DEFAULT_REQUEST_TIMEOUT, details={"error": str(e)})
        except requests.exceptions.RequestException as e:
            logger.exception("DocuSign authentication request error")
            if hasattr(e, 'response') and e.response.status_code == 401:
                raise AuthenticationError(details={"error": str(e)})
            raise DocuSignResponseError(
                response_status=e.response.status_code if hasattr(e, 'response') else None,
                response_body=e.response.json() if hasattr(e, 'response') and hasattr(e.response, 'json') else None,
                details={"error": str(e)}
            )
        except Exception as e:
            logger.exception("DocuSign authentication error")
            raise DocuSignException(message=f"Authentication failed: {str(e)}")
            
        return False

    def _is_token_valid(self) -> bool:
        """Check if the current access token is valid.
        
        Returns:
            bool: True if token is valid and not expired
        """
        if not self._access_token:
            return False
            
        if not self._token_expiration:
            return False
            
        # Add buffer time (30 seconds) to ensure token doesn't expire during use
        buffer_time = datetime.timedelta(seconds=30)
        return datetime.datetime.utcnow() + buffer_time < self._token_expiration

    def _make_request(
        self, 
        method: str, 
        endpoint: str, 
        params: Optional[Dict[str, Any]] = None,
        data: Optional[Dict[str, Any]] = None,
        headers: Optional[Dict[str, Any]] = None,
        timeout: Optional[int] = None
    ) -> Dict[str, Any]:
        """Make an authenticated request to the DocuSign API.
        
        Args:
            method: HTTP method (GET, POST, PUT, DELETE)
            endpoint: API endpoint
            params: URL parameters
            data: JSON data for request body
            headers: Custom headers
            timeout: Request timeout in seconds
        
        Returns:
            Dict[str, Any]: Response data from DocuSign API
        
        Raises:
            DocuSignConnectionError: When connection fails
            DocuSignTimeoutError: When request times out
            DocuSignResponseError: When API returns an error
            AuthenticationError: When authentication fails
        """
        # Ensure we have a valid token
        if not self._is_token_valid():
            self.authenticate()
            
        url = f"{self._base_url}/{endpoint}"
        default_headers = {
            'Authorization': f'Bearer {self._access_token}',
            'Content-Type': 'application/json',
            'Accept': 'application/json'
        }
        
        # Merge headers, with provided headers taking precedence
        request_headers = {**default_headers, **(headers or {})}
        timeout_val = timeout if timeout is not None else DEFAULT_REQUEST_TIMEOUT
        
        try:
            logger.debug(f"Making DocuSign API request: {method} {url}")
            response = requests.request(
                method=method,
                url=url,
                params=params,
                json=data,
                headers=request_headers,
                timeout=timeout_val
            )
            
            # Check for successful response
            if response.status_code >= 200 and response.status_code < 300:
                # For 204 No Content responses, return empty dict
                if response.status_code == 204:
                    return {}
                    
                try:
                    # Try to parse response as JSON
                    return response.json()
                except json.JSONDecodeError:
                    # If not JSON, return content as string in a dict
                    return {"content": response.content.decode("utf-8", errors="ignore")}
            
            # Handle error responses
            error_message = "DocuSign API error"
            error_details = {}
            
            try:
                error_data = response.json()
                if isinstance(error_data, dict):
                    error_message = error_data.get('message', error_message)
                    error_details = error_data
            except (json.JSONDecodeError, ValueError):
                error_details = {"content": response.content.decode("utf-8", errors="ignore")}
                
            logger.error(f"DocuSign API error: {response.status_code} - {error_message}")
            
            # Handle specific error codes
            if response.status_code == 401:
                # Clear token to force re-authentication on next request
                self._access_token = None
                self._token_expiration = None
                raise AuthenticationError(message=error_message, details=error_details)
                
            raise DocuSignResponseError(
                message=error_message,
                response_status=response.status_code,
                response_body=error_details
            )
                
        except requests.exceptions.ConnectionError as e:
            logger.exception(f"DocuSign connection error: {str(e)}")
            raise DocuSignConnectionError(details={"error": str(e), "url": url})
        except requests.exceptions.Timeout as e:
            logger.exception(f"DocuSign request timeout: {str(e)}")
            raise DocuSignTimeoutError(
                timeout_seconds=timeout_val, 
                details={"error": str(e), "url": url}
            )
        except (DocuSignConnectionError, DocuSignTimeoutError, DocuSignResponseError, AuthenticationError):
            # Re-raise specific exceptions
            raise
        except Exception as e:
            logger.exception(f"DocuSign request error: {str(e)}")
            raise DocuSignException(message=f"Request failed: {str(e)}", details={"url": url})

    def create_envelope(self, envelope_data: EnvelopeCreate) -> Envelope:
        """Create a new envelope with documents for signature.
        
        Args:
            envelope_data: Envelope creation data
            
        Returns:
            Envelope: Created envelope information
            
        Raises:
            EnvelopeCreationError: When envelope creation fails
        """
        try:
            # Convert envelope data to DocuSign format
            docusign_data = envelope_data.to_docusign_dict()
            
            # Make API request to create envelope
            response = self._make_request(
                method="POST",
                endpoint="envelopes",
                data=docusign_data
            )
            
            # Create Envelope object from response
            envelope = Envelope.from_docusign_response(response)
            logger.info(f"Envelope created successfully: {envelope.envelope_id}")
            
            return envelope
            
        except (DocuSignConnectionError, DocuSignTimeoutError, DocuSignResponseError) as e:
            # Convert to EnvelopeCreationError for better context
            envelope_id = None
            if hasattr(e, 'response_body') and isinstance(e.response_body, dict):
                envelope_id = e.response_body.get('envelopeId')
                
            logger.error(f"Failed to create envelope: {str(e)}")
            raise EnvelopeCreationError(
                message=f"Failed to create envelope: {str(e)}",
                envelope_id=envelope_id,
                details=e.details if hasattr(e, 'details') else None
            )

    def get_envelope(self, envelope_id: str) -> Envelope:
        """Get information about an existing envelope.
        
        Args:
            envelope_id: ID of the envelope
            
        Returns:
            Envelope: Envelope information
            
        Raises:
            DocuSignResponseError: When API returns an error
        """
        try:
            response = self._make_request(
                method="GET",
                endpoint=f"envelopes/{envelope_id}"
            )
            
            envelope = Envelope.from_docusign_response(response)
            logger.debug(f"Retrieved envelope: {envelope_id}")
            
            return envelope
            
        except Exception as e:
            logger.error(f"Failed to get envelope {envelope_id}: {str(e)}")
            raise

    def update_envelope_status(self, status_update: EnvelopeStatusUpdate) -> Envelope:
        """Update the status of an existing envelope.
        
        Args:
            status_update: Status update information
            
        Returns:
            Envelope: Updated envelope information
            
        Raises:
            DocuSignResponseError: When API returns an error
        """
        try:
            # Convert status update to DocuSign format
            docusign_data = status_update.to_docusign_dict()
            
            # Make API request to update envelope status
            self._make_request(
                method="PUT",
                endpoint=f"envelopes/{status_update.envelope_id}",
                data=docusign_data
            )
            
            # Get updated envelope
            updated_envelope = self.get_envelope(status_update.envelope_id)
            logger.info(f"Updated envelope status: {status_update.envelope_id} -> {status_update.status}")
            
            return updated_envelope
            
        except Exception as e:
            logger.error(f"Failed to update envelope status {status_update.envelope_id}: {str(e)}")
            raise

    def void_envelope(self, envelope_id: str, reason: str) -> Envelope:
        """Void an existing envelope.
        
        Args:
            envelope_id: ID of the envelope to void
            reason: Reason for voiding the envelope
            
        Returns:
            Envelope: Updated envelope information
            
        Raises:
            DocuSignResponseError: When API returns an error
        """
        try:
            # Create status update for voiding
            status_update = EnvelopeStatusUpdate(
                envelope_id=envelope_id,
                status="voided",
                status_reason=reason
            )
            
            # Update envelope status
            return self.update_envelope_status(status_update)
            
        except Exception as e:
            logger.error(f"Failed to void envelope {envelope_id}: {str(e)}")
            raise

    def create_recipient_view(
        self,
        envelope_id: str,
        recipient_email: str,
        recipient_name: str,
        return_url: Optional[str] = None
    ) -> SigningUrl:
        """Create a recipient view URL for embedded signing.
        
        Args:
            envelope_id: ID of the envelope
            recipient_email: Email of the recipient
            recipient_name: Name of the recipient
            return_url: URL to redirect after signing (optional)
            
        Returns:
            SigningUrl: Signing URL information
            
        Raises:
            RecipientError: When recipient view creation fails
        """
        try:
            # Use callback_url from config if return_url not provided
            redirect_url = return_url or self._config.callback_url
            if not redirect_url:
                raise RecipientError(
                    message="Return URL must be provided either in request or in configuration",
                    envelope_id=envelope_id,
                    recipient_email=recipient_email
                )
                
            # Prepare recipient view request
            view_request = {
                "returnUrl": redirect_url,
                "authenticationMethod": "none",
                "email": recipient_email,
                "userName": recipient_name,
                "clientUserId": recipient_email,  # Use email as clientUserId for consistency
            }
            
            # Make API request to create recipient view
            response = self._make_request(
                method="POST",
                endpoint=f"envelopes/{envelope_id}/views/recipient",
                data=view_request
            )
            
            # Create SigningUrl object from response
            signing_url = SigningUrl.from_docusign_response(
                response, 
                envelope_id=envelope_id,
                recipient_id=recipient_email
            )
            
            logger.info(f"Created signing URL for envelope {envelope_id}, recipient {recipient_email}")
            return signing_url
            
        except (DocuSignConnectionError, DocuSignTimeoutError, DocuSignResponseError) as e:
            logger.error(f"Failed to create recipient view: {str(e)}")
            raise RecipientError(
                message=f"Failed to create recipient view: {str(e)}",
                envelope_id=envelope_id,
                recipient_email=recipient_email,
                details=e.details if hasattr(e, 'details') else None
            )
        except Exception as e:
            logger.error(f"Failed to create recipient view: {str(e)}")
            raise RecipientError(
                message=f"Failed to create recipient view: {str(e)}",
                envelope_id=envelope_id,
                recipient_email=recipient_email
            )

    def get_envelope_documents(self, envelope_id: str) -> List[DocumentInfo]:
        """Get documents from an existing envelope.
        
        Args:
            envelope_id: ID of the envelope
            
        Returns:
            List[DocumentInfo]: List of documents in the envelope
            
        Raises:
            DocuSignResponseError: When API returns an error
        """
        try:
            response = self._make_request(
                method="GET",
                endpoint=f"envelopes/{envelope_id}/documents"
            )
            
            # Create DocumentInfo objects from response
            documents = []
            for doc_data in response.get("documents", []):
                documents.append(DocumentInfo.from_docusign_response(doc_data))
                
            logger.debug(f"Retrieved {len(documents)} documents for envelope {envelope_id}")
            return documents
            
        except Exception as e:
            logger.error(f"Failed to get envelope documents {envelope_id}: {str(e)}")
            raise

    def get_document_content(self, envelope_id: str, document_id: str) -> bytes:
        """Get the content of a document from an envelope.
        
        Args:
            envelope_id: ID of the envelope
            document_id: ID of the document
            
        Returns:
            bytes: Document content as bytes
            
        Raises:
            DocuSignResponseError: When API returns an error
        """
        try:
            # For document content, we need to accept PDF
            headers = {
                "Accept": "application/pdf"
            }
            
            # Make API request to get document content
            response = requests.get(
                url=f"{self._base_url}/envelopes/{envelope_id}/documents/{document_id}",
                headers={
                    **headers,
                    "Authorization": f"Bearer {self._access_token}"
                },
                timeout=DEFAULT_REQUEST_TIMEOUT
            )
            
            if response.status_code >= 200 and response.status_code < 300:
                logger.debug(f"Retrieved document content for envelope {envelope_id}, document {document_id}")
                return response.content
                
            # Handle error
            error_message = f"Failed to get document content: Status {response.status_code}"
            logger.error(error_message)
            
            # Try to parse error response
            try:
                error_data = response.json()
                if isinstance(error_data, dict):
                    error_message = error_data.get("message", error_message)
            except:
                pass
                
            raise DocuSignResponseError(
                message=error_message,
                response_status=response.status_code,
                response_body={"content": response.content}
            )
            
        except requests.exceptions.ConnectionError as e:
            logger.exception(f"DocuSign connection error: {str(e)}")
            raise DocuSignConnectionError(details={"error": str(e)})
        except requests.exceptions.Timeout as e:
            logger.exception(f"DocuSign request timeout: {str(e)}")
            raise DocuSignTimeoutError(timeout_seconds=DEFAULT_REQUEST_TIMEOUT, details={"error": str(e)})
        except Exception as e:
            logger.error(f"Failed to get document content: {str(e)}")
            raise

    def get_envelope_recipients(self, envelope_id: str) -> List[Recipient]:
        """Get recipients of an existing envelope.
        
        Args:
            envelope_id: ID of the envelope
            
        Returns:
            List[Recipient]: List of recipients in the envelope
            
        Raises:
            DocuSignResponseError: When API returns an error
        """
        try:
            response = self._make_request(
                method="GET",
                endpoint=f"envelopes/{envelope_id}/recipients"
            )
            
            # Process recipient types
            recipients = []
            for recipient_type in ["signers", "carbonCopies", "inPersonSigners", "editors", "intermediaries"]:
                if recipient_type in response and response[recipient_type]:
                    for recipient_data in response[recipient_type]:
                        # Add recipient type to data
                        recipient_data["recipientType"] = recipient_type[:-1]  # Remove trailing 's'
                        recipients.append(Recipient.from_docusign_response(recipient_data))
            
            logger.debug(f"Retrieved {len(recipients)} recipients for envelope {envelope_id}")
            return recipients
            
        except Exception as e:
            logger.error(f"Failed to get envelope recipients {envelope_id}: {str(e)}")
            raise

    def get_templates(self) -> List[TemplateInfo]:
        """Get available templates for the account.
        
        Returns:
            List[TemplateInfo]: List of available templates
            
        Raises:
            TemplateError: When template retrieval fails
        """
        try:
            response = self._make_request(
                method="GET",
                endpoint="templates"
            )
            
            templates = []
            for template_data in response.get("envelopeTemplates", []):
                templates.append(TemplateInfo.from_docusign_response(template_data))
                
            logger.debug(f"Retrieved {len(templates)} templates")
            return templates
            
        except (DocuSignConnectionError, DocuSignTimeoutError, DocuSignResponseError) as e:
            logger.error(f"Failed to get templates: {str(e)}")
            raise TemplateError(
                message=f"Failed to get templates: {str(e)}",
                details=e.details if hasattr(e, 'details') else None
            )
        except Exception as e:
            logger.error(f"Failed to get templates: {str(e)}")
            raise TemplateError(message=f"Failed to get templates: {str(e)}")

    def get_template(self, template_id: str) -> TemplateInfo:
        """Get information about a specific template.
        
        Args:
            template_id: ID of the template
            
        Returns:
            TemplateInfo: Template information
            
        Raises:
            TemplateError: When template retrieval fails
        """
        try:
            response = self._make_request(
                method="GET",
                endpoint=f"templates/{template_id}"
            )
            
            template = TemplateInfo.from_docusign_response(response)
            logger.debug(f"Retrieved template: {template_id}")
            
            return template
            
        except (DocuSignConnectionError, DocuSignTimeoutError, DocuSignResponseError) as e:
            logger.error(f"Failed to get template {template_id}: {str(e)}")
            raise TemplateError(
                message=f"Failed to get template: {str(e)}",
                template_id=template_id,
                details=e.details if hasattr(e, 'details') else None
            )
        except Exception as e:
            logger.error(f"Failed to get template {template_id}: {str(e)}")
            raise TemplateError(
                message=f"Failed to get template: {str(e)}",
                template_id=template_id
            )

    def create_envelope_from_template(
        self,
        template_id: str,
        recipients: List[Recipient],
        email_subject: str,
        email_body: Optional[str] = None,
        status: str = "sent"
    ) -> Envelope:
        """Create a new envelope using a template.
        
        Args:
            template_id: ID of the template to use
            recipients: List of recipients
            email_subject: Subject of the email
            email_body: Body of the email (optional)
            status: Status of the envelope (draft, sent)
            
        Returns:
            Envelope: Created envelope information
            
        Raises:
            EnvelopeCreationError: When envelope creation fails
        """
        try:
            # Prepare envelope data with template
            envelope_data = {
                "templateId": template_id,
                "emailSubject": email_subject,
                "status": status,
            }
            
            if email_body:
                envelope_data["emailBlurb"] = email_body
                
            # Add recipients
            if recipients:
                recipients_dict = []
                for recipient in recipients:
                    recipients_dict.append(recipient.to_docusign_dict())
                envelope_data["templateRoles"] = recipients_dict
                
            # Make API request to create envelope
            response = self._make_request(
                method="POST",
                endpoint="envelopes",
                data=envelope_data
            )
            
            # Create Envelope object from response
            envelope = Envelope.from_docusign_response(response)
            logger.info(f"Created envelope from template {template_id}: {envelope.envelope_id}")
            
            return envelope
            
        except (DocuSignConnectionError, DocuSignTimeoutError, DocuSignResponseError) as e:
            logger.error(f"Failed to create envelope from template {template_id}: {str(e)}")
            raise EnvelopeCreationError(
                message=f"Failed to create envelope from template: {str(e)}",
                details=e.details if hasattr(e, 'details') else None
            )
        except Exception as e:
            logger.error(f"Failed to create envelope from template {template_id}: {str(e)}")
            raise EnvelopeCreationError(message=f"Failed to create envelope from template: {str(e)}")

    def process_webhook_event(self, webhook_data: Dict[str, Any]) -> WebhookEvent:
        """Process a webhook event from DocuSign.
        
        Args:
            webhook_data: Webhook event data from DocuSign
            
        Returns:
            WebhookEvent: Processed webhook event
            
        Raises:
            DocuSignException: When webhook processing fails
        """
        try:
            # Create WebhookEvent from payload
            webhook_event = WebhookEvent.from_docusign_payload(webhook_data)
            
            logger.info(f"Processed webhook event for envelope {webhook_event.envelope_id}: {webhook_event.status}")
            return webhook_event
            
        except Exception as e:
            logger.error(f"Failed to process webhook event: {str(e)}")
            raise DocuSignException(message=f"Failed to process webhook event: {str(e)}")