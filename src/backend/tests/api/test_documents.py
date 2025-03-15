import json
import uuid
import io

import pytest
from fastapi import status
from io import BytesIO

from ..conftest import client, db_session, pharma_token_headers, cro_token_headers, test_submission
from ...app.constants.document_types import DocumentType, DOCUMENT_STATUS

def test_create_upload_url(client, pharma_token_headers, test_submission):
    """Test generating a presigned URL for document upload"""
    # Create upload URL request data with filename, document type, and submission ID
    request_data = {
        "filename": "test_document.pdf",
        "document_type": "MATERIAL_TRANSFER_AGREEMENT",
        "submission_id": str(test_submission.id)
    }
    # Make POST request to /api/v1/documents/upload-url with request data
    response = client.post("/api/v1/documents/upload-url", json=request_data, headers=pharma_token_headers)
    # Verify response status code is 200 OK
    assert response.status_code == status.HTTP_200_OK
    # Verify response contains document_id, upload_url, and upload_fields
    response_data = response.json()
    assert "document_id" in response_data
    assert "upload_url" in response_data
    assert "upload_fields" in response_data
    # Verify document_id is a valid UUID
    try:
        uuid.UUID(response_data["document_id"])
    except ValueError:
        assert False, "document_id is not a valid UUID"

def test_upload_document(client, pharma_token_headers, test_submission):
    """Test uploading a document directly via the API"""
    # Create test file content as bytes
    file_content = b"Test document content"
    # Create file object using BytesIO
    file_obj = BytesIO(file_content)
    file_obj.name = "test_document.pdf"
    # Create multipart form data with file, document_type, and submission_id
    form_data = {
        "file": (file_obj.name, file_obj, "application/pdf"),
        "document_type": "MATERIAL_TRANSFER_AGREEMENT",
        "submission_id": str(test_submission.id)
    }
    # Make POST request to /api/v1/documents/upload with form data
    response = client.post("/api/v1/documents/upload", files=form_data, headers=pharma_token_headers)
    # Verify response status code is 201 CREATED
    assert response.status_code == status.HTTP_200_OK
    # Verify response contains document details including id, name, type, and status
    response_data = response.json()
    assert "id" in response_data
    assert "name" in response_data
    assert "type" in response_data
    assert "status" in response_data
    # Verify document status is DRAFT
    assert response_data["status"] == "DRAFT"

def test_get_document(client, pharma_token_headers, test_submission):
    """Test retrieving a document by ID"""
    # Upload a test document via API
    file_content = b"Test document content"
    file_obj = BytesIO(file_content)
    file_obj.name = "test_document.pdf"
    form_data = {
        "file": (file_obj.name, file_obj, "application/pdf"),
        "document_type": "MATERIAL_TRANSFER_AGREEMENT",
        "submission_id": str(test_submission.id)
    }
    response = client.post("/api/v1/documents/upload", files=form_data, headers=pharma_token_headers)
    assert response.status_code == status.HTTP_200_OK
    document_id = response.json()["id"]
    # Make GET request to /api/v1/documents/{document_id}
    response = client.get(f"/api/v1/documents/{document_id}", headers=pharma_token_headers)
    # Verify response status code is 200 OK
    assert response.status_code == status.HTTP_200_OK
    # Verify response contains expected document details
    response_data = response.json()
    assert response_data["id"] == document_id
    assert response_data["name"] == file_obj.name
    assert response_data["type"] == "MATERIAL_TRANSFER_AGREEMENT"
    # Verify response includes presigned_url for document access
    assert "presigned_url" in response_data

