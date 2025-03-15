from typing import Optional, Any, Dict, List, Union
from sqlalchemy.orm import Session
from sqlalchemy import or_

from .base import CRUDBase
from ..models.user import User
from ..schemas.user import UserCreate, UserUpdate
from ..db.session import db_session


class CRUDUser(CRUDBase[User, UserCreate, UserUpdate]):
    """CRUD operations for User model with specialized methods for user management"""

    def get_by_email(self, email: str, db: Optional[Session] = None) -> Optional[User]:
        """
        Get a user by email address
        
        Args:
            email: User's email address
            db: Optional database session
            
        Returns:
            User instance if found, None otherwise
        """
        db_session_local = db or db_session
        return db_session_local.query(User).filter(User.email.ilike(email)).first()
    
    def create(self, obj_in: UserCreate, db: Optional[Session] = None) -> User:
        """
        Create a new user with password hashing
        
        Args:
            obj_in: User data for creation
            db: Optional database session
            
        Returns:
            Created user instance
        """
        db_session_local = db or db_session
        
        # Create a dictionary from obj_in excluding password
        obj_data = obj_in.model_dump(exclude={"password"})
        
        # Create user instance
        db_obj = User.from_dict(obj_data)
        
        # Set password hash
        db_obj.set_password(obj_in.password)
        
        # Add to database, commit, and refresh
        db_session_local.add(db_obj)
        db_session_local.commit()
        db_session_local.refresh(db_obj)
        
        return db_obj
    
    def update(self, db_obj: User, obj_in: Union[UserUpdate, Dict[str, Any]], db: Optional[Session] = None) -> User:
        """
        Update a user, handling password updates securely
        
        Args:
            db_obj: Existing user to update
            obj_in: User data for updating
            db: Optional database session
            
        Returns:
            Updated user instance
        """
        db_session_local = db or db_session
        
        # Convert obj_in to dict if it's a Pydantic model
        if not isinstance(obj_in, dict):
            update_data = obj_in.model_dump(exclude_unset=True)
        else:
            update_data = obj_in.copy()
        
        # Check if password is present in update data
        if "password" in update_data and update_data["password"]:
            # Update password separately using set_password method
            db_obj.set_password(update_data["password"])
            # Remove password from update data
            del update_data["password"]
        
        # Update remaining fields using parent update method
        return super().update(db_obj, update_data, db=db_session_local)
    
    def authenticate(self, email: str, password: str, db: Optional[Session] = None) -> Optional[User]:
        """
        Authenticate a user by email and password
        
        Args:
            email: User's email address
            password: User's password
            db: Optional database session
            
        Returns:
            Authenticated user or None if authentication fails
        """
        db_session_local = db or db_session
        
        # Get user by email
        user = self.get_by_email(email, db=db_session_local)
        if not user:
            return None
        
        # Verify password
        if not user.check_password(password):
            return None
        
        # Update last login timestamp
        user.update_last_login()
        
        # Commit changes
        db_session_local.add(user)
        db_session_local.commit()
        
        return user
    
    def is_active(self, user: User) -> bool:
        """
        Check if a user is active
        
        Args:
            user: User to check
            
        Returns:
            True if user is active, False otherwise
        """
        return user.is_active
    
    def is_superuser(self, user: User) -> bool:
        """
        Check if a user is a superuser
        
        Args:
            user: User to check
            
        Returns:
            True if user is a superuser, False otherwise
        """
        return user.is_superuser
    
    def get_by_organization(
        self, 
        organization_id: Any, 
        db: Optional[Session] = None,
        skip: int = 0,
        limit: int = 100
    ) -> Dict[str, Any]:
        """
        Get users belonging to a specific organization
        
        Args:
            organization_id: ID of the organization
            db: Optional database session
            skip: Number of records to skip (pagination)
            limit: Maximum number of records to return (pagination)
            
        Returns:
            Dictionary with users and pagination metadata
        """
        db_session_local = db or db_session
        
        # Query users by organization ID
        query = db_session_local.query(User).filter(User.organization_id == organization_id)
        
        # Get total count
        total = query.count()
        
        # Apply pagination
        users = query.offset(skip).limit(limit).all()
        
        # Return results with pagination metadata
        return {
            "items": users,
            "total": total,
            "page": skip // limit + 1 if limit > 0 else 1,
            "size": limit,
            "pages": (total + limit - 1) // limit if limit > 0 else 1
        }
    
    def search(
        self, 
        query: str, 
        db: Optional[Session] = None,
        skip: int = 0,
        limit: int = 100
    ) -> Dict[str, Any]:
        """
        Search users by email or full name
        
        Args:
            query: Search string
            db: Optional database session
            skip: Number of records to skip (pagination)
            limit: Maximum number of records to return (pagination)
            
        Returns:
            Dictionary with matching users and pagination metadata
        """
        db_session_local = db or db_session
        
        # Create search pattern for LIKE operator
        search_pattern = f"%{query}%"
        
        # Query users matching the search pattern in email or full name
        query_obj = db_session_local.query(User).filter(
            or_(
                User.email.ilike(search_pattern),
                User.full_name.ilike(search_pattern)
            )
        )
        
        # Get total count
        total = query_obj.count()
        
        # Apply pagination
        users = query_obj.offset(skip).limit(limit).all()
        
        # Return results with pagination metadata
        return {
            "items": users,
            "total": total,
            "page": skip // limit + 1 if limit > 0 else 1,
            "size": limit,
            "pages": (total + limit - 1) // limit if limit > 0 else 1
        }
    
    def get_by_role(
        self, 
        role: str, 
        db: Optional[Session] = None,
        skip: int = 0,
        limit: int = 100
    ) -> Dict[str, Any]:
        """
        Get users with a specific role
        
        Args:
            role: User role
            db: Optional database session
            skip: Number of records to skip (pagination)
            limit: Maximum number of records to return (pagination)
            
        Returns:
            Dictionary with users and pagination metadata
        """
        db_session_local = db or db_session
        
        # Query users by role
        query = db_session_local.query(User).filter(User.role == role)
        
        # Get total count
        total = query.count()
        
        # Apply pagination
        users = query.offset(skip).limit(limit).all()
        
        # Return results with pagination metadata
        return {
            "items": users,
            "total": total,
            "page": skip // limit + 1 if limit > 0 else 1,
            "size": limit,
            "pages": (total + limit - 1) // limit if limit > 0 else 1
        }


# Create a singleton instance
user = CRUDUser()