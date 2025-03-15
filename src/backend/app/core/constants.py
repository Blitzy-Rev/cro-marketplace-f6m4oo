"""
Core application constants for the Molecular Data Management and CRO Integration Platform.

This module defines system-wide constants used across the application, including
API version information, environment settings, pagination defaults, and other
configuration values that need to be accessible throughout the application.
"""

import os  # standard library - built into Python

# Project information
PROJECT_NAME = "Molecular Data Management and CRO Integration Platform"
VERSION = "1.0.0"
API_V1_STR = "/api/v1"

# Environment constants
ENVIRONMENT_DEVELOPMENT = "development"
ENVIRONMENT_TESTING = "testing"
ENVIRONMENT_STAGING = "staging"
ENVIRONMENT_PRODUCTION = "production"
ENVIRONMENTS = [ENVIRONMENT_DEVELOPMENT, ENVIRONMENT_TESTING, ENVIRONMENT_STAGING, ENVIRONMENT_PRODUCTION]
DEFAULT_ENVIRONMENT = ENVIRONMENT_DEVELOPMENT

# Pagination defaults
DEFAULT_PAGE_SIZE = 50
MAX_PAGE_SIZE = 100
DEFAULT_SORT_FIELD = "created_at"
DEFAULT_SORT_DIRECTION = "desc"

# Data processing limits
CSV_MAX_FILE_SIZE_MB = 100
CSV_MAX_ROWS = 500000
MOLECULE_BATCH_SIZE = 1000
AI_PREDICTION_BATCH_SIZE = 100

# Security constants
TOKEN_ALGORITHM = "HS256"
PASSWORD_MIN_LENGTH = 12
PASSWORD_REGEX = r"^(?=.*[a-z])(?=.*[A-Z])(?=.*\d)(?=.*[@$!%*?&])[A-Za-z\d@$!%*?&]{12,}$"
MAX_LOGIN_ATTEMPTS = 5
ACCOUNT_LOCKOUT_MINUTES = 30

# File handling
UPLOAD_FOLDER = "uploads"
ALLOWED_UPLOAD_EXTENSIONS = ['.csv', '.sdf', '.mol', '.pdf', '.docx', '.xlsx']
TEMP_FOLDER = "temp"

# Logging
LOG_FORMAT = "%(asctime)s - %(name)s - %(levelname)s - %(message)s"
DEFAULT_LOG_LEVEL = "INFO"

# Caching
CACHE_TTL_SECONDS = 300  # 5 minutes

# Rate limiting
RATE_LIMIT_DEFAULT = 100  # requests
RATE_LIMIT_PERIOD_SECONDS = 60  # per minute

# CORS settings
CORS_ALLOW_ORIGINS = "*"
CORS_ALLOW_METHODS = ["GET", "POST", "PUT", "DELETE", "OPTIONS", "PATCH"]
CORS_ALLOW_HEADERS = ["Content-Type", "Authorization", "X-Requested-With"]
CORS_MAX_AGE = 86400  # 24 hours

# API documentation
HEALTH_CHECK_PATH = "/health"
DOCS_URL = "/docs"
REDOC_URL = "/redoc"
OPENAPI_URL = "/openapi.json"
OPENAPI_TITLE = PROJECT_NAME
OPENAPI_DESCRIPTION = "API for managing molecular data and CRO integrations"


def get_environment() -> str:
    """
    Get the current environment from environment variables or use default.
    
    Returns:
        str: Current environment name
    """
    env = os.environ.get('ENVIRONMENT')
    if env is None or env not in ENVIRONMENTS:
        return DEFAULT_ENVIRONMENT
    return env


def is_development() -> bool:
    """
    Check if the current environment is development.
    
    Returns:
        bool: True if in development environment, False otherwise
    """
    return get_environment() == ENVIRONMENT_DEVELOPMENT


def is_testing() -> bool:
    """
    Check if the current environment is testing.
    
    Returns:
        bool: True if in testing environment, False otherwise
    """
    return get_environment() == ENVIRONMENT_TESTING


def is_production() -> bool:
    """
    Check if the current environment is production.
    
    Returns:
        bool: True if in production environment, False otherwise
    """
    return get_environment() == ENVIRONMENT_PRODUCTION