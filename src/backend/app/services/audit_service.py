import typing
from typing import Dict, List, Optional, Any, Union
import datetime
import uuid

from ..core.logging import get_logger, get_correlation_id
from ..models.audit import AuditEventType, Audit
from ..db.session import db_session
from ..core.config import settings

# Initialize logger
logger = get_logger(__name__)

def create_audit_log(
    user_id: uuid.UUID,
    event_type: str,
    resource_type: str,
    resource_id: Optional[uuid.UUID] = None,
    description: str = "",
    old_values: Optional[Dict[str, Any]] = None,
    new_values: Optional[Dict[str, Any]] = None,
    ip_address: Optional[str] = None,
    user_agent: Optional[str] = None,
) -> Optional[Audit]:
    """
    Create a new audit log entry with the provided information.
    
    Args:
        user_id: ID of the user who performed the action
        event_type: Type of event (from AuditEventType enum)
        resource_type: Type of resource affected (e.g., "Molecule", "User")
        resource_id: ID of the specific resource instance affected
        description: Human-readable description of the action
        old_values: Previous state of the resource (for updates/deletes)
        new_values: New state of the resource (for creates/updates)
        ip_address: IP address where the request originated
        user_agent: User agent string from the request
        
    Returns:
        Created audit log entry or None if audit logging is disabled
    """
    # Check if audit logging is enabled
    if not settings.AUDIT_ENABLED:
        logger.debug("Audit logging disabled, skipping audit record creation")
        return None
    
    try:
        # Get correlation ID for linking related events
        correlation_id = get_correlation_id()
        
        # Create audit record
        audit = Audit.create_audit_log(
            user_id=user_id,
            event_type=event_type,
            resource_type=resource_type,
            resource_id=resource_id,
            description=description,
            old_values=old_values,
            new_values=new_values,
            ip_address=ip_address,
            user_agent=user_agent,
        )
        
        # Add to session and commit
        db_session.add(audit)
        db_session.commit()
        
        logger.info(
            f"Audit record created: {event_type} on {resource_type}"
            f"{f'/{resource_id}' if resource_id else ''} by user {user_id}"
        )
        
        return audit
    except Exception as e:
        db_session.rollback()
        logger.error(f"Failed to create audit log: {str(e)}")
        return None

def get_resource_history(
    resource_type: str,
    resource_id: uuid.UUID,
    limit: Optional[int] = None,
    skip: Optional[int] = None,
) -> List[Audit]:
    """
    Get audit history for a specific resource.
    
    Args:
        resource_type: Type of resource (e.g., "Molecule", "User")
        resource_id: ID of the specific resource
        limit: Maximum number of records to return
        skip: Number of records to skip (for pagination)
        
    Returns:
        List of audit records for the resource
    """
    if not settings.AUDIT_ENABLED:
        logger.debug("Audit logging disabled, returning empty resource history")
        return []
    
    try:
        return Audit.get_resource_history(
            resource_type=resource_type,
            resource_id=resource_id,
            db=db_session,
            limit=limit,
            skip=skip,
        )
    except Exception as e:
        logger.error(f"Failed to get resource history: {str(e)}")
        return []

def get_user_activity(
    user_id: uuid.UUID,
    start_date: Optional[datetime.datetime] = None,
    end_date: Optional[datetime.datetime] = None,
    limit: Optional[int] = None,
    skip: Optional[int] = None,
) -> List[Audit]:
    """
    Get audit history for a specific user.
    
    Args:
        user_id: ID of the user
        start_date: Optional start date for filtering
        end_date: Optional end date for filtering
        limit: Maximum number of records to return
        skip: Number of records to skip (for pagination)
        
    Returns:
        List of audit records for the user
    """
    if not settings.AUDIT_ENABLED:
        logger.debug("Audit logging disabled, returning empty user activity")
        return []
    
    try:
        return Audit.get_user_activity(
            user_id=user_id,
            db=db_session,
            start_date=start_date,
            end_date=end_date,
            limit=limit,
            skip=skip,
        )
    except Exception as e:
        logger.error(f"Failed to get user activity: {str(e)}")
        return []

def get_audit_by_event_type(
    event_type: Union[str, AuditEventType],
    limit: Optional[int] = None,
    skip: Optional[int] = None,
) -> List[Audit]:
    """
    Get audit records filtered by event type.
    
    Args:
        event_type: Type of event to filter by (string or AuditEventType)
        limit: Maximum number of records to return
        skip: Number of records to skip (for pagination)
        
    Returns:
        List of audit records with the specified event type
    """
    if not settings.AUDIT_ENABLED:
        logger.debug("Audit logging disabled, returning empty event type results")
        return []
    
    try:
        # Convert enum to string if needed
        if isinstance(event_type, AuditEventType):
            event_type = event_type.value
            
        return Audit.filter_by_event_type(
            event_type=event_type,
            db=db_session,
            limit=limit,
            skip=skip,
        )
    except Exception as e:
        logger.error(f"Failed to get audit by event type: {str(e)}")
        return []

