"""
Test module for AI Engine client integration.

This module contains tests for the AIEngineClient class that handles communication
with the external AI prediction service.
"""

import pytest
import json
import uuid
from unittest.mock import patch, MagicMock, Mock

import requests
import pybreaker
from requests.exceptions import ConnectionError, Timeout

from app.integrations.ai_engine.client import AIEngineClient
from app.integrations.ai_engine.models import (
    PredictionRequest,
    PredictionResponse,
    BatchPredictionRequest,
    PredictionJobStatus,
    MAX_BATCH_SIZE
)
from app.integrations.ai_engine.exceptions import (
    AIEngineException,
    AIEngineConnectionError,
    AIEngineTimeoutError,
    AIEngineResponseError,
    BatchSizeExceededError,
    UnsupportedPropertyError
)
from app.constants.molecule_properties import PREDICTABLE_PROPERTIES


class MockResponse:
    """Mock HTTP response for testing API interactions."""
    
    def __init__(self, status_code, json_data):
        """Initialize mock response with status code and data."""
        self.status_code = status_code
        self.json_data = json_data
        self.ok = 200 <= status_code < 300
        self.text = json.dumps(json_data)
    
    def json(self):
        """Mock json method to return the json_data."""
        return self.json_data
    
    def raise_for_status(self):
        """Mock raise_for_status method to raise HTTPError for non-2xx status codes."""
        if not self.ok:
            raise requests.HTTPError(f"HTTP Error: {self.status_code}")


def test_ai_engine_client_init():
    """Tests the initialization of the AIEngineClient with default and custom parameters."""
    # Test with default parameters
    client = AIEngineClient()
    assert client.api_url == "http://ai-engine-api.example.com"  # Default from settings
    assert client.api_key == "test-api-key"  # Default from settings
    assert client.timeout == 30  # Default timeout
    assert client.max_retries == 3  # Default retries
    
    # Test with custom parameters
    custom_client = AIEngineClient(
        api_url="https://custom-api.example.com",
        api_key="custom-key",
        timeout=60,
        max_retries=5,
        retry_backoff_factor=1.0
    )
    assert custom_client.api_url == "https://custom-api.example.com"
    assert custom_client.api_key == "custom-key"
    assert custom_client.timeout == 60
    assert custom_client.max_retries == 5
    assert custom_client.retry_backoff_factor == 1.0
    
    # Verify session headers
    assert custom_client.session.headers["Content-Type"] == "application/json"
    assert custom_client.session.headers["Accept"] == "application/json"
    assert custom_client.session.headers["X-API-Key"] == "custom-key"


@patch('requests.Session.post')
def test_predict_properties_success(mock_post):
    """Tests successful property prediction request and response."""
    # Mock successful response
    mock_response = MockResponse(200, {
        "job_id": "123e4567-e89b-12d3-a456-426614174000",
        "status": "queued",
        "model_name": "molecule_property_predictor",
        "model_version": "v1.0"
    })
    mock_post.return_value = mock_response
    
    # Create client and request
    client = AIEngineClient()
    request = PredictionRequest(
        smiles=["CC(C)CCO", "c1ccccc1"],
        properties=["logp", "solubility"]
    )
    
    # Call method under test
    response = client.predict_properties(request)
    
    # Verify request was made correctly
    mock_post.assert_called_once()
    args, kwargs = mock_post.call_args
    assert kwargs["url"] == "http://ai-engine-api.example.com/predictions"
    assert kwargs["json"] == request.dict()
    
    # Verify response parsing
    assert isinstance(response, PredictionResponse)
    assert response.job_id == "123e4567-e89b-12d3-a456-426614174000"
    assert response.status == "queued"
    assert response.model_name == "molecule_property_predictor"
    assert response.model_version == "v1.0"