def test_get_documents_by_submission(client, pharma_token_headers, test_submission):
    """Test retrieving all documents for a specific submission"""
    # Upload multiple test documents for the same submission
    num_documents = 3
    document_ids = []
    for i in range(num_documents):
        file_content = f"Test document content {i}".encode()
        file_obj = BytesIO(file_content)
        file_obj.name = f"test_document_{i}.pdf"
        form_data = {
            "file": (file_obj.name, file_obj, "application/pdf"),
            "document_type": "MATERIAL_TRANSFER_AGREEMENT",
            "submission_id": str(test_submission.id)
        }
        response = client.post("/api/v1/documents/upload", files=form_data, headers=pharma_token_headers)
        assert response.status_code == status.HTTP_200_OK
        document_ids.append(response.json()["id"])
    # Make GET request to /api/v1/documents/submission/{submission_id}
    response = client.get(f"/api/v1/documents/submission/{test_submission.id}", headers=pharma_token_headers)
    # Verify response status code is 200 OK
    assert response.status_code == status.HTTP_200_OK
    # Verify response is a list containing all uploaded documents
    response_data = response.json()
    assert isinstance(response_data, list)
    assert len(response_data) == num_documents
    # Verify each document in the list has expected fields
    for doc in response_data:
        assert "id" in doc
        assert "name" in doc
        assert "type" in doc
        # Verify each document has a presigned_url
        assert "presigned_url" in doc

def test_get_required_documents(client, pharma_token_headers, test_submission):
    """Test retrieving required documents for a submission"""
    # Make GET request to /api/v1/documents/required/{submission_id}
    response = client.get(f"/api/v1/documents/required/{test_submission.id}", headers=pharma_token_headers)
    # Verify response status code is 200 OK
    assert response.status_code == status.HTTP_200_OK
    # Verify response contains list of required document types
    response_data = response.json()
    assert isinstance(response_data, list)
    # Verify required documents include MTA, NDA, and Experiment Specification
    required_types = [item['type'] for item in response_data]
    assert "MATERIAL_TRANSFER_AGREEMENT" in required_types
    assert "NON_DISCLOSURE_AGREEMENT" in required_types
    assert "EXPERIMENT_SPECIFICATION" in required_types
    # Verify each document type has completion status (completed or missing)
    for doc_type in response_data:
        assert "type" in doc_type
        assert "completed" in doc_type

def test_update_document(client, pharma_token_headers, test_submission):
    """Test updating an existing document's metadata"""
    # Upload a test document via API
    file_content = b"Test document content"
    file_obj = BytesIO(file_content)
    file_obj.name = "test_document.pdf"
    form_data = {
        "file": (file_obj.name, file_obj, "application/pdf"),
        "document_type": "MATERIAL_TRANSFER_AGREEMENT",
        "submission_id": str(test_submission.id)
    }
    response = client.post("/api/v1/documents/upload", files=form_data, headers=pharma_token_headers)
    assert response.status_code == status.HTTP_200_OK
    document_id = response.json()["id"]
    # Create update data with new name and description
    update_data = {
        "name": "updated_document.pdf",
        "description": "Updated description"
    }
    # Make PUT request to /api/v1/documents/{document_id} with update data
    response = client.put(f"/api/v1/documents/{document_id}", json=update_data, headers=pharma_token_headers)
    # Verify response status code is 200 OK
    assert response.status_code == status.HTTP_200_OK
    # Verify response contains updated fields
    response_data = response.json()
    assert response_data["name"] == "updated_document.pdf"
    assert response_data["description"] == "Updated description"
    # Verify other fields remain unchanged
    assert response_data["id"] == document_id
    assert response_data["type"] == "MATERIAL_TRANSFER_AGREEMENT"

def test_delete_document(client, pharma_token_headers, test_submission):
    """Test deleting a document"""
    # Upload a test document via API
    file_content = b"Test document content"
    file_obj = BytesIO(file_content)
    file_obj.name = "test_document.pdf"
    form_data = {
        "file": (file_obj.name, file_obj, "application/pdf"),
        "document_type": "MATERIAL_TRANSFER_AGREEMENT",
        "submission_id": str(test_submission.id)
    }
    response = client.post("/api/v1/documents/upload", files=form_data, headers=pharma_token_headers)
    assert response.status_code == status.HTTP_200_OK
    document_id = response.json()["id"]
    # Make DELETE request to /api/v1/documents/{document_id}
    response = client.delete(f"/api/v1/documents/{document_id}", headers=pharma_token_headers)
    # Verify response status code is 200 OK
    assert response.status_code == status.HTTP_200_OK
    # Verify response contains success message
    assert response.json()["message"] == "Document deleted successfully"
    # Make GET request to /api/v1/documents/{document_id}
    response = client.get(f"/api/v1/documents/{document_id}", headers=pharma_token_headers)
    # Verify GET request returns 404 NOT_FOUND
    assert response.status_code == status.HTTP_404_NOT_FOUND

