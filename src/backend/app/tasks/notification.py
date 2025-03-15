"""
Implements asynchronous notification tasks for the Molecular Data Management and CRO Integration Platform.

This module provides Celery tasks for sending notifications to users based on system events,
particularly focusing on CRO submission workflow status changes, result availability, and system alerts.
"""

from typing import Dict, List, Optional, Any
from uuid import UUID

from .celery_app import celery_app
from ..core.logging import get_logger
from ..services.email_service import send_email, send_template_email
from ..constants.submission_status import SubmissionStatus
from ..db.session import db_session

# Set up logger
logger = get_logger(__name__)

# Define email templates for different notification types
NOTIFICATION_TEMPLATES = {
    'submission_created': 'submission/created.html',
    'submission_status_changed': 'submission/status_changed.html',
    'submission_pricing_provided': 'submission/pricing_provided.html',
    'submission_approved': 'submission/approved.html',
    'submission_rejected': 'submission/rejected.html',
    'submission_cancelled': 'submission/cancelled.html',
    'results_available': 'results/available.html',
    'results_reviewed': 'results/reviewed.html',
    'molecule_upload_complete': 'molecule/upload_complete.html',
    'prediction_complete': 'prediction/complete.html',
    'system_alert': 'system/alert.html',
}


@celery_app.task(name='tasks.notify_submission_status_change', queue='notifications')
def notify_submission_status_change(
    submission_id: UUID,
    old_status: str,
    new_status: str,
    additional_context: Optional[Dict[str, Any]] = None
) -> bool:
    """
    Send notification when a submission status changes.
    
    Args:
        submission_id: UUID of the submission
        old_status: Previous status of the submission
        new_status: New status of the submission
        additional_context: Optional additional context for the notification
        
    Returns:
        True if notification was sent successfully
    """
    logger.info(f"Notification task started: submission status change for {submission_id}: {old_status} -> {new_status}")
    
    try:
        # Retrieve submission details from database
        session = db_session()
        try:
            # In a real implementation, we would use proper ORM models
            # This is a simplified placeholder for the actual implementation
            
            # Get submission details with joins to user and CRO service
            submission_query = (
                "SELECT s.*, u.email as user_email, u.name as user_name, "
                "c.name as cro_name, c.contact_email as cro_email "
                "FROM submissions s "
                "JOIN users u ON s.created_by_id = u.id "
                "JOIN cro_services c ON s.cro_service_id = c.id "
                "WHERE s.id = :id"
            )
            submission = session.execute(submission_query, {"id": str(submission_id)}).fetchone()
            
            if not submission:
                logger.error(f"Submission not found: {submission_id}")
                return False
        finally:
            session.close()
        
        # Determine appropriate template
        template_name = get_notification_template('submission', new_status)
        
        # Prepare context
        context = {
            'submission_id': str(submission_id),
            'submission_name': submission.name,
            'old_status': old_status,
            'new_status': new_status,
            'user_name': submission.user_name,
            'cro_name': submission.cro_name
        }
        
        # Add any additional context
        if additional_context:
            context.update(additional_context)
        
        # Send notification to pharma user
        pharma_success = send_template_email(
            subject=f"Submission Status Update: {submission.name} - {new_status}",
            template_name=template_name,
            context=context,
            to_email=submission.user_email
        )
        
        # Send notification to CRO for specific status changes
        cro_success = True
        if new_status in [
            SubmissionStatus.SUBMITTED.value,
            SubmissionStatus.APPROVED.value,
            SubmissionStatus.CANCELLED.value
        ]:
            cro_success = send_template_email(
                subject=f"Submission Status Update: {submission.name} - {new_status}",
                template_name=template_name,
                context=context,
                to_email=submission.cro_email
            )
        
        logger.info(f"Notification completed for submission {submission_id} status change: {old_status} -> {new_status}")
        return pharma_success and cro_success
        
    except Exception as e:
        logger.error(f"Error sending submission status change notification: {str(e)}", exc_info=True)
        return False


