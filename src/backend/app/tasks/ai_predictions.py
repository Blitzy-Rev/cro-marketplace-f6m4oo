"""
Implements Celery tasks for asynchronous AI property prediction processing in the Molecular Data Management and CRO Integration Platform.
This module handles batch prediction requests, monitors prediction job status, processes results, and manages error handling for AI prediction operations.
"""

import uuid
import time
from typing import Dict, Any, Optional
from celery import Celery

from .celery_app import celery_app, get_logger
from ..services.prediction_service import PredictionService, prediction_service
from ..integrations.ai_engine.exceptions import AIEngineException, AIEngineTimeoutError, AIServiceUnavailableError
from ..core.exceptions import PredictionException
from ..db.session import db_session

# Initialize logger
logger = get_logger(__name__)

# Constants for retry configuration
MAX_RETRIES = 3
RETRY_DELAY = 60  # seconds
MAX_RETRY_DELAY = 300  # seconds
POLL_INTERVAL = 30  # seconds


@celery_app.task(name='tasks.ai_predictions.submit_prediction_batch', bind=True, max_retries=MAX_RETRIES, default_retry_delay=RETRY_DELAY)
def submit_prediction_batch(self: Celery, batch_id: uuid.UUID) -> Dict[str, Any]:
    """
    Celery task to submit a batch of molecules for AI property prediction.

    Args:
        batch_id (uuid.UUID): The ID of the prediction batch.

    Returns:
        Dict[str, Any]: Result of the prediction batch submission.
    """
    logger.info(f"Starting submit_prediction_batch task for batch_id: {batch_id}")
    db_session_local = next(db_session())
    try:
        # Get batch details from database
        batch = prediction_service.get_prediction_job_status(batch_id, db=db_session_local)
        job_id = batch.get("external_job_id")
        if not job_id:
            logger.error(f"No job_id found for batch_id: {batch_id}")
            raise PredictionException(f"No job_id found for batch_id: {batch_id}")

        # Submit batch to AI engine using prediction_service
        result = prediction_service.check_and_update_prediction_job(batch_id, job_id, db=db_session_local)

        logger.info(f"Successfully submitted prediction batch {batch_id} to AI Engine, job_id: {job_id}")
        return {"batch_id": str(batch_id), "status": "submitted", "job_id": job_id}

    except AIServiceUnavailableError as exc:
        # Retry with exponential backoff
        retry_delay = self.retry_backoff_factor * (2 ** self.request.retries)
        if retry_delay > MAX_RETRY_DELAY:
            retry_delay = MAX_RETRY_DELAY
        logger.warning(f"AI service unavailable, retrying in {retry_delay} seconds")
        raise self.retry(exc=exc, countdown=retry_delay)

    except AIEngineTimeoutError as exc:
        # Retry with longer delay
        retry_delay = MAX_RETRY_DELAY
        logger.warning(f"AI engine timeout, retrying in {retry_delay} seconds")
        raise self.retry(exc=exc, countdown=retry_delay)

    except Exception as exc:
        # Log error and handle failure
        logger.error(f"Failed to submit prediction batch {batch_id}: {str(exc)}")
        prediction_service.handle_prediction_failure(batch_id, str(exc), db=db_session_local)
        return {"batch_id": str(batch_id), "status": "failed", "error": str(exc)}

    finally:
        db_session_local.close()


@celery_app.task(name='tasks.ai_predictions.monitor_prediction_job', bind=True, max_retries=MAX_RETRIES, default_retry_delay=RETRY_DELAY)
def monitor_prediction_job(self: Celery, batch_id: uuid.UUID, job_id: str) -> Dict[str, Any]:
    """
    Celery task to monitor the status of an AI prediction job.

    Args:
        batch_id (uuid.UUID): The ID of the prediction batch.
        job_id (str): The ID of the prediction job.

    Returns:
        Dict[str, Any]: Result of the monitoring operation.
    """
    logger.info(f"Starting monitor_prediction_job task for batch_id: {batch_id}, job_id: {job_id}")
    db_session_local = next(db_session())
    try:
        # Check and update prediction job status
        job_status = prediction_service.check_and_update_prediction_job(batch_id, job_id, db=db_session_local)

        if job_status["status"] == "processing":
            # Job is still processing, schedule this task again after POLL_INTERVAL
            logger.info(f"Job {job_id} is still processing, rescheduling task in {POLL_INTERVAL} seconds")
            self.retry(countdown=POLL_INTERVAL)
        elif job_status["status"] == "completed":
            # Job is completed, schedule process_prediction_results task
            logger.info(f"Job {job_id} completed, scheduling process_prediction_results task")
            process_prediction_results.delay(str(batch_id), job_id)
        elif job_status["status"] == "failed":
            # Job failed, handle prediction failure
            logger.error(f"Job {job_id} failed, handling prediction failure")
            prediction_service.handle_prediction_failure(batch_id, "AI Engine prediction failed", db=db_session_local)

        return {"batch_id": str(batch_id), "job_id": job_id, "status": job_status["status"]}

    except AIServiceUnavailableError as exc:
        # Retry with exponential backoff
        retry_delay = self.retry_backoff_factor * (2 ** self.request.retries)
        if retry_delay > MAX_RETRY_DELAY:
            retry_delay = MAX_RETRY_DELAY
        logger.warning(f"AI service unavailable, retrying in {retry_delay} seconds")
        raise self.retry(exc=exc, countdown=retry_delay)

    except AIEngineTimeoutError as exc:
        # Retry with longer delay
        retry_delay = MAX_RETRY_DELAY
        logger.warning(f"AI engine timeout, retrying in {retry_delay} seconds")
        raise self.retry(exc=exc, countdown=retry_delay)

    except Exception as exc:
        # Log error and handle failure
        logger.error(f"Failed to monitor prediction job {job_id}: {str(exc)}")
        prediction_service.handle_prediction_failure(batch_id, str(exc), db=db_session_local)
        return {"batch_id": str(batch_id), "job_id": job_id, "status": "failed", "error": str(exc)}

    finally:
        db_session_local.close()


