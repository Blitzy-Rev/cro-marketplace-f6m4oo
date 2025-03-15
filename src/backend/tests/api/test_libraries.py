import pytest
from fastapi import status
import uuid
import json
import random
from typing import List

from ..conftest import client, db_session, admin_token_headers, pharma_token_headers, test_user, test_molecule, test_molecules
from ...app.models.library import Library
from ...app.crud.crud_library import library


def test_create_library(client, pharma_token_headers):
    """Test creating a new library via the API"""
    # Create library data dictionary with name and description
    library_data = {"name": "Test Library", "description": "A test library"}
    # Send POST request to /api/v1/libraries/ with library data and authentication headers
    response = client.post("/api/v1/libraries/", json=library_data, headers=pharma_token_headers)
    # Assert response status code is 201 CREATED
    assert response.status_code == status.HTTP_201_CREATED
    # Assert response JSON contains expected library data
    response_json = response.json()
    assert "id" in response_json
    # Assert library ID is a valid UUID
    try:
        uuid.UUID(response_json["id"])
    except ValueError:
        assert False, "Library ID is not a valid UUID"
    # Assert library name matches input data
    assert response_json["name"] == library_data["name"]
    # Assert library description matches input data
    assert response_json["description"] == library_data["description"]


def test_create_library_invalid_data(client, pharma_token_headers):
    """Test creating a library with invalid data"""
    # Create invalid library data (empty name)
    invalid_library_data = {"name": "", "description": "Invalid library"}
    # Send POST request to /api/v1/libraries/ with invalid data and authentication headers
    response = client.post("/api/v1/libraries/", json=invalid_library_data, headers=pharma_token_headers)
    # Assert response status code is 422 UNPROCESSABLE ENTITY
    assert response.status_code == status.HTTP_422_UNPROCESSABLE_ENTITY
    # Assert response contains validation error details
    assert "detail" in response.json()


def test_create_library_unauthorized(client):
    """Test creating a library without authentication"""
    # Create valid library data
    library_data = {"name": "Unauthorized Library", "description": "An unauthorized library"}
    # Send POST request to /api/v1/libraries/ without authentication headers
    response = client.post("/api/v1/libraries/", json=library_data)
    # Assert response status code is 401 UNAUTHORIZED
    assert response.status_code == status.HTTP_401_UNAUTHORIZED


def test_get_library(client, pharma_token_headers, db_session, test_user):
    """Test retrieving a library by ID"""
    # Create a test library in the database
    library_data = {"name": "Get Library", "description": "Library to get"}
    created_library = library.create_with_owner(library_data, test_user.id, db=db_session)
    # Send GET request to /api/v1/libraries/{library_id} with authentication headers
    response = client.get(f"/api/v1/libraries/{created_library.id}", headers=pharma_token_headers)
    # Assert response status code is 200 OK
    assert response.status_code == status.HTTP_200_OK
    # Assert response JSON contains expected library data
    response_json = response.json()
    assert response_json["id"] == str(created_library.id)
    # Assert library ID matches the created library
    assert response_json["name"] == library_data["name"]
    # Assert library name and description match expected values
    assert response_json["description"] == library_data["description"]


def test_get_library_not_found(client, pharma_token_headers):
    """Test retrieving a non-existent library"""
    # Generate a random UUID for a non-existent library
    random_uuid = uuid.uuid4()
    # Send GET request to /api/v1/libraries/{random_uuid} with authentication headers
    response = client.get(f"/api/v1/libraries/{random_uuid}", headers=pharma_token_headers)
    # Assert response status code is 404 NOT FOUND
    assert response.status_code == status.HTTP_404_NOT_FOUND
    # Assert response contains appropriate error message
    assert "detail" in response.json()


def test_get_libraries(client, pharma_token_headers, db_session, test_user):
    """Test retrieving all accessible libraries"""
    # Create multiple test libraries in the database
    library_data1 = {"name": "Library 1", "description": "First library"}
    library.create_with_owner(library_data1, test_user.id, db=db_session)
    library_data2 = {"name": "Library 2", "description": "Second library"}
    library.create_with_owner(library_data2, test_user.id, db=db_session)
    # Send GET request to /api/v1/libraries/ with authentication headers
    response = client.get("/api/v1/libraries/", headers=pharma_token_headers)
    # Assert response status code is 200 OK
    assert response.status_code == status.HTTP_200_OK
    # Assert response contains items array
    response_json = response.json()
    assert "items" in response_json
    # Assert total count matches expected number of libraries
    assert response_json["total"] == 2
    # Assert response contains pagination information
    assert "page" in response_json
    assert "size" in response_json
    assert "pages" in response_json


def test_update_library(client, pharma_token_headers, db_session, test_user):
    """Test updating a library"""
    # Create a test library in the database
    library_data = {"name": "Original Library", "description": "Original description"}
    created_library = library.create_with_owner(library_data, test_user.id, db=db_session)
    # Create update data with new name and description
    update_data = {"name": "Updated Library", "description": "Updated description"}
    # Send PUT request to /api/v1/libraries/{library_id} with update data and authentication headers
    response = client.put(f"/api/v1/libraries/{created_library.id}", json=update_data, headers=pharma_token_headers)
    # Assert response status code is 200 OK
    assert response.status_code == status.HTTP_200_OK
    # Assert response JSON contains updated library data
    response_json = response.json()
    assert response_json["name"] == update_data["name"]
    # Assert library name and description match the updated values
    assert response_json["description"] == update_data["description"]


