import pytest
import uuid
import random
import string

from ...app.crud.crud_user import user
from ...app.models.user import User
from ...app.schemas.user import UserCreate, UserUpdate
from ...app.constants.user_roles import (
    SYSTEM_ADMIN, PHARMA_ADMIN, PHARMA_SCIENTIST, CRO_ADMIN
)


def test_create_user(db_session):
    """Test creating a new user with the CRUD user service."""
    # Create a random email for testing
    email = ''.join(random.choice(string.ascii_lowercase) for _ in range(10)) + "@example.com"
    
    # Create a UserCreate object with test data
    user_in = UserCreate(
        email=email,
        full_name="Test User",
        password="StrongPass123!",
        organization_name="Test Org",
        organization_id=uuid.uuid4(),
        role=PHARMA_SCIENTIST
    )
    
    # Call user.create with the UserCreate object
    db_user = user.create(user_in, db=db_session)
    
    # Assert that the created user has the expected attributes
    assert db_user.email == email
    assert db_user.full_name == "Test User"
    assert db_user.organization_name == "Test Org"
    assert db_user.role == PHARMA_SCIENTIST
    
    # Assert that the password was properly hashed
    assert db_user.hashed_password != "StrongPass123!"
    assert db_user.check_password("StrongPass123!")
    
    # Verify the user exists in the database by email
    saved_user = user.get_by_email(email, db=db_session)
    assert saved_user is not None
    assert saved_user.id == db_user.id


def test_get_user_by_email(db_session, test_user):
    """Test retrieving a user by email."""
    # Get the test user's email
    email = test_user.email
    
    # Call user.get_by_email with the email
    db_user = user.get_by_email(email, db=db_session)
    
    # Assert that the retrieved user has the same ID as the test user
    assert db_user is not None
    assert db_user.id == test_user.id
    
    # Test case-insensitive email lookup
    upper_email = email.upper()
    if upper_email != email:  # Only test if the email has characters that can be uppercase
        case_insensitive_user = user.get_by_email(upper_email, db=db_session)
        assert case_insensitive_user is not None
        assert case_insensitive_user.id == test_user.id
    
    # Try to get a non-existent email
    non_existent_user = user.get_by_email("nonexistent@example.com", db=db_session)
    assert non_existent_user is None


def test_authenticate_user(db_session):
    """Test user authentication with email and password."""
    # Create a random email and password for testing
    email = ''.join(random.choice(string.ascii_lowercase) for _ in range(10)) + "@example.com"
    password = "StrongPass123!"
    
    # Create a UserCreate object with test data
    user_in = UserCreate(
        email=email,
        full_name="Auth Test User",
        password=password,
        role=PHARMA_SCIENTIST
    )
    db_user = user.create(user_in, db=db_session)
    
    # Authenticate with correct email and password
    authenticated_user = user.authenticate(email, password, db=db_session)
    assert authenticated_user is not None
    assert authenticated_user.id == db_user.id
    
    # Authenticate with correct email but wrong password
    wrong_auth_user = user.authenticate(email, "WrongPass123!", db=db_session)
    assert wrong_auth_user is None
    
    # Authenticate with non-existent email
    nonexistent_auth_user = user.authenticate("nonexistent@example.com", password, db=db_session)
    assert nonexistent_auth_user is None


def test_update_user(db_session, test_user):
    """Test updating user information."""
    # Create a UserUpdate object with new full name
    update_data = UserUpdate(full_name="Updated Name")
    
    # Call user.update with the test user and UserUpdate object
    updated_user = user.update(test_user, update_data, db=db_session)
    
    # Assert that the user's full name was updated
    assert updated_user.full_name == "Updated Name"
    
    # Create a UserUpdate object with new password
    new_password = "NewStrongPass123!"
    update_data = UserUpdate(password=new_password)
    
    # Call user.update with the test user and UserUpdate object
    updated_user = user.update(test_user, update_data, db=db_session)
    
    # Assert that the user's password was updated and hashed
    assert updated_user.check_password(new_password)
    
    # Update multiple fields simultaneously
    new_org_id = uuid.uuid4()
    update_data = UserUpdate(
        full_name="Multiple Updates",
        organization_name="New Org",
        organization_id=new_org_id,
        role=PHARMA_ADMIN
    )
    
    # Call user.update with the test user and UserUpdate object
    updated_user = user.update(test_user, update_data, db=db_session)
    
    # Assert all fields were updated correctly
    assert updated_user.full_name == "Multiple Updates"
    assert updated_user.organization_name == "New Org"
    assert updated_user.organization_id == new_org_id
    assert updated_user.role == PHARMA_ADMIN
    
    # Verify the user can authenticate with the new password
    authenticated_user = user.authenticate(test_user.email, new_password, db=db_session)
    assert authenticated_user is not None
    assert authenticated_user.id == test_user.id


