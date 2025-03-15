"""
Constants Module

This module serves as the central access point for all application constants.
It imports and re-exports constants from specialized submodules to provide
a unified and organized way to access constants throughout the application.
"""

# Import all constants from specialized modules
from .molecule_properties import *
from .error_messages import *
from .submission_status import *
from .document_types import *
from .user_roles import *

# Define __all__ to explicitly specify what is exported
__all__ = [
    # Molecule Property Constants
    "PropertyType", "PropertySource", "PropertyCategory",
    "PROPERTY_UNITS", "PROPERTY_RANGES", "REQUIRED_PROPERTIES",
    "STANDARD_PROPERTIES", "PREDICTABLE_PROPERTIES", "FILTERABLE_PROPERTIES",
    
    # Error Message Constants
    "AUTH_ERRORS", "VALIDATION_ERRORS", "MOLECULE_ERRORS", "CSV_ERRORS",
    "LIBRARY_ERRORS", "SUBMISSION_ERRORS", "DOCUMENT_ERRORS", "RESULT_ERRORS",
    "PREDICTION_ERRORS", "INTEGRATION_ERRORS", "SYSTEM_ERRORS",
    
    # Submission Status Constants
    "SubmissionStatus", "SubmissionAction", "ACTIVE_STATUSES",
    "TERMINAL_STATUSES", "EDITABLE_STATUSES", "STATUS_TRANSITIONS",
    "PHARMA_EDITABLE_STATUSES", "CRO_EDITABLE_STATUSES", "STATUS_DESCRIPTIONS",
    
    # Document Type Constants
    "DocumentType", "DOCUMENT_STATUS", "SIGNATURE_REQUIRED_TYPES",
    "DOCUMENT_TYPE_DESCRIPTIONS", "REQUIRED_DOCUMENT_TYPES",
    
    # User Role Constants
    "SYSTEM_ADMIN", "PHARMA_ADMIN", "PHARMA_SCIENTIST", "CRO_ADMIN",
    "CRO_TECHNICIAN", "AUDITOR", "DEFAULT_ROLE", "ALL_ROLES",
    "ROLE_HIERARCHY", "PHARMA_ROLES", "CRO_ROLES", "ADMIN_ROLES"
]