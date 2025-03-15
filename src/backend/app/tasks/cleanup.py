"""
Implements scheduled and on-demand cleanup tasks for the Molecular Data Management and CRO Integration Platform.

This module handles the removal of temporary files, expired documents, orphaned database records,
and stale task entries to maintain system performance and data integrity.
"""

from typing import List, Dict, Any, Optional
from datetime import datetime, timedelta

import sqlalchemy

from .celery_app import celery_app
from ..core.logging import get_logger
from ..core.settings import settings
from ..services.storage_service import (
    storage_service,
    CSV_FOLDER,
    DOCUMENT_FOLDER,
    RESULT_FOLDER
)
from ..db.session import db_session
from ..models.document import Document
from ..constants.document_types import DOCUMENT_STATUS

# Set up logger
logger = get_logger(__name__)

# Constants for retry behavior and batch processing
MAX_RETRIES = 3
RETRY_DELAY = 60  # seconds
BATCH_SIZE = 100  # number of records to process in a batch


@celery_app.task(name='tasks.cleanup.cleanup_temporary_files', bind=True, max_retries=MAX_RETRIES, default_retry_delay=RETRY_DELAY)
def cleanup_temporary_files(self, folder: Optional[str] = None, days: Optional[int] = None) -> Dict[str, Any]:
    """
    Celery task to clean up temporary files older than the configured retention period.
    
    Args:
        folder: Optional specific folder to clean up (if not specified, all folders will be cleaned)
        days: Optional number of days to retain files (defaults to settings.TEMP_FILE_RETENTION_DAYS)
    
    Returns:
        Dict[str, Any]: Cleanup result with statistics
    """
    logger.info(f"Starting temporary file cleanup task: folder={folder}, days={days}")
    stats = {"deleted_files": 0, "total_size": 0, "errors": 0}
    
    try:
        # Use provided days or default from settings
        retention_days = days if days is not None else settings.TEMP_FILE_RETENTION_DAYS
        cutoff_date = datetime.utcnow() - timedelta(days=retention_days)
        logger.info(f"Cleaning up files older than {cutoff_date.isoformat()}")

        # Define folders to clean
        folders_to_clean = []
        if folder:
            folders_to_clean.append(folder)
        else:
            folders_to_clean = [CSV_FOLDER, DOCUMENT_FOLDER, RESULT_FOLDER]
        
        # Process each folder
        for target_folder in folders_to_clean:
            logger.info(f"Cleaning up files in folder: {target_folder}")
            
            try:
                # List objects in the folder
                objects = storage_service.S3Client.list(prefix=target_folder)
                
                # Filter objects older than cutoff date
                for object_key in objects:
                    try:
                        # Get object metadata
                        metadata = storage_service.S3Client.get_metadata(object_key)
                        last_modified = metadata.get('LastModified')
                        
                        if last_modified and last_modified < cutoff_date:
                            # Get size before deletion for statistics
                            size = metadata.get('ContentLength', 0)
                            
                            # Delete the file
                            storage_service.delete_file(object_key)
                            
                            # Update statistics
                            stats["deleted_files"] += 1
                            stats["total_size"] += size
                            
                            logger.info(f"Deleted file: {object_key}, size: {size} bytes")
                    
                    except Exception as e:
                        logger.error(f"Error processing file {object_key}: {str(e)}")
                        stats["errors"] += 1
            
            except Exception as e:
                logger.error(f"Error listing files in folder {target_folder}: {str(e)}")
                stats["errors"] += 1
        
        logger.info(f"Temporary file cleanup complete. Stats: {stats}")
        return stats
    
    except Exception as e:
        logger.error(f"Error in temporary file cleanup: {str(e)}")
        
        # Retry the task if it's not the final retry
        if self.request.retries < MAX_RETRIES:
            raise self.retry(exc=e)
        
        # On final retry, log the error and return stats with error information
        stats["error"] = str(e)
        return stats


