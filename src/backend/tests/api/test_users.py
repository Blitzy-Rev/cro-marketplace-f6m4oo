# src/backend/tests/api/test_users.py

import pytest
import uuid
import json
from typing import Dict, Any

from fastapi import FastAPI, Request, Response, Depends, HTTPException, status
from starlette.status import HTTP_200_OK, HTTP_201_CREATED, HTTP_400_BAD_REQUEST, HTTP_401_UNAUTHORIZED, HTTP_403_FORBIDDEN, HTTP_404_NOT_FOUND, HTTP_422_UNPROCESSABLE_ENTITY

from src.backend.tests.conftest import client, db_session, admin_token_headers, pharma_token_headers, cro_token_headers, test_user, test_admin_user, create_test_user, User
from src.backend.app.schemas.user import UserCreate, UserUpdate
from src.backend.app.constants.user_roles import SYSTEM_ADMIN, PHARMA_ADMIN, PHARMA_SCIENTIST, CRO_ADMIN, CRO_TECHNICIAN

@pytest.mark.parametrize('skip,limit', [(0, 10), (0, 100), (10, 10)])
def test_get_users_admin(client, admin_token_headers):
    """Test that admin users can retrieve all users"""
    # Send GET request to /api/v1/users/ with admin token headers and skip/limit parameters
    response = client.get("/api/v1/users/", headers=admin_token_headers, params={"skip": skip, "limit": limit})
    
    # Assert response status code is 200
    assert response.status_code == HTTP_200_OK
    
    # Parse response JSON
    data = response.json()
    
    # Assert response contains 'items', 'total', 'page', 'size' keys
    assert "items" in data
    assert "total" in data
    assert "page" in data
    assert "size" in data
    
    # Assert 'items' is a list
    assert isinstance(data["items"], list)
    
    # Assert 'total' is an integer
    assert isinstance(data["total"], int)
    
    # Assert length of 'items' is less than or equal to limit
    assert len(data["items"]) <= limit

def test_get_users_pharma_admin(client, pharma_token_headers, db_session):
    """Test that pharma admin users can only retrieve users from their organization"""
    # Create test users from different organizations
    org_id = uuid.uuid4()
    create_test_user(db_session, "same_org@example.com", "password", "Same Org User", PHARMA_SCIENTIST)
    create_test_user(db_session, "diff_org@example.com", "password", "Diff Org User", PHARMA_SCIENTIST)
    db_session.commit()
    
    # Send GET request to /api/v1/users/ with pharma admin token headers
    response = client.get("/api/v1/users/", headers=pharma_token_headers)
    
    # Assert response status code is 200
    assert response.status_code == HTTP_200_OK
    
    # Parse response JSON
    data = response.json()
    
    # Assert all returned users belong to the pharma admin's organization
    for user in data["items"]:
        assert user["organization_id"] == org_id

def test_get_users_unauthorized(client):
    """Test that non-admin users cannot retrieve user lists"""
    # Send GET request to /api/v1/users/ without token headers
    response = client.get("/api/v1/users/")
    
    # Assert response status code is 401 (Unauthorized)
    assert response.status_code == HTTP_401_UNAUTHORIZED

def test_create_user_admin(client, admin_token_headers):
    """Test that admin users can create new users"""
    # Create user data with unique email
    user_data = {
        "email": f"new_user_{uuid.uuid4()}@example.com",
        "password": "password123!",
        "full_name": "New Test User",
        "role": PHARMA_SCIENTIST
    }
    
    # Send POST request to /api/v1/users/ with admin token headers and user data
    response = client.post("/api/v1/users/", headers=admin_token_headers, json=user_data)
    
    # Assert response status code is 201 (Created)
    assert response.status_code == HTTP_201_CREATED
    
    # Parse response JSON
    data = response.json()
    
    # Assert response contains expected user data
    assert data["email"] == user_data["email"]
    assert data["full_name"] == user_data["full_name"]
    assert data["role"] == user_data["role"]
    
    # Assert user ID is a valid UUID
    assert uuid.UUID(data["id"])

