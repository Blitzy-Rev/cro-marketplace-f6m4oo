"""
Error Messages Module

This module defines standardized error messages used throughout the application for
consistent error handling and user feedback. These messages are organized by domain
and error type to ensure clear communication of issues to users and developers.

The error messages support:
- API responses with structured error formats
- Validation feedback for data inputs
- Consistent wording across application components
- Clear guidance for corrective actions
"""

# Authentication and authorization error messages
AUTH_ERRORS = {
    "INVALID_CREDENTIALS": "Invalid username or password",
    "EXPIRED_TOKEN": "Authentication token has expired",
    "INVALID_TOKEN": "Invalid authentication token",
    "MISSING_TOKEN": "Authentication token is required",
    "INSUFFICIENT_PERMISSIONS": "You do not have permission to perform this action",
    "ACCOUNT_LOCKED": "Your account has been locked due to multiple failed login attempts",
    "ACCOUNT_DISABLED": "Your account has been disabled",
    "EMAIL_ALREADY_EXISTS": "A user with this email already exists",
    "PASSWORD_RESET_EXPIRED": "Password reset link has expired",
    "PASSWORD_RESET_INVALID": "Invalid password reset token",
    "PASSWORD_TOO_WEAK": "Password does not meet security requirements",
    "MFA_REQUIRED": "Multi-factor authentication is required"
}

# General data validation error messages
VALIDATION_ERRORS = {
    "REQUIRED_FIELD": "This field is required",
    "INVALID_FORMAT": "Invalid format",
    "VALUE_TOO_LONG": "Value exceeds maximum length",
    "VALUE_TOO_SHORT": "Value is shorter than minimum length",
    "VALUE_OUT_OF_RANGE": "Value is outside the allowed range",
    "INVALID_CHOICE": "Invalid choice, must be one of the allowed values",
    "INVALID_EMAIL": "Invalid email address format",
    "INVALID_UUID": "Invalid UUID format",
    "INVALID_DATE": "Invalid date format",
    "FUTURE_DATE_REQUIRED": "Date must be in the future",
    "PAST_DATE_REQUIRED": "Date must be in the past"
}

# Molecule-specific error messages
MOLECULE_ERRORS = {
    "INVALID_SMILES": "Invalid SMILES string",
    "MOLECULE_NOT_FOUND": "Molecule not found",
    "DUPLICATE_MOLECULE": "Molecule already exists",
    "INVALID_INCHI_KEY": "Invalid InChI key",
    "PROPERTY_NOT_FOUND": "Molecular property not found",
    "INVALID_PROPERTY_VALUE": "Invalid property value",
    "INVALID_PROPERTY_TYPE": "Invalid property type",
    "STRUCTURE_GENERATION_FAILED": "Failed to generate molecular structure",
    "DESCRIPTOR_CALCULATION_FAILED": "Failed to calculate molecular descriptors",
    "FINGERPRINT_GENERATION_FAILED": "Failed to generate molecular fingerprint",
    "SIMILARITY_SEARCH_FAILED": "Failed to perform similarity search",
    "SUBSTRUCTURE_SEARCH_FAILED": "Failed to perform substructure search"
}

# CSV processing error messages
CSV_ERRORS = {
    "FILE_TOO_LARGE": "CSV file exceeds maximum size limit of 100MB",
    "INVALID_CSV_FORMAT": "Invalid CSV format",
    "EMPTY_FILE": "CSV file is empty",
    "TOO_MANY_ROWS": "CSV file contains too many rows (maximum 500,000)",
    "MISSING_REQUIRED_COLUMN": "Required column is missing",
    "INVALID_COLUMN_MAPPING": "Invalid column mapping",
    "MISSING_SMILES_COLUMN": "SMILES column is required",
    "DUPLICATE_COLUMN_NAMES": "Duplicate column names detected",
    "PARSING_ERROR": "Error parsing CSV file",
    "INVALID_ROW_DATA": "Invalid data in row",
    "IMPORT_FAILED": "Failed to import molecules from CSV",
    "COLUMN_MAPPING_REQUIRED": "Column mapping is required"
}

# Library management error messages
LIBRARY_ERRORS = {
    "LIBRARY_NOT_FOUND": "Library not found",
    "DUPLICATE_LIBRARY_NAME": "Library with this name already exists",
    "MOLECULE_ALREADY_IN_LIBRARY": "Molecule is already in this library",
    "MOLECULE_NOT_IN_LIBRARY": "Molecule is not in this library",
    "LIBRARY_LIMIT_EXCEEDED": "Maximum number of libraries exceeded",
    "LIBRARY_SIZE_LIMIT_EXCEEDED": "Maximum library size exceeded",
    "INVALID_LIBRARY_OPERATION": "Invalid operation for this library",
    "INSUFFICIENT_LIBRARY_PERMISSIONS": "Insufficient permissions for this library"
}