@celery_app.task(name='tasks.cleanup.cleanup_expired_documents', bind=True, max_retries=MAX_RETRIES, default_retry_delay=RETRY_DELAY)
def cleanup_expired_documents(self, days: Optional[int] = None) -> Dict[str, Any]:
    """
    Celery task to mark documents as expired after the configured expiration period.
    
    Args:
        days: Optional number of days after which documents expire (defaults to settings.DOCUMENT_EXPIRATION_DAYS)
    
    Returns:
        Dict[str, Any]: Cleanup result with statistics
    """
    logger.info(f"Starting expired documents cleanup task: days={days}")
    stats = {"expired_documents": 0, "errors": 0}
    
    try:
        # Use provided days or default from settings
        expiration_days = days if days is not None else settings.DOCUMENT_EXPIRATION_DAYS
        cutoff_date = datetime.utcnow() - timedelta(days=expiration_days)
        logger.info(f"Marking documents created before {cutoff_date.isoformat()} as expired")
        
        # Create database session
        session = db_session()
        
        try:
            # Query for documents created before cutoff date that aren't already expired
            # Process in batches to avoid memory issues with large result sets
            offset = 0
            while True:
                # Query for a batch of documents
                documents = session.query(Document).filter(
                    Document.created_at < cutoff_date,
                    Document.status != DOCUMENT_STATUS['EXPIRED']
                ).limit(BATCH_SIZE).offset(offset).all()
                
                # If no documents returned, we're done
                if not documents:
                    break
                
                # Update each document's status
                for document in documents:
                    try:
                        document.status = DOCUMENT_STATUS['EXPIRED']
                        stats["expired_documents"] += 1
                    except Exception as e:
                        logger.error(f"Error updating document {document.id}: {str(e)}")
                        stats["errors"] += 1
                
                # Commit batch
                session.commit()
                
                # Move to next batch
                offset += BATCH_SIZE
                logger.info(f"Processed batch of {len(documents)} documents")
            
            logger.info(f"Expired documents cleanup complete. Stats: {stats}")
            return stats
        
        except Exception as e:
            # Rollback on error
            session.rollback()
            raise e
        
        finally:
            # Close the session
            session.close()
    
    except Exception as e:
        logger.error(f"Error in expired documents cleanup: {str(e)}")
        
        # Retry the task if it's not the final retry
        if self.request.retries < MAX_RETRIES:
            raise self.retry(exc=e)
        
        # On final retry, log the error and return stats with error information
        stats["error"] = str(e)
        return stats


@celery_app.task(name='tasks.cleanup.cleanup_orphaned_records', bind=True, max_retries=MAX_RETRIES, default_retry_delay=RETRY_DELAY)
def cleanup_orphaned_records(self) -> Dict[str, Any]:
    """
    Celery task to clean up orphaned database records.
    
    Returns:
        Dict[str, Any]: Cleanup result with statistics
    """
    logger.info("Starting orphaned records cleanup task")
    stats = {
        "deleted_molecule_properties": 0,
        "deleted_library_molecules": 0,
        "deleted_documents": 0,
        "deleted_results": 0,
        "errors": 0
    }
    
    try:
        # Create database session
        session = db_session()
        
        try:
            # Clean up orphaned molecule_property records (where molecule_id doesn't exist)
            try:
                result = session.execute(
                    """
                    DELETE FROM molecule_property mp
                    WHERE NOT EXISTS (
                        SELECT 1 FROM molecule m WHERE m.id = mp.molecule_id
                    )
                    """
                )
                stats["deleted_molecule_properties"] = result.rowcount
                session.commit()
                logger.info(f"Deleted {stats['deleted_molecule_properties']} orphaned molecule properties")
            except Exception as e:
                session.rollback()
                logger.error(f"Error cleaning up orphaned molecule properties: {str(e)}")
                stats["errors"] += 1
            
            # Clean up orphaned library_molecule records (where library_id or molecule_id doesn't exist)
            try:
                result = session.execute(
                    """
                    DELETE FROM library_molecule lm
                    WHERE NOT EXISTS (
                        SELECT 1 FROM library l WHERE l.id = lm.library_id
                    ) OR NOT EXISTS (
                        SELECT 1 FROM molecule m WHERE m.id = lm.molecule_id
                    )
                    """
                )
                stats["deleted_library_molecules"] = result.rowcount
                session.commit()
                logger.info(f"Deleted {stats['deleted_library_molecules']} orphaned library molecules")
            except Exception as e:
                session.rollback()
                logger.error(f"Error cleaning up orphaned library molecules: {str(e)}")
                stats["errors"] += 1
            
            # Clean up orphaned document records (where submission_id doesn't exist)
            try:
                result = session.execute(
                    """
                    DELETE FROM document d
                    WHERE d.submission_id IS NOT NULL AND NOT EXISTS (
                        SELECT 1 FROM submission s WHERE s.id = d.submission_id
                    )
                    """
                )
                stats["deleted_documents"] = result.rowcount
                session.commit()
                logger.info(f"Deleted {stats['deleted_documents']} orphaned documents")
            except Exception as e:
                session.rollback()
                logger.error(f"Error cleaning up orphaned documents: {str(e)}")
                stats["errors"] += 1
            
            # Clean up orphaned result records (where submission_id doesn't exist)
            try:
                result = session.execute(
                    """
                    DELETE FROM result r
                    WHERE NOT EXISTS (
                        SELECT 1 FROM submission s WHERE s.id = r.submission_id
                    )
                    """
                )
                stats["deleted_results"] = result.rowcount
                session.commit()
                logger.info(f"Deleted {stats['deleted_results']} orphaned results")
            except Exception as e:
                session.rollback()
                logger.error(f"Error cleaning up orphaned results: {str(e)}")
                stats["errors"] += 1
            
            logger.info(f"Orphaned records cleanup complete. Stats: {stats}")
            return stats
        
        finally:
            # Close the session
            session.close()
    
    except Exception as e:
        logger.error(f"Error in orphaned records cleanup: {str(e)}")
        
        # Retry the task if it's not the final retry
        if self.request.retries < MAX_RETRIES:
            raise self.retry(exc=e)
        
        # On final retry, log the error and return stats with error information
        stats["error"] = str(e)
        return stats