@celery_app.task(name='tasks.notify_results_available', queue='notifications')
def notify_results_available(
    submission_id: UUID,
    result_id: UUID,
    additional_context: Optional[Dict[str, Any]] = None
) -> bool:
    """
    Send notification when experimental results are available.
    
    Args:
        submission_id: UUID of the submission
        result_id: UUID of the result
        additional_context: Optional additional context for the notification
        
    Returns:
        True if notification was sent successfully
    """
    logger.info(f"Notification task started: results available for submission {submission_id}, result {result_id}")
    
    try:
        # Retrieve submission and result details from database
        session = db_session()
        try:
            # In a real implementation, this would use proper ORM models
            # This is a simplified placeholder for the actual implementation
            
            # Get submission with user information
            submission_query = (
                "SELECT s.*, u.email as user_email, u.name as user_name "
                "FROM submissions s "
                "JOIN users u ON s.created_by_id = u.id "
                "WHERE s.id = :id"
            )
            submission = session.execute(submission_query, {"id": str(submission_id)}).fetchone()
            
            if not submission:
                logger.error(f"Submission not found: {submission_id}")
                return False
            
            # Get result details
            result_query = "SELECT * FROM results WHERE id = :id"
            result = session.execute(result_query, {"id": str(result_id)}).fetchone()
            
            if not result:
                logger.error(f"Result not found: {result_id}")
                return False
        finally:
            session.close()
        
        # Prepare context
        context = {
            'submission_id': str(submission_id),
            'submission_name': submission.name,
            'result_id': str(result_id),
            'uploaded_at': result.uploaded_at.isoformat() if hasattr(result.uploaded_at, 'isoformat') else result.uploaded_at,
            'user_name': submission.user_name
        }
        
        # Add any additional context
        if additional_context:
            context.update(additional_context)
        
        # Send notification to pharma user
        success = send_template_email(
            subject=f"Results Available: {submission.name}",
            template_name=NOTIFICATION_TEMPLATES['results_available'],
            context=context,
            to_email=submission.user_email
        )
        
        logger.info(f"Notification completed for results available: submission {submission_id}, result {result_id}")
        return success
        
    except Exception as e:
        logger.error(f"Error sending results available notification: {str(e)}", exc_info=True)
        return False


@celery_app.task(name='tasks.notify_molecule_upload_complete', queue='notifications')
def notify_molecule_upload_complete(
    upload_id: UUID,
    molecule_count: int,
    success_count: int,
    error_count: int,
    additional_context: Optional[Dict[str, Any]] = None
) -> bool:
    """
    Send notification when a molecule CSV upload is complete.
    
    Args:
        upload_id: UUID of the upload
        molecule_count: Total number of molecules in the upload
        success_count: Number of successfully processed molecules
        error_count: Number of molecules with processing errors
        additional_context: Optional additional context for the notification
        
    Returns:
        True if notification was sent successfully
    """
    logger.info(f"Notification task started: molecule upload complete for upload {upload_id}")
    
    try:
        # Retrieve upload details from database
        session = db_session()
        try:
            # In a real implementation, this would use proper ORM models
            # This is a simplified placeholder for the actual implementation
            
            # Get upload details with user information
            upload_query = (
                "SELECT u.*, usr.email as user_email, usr.name as user_name "
                "FROM molecule_uploads u "
                "JOIN users usr ON u.user_id = usr.id "
                "WHERE u.id = :id"
            )
            upload = session.execute(upload_query, {"id": str(upload_id)}).fetchone()
            
            if not upload:
                logger.error(f"Upload not found: {upload_id}")
                return False
        finally:
            session.close()
        
        # Prepare context
        context = {
            'upload_id': str(upload_id),
            'filename': upload.filename,
            'upload_date': upload.created_at.isoformat() if hasattr(upload.created_at, 'isoformat') else upload.created_at,
            'molecule_count': molecule_count,
            'success_count': success_count,
            'error_count': error_count,
            'success_rate': f"{(success_count / molecule_count * 100):.1f}%" if molecule_count > 0 else "0%",
            'user_name': upload.user_name
        }
        
        # Add any additional context
        if additional_context:
            context.update(additional_context)
        
        # Send notification
        success = send_template_email(
            subject=f"Molecule Upload Complete: {upload.filename}",
            template_name=NOTIFICATION_TEMPLATES['molecule_upload_complete'],
            context=context,
            to_email=upload.user_email
        )
        
        logger.info(f"Notification completed for molecule upload: {upload_id}")
        return success
        
    except Exception as e:
        logger.error(f"Error sending molecule upload notification: {str(e)}", exc_info=True)
        return False


