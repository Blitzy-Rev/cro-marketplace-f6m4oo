# src/backend/tests/crud/test_crud_submission.py
import pytest
from uuid import uuid4
from datetime import datetime
import random

from ..conftest import db_session, test_user, test_molecule, test_molecules
from ...app.crud.crud_submission import submission
from ...app.crud.crud_cro_service import cro_service
from ...app.crud.crud_document import document
from ...app.schemas.submission import SubmissionCreate, SubmissionUpdate, SubmissionFilter, SubmissionAction, SubmissionPricingUpdate
from ...app.constants.submission_status import SubmissionStatus, SubmissionAction as SubmissionActionEnum
from ...app.models.cro_service import ServiceType
from ...app.constants.document_types import DocumentType

@pytest.fixture
def create_test_cro_service(db_session):
    """Creates a test CRO service for submission testing"""
    cro_service_data = {
        "name": f"Test CRO Service {uuid4()}",
        "description": "Test CRO service description",
        "provider": "Test CRO Provider",
        "service_type": ServiceType.BINDING_ASSAY,
        "base_price": random.uniform(100, 1000),
        "price_currency": "USD",
        "typical_turnaround_days": random.randint(7, 30),
        "active": True
    }
    created_cro_service = cro_service.create(cro_service_data, db=db_session)
    return created_cro_service

@pytest.fixture
def create_test_submission(db_session, test_user, create_test_cro_service):
    """Creates a test submission for testing CRUD operations"""
    submission_data = {
        "name": "Test Submission",
        "cro_service_id": create_test_cro_service.id,
        "created_by": test_user.id,
        "description": "Test submission description"
    }
    created_submission = submission.create_submission(submission_data, test_user, db=db_session)
    return created_submission

@pytest.fixture
def create_test_submission_with_molecules(db_session, test_user, create_test_cro_service, test_molecules):
    """Creates a test submission with molecules for testing"""
    submission_data = {
        "name": "Test Submission with Molecules",
        "cro_service_id": create_test_cro_service.id,
        "created_by": test_user.id,
        "description": "Test submission with molecules description",
        "molecule_ids": [molecule.id for molecule in test_molecules]
    }
    created_submission = submission.create_submission(submission_data, test_user, db=db_session)
    return created_submission

@pytest.fixture
def create_test_documents(db_session, create_test_submission):
    """Creates test documents for a submission"""
    document_data = [
        {
            "name": "Test Material Transfer Agreement",
            "type": DocumentType.MATERIAL_TRANSFER_AGREEMENT,
            "submission_id": create_test_submission.id,
            "uploaded_by": create_test_submission.created_by,
            "url": "http://example.com/mta.pdf",
            "status": "UPLOADED",
            "is_signed": True
        },
        {
            "name": "Test Non-Disclosure Agreement",
            "type": DocumentType.NON_DISCLOSURE_AGREEMENT,
            "submission_id": create_test_submission.id,
            "uploaded_by": create_test_submission.created_by,
            "url": "http://example.com/nda.pdf",
            "status": "UPLOADED",
            "is_signed": True
        },
        {
            "name": "Test Experiment Specification",
            "type": DocumentType.EXPERIMENT_SPECIFICATION,
            "submission_id": create_test_submission.id,
            "uploaded_by": create_test_submission.created_by,
            "url": "http://example.com/spec.pdf",
            "status": "UPLOADED",
            "is_signed": True
        }
    ]
    created_documents = []
    for data in document_data:
        created_document = document.create(data, db=db_session)
        created_documents.append(created_document)
    return created_documents

def test_create_submission(db_session, test_user, create_test_cro_service):
    """Tests creating a new submission"""
    submission_data = {
        "name": "Test Submission",
        "cro_service_id": create_test_cro_service.id,
        "created_by": test_user.id,
        "description": "Test submission description"
    }
    created_submission = submission.create_submission(submission_data, test_user, db=db_session)
    assert created_submission.name == "Test Submission"
    assert created_submission.cro_service_id == create_test_cro_service.id
    assert created_submission.created_by == test_user.id
    assert created_submission.description == "Test submission description"
    assert created_submission.status == SubmissionStatus.DRAFT.value

