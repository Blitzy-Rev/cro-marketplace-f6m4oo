"""
Worker configuration module for the Molecular Data Management and CRO Integration Platform.

This module configures and initializes the Celery worker processes, setting up concurrency,
queue-specific settings, and worker lifecycle hooks. It ensures appropriate resource allocation
for different task types like CSV processing, AI predictions, and document handling.
"""

import os  # standard library
import multiprocessing  # standard library
from celery.signals import worker_ready, worker_shutdown, task_failure  # celery ^5.2.0

from ..core.logging import get_logger
from ..core.settings import settings
from .celery_app import task

# Set up logger
logger = get_logger(__name__)

# Worker concurrency settings - use environment variable or CPU count
WORKER_CONCURRENCY = int(os.environ.get('WORKER_CONCURRENCY', multiprocessing.cpu_count()))

# Define queue-specific concurrency settings to allocate resources appropriately
QUEUE_CONCURRENCY = {
    'csv_processing': max(1, WORKER_CONCURRENCY // 2),  # CPU-intensive tasks
    'ai_predictions': max(1, WORKER_CONCURRENCY // 2),  # CPU-intensive tasks
    'notifications': max(1, WORKER_CONCURRENCY // 4),   # I/O-bound tasks
    'document_processing': max(1, WORKER_CONCURRENCY // 4),  # I/O-bound tasks
    'result_processing': max(1, WORKER_CONCURRENCY // 4),    # I/O-bound tasks
    'default': max(1, WORKER_CONCURRENCY // 4),  # General-purpose tasks
}


def configure_worker():
    """
    Configure Celery worker settings based on environment and queue type.
    
    Returns:
        dict: Worker configuration dictionary
    """
    # Get Redis connection parameters from settings
    redis_params = settings.get_redis_connection_parameters()
    
    # Configure worker settings
    config = {
        # Worker concurrency settings
        "worker_concurrency": WORKER_CONCURRENCY,
        "queue_concurrency": QUEUE_CONCURRENCY,
        
        # Redis connection settings
        "broker_url": f"redis://{redis_params['host']}:{redis_params['port']}/{redis_params['db']}",
        "broker_connection_retry": True,
        "broker_connection_max_retries": 10,
        "broker_connection_timeout": 5.0,  # seconds
        
        # Task execution settings
        "task_time_limit": 3600,  # 1 hour
        "task_soft_time_limit": 3000,  # 50 minutes
        "worker_prefetch_multiplier": 1,  # Disable prefetching for fair processing
        
        # Logging settings
        "worker_redirect_stdouts": True,
        "worker_redirect_stdouts_level": "INFO",
        
        # Worker pool settings based on environment
        "worker_pool": "prefork",  # Use processes for better isolation
        "worker_pool_restarts": True,  # Enable worker pool restarts
    }
    
    # Add environment-specific settings
    if settings.ENV == "development":
        config.update({
            "worker_log_color": True,
            "worker_enable_remote_control": True,
        })
    elif settings.ENV == "production":
        config.update({
            "worker_log_color": False,
            "worker_enable_remote_control": False,
        })
    
    logger.info(f"Worker configured with concurrency: {WORKER_CONCURRENCY}")
    return config


@worker_ready.connect
def worker_ready(sender, **kwargs):
    """
    Signal handler for worker ready event.
    
    Args:
        sender (Any): The worker instance
        **kwargs (Any): Additional arguments
    
    Returns:
        None: Function performs side effects only
    """
    logger.info(f"Worker ready: {sender.hostname}")
    queues = getattr(sender, 'queues', ['unknown'])
    logger.info(f"Queues: {', '.join(str(q) for q in queues)}")
    
    # Initialize any required worker resources
    # Register worker with monitoring system if configured


@worker_shutdown.connect
def worker_shutdown(sender, **kwargs):
    """
    Signal handler for worker shutdown event.
    
    Args:
        sender (Any): The worker instance
        **kwargs (Any): Additional arguments
    
    Returns:
        None: Function performs side effects only
    """
    logger.info(f"Worker shutting down: {sender.hostname}")
    
    # Perform cleanup of worker resources
    # Ensure any in-progress tasks are properly handled


@task_failure.connect
def task_failure_handler(task, exc, task_id, args, kwargs, einfo):
    """
    Signal handler for task failure events.
    
    Args:
        task (Any): The task that failed
        exc (Exception): The exception raised
        task_id (str): The ID of the task
        args (Any): Task positional arguments
        kwargs (Any): Task keyword arguments
        einfo (Any): Exception information
    
    Returns:
        None: Function performs side effects only
    """
    logger.error(
        f"Task failure: {task.name}[{task_id}] raised {exc.__class__.__name__}: {str(exc)}",
        extra={
            "task_id": task_id,
            "task_name": task.name,
            "exception": str(exc),
            "traceback": einfo.traceback,
        }
    )
    
    # Implement custom error handling based on task type
    if task.name.startswith('tasks.csv_processing'):
        logger.info(f"Handling CSV processing failure for task {task_id}")
        # Could trigger a cleanup task or notification here
    elif task.name.startswith('tasks.ai_predictions'):
        logger.info(f"Handling AI prediction failure for task {task_id}")
        # Could trigger a fallback prediction method or notification here
    elif task.name.startswith('tasks.document_processing'):
        logger.info(f"Handling document processing failure for task {task_id}")
        # Could trigger appropriate failure handling tasks if needed