def test_predict_properties_invalid_property():
    """Tests error handling when invalid property is requested."""
    client = AIEngineClient()
    
    # Create request with invalid property
    request = PredictionRequest(
        smiles=["CC(C)CCO"],
        properties=["invalid_property"]  # Not in PREDICTABLE_PROPERTIES
    )
    
    # Expect UnsupportedPropertyError
    with pytest.raises(UnsupportedPropertyError) as excinfo:
        client.predict_properties(request)
    
    # Verify error message contains the invalid property name
    assert "invalid_property" in str(excinfo.value)


def test_predict_properties_batch_size_exceeded():
    """Tests error handling when batch size exceeds maximum."""
    client = AIEngineClient()
    
    # Create request with too many SMILES
    smiles_list = ["CC(C)CCO"] * (MAX_BATCH_SIZE + 1)
    request = PredictionRequest(
        smiles=smiles_list,
        properties=["logp"]
    )
    
    # Expect BatchSizeExceededError
    with pytest.raises(BatchSizeExceededError) as excinfo:
        client.predict_properties(request)
    
    # Verify error message contains the batch size and maximum allowed
    assert str(MAX_BATCH_SIZE) in str(excinfo.value)
    assert str(len(smiles_list)) in str(excinfo.value)


@patch('requests.Session.post')
def test_predict_properties_connection_error(mock_post):
    """Tests error handling when connection to AI engine fails."""
    # Mock connection error
    mock_post.side_effect = ConnectionError("Connection failed")
    
    # Create client and request
    client = AIEngineClient()
    request = PredictionRequest(
        smiles=["CC(C)CCO"],
        properties=["logp"]
    )
    
    # Expect AIEngineConnectionError
    with pytest.raises(AIEngineConnectionError) as excinfo:
        client.predict_properties(request)
    
    # Verify retry mechanism is attempted the correct number of times
    assert mock_post.call_count == client.max_retries + 1  # Initial attempt + retries
    assert "failed to connect" in str(excinfo.value).lower()


@patch('requests.Session.post')
def test_predict_properties_timeout_error(mock_post):
    """Tests error handling when request to AI engine times out."""
    # Mock timeout error
    mock_post.side_effect = Timeout("Request timed out")
    
    # Create client and request
    client = AIEngineClient()
    request = PredictionRequest(
        smiles=["CC(C)CCO"],
        properties=["logp"]
    )
    
    # Expect AIEngineTimeoutError
    with pytest.raises(AIEngineTimeoutError) as excinfo:
        client.predict_properties(request)
    
    # Verify error message contains timeout information
    assert "timed out" in str(excinfo.value).lower()
    assert mock_post.call_count == 1  # No retries for timeout


@patch('requests.Session.post')
def test_predict_properties_response_error(mock_post):
    """Tests error handling when AI engine returns error response."""
    # Mock error response
    error_response = MockResponse(400, {
        "message": "Invalid SMILES notation",
        "details": {"invalid_smiles": ["CC(C"]},
        "error_code": "validation_error"
    })
    mock_post.return_value = error_response
    
    # Create client and request
    client = AIEngineClient()
    request = PredictionRequest(
        smiles=["CC(C"],  # Invalid SMILES
        properties=["logp"]
    )
    
    # Expect AIEngineResponseError
    with pytest.raises(AIEngineResponseError) as excinfo:
        client.predict_properties(request)
    
    # Verify error message contains response status code
    assert mock_post.call_count == 1
    assert "400" in str(excinfo.value)
    assert "Invalid SMILES notation" in str(excinfo.value)