def test_download_document(client, pharma_token_headers, test_submission):
    """Test downloading a document's content"""
    # Upload a test document with known content
    file_content = b"Test document content"
    file_obj = BytesIO(file_content)
    file_obj.name = "test_document.pdf"
    form_data = {
        "file": (file_obj.name, file_obj, "application/pdf"),
        "document_type": "MATERIAL_TRANSFER_AGREEMENT",
        "submission_id": str(test_submission.id)
    }
    response = client.post("/api/v1/documents/upload", files=form_data, headers=pharma_token_headers)
    assert response.status_code == status.HTTP_200_OK
    document_id = response.json()["id"]
    # Make GET request to /api/v1/documents/{document_id}/download
    response = client.get(f"/api/v1/documents/{document_id}/download", headers=pharma_token_headers)
    # Verify response status code is 200 OK
    assert response.status_code == status.HTTP_200_OK
    # Verify response content matches the uploaded content
    assert response.content == file_content
    # Verify response content-type header is correct
    assert response.headers["content-type"] == "application/pdf"

def test_filter_documents(client, pharma_token_headers, test_submission):
    """Test filtering documents based on criteria"""
    # Upload multiple test documents with different types and statuses
    file_content = b"Test document content"
    file_obj = BytesIO(file_content)
    file_obj.name = "test_document_1.pdf"
    form_data = {
        "file": (file_obj.name, file_obj, "application/pdf"),
        "document_type": "MATERIAL_TRANSFER_AGREEMENT",
        "submission_id": str(test_submission.id)
    }
    response = client.post("/api/v1/documents/upload", files=form_data, headers=pharma_token_headers)
    assert response.status_code == status.HTTP_200_OK
    doc1_id = response.json()["id"]

    file_obj = BytesIO(file_content)
    file_obj.name = "test_document_2.pdf"
    form_data = {
        "file": (file_obj.name, file_obj, "application/pdf"),
        "document_type": "EXPERIMENT_SPECIFICATION",
        "submission_id": str(test_submission.id)
    }
    response = client.post("/api/v1/documents/upload", files=form_data, headers=pharma_token_headers)
    assert response.status_code == status.HTTP_200_OK
    doc2_id = response.json()["id"]
    # Create filter criteria for document type
    filter_data = {"type": ["MATERIAL_TRANSFER_AGREEMENT"]}
    # Make POST request to /api/v1/documents/filter with filter criteria
    response = client.post("/api/v1/documents/filter", json=filter_data, headers=pharma_token_headers)
    # Verify response status code is 200 OK
    assert response.status_code == status.HTTP_200_OK
    # Verify response contains only documents matching filter criteria
    response_data = response.json()
    assert isinstance(response_data["items"], list)
    assert len(response_data["items"]) == 1
    assert response_data["items"][0]["id"] == doc1_id
    # Create filter criteria for document status
    filter_data = {"status": ["DRAFT"]}
    # Make POST request with status filter criteria
    response = client.post("/api/v1/documents/filter", json=filter_data, headers=pharma_token_headers)
    # Verify response status code is 200 OK
    assert response.status_code == status.HTTP_200_OK
    # Verify response contains only documents with matching status
    response_data = response.json()
    assert isinstance(response_data["items"], list)
    assert len(response_data["items"]) == 2
    # Test pagination parameters (skip, limit)
    response = client.post("/api/v1/documents/filter?skip=0&limit=1", json=filter_data, headers=pharma_token_headers)
    assert response.status_code == status.HTTP_200_OK
    response_data = response.json()
    assert len(response_data["items"]) == 1
    assert response_data["total"] == 2
    assert response_data["page"] == 1
    assert response_data["size"] == 1
    assert response_data["pages"] == 2

