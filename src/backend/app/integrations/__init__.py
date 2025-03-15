"""
Main initialization module for the integrations package that exports all necessary components from AI Engine, DocuSign, and AWS integrations.
This module serves as a centralized entry point for all external service integrations used by the Molecular Data Management and CRO Integration Platform.
"""

__version__ = "0.1.0"

# AI Engine Integration
from .ai_engine import (
    AIEngineClient,
    AIEngineException,
    PredictionRequest,
    PredictionResponse,
    BatchPredictionRequest,
    BatchPredictionResponse,
)

# DocuSign Integration
from .docusign import (
    DocuSignClient,
    DocuSignException,
    EnvelopeCreate,
    Envelope,
    WebhookEvent,
)

# AWS Integration
from .aws import (
    S3Client,
    SQSClient,
    SQSProducer,
    SQSConsumer,
    upload_file,
    download_file,
    generate_presigned_url,
)

__all__ = [
    "AIEngineClient",
    "AIEngineException",
    "PredictionRequest",
    "PredictionResponse",
    "BatchPredictionRequest",
    "BatchPredictionResponse",
    "DocuSignClient",
    "DocuSignException",
    "EnvelopeCreate",
    "Envelope",
    "WebhookEvent",
    "S3Client",
    "SQSClient",
    "SQSProducer",
    "SQSConsumer",
    "upload_file",
    "download_file",
    "generate_presigned_url",
]