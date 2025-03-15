import json
import uuid
from typing import List, Dict

import pytest
from fastapi import status
from fastapi.testclient import TestClient

from ..conftest import client, db_session, pharma_token_headers, cro_token_headers, test_user, test_molecule, test_molecules
from ...app.constants.submission_status import SubmissionStatus, SubmissionAction
from ...app.models.submission import Submission
from ...app.crud.crud_submission import submission


def test_create_submission(
    client: TestClient,
    pharma_token_headers: Dict,
    db_session: db_session,
    test_user: test_user,
    test_molecule: test_molecule,
) -> None:
    """Test creating a new submission"""
    # Create submission data dictionary with name, cro_service_id, and molecule_ids
    submission_data = {
        "name": "Test Submission",
        "cro_service_id": str(uuid.uuid4()),
        "molecule_ids": [str(test_molecule.id)],
    }
    # Send POST request to /api/v1/submissions/ with submission data
    response = client.post("/api/v1/submissions/", headers=pharma_token_headers, json=submission_data)
    # Assert response status code is 201 CREATED
    assert response.status_code == 201
    # Assert response JSON contains expected fields (id, name, status)
    response_json = response.json()
    assert "id" in response_json
    assert "name" in response_json
    assert "status" in response_json
    # Assert status is DRAFT
    assert response_json["status"] == SubmissionStatus.DRAFT.value
    # Assert molecule_ids contains test_molecule.id
    assert str(test_molecule.id) in response_json["molecule_ids"]


def test_get_submission(
    client: TestClient,
    pharma_token_headers: Dict,
    db_session: db_session,
    test_user: test_user,
    test_molecule: test_molecule,
) -> None:
    """Test retrieving a submission by ID"""
    # Create a test submission in the database
    submission_data = {
        "name": "Test Submission",
        "cro_service_id": str(uuid.uuid4()),
        "molecule_ids": [str(test_molecule.id)],
        "created_by": str(test_user.id),
    }
    test_submission = submission.create_submission(submission_data, test_user, db_session)
    # Send GET request to /api/v1/submissions/{submission_id}
    response = client.get(f"/api/v1/submissions/{test_submission.id}", headers=pharma_token_headers)
    # Assert response status code is 200 OK
    assert response.status_code == 200
    # Assert response JSON contains expected fields (id, name, status)
    response_json = response.json()
    assert "id" in response_json
    assert "name" in response_json
    assert "status" in response_json
    # Assert id matches the created submission
    assert response_json["id"] == str(test_submission.id)
    # Assert molecules list contains test_molecule data
    assert str(test_molecule.id) in response_json["molecules"]


def test_update_submission(
    client: TestClient,
    pharma_token_headers: Dict,
    db_session: db_session,
    test_user: test_user,
    test_molecule: test_molecule,
) -> None:
    """Test updating an existing submission"""
    # Create a test submission in the database
    submission_data = {
        "name": "Test Submission",
        "cro_service_id": str(uuid.uuid4()),
        "molecule_ids": [str(test_molecule.id)],
        "created_by": str(test_user.id),
    }
    test_submission = submission.create_submission(submission_data, test_user, db_session)
    # Create update data with new name and description
    update_data = {"name": "Updated Submission", "description": "Updated description"}
    # Send PUT request to /api/v1/submissions/{submission_id} with update data
    response = client.put(
        f"/api/v1/submissions/{test_submission.id}", headers=pharma_token_headers, json=update_data
    )
    # Assert response status code is 200 OK
    assert response.status_code == 200
    # Assert response JSON contains updated name and description
    response_json = response.json()
    assert response_json["name"] == "Updated Submission"
    assert response_json["description"] == "Updated description"
    # Assert other fields remain unchanged
    assert response_json["id"] == str(test_submission.id)


