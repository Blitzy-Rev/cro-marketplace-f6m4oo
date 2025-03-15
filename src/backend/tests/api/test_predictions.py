import pytest
from unittest import mock
import json
import uuid
from datetime import datetime

from ..conftest import client, db_session, pharma_token_headers, test_molecule, test_molecules
from ...app.services.prediction_service import prediction_service, AIEngineClient
from ...app.integrations.ai_engine.exceptions import AIEngineException, AIServiceUnavailableError
from ...app.core.exceptions import PredictionException
from ...app.schemas.prediction import PredictionBatchCreate, PredictionFilter
from ...app.models.prediction import PredictionStatus, PREDICTABLE_PROPERTIES


@pytest.mark.parametrize('wait_for_results', [True, False])
def test_predict_molecule_properties(client, pharma_token_headers, test_molecule, mocker, wait_for_results):
    """Test successful prediction request for a single molecule"""
    # Mock prediction_service.predict_properties_for_molecule to return test prediction data
    mocker.patch('src.backend.app.services.prediction_service.PredictionService.predict_properties', return_value={
        "job_id": "test_job_id",
        "status": "completed",
        "results": [{"smiles": test_molecule.smiles, "properties": {"logP": {"value": 2.5, "confidence": 0.9}}}]
    })

    # Set up mock response with job_id and status for async case
    if wait_for_results == False:
        mock_response = {"job_id": "test_job_id", "status": "queued"}
    # Set up mock response with prediction results for sync case
    else:
        mock_response = {"job_id": "test_job_id", "status": "completed", "results": [{"smiles": test_molecule.smiles, "properties": {"logP": {"value": 2.5, "confidence": 0.9}}}]}

    # Make POST request to /api/v1/predictions/molecules/{molecule_id}/predict
    response = client.post(f"/api/v1/predictions/molecules/{test_molecule.id}/predict?wait_for_results={wait_for_results}", headers=pharma_token_headers)

    # Assert response status code is 202 (Accepted)
    assert response.status_code == status.HTTP_202_ACCEPTED

    # Assert response contains expected data (job_id or results)
    assert response.json() == mock_response

    # Verify prediction_service was called with correct parameters
    # prediction_service.predict_properties_for_molecule.assert_called_once_with(molecule_id=test_molecule.id, properties=None, wait_for_results=wait_for_results)


def test_predict_molecule_properties_service_unavailable(client, pharma_token_headers, test_molecule, mocker):
    """Test prediction request when AI service is unavailable"""
    # Mock prediction_service.predict_properties_for_molecule to raise AIServiceUnavailableError
    mocker.patch('src.backend.app.services.prediction_service.PredictionService.predict_properties', side_effect=AIServiceUnavailableError)

    # Make POST request to /api/v1/predictions/molecules/{molecule_id}/predict
    response = client.post(f"/api/v1/predictions/molecules/{test_molecule.id}/predict", headers=pharma_token_headers)

    # Assert response status code is 503 (Service Unavailable)
    assert response.status_code == status.HTTP_503_SERVICE_UNAVAILABLE

    # Assert response contains error message about service unavailability
    assert response.json() == {"detail": "AI Engine service is currently unavailable", "error_code": "ai_service_unavailable", "status_code": 503}


def test_predict_molecule_properties_prediction_error(client, pharma_token_headers, test_molecule, mocker):
    """Test prediction request with prediction-specific error"""
    # Mock prediction_service.predict_properties_for_molecule to raise PredictionException
    mocker.patch('src.backend.app.services.prediction_service.PredictionService.predict_properties', side_effect=PredictionException("Invalid SMILES"))

    # Make POST request to /api/v1/predictions/molecules/{molecule_id}/predict
    response = client.post(f"/api/v1/predictions/molecules/{test_molecule.id}/predict", headers=pharma_token_headers)

    # Assert response status code is 400 (Bad Request)
    assert response.status_code == status.HTTP_400_BAD_REQUEST

    # Assert response contains specific error message from exception
    assert response.json() == {"detail": "Invalid SMILES", "error_code": "prediction_error", "status_code": 400}