@patch('requests.Session.get')
def test_get_prediction_status(mock_get):
    """Tests retrieving prediction job status."""
    # Mock successful response
    mock_response = MockResponse(200, {
        "job_id": "123e4567-e89b-12d3-a456-426614174000",
        "status": "processing",
        "total_molecules": 10,
        "completed_molecules": 5,
        "model_name": "molecule_property_predictor",
        "model_version": "v1.0"
    })
    mock_get.return_value = mock_response
    
    # Create client and call method
    client = AIEngineClient()
    job_id = "123e4567-e89b-12d3-a456-426614174000"
    status = client.get_prediction_status(job_id)
    
    # Verify request was made with correct URL and parameters
    mock_get.assert_called_once()
    args, kwargs = mock_get.call_args
    assert kwargs["url"] == f"http://ai-engine-api.example.com/predictions/{job_id}/status"
    
    # Verify response is parsed correctly into PredictionJobStatus object
    assert isinstance(status, PredictionJobStatus)
    assert status.job_id == job_id
    assert status.status == "processing"
    assert status.total_molecules == 10
    assert status.completed_molecules == 5
    assert status.model_name == "molecule_property_predictor"
    assert status.model_version == "v1.0"


@patch('requests.Session.get')
def test_get_prediction_results(mock_get):
    """Tests retrieving prediction results."""
    # Mock successful response
    mock_response = MockResponse(200, {
        "job_id": "123e4567-e89b-12d3-a456-426614174000",
        "status": "completed",
        "model_name": "molecule_property_predictor",
        "model_version": "v1.0",
        "results": [
            {
                "smiles": "CC(C)CCO",
                "properties": {
                    "logp": {
                        "value": 1.2,
                        "confidence": 0.95,
                        "units": None
                    },
                    "solubility": {
                        "value": 0.85,
                        "confidence": 0.87,
                        "units": "mg/mL"
                    }
                }
            },
            {
                "smiles": "c1ccccc1",
                "properties": {
                    "logp": {
                        "value": 2.1,
                        "confidence": 0.98,
                        "units": None
                    },
                    "solubility": {
                        "value": 0.32,
                        "confidence": 0.75,
                        "units": "mg/mL"
                    }
                }
            }
        ]
    })
    mock_get.return_value = mock_response
    
    # Create client and call method
    client = AIEngineClient()
    job_id = "123e4567-e89b-12d3-a456-426614174000"
    results = client.get_prediction_results(job_id)
    
    # Verify request was made with correct URL and parameters
    mock_get.assert_called_once()
    args, kwargs = mock_get.call_args
    assert kwargs["url"] == f"http://ai-engine-api.example.com/predictions/{job_id}/results"
    
    # Verify response is parsed correctly into PredictionResponse object
    assert isinstance(results, PredictionResponse)
    assert results.job_id == job_id
    assert results.status == "completed"
    assert len(results.results) == 2
    
    # Verify results contain expected molecule predictions and properties
    assert results.results[0].smiles == "CC(C)CCO"
    assert results.results[0].properties["logp"]["value"] == 1.2
    assert results.results[0].properties["logp"]["confidence"] == 0.95
    
    assert results.results[1].smiles == "c1ccccc1"
    assert results.results[1].properties["solubility"]["value"] == 0.32
    assert results.results[1].properties["solubility"]["confidence"] == 0.75
    assert results.results[1].properties["solubility"]["units"] == "mg/mL"


@patch('app.integrations.ai_engine.client.AIEngineClient.get_prediction_status')
@patch('app.integrations.ai_engine.client.AIEngineClient.get_prediction_results')
def test_wait_for_prediction_completion_success(mock_get_results, mock_get_status):
    """Tests waiting for prediction job to complete successfully."""
    # Mock get_prediction_status to return 'completed' status after a few calls
    job_id = "123e4567-e89b-12d3-a456-426614174000"
    
    # Create a sequence of statuses, transitioning from processing to completed
    processing_status = PredictionJobStatus(
        job_id=job_id,
        status="processing",
        total_molecules=10,
        completed_molecules=5
    )
    
    completed_status = PredictionJobStatus(
        job_id=job_id,
        status="completed",
        total_molecules=10,
        completed_molecules=10
    )
    
    # First return processing status, then completed
    mock_get_status.side_effect = [processing_status, processing_status, completed_status]
    
    # Mock results response
    mock_results = PredictionResponse(
        job_id=job_id,
        status="completed",
        model_name="molecule_property_predictor",
        model_version="v1.0",
        results=[
            {
                "smiles": "CC(C)CCO",
                "properties": {
                    "logp": {
                        "value": 1.2,
                        "confidence": 0.95
                    }
                }
            }
        ]
    )
    mock_get_results.return_value = mock_results
    
    # Create client and call method
    client = AIEngineClient()
    results = client.wait_for_prediction_completion(
        job_id=job_id,
        max_wait_time=30,
        poll_interval=1  # Use short interval for testing
    )
    
    # Verify get_prediction_status is called multiple times until completion
    assert mock_get_status.call_count == 3
    
    # Verify get_prediction_results is called once after completion
    mock_get_results.assert_called_once_with(job_id)
    
    # Verify returned results match expected prediction results
    assert results == mock_results