def test_list_submissions(
    client: TestClient, pharma_token_headers: Dict, db_session: db_session, test_user: test_user
) -> None:
    """Test listing submissions with optional filtering"""
    # Create multiple test submissions in the database
    submission_data_1 = {
        "name": "Test Submission 1",
        "cro_service_id": str(uuid.uuid4()),
        "molecule_ids": [],
        "created_by": str(test_user.id),
    }
    submission.create_submission(submission_data_1, test_user, db_session)
    submission_data_2 = {
        "name": "Test Submission 2",
        "cro_service_id": str(uuid.uuid4()),
        "molecule_ids": [],
        "created_by": str(test_user.id),
    }
    submission.create_submission(submission_data_2, test_user, db_session)
    # Send GET request to /api/v1/submissions/
    response = client.get("/api/v1/submissions/", headers=pharma_token_headers)
    # Assert response status code is 200 OK
    assert response.status_code == 200
    # Assert response JSON contains items and pagination metadata
    response_json = response.json()
    assert "items" in response_json
    assert "total" in response_json
    # Assert items count matches expected number of submissions
    assert response_json["total"] == 2
    # Test with filter parameters (status, name_contains)
    response = client.get(
        "/api/v1/submissions/?name_contains=1", headers=pharma_token_headers
    )
    assert response.status_code == 200
    response_json = response.json()
    # Assert filtered results match expected criteria
    assert response_json["total"] == 1


def test_submission_workflow(
    client: TestClient,
    pharma_token_headers: Dict,
    cro_token_headers: Dict,
    db_session: db_session,
    test_user: test_user,
    test_molecules: List[test_molecules],
) -> None:
    """Test the complete submission workflow from creation to completion"""
    # Create a new submission with test molecules
    submission_data = {
        "name": "Workflow Submission",
        "cro_service_id": str(uuid.uuid4()),
        "molecule_ids": [str(molecule.id) for molecule in test_molecules],
        "created_by": str(test_user.id),
    }
    test_submission = submission.create_submission(submission_data, test_user, db_session)
    submission_id = str(test_submission.id)
    # Submit the submission (DRAFT -> SUBMITTED)
    response = client.post(
        f"/api/v1/submissions/{submission_id}/actions",
        headers=pharma_token_headers,
        json={"action": SubmissionStatus.SUBMITTED.value},
    )
    assert response.status_code == 200
    # Assert status changed to SUBMITTED
    assert response.json()["status"] == SubmissionStatus.SUBMITTED.value
    # As CRO user, update status to PENDING_REVIEW
    response = client.post(
        f"/api/v1/submissions/{submission_id}/actions",
        headers=cro_token_headers,
        json={"action": SubmissionStatus.PENDING_REVIEW.value},
    )
    assert response.status_code == 200
    # Provide pricing information (PENDING_REVIEW -> PRICING_PROVIDED)
    response = client.post(
        f"/api/v1/submissions/{submission_id}/actions",
        headers=cro_token_headers,
        json={
            "action": SubmissionStatus.PRICING_PROVIDED.value,
            "data": {"price": 1000, "price_currency": "USD", "estimated_turnaround_days": 14},
        },
    )
    assert response.status_code == 200
    # Assert status changed to PRICING_PROVIDED
    assert response.json()["status"] == SubmissionStatus.PRICING_PROVIDED.value
    # As pharma user, approve pricing (PRICING_PROVIDED -> APPROVED)
    response = client.post(
        f"/api/v1/submissions/{submission_id}/actions",
        headers=pharma_token_headers,
        json={"action": SubmissionStatus.APPROVED.value},
    )
    assert response.status_code == 200
    # Assert status changed to APPROVED
    assert response.json()["status"] == SubmissionStatus.APPROVED.value
    # As CRO user, start experiment (APPROVED -> IN_PROGRESS)
    response = client.post(
        f"/api/v1/submissions/{submission_id}/actions",
        headers=cro_token_headers,
        json={"action": SubmissionStatus.IN_PROGRESS.value},
    )
    assert response.status_code == 200
    # Assert status changed to IN_PROGRESS
    assert response.json()["status"] == SubmissionStatus.IN_PROGRESS.value
    # Upload results (IN_PROGRESS -> RESULTS_UPLOADED)
    response = client.post(
        f"/api/v1/submissions/{submission_id}/actions",
        headers=cro_token_headers,
        json={"action": SubmissionStatus.RESULTS_UPLOADED.value},
    )
    assert response.status_code == 200
    # Assert status changed to RESULTS_UPLOADED
    assert response.json()["status"] == SubmissionStatus.RESULTS_UPLOADED.value
    # As pharma user, review results (RESULTS_UPLOADED -> RESULTS_REVIEWED)
    response = client.post(
        f"/api/v1/submissions/{submission_id}/actions",
        headers=pharma_token_headers,
        json={"action": SubmissionStatus.RESULTS_REVIEWED.value},
    )
    assert response.status_code == 200
    # Complete the submission (RESULTS_REVIEWED -> COMPLETED)
    response = client.post(
        f"/api/v1/submissions/{submission_id}/actions",
        headers=pharma_token_headers,
        json={"action": SubmissionStatus.COMPLETED.value},
    )
    assert response.status_code == 200
    # Assert status changed to COMPLETED
    assert response.json()["status"] == SubmissionStatus.COMPLETED.value
    # Verify submission timeline contains all status changes
    response = client.get(f"/api/v1/submissions/{submission_id}", headers=pharma_token_headers)
    assert response.status_code == 200
    # TODO: Add timeline verification


