"""
Middleware package initialization for the Molecular Data Management and CRO Integration Platform.

This module exports all middleware components and provides a function to configure
and register middleware with a FastAPI application. The middleware components handle
cross-cutting concerns like authentication, logging, error handling, and compliance.
"""

from fastapi import FastAPI

# Import middleware components
from .logging_middleware import LoggingMiddleware
from .error_handlers import add_exception_handlers
from .cors_middleware import setup_cors_middleware
from .rate_limiter import (
    RateLimiter,
    InMemoryRateLimiter,
    RedisRateLimiter,
    RateLimitMiddleware
)
from .auth_middleware import (
    AuthMiddleware,
    get_current_user,
    get_current_active_user,
    require_roles,
    oauth2_scheme
)
from .audit_middleware import AuditMiddleware

# Import logging utilities and configuration
from ..core.logging import get_logger
from ..core.config import settings
from ..core.constants import RATE_LIMIT_DEFAULT, RATE_LIMIT_PERIOD_SECONDS

# Initialize logger
logger = get_logger(__name__)

def setup_middleware(app: FastAPI) -> None:
    """
    Configure and register all middleware components for a FastAPI application.
    
    Args:
        app: FastAPI application instance
    """
    # Register exception handlers
    add_exception_handlers(app)
    
    # Configure CORS middleware
    setup_cors_middleware(app)
    
    # Add logging middleware
    app.add_middleware(LoggingMiddleware)
    
    # Add authentication middleware
    app.add_middleware(AuthMiddleware)
    
    # Add audit logging middleware
    app.add_middleware(AuditMiddleware)
    
    # Configure rate limiting middleware
    try:
        # Create rate limiter based on configuration
        if hasattr(settings, 'REDIS_URL') and settings.REDIS_URL:
            # Use Redis-based rate limiter
            try:
                import redis
                
                redis_client = redis.Redis.from_url(settings.REDIS_URL)
                rate_limiter = RedisRateLimiter(
                    rate_limit=RATE_LIMIT_DEFAULT,
                    time_window=RATE_LIMIT_PERIOD_SECONDS,
                    redis_client=redis_client
                )
                logger.info("Configured Redis-based rate limiter")
            except (ImportError, Exception) as e:
                logger.warning(f"Failed to configure Redis rate limiter, falling back to in-memory: {str(e)}")
                rate_limiter = InMemoryRateLimiter(
                    rate_limit=RATE_LIMIT_DEFAULT,
                    time_window=RATE_LIMIT_PERIOD_SECONDS
                )
        else:
            # Use in-memory rate limiter
            rate_limiter = InMemoryRateLimiter(
                rate_limit=RATE_LIMIT_DEFAULT,
                time_window=RATE_LIMIT_PERIOD_SECONDS
            )
            logger.info("Configured in-memory rate limiter")
            
        # Add rate limiting middleware
        app.add_middleware(
            RateLimitMiddleware,
            rate_limiter=rate_limiter,
            exclude_paths=["/health", "/metrics", "/docs", "/redoc", "/openapi.json"]
        )
    except Exception as e:
        logger.warning(f"Error configuring rate limiting middleware: {str(e)}")
    
    logger.info("All middleware components configured successfully")

# Export all middleware components
__all__ = [
    'LoggingMiddleware',
    'AuthMiddleware',
    'AuditMiddleware',
    'RateLimitMiddleware',
    'RateLimiter',
    'InMemoryRateLimiter',
    'RedisRateLimiter',
    'add_exception_handlers',
    'setup_cors_middleware',
    'setup_middleware',
    'get_current_user',
    'get_current_active_user',
    'require_roles',
    'oauth2_scheme'
]