def search_audit_logs(
    user_id: Optional[uuid.UUID] = None,
    event_type: Optional[str] = None,
    resource_type: Optional[str] = None,
    resource_id: Optional[uuid.UUID] = None,
    start_date: Optional[datetime.datetime] = None,
    end_date: Optional[datetime.datetime] = None,
    search_term: Optional[str] = None,
    skip: int = 0,
    limit: int = 100,
) -> List[Audit]:
    """
    Search audit logs with various filters.
    
    Args:
        user_id: Optional user ID to filter by
        event_type: Optional event type to filter by
        resource_type: Optional resource type to filter by
        resource_id: Optional resource ID to filter by
        start_date: Optional start date for filtering
        end_date: Optional end date for filtering
        search_term: Optional term to search for in the description
        skip: Number of records to skip (for pagination)
        limit: Maximum number of records to return
        
    Returns:
        List of matching audit records
    """
    if not settings.AUDIT_ENABLED:
        logger.debug("Audit logging disabled, returning empty search results")
        return []
    
    try:
        return Audit.search_audit_logs(
            user_id=user_id,
            event_type=event_type,
            resource_type=resource_type,
            resource_id=resource_id,
            start_date=start_date,
            end_date=end_date,
            search_term=search_term,
            db=db_session,
            skip=skip,
            limit=limit,
        )
    except Exception as e:
        logger.error(f"Failed to search audit logs: {str(e)}")
        return []

def log_login_event(
    user_id: uuid.UUID,
    ip_address: Optional[str] = None,
    user_agent: Optional[str] = None,
) -> Optional[Audit]:
    """
    Create an audit log entry for a user login event.
    
    Args:
        user_id: ID of the user who logged in
        ip_address: IP address where the login originated
        user_agent: User agent string from the request
        
    Returns:
        Created audit log entry or None if audit logging is disabled
    """
    return create_audit_log(
        user_id=user_id,
        event_type=AuditEventType.LOGIN,
        resource_type="user",
        resource_id=user_id,
        description="User login successful",
        ip_address=ip_address,
        user_agent=user_agent,
    )

def log_logout_event(
    user_id: uuid.UUID,
    ip_address: Optional[str] = None,
    user_agent: Optional[str] = None,
) -> Optional[Audit]:
    """
    Create an audit log entry for a user logout event.
    
    Args:
        user_id: ID of the user who logged out
        ip_address: IP address where the logout originated
        user_agent: User agent string from the request
        
    Returns:
        Created audit log entry or None if audit logging is disabled
    """
    return create_audit_log(
        user_id=user_id,
        event_type=AuditEventType.LOGOUT,
        resource_type="user",
        resource_id=user_id,
        description="User logout",
        ip_address=ip_address,
        user_agent=user_agent,
    )

def log_data_access(
    user_id: uuid.UUID,
    resource_type: str,
    resource_id: uuid.UUID,
    description: str,
    ip_address: Optional[str] = None,
    user_agent: Optional[str] = None,
) -> Optional[Audit]:
    """
    Create an audit log entry for data access events.
    
    Args:
        user_id: ID of the user who accessed the data
        resource_type: Type of resource accessed
        resource_id: ID of the specific resource accessed
        description: Description of the access
        ip_address: IP address where the access originated
        user_agent: User agent string from the request
        
    Returns:
        Created audit log entry or None if audit logging is disabled
    """
    return create_audit_log(
        user_id=user_id,
        event_type=AuditEventType.READ,
        resource_type=resource_type,
        resource_id=resource_id,
        description=description,
        ip_address=ip_address,
        user_agent=user_agent,
    )

def log_data_modification(
    user_id: uuid.UUID,
    event_type: Union[str, AuditEventType],
    resource_type: str,
    resource_id: uuid.UUID,
    description: str,
    old_values: Dict[str, Any],
    new_values: Dict[str, Any],
    ip_address: Optional[str] = None,
    user_agent: Optional[str] = None,
) -> Optional[Audit]:
    """
    Create an audit log entry for data modification events.
    
    Args:
        user_id: ID of the user who modified the data
        event_type: Type of modification (CREATE, UPDATE, DELETE)
        resource_type: Type of resource modified
        resource_id: ID of the specific resource modified
        description: Description of the modification
        old_values: Previous state of the resource
        new_values: New state of the resource
        ip_address: IP address where the modification originated
        user_agent: User agent string from the request
        
    Returns:
        Created audit log entry or None if audit logging is disabled
    """
    # Convert enum to string if needed
    if isinstance(event_type, AuditEventType):
        event_type = event_type.value
        
    # Validate event type is a modification type
    valid_types = [AuditEventType.CREATE.value, AuditEventType.UPDATE.value, AuditEventType.DELETE.value]
    if event_type not in valid_types:
        logger.error(f"Invalid modification event type: {event_type}")
        return None
    
    return create_audit_log(
        user_id=user_id,
        event_type=event_type,
        resource_type=resource_type,
        resource_id=resource_id,
        description=description,
        old_values=old_values,
        new_values=new_values,
        ip_address=ip_address,
        user_agent=user_agent,
    )