def test_create_user_duplicate_email(client, admin_token_headers, test_user):
    """Test that creating a user with an existing email fails"""
    # Create user data with the same email as test_user
    user_data = {
        "email": test_user.email,
        "password": "password123!",
        "full_name": "New Test User",
        "role": PHARMA_SCIENTIST
    }
    
    # Send POST request to /api/v1/users/ with admin token headers and user data
    response = client.post("/api/v1/users/", headers=admin_token_headers, json=user_data)
    
    # Assert response status code is 400 (Bad Request)
    assert response.status_code == HTTP_400_BAD_REQUEST
    
    # Parse response JSON
    data = response.json()
    
    # Assert response contains error message about duplicate email
    assert "A user with this email already exists" in data["detail"]

def test_create_user_pharma_admin(client, pharma_token_headers):
    """Test that pharma admin users can create users in their organization"""
    # Create user data with unique email and pharma scientist role
    user_data = {
        "email": f"new_user_{uuid.uuid4()}@example.com",
        "password": "password123!",
        "full_name": "New Test User",
        "role": PHARMA_SCIENTIST
    }
    
    # Send POST request to /api/v1/users/ with pharma admin token headers and user data
    response = client.post("/api/v1/users/", headers=pharma_token_headers, json=user_data)
    
    # Assert response status code is 201 (Created)
    assert response.status_code == HTTP_201_CREATED
    
    # Parse response JSON
    data = response.json()
    
    # Assert response contains expected user data
    assert data["email"] == user_data["email"]
    assert data["full_name"] == user_data["full_name"]
    assert data["role"] == user_data["role"]
    
    # Assert user has the same organization_id as the pharma admin
    # TODO: Implement organization_id check

@pytest.mark.parametrize('role', [SYSTEM_ADMIN, CRO_ADMIN, CRO_TECHNICIAN])
def test_create_user_unauthorized_role(client, pharma_token_headers, role):
    """Test that pharma admin cannot create users with unauthorized roles"""
    # Create user data with unique email and unauthorized role
    user_data = {
        "email": f"new_user_{uuid.uuid4()}@example.com",
        "password": "password123!",
        "full_name": "New Test User",
        "role": role
    }
    
    # Send POST request to /api/v1/users/ with pharma admin token headers and user data
    response = client.post("/api/v1/users/", headers=pharma_token_headers, json=user_data)
    
    # Assert response status code is 403 (Forbidden)
    assert response.status_code == HTTP_403_FORBIDDEN
    
    # Parse response JSON
    data = response.json()
    
    # Assert response contains error message about unauthorized role
    assert "You do not have permission to perform this action" in data["detail"]

def test_get_user_by_id(client, admin_token_headers, test_user):
    """Test retrieving a specific user by ID"""
    # Send GET request to /api/v1/users/{test_user.id} with admin token headers
    response = client.get(f"/api/v1/users/{test_user.id}", headers=admin_token_headers)
    
    # Assert response status code is 200
    assert response.status_code == HTTP_200_OK
    
    # Parse response JSON
    data = response.json()
    
    # Assert response contains expected user data
    assert data["email"] == test_user.email
    assert data["full_name"] == test_user.full_name
    
    # Assert user ID matches test_user.id
    assert data["id"] == str(test_user.id)

def test_get_user_not_found(client, admin_token_headers):
    """Test retrieving a non-existent user returns 404"""
    # Generate a random UUID for a non-existent user
    random_uuid = uuid.uuid4()
    
    # Send GET request to /api/v1/users/{random_uuid} with admin token headers
    response = client.get(f"/api/v1/users/{random_uuid}", headers=admin_token_headers)
    
    # Assert response status code is 404 (Not Found)
    assert response.status_code == HTTP_404_NOT_FOUND