@celery_app.task(name='tasks.notify_prediction_complete', queue='notifications')
def notify_prediction_complete(
    prediction_batch_id: UUID,
    molecule_count: int,
    additional_context: Optional[Dict[str, Any]] = None
) -> bool:
    """
    Send notification when AI predictions are complete.
    
    Args:
        prediction_batch_id: UUID of the prediction batch
        molecule_count: Number of molecules in the prediction batch
        additional_context: Optional additional context for the notification
        
    Returns:
        True if notification was sent successfully
    """
    logger.info(f"Notification task started: prediction complete for batch {prediction_batch_id}")
    
    try:
        # Retrieve prediction batch details from database
        session = db_session()
        try:
            # In a real implementation, this would use proper ORM models
            # This is a simplified placeholder for the actual implementation
            
            # Get prediction batch with user information
            batch_query = (
                "SELECT p.*, u.email as user_email, u.name as user_name "
                "FROM prediction_batches p "
                "JOIN users u ON p.user_id = u.id "
                "WHERE p.id = :id"
            )
            batch = session.execute(batch_query, {"id": str(prediction_batch_id)}).fetchone()
            
            if not batch:
                logger.error(f"Prediction batch not found: {prediction_batch_id}")
                return False
        finally:
            session.close()
        
        # Prepare context
        context = {
            'batch_id': str(prediction_batch_id),
            'batch_name': batch.name if hasattr(batch, 'name') else f"Batch {prediction_batch_id}",
            'molecule_count': molecule_count,
            'completion_time': batch.completed_at.isoformat() if hasattr(batch, 'completed_at') and hasattr(batch.completed_at, 'isoformat') else "Unknown",
            'user_name': batch.user_name
        }
        
        # Add any additional context
        if additional_context:
            context.update(additional_context)
        
        # Send notification
        success = send_template_email(
            subject=f"AI Predictions Complete: {context['batch_name']}",
            template_name=NOTIFICATION_TEMPLATES['prediction_complete'],
            context=context,
            to_email=batch.user_email
        )
        
        logger.info(f"Notification completed for prediction batch: {prediction_batch_id}")
        return success
        
    except Exception as e:
        logger.error(f"Error sending prediction complete notification: {str(e)}", exc_info=True)
        return False


@celery_app.task(name='tasks.notify_system_alert', queue='notifications')
def notify_system_alert(
    alert_type: str,
    alert_message: str,
    severity: str,
    additional_context: Optional[Dict[str, Any]] = None
) -> bool:
    """
    Send system alert notification to administrators.
    
    Args:
        alert_type: Type of system alert
        alert_message: Alert message
        severity: Alert severity (critical, high, medium, low)
        additional_context: Optional additional context for the notification
        
    Returns:
        True if notification was sent successfully
    """
    logger.info(f"Notification task started: system alert {alert_type} with {severity} severity")
    
    try:
        # Retrieve administrator users from database
        session = db_session()
        try:
            # In a real implementation, this would use proper ORM models
            # This is a simplified placeholder for the actual implementation
            
            # Get admin users
            admin_query = "SELECT * FROM users WHERE role = 'admin'"
            admin_users = session.execute(admin_query).fetchall()
            
            if not admin_users:
                logger.warning("No admin users found to send system alert")
                return False
        finally:
            session.close()
        
        # Prepare context
        from datetime import datetime
        context = {
            'alert_type': alert_type,
            'alert_message': alert_message,
            'severity': severity,
            'timestamp': datetime.now().isoformat()
        }
        
        # Add any additional context
        if additional_context:
            context.update(additional_context)
        
        # Send notification to all admin users
        success = True
        for admin in admin_users:
            result = send_template_email(
                subject=f"[{severity.upper()}] System Alert: {alert_type}",
                template_name=NOTIFICATION_TEMPLATES['system_alert'],
                context=context,
                to_email=admin.email
            )
            success = success and result
        
        logger.info(f"System alert notification completed: {alert_type}")
        return success
        
    except Exception as e:
        logger.error(f"Error sending system alert notification: {str(e)}", exc_info=True)
        return False


