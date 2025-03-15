# src/backend/tests/crud/test_crud_library.py
import pytest
from uuid import uuid4
from datetime import datetime, timedelta
import random

from src.backend.app.crud.crud_library import CRUDLibrary, library
from src.backend.app.models.library import Library
from src.backend.app.models.molecule import Molecule
from src.backend.app.models.user import User
from src.backend.app.schemas.library import LibraryCreate, LibraryUpdate, LibraryFilter
from src.backend.tests.conftest import create_test_user, create_test_molecule


def test_create_with_owner(db_session):
    """Tests creating a library with an owner"""
    # Create a test user to be the owner
    owner = create_test_user(db_session, "owner@example.com", "password", "Owner User", "pharma_scientist")

    # Create a LibraryCreate object with name and description
    library_data = LibraryCreate(name="Test Library", description="A test library")

    # Call library.create_with_owner with the LibraryCreate object and owner ID
    library_obj = library.create_with_owner(library_data, owner.id, db=db_session)

    # Assert that the returned object is a Library instance
    assert isinstance(library_obj, Library)

    # Assert that the library has the correct name and description
    assert library_obj.name == "Test Library"
    assert library_obj.description == "A test library"

    # Assert that the library has the correct owner_id
    assert library_obj.owner_id == owner.id

    # Assert that created_at and updated_at are set
    assert library_obj.created_at is not None
    assert library_obj.updated_at is not None


def test_get_by_owner(db_session):
    """Tests retrieving libraries owned by a specific user"""
    # Create a test user to be the owner
    owner = create_test_user(db_session, "owner2@example.com", "password", "Owner User 2", "pharma_scientist")

    # Create multiple libraries with the same owner
    library_data1 = LibraryCreate(name="Library 1", description="Library 1 description")
    library_data2 = LibraryCreate(name="Library 2", description="Library 2 description")
    library.create_with_owner(library_data1, owner.id, db=db_session)
    library.create_with_owner(library_data2, owner.id, db=db_session)

    # Call library.get_by_owner with the owner ID
    libraries = library.get_by_owner(owner.id, db=db_session)

    # Assert that the correct number of libraries are returned
    assert libraries["total"] == 2
    assert len(libraries["items"]) == 2

    # Assert that all returned libraries have the correct owner_id
    for lib in libraries["items"]:
        assert lib.owner_id == owner.id

    # Test pagination by setting skip and limit parameters
    libraries_page2 = library.get_by_owner(owner.id, db=db_session, skip=1, limit=1)

    # Assert that pagination works correctly
    assert libraries_page2["total"] == 2
    assert len(libraries_page2["items"]) == 1
    assert libraries_page2["page"] == 2
    assert libraries_page2["size"] == 1


def test_get_by_organization(db_session):
    """Tests retrieving libraries belonging to a specific organization"""
    # Create a test organization ID
    org_id = uuid4()

    # Create multiple libraries with the same organization_id
    library_data1 = LibraryCreate(name="Org Library 1", description="Org Library 1 description", organization_id=org_id)
    library_data2 = LibraryCreate(name="Org Library 2", description="Org Library 2 description", organization_id=org_id)
    library.create_with_owner(library_data1, uuid4(), db=db_session)
    library.create_with_owner(library_data2, uuid4(), db=db_session)

    # Create some libraries with a different organization_id
    library_data3 = LibraryCreate(name="Other Org Library", description="Other Org Library description", organization_id=uuid4())
    library.create_with_owner(library_data3, uuid4(), db=db_session)

    # Call library.get_by_organization with the organization ID
    libraries = library.get_by_organization(org_id, db=db_session)

    # Assert that only libraries from the specified organization are returned
    assert libraries["total"] == 2
    for lib in libraries["items"]:
        assert lib.organization_id == org_id

    # Test pagination by setting skip and limit parameters
    libraries_page2 = library.get_by_organization(org_id, db=db_session, skip=1, limit=1)

    # Assert that pagination works correctly
    assert libraries_page2["total"] == 2
    assert len(libraries_page2["items"]) == 1
    assert libraries_page2["page"] == 2
    assert libraries_page2["size"] == 1


