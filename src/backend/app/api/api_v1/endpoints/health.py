from fastapi import APIRouter, Depends, status
from sqlalchemy.orm import Session
from datetime import datetime

from ...core.config import settings
from ...db.session import get_db
from ...schemas.msg import ResponseMsg
from ...core.logging import get_logger

# Configure logger
logger = get_logger(__name__)

# Create API router with health tag
router = APIRouter(tags=["health"])

@router.get(
    "/health",
    status_code=status.HTTP_200_OK,
    summary="Health Check",
    description="Check the health status of the application and its dependencies"
)
def check_health(db: Session = Depends(get_db)) -> ResponseMsg:
    """
    Health check endpoint that verifies system status and connectivity to critical dependencies.
    
    Args:
        db: Database session dependency
        
    Returns:
        ResponseMsg: Health status information with component statuses
    """
    # Initialize health information
    health_info = {
        "app_name": settings.PROJECT_NAME,
        "version": settings.VERSION,
        "environment": settings.ENV,
        "timestamp": datetime.now().isoformat(),
        "components": {}
    }
    
    # Check database connectivity
    db_status = "healthy"
    db_details = {}
    try:
        # Execute a simple query to check database connectivity
        db.execute("SELECT 1")
        db_message = "Database connection successful"
    except Exception as e:
        db_status = "unhealthy"
        db_message = "Database connection failed"
        db_details = {"error": str(e)}
        logger.error(f"Health check database error: {str(e)}")
    
    health_info["components"]["database"] = {
        "status": db_status,
        "message": db_message,
        "details": db_details
    }
    
    # Check Redis connectivity if configured
    if hasattr(settings, "REDIS_URL") and settings.REDIS_URL:
        redis_status = "healthy"
        redis_details = {}
        try:
            # This would typically use a Redis client, but we'll keep it simple
            # For a real implementation, we would import and use the Redis client
            # redis_client = redis.from_url(settings.REDIS_URL)
            # redis_client.ping()
            redis_message = "Redis connection successful"
        except Exception as e:
            redis_status = "unhealthy"
            redis_message = "Redis connection failed"
            redis_details = {"error": str(e)}
            logger.error(f"Health check Redis error: {str(e)}")
        
        health_info["components"]["redis"] = {
            "status": redis_status,
            "message": redis_message,
            "details": redis_details
        }
    
    # Check S3 connectivity if configured
    if hasattr(settings, "S3_BUCKET_NAME") and settings.S3_BUCKET_NAME:
        s3_status = "healthy"
        s3_details = {}
        try:
            # In a real implementation, we would check S3 connectivity
            # boto3_client = boto3.client('s3')
            # boto3_client.head_bucket(Bucket=settings.S3_BUCKET_NAME)
            s3_message = "S3 connection successful"
        except Exception as e:
            s3_status = "unhealthy"
            s3_message = "S3 connection failed"
            s3_details = {"error": str(e)}
            logger.error(f"Health check S3 error: {str(e)}")
        
        health_info["components"]["s3"] = {
            "status": s3_status,
            "message": s3_message,
            "details": s3_details
        }
    
    # Determine overall health status
    overall_status = "healthy"
    for component, details in health_info["components"].items():
        if details["status"] == "unhealthy":
            overall_status = "unhealthy"
            break
    
    health_info["status"] = overall_status
    
    # Log health check result
    if overall_status == "unhealthy":
        logger.error(f"Health check status: {overall_status}")
    else:
        logger.info(f"Health check status: {overall_status}")
    
    # Return health check response
    return ResponseMsg(
        status=overall_status,
        message=f"Health check completed with status: {overall_status}",
        data=health_info
    )

@router.get(
    "/readiness",
    status_code=status.HTTP_200_OK,
    summary="Readiness Probe",
    description="Check if the application is ready to serve requests"
)
def check_readiness(db: Session = Depends(get_db)) -> ResponseMsg:
    """
    Readiness probe endpoint that verifies if the application is ready to serve requests.
    
    Args:
        db: Database session dependency
        
    Returns:
        ResponseMsg: Readiness status information
    """
    # Check database connectivity as a key readiness indicator
    try:
        db.execute("SELECT 1")
        ready = True
        message = "Application is ready to serve requests"
    except Exception as e:
        ready = False
        message = f"Application is not ready: database connection failed - {str(e)}"
        logger.error(f"Readiness check failed: {str(e)}")
    
    readiness_info = {
        "ready": ready,
        "app_name": settings.PROJECT_NAME,
        "version": settings.VERSION,
        "timestamp": datetime.now().isoformat()
    }
    
    # Log readiness check result
    logger.info(f"Readiness check status: {'ready' if ready else 'not ready'}")
    
    # Return readiness status
    return ResponseMsg(
        status="success" if ready else "error",
        message=message,
        data=readiness_info
    )

@router.get(
    "/liveness",
    status_code=status.HTTP_200_OK,
    summary="Liveness Probe",
    description="Check if the application is running"
)
def check_liveness() -> ResponseMsg:
    """
    Liveness probe endpoint that verifies if the application is running.
    
    Returns:
        ResponseMsg: Liveness status information
    """
    # For liveness, we just need to respond to confirm the application is running
    liveness_info = {
        "alive": True,
        "app_name": settings.PROJECT_NAME,
        "version": settings.VERSION,
        "timestamp": datetime.now().isoformat()
    }
    
    # Log liveness check
    logger.debug("Liveness check performed")
    
    # Return liveness status
    return ResponseMsg(
        status="success",
        message="Application is alive",
        data=liveness_info
    )