def test_get_users_by_organization(db_session):
    """Test retrieving users by organization."""
    # Create a random organization ID
    org_id = uuid.uuid4()
    
    # Create multiple users with the same organization ID
    for i in range(5):
        user_in = UserCreate(
            email=f"orguser{i}_{random.randint(1000, 9999)}@example.com",
            full_name=f"Org User {i}",
            password="StrongPass123!",
            organization_id=org_id,
            role=PHARMA_SCIENTIST
        )
        user.create(user_in, db=db_session)
    
    # Create users with different organization IDs
    different_org_id = uuid.uuid4()
    for i in range(3):
        user_in = UserCreate(
            email=f"difforguser{i}_{random.randint(1000, 9999)}@example.com",
            full_name=f"Different Org User {i}",
            password="StrongPass123!",
            organization_id=different_org_id,
            role=PHARMA_SCIENTIST
        )
        user.create(user_in, db=db_session)
    
    # Call user.get_by_organization with the organization ID
    result = user.get_by_organization(org_id, db=db_session)
    
    # Assert that only users from the specified organization are returned
    assert result["total"] == 5
    assert len(result["items"]) == 5
    for user_item in result["items"]:
        assert user_item.organization_id == org_id
    
    # Verify pagination works correctly
    paged_result = user.get_by_organization(org_id, db=db_session, skip=2, limit=2)
    assert paged_result["total"] == 5
    assert len(paged_result["items"]) == 2
    assert paged_result["page"] == 2
    assert paged_result["pages"] == 3


def test_search_users(db_session):
    """Test searching users by email or name."""
    # Create users with specific email patterns and names
    base_email = "searchtest"
    for i in range(5):
        user_in = UserCreate(
            email=f"{base_email}{i}@example.com",
            full_name=f"Search Test User {i}",
            password="StrongPass123!",
            role=PHARMA_SCIENTIST
        )
        user.create(user_in, db=db_session)
    
    # Create users with different positions of search term
    user.create(UserCreate(
        email="prefix_searchterm@example.com",
        full_name="Prefix Search Name",
        password="StrongPass123!",
        role=PHARMA_SCIENTIST
    ), db=db_session)
    
    user.create(UserCreate(
        email="middle_searchterm_suffix@example.com",
        full_name="Middle Search Term Name",
        password="StrongPass123!",
        role=PHARMA_SCIENTIST
    ), db=db_session)
    
    user.create(UserCreate(
        email="suffix_searchterm@example.com",
        full_name="Suffix Search Name",
        password="StrongPass123!",
        role=PHARMA_SCIENTIST
    ), db=db_session)
    
    # Create users with different email patterns
    for i in range(3):
        user_in = UserCreate(
            email=f"different{i}@example.com",
            full_name=f"Different User {i}",
            password="StrongPass123!",
            role=PHARMA_SCIENTIST
        )
        user.create(user_in, db=db_session)
    
    # Search for users with a partial email match
    email_search_result = user.search("searchtest", db=db_session)
    assert email_search_result["total"] == 5
    assert len(email_search_result["items"]) == 5
    
    # Search for users with a partial name match
    name_search_result = user.search("Search Test", db=db_session)
    assert name_search_result["total"] == 5
    assert len(name_search_result["items"]) == 5
    
    # Search partial term at beginning
    prefix_result = user.search("prefix", db=db_session)
    assert prefix_result["total"] == 1
    assert prefix_result["items"][0].email == "prefix_searchterm@example.com"
    
    # Search partial term in middle
    middle_result = user.search("middle", db=db_session)
    assert middle_result["total"] == 1
    assert middle_result["items"][0].email == "middle_searchterm_suffix@example.com"
    
    # Search partial term at end
    suffix_result = user.search("suffix", db=db_session)
    assert suffix_result["total"] == 1
    
    # Verify pagination works correctly
    paged_result = user.search("searchtest", db=db_session, skip=2, limit=2)
    assert paged_result["total"] == 5
    assert len(paged_result["items"]) == 2
    assert paged_result["page"] == 2
    assert paged_result["pages"] == 3
    
    # Search with a non-matching query
    no_match_result = user.search("nonexistent", db=db_session)
    assert no_match_result["total"] == 0
    assert len(no_match_result["items"]) == 0