@patch('app.integrations.ai_engine.client.AIEngineClient.get_prediction_status')
def test_wait_for_prediction_completion_failure(mock_get_status):
    """Tests waiting for prediction job that fails."""
    # Mock get_prediction_status to return 'failed' status after a few calls
    job_id = "123e4567-e89b-12d3-a456-426614174000"
    
    # Create a sequence of statuses, transitioning from processing to failed
    processing_status = PredictionJobStatus(
        job_id=job_id,
        status="processing",
        total_molecules=10,
        completed_molecules=5
    )
    
    failed_status = PredictionJobStatus(
        job_id=job_id,
        status="failed",
        total_molecules=10,
        completed_molecules=7
    )
    
    # First return processing status, then failed
    mock_get_status.side_effect = [processing_status, failed_status]
    
    # Create client and call method
    client = AIEngineClient()
    
    # Expect AIEngineException when job fails
    with pytest.raises(AIEngineException) as excinfo:
        client.wait_for_prediction_completion(
            job_id=job_id,
            max_wait_time=30,
            poll_interval=1  # Use short interval for testing
        )
    
    # Verify error message contains failure reason from status response
    assert "failed" in str(excinfo.value)
    assert job_id in str(excinfo.value)


@patch('app.integrations.ai_engine.client.AIEngineClient.get_prediction_status')
@patch('time.sleep')
def test_wait_for_prediction_completion_timeout(mock_sleep, mock_get_status):
    """Tests timeout while waiting for prediction job."""
    # Mock get_prediction_status to always return 'processing' status
    job_id = "123e4567-e89b-12d3-a456-426614174000"
    
    processing_status = PredictionJobStatus(
        job_id=job_id,
        status="processing",
        total_molecules=10,
        completed_molecules=5
    )
    
    # Always return processing to trigger timeout
    mock_get_status.return_value = processing_status
    
    # Create client and call method
    client = AIEngineClient()
    
    # Expect AIEngineTimeoutError when max wait time is exceeded
    with pytest.raises(AIEngineTimeoutError) as excinfo:
        client.wait_for_prediction_completion(
            job_id=job_id,
            max_wait_time=5,  # Short timeout for testing
            poll_interval=1
        )
    
    # Verify error message contains job_id and max wait time
    assert "did not complete" in str(excinfo.value)
    assert job_id in str(excinfo.value)
    assert "5 seconds" in str(excinfo.value)


