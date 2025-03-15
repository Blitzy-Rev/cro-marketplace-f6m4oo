import logging
import sys
import os

from fastapi import FastAPI, Request, Response, Depends, HTTPException, status
from fastapi.middleware.cors import CORSMiddleware  # fastapi version: 0.95+
from fastapi.exceptions import RequestValidationError
from pydantic import ValidationError
from sqlalchemy.exc import SQLAlchemyError, IntegrityError

from .core.config import settings  # Import application settings
from .api.api_v1.api import api_router  # Import API router with all endpoints
from .middleware.cors_middleware import setup_cors_middleware  # Import CORS middleware setup function
from .middleware.error_handlers import add_exception_handlers  # Import exception handler setup function
from .middleware.logging_middleware import LoggingMiddleware  # Import logging middleware
from .middleware.auth_middleware import AuthMiddleware  # Import authentication middleware
from .middleware.rate_limiter import RateLimitMiddleware, InMemoryRateLimiter, RedisRateLimiter  # Import rate limiting middleware
from .middleware.audit_middleware import AuditMiddleware  # Import audit logging middleware
from .db.init_db import init_db  # Import database initialization function
from .db.session import close_db_connections  # Import database connection cleanup function
from .core.logging import get_logger  # Import logger function

# Initialize logger
logger = get_logger(__name__)

# Create FastAPI application with title, version, and documentation URLs
app = FastAPI(title=settings.PROJECT_NAME, version=settings.VERSION, docs_url='/docs', redoc_url='/redoc', openapi_url='/openapi.json')

def configure_middleware(app: FastAPI) -> None:
    """Configure all middleware for the FastAPI application"""
    # Set up CORS middleware
    setup_cors_middleware(app)

    # Add logging middleware
    app.add_middleware(LoggingMiddleware)

    # Configure rate limiting middleware
    if settings.REDIS_URL:
        # Use RedisRateLimiter if Redis is configured
        rate_limiter = RedisRateLimiter(rate_limit=100, time_window=60)
    else:
        # Use InMemoryRateLimiter if Redis is not configured
        rate_limiter = InMemoryRateLimiter(rate_limit=100, time_window=60)

    # Add rate limit middleware
    app.add_middleware(RateLimitMiddleware, rate_limiter=rate_limiter, exclude_paths=['/health'])

    # Add authentication middleware
    app.add_middleware(AuthMiddleware)

    # Add audit middleware
    app.add_middleware(AuditMiddleware)

    # Set up exception handlers
    add_exception_handlers(app)

    logger.info("Middleware configured successfully")

def configure_routers(app: FastAPI) -> None:
    """Configure API routers for the FastAPI application"""
    # Include the API v1 router with prefix
    app.include_router(api_router, prefix=settings.API_V1_STR)

    logger.info("Routers configured successfully")

def configure_startup_events(app: FastAPI) -> None:
    """Configure startup event handlers for the FastAPI application"""
    @app.on_event("startup")
    async def startup_db_handler():
        """Startup event handler for database initialization"""
        logger.info("Application startup: initializing database")
        init_db()
        logger.info("Application startup: database initialized")

    logger.info("Startup events configured successfully")

def configure_shutdown_events(app: FastAPI) -> None:
    """Configure shutdown event handlers for the FastAPI application"""
    @app.on_event("shutdown")
    async def shutdown_db_handler():
        """Shutdown event handler for database connection cleanup"""
        logger.info("Application shutdown: cleaning up database connections")
        close_db_connections()
        logger.info("Application shutdown: database connections cleaned up")

    logger.info("Shutdown events configured successfully")

def get_app() -> FastAPI:
    """Create and configure the FastAPI application"""
    # Configure middleware
    configure_middleware(app)

    # Configure routers
    configure_routers(app)

    # Configure startup events
    configure_startup_events(app)

    # Configure shutdown events
    configure_shutdown_events(app)

    return app

# Configure middleware, routers, and events
# Configure middleware
configure_middleware(app)

# Configure routers
configure_routers(app)

# Configure startup events
configure_startup_events(app)

# Configure shutdown events
configure_shutdown_events(app)

if __name__ == "__main__":
    # Only run if the script is executed directly (not imported)
    import uvicorn  # uvicorn version: ^0.22.0

    # Determine host and port from environment or use defaults
    HOST = os.environ.get("HOST", "0.0.0.0")
    PORT = int(os.environ.get("PORT", 8000))
    RELOAD = os.environ.get("RELOAD", "False").lower() == "true"

    logger.info(f"Starting application: host={HOST}, port={PORT}, reload={RELOAD}")

    uvicorn.run(app, host=HOST, port=PORT, reload=RELOAD)