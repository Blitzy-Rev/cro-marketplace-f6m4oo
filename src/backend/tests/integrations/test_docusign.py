import pytest
from unittest.mock import MagicMock, patch
import os
import tempfile
import base64
import json
from datetime import datetime
import uuid

# Import DocuSign client and models
from ../../app/integrations/docusign/client import DocuSignClient
from ../../app/integrations/docusign/models import (
    DocuSignConfig, Recipient, DocumentInfo, EnvelopeCreate,
    Envelope, EnvelopeStatusUpdate, WebhookEvent, SigningUrl,
    TemplateInfo, ENVELOPE_STATUS, RECIPIENT_TYPES
)
from ../../app/integrations/docusign/exceptions import (
    DocuSignException, DocuSignConnectionError, DocuSignTimeoutError,
    DocuSignResponseError, AuthenticationError, EnvelopeCreationError,
    TemplateError, RecipientError
)

# Test constants
TEST_CLIENT_ID = "test-client-id"
TEST_CLIENT_SECRET = "test-client-secret"
TEST_AUTH_SERVER = "https://account-d.docusign.com"
TEST_ACCOUNT_ID = "test-account-id"
TEST_USER_ID = "test-user-id"
TEST_BASE_PATH = "https://demo.docusign.net/restapi"
TEST_CALLBACK_URL = "https://example.com/docusign/callback"


def create_test_config(use_jwt_auth=False, private_key_path=None):
    """Creates a DocuSignConfig instance for testing"""
    return DocuSignConfig(
        client_id=TEST_CLIENT_ID,
        client_secret=TEST_CLIENT_SECRET,
        authorization_server=TEST_AUTH_SERVER,
        account_id=TEST_ACCOUNT_ID,
        user_id=TEST_USER_ID,
        private_key_path=private_key_path,
        base_path=TEST_BASE_PATH,
        use_jwt_auth=use_jwt_auth,
        callback_url=TEST_CALLBACK_URL
    )


def create_mock_response(status_code, json_data):
    """Creates a mock response object for testing API calls"""
    mock_response = MagicMock()
    mock_response.status_code = status_code
    mock_response.json.return_value = json_data
    
    # Set content attribute if needed for document content tests
    if "content" in json_data:
        mock_response.content = json_data["content"].encode("utf-8") if isinstance(json_data["content"], str) else json_data["content"]
    
    return mock_response


class TestDocuSignConfig:
    """Test cases for DocuSignConfig model"""
    
    def test_config_creation(self):
        """Test that DocuSignConfig can be created with valid parameters"""
        # Create config without JWT auth
        config = create_test_config(use_jwt_auth=False)
        
        # Verify all properties are set correctly
        assert config.client_id == TEST_CLIENT_ID
        assert config.client_secret == TEST_CLIENT_SECRET
        assert config.authorization_server == TEST_AUTH_SERVER
        assert config.account_id == TEST_ACCOUNT_ID
        assert config.user_id == TEST_USER_ID
        assert config.base_path == TEST_BASE_PATH
        assert config.use_jwt_auth is False
        assert config.callback_url == TEST_CALLBACK_URL
        
        # Create config with JWT auth and private key path
        with tempfile.NamedTemporaryFile() as temp_file:
            config = create_test_config(use_jwt_auth=True, private_key_path=temp_file.name)
            assert config.use_jwt_auth is True
            assert config.private_key_path == temp_file.name
    
    def test_config_validation(self):
        """Test that DocuSignConfig validates JWT auth requirements"""
        # Should raise ValueError when use_jwt_auth=True but no private_key_path
        with pytest.raises(ValueError):
            DocuSignConfig(
                client_id=TEST_CLIENT_ID,
                client_secret=TEST_CLIENT_SECRET,
                authorization_server=TEST_AUTH_SERVER,
                account_id=TEST_ACCOUNT_ID,
                user_id=TEST_USER_ID,
                base_path=TEST_BASE_PATH,
                use_jwt_auth=True  # No private_key_path provided
            )
        
        # Should not raise error when use_jwt_auth=False and no private_key_path
        config = DocuSignConfig(
            client_id=TEST_CLIENT_ID,
            client_secret=TEST_CLIENT_SECRET,
            authorization_server=TEST_AUTH_SERVER,
            account_id=TEST_ACCOUNT_ID,
            user_id=TEST_USER_ID,
            base_path=TEST_BASE_PATH,
            use_jwt_auth=False  # No private_key_path needed
        )
        assert config.use_jwt_auth is False