def test_get_accessible_libraries(db_session):
    """Tests retrieving libraries accessible to a specific user"""
    # Create a test user with a specific organization
    org_id = uuid4()
    user1 = create_test_user(db_session, "user1@example.com", "password", "User 1", "pharma_scientist")
    user1.organization_id = org_id

    # Create libraries owned by the user
    library_data1 = LibraryCreate(name="User Library", description="Library owned by user", owner_id=user1.id, organization_id=org_id)
    library.create_with_owner(library_data1, user1.id, db=db_session)

    # Create libraries in the user's organization but not owned by the user
    library_data2 = LibraryCreate(name="Org Library", description="Library in user's org", owner_id=uuid4(), organization_id=org_id)
    library.create_with_owner(library_data2, uuid4(), db=db_session)

    # Create public libraries not in the user's organization
    library_data3 = LibraryCreate(name="Public Library", description="Public library", owner_id=uuid4(), organization_id=uuid4(), is_public=True)
    library.create_with_owner(library_data3, uuid4(), db=db_session)

    # Create private libraries not in the user's organization
    library_data4 = LibraryCreate(name="Private Library", description="Private library", owner_id=uuid4(), organization_id=uuid4(), is_public=False)
    library.create_with_owner(library_data4, uuid4(), db=db_session)

    # Call library.get_accessible_libraries with the user
    accessible_libraries = library.get_accessible_libraries(user1, db=db_session)

    # Assert that the user can access their own libraries
    assert any(lib.name == "User Library" for lib in accessible_libraries["items"])

    # Assert that the user can access libraries in their organization
    assert any(lib.name == "Org Library" for lib in accessible_libraries["items"])

    # Assert that the user can access public libraries
    assert any(lib.name == "Public Library" for lib in accessible_libraries["items"])

    # Assert that the user cannot access private libraries from other organizations
    assert not any(lib.name == "Private Library" for lib in accessible_libraries["items"])

    # Test with a superuser who should access all libraries
    superuser = create_test_user(db_session, "superuser@example.com", "password", "Superuser", "system_admin")
    accessible_libraries_superuser = library.get_accessible_libraries(superuser, db=db_session)
    assert any(lib.name == "Private Library" for lib in accessible_libraries_superuser["items"])


def test_check_user_access(db_session):
    """Tests checking if a user has access to a specific library"""
    # Create a test user with a specific organization
    org_id = uuid4()
    user1 = create_test_user(db_session, "user2@example.com", "password", "User 2", "pharma_scientist")
    user1.organization_id = org_id

    # Create a library owned by the user
    library_data1 = LibraryCreate(name="User Library", description="Library owned by user", owner_id=user1.id, organization_id=org_id)
    library1 = library.create_with_owner(library_data1, user1.id, db=db_session)

    # Create a library in the user's organization but not owned by the user
    library_data2 = LibraryCreate(name="Org Library", description="Library in user's org", owner_id=uuid4(), organization_id=org_id)
    library2 = library.create_with_owner(library_data2, uuid4(), db=db_session)

    # Create a public library not in the user's organization
    library_data3 = LibraryCreate(name="Public Library", description="Public library", owner_id=uuid4(), organization_id=uuid4(), is_public=True)
    library3 = library.create_with_owner(library_data3, uuid4(), db=db_session)

    # Create a private library not in the user's organization
    library_data4 = LibraryCreate(name="Private Library", description="Private library", owner_id=uuid4(), organization_id=uuid4(), is_public=False)
    library4 = library.create_with_owner(library_data4, uuid4(), db=db_session)

    # Call library.check_user_access for each library with the user
    has_access1 = library.check_user_access(library1.id, user1, db=db_session)
    has_access2 = library.check_user_access(library2.id, user1, db=db_session)
    has_access3 = library.check_user_access(library3.id, user1, db=db_session)
    has_access4 = library.check_user_access(library4.id, user1, db=db_session)

    # Assert that the user has access to their own library
    assert has_access1 is True

    # Assert that the user has access to a library in their organization
    assert has_access2 is True

    # Assert that the user has access to a public library
    assert has_access3 is True

    # Assert that the user does not have access to a private library from another organization
    assert has_access4 is False

    # Test with a superuser who should have access to all libraries
    superuser = create_test_user(db_session, "superuser2@example.com", "password", "Superuser 2", "system_admin")
    has_access_superuser = library.check_user_access(library4.id, superuser, db=db_session)
    assert has_access_superuser is True