def test_get_user_different_organization(client, pharma_token_headers, db_session):
    """Test that pharma admin cannot retrieve users from different organizations"""
    # Create a test user from a different organization
    different_org_user = create_test_user(db_session, "different_org@example.com", "password", "Different Org User", PHARMA_SCIENTIST)
    db_session.commit()
    
    # Send GET request to /api/v1/users/{different_org_user.id} with pharma admin token headers
    response = client.get(f"/api/v1/users/{different_org_user.id}", headers=pharma_token_headers)
    
    # Assert response status code is 403 (Forbidden)
    assert response.status_code == HTTP_403_FORBIDDEN

def test_update_user(client, admin_token_headers, test_user):
    """Test updating a user's information"""
    # Create update data with new full_name and role
    update_data = {
        "full_name": "Updated Test User",
        "role": PHARMA_ADMIN
    }
    
    # Send PUT request to /api/v1/users/{test_user.id} with admin token headers and update data
    response = client.put(f"/api/v1/users/{test_user.id}", headers=admin_token_headers, json=update_data)
    
    # Assert response status code is 200
    assert response.status_code == HTTP_200_OK
    
    # Parse response JSON
    data = response.json()
    
    # Assert response contains updated user data
    assert data["full_name"] == update_data["full_name"]
    assert data["role"] == update_data["role"]

def test_update_user_email_conflict(client, admin_token_headers, test_user, test_admin_user):
    """Test that updating a user's email to an existing email fails"""
    # Create update data with test_admin's email
    update_data = {
        "email": test_admin_user.email
    }
    
    # Send PUT request to /api/v1/users/{test_user.id} with admin token headers and update data
    response = client.put(f"/api/v1/users/{test_user.id}", headers=admin_token_headers, json=update_data)
    
    # Assert response status code is 400 (Bad Request)
    assert response.status_code == HTTP_400_BAD_REQUEST
    
    # Parse response JSON
    data = response.json()
    
    # Assert response contains error message about duplicate email
    assert "A user with this email already exists" in data["detail"]

def test_update_user_pharma_admin(client, pharma_token_headers, db_session):
    """Test that pharma admin can update users in their organization"""
    # Create a test user in the same organization as pharma admin
    same_org_user = create_test_user(db_session, "same_org_update@example.com", "password", "Same Org User", PHARMA_SCIENTIST)
    db_session.commit()
    
    # Create update data with new full_name
    update_data = {
        "full_name": "Updated Same Org User"
    }
    
    # Send PUT request to /api/v1/users/{same_org_user.id} with pharma admin token headers and update data
    response = client.put(f"/api/v1/users/{same_org_user.id}", headers=pharma_token_headers, json=update_data)
    
    # Assert response status code is 200
    assert response.status_code == HTTP_200_OK
    
    # Parse response JSON
    data = response.json()
    
    # Assert response contains updated user data
    assert data["full_name"] == update_data["full_name"]

@pytest.mark.parametrize('role', [SYSTEM_ADMIN, CRO_ADMIN, CRO_TECHNICIAN])
def test_update_user_unauthorized_role(client, pharma_token_headers, db_session, role):
    """Test that pharma admin cannot update users to unauthorized roles"""
    # Create a test user in the same organization as pharma admin
    same_org_user = create_test_user(db_session, "same_org_update_role@example.com", "password", "Same Org User", PHARMA_SCIENTIST)
    db_session.commit()
    
    # Create update data with unauthorized role
    update_data = {
        "role": role
    }
    
    # Send PUT request to /api/v1/users/{same_org_user.id} with pharma admin token headers and update data
    response = client.put(f"/api/v1/users/{same_org_user.id}", headers=pharma_token_headers, json=update_data)
    
    # Assert response status code is 403 (Forbidden)
    assert response.status_code == HTTP_403_FORBIDDEN
    
    # Parse response JSON
    data = response.json()
    
    # Assert response contains error message about unauthorized role
    assert "You do not have permission to perform this action" in data["detail"]