def test_request_signature(client, pharma_token_headers, test_submission):
    """Test requesting e-signatures for a document"""
    # Upload a test document via API
    file_content = b"Test document content"
    file_obj = BytesIO(file_content)
    file_obj.name = "test_document.pdf"
    form_data = {
        "file": (file_obj.name, file_obj, "application/pdf"),
        "document_type": "MATERIAL_TRANSFER_AGREEMENT",
        "submission_id": str(test_submission.id)
    }
    response = client.post("/api/v1/documents/upload", files=form_data, headers=pharma_token_headers)
    assert response.status_code == status.HTTP_200_OK
    document_id = response.json()["id"]
    # Create signature request data with document_id and signers list
    signature_request_data = {
        "document_id": document_id,
        "signers": [
            {"email": "signer1@example.com", "name": "Signer One"},
            {"email": "signer2@example.com", "name": "Signer Two"}
        ]
    }
    # Make POST request to /api/v1/documents/signature/request with request data
    response = client.post("/api/v1/documents/signature/request", json=signature_request_data, headers=pharma_token_headers)
    # Verify response status code is 200 OK
    assert response.status_code == status.HTTP_200_OK
    # Verify response contains envelope_id and signing_url
    response_data = response.json()
    assert "envelope_id" in response_data
    assert "signing_url" in response_data
    # Make GET request to /api/v1/documents/{document_id}
    response = client.get(f"/api/v1/documents/{document_id}", headers=pharma_token_headers)
    # Verify document status is updated to PENDING_SIGNATURE
    assert response.json()["status"] == "PENDING_SIGNATURE"

def test_get_signing_url(client, pharma_token_headers, test_submission):
    """Test getting a signing URL for a specific recipient"""
    # Upload a test document and request signatures
    file_content = b"Test document content"
    file_obj = BytesIO(file_content)
    file_obj.name = "test_document.pdf"
    form_data = {
        "file": (file_obj.name, file_obj, "application/pdf"),
        "document_type": "MATERIAL_TRANSFER_AGREEMENT",
        "submission_id": str(test_submission.id)
    }
    response = client.post("/api/v1/documents/upload", files=form_data, headers=pharma_token_headers)
    assert response.status_code == status.HTTP_200_OK
    document_id = response.json()["id"]
    signature_request_data = {
        "document_id": document_id,
        "signers": [
            {"email": "signer1@example.com", "name": "Signer One"},
            {"email": "signer2@example.com", "name": "Signer Two"}
        ]
    }
    response = client.post("/api/v1/documents/signature/request", json=signature_request_data, headers=pharma_token_headers)
    assert response.status_code == status.HTTP_200_OK
    # Extract document ID from response
    # Make GET request to /api/v1/documents/{document_id}/signing-url with recipient parameters
    response = client.get(
        f"/api/v1/documents/{document_id}/signing-url?recipient_email=signer1@example.com&recipient_name=Signer One",
        headers=pharma_token_headers
    )
    # Verify response status code is 200 OK
    assert response.status_code == status.HTTP_200_OK
    # Verify response contains signing_url
    assert "signing_url" in response.json()