def test_get_submission(db_session, create_test_submission):
    """Tests retrieving a submission by ID"""
    retrieved_submission = submission.get_with_relationships(create_test_submission.id, db=db_session)
    assert retrieved_submission.id == create_test_submission.id

def test_get_submission_with_relationships(db_session, create_test_submission_with_molecules, create_test_documents):
    """Tests retrieving a submission with its relationships"""
    retrieved_submission = submission.get_with_relationships(create_test_submission_with_molecules.id, db=db_session)
    assert retrieved_submission.id == create_test_submission_with_molecules.id
    assert len(retrieved_submission.molecules) > 0
    assert len(retrieved_submission.documents) > 0
    assert retrieved_submission.cro_service is not None

def test_update_submission(db_session, create_test_submission):
    """Tests updating a submission"""
    update_data = {
        "name": "Updated Submission Name",
        "description": "Updated submission description"
    }
    updated_submission = submission.update_submission(create_test_submission, update_data, db=db_session)
    assert updated_submission.name == "Updated Submission Name"
    assert updated_submission.description == "Updated submission description"

def test_get_by_creator(db_session, test_user, create_test_submission):
    """Tests retrieving submissions by creator"""
    retrieved_submissions = submission.get_by_creator(test_user.id, db=db_session)
    assert len(retrieved_submissions["items"]) > 0
    assert retrieved_submissions["total"] > 0
    assert create_test_submission in retrieved_submissions["items"]

def test_get_by_status(db_session, create_test_submission):
    """Tests retrieving submissions by status"""
    retrieved_submissions = submission.get_by_status([SubmissionStatus.DRAFT.value], db=db_session)
    assert len(retrieved_submissions["items"]) > 0
    assert retrieved_submissions["total"] > 0
    assert create_test_submission in retrieved_submissions["items"]

def test_get_active_submissions(db_session, create_test_submission):
    """Tests retrieving active submissions"""
    retrieved_submissions = submission.get_active_submissions(db=db_session)
    assert len(retrieved_submissions["items"]) > 0
    assert retrieved_submissions["total"] > 0
    assert create_test_submission in retrieved_submissions["items"]

def test_get_by_molecule(db_session, test_molecule, create_test_submission_with_molecules):
    """Tests retrieving submissions by molecule"""
    retrieved_submissions = submission.get_by_molecule(test_molecule.id, db=db_session)
    assert len(retrieved_submissions["items"]) > 0
    assert retrieved_submissions["total"] > 0
    assert create_test_submission_with_molecules in retrieved_submissions["items"]

def test_get_by_cro_service(db_session, create_test_cro_service, create_test_submission):
    """Tests retrieving submissions by CRO service"""
    retrieved_submissions = submission.get_by_cro_service(create_test_cro_service.id, db=db_session)
    assert len(retrieved_submissions["items"]) > 0
    assert retrieved_submissions["total"] > 0
    assert create_test_submission in retrieved_submissions["items"]

def test_filter_submissions(db_session, test_user, create_test_submission):
    """Tests filtering submissions with multiple criteria"""
    filter_params = SubmissionFilter(created_by=test_user.id, name_contains="Test")
    filtered_submissions = submission.filter_submissions(filter_params, db=db_session)
    assert len(filtered_submissions["items"]) > 0
    assert filtered_submissions["total"] > 0
    assert create_test_submission in filtered_submissions["items"]

def test_update_status(db_session, create_test_submission):
    """Tests updating a submission status"""
    updated_submission = submission.update_status(create_test_submission.id, SubmissionStatus.SUBMITTED.value, db=db_session)
    assert updated_submission.status == SubmissionStatus.SUBMITTED.value
    assert updated_submission.submitted_at is not None

def test_add_molecule(db_session, create_test_submission, test_molecule):
    """Tests adding a molecule to a submission"""
    success = submission.add_molecule(create_test_submission.id, test_molecule.id, db=db_session)
    assert success is True
    retrieved_submission = submission.get_with_relationships(create_test_submission.id, db=db_session)
    assert test_molecule in retrieved_submission.molecules

