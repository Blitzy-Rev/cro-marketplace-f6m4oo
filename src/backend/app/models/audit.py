from enum import Enum
from sqlalchemy import Column, String, Text, JSON, ForeignKey, UUID
from sqlalchemy.orm import relationship, Session
from typing import Dict, List, Optional, Any
import datetime
import uuid

from ..db.base_class import Base


class AuditEventType(str, Enum):
    """Enumeration of possible audit event types for categorizing audit records"""
    CREATE = "CREATE"
    READ = "READ"
    UPDATE = "UPDATE"
    DELETE = "DELETE"
    LOGIN = "LOGIN"
    LOGOUT = "LOGOUT"
    EXPORT = "EXPORT"
    IMPORT = "IMPORT"
    SUBMISSION = "SUBMISSION"
    STATUS_CHANGE = "STATUS_CHANGE"
    DOCUMENT_SIGN = "DOCUMENT_SIGN"
    DOCUMENT_UPLOAD = "DOCUMENT_UPLOAD"
    RESULT_UPLOAD = "RESULT_UPLOAD"
    PERMISSION_CHANGE = "PERMISSION_CHANGE"
    SYSTEM_ERROR = "SYSTEM_ERROR"
    SECURITY_EVENT = "SECURITY_EVENT"


class Audit(Base):
    """
    SQLAlchemy model for audit records capturing all system activities
    for compliance and security monitoring.
    
    This model stores detailed audit information to meet regulatory requirements
    such as 21 CFR Part 11 and GDPR. It provides a tamper-evident audit trail
    for all system activities including data modifications, access attempts,
    and security events.
    """
    
    # User who performed the action
    user_id = Column(UUID, ForeignKey("user.id"), nullable=True, index=True)
    
    # What action was performed
    event_type = Column(String(50), nullable=False, index=True)
    
    # What resource was affected
    resource_type = Column(String(255), nullable=False, index=True)
    resource_id = Column(UUID, nullable=True, index=True)
    
    # Description of the action
    description = Column(Text, nullable=False)
    
    # Data before and after the change
    old_values = Column(JSON, nullable=True)
    new_values = Column(JSON, nullable=True)
    
    # Contextual information
    ip_address = Column(String(50), nullable=True)
    user_agent = Column(String(255), nullable=True)
    
    # Relationship with User model
    user = relationship("User")
    
    @classmethod
    def create_audit_log(
        cls,
        user_id: Optional[uuid.UUID],
        event_type: str,
        resource_type: str,
        resource_id: Optional[uuid.UUID],
        description: str,
        old_values: Optional[Dict[str, Any]] = None,
        new_values: Optional[Dict[str, Any]] = None,
        ip_address: Optional[str] = None,
        user_agent: Optional[str] = None
    ) -> "Audit":
        """
        Create a new audit log entry.
        
        Args:
            user_id: ID of the user who performed the action (None for system actions)
            event_type: Type of event (from AuditEventType enum)
            resource_type: Type of resource affected (e.g., "Molecule", "User")
            resource_id: ID of the specific resource instance affected
            description: Human-readable description of the action
            old_values: Previous state of the resource (for updates/deletes)
            new_values: New state of the resource (for creates/updates)
            ip_address: IP address where the request originated
            user_agent: User agent string from the request
            
        Returns:
            Created audit log entry
        """
        return cls(
            user_id=user_id,
            event_type=event_type,
            resource_type=resource_type,
            resource_id=resource_id,
            description=description,
            old_values=old_values,
            new_values=new_values,
            ip_address=ip_address,
            user_agent=user_agent
        )
    
    @classmethod
    def get_resource_history(
        cls,
        resource_type: str,
        resource_id: uuid.UUID,
        db: Optional[Session] = None,
        limit: Optional[int] = None,
        skip: Optional[int] = None
    ) -> List["Audit"]:
        """
        Get audit history for a specific resource.
        
        Args:
            resource_type: Type of resource (e.g., "Molecule", "User")
            resource_id: ID of the specific resource
            db: SQLAlchemy session (required if not using session.query directly)
            limit: Maximum number of records to return
            skip: Number of records to skip (for pagination)
            
        Returns:
            List of audit records for the resource, ordered by creation time descending
        """
        if db is None:
            raise ValueError("Database session is required")
            
        query = db.query(cls).filter(
            cls.resource_type == resource_type,
            cls.resource_id == resource_id
        ).order_by(cls.created_at.desc())
        
        if skip is not None:
            query = query.offset(skip)
        if limit is not None:
            query = query.limit(limit)
            
        return query.all()
    
    @classmethod
    def get_user_activity(
        cls,
        user_id: uuid.UUID,
        db: Optional[Session] = None,
        start_date: Optional[datetime.datetime] = None,
        end_date: Optional[datetime.datetime] = None,
        limit: Optional[int] = None,
        skip: Optional[int] = None
    ) -> List["Audit"]:
        """
        Get audit history for a specific user.
        
        Args:
            user_id: ID of the user
            db: SQLAlchemy session (required if not using session.query directly)
            start_date: Optional start date for filtering
            end_date: Optional end date for filtering
            limit: Maximum number of records to return
            skip: Number of records to skip (for pagination)
            
        Returns:
            List of audit records for the user, ordered by creation time descending
        """
        if db is None:
            raise ValueError("Database session is required")
            
        query = db.query(cls).filter(cls.user_id == user_id)
        
        if start_date is not None:
            query = query.filter(cls.created_at >= start_date)
        if end_date is not None:
            query = query.filter(cls.created_at <= end_date)
            
        query = query.order_by(cls.created_at.desc())
        
        if skip is not None:
            query = query.offset(skip)
        if limit is not None:
            query = query.limit(limit)
            
        return query.all()
    
    @classmethod
    def filter_by_event_type(
        cls,
        event_type: str,
        db: Optional[Session] = None,
        limit: Optional[int] = None,
        skip: Optional[int] = None
    ) -> List["Audit"]:
        """
        Filter audit records by event type.
        
        Args:
            event_type: Type of event to filter by (from AuditEventType enum)
            db: SQLAlchemy session (required if not using session.query directly)
            limit: Maximum number of records to return
            skip: Number of records to skip (for pagination)
            
        Returns:
            List of audit records with the specified event type
        """
        if db is None:
            raise ValueError("Database session is required")
            
        query = db.query(cls).filter(cls.event_type == event_type)
        query = query.order_by(cls.created_at.desc())
        
        if skip is not None:
            query = query.offset(skip)
        if limit is not None:
            query = query.limit(limit)
            
        return query.all()
    
    @classmethod
    def search_audit_logs(
        cls,
        user_id: Optional[uuid.UUID] = None,
        event_type: Optional[str] = None,
        resource_type: Optional[str] = None,
        resource_id: Optional[uuid.UUID] = None,
        start_date: Optional[datetime.datetime] = None,
        end_date: Optional[datetime.datetime] = None,
        search_term: Optional[str] = None,
        db: Optional[Session] = None,
        skip: int = 0,
        limit: int = 100
    ) -> List["Audit"]:
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
            db: SQLAlchemy session (required if not using session.query directly)
            skip: Number of records to skip (for pagination)
            limit: Maximum number of records to return
            
        Returns:
            List of matching audit records, ordered by creation time descending
        """
        if db is None:
            raise ValueError("Database session is required")
            
        query = db.query(cls)
        
        # Apply filters
        if user_id is not None:
            query = query.filter(cls.user_id == user_id)
        if event_type is not None:
            query = query.filter(cls.event_type == event_type)
        if resource_type is not None:
            query = query.filter(cls.resource_type == resource_type)
        if resource_id is not None:
            query = query.filter(cls.resource_id == resource_id)
        if start_date is not None:
            query = query.filter(cls.created_at >= start_date)
        if end_date is not None:
            query = query.filter(cls.created_at <= end_date)
        if search_term is not None:
            query = query.filter(cls.description.ilike(f"%{search_term}%"))
            
        # Order and paginate
        query = query.order_by(cls.created_at.desc())
        query = query.offset(skip).limit(limit)
            
        return query.all()
    
    def to_dict_with_related(self) -> Dict[str, Any]:
        """
        Convert audit record to dictionary with related data.
        
        Extends the base to_dict method with additional related information
        like user details for better context in audit reports.
        
        Returns:
            Dictionary representation with related data included
        """
        result = self.to_dict()
        
        # Add user information if available
        if hasattr(self, "user") and self.user is not None:
            result["user"] = {
                "id": str(self.user.id),
                "email": self.user.email,
                "name": getattr(self.user, "name", None)
            }
        
        # Format timestamps for readability
        if "created_at" in result and result["created_at"]:
            created_at = datetime.datetime.fromisoformat(result["created_at"])
            result["created_at_formatted"] = created_at.strftime("%Y-%m-%d %H:%M:%S UTC")
            
        return result