def test_add_molecule(db_session):
    """Tests adding a molecule to a library"""
    # Create a test library
    library_data = LibraryCreate(name="Test Library", description="A test library")
    library_obj = library.create_with_owner(library_data, uuid4(), db=db_session)

    # Create a test molecule
    molecule_obj = create_test_molecule(db_session, smiles="CC(=O)Oc1ccccc1C(=O)O")

    # Create a test user as the adder
    adder = create_test_user(db_session, "adder@example.com", "password", "Adder User", "pharma_scientist")

    # Call library.add_molecule with the library ID, molecule ID, and adder ID
    result = library.add_molecule(library_obj.id, molecule_obj.id, adder.id, db=db_session)

    # Assert that the function returns True (molecule added)
    assert result is True

    # Call library.get_molecules with the library ID
    molecules = library.get_molecules(library_obj.id, db=db_session)

    # Assert that the molecule is in the returned list
    assert any(mol.id == molecule_obj.id for mol in molecules["items"])

    # Call library.add_molecule with the same parameters again
    result2 = library.add_molecule(library_obj.id, molecule_obj.id, adder.id, db=db_session)

    # Assert that the function returns False (molecule already in library)
    assert result2 is False


def test_add_molecules(db_session):
    """Tests adding multiple molecules to a library"""
    # Create a test library
    library_data = LibraryCreate(name="Test Library", description="A test library")
    library_obj = library.create_with_owner(library_data, uuid4(), db=db_session)

    # Create multiple test molecules
    molecule_obj1 = create_test_molecule(db_session, smiles="CC(=O)Oc1ccccc1C(=O)O1")
    molecule_obj2 = create_test_molecule(db_session, smiles="CC(=O)Oc1ccccc1C(=O)O2")
    molecule_ids = [molecule_obj1.id, molecule_obj2.id]

    # Create a test user as the adder
    adder = create_test_user(db_session, "adder2@example.com", "password", "Adder User 2", "pharma_scientist")

    # Call library.add_molecules with the library ID, list of molecule IDs, and adder ID
    result = library.add_molecules(library_obj.id, molecule_ids, adder.id, db=db_session)

    # Assert that the function returns the correct counts of added and skipped molecules
    assert result["added"] == 2
    assert result["skipped"] == 0

    # Call library.get_molecules with the library ID
    molecules = library.get_molecules(library_obj.id, db=db_session)

    # Assert that all molecules are in the returned list
    assert any(mol.id == molecule_obj1.id for mol in molecules["items"])
    assert any(mol.id == molecule_obj2.id for mol in molecules["items"])

    # Call library.add_molecules with the same parameters again
    result2 = library.add_molecules(library_obj.id, molecule_ids, adder.id, db=db_session)

    # Assert that all molecules are reported as skipped (already in library)
    assert result2["added"] == 0
    assert result2["skipped"] == 2


def test_remove_molecule(db_session):
    """Tests removing a molecule from a library"""
    # Create a test library
    library_data = LibraryCreate(name="Test Library", description="A test library")
    library_obj = library.create_with_owner(library_data, uuid4(), db=db_session)

    # Create a test molecule
    molecule_obj = create_test_molecule(db_session, smiles="CC(=O)Oc1ccccc1C(=O)O3")

    # Add the molecule to the library
    adder = create_test_user(db_session, "adder3@example.com", "password", "Adder User 3", "pharma_scientist")
    library.add_molecule(library_obj.id, molecule_obj.id, adder.id, db=db_session)

    # Call library.remove_molecule with the library ID and molecule ID
    result = library.remove_molecule(library_obj.id, molecule_obj.id, db=db_session)

    # Assert that the function returns True (molecule removed)
    assert result is True

    # Call library.get_molecules with the library ID
    molecules = library.get_molecules(library_obj.id, db=db_session)

    # Assert that the molecule is not in the returned list
    assert not any(mol.id == molecule_obj.id for mol in molecules["items"])

    # Call library.remove_molecule with the same parameters again
    result2 = library.remove_molecule(library_obj.id, molecule_obj.id, db=db_session)

    # Assert that the function returns False (molecule not in library)
    assert result2 is False


def test_remove_molecules(db_session):
    """Tests removing multiple molecules from a library"""
    # Create a test library
    library_data = LibraryCreate(name="Test Library", description="A test library")
    library_obj = library.create_with_owner(library_data, uuid4(), db=db_session)

    # Create multiple test molecules
    molecule_obj1 = create_test_molecule(db_session, smiles="CC(=O)Oc1ccccc1C(=O)O4")
    molecule_obj2 = create_test_molecule(db_session, smiles="CC(=O)Oc1ccccc1C(=O)O5")
    molecule_ids = [molecule_obj1.id, molecule_obj2.id]

    # Add all molecules to the library
    adder = create_test_user(db_session, "adder4@example.com", "password", "Adder User 4", "pharma_scientist")
    library.add_molecules(library_obj.id, molecule_ids, adder.id, db=db_session)

    # Call library.remove_molecules with the library ID and list of molecule IDs
    result = library.remove_molecules(library_obj.id, molecule_ids, db=db_session)

    # Assert that the function returns the correct counts of removed and skipped molecules
    assert result["removed"] == 2
    assert result["skipped"] == 0

    # Call library.get_molecules with the library ID
    molecules = library.get_molecules(library_obj.id, db=db_session)

    # Assert that all molecules are removed from the library
    assert not any(mol.id == molecule_obj1.id for mol in molecules["items"])
    assert not any(mol.id == molecule_obj2.id for mol in molecules["items"])

    # Call library.remove_molecules with the same parameters again
    result2 = library.remove_molecules(library_obj.id, molecule_ids, db=db_session)

    # Assert that all molecules are reported as skipped (not in library)
    assert result2["removed"] == 0
    assert result2["skipped"] == 2


