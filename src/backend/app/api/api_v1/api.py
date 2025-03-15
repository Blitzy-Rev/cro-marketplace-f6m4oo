from fastapi import APIRouter  # fastapi version: ^0.95.0

from .endpoints import health  # Import health check endpoints
from .endpoints import auth  # Import authentication endpoints
from .endpoints import users  # Import user management endpoints
from .endpoints import molecules  # Import molecule management endpoints
from .endpoints import libraries  # Import library management endpoints
from .endpoints import cro  # Import CRO service endpoints
from .endpoints import submissions  # Import submission management endpoints
from .endpoints import documents  # Import document management endpoints
from .endpoints import results  # Import results management endpoints
from .endpoints import predictions  # Import AI prediction endpoints

# Create main API router
api_router = APIRouter()

# Include endpoint routers with appropriate prefixes
api_router.include_router(health.router)
api_router.include_router(auth.router, prefix="/auth")
api_router.include_router(users.router, prefix="/users")
api_router.include_router(molecules.router, prefix="/molecules")
api_router.include_router(libraries.router, prefix="/libraries")
api_router.include_router(cro.router, prefix="/cro")
api_router.include_router(submissions.router, prefix="/submissions")
api_router.include_router(documents.router, prefix="/documents")
api_router.include_router(results.router, prefix="/results")
api_router.include_router(predictions.router, prefix="/predictions")

# Export the router