def test_submission_document_requirements(
    client: TestClient,
    pharma_token_headers: Dict,
    db_session: db_session,
    test_user: test_user,
    test_molecule: test_molecule,
) -> None:
    """Test checking document requirements for a submission"""
    # Create a test submission in the database
    submission_data = {
        "name": "Test Submission",
        "cro_service_id": str(uuid.uuid4()),
        "molecule_ids": [str(test_molecule.id)],
        "created_by": str(test_user.id),
    }
    test_submission = submission.create_submission(submission_data, test_user, db_session)
    # Send GET request to /api/v1/submissions/{submission_id}/documents/check
    response = client.get(
        f"/api/v1/submissions/{test_submission.id}/documents/check", headers=pharma_token_headers
    )
    # Assert response status code is 200 OK
    assert response.status_code == 200
    # Assert response JSON contains required_documents, optional_documents, and existing_documents
    response_json = response.json()
    assert "required_documents" in response_json
    assert "optional_documents" in response_json
    assert "existing_documents" in response_json
    # Assert required_documents list matches expected document types for the CRO service
    # Assert existing_documents is empty for new submission
    assert len(response_json["existing_documents"]) == 0


def test_submission_counts(
    client: TestClient, pharma_token_headers: Dict, db_session: db_session, test_user: test_user
) -> None:
    """Test getting submission counts by status"""
    # Create multiple test submissions with different statuses
    submission_data_1 = {
        "name": "Test Submission 1",
        "cro_service_id": str(uuid.uuid4()),
        "molecule_ids": [],
        "created_by": str(test_user.id),
    }
    submission.create_submission(submission_data_1, test_user, db_session)
    submission_data_2 = {
        "name": "Test Submission 2",
        "cro_service_id": str(uuid.uuid4()),
        "molecule_ids": [],
        "created_by": str(test_user.id),
        "status": SubmissionStatus.SUBMITTED.value,
    }
    submission.create_submission(submission_data_2, test_user, db_session)
    # Send GET request to /api/v1/submissions/counts
    response = client.get("/api/v1/submissions/counts", headers=pharma_token_headers)
    # Assert response status code is 200 OK
    assert response.status_code == 200
    # Assert response JSON is a list of status counts
    response_json = response.json()
    assert isinstance(response_json, list)
    # Assert counts match expected values for each status
    draft_count = next(
        (item["count"] for item in response_json if item["status"] == SubmissionStatus.DRAFT.value), 0
    )
    submitted_count = next(
        (item["count"] for item in response_json if item["status"] == SubmissionStatus.SUBMITTED.value), 0
    )
    assert draft_count == 1
    assert submitted_count == 1