def test_get_users_by_role(db_session):
    """Test retrieving users by role."""
    # Create users with different roles (SYSTEM_ADMIN, PHARMA_ADMIN, PHARMA_SCIENTIST, CRO_ADMIN)
    role_counts = {
        SYSTEM_ADMIN: 2,
        PHARMA_ADMIN: 3,
        PHARMA_SCIENTIST: 5,
        CRO_ADMIN: 2
    }
    
    for role, count in role_counts.items():
        for i in range(count):
            user_in = UserCreate(
                email=f"{role.lower()}{i}_{random.randint(1000, 9999)}@example.com",
                full_name=f"{role} User {i}",
                password="StrongPass123!",
                role=role
            )
            user.create(user_in, db=db_session)
    
    # Call user.get_by_role with each role
    for role, count in role_counts.items():
        result = user.get_by_role(role, db=db_session)
        assert result["total"] == count
        assert len(result["items"]) == count
        for user_item in result["items"]:
            assert user_item.role == role
    
    # Verify pagination works correctly
    paged_result = user.get_by_role(PHARMA_SCIENTIST, db=db_session, skip=2, limit=2)
    assert paged_result["total"] == 5
    assert len(paged_result["items"]) == 2
    assert paged_result["page"] == 2
    assert paged_result["pages"] == 3
    
    # Call with a non-existent role
    non_existent_role_result = user.get_by_role("non_existent_role", db=db_session)
    assert non_existent_role_result["total"] == 0
    assert len(non_existent_role_result["items"]) == 0


def test_is_active_superuser(db_session):
    """Test checking if a user is active and/or a superuser."""
    # Create a regular active user
    regular_user_in = UserCreate(
        email=f"regular_{random.randint(1000, 9999)}@example.com",
        full_name="Regular User",
        password="StrongPass123!",
        role=PHARMA_SCIENTIST,
    )
    regular_user = user.create(regular_user_in, db=db_session)
    
    # Assert that user.is_active returns True
    assert user.is_active(regular_user) is True
    
    # Assert that user.is_superuser returns False
    assert user.is_superuser(regular_user) is False
    
    # Create a superuser
    superuser_in = UserCreate(
        email=f"super_{random.randint(1000, 9999)}@example.com",
        full_name="Superuser",
        password="StrongPass123!",
        role=SYSTEM_ADMIN
    )
    superuser = user.create(superuser_in, db=db_session)
    superuser.is_superuser = True
    db_session.add(superuser)
    db_session.commit()
    db_session.refresh(superuser)
    
    # Assert that user.is_active returns True
    assert user.is_active(superuser) is True
    
    # Assert that user.is_superuser returns True
    assert user.is_superuser(superuser) is True
    
    # Create an inactive user
    inactive_user_in = UserCreate(
        email=f"inactive_{random.randint(1000, 9999)}@example.com",
        full_name="Inactive User",
        password="StrongPass123!",
        role=PHARMA_SCIENTIST,
    )
    inactive_user = user.create(inactive_user_in, db=db_session)
    inactive_user.is_active = False
    db_session.add(inactive_user)
    db_session.commit()
    db_session.refresh(inactive_user)
    
    # Assert that user.is_active returns False
    assert user.is_active(inactive_user) is False