def test_get_molecules(db_session):
    """Tests retrieving molecules in a library with filtering and pagination"""
    # Create a test library
    library_data = LibraryCreate(name="Test Library", description="A test library")
    library_obj = library.create_with_owner(library_data, uuid4(), db=db_session)

    # Create multiple test molecules with different properties
    molecule_obj1 = create_test_molecule(db_session, smiles="CC(=O)Oc1ccccc1C(=O)O6")
    molecule_obj1.molecular_weight = 180.0
    molecule_obj2 = create_test_molecule(db_session, smiles="CC(=O)Oc1ccccc1C(=O)O7")
    molecule_obj2.molecular_weight = 200.0
    molecule_obj3 = create_test_molecule(db_session, smiles="CC(=O)Oc1ccccc1C(=O)O8")
    molecule_obj3.molecular_weight = 220.0
    db_session.add_all([molecule_obj1, molecule_obj2, molecule_obj3])
    db_session.commit()

    # Add all molecules to the library
    adder = create_test_user(db_session, "adder5@example.com", "password", "Adder User 5", "pharma_scientist")
    library.add_molecules(library_obj.id, [molecule_obj1.id, molecule_obj2.id, molecule_obj3.id], adder.id, db=db_session)

    # Call library.get_molecules with the library ID
    molecules = library.get_molecules(library_obj.id, db=db_session)

    # Assert that all molecules are returned
    assert molecules["total"] == 3
    assert len(molecules["items"]) == 3

    # Call library.get_molecules with filter parameters
    filter_params = {"molecular_weight": {"gt": 190.0}}
    filtered_molecules = library.get_molecules(library_obj.id, filter_params=filter_params, db=db_session)

    # Assert that only molecules matching the filters are returned
    assert filtered_molecules["total"] == 2
    assert all(mol.molecular_weight > 190.0 for mol in filtered_molecules["items"])

    # Test pagination by setting skip and limit parameters
    paged_molecules = library.get_molecules(library_obj.id, db=db_session, skip=1, limit=1)

    # Assert that pagination works correctly
    assert paged_molecules["total"] == 3
    assert len(paged_molecules["items"]) == 1
    assert paged_molecules["page"] == 2
    assert paged_molecules["size"] == 1

    # Test sorting by different properties
    sorted_molecules = library.get_molecules(library_obj.id, db=db_session, sort_by="molecular_weight")

    # Assert that sorting works correctly in both ascending and descending order
    assert sorted_molecules["items"][0].molecular_weight == 180.0
    sorted_molecules_desc = library.get_molecules(library_obj.id, db=db_session, sort_by="molecular_weight", descending=True)
    assert sorted_molecules_desc["items"][0].molecular_weight == 220.0