def test_submission_authorization(
    client: TestClient,
    pharma_token_headers: Dict,
    cro_token_headers: Dict,
    db_session: db_session,
    test_user: test_user,
    test_molecule: test_molecule,
) -> None:
    """Test authorization rules for submission endpoints"""
    # Create a test submission as pharma user
    submission_data = {
        "name": "Test Submission",
        "cro_service_id": str(uuid.uuid4()),
        "molecule_ids": [str(test_molecule.id)],
        "created_by": str(test_user.id),
    }
    test_submission = submission.create_submission(submission_data, test_user, db_session)
    # Try to update submission as different pharma user
    different_pharma_headers = {"Authorization": "Bearer different_pharma_token"}
    response = client.put(
        f"/api/v1/submissions/{test_submission.id}", headers=different_pharma_headers, json={"name": "Unauthorized"}
    )
    # Assert response status code is 403 FORBIDDEN
    assert response.status_code == 403
    # Try to set pricing as pharma user
    response = client.post(
        f"/api/v1/submissions/{test_submission.id}/actions",
        headers=pharma_token_headers,
        json={
            "action": SubmissionStatus.PRICING_PROVIDED.value,
            "data": {"price": 1000, "price_currency": "USD", "estimated_turnaround_days": 14},
        },
    )
    # Assert response status code is 403 FORBIDDEN
    assert response.status_code == 403
    # Try to access submission without authentication
    response = client.get(f"/api/v1/submissions/{test_submission.id}")
    # Assert response status code is 401 UNAUTHORIZED
    assert response.status_code == 401


def test_invalid_submission_actions(
    client: TestClient,
    pharma_token_headers: Dict,
    db_session: db_session,
    test_user: test_user,
    test_molecule: test_molecule,
) -> None:
    """Test handling of invalid submission actions"""
    # Create a test submission in the database
    submission_data = {
        "name": "Test Submission",
        "cro_service_id": str(uuid.uuid4()),
        "molecule_ids": [str(test_molecule.id)],
        "created_by": str(test_user.id),
    }
    test_submission = submission.create_submission(submission_data, test_user, db_session)
    submission_id = str(test_submission.id)
    # Try to approve submission in DRAFT status
    response = client.post(
        f"/api/v1/submissions/{submission_id}/actions",
        headers=pharma_token_headers,
        json={"action": SubmissionStatus.APPROVED.value},
    )
    # Assert response status code is 400 BAD REQUEST
    assert response.status_code == 400
    # Try to submit submission without required documents
    response = client.post(
        f"/api/v1/submissions/{submission_id}/actions",
        headers=pharma_token_headers,
        json={"action": SubmissionStatus.SUBMITTED.value},
    )
    # Assert response status code is 400 BAD REQUEST
    assert response.status_code == 400
    # Try to complete submission in DRAFT status
    response = client.post(
        f"/api/v1/submissions/{submission_id}/actions",
        headers=pharma_token_headers,
        json={"action": SubmissionStatus.COMPLETED.value},
    )
    # Assert response status code is 400 BAD REQUEST
    assert response.status_code == 400
    # Try to perform action with invalid action type
    response = client.post(
        f"/api/v1/submissions/{submission_id}/actions",
        headers=pharma_token_headers,
        json={"action": "INVALID_ACTION"},
    )
    # Assert response status code is 422 UNPROCESSABLE ENTITY
    assert response.status_code == 422


class TestSubmissionFixtures:
    """Fixtures for submission tests"""

    @pytest.fixture
    def test_submission(self, db_session: db_session, test_user: test_user, test_molecule: test_molecule):
        """Fixture that creates a test submission"""
        # Create submission data with test user and molecule
        submission_data = {
            "name": "Test Submission",
            "cro_service_id": str(uuid.uuid4()),
            "molecule_ids": [str(test_molecule.id)],
            "created_by": str(test_user.id),
        }
        # Use submission.create_submission to create submission in database
        test_submission = submission.create_submission(submission_data, test_user, db_session)
        # Yield the created submission for test use
        yield test_submission
        # After test completes, optionally clean up the submission

    @pytest.fixture
    def test_submissions_with_status(self, db_session: db_session, test_user: test_user, test_molecule: test_molecule):
        """Fixture that creates multiple test submissions with different statuses"""
        # Create submissions with different statuses (DRAFT, SUBMITTED, etc.)
        submissions = {}
        for status in SubmissionStatus:
            submission_data = {
                "name": f"Test Submission {status.value}",
                "cro_service_id": str(uuid.uuid4()),
                "molecule_ids": [str(test_molecule.id)],
                "created_by": str(test_user.id),
                "status": status.value,
            }
            # For each status, create a submission and update its status
            test_submission = submission.create_submission(submission_data, test_user, db_session)
            submissions[status.value] = test_submission
        # Return dictionary mapping status to submission instance
        yield submissions
        # After test completes, clean up all created submissions