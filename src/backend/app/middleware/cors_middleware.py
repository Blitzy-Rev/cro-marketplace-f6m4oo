"""
CORS (Cross-Origin Resource Sharing) middleware configuration for the Molecular Data Management and CRO Integration Platform.

This file provides a function to set up CORS middleware with appropriate origins and headers to enable 
secure cross-origin requests between the frontend application and backend API.
"""

import logging  # standard library
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware  # FastAPI 0.95+
from ..core.config import settings
from ..core.logging import get_logger

# Set up logger for the middleware
logger = get_logger(__name__)

def setup_cors_middleware(app: FastAPI) -> None:
    """
    Configure and add CORS middleware to the FastAPI application.
    
    Args:
        app (FastAPI): The FastAPI application instance
        
    Returns:
        None: Function performs side effects only
    """
    logger.info(f"Configuring CORS middleware with origins: {settings.BACKEND_CORS_ORIGINS}")
    
    app.add_middleware(
        CORSMiddleware,
        allow_origins=settings.BACKEND_CORS_ORIGINS,
        allow_credentials=True,
        allow_methods=["GET", "POST", "PUT", "DELETE", "OPTIONS", "PATCH"],
        allow_headers=[
            "Content-Type", 
            "Authorization", 
            "X-Requested-With",
            "X-API-Key", 
            "Accept", 
            "Origin", 
            "X-CSRF-Token",
            "X-Molecule-ID",
            "X-Submission-ID"
        ],
        expose_headers=[
            "Content-Length", 
            "Content-Type", 
            "X-Request-ID",
            "X-Correlation-ID"
        ],
        max_age=86400,  # 24 hours cache for preflight requests
    )
    
    logger.info("CORS middleware configured successfully")