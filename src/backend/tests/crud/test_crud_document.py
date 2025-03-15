import pytest
from uuid import uuid4
from datetime import datetime

from ..conftest import db_session, test_user
from ...app.crud.crud_document import document
from ...app.models.document import Document
from ...app.models.submission import Submission
from ...app.schemas.document import DocumentCreate, DocumentUpdate, DocumentFilter
from ...app.constants.document_types import DocumentType, DOCUMENT_STATUS


def create_test_submission(db_session, user_id):
    """Helper function to create a test submission for document tests"""
    submission_data = {
        "name": "Test Submission",
        "created_by": user_id,
        "cro_service_id": uuid4()
    }
    submission = Submission(**submission_data)
    db_session.add(submission)
    db_session.commit()
    return submission


def create_test_document(db_session, submission_id, user_id, doc_type, name, status):
    """Helper function to create a test document"""
    document_data = {
        "name": name,
        "type": doc_type,
        "submission_id": submission_id,
        "uploaded_by": user_id,
        "url": "http://example.com/document.pdf",
        "status": status
    }
    document = Document(**document_data)
    db_session.add(document)
    db_session.commit()
    return document


def test_create_document(db_session, test_user):
    """Test creating a document using the CRUD service"""
    test_submission = create_test_submission(db_session, test_user.id)
    document_create = DocumentCreate(
        name="Test Document",
        type=DocumentType.MATERIAL_TRANSFER_AGREEMENT,
        submission_id=test_submission.id,
        uploaded_by=test_user.id,
        content_type="application/pdf",
        file_size=1024
    )
    created_document = document.create_with_owner(document_create, test_user.id, db_session)
    assert created_document.name == "Test Document"
    assert created_document.type == DocumentType.MATERIAL_TRANSFER_AGREEMENT
    assert created_document.status == "DRAFT"
    assert created_document.is_signed is False


def test_get_document(db_session, test_user):
    """Test retrieving a document by ID"""
    test_submission = create_test_submission(db_session, test_user.id)
    test_document = create_test_document(db_session, test_submission.id, test_user.id, DocumentType.MATERIAL_TRANSFER_AGREEMENT, "Test Document", "DRAFT")
    retrieved_document = document.get(test_document.id, db_session)
    assert retrieved_document.id == test_document.id
    assert retrieved_document.name == "Test Document"

    non_existent_document = document.get(uuid4(), db_session)
    assert non_existent_document is None


def test_get_by_submission(db_session, test_user):
    """Test retrieving all documents for a submission"""
    test_submission = create_test_submission(db_session, test_user.id)
    document1 = create_test_document(db_session, test_submission.id, test_user.id, DocumentType.MATERIAL_TRANSFER_AGREEMENT, "Document 1", "DRAFT")
    document2 = create_test_document(db_session, test_submission.id, test_user.id, DocumentType.NON_DISCLOSURE_AGREEMENT, "Document 2", "SIGNED")
    documents = document.get_by_submission(test_submission.id, db_session)
    assert len(documents) == 2
    assert document1 in documents
    assert document2 in documents

    empty_documents = document.get_by_submission(uuid4(), db_session)
    assert len(empty_documents) == 0


def test_get_with_presigned_url(db_session, test_user, monkeypatch):
    """Test retrieving a document with a presigned URL"""
    test_submission = create_test_submission(db_session, test_user.id)
    test_document = create_test_document(db_session, test_submission.id, test_user.id, DocumentType.MATERIAL_TRANSFER_AGREEMENT, "Test Document", "DRAFT")

    def mock_get_presigned_url(url, expiration_seconds):
        return f"{url}?presigned=true&expiry={expiration_seconds}"

    monkeypatch.setattr(Document, "get_presigned_url", mock_get_presigned_url)
    retrieved_document = document.get_with_presigned_url(test_document.id, db_session)
    assert retrieved_document["id"] == str(test_document.id)
    assert "presigned_url" in retrieved_document
    assert retrieved_document["presigned_url"] == f"{test_document.url}?presigned=true&expiry=3600"

    non_existent_document = document.get_with_presigned_url(uuid4(), db_session)
    assert non_existent_document is None


def test_update_status(db_session, test_user):
    """Test updating a document's status"""
    test_submission = create_test_submission(db_session, test_user.id)
    test_document = create_test_document(db_session, test_submission.id, test_user.id, DocumentType.MATERIAL_TRANSFER_AGREEMENT, "Test Document", "DRAFT")
    updated_document = document.update_status(test_document.id, DOCUMENT_STATUS["PENDING_SIGNATURE"], db_session)
    assert updated_document.status == DOCUMENT_STATUS["PENDING_SIGNATURE"]

    updated_document = document.update_status(test_document.id, DOCUMENT_STATUS["SIGNED"], db_session)
    assert updated_document.status == DOCUMENT_STATUS["SIGNED"]
    assert updated_document.is_signed is True

    invalid_document = document.update_status(test_document.id, "INVALID_STATUS", db_session)
    assert invalid_document is None

    non_existent_document = document.update_status(uuid4(), DOCUMENT_STATUS["SIGNED"], db_session)
    assert non_existent_document is None