def test_remove_molecule(db_session, create_test_submission_with_molecules, test_molecules):
    """Tests removing a molecule from a submission"""
    molecule_to_remove = test_molecules[0]
    success = submission.remove_molecule(create_test_submission_with_molecules.id, molecule_to_remove.id, db=db_session)
    assert success is True
    retrieved_submission = submission.get_with_relationships(create_test_submission_with_molecules.id, db=db_session)
    assert molecule_to_remove not in retrieved_submission.molecules

def test_set_pricing(db_session, create_test_submission):
    """Tests setting pricing for a submission"""
    pricing_data = {
        "price": 1500.00,
        "price_currency": "USD",
        "estimated_turnaround_days": 14
    }
    submission.update_status(create_test_submission.id, SubmissionStatus.PENDING_REVIEW.value, db=db_session)
    updated_submission = submission.set_pricing(create_test_submission.id, pricing_data, db=db_session)
    assert updated_submission.price == 1500.00
    assert updated_submission.price_currency == "USD"
    assert updated_submission.estimated_turnaround_days == 14
    assert updated_submission.status == SubmissionStatus.PRICING_PROVIDED.value

def test_set_specifications(db_session, create_test_submission):
    """Tests setting specifications for a submission"""
    specifications = {"assay_type": "Binding Assay", "target": "Target Protein"}
    updated_submission = submission.set_specifications(create_test_submission.id, specifications, db=db_session)
    assert updated_submission.specifications == specifications

def test_submit_submission(db_session, create_test_submission_with_molecules, create_test_documents):
    """Tests submitting a submission to a CRO"""
    updated_submission = submission.submit_submission(create_test_submission_with_molecules.id, db=db_session)
    assert updated_submission.status == SubmissionStatus.SUBMITTED.value
    assert updated_submission.submitted_at is not None

def test_approve_submission(db_session, create_test_submission_with_molecules, create_test_documents):
    """Tests approving a submission with pricing"""
    submission_id = create_test_submission_with_molecules.id
    submission.update_status(submission_id, SubmissionStatus.PENDING_REVIEW.value, db=db_session)
    pricing_data = SubmissionPricingUpdate(price=1500.00, price_currency="USD", estimated_turnaround_days=14)
    submission.set_pricing(submission_id, pricing_data, db=db_session)
    updated_submission = submission.approve_submission(submission_id, db=db_session)
    assert updated_submission.status == SubmissionStatus.APPROVED.value
    assert updated_submission.approved_at is not None

def test_cancel_submission(db_session, create_test_submission):
    """Tests cancelling a submission"""
    updated_submission = submission.cancel_submission(create_test_submission.id, db=db_session)
    assert updated_submission.status == SubmissionStatus.CANCELLED.value

def test_complete_submission(db_session, create_test_submission_with_molecules, create_test_documents):
    """Tests completing a submission"""
    submission_id = create_test_submission_with_molecules.id
    submission.update_status(submission_id, SubmissionStatus.RESULTS_REVIEWED.value, db=db_session)
    updated_submission = submission.complete_submission(submission_id, db=db_session)
    assert updated_submission.status == SubmissionStatus.COMPLETED.value
    assert updated_submission.completed_at is not None

def test_process_submission_action(db_session, create_test_submission_with_molecules, create_test_documents):
    """Tests processing different submission actions"""
    action_data = SubmissionAction(action=SubmissionStatus.SUBMITTED.value)
    updated_submission = submission.process_submission_action(create_test_submission_with_molecules.id, action_data, db=db_session)
    assert updated_submission.status == SubmissionStatus.SUBMITTED.value

def test_get_submission_counts_by_status(db_session, test_user, create_test_submission):
    """Tests getting submission counts grouped by status"""
    status_counts = submission.get_submission_counts_by_status(db=db_session)
    assert any(count.status == SubmissionStatus.DRAFT.value and count.count > 0 for count in status_counts)

def test_check_required_documents(db_session, create_test_submission, create_test_documents):
    """Tests checking required documents for a submission"""
    document_requirements = submission.check_required_documents(create_test_submission.id, db=db_session)
    assert len(document_requirements.required_documents) > 0
    assert len(document_requirements.existing_documents) > 0
    for doc in document_requirements.required_documents:
        assert doc["completed"] is True

