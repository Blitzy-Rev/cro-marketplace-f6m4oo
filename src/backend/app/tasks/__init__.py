# src/backend/app/tasks/__init__.py
"""
Initializes the tasks module for the Molecular Data Management and CRO Integration Platform.
This file serves as the entry point for Celery tasks, exposing the Celery application instance and task functions from various task modules. It enables asynchronous processing of long-running operations such as CSV imports, AI predictions, and notifications.
"""

from .celery_app import celery_app  # Import Celery application instance for task registration and execution
from .csv_processing import process_csv_file  # Import CSV processing task for molecule data ingestion
from .csv_processing import process_csv_chunk  # Import CSV chunk processing task for large file handling
from .csv_processing import check_csv_job_status  # Import CSV job status checking task
from .csv_processing import trigger_predictions_after_import  # Import task to trigger predictions after CSV import
from .csv_processing import cleanup_csv_processing  # Import cleanup task for CSV processing
from .ai_predictions import submit_prediction_batch  # Import task for submitting molecule batches for AI prediction
from .ai_predictions import monitor_prediction_job  # Import task for monitoring AI prediction job status
from .ai_predictions import process_prediction_results  # Import task for processing AI prediction results
from .ai_predictions import retry_failed_prediction  # Import task for retrying failed AI predictions
from .ai_predictions import handle_prediction_failure  # Import task for handling AI prediction failures
from .notification import notify_submission_status_change  # Import task for notifying users about submission status changes
from .notification import notify_results_available  # Import task for notifying users about available results
from .notification import notify_molecule_upload_complete  # Import task for notifying users about completed molecule uploads
from .notification import notify_prediction_complete  # Import task for notifying users about completed predictions
from .notification import notify_system_alert  # Import task for sending system alerts to administrators

__all__ = [
    "celery_app",
    "process_csv_file",
    "process_csv_chunk",
    "check_csv_job_status",
    "trigger_predictions_after_import",
    "cleanup_csv_processing",
    "submit_prediction_batch",
    "monitor_prediction_job",
    "process_prediction_results",
    "retry_failed_prediction",
    "handle_prediction_failure",
    "notify_submission_status_change",
    "notify_results_available",
    "notify_molecule_upload_complete",
    "notify_prediction_complete",
    "notify_system_alert",
]