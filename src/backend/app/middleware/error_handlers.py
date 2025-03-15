"""
Error Handlers Module

This module implements exception handlers for the FastAPI application to provide standardized
error responses across the Molecular Data Management and CRO Integration Platform. It ensures
consistent error handling with proper status codes and detailed error information.
"""

import traceback
import uuid
from typing import Dict, Any, Callable, List

import fastapi
from fastapi import Request, HTTPException, status
from fastapi.exceptions import RequestValidationError
from fastapi.responses import JSONResponse
from pydantic import ValidationError
from sqlalchemy.exc import SQLAlchemyError, IntegrityError

from ..core.logging import get_logger
from ..core.exceptions import (
    BaseAppException,
    ValidationException,
    AuthenticationException,
    AuthorizationException,
    NotFoundException,
    ConflictException,
    RateLimitException,
    ServiceUnavailableException,
    InternalServerException,
    MoleculeException,
    CSVException,
    LibraryException,
    SubmissionException,
    DocumentException,
    ResultException,
    PredictionException,
    IntegrationException,
)
from ..constants.error_messages import SYSTEM_ERRORS

# Set up logging
logger = get_logger(__name__)


def add_exception_handlers(app: fastapi.FastAPI) -> None:
    """
    Register all exception handlers with the FastAPI application.
    
    Args:
        app: FastAPI application instance
    """
    # Handle FastAPI validation errors
    app.add_exception_handler(RequestValidationError, handle_validation_error)
    
    # Handle Pydantic validation errors
    app.add_exception_handler(ValidationError, handle_pydantic_validation_error)
    
    # Handle FastAPI HTTP exceptions
    app.add_exception_handler(HTTPException, handle_http_exception)
    
    # Handle application-specific exceptions
    app.add_exception_handler(BaseAppException, handle_app_exception)
    
    # Handle database errors
    app.add_exception_handler(SQLAlchemyError, handle_sqlalchemy_error)
    app.add_exception_handler(IntegrityError, handle_integrity_error)
    
    # Fallback handler for any unhandled exceptions
    app.add_exception_handler(Exception, handle_generic_exception)


async def handle_validation_error(request: Request, exc: RequestValidationError) -> JSONResponse:
    """
    Handle FastAPI request validation errors.
    
    Args:
        request: FastAPI request object
        exc: Validation exception
        
    Returns:
        JSONResponse with structured error details
    """
    errors = format_validation_errors(exc.errors())
    
    # Log validation error with request path
    logger.warning(
        f"Validation error for request {request.url.path}: {str(exc)}",
        extra={"validation_errors": errors}
    )
    
    return JSONResponse(
        status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
        content={
            "error_code": "validation_error",
            "message": "Invalid request data",
            "details": {
                "validation_errors": errors
            },
            "status_code": status.HTTP_422_UNPROCESSABLE_ENTITY
        }
    )


async def handle_pydantic_validation_error(request: Request, exc: ValidationError) -> JSONResponse:
    """
    Handle Pydantic validation errors.
    
    Args:
        request: FastAPI request object
        exc: Pydantic validation exception
        
    Returns:
        JSONResponse with structured error details
    """
    errors = format_validation_errors(exc.errors())
    
    # Log validation error with request path
    logger.warning(
        f"Pydantic validation error for request {request.url.path}: {str(exc)}",
        extra={"validation_errors": errors}
    )
    
    return JSONResponse(
        status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
        content={
            "error_code": "validation_error",
            "message": "Invalid data structure",
            "details": {
                "validation_errors": errors
            },
            "status_code": status.HTTP_422_UNPROCESSABLE_ENTITY
        }
    )


async def handle_http_exception(request: Request, exc: HTTPException) -> JSONResponse:
    """
    Handle FastAPI HTTP exceptions.
    
    Args:
        request: FastAPI request object
        exc: HTTP exception
        
    Returns:
        JSONResponse with structured error details
    """
    status_code = exc.status_code
    detail = exc.detail
    
    # Log HTTP exception with request path and status code
    logger.warning(
        f"HTTP exception for request {request.url.path}: {status_code} - {detail}"
    )
    
    return JSONResponse(
        status_code=status_code,
        content={
            "error_code": f"http_{status_code}",
            "message": detail,
            "status_code": status_code
        }
    )