def test_delete_user(client, admin_token_headers, db_session):
    """Test deleting a user"""
    # Create a test user to be deleted
    user_to_delete = create_test_user(db_session, "delete_user@example.com", "password", "User To Delete", PHARMA_SCIENTIST)
    db_session.commit()
    
    # Send DELETE request to /api/v1/users/{user_to_delete.id} with admin token headers
    response = client.delete(f"/api/v1/users/{user_to_delete.id}", headers=admin_token_headers)
    
    # Assert response status code is 200
    assert response.status_code == HTTP_200_OK
    
    # Parse response JSON
    data = response.json()
    
    # Assert response contains success message
    assert data["message"] == "User successfully deleted"
    
    # Verify user no longer exists in database
    deleted_user = db_session.query(User).filter(User.id == user_to_delete.id).first()
    assert deleted_user is None

def test_delete_user_not_found(client, admin_token_headers):
    """Test deleting a non-existent user returns 404"""
    # Generate a random UUID for a non-existent user
    random_uuid = uuid.uuid4()
    
    # Send DELETE request to /api/v1/users/{random_uuid} with admin token headers
    response = client.delete(f"/api/v1/users/{random_uuid}", headers=admin_token_headers)
    
    # Assert response status code is 404 (Not Found)
    assert response.status_code == HTTP_404_NOT_FOUND

def test_delete_self(client, admin_token_headers, test_admin_user):
    """Test that a user cannot delete themselves"""
    # Send DELETE request to /api/v1/users/{test_admin.id} with admin token headers
    response = client.delete(f"/api/v1/users/{test_admin_user.id}", headers=admin_token_headers)
    
    # Assert response status code is 400 (Bad Request)
    assert response.status_code == HTTP_400_BAD_REQUEST
    
    # Parse response JSON
    data = response.json()
    
    # Assert response contains error message about deleting self
    assert "Users cannot delete themselves" in data["detail"]

def test_delete_user_unauthorized(client, pharma_token_headers, test_user):
    """Test that only superusers can delete users"""
    # Send DELETE request to /api/v1/users/{test_user.id} with pharma admin token headers
    response = client.delete(f"/api/v1/users/{test_user.id}", headers=pharma_token_headers)
    
    # Assert response status code is 403 (Forbidden)
    assert response.status_code == HTTP_403_FORBIDDEN

def test_get_me(client, admin_token_headers, test_admin_user):
    """Test retrieving current user information"""
    # Send GET request to /api/v1/users/me with admin token headers
    response = client.get("/api/v1/users/me", headers=admin_token_headers)
    
    # Assert response status code is 200
    assert response.status_code == HTTP_200_OK
    
    # Parse response JSON
    data = response.json()
    
    # Assert response contains expected user data
    assert data["email"] == test_admin_user.email
    assert data["full_name"] == test_admin_user.full_name
    
    # Assert user ID matches test_admin.id
    assert data["id"] == str(test_admin_user.id)

def test_get_my_permissions(client, admin_token_headers):
    """Test retrieving current user permissions"""
    # Send GET request to /api/v1/users/me/permissions with admin token headers
    response = client.get("/api/v1/users/me/permissions", headers=admin_token_headers)
    
    # Assert response status code is 200
    assert response.status_code == HTTP_200_OK
    
    # Parse response JSON
    data = response.json()
    
    # Assert response contains 'permissions' key
    assert "permissions" in data
    
    # Assert permissions is a dictionary with expected structure
    assert isinstance(data["permissions"], dict)

def test_update_me(client, admin_token_headers):
    """Test updating current user information"""
    # Create update data with new full_name and password
    update_data = {
        "full_name": "Updated Admin Name",
        "password": "new_password123!"
    }
    
    # Send PUT request to /api/v1/users/me with admin token headers and update data
    response = client.put("/api/v1/users/me", headers=admin_token_headers, json=update_data)
    
    # Assert response status code is 200
    assert response.status_code == HTTP_200_OK
    
    # Parse response JSON
    data = response.json()
    
    # Assert response contains updated user data
    assert data["full_name"] == update_data["full_name"]