def test_process_signature_webhook(client, pharma_token_headers, test_submission):
    """Test processing DocuSign webhook events for signature updates"""
    # Upload a test document and request signatures
    file_content = b"Test document content"
    file_obj = BytesIO(file_content)
    file_obj.name = "test_document.pdf"
    form_data = {
        "file": (file_obj.name, file_obj, "application/pdf"),
        "document_type": "MATERIAL_TRANSFER_AGREEMENT",
        "submission_id": str(test_submission.id)
    }
    response = client.post("/api/v1/documents/upload", files=form_data, headers=pharma_token_headers)
    assert response.status_code == status.HTTP_200_OK
    document_id = response.json()["id"]
    signature_request_data = {
        "document_id": document_id,
        "signers": [
            {"email": "signer1@example.com", "name": "Signer One"},
            {"email": "signer2@example.com", "name": "Signer Two"}
        ]
    }
    response = client.post("/api/v1/documents/signature/request", json=signature_request_data, headers=pharma_token_headers)
    assert response.status_code == status.HTTP_200_OK
    envelope_id = response.json()["envelope_id"]
    # Create mock DocuSign webhook data for completed signature
    webhook_data = {
        "envelopeStatus": {
            "envelopeId": envelope_id,
            "status": "Completed"
        }
    }
    # Make POST request to /api/v1/documents/signature/webhook with webhook data
    response = client.post("/api/v1/documents/signature/webhook", json=webhook_data, headers=pharma_token_headers)
    # Verify response status code is 200 OK
    assert response.status_code == status.HTTP_200_OK
    # Verify response contains success message
    assert response.json()["message"] == "Webhook processed successfully"
    # Make GET request to /api/v1/documents/{document_id}
    response = client.get(f"/api/v1/documents/{document_id}", headers=pharma_token_headers)
    # Verify document status is updated to SIGNED
    assert response.json()["status"] == "SIGNED"
    # Verify is_signed flag is set to true
    assert response.json()["is_signed"] == True

def test_unauthorized_access(client, pharma_token_headers, test_submission):
    """Test that unauthorized users cannot access document endpoints"""
    # Upload a test document with authenticated user
    file_content = b"Test document content"
    file_obj = BytesIO(file_content)
    file_obj.name = "test_document.pdf"
    form_data = {
        "file": (file_obj.name, file_obj, "application/pdf"),
        "document_type": "MATERIAL_TRANSFER_AGREEMENT",
        "submission_id": str(test_submission.id)
    }
    response = client.post("/api/v1/documents/upload", files=form_data, headers=pharma_token_headers)
    assert response.status_code == status.HTTP_200_OK
    document_id = response.json()["id"]
    # Make GET request to /api/v1/documents/{document_id} without authentication
    response = client.get(f"/api/v1/documents/{document_id}")
    # Verify response status code is 401 UNAUTHORIZED
    assert response.status_code == status.HTTP_401_UNAUTHORIZED
    # Make PUT request to update document without authentication
    response = client.put(f"/api/v1/documents/{document_id}", json={"name": "updated_name.pdf"})
    # Verify response status code is 401 UNAUTHORIZED
    assert response.status_code == status.HTTP_401_UNAUTHORIZED
    # Make DELETE request without authentication
    response = client.delete(f"/api/v1/documents/{document_id}")
    # Verify response status code is 401 UNAUTHORIZED
    assert response.status_code == status.HTTP_401_UNAUTHORIZED

def test_cross_submission_access(client, pharma_token_headers, cro_token_headers, test_submission, db_session):
    """Test that users cannot access documents from other submissions"""
    from src.backend.app.models.submission import Submission
    # Create two test submissions with different owners
    submission2 = Submission(
        name="Submission 2",
        cro_service_id=test_submission.cro_service_id,
        created_by=uuid.uuid4(),  # Different user ID
        created_at=datetime.now(),
        updated_at=datetime.now()
    )
    db_session.add(submission2)
    db_session.commit()
    # Upload a document to the first submission
    file_content = b"Test document content"
    file_obj = BytesIO(file_content)
    file_obj.name = "test_document.pdf"
    form_data = {
        "file": (file_obj.name, file_obj, "application/pdf"),
        "document_type": "MATERIAL_TRANSFER_AGREEMENT",
        "submission_id": str(test_submission.id)
    }
    response = client.post("/api/v1/documents/upload", files=form_data, headers=pharma_token_headers)
    assert response.status_code == status.HTTP_200_OK
    document_id = response.json()["id"]
    # Try to access the document using the second user's authentication
    response = client.get(f"/api/v1/documents/{document_id}", headers=cro_token_headers)
    # Verify response status code is 403 FORBIDDEN
    assert response.status_code == status.HTTP_403_FORBIDDEN
    # Try to update the document using the second user's authentication
    response = client.put(f"/api/v1/documents/{document_id}", json={"name": "updated_name.pdf"}, headers=cro_token_headers)
    # Verify response status code is 403 FORBIDDEN
    assert response.status_code == status.HTTP_403_FORBIDDEN