def test_update_library_not_found(client, pharma_token_headers):
    """Test updating a non-existent library"""
    # Generate a random UUID for a non-existent library
    random_uuid = uuid.uuid4()
    # Create valid update data
    update_data = {"name": "Updated Library", "description": "Updated description"}
    # Send PUT request to /api/v1/libraries/{random_uuid} with update data and authentication headers
    response = client.put(f"/api/v1/libraries/{random_uuid}", json=update_data, headers=pharma_token_headers)
    # Assert response status code is 404 NOT FOUND
    assert response.status_code == status.HTTP_404_NOT_FOUND
    # Assert response contains appropriate error message
    assert "detail" in response.json()


def test_update_library_unauthorized(client, pharma_token_headers, admin_token_headers, db_session, test_user):
    """Test updating a library without proper authorization"""
    # Create a test library owned by test_user
    library_data = {"name": "Unauthorized Library", "description": "Unauthorized description"}
    created_library = library.create_with_owner(library_data, test_user.id, db=db_session)
    # Create valid update data
    update_data = {"name": "Updated Library", "description": "Updated description"}
    # Send PUT request to /api/v1/libraries/{library_id} with admin_token_headers (different user)
    response = client.put(f"/api/v1/libraries/{created_library.id}", json=update_data, headers=admin_token_headers)
    # Assert response status code is 403 FORBIDDEN
    assert response.status_code == status.HTTP_403_FORBIDDEN
    # Assert response contains appropriate error message
    assert "detail" in response.json()


def test_delete_library(client, pharma_token_headers, db_session, test_user):
    """Test deleting a library"""
    # Create a test library in the database
    library_data = {"name": "Delete Library", "description": "Library to delete"}
    created_library = library.create_with_owner(library_data, test_user.id, db=db_session)
    # Send DELETE request to /api/v1/libraries/{library_id} with authentication headers
    response = client.delete(f"/api/v1/libraries/{created_library.id}", headers=pharma_token_headers)
    # Assert response status code is 200 OK
    assert response.status_code == status.HTTP_200_OK
    # Assert response contains success message
    assert "message" in response.json()
    # Verify library no longer exists in database
    deleted_library = library.get(created_library.id, db=db_session)
    assert deleted_library is None


def test_delete_library_not_found(client, pharma_token_headers):
    """Test deleting a non-existent library"""
    # Generate a random UUID for a non-existent library
    random_uuid = uuid.uuid4()
    # Send DELETE request to /api/v1/libraries/{random_uuid} with authentication headers
    response = client.delete(f"/api/v1/libraries/{random_uuid}", headers=pharma_token_headers)
    # Assert response status code is 404 NOT FOUND
    assert response.status_code == status.HTTP_404_NOT_FOUND
    # Assert response contains appropriate error message
    assert "detail" in response.json()


def test_get_library_with_molecules(client, pharma_token_headers, db_session, test_user, test_molecules):
    """Test retrieving a library with its molecules"""
    # Create a test library in the database
    library_data = {"name": "Molecule Library", "description": "Library with molecules"}
    created_library = library.create_with_owner(library_data, test_user.id, db=db_session)
    # Add test molecules to the library
    created_library.molecules.extend(test_molecules)
    db_session.commit()
    # Send GET request to /api/v1/libraries/{library_id}/molecules with authentication headers
    response = client.get(f"/api/v1/libraries/{created_library.id}/molecules", headers=pharma_token_headers)
    # Assert response status code is 200 OK
    assert response.status_code == status.HTTP_200_OK
    # Assert response contains library data
    response_json = response.json()
    assert "library" in response_json
    # Assert response contains molecules array
    assert "molecules" in response_json
    # Assert molecules count matches expected number
    assert len(response_json["molecules"]) == len(test_molecules)
    # Assert molecule data contains expected properties
    for molecule in response_json["molecules"]:
        assert "id" in molecule
        assert "smiles" in molecule


def test_add_molecules_to_library(client, pharma_token_headers, db_session, test_user, test_molecules):
    """Test adding molecules to a library"""
    # Create a test library in the database
    library_data = {"name": "Add Molecules", "description": "Library to add molecules to"}
    created_library = library.create_with_owner(library_data, test_user.id, db=db_session)
    # Create request data with library_id, molecule_ids, and operation='add'
    molecule_ids = [str(molecule.id) for molecule in test_molecules]
    request_data = {"library_id": str(created_library.id), "molecule_ids": molecule_ids, "operation": "add"}
    # Send POST request to /api/v1/libraries/molecules/add with request data and authentication headers
    response = client.post("/api/v1/libraries/molecules/add", json=request_data, headers=pharma_token_headers)
    # Assert response status code is 200 OK
    assert response.status_code == status.HTTP_200_OK
    # Assert response contains success counts
    response_json = response.json()
    assert "added" in response_json
    # Assert added count matches expected number
    assert response_json["added"] == len(test_molecules)
    # Verify molecules are now associated with the library in the database
    updated_library = library.get(created_library.id, db=db_session)
    assert len(updated_library.molecules) == len(test_molecules)


