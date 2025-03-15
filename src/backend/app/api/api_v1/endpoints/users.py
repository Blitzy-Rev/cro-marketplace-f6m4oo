from typing import Dict, Any, Optional, List
from uuid import UUID

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session

# Internal imports
from ../../api.deps import (
    get_db,
    get_current_user,
    get_current_superuser,
    get_current_admin,
    get_organization_access
)
from ../../schemas.user import (
    User, 
    UserCreate, 
    UserUpdate, 
    UserWithPermissions
)
from ../../schemas.msg import ResponseMsg
from ../../crud.crud_user import user
from ../../core.exceptions import ValidationException, AuthorizationException
from ../../services.user_service import get_user_permissions

router = APIRouter(tags=["users"])


@router.get("/", response_model=Dict[str, Any])
async def get_users(
    skip: int = 0,
    limit: int = 100,
    current_user: User = Depends(get_current_admin),
    db: Session = Depends(get_db)
) -> Dict[str, Any]:
    """
    Get list of users with pagination.
    
    Only admins can view users. Regular admins can only see users 
    from their own organization, while superusers can see all users.
    """
    if current_user.is_superuser:
        # Superusers can see all users
        users_data = user.get_multi(db=db, skip=skip, limit=limit)
    else:
        # Regular admins can only see users from their organization
        users_data = user.get_by_organization(
            organization_id=current_user.organization_id, 
            db=db, 
            skip=skip, 
            limit=limit
        )
    
    return users_data


@router.post("/", response_model=User, status_code=status.HTTP_201_CREATED)
async def create_user(
    user_in: UserCreate,
    current_user: User = Depends(get_current_admin),
    db: Session = Depends(get_db)
) -> User:
    """
    Create a new user.
    
    Only admins can create users. The user will be created in the
    same organization as the admin unless the admin is a superuser.
    """
    # Check if user with same email already exists
    existing_user = user.get_by_email(email=user_in.email, db=db)
    if existing_user:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="A user with this email already exists"
        )
    
    # If not a superuser, set the organization to the current user's organization
    if not current_user.is_superuser and not user_in.organization_id:
        user_in.organization_id = current_user.organization_id
        if hasattr(current_user, 'organization_name') and current_user.organization_name:
            user_in.organization_name = current_user.organization_name
    
    # Create the new user
    new_user = user.create(obj_in=user_in, db=db)
    return new_user


@router.get("/me", response_model=User)
async def get_me(
    current_user: User = Depends(get_current_user)
) -> User:
    """
    Get current user information.
    """
    return current_user


@router.get("/me/permissions", response_model=UserWithPermissions)
async def get_my_permissions(
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
) -> UserWithPermissions:
    """
    Get current user permissions.
    """
    # Get user permissions
    permissions = get_user_permissions(current_user, db)
    
    # Combine user data with permissions
    user_with_permissions = UserWithPermissions.model_validate({
        **current_user.to_dict(),
        "permissions": permissions
    })
    
    return user_with_permissions


@router.put("/me", response_model=User)
async def update_me(
    user_in: UserUpdate,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
) -> User:
    """
    Update current user information.
    
    Users can only update their own profile information, not role or active status.
    """
    # Ensure users cannot change their role or active status
    user_data = user_in.model_dump(exclude_unset=True)
    if "role" in user_data:
        del user_data["role"]
    if "is_active" in user_data:
        del user_data["is_active"]
    
    # Update the user
    updated_user = user.update(db_obj=current_user, obj_in=user_data, db=db)
    return updated_user


@router.get("/search", response_model=Dict[str, Any])
async def search_users(
    query: str,
    skip: int = 0,
    limit: int = 100,
    current_user: User = Depends(get_current_admin),
    db: Session = Depends(get_db)
) -> Dict[str, Any]:
    """
    Search users by email or name.
    
    Only admins can search users. Regular admins can only search users
    from their own organization, while superusers can search all users.
    """
    if current_user.is_superuser:
        return user.search(query=query, db=db, skip=skip, limit=limit)
    else:
        # For regular admins, first get users from their organization
        org_users = user.get_by_organization(
            organization_id=current_user.organization_id, 
            db=db, 
            skip=0,
            limit=1000  # Large limit to get all organization users
        )
        
        # Then filter by the search query
        filtered_items = []
        for u in org_users["items"]:
            if (query.lower() in u.email.lower() or 
                (u.full_name and query.lower() in u.full_name.lower())):
                filtered_items.append(u)
        
        # Apply pagination
        start = skip
        end = skip + limit
        paginated_items = filtered_items[start:end] if start < len(filtered_items) else []
        
        # Create result with pagination info
        result = {
            "items": paginated_items,
            "total": len(filtered_items),
            "page": skip // limit + 1 if limit > 0 else 1,
            "size": limit,
            "pages": (len(filtered_items) + limit - 1) // limit if limit > 0 else 1
        }
        
        return result


