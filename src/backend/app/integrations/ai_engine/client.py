"""
AI Engine Client Implementation

This module provides a client for interacting with the external AI prediction engine.
It handles API communication, request/response processing, error handling, and implements
resilience patterns for the AI integration workflow.
"""

import requests
import json
import time
import uuid
from typing import List, Dict, Optional, Any, Union

from pybreaker import CircuitBreaker  # pybreaker ^1.0.0

from ...core.config import settings
from ...core.logging import get_logger
from ...constants.molecule_properties import PREDICTABLE_PROPERTIES

from .exceptions import (
    AIEngineException,
    AIEngineConnectionError,
    AIEngineTimeoutError,
    AIEngineResponseError,
    AIServiceUnavailableError,
    BatchSizeExceededError,
    UnsupportedPropertyError,
    PredictionJobNotFoundError,
    InvalidPredictionParametersError,
)

from .models import (
    PredictionRequest,
    PredictionResponse,
    PredictionJobRequest,
    PredictionJobStatus,
    BatchPredictionRequest,
    BatchPredictionResponse,
    AIModelInfo,
    MAX_BATCH_SIZE,
)

# Set up logger for this module
logger = get_logger(__name__)

# Default configuration values
DEFAULT_TIMEOUT = 30  # seconds
DEFAULT_RETRIES = 3
RETRY_BACKOFF_FACTOR = 0.5
DEFAULT_POLL_INTERVAL = 5  # seconds
DEFAULT_MAX_WAIT_TIME = 300  # seconds (5 minutes)

# Initialize circuit breaker for AI engine requests
ai_engine_circuit_breaker = CircuitBreaker(fail_max=5, reset_timeout=60)


def validate_api_response(response: requests.Response) -> Dict[str, Any]:
    """
    Validates the API response from the AI engine.
    
    Args:
        response: HTTP response from the API
        
    Returns:
        Validated response data as dictionary
        
    Raises:
        AIEngineResponseError: If the response is invalid or contains errors
    """
    if 200 <= response.status_code < 300:
        try:
            data = response.json()
            return data
        except json.JSONDecodeError:
            raise AIEngineResponseError(
                message="Failed to parse API response as JSON",
                response_status=response.status_code,
                response_body={"content": response.text}
            )
    
    # Handle error responses
    error_message = "AI Engine API returned an error"
    error_details = {"status_code": response.status_code}
    
    try:
        error_data = response.json()
        if isinstance(error_data, dict):
            error_message = error_data.get("message", error_message)
            error_details["response_body"] = error_data
    except (json.JSONDecodeError, ValueError):
        error_details["response_body"] = {"content": response.text}
    
    # Map HTTP status codes to appropriate exceptions
    if response.status_code == 404:
        raise PredictionJobNotFoundError(
            message=error_message,
            job_id=error_details.get("job_id"),
            details=error_details
        )
    elif response.status_code == 400:
        raise InvalidPredictionParametersError(
            message=error_message,
            details=error_details
        )
    elif response.status_code == 429:
        raise AIEngineResponseError(
            message="AI Engine rate limit exceeded",
            response_status=response.status_code,
            response_body=error_details.get("response_body")
        )
    elif response.status_code == 503:
        raise AIServiceUnavailableError(
            message="AI Engine service is currently unavailable",
            details=error_details
        )
    else:
        raise AIEngineResponseError(
            message=error_message,
            response_status=response.status_code,
            response_body=error_details.get("response_body")
        )


