"""
Celery application configuration for the Molecular Data Management and CRO Integration Platform.

This module initializes and configures the Celery application for asynchronous task processing,
setting up the Redis broker connection, task routing, serialization, and error handling.
"""

import os  # standard library
from celery import Celery  # celery ^5.2.0
from kombu.serialization import register  # kombu ^5.2.0
import celery.signals  # celery ^5.2.0

from ..core.config import settings
from ..core.logging import get_logger

# Set up logger
logger = get_logger(__name__)

# Define task queues for different types of operations
TASK_QUEUES = {
    'csv_processing': 'Queue for CSV processing tasks',
    'ai_predictions': 'Queue for AI prediction tasks',
    'notifications': 'Queue for notification tasks',
    'document_processing': 'Queue for document processing tasks',
    'result_processing': 'Queue for result processing tasks',
    'default': 'Default queue for miscellaneous tasks'
}

# Define routing patterns for tasks to appropriate queues
TASK_ROUTES = {
    'tasks.csv_processing.*': {'queue': 'csv_processing'},
    'tasks.ai_predictions.*': {'queue': 'ai_predictions'},
    'tasks.notification.*': {'queue': 'notifications'},
    'tasks.document_processing.*': {'queue': 'document_processing'},
    'tasks.result_processing.*': {'queue': 'result_processing'}
}


def configure_task_serialization():
    """
    Configure task serialization formats.
    """
    # Use kombu to ensure proper JSON serialization
    # Note: JSON serialization is already registered by default in Celery,
    # but we can customize it if needed
    from kombu.serialization import registry
    
    # Check if JSON serialization is registered
    if 'json' in registry._decoders:
        logger.info("JSON serialization already registered")
    else:
        # This would only happen in very unusual circumstances
        logger.warning("JSON serialization not found, registering it")
        register('json', 
                 content_type='application/json',
                 content_encoding='utf-8')
    
    logger.info("Task serialization configured with JSON format")


def configure_task_routes(app):
    """
    Configure task routing to appropriate queues.
    
    Args:
        app (Celery): The Celery application instance
    """
    app.conf.task_routes = TASK_ROUTES
    logger.info(f"Task routes configured: {len(TASK_ROUTES)} patterns")


def on_task_failure(task, exc, task_id, args, kwargs, einfo):
    """
    Signal handler for task failure events.
    
    Args:
        task: The task instance
        exc: The exception raised
        task_id: The ID of the task
        args: Task positional arguments
        kwargs: Task keyword arguments
        einfo: Exception information
    """
    logger.error(
        f"Task failure: {task.name}[{task_id}] raised {exc.__class__.__name__}: {str(exc)}",
        extra={
            "task_id": task_id,
            "task_name": task.name,
            "exception": str(exc),
            "traceback": einfo.traceback
        }
    )
    
    # Additional error handling based on task type
    if task.name.startswith('tasks.csv_processing'):
        logger.info(f"Handling CSV processing failure for task {task_id}")
        # Could trigger a cleanup task or notification here
    elif task.name.startswith('tasks.ai_predictions'):
        logger.info(f"Handling AI prediction failure for task {task_id}")
        # Could trigger a fallback prediction method or notification here


def setup_error_handlers(app):
    """
    Set up error handling for Celery tasks.
    
    Args:
        app (Celery): The Celery application instance
    """
    # Register the task failure handler
    celery.signals.task_failure.connect(on_task_failure)
    
    # Configure default retry behavior
    app.conf.task_acks_late = True  # Tasks are acknowledged after execution
    app.conf.task_reject_on_worker_lost = True  # Requeue tasks if worker is lost
    
    # Set default retry settings
    app.conf.task_default_retry_delay = 3  # 3 seconds
    app.conf.task_max_retries = 3  # Retry 3 times by default
    
    logger.info("Task error handlers configured")


def create_celery_app():
    """
    Create and configure the Celery application instance.
    
    Returns:
        Celery: Configured Celery application instance
    """
    # Configure task serialization
    configure_task_serialization()
    
    # Create Celery app with project name
    app = Celery(settings.PROJECT_NAME)
    
    # Configure broker and backend
    app.conf.broker_url = settings.REDIS_URL
    app.conf.result_backend = f"redis://{settings.REDIS_URL.split('://')[-1]}"
    
    # Configure serialization
    app.conf.task_serializer = 'json'
    app.conf.result_serializer = 'json'
    app.conf.accept_content = ['json']
    
    # Configure task execution
    app.conf.task_time_limit = 3600  # 1 hour max runtime
    app.conf.task_soft_time_limit = 3000  # 50 minutes soft limit
    app.conf.worker_prefetch_multiplier = 1  # Disable prefetching for fair processing
    app.conf.task_default_queue = 'default'
    
    # Configure task routing
    configure_task_routes(app)
    
    # Set up error handling
    setup_error_handlers(app)
    
    # Add environment and configuration info
    app.conf.update(
        broker_transport_options={
            'visibility_timeout': 3600,  # 1 hour
            'max_connections': 100,
        },
        worker_send_task_events=True,
        task_send_sent_event=True,
        timezone='UTC',
        enable_utc=True,
    )
    
    logger.info(f"Celery app configured: {settings.PROJECT_NAME}, environment: {settings.ENV}")
    return app


# Create the celery application instance
celery_app = create_celery_app()

# Add optional configuration based on environment
if settings.ENV == "development":
    # Development-specific settings
    celery_app.conf.task_always_eager = os.environ.get("CELERY_ALWAYS_EAGER", "0") == "1"
    celery_app.conf.task_eager_propagates = True
    logger.info(f"Development mode: task_always_eager={celery_app.conf.task_always_eager}")