def test_submission_workflow(db_session, test_user, create_test_cro_service, test_molecules):
    """Tests the complete submission workflow from creation to completion"""
    # 1. Create a new submission
    submission_data = {
        "name": "Test Submission Workflow",
        "cro_service_id": create_test_cro_service.id,
        "created_by": test_user.id,
        "description": "Test submission workflow description"
    }
    created_submission = submission.create_submission(submission_data, test_user, db=db_session)
    assert created_submission.status == SubmissionStatus.DRAFT.value

    # 2. Add molecules to the submission
    for molecule in test_molecules:
        success = submission.add_molecule(created_submission.id, molecule.id, db=db_session)
        assert success is True
    retrieved_submission = submission.get_with_relationships(created_submission.id, db=db_session)
    assert len(retrieved_submission.molecules) == len(test_molecules)

    # 3. Create required documents
    document_data = [
        {
            "name": "Test Material Transfer Agreement",
            "type": DocumentType.MATERIAL_TRANSFER_AGREEMENT,
            "submission_id": created_submission.id,
            "uploaded_by": created_submission.created_by,
            "url": "http://example.com/mta.pdf",
            "status": "UPLOADED",
            "is_signed": True
        },
        {
            "name": "Test Non-Disclosure Agreement",
            "type": DocumentType.NON_DISCLOSURE_AGREEMENT,
            "submission_id": created_submission.id,
            "uploaded_by": created_submission.created_by,
            "url": "http://example.com/nda.pdf",
            "status": "UPLOADED",
            "is_signed": True
        },
        {
            "name": "Test Experiment Specification",
            "type": DocumentType.EXPERIMENT_SPECIFICATION,
            "submission_id": created_submission.id,
            "uploaded_by": created_submission.created_by,
            "url": "http://example.com/spec.pdf",
            "status": "UPLOADED",
            "is_signed": True
        }
    ]
    for data in document_data:
        document.create(data, db=db_session)

    # 4. Submit the submission
    updated_submission = submission.submit_submission(created_submission.id, db=db_session)
    assert updated_submission.status == SubmissionStatus.SUBMITTED.value
    assert updated_submission.submitted_at is not None

    # 5. Provide pricing for the submission
    pricing_data = SubmissionPricingUpdate(price=1500.00, price_currency="USD", estimated_turnaround_days=14)
    submission.update_status(created_submission.id, SubmissionStatus.PENDING_REVIEW.value, db=db_session)
    updated_submission = submission.set_pricing(created_submission.id, pricing_data, db=db_session)
    assert updated_submission.status == SubmissionStatus.PRICING_PROVIDED.value
    assert updated_submission.price == 1500.00
    assert updated_submission.price_currency == "USD"
    assert updated_submission.estimated_turnaround_days == 14

    # 6. Approve the submission
    updated_submission = submission.approve_submission(created_submission.id, db=db_session)
    assert updated_submission.status == SubmissionStatus.APPROVED.value
    assert updated_submission.approved_at is not None

    # 7. Update status to IN_PROGRESS
    action_data = SubmissionAction(action=SubmissionStatus.IN_PROGRESS.value)
    updated_submission = submission.process_submission_action(created_submission.id, action_data, db=db_session)
    assert updated_submission.status == SubmissionStatus.IN_PROGRESS.value

    # 8. Update status to RESULTS_UPLOADED
    action_data = SubmissionAction(action=SubmissionStatus.RESULTS_UPLOADED.value)
    updated_submission = submission.process_submission_action(created_submission.id, action_data, db=db_session)
    assert updated_submission.status == SubmissionStatus.RESULTS_UPLOADED.value

    # 9. Update status to RESULTS_REVIEWED
    action_data = SubmissionAction(action=SubmissionStatus.RESULTS_REVIEWED.value)
    updated_submission = submission.process_submission_action(created_submission.id, action_data, db=db_session)
    assert updated_submission.status == SubmissionStatus.RESULTS_REVIEWED.value

    # 10. Complete the submission
    updated_submission = submission.complete_submission(created_submission.id, db=db_session)
    assert updated_submission.status == SubmissionStatus.COMPLETED.value
    assert updated_submission.completed_at is not None