def test_invalid_document_data(client, pharma_token_headers, test_submission):
    """Test validation of invalid document data"""
    # Create upload URL request with invalid document type
    request_data = {
        "filename": "test_document.pdf",
        "document_type": "INVALID_TYPE",
        "submission_id": str(test_submission.id)
    }
    # Make POST request to /api/v1/documents/upload-url with invalid data
    response = client.post("/api/v1/documents/upload-url", json=request_data, headers=pharma_token_headers)
    # Verify response status code is 422 UNPROCESSABLE_ENTITY
    assert response.status_code == status.HTTP_422_UNPROCESSABLE_ENTITY
    # Create upload URL request with non-existent submission ID
    request_data = {
        "filename": "test_document.pdf",
        "document_type": "MATERIAL_TRANSFER_AGREEMENT",
        "submission_id": str(uuid.uuid4())
    }
    # Make POST request with invalid submission ID
    response = client.post("/api/v1/documents/upload-url", json=request_data, headers=pharma_token_headers)
    # Verify response status code is 404 NOT_FOUND
    assert response.status_code == status.HTTP_404_NOT_FOUND
    # Create update data with invalid status value
    file_content = b"Test document content"
    file_obj = BytesIO(file_content)
    file_obj.name = "test_document.pdf"
    form_data = {
        "file": (file_obj.name, file_obj, "application/pdf"),
        "document_type": "MATERIAL_TRANSFER_AGREEMENT",
        "submission_id": str(test_submission.id)
    }
    response = client.post("/api/v1/documents/upload", files=form_data, headers=pharma_token_headers)
    assert response.status_code == status.HTTP_200_OK
    document_id = response.json()["id"]
    update_data = {"status": "INVALID_STATUS"}
    # Make PUT request with invalid status
    response = client.put(f"/api/v1/documents/{document_id}", json=update_data, headers=pharma_token_headers)
    # Verify response status code is 422 UNPROCESSABLE_ENTITY
    assert response.status_code == status.HTTP_422_UNPROCESSABLE_ENTITY

def test_cro_document_access(client, pharma_token_headers, cro_token_headers, test_submission):
    """Test CRO access to documents after submission"""
    # Upload a document to a submission as pharma user
    file_content = b"Test document content"
    file_obj = BytesIO(file_content)
    file_obj.name = "test_document.pdf"
    form_data = {
        "file": (file_obj.name, file_obj, "application/pdf"),
        "document_type": "MATERIAL_TRANSFER_AGREEMENT",
        "submission_id": str(test_submission.id)
    }
    response = client.post("/api/v1/documents/upload", files=form_data, headers=pharma_token_headers)
    assert response.status_code == status.HTTP_200_OK
    document_id = response.json()["id"]
    # Try to access the document as CRO user before submission is sent to CRO
    response = client.get(f"/api/v1/documents/{document_id}", headers=cro_token_headers)
    # Verify response status code is 403 FORBIDDEN
    assert response.status_code == status.HTTP_403_FORBIDDEN
    # Update submission status to SUBMITTED (sent to CRO)
    update_data = {"status": "SUBMITTED"}
    response = client.put(f"/api/v1/submissions/{test_submission.id}", json=update_data, headers=pharma_token_headers)
    assert response.status_code == status.HTTP_200_OK
    # Try to access the document as CRO user after submission
    response = client.get(f"/api/v1/documents/{document_id}", headers=cro_token_headers)
    # Verify response status code is 200 OK
    assert response.status_code == status.HTTP_200_OK
    # Verify CRO user can view but not modify the document
    response_data = response.json()
    assert response_data["id"] == document_id