@patch('requests.Session.post')
def test_submit_batch_prediction(mock_post):
    """Tests submitting batch prediction request."""
    # Mock successful response
    mock_response = MockResponse(200, {
        "batch_id": "123e4567-e89b-12d3-a456-426614174000",
        "status": "queued",
        "job_id": "987e6543-e21b-12d3-a456-426614174000",
        "model_name": "molecule_property_predictor",
        "model_version": "v1.0"
    })
    mock_post.return_value = mock_response
    
    # Create client and request
    client = AIEngineClient()
    molecule_ids = [uuid.uuid4() for _ in range(5)]
    request = BatchPredictionRequest(
        molecule_ids=molecule_ids,
        properties=["logp", "solubility"]
    )
    
    # Call method under test
    response = client.submit_batch_prediction(request)
    
    # Verify request was made with correct URL and payload
    mock_post.assert_called_once()
    args, kwargs = mock_post.call_args
    assert kwargs["url"] == "http://ai-engine-api.example.com/predictions/batch"
    assert kwargs["json"] == request.dict()
    
    # Verify response is parsed correctly into BatchPredictionResponse object
    assert response.batch_id == "123e4567-e89b-12d3-a456-426614174000"
    assert response.status == "queued"
    assert response.job_id == "987e6543-e21b-12d3-a456-426614174000"
    assert response.model_name == "molecule_property_predictor"
    assert response.model_version == "v1.0"


@patch('requests.Session.get')
def test_get_batch_prediction_status(mock_get):
    """Tests retrieving batch prediction status."""
    # Mock successful response with batch status
    batch_id = "123e4567-e89b-12d3-a456-426614174000"
    mock_response = MockResponse(200, {
        "batch_id": batch_id,
        "status": "processing",
        "job_id": "987e6543-e21b-12d3-a456-426614174000",
        "model_name": "molecule_property_predictor",
        "model_version": "v1.0",
        "metadata": {
            "progress": "50%",
            "estimated_completion": "2023-09-20T15:30:00Z"
        }
    })
    mock_get.return_value = mock_response
    
    # Create client and call method
    client = AIEngineClient()
    status = client.get_batch_prediction_status(batch_id)
    
    # Verify request was made with correct URL and parameters
    mock_get.assert_called_once()
    args, kwargs = mock_get.call_args
    assert kwargs["url"] == f"http://ai-engine-api.example.com/predictions/batch/{batch_id}"
    
    # Verify response is parsed correctly into BatchPredictionResponse object
    assert status.batch_id == batch_id
    assert status.status == "processing"
    assert status.job_id == "987e6543-e21b-12d3-a456-426614174000"
    assert status.model_name == "molecule_property_predictor"
    assert status.model_version == "v1.0"
    assert status.metadata["progress"] == "50%"


@patch('requests.Session.get')
def test_get_available_models(mock_get):
    """Tests retrieving available AI models."""
    # Mock successful response with available models
    mock_response = MockResponse(200, {
        "models": [
            {
                "name": "molecule_property_predictor",
                "version": "v1.0",
                "supported_properties": ["logp", "solubility", "permeability"],
                "description": "General purpose property prediction model"
            },
            {
                "name": "adme_predictor",
                "version": "v2.1",
                "supported_properties": ["clearance", "half_life", "bioavailability"],
                "description": "Specialized model for ADME predictions"
            }
        ]
    })
    mock_get.return_value = mock_response
    
    # Create client and call method
    client = AIEngineClient()
    models = client.get_available_models()
    
    # Verify request was made with correct URL
    mock_get.assert_called_once()
    args, kwargs = mock_get.call_args
    assert kwargs["url"] == "http://ai-engine-api.example.com/models"
    
    # Verify response is parsed correctly into list of AIModelInfo objects
    assert len(models) == 2
    assert models[0].name == "molecule_property_predictor"
    assert models[0].version == "v1.0"
    assert "logp" in models[0].supported_properties
    assert models[1].name == "adme_predictor"
    assert models[1].version == "v2.1"
    assert "clearance" in models[1].supported_properties