@router.get("/organization/{organization_id}", response_model=Dict[str, Any])
async def get_users_by_organization(
    organization_id: UUID,
    skip: int = 0,
    limit: int = 100,
    current_user: User = Depends(get_organization_access),
    db: Session = Depends(get_db)
) -> Dict[str, Any]:
    """
    Get users belonging to a specific organization.
    
    Users must have access to the organization to view its users.
    """
    users_data = user.get_by_organization(
        organization_id=organization_id,
        db=db,
        skip=skip,
        limit=limit
    )
    
    return users_data


@router.get("/role/{role}", response_model=Dict[str, Any])
async def get_users_by_role(
    role: str,
    skip: int = 0,
    limit: int = 100,
    current_user: User = Depends(get_current_admin),
    db: Session = Depends(get_db)
) -> Dict[str, Any]:
    """
    Get users with a specific role.
    
    Only admins can filter users by role. Regular admins can only see users
    from their own organization, while superusers can see all users.
    """
    if current_user.is_superuser:
        return user.get_by_role(role=role, db=db, skip=skip, limit=limit)
    else:
        # For regular admins, first get users from their organization
        org_users = user.get_by_organization(
            organization_id=current_user.organization_id, 
            db=db, 
            skip=0,
            limit=1000  # Large limit to get all organization users
        )
        
        # Then filter by role
        filtered_items = []
        for u in org_users["items"]:
            if u.role == role:
                filtered_items.append(u)
        
        # Apply pagination
        start = skip
        end = skip + limit
        paginated_items = filtered_items[start:end] if start < len(filtered_items) else []
        
        # Create result with pagination info
        result = {
            "items": paginated_items,
            "total": len(filtered_items),
            "page": skip // limit + 1 if limit > 0 else 1,
            "size": limit,
            "pages": (len(filtered_items) + limit - 1) // limit if limit > 0 else 1
        }
        
        return result


@router.get("/{user_id}", response_model=User)
async def get_user(
    user_id: UUID,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
) -> User:
    """
    Get a specific user by ID.
    
    Users can only view themselves or users from their organization if they are admins.
    Superusers can view any user.
    """
    db_user = user.get(id=user_id, db=db)
    
    if not db_user:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="User not found"
        )
    
    # Check permissions: User can see themselves or admins can see users in their org
    if (current_user.id != user_id and 
        not current_user.is_superuser and 
        (not current_user.is_admin() or 
         current_user.organization_id != db_user.organization_id)):
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Not enough permissions to access this user"
        )
    
    return db_user


@router.get("/{user_id}/permissions", response_model=UserWithPermissions)
async def get_user_with_permissions(
    user_id: UUID,
    current_user: User = Depends(get_current_admin),
    db: Session = Depends(get_db)
) -> UserWithPermissions:
    """
    Get a user with their permissions.
    
    Only admins can view user permissions. Regular admins can only see 
    users from their own organization, while superusers can see any user.
    """
    db_user = user.get(id=user_id, db=db)
    
    if not db_user:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="User not found"
        )
    
    # Check permissions
    if (not current_user.is_superuser and 
        current_user.organization_id != db_user.organization_id):
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Not enough permissions to access this user"
        )
    
    # Get user permissions
    permissions = get_user_permissions(db_user, db)
    
    # Combine user data with permissions
    user_with_permissions = UserWithPermissions.model_validate({
        **db_user.to_dict(),
        "permissions": permissions
    })
    
    return user_with_permissions


@router.put("/{user_id}", response_model=User)
async def update_user(
    user_id: UUID,
    user_in: UserUpdate,
    current_user: User = Depends(get_current_admin),
    db: Session = Depends(get_db)
) -> User:
    """
    Update a user.
    
    Only admins can update users. Regular admins can only update users
    from their own organization, while superusers can update any user.
    """
    db_user = user.get(id=user_id, db=db)
    
    if not db_user:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="User not found"
        )
    
    # Check permissions
    if (not current_user.is_superuser and 
        current_user.organization_id != db_user.organization_id):
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Not enough permissions to update this user"
        )
    
    # Update the user
    updated_user = user.update(db_obj=db_user, obj_in=user_in, db=db)
    return updated_user


@router.delete("/{user_id}", response_model=ResponseMsg)
async def delete_user(
    user_id: UUID,
    current_user: User = Depends(get_current_superuser),
    db: Session = Depends(get_db)
) -> ResponseMsg:
    """
    Delete a user.
    
    Only superusers can delete users. A user cannot delete themselves.
    """
    if user_id == current_user.id:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Users cannot delete themselves"
        )
    
    db_user = user.get(id=user_id, db=db)
    
    if not db_user:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="User not found"
        )
    
    # Delete the user
    user.remove(id=user_id, db=db)
    
    return ResponseMsg(
        status="success",
        message=f"User successfully deleted"
    )