def test_predict_molecule_properties_ai_engine_error(client, pharma_token_headers, test_molecule, mocker):
    """Test prediction request with AI engine error"""
    # Mock prediction_service.predict_properties_for_molecule to raise AIEngineException
    mocker.patch('src.backend.app.services.prediction_service.PredictionService.predict_properties', side_effect=AIEngineException("AI Engine internal error"))

    # Make POST request to /api/v1/predictions/molecules/{molecule_id}/predict
    response = client.post(f"/api/v1/predictions/molecules/{test_molecule.id}/predict", headers=pharma_token_headers)

    # Assert response status code is 500 (Internal Server Error)
    assert response.status_code == status.HTTP_500_INTERNAL_SERVER_ERROR

    # Assert response contains error message about AI engine error
    assert response.json() == {"detail": "AI Engine internal error", "error_code": "ai_engine_error", "status_code": 500}


def test_predict_molecules_batch(client, pharma_token_headers, test_molecules, mocker):
    """Test successful batch prediction request for multiple molecules"""
    # Mock prediction_service.predict_properties_for_molecules to return test batch data
    mocker.patch('src.backend.app.services.prediction_service.PredictionService.predict_properties_for_molecules', return_value={
        "batch_id": "test_batch_id",
        "job_id": "test_job_id"
    })

    # Create batch request payload with molecule_ids and properties
    molecule_ids = [str(molecule.id) for molecule in test_molecules]
    properties = ["logP", "solubility"]
    payload = {"molecule_ids": molecule_ids, "properties": properties}

    # Make POST request to /api/v1/predictions/molecules/predict/batch
    response = client.post("/api/v1/predictions/molecules/predict/batch", headers=pharma_token_headers, json=payload)

    # Assert response status code is 202 (Accepted)
    assert response.status_code == status.HTTP_202_ACCEPTED

    # Assert response contains batch_id and job_id
    assert response.json() == {"batch_id": "test_batch_id", "job_id": "test_job_id"}

    # Verify prediction_service was called with correct parameters
    # prediction_service.predict_properties_for_molecules.assert_called_once_with(molecule_ids=molecule_ids, properties=properties, created_by=ANY)


def test_predict_molecules_batch_service_unavailable(client, pharma_token_headers, test_molecules, mocker):
    """Test batch prediction request when AI service is unavailable"""
    # Mock prediction_service.predict_properties_for_molecules to raise AIServiceUnavailableError
    mocker.patch('src.backend.app.services.prediction_service.PredictionService.predict_properties_for_molecules', side_effect=AIServiceUnavailableError)

    # Create batch request payload with molecule_ids and properties
    molecule_ids = [str(molecule.id) for molecule in test_molecules]
    properties = ["logP", "solubility"]
    payload = {"molecule_ids": molecule_ids, "properties": properties}

    # Make POST request to /api/v1/predictions/molecules/predict/batch
    response = client.post("/api/v1/predictions/molecules/predict/batch", headers=pharma_token_headers, json=payload)

    # Assert response status code is 503 (Service Unavailable)
    assert response.status_code == status.HTTP_503_SERVICE_UNAVAILABLE

    # Assert response contains error message about service unavailability
    assert response.json() == {"detail": "AI Engine service is currently unavailable", "error_code": "ai_service_unavailable", "status_code": 503}


def test_get_prediction_job_status(client, pharma_token_headers, mocker):
    """Test retrieving prediction job status"""
    # Create test batch_id
    batch_id = uuid.uuid4()

    # Mock prediction_service.get_prediction_job_status to return test status data
    mocker.patch('src.backend.app.services.prediction_service.PredictionService.get_prediction_job_status', return_value={
        "batch_id": str(batch_id),
        "status": "completed",
        "total_molecules": 100,
        "completed_molecules": 100
    })

    # Make GET request to /api/v1/predictions/{batch_id}/status
    response = client.get(f"/api/v1/predictions/{batch_id}/status", headers=pharma_token_headers)

    # Assert response status code is 200 (OK)
    assert response.status_code == status.HTTP_200_OK

    # Assert response contains expected status information
    assert response.json() == {"batch_id": str(batch_id), "status": "completed", "total_molecules": 100, "completed_molecules": 100}

    # Verify prediction_service was called with correct batch_id
    # prediction_service.get_prediction_job_status.assert_called_once_with(batch_id=batch_id)