class TestDocuSignClient:
    """Test cases for DocuSignClient functionality"""
    
    def test_client_initialization(self):
        """Test that DocuSignClient initializes correctly"""
        config = create_test_config()
        client = DocuSignClient(config)
        
        # Verify all properties are set correctly
        assert client._config == config
        assert client._base_url == f"{config.base_path}/v2.1/accounts/{config.account_id}"
        assert client._account_id == config.account_id
        assert client._access_token is None
        assert client._token_expiration is None
    
    @patch('src.backend.app.integrations.docusign.client.requests.post')
    def test_authenticate_jwt(self, mock_post):
        """Test JWT authentication flow"""
        # Create mock response with access token
        mock_response = create_mock_response(200, {
            "access_token": "test-access-token",
            "expires_in": 3600  # 1 hour
        })
        mock_post.return_value = mock_response
        
        # Create client with JWT auth config (using a temporary file for private key)
        with tempfile.NamedTemporaryFile() as temp_file:
            # Write some content to the file
            temp_file.write(b"-----BEGIN PRIVATE KEY-----\nMIIEvQIBADANBgkqhkiG9w0BAQEFAASCBKcwggSjAgEAAoIBAQC7VJTUt9Us8cKj\nMzEfYyjiWA4R4/M2bS1GB4t7NXp98C3SC6dVMvDuictGeurT8jNbvJZHtCSuYEvu\nNMoSfm76oqFvAp8Gy0iz5sxjZmSnXyCdPEovGhLa0VzMaQ8s+CLOyS56YyCFGeJZ\n-----END PRIVATE KEY-----\n")
            temp_file.flush()
            
            config = create_test_config(use_jwt_auth=True, private_key_path=temp_file.name)
            client = DocuSignClient(config)
            
            # Test authenticate method
            result = client.authenticate()
            
            # Verify authentication was successful
            assert result is True
            assert client._access_token == "test-access-token"
            assert client._token_expiration is not None  # Should be set to future time
            
            # Verify that requests.post was called with correct parameters
            mock_post.assert_called_once()
            args, kwargs = mock_post.call_args
            assert kwargs["url"] == f"{TEST_AUTH_SERVER}/oauth/token"
            assert "grant_type" in kwargs["data"]
            assert kwargs["data"]["grant_type"] == "urn:ietf:params:oauth:grant-type:jwt-bearer"
    
    @patch('src.backend.app.integrations.docusign.client.requests.post')
    def test_authenticate_oauth(self, mock_post):
        """Test OAuth authentication flow"""
        # Create mock response with access token
        mock_response = create_mock_response(200, {
            "access_token": "test-access-token",
            "expires_in": 3600  # 1 hour
        })
        mock_post.return_value = mock_response
        
        # Create client with OAuth config (use_jwt_auth=False)
        config = create_test_config(use_jwt_auth=False)
        client = DocuSignClient(config)
        
        # Test authenticate method
        result = client.authenticate()
        
        # Verify authentication was successful
        assert result is True
        assert client._access_token == "test-access-token"
        assert client._token_expiration is not None  # Should be set to future time
        
        # Verify that requests.post was called with correct parameters
        mock_post.assert_called_once()
        args, kwargs = mock_post.call_args
        assert kwargs["url"] == f"{TEST_AUTH_SERVER}/oauth/token"
        assert kwargs["data"]["grant_type"] == "client_credentials"
        assert kwargs["data"]["client_id"] == TEST_CLIENT_ID
        assert kwargs["data"]["client_secret"] == TEST_CLIENT_SECRET
    
    @patch('src.backend.app.integrations.docusign.client.requests.post')
    def test_authenticate_failure(self, mock_post):
        """Test authentication failure handling"""
        # Create mock response with error
        mock_response = create_mock_response(401, {
            "error": "invalid_client",
            "error_description": "Invalid client credentials"
        })
        mock_post.return_value = mock_response
        mock_post.return_value.raise_for_status.side_effect = Exception("Authentication failed")
        
        # Create client
        config = create_test_config()
        client = DocuSignClient(config)
        
        # Test authenticate method
        result = client.authenticate()
        
        # Verify authentication failed
        assert result is False
        assert client._access_token is None
        assert client._token_expiration is None
    
    def test_is_token_valid(self):
        """Test token validation logic"""
        config = create_test_config()
        client = DocuSignClient(config)
        
        # Initially, token should be invalid (None)
        assert client._is_token_valid() is False
        
        # Set access token but no expiration
        client._access_token = "test-access-token"
        assert client._is_token_valid() is False
        
        # Set expiration to past time
        client._token_expiration = datetime.utcnow()
        assert client._is_token_valid() is False
        
        # Set expiration to future time
        client._token_expiration = datetime.utcnow().replace(year=datetime.utcnow().year + 1)
        assert client._is_token_valid() is True
    
    @patch('src.backend.app.integrations.docusign.client.requests.request')
    def test_make_request(self, mock_request):
        """Test making authenticated requests"""
        # Create mock response
        mock_response = create_mock_response(200, {"result": "success"})
        mock_request.return_value = mock_response
        
        # Create client with mocked authentication
        config = create_test_config()
        client = DocuSignClient(config)
        client._access_token = "test-access-token"
        client._token_expiration = datetime.utcnow().replace(year=datetime.utcnow().year + 1)
        
        # Test _make_request method
        result = client._make_request("GET", "test_endpoint", params={"param": "value"})
        
        # Verify result
        assert result == {"result": "success"}
        
        # Verify that requests.request was called with correct parameters
        mock_request.assert_called_once()
        args, kwargs = mock_request.call_args
        assert kwargs["method"] == "GET"
        assert kwargs["url"] == f"{client._base_url}/test_endpoint"
        assert kwargs["params"] == {"param": "value"}
        assert kwargs["headers"]["Authorization"] == "Bearer test-access-token"
    
    @patch('src.backend.app.integrations.docusign.client.requests.request')
    def test_make_request_error_handling(self, mock_request):
        """Test error handling in request method"""
        # Create client with mocked authentication
        config = create_test_config()
        client = DocuSignClient(config)
        client._access_token = "test-access-token"
        client._token_expiration = datetime.utcnow().replace(year=datetime.utcnow().year + 1)
        
        # Test ConnectionError
        mock_request.side_effect = ConnectionError("Connection failed")
        with pytest.raises(DocuSignConnectionError):
            client._make_request("GET", "test_endpoint")
        
        # Test Timeout
        mock_request.side_effect = TimeoutError("Request timed out")
        with pytest.raises(DocuSignTimeoutError):
            client._make_request("GET", "test_endpoint")
        
        # Test 401 error response
        mock_response = create_mock_response(401, {"error": "Unauthorized"})
        mock_request.side_effect = None
        mock_request.return_value = mock_response
        with pytest.raises(AuthenticationError):
            client._make_request("GET", "test_endpoint")
        
        # Test other error response
        mock_response = create_mock_response(500, {"error": "Internal Server Error"})
        mock_request.return_value = mock_response
        with pytest.raises(DocuSignResponseError):
            client._make_request("GET", "test_endpoint")
    
    @patch.object(DocuSignClient, '_make_request')
    def test_create_envelope(self, mock_make_request):
        """Test envelope creation functionality"""
        # Create mock envelope response
        envelope_id = str(uuid.uuid4())
        mock_response = {
            "envelopeId": envelope_id,
            "status": "sent",
            "statusDateTime": "2023-09-15T12:34:56Z",
            "uri": f"/envelopes/{envelope_id}"
        }
        mock_make_request.return_value = mock_response
        
        # Create client
        config = create_test_config()
        client = DocuSignClient(config)
        
        # Create test recipients and documents
        recipients = [
            Recipient(
                email="signer@example.com",
                name="Test Signer",
                recipient_id="1",
                recipient_type="signer"
            )
        ]
        
        documents = [
            DocumentInfo(
                document_id="1",
                name="Test Document",
                file_extension="pdf",
                document_base64="dGVzdCBkb2N1bWVudCBjb250ZW50" # "test document content" in base64
            )
        ]
        
        # Create envelope data
        envelope_data = EnvelopeCreate(
            email_subject="Test Envelope",
            email_body="Please sign this document",
            documents=documents,
            recipients=recipients,
            status="sent"
        )
        
        # Test create_envelope method
        envelope = client.create_envelope(envelope_data)
        
        # Verify envelope was created correctly
        assert envelope.envelope_id == envelope_id
        assert envelope.status == "sent"
        
        # Verify that _make_request was called with correct parameters
        mock_make_request.assert_called_once_with(
            method="POST",
            endpoint="envelopes",
            data=envelope_data.to_docusign_dict()
        )
    
    @patch.object(DocuSignClient, '_make_request')
    def test_get_envelope(self, mock_make_request):
        """Test retrieving envelope information"""
        # Create mock envelope response
        envelope_id = str(uuid.uuid4())
        mock_response = {
            "envelopeId": envelope_id,
            "status": "sent",
            "statusDateTime": "2023-09-15T12:34:56Z",
            "emailSubject": "Test Envelope"
        }
        mock_make_request.return_value = mock_response
        
        # Create client
        config = create_test_config()
        client = DocuSignClient(config)
        
        # Test get_envelope method
        envelope = client.get_envelope(envelope_id)
        
        # Verify envelope was retrieved correctly
        assert envelope.envelope_id == envelope_id
        assert envelope.status == "sent"
        assert envelope.email_subject == "Test Envelope"
        
        # Verify that _make_request was called with correct parameters
        mock_make_request.assert_called_once_with(
            method="GET",
            endpoint=f"envelopes/{envelope_id}"
        )
    
    @patch.object(DocuSignClient, '_make_request')
    @patch.object(DocuSignClient, 'get_envelope')
    def test_update_envelope_status(self, mock_get_envelope, mock_make_request):
        """Test updating envelope status"""
        # Create mock envelope response
        envelope_id = str(uuid.uuid4())
        mock_response = {
            "envelopeId": envelope_id,
            "status": "voided",
            "statusDateTime": "2023-09-15T14:34:56Z"
        }
        mock_make_request.return_value = mock_response
        
        # Mock get_envelope to return the updated envelope
        mock_get_envelope.return_value = Envelope.from_docusign_response(mock_response)
        
        # Create client
        config = create_test_config()
        client = DocuSignClient(config)
        
        # Create status update
        status_update = EnvelopeStatusUpdate(
            envelope_id=envelope_id,
            status="voided",
            status_reason="Testing envelope voiding"
        )
        
        # Test update_envelope_status method
        envelope = client.update_envelope_status(status_update)
        
        # Verify envelope status was updated correctly
        assert envelope.envelope_id == envelope_id
        assert envelope.status == "voided"
        
        # Verify that _make_request was called with correct parameters
        mock_make_request.assert_called_once_with(
            method="PUT",
            endpoint=f"envelopes/{envelope_id}",
            data=status_update.to_docusign_dict()
        )
        
        # Verify that get_envelope was called with correct envelope_id
        mock_get_envelope.assert_called_once_with(envelope_id)
    
    @patch.object(DocuSignClient, 'update_envelope_status')
    def test_void_envelope(self, mock_update_envelope_status):
        """Test voiding an envelope"""
        # Create mock envelope response
        envelope_id = str(uuid.uuid4())
        mock_envelope = Envelope(
            envelope_id=envelope_id,
            status="voided"
        )
        mock_update_envelope_status.return_value = mock_envelope
        
        # Create client
        config = create_test_config()
        client = DocuSignClient(config)
        
        # Test void_envelope method
        envelope = client.void_envelope(envelope_id, "Testing void functionality")
        
        # Verify envelope was voided correctly
        assert envelope.envelope_id == envelope_id
        assert envelope.status == "voided"
        
        # Verify that update_envelope_status was called with correct parameters
        mock_update_envelope_status.assert_called_once()
        args, kwargs = mock_update_envelope_status.call_args
        status_update = args[0]
        assert status_update.envelope_id == envelope_id
        assert status_update.status == "voided"
        assert status_update.status_reason == "Testing void functionality"
    
    @patch.object(DocuSignClient, '_make_request')
    def test_create_recipient_view(self, mock_make_request):
        """Test creating a recipient view for embedded signing"""
        # Create mock response with signing URL
        envelope_id = str(uuid.uuid4())
        mock_response = {
            "url": "https://demo.docusign.net/signing/xyz123"
        }
        mock_make_request.return_value = mock_response
        
        # Create client
        config = create_test_config()
        client = DocuSignClient(config)
        
        # Test create_recipient_view method
        signing_url = client.create_recipient_view(
            envelope_id=envelope_id,
            recipient_email="signer@example.com",
            recipient_name="Test Signer",
            return_url="https://example.com/return"
        )
        
        # Verify signing URL was created correctly
        assert signing_url.url == "https://demo.docusign.net/signing/xyz123"
        assert signing_url.envelope_id == envelope_id
        assert signing_url.recipient_id == "signer@example.com"
        
        # Verify that _make_request was called with correct parameters
        mock_make_request.assert_called_once()
        args, kwargs = mock_make_request.call_args
        assert kwargs["method"] == "POST"
        assert kwargs["endpoint"] == f"envelopes/{envelope_id}/views/recipient"
        assert kwargs["data"]["email"] == "signer@example.com"
        assert kwargs["data"]["userName"] == "Test Signer"
        assert kwargs["data"]["returnUrl"] == "https://example.com/return"
    
    @patch.object(DocuSignClient, '_make_request')
    def test_get_envelope_documents(self, mock_make_request):
        """Test retrieving documents from an envelope"""
        # Create mock response with document list
        envelope_id = str(uuid.uuid4())
        mock_response = {
            "envelopeId": envelope_id,
            "documents": [
                {
                    "documentId": "1",
                    "name": "Document 1",
                    "fileExtension": "pdf",
                    "uri": f"/envelopes/{envelope_id}/documents/1"
                },
                {
                    "documentId": "2",
                    "name": "Document 2",
                    "fileExtension": "pdf",
                    "uri": f"/envelopes/{envelope_id}/documents/2"
                }
            ]
        }
        mock_make_request.return_value = mock_response
        
        # Create client
        config = create_test_config()
        client = DocuSignClient(config)
        
        # Test get_envelope_documents method
        documents = client.get_envelope_documents(envelope_id)
        
        # Verify documents were retrieved correctly
        assert len(documents) == 2
        assert documents[0].document_id == "1"
        assert documents[0].name == "Document 1"
        assert documents[1].document_id == "2"
        assert documents[1].name == "Document 2"
        
        # Verify that _make_request was called with correct parameters
        mock_make_request.assert_called_once_with(
            method="GET",
            endpoint=f"envelopes/{envelope_id}/documents"
        )
    
    @patch.object(DocuSignClient, '_make_request')
    def test_get_document_content(self, mock_make_request):
        """Test retrieving document content"""
        # Create mock response with document content
        envelope_id = str(uuid.uuid4())
        document_id = "1"
        document_content = b"Test document content"
        
        # Mock the requests.get function since _make_request doesn't return binary content directly
        with patch('requests.get') as mock_get:
            mock_response = MagicMock()
            mock_response.status_code = 200
            mock_response.content = document_content
            mock_get.return_value = mock_response
            
            # Create client
            config = create_test_config()
            client = DocuSignClient(config)
            
            # Set access token for authorization header
            client._access_token = "test-access-token"
            
            # Test get_document_content method
            content = client.get_document_content(envelope_id, document_id)
            
            # Verify content was retrieved correctly
            assert content == document_content
            
            # Verify that requests.get was called with correct parameters
            mock_get.assert_called_once()
            args, kwargs = mock_get.call_args
            assert kwargs["url"] == f"{client._base_url}/envelopes/{envelope_id}/documents/{document_id}"
            assert "Authorization" in kwargs["headers"]
            assert kwargs["headers"]["Authorization"] == "Bearer test-access-token"
    
    @patch.object(DocuSignClient, '_make_request')
    def test_get_envelope_recipients(self, mock_make_request):
        """Test retrieving recipients from an envelope"""
        # Create mock response with recipient list
        envelope_id = str(uuid.uuid4())
        mock_response = {
            "signers": [
                {
                    "recipientId": "1",
                    "name": "Test Signer",
                    "email": "signer@example.com",
                    "status": "sent",
                    "routingOrder": "1"
                }
            ],
            "carbonCopies": [
                {
                    "recipientId": "2",
                    "name": "Test CC",
                    "email": "cc@example.com",
                    "status": "sent",
                    "routingOrder": "2"
                }
            ]
        }
        mock_make_request.return_value = mock_response
        
        # Create client
        config = create_test_config()
        client = DocuSignClient(config)
        
        # Test get_envelope_recipients method
        recipients = client.get_envelope_recipients(envelope_id)
        
        # Verify recipients were retrieved correctly
        assert len(recipients) == 2
        assert recipients[0].recipient_id == "1"
        assert recipients[0].name == "Test Signer"
        assert recipients[0].email == "signer@example.com"
        assert recipients[0].recipient_type == "signer"
        assert recipients[1].recipient_id == "2"
        assert recipients[1].name == "Test CC"
        assert recipients[1].email == "cc@example.com"
        assert recipients[1].recipient_type == "carbonCopy"
        
        # Verify that _make_request was called with correct parameters
        mock_make_request.assert_called_once_with(
            method="GET",
            endpoint=f"envelopes/{envelope_id}/recipients"
        )
    
    @patch.object(DocuSignClient, '_make_request')
    def test_get_templates(self, mock_make_request):
        """Test retrieving available templates"""
        # Create mock response with template list
        mock_response = {
            "envelopeTemplates": [
                {
                    "templateId": "template-1",
                    "name": "Test Template 1",
                    "description": "Template for testing",
                    "created": "2023-09-15T12:34:56Z",
                    "lastModified": "2023-09-15T12:34:56Z"
                },
                {
                    "templateId": "template-2",
                    "name": "Test Template 2",
                    "description": "Another template for testing",
                    "created": "2023-09-15T12:34:56Z",
                    "lastModified": "2023-09-15T12:34:56Z"
                }
            ]
        }
        mock_make_request.return_value = mock_response
        
        # Create client
        config = create_test_config()
        client = DocuSignClient(config)
        
        # Test get_templates method
        templates = client.get_templates()
        
        # Verify templates were retrieved correctly
        assert len(templates) == 2
        assert templates[0].template_id == "template-1"
        assert templates[0].name == "Test Template 1"
        assert templates[1].template_id == "template-2"
        assert templates[1].name == "Test Template 2"
        
        # Verify that _make_request was called with correct parameters
        mock_make_request.assert_called_once_with(
            method="GET",
            endpoint="templates"
        )
    
    @patch.object(DocuSignClient, '_make_request')
    def test_get_template(self, mock_make_request):
        """Test retrieving a specific template"""
        # Create mock response for a template
        template_id = "template-1"
        mock_response = {
            "templateId": template_id,
            "name": "Test Template",
            "description": "Template for testing",
            "created": "2023-09-15T12:34:56Z",
            "lastModified": "2023-09-15T12:34:56Z"
        }
        mock_make_request.return_value = mock_response
        
        # Create client
        config = create_test_config()
        client = DocuSignClient(config)
        
        # Test get_template method
        template = client.get_template(template_id)
        
        # Verify template was retrieved correctly
        assert template.template_id == template_id
        assert template.name == "Test Template"
        assert template.description == "Template for testing"
        
        # Verify that _make_request was called with correct parameters
        mock_make_request.assert_called_once_with(
            method="GET",
            endpoint=f"templates/{template_id}"
        )
    
    @patch.object(DocuSignClient, '_make_request')
    def test_create_envelope_from_template(self, mock_make_request):
        """Test creating an envelope from a template"""
        # Create mock response for envelope creation
        template_id = "template-1"
        envelope_id = str(uuid.uuid4())
        mock_response = {
            "envelopeId": envelope_id,
            "status": "sent",
            "statusDateTime": "2023-09-15T12:34:56Z"
        }
        mock_make_request.return_value = mock_response
        
        # Create client
        config = create_test_config()
        client = DocuSignClient(config)
        
        # Create test recipients
        recipients = [
            Recipient(
                email="signer@example.com",
                name="Test Signer",
                recipient_id="1",
                recipient_type="signer"
            )
        ]
        
        # Test create_envelope_from_template method
        envelope = client.create_envelope_from_template(
            template_id=template_id,
            recipients=recipients,
            email_subject="Test Template Envelope",
            email_body="Please sign this document from template",
            status="sent"
        )
        
        # Verify envelope was created correctly
        assert envelope.envelope_id == envelope_id
        assert envelope.status == "sent"
        
        # Verify that _make_request was called with correct parameters
        mock_make_request.assert_called_once()
        args, kwargs = mock_make_request.call_args
        assert kwargs["method"] == "POST"
        assert kwargs["endpoint"] == "envelopes"
        assert kwargs["data"]["templateId"] == template_id
        assert kwargs["data"]["emailSubject"] == "Test Template Envelope"
        assert kwargs["data"]["emailBlurb"] == "Please sign this document from template"
        assert len(kwargs["data"]["templateRoles"]) == 1
    
    def test_process_webhook_event(self):
        """Test processing webhook events from DocuSign"""
        # Create test webhook payload
        envelope_id = str(uuid.uuid4())
        webhook_payload = {
            "event": "envelope-status-changed",
            "apiVersion": "v2.1",
            "envelopeStatus": {
                "envelopeId": envelope_id,
                "status": "completed",
                "statusChangedDateTime": "2023-09-15T12:34:56Z"
            }
        }
        
        # Create client
        config = create_test_config()
        client = DocuSignClient(config)
        
        # Test process_webhook_event method
        webhook_event = client.process_webhook_event(webhook_payload)
        
        # Verify webhook event was processed correctly
        assert webhook_event.envelope_id == envelope_id
        assert webhook_event.status == "completed"
        assert webhook_event.event_type == "envelope-status-changed"
        assert webhook_event.raw_data == webhook_payload