def test_record_signature(db_session, test_user):
    """Test recording a signature for a document"""
    test_submission = create_test_submission(db_session, test_user.id)
    test_document = create_test_document(db_session, test_submission.id, test_user.id, DocumentType.MATERIAL_TRANSFER_AGREEMENT, "Test Document", "DRAFT")
    signature_id = "test_signature_id"
    signed_document = document.record_signature(test_document.id, signature_id, db_session)
    assert signed_document.signature_id == signature_id
    assert signed_document.is_signed is True
    assert signed_document.status == "SIGNED"
    assert signed_document.signed_at is not None

    non_existent_document = document.record_signature(uuid4(), signature_id, db_session)
    assert non_existent_document is None


def test_get_by_signature_id(db_session, test_user):
    """Test retrieving a document by signature ID"""
    test_submission = create_test_submission(db_session, test_user.id)
    test_document = create_test_document(db_session, test_submission.id, test_user.id, DocumentType.MATERIAL_TRANSFER_AGREEMENT, "Test Document", "DRAFT")
    signature_id = "test_signature_id"
    document.record_signature(test_document.id, signature_id, db_session)
    retrieved_document = document.get_by_signature_id(signature_id, db_session)
    assert retrieved_document.id == test_document.id
    assert retrieved_document.signature_id == signature_id

    non_existent_document = document.get_by_signature_id("non_existent_id", db_session)
    assert non_existent_document is None


def test_filter_documents(db_session, test_user):
    """Test filtering documents with various criteria"""
    test_submission = create_test_submission(db_session, test_user.id)
    doc1 = create_test_document(db_session, test_submission.id, test_user.id, DocumentType.MATERIAL_TRANSFER_AGREEMENT, "MTA Document", "SIGNED")
    doc2 = create_test_document(db_session, test_submission.id, test_user.id, DocumentType.NON_DISCLOSURE_AGREEMENT, "NDA Document", "DRAFT")
    doc3 = create_test_document(db_session, test_submission.id, test_user.id, DocumentType.EXPERIMENT_SPECIFICATION, "Experiment Spec", "PENDING_SIGNATURE")

    # Test filtering by name_contains
    filters = DocumentFilter(name_contains="MTA")
    filtered_documents = document.filter_documents(filters, db_session)
    assert len(filtered_documents["items"]) == 1
    assert filtered_documents["items"][0].id == doc1.id

    # Test filtering by submission_id
    filters = DocumentFilter(submission_id=test_submission.id)
    filtered_documents = document.filter_documents(filters, db_session)
    assert len(filtered_documents["items"]) == 3

    # Test filtering by document type
    filters = DocumentFilter(type=[DocumentType.NON_DISCLOSURE_AGREEMENT])
    filtered_documents = document.filter_documents(filters, db_session)
    assert len(filtered_documents["items"]) == 1
    assert filtered_documents["items"][0].id == doc2.id

    # Test filtering by status
    filters = DocumentFilter(status=["DRAFT"])
    filtered_documents = document.filter_documents(filters, db_session)
    assert len(filtered_documents["items"]) == 1
    assert filtered_documents["items"][0].id == doc2.id

    # Test filtering by is_signed
    filters = DocumentFilter(is_signed=True)
    filtered_documents = document.filter_documents(filters, db_session)
    assert len(filtered_documents["items"]) == 1
    assert filtered_documents["items"][0].id == doc1.id

    # Test filtering by uploaded_after and uploaded_before
    filters = DocumentFilter(uploaded_after=datetime(2023, 1, 1), uploaded_before=datetime(2024, 1, 1))
    filtered_documents = document.filter_documents(filters, db_session)
    assert len(filtered_documents["items"]) == 3

    # Test pagination with skip and limit
    filters = DocumentFilter()
    filtered_documents = document.filter_documents(filters, db_session, skip=1, limit=1)
    assert len(filtered_documents["items"]) == 1
    assert filtered_documents["total"] == 3


def test_get_required_documents(db_session, test_user):
    """Test retrieving required documents for a submission"""
    test_submission = create_test_submission(db_session, test_user.id)
    create_test_document(db_session, test_submission.id, test_user.id, DocumentType.MATERIAL_TRANSFER_AGREEMENT, "MTA Document", "SIGNED")
    required_documents = document.get_required_documents(test_submission.id, db_session)
    assert len(required_documents) == 3
    assert any(doc["type"] == DocumentType.MATERIAL_TRANSFER_AGREEMENT for doc in required_documents)
    assert any(doc["type"] == DocumentType.NON_DISCLOSURE_AGREEMENT for doc in required_documents)
    assert any(doc["type"] == DocumentType.EXPERIMENT_SPECIFICATION for doc in required_documents)
    assert any(doc["completed"] is True for doc in required_documents if doc["type"] == DocumentType.MATERIAL_TRANSFER_AGREEMENT)
    assert any(doc["completed"] is False for doc in required_documents if doc["type"] != DocumentType.MATERIAL_TRANSFER_AGREEMENT)

    empty_documents = document.get_required_documents(uuid4(), db_session)
    assert len(empty_documents) == 0