def test_get_prediction_job_status_not_found(client, pharma_token_headers, mocker):
    """Test retrieving status for non-existent prediction job"""
    # Create test batch_id
    batch_id = uuid.uuid4()

    # Mock prediction_service.get_prediction_job_status to raise PredictionException
    mocker.patch('src.backend.app.services.prediction_service.PredictionService.get_prediction_job_status', side_effect=PredictionException("Job not found"))

    # Make GET request to /api/v1/predictions/{batch_id}/status
    response = client.get(f"/api/v1/predictions/{batch_id}/status", headers=pharma_token_headers)

    # Assert response status code is 404 (Not Found)
    assert response.status_code == status.HTTP_404_NOT_FOUND

    # Assert response contains error message about job not found
    assert response.json() == {"detail": "Job not found", "error_code": "prediction_error", "status_code": 404}


def test_get_molecule_predictions(client, pharma_token_headers, test_molecule, mocker):
    """Test retrieving all predictions for a molecule"""
    # Mock prediction_service.get_molecule_predictions to return test prediction data
    mocker.patch('src.backend.app.services.prediction_service.PredictionService.get_molecule_predictions', return_value=[
        {"property_name": "logP", "value": 2.5, "confidence": 0.9},
        {"property_name": "solubility", "value": -3.2, "confidence": 0.8}
    ])

    # Make GET request to /api/v1/molecules/{molecule_id}/predictions
    response = client.get(f"/api/v1/molecules/{test_molecule.id}/predictions", headers=pharma_token_headers)

    # Assert response status code is 200 (OK)
    assert response.status_code == status.HTTP_200_OK

    # Assert response contains list of predictions
    assert response.json() == [{"property_name": "logP", "value": 2.5, "confidence": 0.9}, {"property_name": "solubility", "value": -3.2, "confidence": 0.8}]

    # Verify prediction_service was called with correct molecule_id
    # prediction_service.get_molecule_predictions.assert_called_once_with(molecule_id=test_molecule.id, confidence_threshold=None)


def test_get_molecule_predictions_with_confidence(client, pharma_token_headers, test_molecule, mocker):
    """Test retrieving predictions with confidence threshold"""
    # Mock prediction_service.get_molecule_predictions to return filtered predictions
    mocker.patch('src.backend.app.services.prediction_service.PredictionService.get_molecule_predictions', return_value=[
        {"property_name": "logP", "value": 2.5, "confidence": 0.95}
    ])

    # Make GET request to /api/v1/molecules/{molecule_id}/predictions?min_confidence=0.8
    response = client.get(f"/api/v1/molecules/{test_molecule.id}/predictions?min_confidence=0.8", headers=pharma_token_headers)

    # Assert response status code is 200 (OK)
    assert response.status_code == status.HTTP_200_OK

    # Assert response contains only predictions with confidence >= 0.8
    assert response.json() == [{"property_name": "logP", "value": 2.5, "confidence": 0.95}]

    # Verify prediction_service was called with correct confidence threshold
    # prediction_service.get_molecule_predictions.assert_called_once_with(molecule_id=test_molecule.id, confidence_threshold=0.8)


def test_get_molecule_predictions_not_found(client, pharma_token_headers, mocker):
    """Test retrieving predictions for non-existent molecule"""
    # Create test molecule_id
    molecule_id = uuid.uuid4()

    # Mock prediction_service.get_molecule_predictions to raise PredictionException
    mocker.patch('src.backend.app.services.prediction_service.PredictionService.get_molecule_predictions', side_effect=PredictionException("Molecule not found"))

    # Make GET request to /api/v1/molecules/{molecule_id}/predictions
    response = client.get(f"/api/v1/molecules/{molecule_id}/predictions", headers=pharma_token_headers)

    # Assert response status code is 404 (Not Found)
    assert response.status_code == status.HTTP_404_NOT_FOUND

    # Assert response contains error message about molecule not found
    assert response.json() == {"detail": "Molecule not found", "error_code": "prediction_error", "status_code": 404}