class TestDocuSignModels:
    """Test cases for DocuSign data models"""
    
    def test_recipient_model(self):
        """Test Recipient model functionality"""
        # Create a recipient
        recipient = Recipient(
            email="signer@example.com",
            name="Test Signer",
            recipient_id="1",
            recipient_type="signer",
            routing_order="1",
            status="sent"
        )
        
        # Verify properties
        assert recipient.email == "signer@example.com"
        assert recipient.name == "Test Signer"
        assert recipient.recipient_id == "1"
        assert recipient.recipient_type == "signer"
        assert recipient.routing_order == "1"
        assert recipient.status == "sent"
        
        # Test to_docusign_dict method
        docusign_dict = recipient.to_docusign_dict()
        assert docusign_dict["email"] == "signer@example.com"
        assert docusign_dict["name"] == "Test Signer"
        assert docusign_dict["recipientId"] == "1"
        assert docusign_dict["routingOrder"] == "1"
        assert docusign_dict["recipientType"] == "signer"
        
        # Test from_docusign_response method
        response_data = {
            "email": "signer@example.com",
            "name": "Test Signer",
            "recipientId": "1",
            "routingOrder": "1",
            "status": "sent",
            "recipientType": "signer"
        }
        recipient_from_response = Recipient.from_docusign_response(response_data)
        assert recipient_from_response.email == "signer@example.com"
        assert recipient_from_response.name == "Test Signer"
        assert recipient_from_response.recipient_id == "1"
        assert recipient_from_response.recipient_type == "signer"
        assert recipient_from_response.status == "sent"
    
    def test_document_info_model(self):
        """Test DocumentInfo model functionality"""
        # Create a document
        document = DocumentInfo(
            document_id="1",
            name="Test Document",
            file_extension="pdf",
            document_base64="dGVzdCBkb2N1bWVudCBjb250ZW50" # "test document content" in base64
        )
        
        # Verify properties
        assert document.document_id == "1"
        assert document.name == "Test Document"
        assert document.file_extension == "pdf"
        assert document.document_base64 == "dGVzdCBkb2N1bWVudCBjb250ZW50"
        
        # Test to_docusign_dict method
        docusign_dict = document.to_docusign_dict()
        assert docusign_dict["documentId"] == "1"
        assert docusign_dict["name"] == "Test Document"
        assert docusign_dict["fileExtension"] == "pdf"
        assert docusign_dict["documentBase64"] == "dGVzdCBkb2N1bWVudCBjb250ZW50"
        
        # Test from_docusign_response method
        response_data = {
            "documentId": "1",
            "name": "Test Document",
            "fileExtension": "pdf",
            "uri": "/envelopes/abc123/documents/1"
        }
        document_from_response = DocumentInfo.from_docusign_response(response_data)
        assert document_from_response.document_id == "1"
        assert document_from_response.name == "Test Document"
        assert document_from_response.file_extension == "pdf"
    
    def test_envelope_create_model(self):
        """Test EnvelopeCreate model functionality"""
        # Create test recipients and documents
        recipients = [
            Recipient(
                email="signer@example.com",
                name="Test Signer",
                recipient_id="1",
                recipient_type="signer"
            )
        ]
        
        documents = [
            DocumentInfo(
                document_id="1",
                name="Test Document",
                file_extension="pdf",
                document_base64="dGVzdCBkb2N1bWVudCBjb250ZW50" # "test document content" in base64
            )
        ]
        
        # Create an envelope
        envelope_create = EnvelopeCreate(
            email_subject="Test Envelope",
            email_body="Please sign this document",
            documents=documents,
            recipients=recipients,
            status="sent",
            notification_uri="https://example.com/webhook",
            event_types=["envelope-sent", "envelope-completed"]
        )
        
        # Verify properties
        assert envelope_create.email_subject == "Test Envelope"
        assert envelope_create.email_body == "Please sign this document"
        assert envelope_create.documents == documents
        assert envelope_create.recipients == recipients
        assert envelope_create.status == "sent"
        assert envelope_create.notification_uri == "https://example.com/webhook"
        assert envelope_create.event_types == ["envelope-sent", "envelope-completed"]
        
        # Test to_docusign_dict method
        docusign_dict = envelope_create.to_docusign_dict()
        assert docusign_dict["emailSubject"] == "Test Envelope"
        assert docusign_dict["emailBlurb"] == "Please sign this document"
        assert docusign_dict["status"] == "sent"
        assert "documents" in docusign_dict
        assert "recipients" in docusign_dict
        assert "eventNotification" in docusign_dict
        
        # Test status validation
        with pytest.raises(ValueError):
            EnvelopeCreate(
                email_subject="Test Envelope",
                documents=documents,
                recipients=recipients,
                status="invalid_status"  # Invalid status
            )
    
    def test_envelope_model(self):
        """Test Envelope model functionality"""
        # Create an envelope
        envelope_id = str(uuid.uuid4())
        envelope = Envelope(
            envelope_id=envelope_id,
            status="sent",
            email_subject="Test Envelope",
            created_datetime=datetime.utcnow()
        )
        
        # Verify properties
        assert envelope.envelope_id == envelope_id
        assert envelope.status == "sent"
        assert envelope.email_subject == "Test Envelope"
        
        # Test from_docusign_response method
        response_data = {
            "envelopeId": envelope_id,
            "status": "sent",
            "statusChangedDateTime": "2023-09-15T12:34:56Z",
            "createdDateTime": "2023-09-15T12:30:00Z",
            "sentDateTime": "2023-09-15T12:31:00Z",
            "emailSubject": "Test Envelope",
            "recipients": {
                "signers": [
                    {
                        "recipientId": "1",
                        "name": "Test Signer",
                        "email": "signer@example.com",
                        "status": "sent",
                        "routingOrder": "1"
                    }
                ]
            }
        }
        envelope_from_response = Envelope.from_docusign_response(response_data)
        assert envelope_from_response.envelope_id == envelope_id
        assert envelope_from_response.status == "sent"
        assert envelope_from_response.email_subject == "Test Envelope"
        assert len(envelope_from_response.recipients) == 1
        assert envelope_from_response.recipients[0].email == "signer@example.com"
    
    def test_envelope_status_update_model(self):
        """Test EnvelopeStatusUpdate model functionality"""
        # Create a status update
        envelope_id = str(uuid.uuid4())
        status_update = EnvelopeStatusUpdate(
            envelope_id=envelope_id,
            status="voided",
            status_reason="Testing status update"
        )
        
        # Verify properties
        assert status_update.envelope_id == envelope_id
        assert status_update.status == "voided"
        assert status_update.status_reason == "Testing status update"
        
        # Test to_docusign_dict method
        docusign_dict = status_update.to_docusign_dict()
        assert docusign_dict["status"] == "voided"
        assert docusign_dict["statusReason"] == "Testing status update"
        
        # Test status validation
        with pytest.raises(ValueError):
            EnvelopeStatusUpdate(
                envelope_id=envelope_id,
                status="invalid_status"  # Invalid status
            )
    
    def test_webhook_event_model(self):
        """Test WebhookEvent model functionality"""
        # Create a webhook event
        envelope_id = str(uuid.uuid4())
        webhook_event = WebhookEvent(
            envelope_id=envelope_id,
            status="completed",
            event_type="envelope-completed",
            status_changed_datetime=datetime.utcnow()
        )
        
        # Verify properties
        assert webhook_event.envelope_id == envelope_id
        assert webhook_event.status == "completed"
        assert webhook_event.event_type == "envelope-completed"
        
        # Test from_docusign_payload method
        payload = {
            "event": "envelope-completed",
            "envelopeStatus": {
                "envelopeId": envelope_id,
                "status": "completed",
                "statusChangedDateTime": "2023-09-15T12:34:56Z"
            }
        }
        webhook_from_payload = WebhookEvent.from_docusign_payload(payload)
        assert webhook_from_payload.envelope_id == envelope_id
        assert webhook_from_payload.status == "completed"
        assert webhook_from_payload.event_type == "envelope-completed"
        assert webhook_from_payload.raw_data == payload
    
    def test_signing_url_model(self):
        """Test SigningUrl model functionality"""
        # Create a signing URL
        envelope_id = str(uuid.uuid4())
        signing_url = SigningUrl(
            url="https://demo.docusign.net/signing/xyz123",
            envelope_id=envelope_id,
            recipient_id="signer@example.com"
        )
        
        # Verify properties
        assert signing_url.url == "https://demo.docusign.net/signing/xyz123"
        assert signing_url.envelope_id == envelope_id
        assert signing_url.recipient_id == "signer@example.com"
        
        # Test from_docusign_response method
        response_data = {
            "url": "https://demo.docusign.net/signing/xyz123"
        }
        signing_url_from_response = SigningUrl.from_docusign_response(
            response_data, 
            envelope_id=envelope_id,
            recipient_id="signer@example.com"
        )
        assert signing_url_from_response.url == "https://demo.docusign.net/signing/xyz123"
        assert signing_url_from_response.envelope_id == envelope_id
        assert signing_url_from_response.recipient_id == "signer@example.com"
    
    def test_template_info_model(self):
        """Test TemplateInfo model functionality"""
        # Create a template
        template_id = "template-1"
        template = TemplateInfo(
            template_id=template_id,
            name="Test Template",
            description="Template for testing"
        )
        
        # Verify properties
        assert template.template_id == template_id
        assert template.name == "Test Template"
        assert template.description == "Template for testing"
        
        # Test from_docusign_response method
        response_data = {
            "templateId": template_id,
            "name": "Test Template",
            "description": "Template for testing",
            "created": "2023-09-15T12:34:56Z",
            "lastModified": "2023-09-15T12:34:56Z",
            "recipients": {
                "signers": [
                    {
                        "recipientId": "1",
                        "name": "Test Signer",
                        "email": "signer@example.com",
                        "routingOrder": "1"
                    }
                ]
            }
        }
        template_from_response = TemplateInfo.from_docusign_response(response_data)
        assert template_from_response.template_id == template_id
        assert template_from_response.name == "Test Template"
        assert template_from_response.description == "Template for testing"
        assert len(template_from_response.recipients) == 1
        assert template_from_response.recipients[0].email == "signer@example.com"