async def handle_app_exception(request: Request, exc: BaseAppException) -> JSONResponse:
    """
    Handle application-specific exceptions.
    
    Args:
        request: FastAPI request object
        exc: Application exception
        
    Returns:
        JSONResponse with structured error details
    """
    error_dict = exc.to_dict()
    
    # Log application exception with request path and error code
    logger.warning(
        f"Application exception for request {request.url.path}: {exc.error_code} - {exc.message}",
        extra={"error_details": error_dict}
    )
    
    return JSONResponse(
        status_code=exc.status_code,
        content=error_dict
    )


async def handle_sqlalchemy_error(request: Request, exc: SQLAlchemyError) -> JSONResponse:
    """
    Handle SQLAlchemy database errors.
    
    Args:
        request: FastAPI request object
        exc: SQLAlchemy exception
        
    Returns:
        JSONResponse with structured error details
    """
    error_id = str(uuid.uuid4())
    
    # Log database error with error ID and traceback
    logger.error(
        f"Database error for request {request.url.path}: {str(exc)}",
        extra={
            "error_id": error_id,
            "error_details": str(exc),
            "traceback": traceback.format_exc()
        }
    )
    
    return JSONResponse(
        status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
        content={
            "error_code": "database_error",
            "message": SYSTEM_ERRORS["DATABASE_ERROR"],
            "details": {
                "error_id": error_id
            },
            "status_code": status.HTTP_500_INTERNAL_SERVER_ERROR
        }
    )


async def handle_integrity_error(request: Request, exc: IntegrityError) -> JSONResponse:
    """
    Handle SQLAlchemy integrity errors (constraint violations).
    
    Args:
        request: FastAPI request object
        exc: IntegrityError exception
        
    Returns:
        JSONResponse with structured error details
    """
    error_msg = str(exc)
    error_id = str(uuid.uuid4())
    
    # Analyze integrity error to determine if it's a duplicate key violation
    is_duplicate = "duplicate key" in error_msg.lower() or "unique constraint" in error_msg.lower()
    
    status_code = status.HTTP_409_CONFLICT if is_duplicate else status.HTTP_500_INTERNAL_SERVER_ERROR
    error_code = "conflict" if is_duplicate else "database_error"
    message = "Resource already exists" if is_duplicate else SYSTEM_ERRORS["DATABASE_ERROR"]
    
    # Log integrity error with details
    logger.error(
        f"Database integrity error for request {request.url.path}: {str(exc)}",
        extra={
            "error_id": error_id,
            "error_details": str(exc),
            "traceback": traceback.format_exc()
        }
    )
    
    return JSONResponse(
        status_code=status_code,
        content={
            "error_code": error_code,
            "message": message,
            "details": {
                "error_id": error_id
            },
            "status_code": status_code
        }
    )


async def handle_generic_exception(request: Request, exc: Exception) -> JSONResponse:
    """
    Handle any unhandled exceptions as a fallback.
    
    Args:
        request: FastAPI request object
        exc: Any exception
        
    Returns:
        JSONResponse with structured error details
    """
    error_id = str(uuid.uuid4())
    
    # Log unhandled exception with error ID and full traceback
    logger.error(
        f"Unhandled exception for request {request.url.path}: {str(exc)}",
        extra={
            "error_id": error_id,
            "error_type": type(exc).__name__,
            "traceback": traceback.format_exc()
        }
    )
    
    return JSONResponse(
        status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
        content={
            "error_code": "internal_server_error",
            "message": SYSTEM_ERRORS["INTERNAL_SERVER_ERROR"],
            "details": {
                "error_id": error_id
            },
            "status_code": status.HTTP_500_INTERNAL_SERVER_ERROR
        }
    )


def format_validation_errors(errors: list) -> list:
    """
    Format validation errors into a consistent structure.
    
    Args:
        errors: List of validation error dictionaries
        
    Returns:
        List of formatted error dictionaries
    """
    formatted_errors = []
    
    for error in errors:
        formatted_error = {
            "field": ".".join([str(loc) for loc in error.get("loc", [])]),
            "type": error.get("type", "unknown_error"),
            "message": error.get("msg", "Validation error")
        }
        
        # Add ctx if available for more context
        if "ctx" in error:
            formatted_error["context"] = error["ctx"]
        
        formatted_errors.append(formatted_error)
    
    return formatted_errors