def test_get_latest_molecule_predictions(client, pharma_token_headers, test_molecule, mocker):
    """Test retrieving latest predictions for each property of a molecule"""
    # Mock prediction_service.get_latest_predictions to return test prediction data
    mocker.patch('src.backend.app.services.prediction_service.PredictionService.get_latest_predictions', return_value={
        "logP": {"property_name": "logP", "value": 2.5, "confidence": 0.9},
        "solubility": {"property_name": "solubility", "value": -3.2, "confidence": 0.8}
    })

    # Make GET request to /api/v1/molecules/{molecule_id}/predictions/latest
    response = client.get(f"/api/v1/molecules/{test_molecule.id}/predictions/latest", headers=pharma_token_headers)

    # Assert response status code is 200 (OK)
    assert response.status_code == status.HTTP_200_OK

    # Assert response contains dictionary of latest predictions by property
    assert response.json() == {"logP": {"property_name": "logP", "value": 2.5, "confidence": 0.9}, "solubility": {"property_name": "solubility", "value": -3.2, "confidence": 0.8}}

    # Verify prediction_service was called with correct molecule_id
    # prediction_service.get_latest_predictions.assert_called_once_with(molecule_id=test_molecule.id, properties=None)


def test_get_latest_molecule_predictions_with_properties(client, pharma_token_headers, test_molecule, mocker):
    """Test retrieving latest predictions for specific properties"""
    # Mock prediction_service.get_latest_predictions to return filtered predictions
    mocker.patch('src.backend.app.services.prediction_service.PredictionService.get_latest_predictions', return_value={
        "logP": {"property_name": "logP", "value": 2.5, "confidence": 0.9}
    })

    # Make GET request to /api/v1/molecules/{molecule_id}/predictions/latest?properties=logP,solubility
    response = client.get(f"/api/v1/molecules/{test_molecule.id}/predictions/latest?properties=logP,solubility", headers=pharma_token_headers)

    # Assert response status code is 200 (OK)
    assert response.status_code == status.HTTP_200_OK

    # Assert response contains only predictions for specified properties
    assert response.json() == {"logP": {"property_name": "logP", "value": 2.5, "confidence": 0.9}}

    # Verify prediction_service was called with correct properties list
    # prediction_service.get_latest_predictions.assert_called_once_with(molecule_id=test_molecule.id, properties=["logP", "solubility"])


def test_filter_predictions(client, pharma_token_headers, test_molecule, mocker):
    """Test filtering predictions based on various criteria"""
    # Mock prediction_service.filter_predictions to return filtered predictions
    mocker.patch('src.backend.app.services.prediction_service.PredictionService.filter_predictions', return_value={
        "items": [{"property_name": "logP", "value": 2.5, "confidence": 0.9}],
        "total": 1,
        "page": 1,
        "size": 100,
        "pages": 1
    })

    # Create filter request with molecule_id, property_names, and min_confidence
    payload = {"molecule_id": str(test_molecule.id), "property_names": ["logP"], "min_confidence": 0.8}

    # Make POST request to /api/v1/predictions/filter
    response = client.post("/api/v1/predictions/filter", headers=pharma_token_headers, json=payload)

    # Assert response status code is 200 (OK)
    assert response.status_code == status.HTTP_200_OK

    # Assert response contains filtered predictions and pagination info
    assert response.json() == {"items": [{"property_name": "logP", "value": 2.5, "confidence": 0.9}], "total": 1, "page": 1, "size": 100, "pages": 1}

    # Verify prediction_service was called with correct filter parameters
    # prediction_service.filter_predictions.assert_called_once_with(filter_params=ANY, skip=0, limit=100)