@patch('requests.Session.get')
def test_get_model_info(mock_get):
    """Tests retrieving specific model information."""
    # Mock successful response with model details
    model_name = "molecule_property_predictor"
    model_version = "v1.0"
    mock_response = MockResponse(200, {
        "name": model_name,
        "version": model_version,
        "supported_properties": ["logp", "solubility", "permeability"],
        "description": "General purpose property prediction model",
        "metadata": {
            "accuracy": "0.92",
            "training_date": "2023-05-15",
            "architecture": "Graph Neural Network"
        }
    })
    mock_get.return_value = mock_response
    
    # Create client and call method
    client = AIEngineClient()
    model_info = client.get_model_info(model_name, model_version)
    
    # Verify request was made with correct URL including model name and version
    mock_get.assert_called_once()
    args, kwargs = mock_get.call_args
    assert kwargs["url"] == f"http://ai-engine-api.example.com/models/{model_name}/versions/{model_version}"
    
    # Verify response is parsed correctly into AIModelInfo object
    assert model_info.name == model_name
    assert model_info.version == model_version
    assert len(model_info.supported_properties) == 3
    assert "permeability" in model_info.supported_properties
    assert model_info.description == "General purpose property prediction model"
    assert model_info.metadata["accuracy"] == "0.92"


@patch('requests.Session.get')
def test_health_check_success(mock_get):
    """Tests successful health check of AI engine."""
    # Mock successful response with 200 status code
    mock_response = MockResponse(200, {"status": "healthy"})
    mock_get.return_value = mock_response
    
    # Create client and call method
    client = AIEngineClient()
    health_status = client.health_check()
    
    # Verify request was made with correct URL
    mock_get.assert_called_once()
    args, kwargs = mock_get.call_args
    assert kwargs["url"] == "http://ai-engine-api.example.com/health"
    
    # Verify health_check returns True
    assert health_status is True


@patch('requests.Session.get')
def test_health_check_failure(mock_get):
    """Tests failed health check of AI engine."""
    # Mock failed response with non-200 status code
    mock_response = MockResponse(503, {"status": "unhealthy", "message": "Database connection issue"})
    mock_get.return_value = mock_response
    
    # Create client and call method
    client = AIEngineClient()
    health_status = client.health_check()
    
    # Verify request was made with correct URL
    mock_get.assert_called_once()
    args, kwargs = mock_get.call_args
    assert kwargs["url"] == "http://ai-engine-api.example.com/health"
    
    # Verify health_check returns False
    assert health_status is False


@patch('requests.Session.get')
def test_health_check_exception(mock_get):
    """Tests health check when exception occurs."""
    # Mock requests.get to raise an exception
    mock_get.side_effect = ConnectionError("Connection failed")
    
    # Create client and call method
    client = AIEngineClient()
    health_status = client.health_check()
    
    # Verify health_check catches exception and returns False
    assert health_status is False


@patch('requests.Session.post')
@patch('pybreaker.CircuitBreaker.call')
def test_circuit_breaker_functionality(mock_circuit_breaker, mock_post):
    """Tests circuit breaker pattern implementation."""
    # Mock circuit breaker to track calls and failures
    client = AIEngineClient()
    request = PredictionRequest(
        smiles=["CC(C)CCO"],
        properties=["logp"]
    )
    
    # Mock circuit breaker to pass-through but track calls
    def side_effect(func, *args, **kwargs):
        return func(*args, **kwargs)
    
    mock_circuit_breaker.side_effect = side_effect
    
    # First, simulate successful request
    mock_post.return_value = MockResponse(200, {
        "job_id": "123e4567-e89b-12d3-a456-426614174000",
        "status": "queued"
    })
    
    response = client.predict_properties(request)
    assert response.job_id == "123e4567-e89b-12d3-a456-426614174000"
    
    # Now simulate failures to trigger circuit breaker
    mock_post.side_effect = ConnectionError("Connection failed")
    
    # After enough failures, circuit breaker should open
    mock_circuit_breaker.side_effect = pybreaker.CircuitBreakerError("Circuit breaker open")
    
    # Expect circuit breaker prevents further API calls when open
    with pytest.raises(pybreaker.CircuitBreakerError) as excinfo:
        client.predict_properties(request)
    
    assert "Circuit breaker open" in str(excinfo.value)