@celery_app.task(name='tasks.ai_predictions.process_prediction_results', bind=True, max_retries=MAX_RETRIES, default_retry_delay=RETRY_DELAY)
def process_prediction_results(self: Celery, batch_id: uuid.UUID, job_id: str) -> Dict[str, Any]:
    """
    Celery task to process and store AI prediction results.

    Args:
        batch_id (uuid.UUID): The ID of the prediction batch.
        job_id (str): The ID of the prediction job.

    Returns:
        Dict[str, Any]: Result of the processing operation.
    """
    logger.info(f"Starting process_prediction_results task for batch_id: {batch_id}, job_id: {job_id}")
    db_session_local = next(db_session())
    try:
        # Process prediction results using prediction_service
        result = prediction_service.process_prediction_results(batch_id, job_id, db=db_session_local)

        logger.info(f"Successfully processed prediction results for job {job_id}, processed predictions: {result['success_count']}")
        return {"batch_id": str(batch_id), "job_id": job_id, "success_count": result["success_count"], "failure_count": result["failure_count"]}

    except AIServiceUnavailableError as exc:
        # Retry with exponential backoff
        retry_delay = self.retry_backoff_factor * (2 ** self.request.retries)
        if retry_delay > MAX_RETRY_DELAY:
            retry_delay = MAX_RETRY_DELAY
        logger.warning(f"AI service unavailable, retrying in {retry_delay} seconds")
        raise self.retry(exc=exc, countdown=retry_delay)

    except AIEngineTimeoutError as exc:
        # Retry with longer delay
        retry_delay = MAX_RETRY_DELAY
        logger.warning(f"AI engine timeout, retrying in {retry_delay} seconds")
        raise self.retry(exc=exc, countdown=retry_delay)

    except Exception as exc:
        # Log error and handle failure
        logger.error(f"Failed to process prediction results for job {job_id}: {str(exc)}")
        prediction_service.handle_prediction_failure(batch_id, str(exc), db=db_session_local)
        return {"batch_id": str(batch_id), "job_id": job_id, "status": "failed", "error": str(exc)}

    finally:
        db_session_local.close()


@celery_app.task(name='tasks.ai_predictions.retry_failed_prediction')
def retry_failed_prediction(batch_id: uuid.UUID) -> Dict[str, Any]:
    """
    Celery task to retry a failed prediction batch.

    Args:
        batch_id (uuid.UUID): The ID of the prediction batch.

    Returns:
        Dict[str, Any]: Result of the retry operation.
    """
    logger.info(f"Starting retry_failed_prediction task for batch_id: {batch_id}")
    # Schedule submit_prediction_batch task with the batch_id
    submit_prediction_batch.delay(batch_id)
    return {"batch_id": str(batch_id), "status": "retrying"}


@celery_app.task(name='tasks.ai_predictions.handle_prediction_failure')
def handle_prediction_failure(batch_id: uuid.UUID, error_message: str) -> Dict[str, Any]:
    """
    Celery task to handle a failed prediction job.

    Args:
        batch_id (uuid.UUID): The ID of the prediction batch.
        error_message (str): The error message.

    Returns:
        Dict[str, Any]: Result of the failure handling operation.
    """
    logger.info(f"Starting handle_prediction_failure task for batch_id: {batch_id}, error_message: {error_message}")
    db_session_local = next(db_session())
    try:
        # Handle prediction failure using prediction_service
        result = prediction_service.handle_prediction_failure(batch_id, error_message, db=db_session_local)
        logger.info(f"Successfully handled prediction failure for batch_id: {batch_id}, status: {result['status']}")
        return {"batch_id": str(batch_id), "status": result["status"], "error_message": error_message}

    except Exception as exc:
        # Log error
        logger.error(f"Failed to handle prediction failure for batch {batch_id}: {str(exc)}")
        return {"batch_id": str(batch_id), "status": "error", "error": str(exc)}

    finally:
        db_session_local.close()