def test_remove_molecules_from_library(client, pharma_token_headers, db_session, test_user, test_molecules):
    """Test removing molecules from a library"""
    # Create a test library in the database
    library_data = {"name": "Remove Molecules", "description": "Library to remove molecules from"}
    created_library = library.create_with_owner(library_data, test_user.id, db=db_session)
    # Add test molecules to the library
    created_library.molecules.extend(test_molecules)
    db_session.commit()
    # Create request data with library_id, molecule_ids, and operation='remove'
    molecule_ids = [str(molecule.id) for molecule in test_molecules]
    request_data = {"library_id": str(created_library.id), "molecule_ids": molecule_ids, "operation": "remove"}
    # Send POST request to /api/v1/libraries/molecules/remove with request data and authentication headers
    response = client.post("/api/v1/libraries/molecules/remove", json=request_data, headers=pharma_token_headers)
    # Assert response status code is 200 OK
    assert response.status_code == status.HTTP_200_OK
    # Assert response contains success counts
    response_json = response.json()
    assert "removed" in response_json
    # Assert removed count matches expected number
    assert response_json["removed"] == len(test_molecules)
    # Verify molecules are no longer associated with the library in the database
    updated_library = library.get(created_library.id, db=db_session)
    assert len(updated_library.molecules) == 0


def test_filter_libraries(client, pharma_token_headers, db_session, test_user):
    """Test filtering libraries based on criteria"""
    # Create multiple test libraries with different properties
    library_data1 = {"name": "Filtered Library 1", "description": "Description 1"}
    library.create_with_owner(library_data1, test_user.id, db=db_session)
    library_data2 = {"name": "Another Library", "description": "Description 2"}
    library.create_with_owner(library_data2, test_user.id, db=db_session)
    # Create filter criteria (e.g., name_contains, is_public)
    filter_criteria = {"name_contains": "Filtered"}
    # Send POST request to /api/v1/libraries/filter/ with filter criteria and authentication headers
    response = client.post("/api/v1/libraries/filter/", json=filter_criteria, headers=pharma_token_headers)
    # Assert response status code is 200 OK
    assert response.status_code == status.HTTP_200_OK
    # Assert response contains filtered libraries
    response_json = response.json()
    assert "items" in response_json
    # Assert total count matches expected number of filtered libraries
    assert response_json["total"] == 1
    # Verify filtered libraries match the filter criteria
    assert response_json["items"][0]["name"] == "Filtered Library 1"


def test_get_user_libraries(client, pharma_token_headers, db_session, test_user):
    """Test retrieving libraries owned by a specific user"""
    # Create multiple test libraries owned by test_user
    library_data1 = {"name": "User Library 1", "description": "User's first library"}
    library.create_with_owner(library_data1, test_user.id, db=db_session)
    library_data2 = {"name": "User Library 2", "description": "User's second library"}
    library.create_with_owner(library_data2, test_user.id, db=db_session)
    # Send GET request to /api/v1/libraries/user/{user_id} with authentication headers
    response = client.get(f"/api/v1/libraries/user/{test_user.id}", headers=pharma_token_headers)
    # Assert response status code is 200 OK
    assert response.status_code == status.HTTP_200_OK
    # Assert response contains user's libraries
    response_json = response.json()
    assert "items" in response_json
    # Assert total count matches expected number of user's libraries
    assert response_json["total"] == 2
    # Verify all libraries are owned by the specified user
    for lib in response_json["items"]:
        assert lib["owner_id"] == str(test_user.id)


def test_get_organization_libraries(client, pharma_token_headers, db_session, test_user):
    """Test retrieving libraries belonging to a specific organization"""
    # Create multiple test libraries with the same organization_id
    organization_id = uuid.uuid4()
    library_data1 = {"name": "Org Library 1", "description": "Org's first library", "organization_id": organization_id}
    library.create_with_owner(library_data1, test_user.id, db=db_session)
    library_data2 = {"name": "Org Library 2", "description": "Org's second library", "organization_id": organization_id}
    library.create_with_owner(library_data2, test_user.id, db=db_session)
    # Send GET request to /api/v1/libraries/organization/{organization_id} with authentication headers
    response = client.get(f"/api/v1/libraries/organization/{organization_id}", headers=pharma_token_headers)
    # Assert response status code is 200 OK
    assert response.status_code == status.HTTP_200_OK
    # Assert response contains organization's libraries
    response_json = response.json()
    assert "items" in response_json
    # Assert total count matches expected number of organization's libraries
    assert response_json["total"] == 2
    # Verify all libraries belong to the specified organization
    for lib in response_json["items"]:
        assert lib["organization_id"] == str(organization_id)