"""
DocuSign Integration Module

This module provides integration with DocuSign e-signature service for secure document exchange,
e-signature workflows, and webhook event handling in compliance with 21 CFR Part 11 requirements.

The integration addresses the following key requirements:

1. Secure Document Exchange (F-403):
   - System for securely exchanging legal and compliance documents with CROs
   - E-signature integration for legally binding agreements
   - Secure document transfer with encryption and access controls

2. Document Management Integration:
   - Integration with DocuSign API for e-signatures and document workflow
   - Template management for standardized documents
   - Real-time status tracking and notifications

3. 21 CFR Part 11 Compliance:
   - Digital signatures compliant with FDA 21 CFR Part 11 regulations
   - Complete audit trails for all document activities
   - Secure authentication and non-repudiation features
"""

__version__ = "0.1.0"

# Import client
from .client import DocuSignClient

# Import models
from .models import (
    DocuSignConfig,
    Recipient,
    DocumentInfo,
    EnvelopeCreate,
    Envelope,
    EnvelopeStatusUpdate,
    WebhookEvent,
    SigningUrl,
    TemplateInfo,
    ENVELOPE_STATUS,
    RECIPIENT_TYPES,
    RECIPIENT_STATUS,
)

# Import exceptions
from .exceptions import (
    DocuSignException,
    DocuSignConnectionError,
    DocuSignTimeoutError,
    DocuSignResponseError,
    EnvelopeCreationError,
    DocumentUploadError,
    DocumentDownloadError,
    AuthenticationError,
    WebhookError,
    TemplateError,
    RecipientError,
)