def get_notification_recipients(event_type: str, event_data: Dict[str, Any]) -> List[Dict[str, Any]]:
    """
    Helper function to determine notification recipients based on event type.
    
    Args:
        event_type: Type of event
        event_data: Data associated with the event
    
    Returns:
        List of recipient details including email and user information
    """
    recipients = []
    
    # For submission events, include pharma user and potentially CRO
    if event_type.startswith('submission'):
        submission_id = event_data.get('submission_id')
        if submission_id:
            session = db_session()
            try:
                # In a real implementation, this would use proper ORM models
                # This is a simplified placeholder for the actual implementation
                
                # Get submission details
                submission_query = (
                    "SELECT s.*, u.id as user_id, u.email as user_email, u.name as user_name, "
                    "c.id as cro_id, c.name as cro_name, c.contact_email as cro_email "
                    "FROM submissions s "
                    "JOIN users u ON s.created_by_id = u.id "
                    "JOIN cro_services c ON s.cro_service_id = c.id "
                    "WHERE s.id = :id"
                )
                submission = session.execute(submission_query, {"id": str(submission_id)}).fetchone()
                
                if submission:
                    # Add pharma user to recipients
                    recipients.append({
                        'id': submission.user_id,
                        'email': submission.user_email,
                        'name': submission.user_name,
                        'type': 'pharma'
                    })
                    
                    # For certain submission events, include CRO
                    new_status = event_data.get('new_status')
                    if new_status in [
                        SubmissionStatus.SUBMITTED.value,
                        SubmissionStatus.APPROVED.value,
                        SubmissionStatus.CANCELLED.value
                    ]:
                        recipients.append({
                            'id': submission.cro_id,
                            'email': submission.cro_email,
                            'name': submission.cro_name,
                            'type': 'cro'
                        })
            finally:
                session.close()
                
    # For result events, include pharma user
    elif event_type.startswith('result'):
        submission_id = event_data.get('submission_id')
        if submission_id:
            session = db_session()
            try:
                # In a real implementation, this would use proper ORM models
                # This is a simplified placeholder for the actual implementation
                
                # Get pharma user for the submission
                user_query = (
                    "SELECT u.id, u.email, u.name "
                    "FROM users u "
                    "JOIN submissions s ON s.created_by_id = u.id "
                    "WHERE s.id = :submission_id"
                )
                user = session.execute(user_query, {"submission_id": str(submission_id)}).fetchone()
                
                if user:
                    recipients.append({
                        'id': user.id,
                        'email': user.email,
                        'name': user.name,
                        'type': 'pharma'
                    })
            finally:
                session.close()
                
    # For molecule upload events, include uploading user
    elif event_type.startswith('molecule_upload'):
        upload_id = event_data.get('upload_id')
        if upload_id:
            session = db_session()
            try:
                # In a real implementation, this would use proper ORM models
                # This is a simplified placeholder for the actual implementation
                
                # Get user who uploaded the molecules
                user_query = (
                    "SELECT u.id, u.email, u.name "
                    "FROM users u "
                    "JOIN molecule_uploads m ON m.user_id = u.id "
                    "WHERE m.id = :upload_id"
                )
                user = session.execute(user_query, {"upload_id": str(upload_id)}).fetchone()
                
                if user:
                    recipients.append({
                        'id': user.id,
                        'email': user.email,
                        'name': user.name,
                        'type': 'user'
                    })
            finally:
                session.close()
                
    # For prediction events, include requesting user
    elif event_type.startswith('prediction'):
        batch_id = event_data.get('prediction_batch_id')
        if batch_id:
            session = db_session()
            try:
                # In a real implementation, this would use proper ORM models
                # This is a simplified placeholder for the actual implementation
                
                # Get user who requested the predictions
                user_query = (
                    "SELECT u.id, u.email, u.name "
                    "FROM users u "
                    "JOIN prediction_batches p ON p.user_id = u.id "
                    "WHERE p.id = :batch_id"
                )
                user = session.execute(user_query, {"batch_id": str(batch_id)}).fetchone()
                
                if user:
                    recipients.append({
                        'id': user.id,
                        'email': user.email,
                        'name': user.name,
                        'type': 'user'
                    })
            finally:
                session.close()
                
    # For system alerts, include all admin users
    elif event_type == 'system_alert':
        session = db_session()
        try:
            # In a real implementation, this would use proper ORM models
            # This is a simplified placeholder for the actual implementation
            
            # Get all admin users
            admin_query = "SELECT id, email, name FROM users WHERE role = 'admin'"
            admin_users = session.execute(admin_query).fetchall()
            
            for user in admin_users:
                recipients.append({
                    'id': user.id,
                    'email': user.email,
                    'name': user.name,
                    'type': 'admin'
                })
        finally:
            session.close()
    
    return recipients


def get_notification_template(event_type: str, status: Optional[str] = None) -> str:
    """
    Helper function to get the appropriate email template for a notification.
    
    Args:
        event_type: Type of event
        status: Optional status for status-based templates
    
    Returns:
        Template path for the notification
    """
    if event_type == 'submission':
        # Status-specific templates for submissions
        if status == SubmissionStatus.PRICING_PROVIDED.value:
            return NOTIFICATION_TEMPLATES['submission_pricing_provided']
        elif status == SubmissionStatus.APPROVED.value:
            return NOTIFICATION_TEMPLATES['submission_approved']
        elif status == SubmissionStatus.REJECTED.value:
            return NOTIFICATION_TEMPLATES['submission_rejected']
        elif status == SubmissionStatus.CANCELLED.value:
            return NOTIFICATION_TEMPLATES['submission_cancelled']
        else:
            return NOTIFICATION_TEMPLATES['submission_status_changed']
    elif event_type == 'results':
        return NOTIFICATION_TEMPLATES['results_available']
    elif event_type == 'molecule_upload':
        return NOTIFICATION_TEMPLATES['molecule_upload_complete']
    elif event_type == 'prediction':
        return NOTIFICATION_TEMPLATES['prediction_complete']
    elif event_type == 'system_alert':
        return NOTIFICATION_TEMPLATES['system_alert']
    else:
        # Default to status changed for submissions
        return NOTIFICATION_TEMPLATES['submission_status_changed']