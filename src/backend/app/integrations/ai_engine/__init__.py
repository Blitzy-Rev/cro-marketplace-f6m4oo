"""
AI Engine Integration Package

This module provides a clean interface for interacting with the external AI prediction engine.
It handles property prediction requests, both synchronous and asynchronous, and implements
resilience patterns like circuit breakers to prevent cascading failures.

The package includes:
- AIEngineClient: Main client for interacting with the AI prediction engine
- Exception classes: Structured error handling for different failure scenarios
- Data models: Pydantic models for request/response validation
- Utility functions: Helpers for common tasks

This integration addresses the requirements for AI Property Prediction (F-301),
asynchronous processing, and fault tolerance through circuit breaker patterns.
"""

# Import client
from .client import AIEngineClient, validate_api_response

# Import exceptions
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

# Import models
from .models import (
    PredictionRequest,
    PredictionResponse,
    PredictionJobStatus,
    BatchPredictionRequest,
    BatchPredictionResponse,
    MoleculePrediction,
    PropertyPrediction,
    AIModelInfo,
    MAX_BATCH_SIZE,
    DEFAULT_MODEL_NAME,
    DEFAULT_MODEL_VERSION,
)

# Define __all__ to explicitly specify what's exported
__all__ = [
    "AIEngineClient",
    "AIEngineException",
    "AIEngineConnectionError",
    "AIEngineTimeoutError",
    "AIEngineResponseError",
    "AIServiceUnavailableError",
    "BatchSizeExceededError",
    "UnsupportedPropertyError",
    "PredictionJobNotFoundError",
    "InvalidPredictionParametersError",
    "PredictionRequest",
    "PredictionResponse",
    "PredictionJobStatus",
    "BatchPredictionRequest",
    "BatchPredictionResponse",
    "MoleculePrediction",
    "PropertyPrediction",
    "AIModelInfo",
    "MAX_BATCH_SIZE",
    "DEFAULT_MODEL_NAME",
    "DEFAULT_MODEL_VERSION",
    "validate_api_response",
]