def test_filter_libraries(db_session):
    """Tests filtering libraries based on various criteria"""
    # Create multiple libraries with different attributes
    user1 = create_test_user(db_session, "user3@example.com", "password", "User 3", "pharma_scientist")
    org_id = uuid4()
    user1.organization_id = org_id

    library_data1 = LibraryCreate(name="Test Library 1", description="Description 1", owner_id=user1.id, organization_id=org_id, is_public=True)
    library1 = library.create_with_owner(library_data1, user1.id, db=db_session)

    library_data2 = LibraryCreate(name="Test Library 2", description="Description 2", owner_id=uuid4(), organization_id=org_id, is_public=False)
    library2 = library.create_with_owner(library_data2, uuid4(), db=db_session)

    library_data3 = LibraryCreate(name="Another Library", description="Description 3", owner_id=uuid4(), organization_id=uuid4(), is_public=True)
    library3 = library.create_with_owner(library_data3, uuid4(), db=db_session)

    # Create a LibraryFilter object with various filter criteria
    filter_params = LibraryFilter(name_contains="Test", owner_id=user1.id, organization_id=org_id, is_public=True)

    # Call library.filter_libraries with the filter object
    filtered_libraries = library.filter_libraries(filter_params, user=user1, db=db_session)

    # Assert that only libraries matching the filters are returned
    assert filtered_libraries["total"] == 1
    assert filtered_libraries["items"][0].id == library1.id

    # Test filtering by name_contains
    filter_params = LibraryFilter(name_contains="Another")
    filtered_libraries = library.filter_libraries(filter_params, user=user1, db=db_session)
    assert filtered_libraries["total"] == 1
    assert filtered_libraries["items"][0].name == "Another Library"

    # Test filtering by owner_id
    filter_params = LibraryFilter(owner_id=user1.id)
    filtered_libraries = library.filter_libraries(filter_params, user=user1, db=db_session)
    assert filtered_libraries["total"] == 1
    assert filtered_libraries["items"][0].owner_id == user1.id

    # Test filtering by organization_id
    filter_params = LibraryFilter(organization_id=org_id)
    filtered_libraries = library.filter_libraries(filter_params, user=user1, db=db_session)
    assert filtered_libraries["total"] == 2
    assert all(lib.organization_id == org_id for lib in filtered_libraries["items"])

    # Test filtering by is_public
    filter_params = LibraryFilter(is_public=True)
    filtered_libraries = library.filter_libraries(filter_params, user=user1, db=db_session)
    assert filtered_libraries["total"] == 2
    assert all(lib.is_public is True for lib in filtered_libraries["items"])

    # Test filtering by contains_molecule_id
    molecule_obj = create_test_molecule(db_session, smiles="CC(=O)Oc1ccccc1C(=O)O9")
    library.add_molecule(library1.id, molecule_obj.id, user1.id, db=db_session)
    filter_params = LibraryFilter(contains_molecule_id=molecule_obj.id)
    filtered_libraries = library.filter_libraries(filter_params, user=user1, db=db_session)
    assert filtered_libraries["total"] == 1
    assert filtered_libraries["items"][0].id == library1.id

    # Test combinations of multiple filters
    filter_params = LibraryFilter(name_contains="Test", owner_id=user1.id, is_public=True)
    filtered_libraries = library.filter_libraries(filter_params, user=user1, db=db_session)
    assert filtered_libraries["total"] == 1
    assert filtered_libraries["items"][0].id == library1.id

    # Test pagination by setting skip and limit parameters
    filter_params = LibraryFilter()
    filtered_libraries_page2 = library.filter_libraries(filter_params, user=user1, db=db_session, skip=1, limit=1)
    assert filtered_libraries_page2["total"] == 3
    assert len(filtered_libraries_page2["items"]) == 1
    assert filtered_libraries_page2["page"] == 2
    assert filtered_libraries_page2["size"] == 1


def test_get_with_molecule_count(db_session):
    """Tests retrieving a library with its molecule count"""
    # Create a test library
    library_data = LibraryCreate(name="Test Library", description="A test library")
    library_obj = library.create_with_owner(library_data, uuid4(), db=db_session)

    # Create multiple test molecules
    molecule_obj1 = create_test_molecule(db_session, smiles="CC(=O)Oc1ccccc1C(=O)Oa")
    molecule_obj2 = create_test_molecule(db_session, smiles="CC(=O)Oc1ccccc1C(=O)Ob")
    molecule_ids = [molecule_obj1.id, molecule_obj2.id]

    # Add a specific number of molecules to the library
    adder = create_test_user(db_session, "adder6@example.com", "password", "Adder User 6", "pharma_scientist")
    library.add_molecules(library_obj.id, molecule_ids, adder.id, db=db_session)

    # Call library.get_with_molecule_count with the library ID
    library_with_count = library.get_with_molecule_count(library_obj.id, db=db_session)

    # Assert that the returned library has the correct molecule_count
    assert library_with_count["molecule_count"] == 2

    # Add more molecules to the library
    molecule_obj3 = create_test_molecule(db_session, smiles="CC(=O)Oc1ccccc1C(=O)Oc")
    library.add_molecule(library_obj.id, molecule_obj3.id, adder.id, db=db_session)

    # Call library.get_with_molecule_count again
    library_with_count2 = library.get_with_molecule_count(library_obj.id, db=db_session)

    # Assert that the molecule_count has increased accordingly
    assert library_with_count2["molecule_count"] == 3

    # Remove some molecules from the library
    library.remove_molecule(library_obj.id, molecule_obj1.id, db=db_session)

    # Call library.get_with_molecule_count again
    library_with_count3 = library.get_with_molecule_count(library_obj.id, db=db_session)

    # Assert that the molecule_count has decreased accordingly
    assert library_with_count3["molecule_count"] == 2