def test_cancel_prediction_job(client, pharma_token_headers, mocker):
    """Test cancelling an ongoing prediction job"""
    # Create test batch_id
    batch_id = uuid.uuid4()

    # Mock prediction_service.cancel_prediction_job to return cancellation result
    mocker.patch('src.backend.app.services.prediction_service.PredictionService.cancel_prediction_job', return_value={
        "batch_id": str(batch_id),
        "status": "cancelled"
    })

    # Make DELETE request to /api/v1/predictions/{batch_id}
    response = client.delete(f"/api/v1/predictions/{batch_id}", headers=pharma_token_headers)

    # Assert response status code is 200 (OK)
    assert response.status_code == status.HTTP_200_OK

    # Assert response contains cancellation confirmation
    assert response.json() == {"batch_id": str(batch_id), "status": "cancelled"}

    # Verify prediction_service was called with correct batch_id
    # prediction_service.cancel_prediction_job.assert_called_once_with(batch_id=batch_id)


def test_cancel_prediction_job_not_found(client, pharma_token_headers, mocker):
    """Test cancelling a non-existent prediction job"""
    # Create test batch_id
    batch_id = uuid.uuid4()

    # Mock prediction_service.cancel_prediction_job to raise PredictionException
    mocker.patch('src.backend.app.services.prediction_service.PredictionService.cancel_prediction_job', side_effect=PredictionException("Job not found"))

    # Make DELETE request to /api/v1/predictions/{batch_id}
    response = client.delete(f"/api/v1/predictions/{batch_id}", headers=pharma_token_headers)

    # Assert response status code is 404 (Not Found)
    assert response.status_code == status.HTTP_404_NOT_FOUND

    # Assert response contains error message about job not found
    assert response.json() == {"detail": "Job not found", "error_code": "prediction_error", "status_code": 404}


def test_retry_failed_prediction(client, pharma_token_headers, mocker):
    """Test retrying a failed prediction job"""
    # Create test batch_id
    batch_id = uuid.uuid4()

    # Mock prediction_service.retry_failed_prediction to return retry result
    mocker.patch('src.backend.app.services.prediction_service.PredictionService.retry_failed_prediction', return_value={
        "batch_id": str(batch_id),
        "status": "retrying"
    })

    # Make POST request to /api/v1/predictions/{batch_id}/retry
    response = client.post(f"/api/v1/predictions/{batch_id}/retry", headers=pharma_token_headers)

    # Assert response status code is 200 (OK)
    assert response.status_code == status.HTTP_200_OK

    # Assert response contains retry confirmation
    assert response.json() == {"batch_id": str(batch_id), "status": "retrying"}

    # Verify prediction_service was called with correct batch_id
    # prediction_service.retry_failed_prediction.assert_called_once_with(batch_id=batch_id)


def test_retry_failed_prediction_not_failed(client, pharma_token_headers, mocker):
    """Test retrying a prediction job that is not in failed state"""
    # Create test batch_id
    batch_id = uuid.uuid4()

    # Mock prediction_service.retry_failed_prediction to raise PredictionException with message about job not being in failed state
    mocker.patch('src.backend.app.services.prediction_service.PredictionService.retry_failed_prediction', side_effect=PredictionException("Job is not in failed state"))

    # Make POST request to /api/v1/predictions/{batch_id}/retry
    response = client.post(f"/api/v1/predictions/{batch_id}/retry", headers=pharma_token_headers)

    # Assert response status code is 400 (Bad Request)
    assert response.status_code == status.HTTP_400_BAD_REQUEST

    # Assert response contains error message about job not being in failed state
    assert response.json() == {"detail": "Job is not in failed state", "error_code": "prediction_error", "status_code": 400}


def test_get_available_properties(client, pharma_token_headers):
    """Test retrieving available predictable properties"""
    # Make GET request to /api/v1/predictions/properties
    response = client.get("/api/v1/predictions/properties", headers=pharma_token_headers)

    # Assert response status code is 200 (OK)
    assert response.status_code == status.HTTP_200_OK

    # Assert response contains dictionary with PREDICTABLE_PROPERTIES list
    assert response.json() == {"properties": PREDICTABLE_PROPERTIES}