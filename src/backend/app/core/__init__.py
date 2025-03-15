"""
Core module initialization file that exports essential components for the Molecular Data Management and CRO Integration Platform. This file serves as the entry point for the core module, making key functionality available to the rest of the application through a clean, organized interface.
"""

# Configuration and environment settings
from .config import settings, load_environment_variables

# Constants and environment utilities
from .constants import (
    PROJECT_NAME,
    VERSION,
    API_V1_STR,
    get_environment,
    is_development,
    is_production,
)

# Security and authentication utilities
from .security import (
    verify_password,
    get_password_hash,
    create_access_token,
    create_refresh_token,
    validate_access_token,
    validate_refresh_token,
)

# Exception classes for standardized error handling
from .exceptions import (
    BaseAppException,
    ValidationException,
    AuthenticationException,
    AuthorizationException,
    NotFoundException,
)

# Logging and tracing utilities
from .logging import (
    setup_logging,
    get_logger,
    get_correlation_id,
    set_correlation_id,
)

# General utility functions and classes
from .utils import (
    generate_uuid,
    format_datetime,
    parse_datetime,
    Timer,
    Paginator,
)