class AIEngineClient:
    """Client for interacting with the external AI prediction engine."""
    
    def __init__(
        self,
        api_url: Optional[str] = None,
        api_key: Optional[str] = None,
        timeout: int = DEFAULT_TIMEOUT,
        max_retries: int = DEFAULT_RETRIES,
        retry_backoff_factor: float = RETRY_BACKOFF_FACTOR
    ):
        """
        Initialize the AI Engine client with configuration.
        
        Args:
            api_url: Base URL for the AI Engine API (defaults to settings.AI_ENGINE_API_URL)
            api_key: API key for authentication (defaults to settings.AI_ENGINE_API_KEY)
            timeout: Timeout for API requests in seconds
            max_retries: Maximum number of retry attempts for failed requests
            retry_backoff_factor: Backoff factor for retry delays
        """
        self.api_url = api_url or settings.AI_ENGINE_API_URL
        self.api_key = api_key or settings.AI_ENGINE_API_KEY
        self.timeout = timeout
        self.max_retries = max_retries
        self.retry_backoff_factor = retry_backoff_factor
        
        # Initialize session for connection pooling
        self.session = requests.Session()
        self.session.headers.update({
            "Content-Type": "application/json",
            "Accept": "application/json",
            "X-API-Key": self.api_key
        })
        
        logger.info(f"Initialized AI Engine client with API URL: {self.api_url}")
    
    @ai_engine_circuit_breaker
    def predict_properties(self, request: PredictionRequest) -> PredictionResponse:
        """
        Submit a prediction request to the AI engine.
        
        Args:
            request: Prediction request model containing SMILES and properties
            
        Returns:
            Prediction response with job ID and status
            
        Raises:
            UnsupportedPropertyError: If requested properties are not supported
            BatchSizeExceededError: If batch size exceeds maximum limit
            AIEngineConnectionError: If connection to AI Engine fails
            AIEngineTimeoutError: If request times out
            AIEngineResponseError: If AI Engine returns an error response
        """
        # Validate properties against supported properties
        for prop in request.properties:
            if prop not in PREDICTABLE_PROPERTIES:
                raise UnsupportedPropertyError(property_name=prop)
        
        # Check batch size
        if len(request.smiles) > MAX_BATCH_SIZE:
            raise BatchSizeExceededError(
                batch_size=len(request.smiles),
                max_batch_size=MAX_BATCH_SIZE
            )
        
        # Prepare request payload
        payload = request.dict()
        logger.info(f"Submitting prediction request for {len(request.smiles)} molecules "
                    f"and {len(request.properties)} properties")
        
        # Send request to AI Engine API
        response = self._make_request(
            method="POST",
            endpoint="/predictions",
            json_data=payload
        )
        
        # Validate and parse response
        data = validate_api_response(response)
        result = PredictionResponse(**data)
        
        logger.info(f"Successfully submitted prediction request, job ID: {result.job_id}")
        return result
    
    @ai_engine_circuit_breaker
    def get_prediction_status(self, job_id: str) -> PredictionJobStatus:
        """
        Check the status of a prediction job.
        
        Args:
            job_id: ID of the prediction job to check
            
        Returns:
            Current status of the prediction job
            
        Raises:
            PredictionJobNotFoundError: If job ID does not exist
            AIEngineConnectionError: If connection to AI Engine fails
            AIEngineTimeoutError: If request times out
            AIEngineResponseError: If AI Engine returns an error response
        """
        # Validate job ID format
        try:
            uuid.UUID(job_id)
        except ValueError:
            raise InvalidPredictionParametersError(
                message="Invalid job ID format",
                details={"job_id": job_id}
            )
        
        # Send request to AI Engine API
        response = self._make_request(
            method="GET",
            endpoint=f"/predictions/{job_id}/status"
        )
        
        # Validate and parse response
        data = validate_api_response(response)
        result = PredictionJobStatus(**data)
        
        logger.info(f"Job {job_id} status: {result.status}, "
                    f"progress: {result.completed_molecules}/{result.total_molecules}")
        return result
    
    @ai_engine_circuit_breaker
    def get_prediction_results(self, job_id: str) -> PredictionResponse:
        """
        Get the results of a completed prediction job.
        
        Args:
            job_id: ID of the prediction job
            
        Returns:
            Prediction results for the job
            
        Raises:
            PredictionJobNotFoundError: If job ID does not exist
            AIEngineConnectionError: If connection to AI Engine fails
            AIEngineTimeoutError: If request times out
            AIEngineResponseError: If AI Engine returns an error response
        """
        # Validate job ID format
        try:
            uuid.UUID(job_id)
        except ValueError:
            raise InvalidPredictionParametersError(
                message="Invalid job ID format",
                details={"job_id": job_id}
            )
        
        # Send request to AI Engine API
        response = self._make_request(
            method="GET",
            endpoint=f"/predictions/{job_id}/results"
        )
        
        # Validate and parse response
        data = validate_api_response(response)
        result = PredictionResponse(**data)
        
        logger.info(f"Successfully retrieved results for job {job_id}")
        return result
    
    def wait_for_prediction_completion(
        self,
        job_id: str,
        max_wait_time: int = DEFAULT_MAX_WAIT_TIME,
        poll_interval: int = DEFAULT_POLL_INTERVAL
    ) -> PredictionResponse:
        """
        Wait for a prediction job to complete with polling.
        
        Args:
            job_id: ID of the prediction job
            max_wait_time: Maximum time to wait in seconds
            poll_interval: Time between status checks in seconds
            
        Returns:
            Prediction results after job completion
            
        Raises:
            AIEngineTimeoutError: If job does not complete within max_wait_time
            AIEngineException: If job fails or another error occurs
        """
        wait_time = 0
        
        while wait_time < max_wait_time:
            status = self.get_prediction_status(job_id)
            
            if status.status == "completed":
                return self.get_prediction_results(job_id)
            
            if status.status == "failed":
                raise AIEngineException(
                    message=f"Prediction job {job_id} failed",
                    details={"job_id": job_id, "status": status.dict()}
                )
            
            # Job is still processing, wait and check again
            time.sleep(poll_interval)
            wait_time += poll_interval
        
        # If we've reached here, the job hasn't completed within max_wait_time
        raise AIEngineTimeoutError(
            message=f"Prediction job {job_id} did not complete within {max_wait_time} seconds",
            timeout_seconds=max_wait_time,
            details={"job_id": job_id}
        )
    
    @ai_engine_circuit_breaker
    def submit_batch_prediction(self, request: BatchPredictionRequest) -> BatchPredictionResponse:
        """
        Submit a batch prediction request for multiple molecules.
        
        Args:
            request: Batch prediction request with molecule IDs
            
        Returns:
            Batch prediction response with batch ID and status
            
        Raises:
            UnsupportedPropertyError: If requested properties are not supported
            BatchSizeExceededError: If batch size exceeds maximum limit
            AIEngineConnectionError: If connection to AI Engine fails
            AIEngineTimeoutError: If request times out
            AIEngineResponseError: If AI Engine returns an error response
        """
        # Validate properties against supported properties
        for prop in request.properties:
            if prop not in PREDICTABLE_PROPERTIES:
                raise UnsupportedPropertyError(property_name=prop)
        
        # Check batch size
        if len(request.molecule_ids) > MAX_BATCH_SIZE:
            raise BatchSizeExceededError(
                batch_size=len(request.molecule_ids),
                max_batch_size=MAX_BATCH_SIZE
            )
        
        # Prepare request payload
        payload = request.dict()
        logger.info(f"Submitting batch prediction request for {len(request.molecule_ids)} molecules "
                    f"and {len(request.properties)} properties")
        
        # Send request to AI Engine API
        response = self._make_request(
            method="POST",
            endpoint="/predictions/batch",
            json_data=payload
        )
        
        # Validate and parse response
        data = validate_api_response(response)
        result = BatchPredictionResponse(**data)
        
        logger.info(f"Successfully submitted batch prediction request, batch ID: {result.batch_id}")
        return result
    
    @ai_engine_circuit_breaker
    def get_batch_prediction_status(self, batch_id: str) -> BatchPredictionResponse:
        """
        Check the status of a batch prediction job.
        
        Args:
            batch_id: ID of the batch prediction to check
            
        Returns:
            Current status of the batch prediction
            
        Raises:
            PredictionJobNotFoundError: If batch ID does not exist
            AIEngineConnectionError: If connection to AI Engine fails
            AIEngineTimeoutError: If request times out
            AIEngineResponseError: If AI Engine returns an error response
        """
        # Validate batch ID format
        try:
            uuid.UUID(batch_id)
        except ValueError:
            raise InvalidPredictionParametersError(
                message="Invalid batch ID format",
                details={"batch_id": batch_id}
            )
        
        # Send request to AI Engine API
        response = self._make_request(
            method="GET",
            endpoint=f"/predictions/batch/{batch_id}"
        )
        
        # Validate and parse response
        data = validate_api_response(response)
        result = BatchPredictionResponse(**data)
        
        logger.info(f"Batch {batch_id} status: {result.status}")
        return result
    
    @ai_engine_circuit_breaker
    def get_available_models(self) -> List[AIModelInfo]:
        """
        Get information about available AI prediction models.
        
        Returns:
            List of available AI models and their capabilities
            
        Raises:
            AIEngineConnectionError: If connection to AI Engine fails
            AIEngineTimeoutError: If request times out
            AIEngineResponseError: If AI Engine returns an error response
        """
        # Send request to AI Engine API
        response = self._make_request(
            method="GET",
            endpoint="/models"
        )
        
        # Validate and parse response
        data = validate_api_response(response)
        models = [AIModelInfo(**model_data) for model_data in data.get("models", [])]
        
        logger.info(f"Retrieved {len(models)} available AI models")
        return models
    
    @ai_engine_circuit_breaker
    def get_model_info(self, model_name: str, model_version: Optional[str] = None) -> AIModelInfo:
        """
        Get detailed information about a specific AI model.
        
        Args:
            model_name: Name of the AI model
            model_version: Optional version of the AI model
            
        Returns:
            Detailed information about the specified model
            
        Raises:
            AIEngineConnectionError: If connection to AI Engine fails
            AIEngineTimeoutError: If request times out
            AIEngineResponseError: If AI Engine returns an error response
        """
        # Construct endpoint URL
        endpoint = f"/models/{model_name}"
        if model_version:
            endpoint += f"/versions/{model_version}"
        
        # Send request to AI Engine API
        response = self._make_request(
            method="GET",
            endpoint=endpoint
        )
        
        # Validate and parse response
        data = validate_api_response(response)
        model_info = AIModelInfo(**data)
        
        logger.info(f"Retrieved information for model: {model_name}")
        return model_info
    
    def health_check(self) -> bool:
        """
        Check if the AI Engine API is available and responding.
        
        Returns:
            True if API is healthy, False otherwise
        """
        try:
            response = self._make_request(
                method="GET",
                endpoint="/health",
                timeout=5  # Short timeout for health check
            )
            health_status = response.status_code == 200
            
            logger.info(f"AI Engine health check: {'Healthy' if health_status else 'Unhealthy'}")
            return health_status
        except Exception as e:
            logger.warning(f"AI Engine health check failed: {str(e)}")
            return False
    
    def _make_request(
        self,
        method: str,
        endpoint: str,
        json_data: Optional[Dict[str, Any]] = None,
        params: Optional[Dict[str, str]] = None,
        timeout: Optional[int] = None
    ) -> requests.Response:
        """
        Internal method to make HTTP requests with retry logic.
        
        Args:
            method: HTTP method (GET, POST, etc.)
            endpoint: API endpoint path
            json_data: JSON data for request body
            params: Query parameters
            timeout: Request timeout in seconds
            
        Returns:
            HTTP response from the API
            
        Raises:
            AIEngineConnectionError: If connection fails after all retries
            AIEngineTimeoutError: If request times out
            AIEngineException: For other request exceptions
        """
        url = f"{self.api_url.rstrip('/')}/{endpoint.lstrip('/')}"
        timeout = timeout if timeout is not None else self.timeout
        retry_count = 0
        
        while True:
            try:
                response = self.session.request(
                    method=method,
                    url=url,
                    json=json_data,
                    params=params,
                    timeout=timeout
                )
                return response
            
            except requests.exceptions.ConnectionError as e:
                retry_count += 1
                if retry_count > self.max_retries:
                    raise AIEngineConnectionError(
                        message=f"Failed to connect to AI Engine after {self.max_retries} attempts",
                        details={"url": url, "error": str(e)}
                    )
                
                # Exponential backoff
                wait_time = self.retry_backoff_factor * (2 ** (retry_count - 1))
                logger.warning(f"Connection error, retrying in {wait_time:.2f} seconds "
                              f"(attempt {retry_count}/{self.max_retries})")
                time.sleep(wait_time)
            
            except requests.exceptions.Timeout as e:
                raise AIEngineTimeoutError(
                    message="Request to AI Engine timed out",
                    timeout_seconds=timeout,
                    details={"url": url, "error": str(e)}
                )
            
            except Exception as e:
                raise AIEngineException(
                    message=f"Error making request to AI Engine: {str(e)}",
                    details={"url": url, "method": method, "error": str(e)}
                )