def test_update_me_role_ignored(client, pharma_token_headers):
    """Test that updating current user's role is ignored"""
    # Create update data with new role (SYSTEM_ADMIN)
    update_data = {
        "role": SYSTEM_ADMIN
    }
    
    # Send PUT request to /api/v1/users/me with pharma admin token headers and update data
    response = client.put("/api/v1/users/me", headers=pharma_token_headers, json=update_data)
    
    # Assert response status code is 200
    assert response.status_code == HTTP_200_OK
    
    # Parse response JSON
    data = response.json()
    
    # Assert response contains user data with original role (not changed)
    assert data["role"] != update_data["role"]

def test_search_users(client, admin_token_headers, db_session):
    """Test searching users by email or name"""
    # Create multiple test users with distinct names and emails
    create_test_user(db_session, "search_test1@example.com", "password", "Search Test User 1", PHARMA_SCIENTIST)
    create_test_user(db_session, "search_test2@example.com", "password", "Another Search User", PHARMA_SCIENTIST)
    db_session.commit()
    
    # Define search term
    search_term = "search"
    
    # Send GET request to /api/v1/users/search?query={search_term} with admin token headers
    response = client.get(f"/api/v1/users/search?query={search_term}", headers=admin_token_headers)
    
    # Assert response status code is 200
    assert response.status_code == HTTP_200_OK
    
    # Parse response JSON
    data = response.json()
    
    # Assert response contains matching users
    for user in data["items"]:
        assert search_term.lower() in user["email"].lower() or search_term.lower() in user["full_name"].lower()
    
    # Assert non-matching users are not included
    for user in data["items"]:
        assert "search_test3@example.com" not in user["email"]
        assert "Non Matching User" not in user["full_name"]

def test_get_users_by_organization(client, admin_token_headers, db_session):
    """Test retrieving users by organization"""
    # Create test users in different organizations
    org_id = uuid.uuid4()
    create_test_user(db_session, "org_test1@example.com", "password", "Org Test User 1", PHARMA_SCIENTIST)
    create_test_user(db_session, "org_test2@example.com", "password", "Another Org User", PHARMA_SCIENTIST)
    db_session.commit()
    
    # Send GET request to /api/v1/users/organization/{organization_id} with admin token headers
    response = client.get(f"/api/v1/users/organization/{org_id}", headers=admin_token_headers)
    
    # Assert response status code is 200
    assert response.status_code == HTTP_200_OK
    
    # Parse response JSON
    data = response.json()
    
    # Assert all returned users belong to the specified organization
    for user in data["items"]:
        assert user["organization_id"] == org_id
    
    # Assert users from other organizations are not included
    for user in data["items"]:
        assert "other_org@example.com" not in user["email"]

@pytest.mark.parametrize('role', [SYSTEM_ADMIN, PHARMA_ADMIN, PHARMA_SCIENTIST, CRO_ADMIN, CRO_TECHNICIAN])
def test_get_users_by_role(client, admin_token_headers, db_session, role):
    """Test retrieving users by role"""
    # Create test users with different roles
    create_test_user(db_session, "role_test1@example.com", "password", "Role Test User 1", role)
    create_test_user(db_session, "role_test2@example.com", "password", "Another Role User", PHARMA_SCIENTIST)
    db_session.commit()
    
    # Send GET request to /api/v1/users/role/{role} with admin token headers
    response = client.get(f"/api/v1/users/role/{role}", headers=admin_token_headers)
    
    # Assert response status code is 200
    assert response.status_code == HTTP_200_OK
    
    # Parse response JSON
    data = response.json()
    
    # Assert all returned users have the specified role
    for user in data["items"]:
        assert user["role"] == role
    
    # Assert users with other roles are not included
    for user in data["items"]:
        assert "other_role@example.com" not in user["email"]