from fastapi import APIRouter  # fastapi version: ^0.95.0

from .health import router as health_router  # Import health check endpoint router
from .auth import router as auth_router  # Import authentication endpoint router
from .users import router as users_router  # Import user management endpoint router
from .molecules import router as molecules_router  # Import molecule management endpoint router
from .libraries import router as libraries_router  # Import library management endpoint router
from .cro import router as cro_router  # Import CRO service endpoint router
from .documents import router as documents_router  # Import document management endpoint router
from .submissions import router as submissions_router  # Import submission management endpoint router
from .predictions import router as predictions_router  # Import prediction endpoint router
from .results import router as results_router  # Import results management endpoint router
from ...core.logging import get_logger  # Import get logger for consistent log formatting

# Initialize logger
logger = get_logger(__name__)

# Export health check endpoints router for inclusion in the main API router
__all__ = [
    "health_router",
    "auth_router",
    "users_router",
    "molecules_router",
    "libraries_router",
    "cro_router",
    "documents_router",
    "submissions_router",
    "predictions_router",
    "results_router",
]

# Log the initialization of the endpoints
logger.info("API v1 endpoints initialized")