@celery_app.task(name='tasks.cleanup.cleanup_task_history', bind=True, max_retries=MAX_RETRIES, default_retry_delay=RETRY_DELAY)
def cleanup_task_history(self, days: Optional[int] = None) -> Dict[str, Any]:
    """
    Celery task to clean up old task history records.
    
    Args:
        days: Optional number of days to retain task history (defaults to settings.TASK_HISTORY_RETENTION_DAYS)
    
    Returns:
        Dict[str, Any]: Cleanup result with statistics
    """
    logger.info(f"Starting task history cleanup: days={days}")
    stats = {"deleted_tasks": 0, "errors": 0}
    
    try:
        # Use provided days or default from settings
        retention_days = days if days is not None else settings.TASK_HISTORY_RETENTION_DAYS
        cutoff_date = datetime.utcnow() - timedelta(days=retention_days)
        logger.info(f"Cleaning up tasks older than {cutoff_date.isoformat()}")
        
        # Get the Celery app's backend
        backend = self.app.backend
        
        # This implementation depends on the backend type
        # For Redis backend, we can execute the cleanup
        if hasattr(backend, 'client') and hasattr(backend.client, 'keys'):
            try:
                # Get all task result keys
                task_keys = backend.client.keys('celery-task-meta-*')
                
                for key in task_keys:
                    try:
                        # Get task result data
                        result_data = backend.client.get(key)
                        if result_data:
                            # Parse result data to check timestamp
                            import json
                            result = json.loads(result_data)
                            
                            # Check if task is older than cutoff date
                            if 'date_done' in result:
                                date_done = datetime.fromisoformat(result['date_done'].replace('Z', '+00:00'))
                                if date_done < cutoff_date:
                                    # Delete the task result
                                    backend.client.delete(key)
                                    stats["deleted_tasks"] += 1
                    except Exception as e:
                        logger.error(f"Error processing task key {key}: {str(e)}")
                        stats["errors"] += 1
                
                logger.info(f"Task history cleanup complete. Stats: {stats}")
                return stats
            
            except Exception as e:
                logger.error(f"Error accessing Redis backend: {str(e)}")
                raise e
        else:
            logger.warning("Task history cleanup not implemented for this backend type")
            stats["warning"] = "Cleanup not implemented for this backend type"
            return stats
    
    except Exception as e:
        logger.error(f"Error in task history cleanup: {str(e)}")
        
        # Retry the task if it's not the final retry
        if self.request.retries < MAX_RETRIES:
            raise self.retry(exc=e)
        
        # On final retry, log the error and return stats with error information
        stats["error"] = str(e)
        return stats


@celery_app.task(name='tasks.cleanup.run_scheduled_cleanup')
def run_scheduled_cleanup() -> Dict[str, Any]:
    """
    Celery task to run all cleanup tasks on a schedule.
    
    Returns:
        Dict[str, Any]: Cleanup result with statistics from all tasks
    """
    logger.info("Starting scheduled cleanup tasks")
    stats = {}
    
    try:
        # Run each cleanup task and collect results
        temp_files_result = cleanup_temporary_files.delay().get()
        stats["temporary_files"] = temp_files_result
        
        expired_docs_result = cleanup_expired_documents.delay().get()
        stats["expired_documents"] = expired_docs_result
        
        orphaned_records_result = cleanup_orphaned_records.delay().get()
        stats["orphaned_records"] = orphaned_records_result
        
        task_history_result = cleanup_task_history.delay().get()
        stats["task_history"] = task_history_result
        
        logger.info("All scheduled cleanup tasks completed successfully")
        return stats
    
    except Exception as e:
        logger.error(f"Error in scheduled cleanup: {str(e)}")
        stats["error"] = str(e)
        return stats