# CRO submission error messages
SUBMISSION_ERRORS = {
    "SUBMISSION_NOT_FOUND": "Submission not found",
    "INVALID_SUBMISSION_STATUS": "Invalid submission status",
    "INVALID_STATUS_TRANSITION": "Invalid status transition",
    "NO_MOLECULES_SELECTED": "No molecules selected for submission",
    "MISSING_REQUIRED_DOCUMENT": "Required document is missing",
    "INVALID_CRO_SERVICE": "Invalid CRO service",
    "PRICING_REQUIRED": "Pricing information is required",
    "SUBMISSION_ALREADY_PROCESSED": "Submission has already been processed",
    "SUBMISSION_CANCELLED": "Submission has been cancelled",
    "INSUFFICIENT_SUBMISSION_PERMISSIONS": "Insufficient permissions for this submission",
    "INVALID_SUBMISSION_ACTION": "Invalid action for this submission"
}

# Document management error messages
DOCUMENT_ERRORS = {
    "DOCUMENT_NOT_FOUND": "Document not found",
    "INVALID_DOCUMENT_TYPE": "Invalid document type",
    "DOCUMENT_UPLOAD_FAILED": "Failed to upload document",
    "DOCUMENT_DOWNLOAD_FAILED": "Failed to download document",
    "DOCUMENT_TOO_LARGE": "Document exceeds maximum size limit",
    "UNSUPPORTED_FILE_FORMAT": "Unsupported file format",
    "DOCUMENT_PROCESSING_FAILED": "Failed to process document",
    "SIGNATURE_REQUIRED": "Document signature is required",
    "SIGNATURE_FAILED": "Document signature process failed",
    "INSUFFICIENT_DOCUMENT_PERMISSIONS": "Insufficient permissions for this document"
}

# Experimental results error messages
RESULT_ERRORS = {
    "RESULT_NOT_FOUND": "Result not found",
    "INVALID_RESULT_FORMAT": "Invalid result format",
    "RESULT_UPLOAD_FAILED": "Failed to upload results",
    "RESULT_PROCESSING_FAILED": "Failed to process results",
    "MISSING_RESULT_DATA": "Missing required result data",
    "INVALID_RESULT_VALUE": "Invalid result value",
    "RESULTS_ALREADY_UPLOADED": "Results have already been uploaded",
    "INSUFFICIENT_RESULT_PERMISSIONS": "Insufficient permissions for these results"
}

# AI prediction error messages
PREDICTION_ERRORS = {
    "PREDICTION_FAILED": "Property prediction failed",
    "INVALID_PREDICTION_REQUEST": "Invalid prediction request",
    "UNSUPPORTED_PROPERTY": "Property not supported for prediction",
    "PREDICTION_TIMEOUT": "Prediction request timed out",
    "PREDICTION_SERVICE_UNAVAILABLE": "Prediction service is currently unavailable",
    "PREDICTION_JOB_NOT_FOUND": "Prediction job not found",
    "PREDICTION_LIMIT_EXCEEDED": "Prediction request limit exceeded",
    "INVALID_PREDICTION_PARAMETERS": "Invalid prediction parameters"
}

# External integration error messages
INTEGRATION_ERRORS = {
    "AI_ENGINE_CONNECTION_FAILED": "Failed to connect to AI prediction engine",
    "DOCUSIGN_CONNECTION_FAILED": "Failed to connect to DocuSign service",
    "S3_OPERATION_FAILED": "S3 storage operation failed",
    "SQS_OPERATION_FAILED": "Message queue operation failed",
    "EXTERNAL_API_ERROR": "External API returned an error",
    "INTEGRATION_TIMEOUT": "Integration request timed out",
    "INTEGRATION_AUTHENTICATION_FAILED": "Integration authentication failed",
    "INTEGRATION_RATE_LIMIT_EXCEEDED": "Integration rate limit exceeded"
}

# System-level error messages
SYSTEM_ERRORS = {
    "INTERNAL_SERVER_ERROR": "An internal server error occurred",
    "SERVICE_UNAVAILABLE": "Service temporarily unavailable",
    "DATABASE_ERROR": "Database operation failed",
    "UNEXPECTED_ERROR": "An unexpected error occurred",
    "CONFIGURATION_ERROR": "System configuration error",
    "RESOURCE_EXHAUSTED": "System resources exhausted",
    "MAINTENANCE_MODE": "System is currently in maintenance mode",
    "RATE_LIMIT_EXCEEDED": "Rate limit exceeded, please try again later"
}