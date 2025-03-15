from fastapi import APIRouter  # fastapi version: ^0.95.0

from .api_v1.api import api_router as api_v1_router  # Import the main API router from the api_v1 module

# Create main API router
api_router = APIRouter()

# Include v1 API router
api_router.include_router(api_v1_router, prefix="/api/v1")

# Export the router