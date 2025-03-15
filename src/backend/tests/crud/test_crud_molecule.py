# src/backend/tests/crud/test_crud_molecule.py
import pytest
import uuid
from datetime import datetime
import random

from sqlalchemy.orm import Session

from src.backend.app.crud.crud_molecule import CRUDMolecule, molecule
from src.backend.app.models.molecule import Molecule, MoleculeStatus
from src.backend.app.models.library import Library
from src.backend.app.schemas.molecule import MoleculeCreate, MoleculeUpdate
from src.backend.app.constants.molecule_properties import PropertySource
from src.backend.app.utils.smiles import validate_smiles


def test_create_from_smiles(db_session: Session):
    """Tests creating a molecule from a SMILES string"""
    smiles_string = "CC(=O)Oc1ccccc1C(=O)O"
    new_molecule = molecule.create_from_smiles(smiles=smiles_string, db=db_session)

    assert isinstance(new_molecule, Molecule)
    assert new_molecule.smiles == smiles_string
    assert new_molecule.inchi_key is not None
    assert new_molecule.status == MoleculeStatus.AVAILABLE.value


def test_create_from_smiles_duplicate(db_session: Session):
    """Tests that creating a molecule with an existing SMILES returns the existing molecule"""
    smiles_string = "CC(=O)Oc1ccccc1C(=O)O"
    molecule1 = molecule.create_from_smiles(smiles=smiles_string, db=db_session)
    molecule2 = molecule.create_from_smiles(smiles=smiles_string, db=db_session)

    assert molecule1.id == molecule2.id
    assert db_session.query(Molecule).filter(Molecule.smiles == smiles_string).count() == 1


def test_create_with_properties(db_session: Session):
    """Tests creating a molecule with properties"""
    molecule_create = MoleculeCreate(
        smiles="CC(=O)Oc1ccccc1C(=O)O",
        properties=[
            {"name": "logp", "value": 1.2, "source": PropertySource.IMPORTED.value},
            {"name": "molecular_weight", "value": 180.16, "source": PropertySource.IMPORTED.value},
        ],
    )
    new_molecule = molecule.create_with_properties(obj_in=molecule_create, db=db_session)

    assert isinstance(new_molecule, Molecule)
    assert new_molecule.smiles == "CC(=O)Oc1ccccc1C(=O)O"
    assert new_molecule.get_property("logp") == 1.2
    assert new_molecule.get_property("molecular_weight") == 180.16


def test_update_with_properties(db_session: Session):
    """Tests updating a molecule with new properties"""
    initial_molecule = molecule.create_from_smiles(smiles="CC(=O)Oc1ccccc1C(=O)O", db=db_session)
    molecule_update = MoleculeUpdate(
        properties=[
            {"name": "logp", "value": 1.5, "source": PropertySource.IMPORTED.value},
            {"name": "solubility", "value": 0.5, "source": PropertySource.IMPORTED.value},
        ]
    )
    updated_molecule = molecule.update_with_properties(
        db_obj=initial_molecule, obj_in=molecule_update, db=db_session
    )

    assert updated_molecule.id == initial_molecule.id
    assert updated_molecule.get_property("logp") == 1.5
    assert updated_molecule.get_property("solubility") == 0.5


def test_get_by_smiles(db_session: Session):
    """Tests retrieving a molecule by its SMILES string"""
    smiles_string = "CC(=O)Oc1ccccc1C(=O)O"
    created_molecule = molecule.create_from_smiles(smiles=smiles_string, db=db_session)
    retrieved_molecule = molecule.get_by_smiles(smiles=smiles_string, db=db_session)

    assert retrieved_molecule.id == created_molecule.id

    non_existent_molecule = molecule.get_by_smiles(smiles="Invalid SMILES", db=db_session)
    assert non_existent_molecule is None


def test_get_by_inchi_key(db_session: Session):
    """Tests retrieving a molecule by its InChI Key"""
    smiles_string = "CC(=O)Oc1ccccc1C(=O)O"
    created_molecule = molecule.create_from_smiles(smiles=smiles_string, db=db_session)
    inchi_key = created_molecule.inchi_key
    retrieved_molecule = molecule.get_by_inchi_key(inchi_key=inchi_key, db=db_session)

    assert retrieved_molecule.id == created_molecule.id

    non_existent_molecule = molecule.get_by_inchi_key(inchi_key="Invalid InChI Key", db=db_session)
    assert non_existent_molecule is None


def test_get_with_properties(db_session: Session):
    """Tests retrieving a molecule with all its properties"""
    molecule_create = MoleculeCreate(
        smiles="CC(=O)Oc1ccccc1C(=O)O",
        properties=[
            {"name": "logp", "value": 1.2, "source": PropertySource.IMPORTED.value},
            {"name": "molecular_weight", "value": 180.16, "source": PropertySource.IMPORTED.value},
        ],
    )
    created_molecule = molecule.create_with_properties(obj_in=molecule_create, db=db_session)
    retrieved_molecule = molecule.get_with_properties(molecule_id=created_molecule.id, db=db_session)

    assert retrieved_molecule.id == created_molecule.id
    assert len(retrieved_molecule.properties) == 2
    assert retrieved_molecule.get_property("logp") == 1.2
    assert retrieved_molecule.get_property("molecular_weight") == 180.16


def test_add_to_library(db_session: Session):
    """Tests adding a molecule to a library"""
    test_molecule = molecule.create_from_smiles(smiles="CC(=O)Oc1ccccc1C(=O)O", db=db_session)
    test_library = Library(name="Test Library", owner_id=uuid.uuid4())
    db_session.add(test_library)
    db_session.commit()

    add_result = molecule.add_to_library(
        molecule_id=test_molecule.id, library_id=test_library.id, added_by=test_library.owner_id, db=db_session
    )
    assert add_result is True

    library_molecules = molecule.get_by_library(library_id=test_library.id, db=db_session)["items"]
    assert test_molecule in library_molecules

    add_again_result = molecule.add_to_library(
        molecule_id=test_molecule.id, library_id=test_library.id, added_by=test_library.owner_id, db=db_session
    )
    assert add_again_result is False


def test_remove_from_library(db_session: Session):
    """Tests removing a molecule from a library"""
    test_molecule = molecule.create_from_smiles(smiles="CC(=O)Oc1ccccc1C(=O)O", db=db_session)
    test_library = Library(name="Test Library", owner_id=uuid.uuid4())
    db_session.add(test_library)
    db_session.commit()
    molecule.add_to_library(
        molecule_id=test_molecule.id, library_id=test_library.id, added_by=test_library.owner_id, db=db_session
    )

    remove_result = molecule.remove_from_library(molecule_id=test_molecule.id, library_id=test_library.id, db=db_session)
    assert remove_result is True

    library_molecules = molecule.get_by_library(library_id=test_library.id, db=db_session)["items"]
    assert test_molecule not in library_molecules

    remove_again_result = molecule.remove_from_library(
        molecule_id=test_molecule.id, library_id=test_library.id, db=db_session
    )
    assert remove_again_result is False


def test_set_property(db_session: Session):
    """Tests setting a property value on a molecule"""
    test_molecule = molecule.create_from_smiles(smiles="CC(=O)Oc1ccccc1C(=O)O", db=db_session)

    set_result = molecule.set_property(
        molecule_id=test_molecule.id,
        property_name="logp",
        value=1.2,
        source=PropertySource.IMPORTED.value,
        db=db_session,
    )
    assert set_result is True

    retrieved_value = molecule.get_property(molecule_id=test_molecule.id, property_name="logp", db=db_session)
    assert retrieved_value == 1.2

    set_result_updated = molecule.set_property(
        molecule_id=test_molecule.id,
        property_name="logp",
        value=1.5,
        source=PropertySource.IMPORTED.value,
        db=db_session,
    )
    assert set_result_updated is True

    retrieved_value_updated = molecule.get_property(
        molecule_id=test_molecule.id, property_name="logp", db=db_session
    )
    assert retrieved_value_updated == 1.5


def test_get_property(db_session: Session):
    """Tests retrieving a property value from a molecule"""
    test_molecule = molecule.create_from_smiles(smiles="CC(=O)Oc1ccccc1C(=O)O", db=db_session)
    molecule.set_property(
        molecule_id=test_molecule.id,
        property_name="logp",
        value=1.2,
        source=PropertySource.IMPORTED.value,
        db=db_session,
    )
    molecule.set_property(
        molecule_id=test_molecule.id,
        property_name="molecular_weight",
        value=180.16,
        source=PropertySource.IMPORTED.value,
        db=db_session,
    )

    retrieved_value = molecule.get_property(molecule_id=test_molecule.id, property_name="logp", db=db_session)
    assert retrieved_value == 1.2

    non_existent_value = molecule.get_property(
        molecule_id=test_molecule.id, property_name="non_existent", db=db_session
    )
    assert non_existent_value is None

    imported_value = molecule.get_property(
        molecule_id=test_molecule.id, property_name="logp", source=PropertySource.IMPORTED, db=db_session
    )
    assert imported_value == 1.2


def test_filter_molecules(db_session: Session):
    """Tests filtering molecules based on various criteria"""
    # Create multiple molecules with different properties
    molecule1 = molecule.create_from_smiles(smiles="CC(=O)Oc1ccccc1C(=O)O", db=db_session)
    molecule2 = molecule.create_from_smiles(smiles="c1ccccc1", db=db_session)
    molecule3 = molecule.create_from_smiles(smiles="C1CCCCC1", db=db_session)

    # Test filtering by SMILES substring
    filter_params = {"smiles_contains": "c1ccccc1"}
    filtered_molecules = molecule.filter_molecules(filter_params=filter_params, db=db_session)["items"]
    assert molecule2 in filtered_molecules
    assert molecule1 not in filtered_molecules
    assert molecule3 not in filtered_molecules

    # Test filtering by formula substring
    filter_params = {"formula_contains": "C6H6"}
    filtered_molecules = molecule.filter_molecules(filter_params=filter_params, db=db_session)["items"]
    assert molecule2 in filtered_molecules
    assert molecule1 not in filtered_molecules
    assert molecule3 not in filtered_molecules

    # Test filtering by status
    molecule1.status = MoleculeStatus.PENDING.value
    db_session.commit()
    filter_params = {"status": MoleculeStatus.PENDING.value}
    filtered_molecules = molecule.filter_molecules(filter_params=filter_params, db=db_session)["items"]
    assert molecule1 in filtered_molecules
    assert molecule2 not in filtered_molecules
    assert molecule3 not in filtered_molecules

    # Test filtering by property ranges
    molecule.set_property(molecule_id=molecule1.id, property_name="logp", value=1.2, source=PropertySource.IMPORTED.value, db=db_session)
    molecule.set_property(molecule_id=molecule2.id, property_name="logp", value=2.5, source=PropertySource.IMPORTED.value, db=db_session)
    filter_params = {"property_ranges": {"logp": {"min": 1.0, "max": 2.0}}}
    filtered_molecules = molecule.filter_molecules(filter_params=filter_params, db=db_session)["items"]
    assert molecule1 in filtered_molecules
    assert molecule2 not in filtered_molecules
    assert molecule3 not in filtered_molecules

    # Test filtering by library ID
    library1 = Library(name="Library 1", owner_id=uuid.uuid4())
    db_session.add(library1)
    db_session.commit()
    molecule.add_to_library(molecule_id=molecule1.id, library_id=library1.id, added_by=library1.owner_id, db=db_session)
    filter_params = {"library_id": library1.id}
    filtered_molecules = molecule.filter_molecules(filter_params=filter_params, db=db_session)["items"]
    assert molecule1 in filtered_molecules
    assert molecule2 not in filtered_molecules
    assert molecule3 not in filtered_molecules

    # Test filtering by created_by user ID
    user_id = uuid.uuid4()
    molecule3 = molecule.create_from_smiles(smiles="C1CCCCC1", created_by=user_id, db=db_session)
    filter_params = {"created_by": user_id}
    filtered_molecules = molecule.filter_molecules(filter_params=filter_params, db=db_session)["items"]
    assert molecule3 in filtered_molecules
    assert molecule1 not in filtered_molecules
    assert molecule2 not in filtered_molecules

    # Test combinations of multiple filters
    filter_params = {
        "smiles_contains": "c1",
        "property_ranges": {"logp": {"min": 1.0, "max": 3.0}},
        "library_id": library1.id,
    }
    filtered_molecules = molecule.filter_molecules(filter_params=filter_params, db=db_session)["items"]
    assert molecule1 in filtered_molecules
    assert molecule2 not in filtered_molecules
    assert molecule3 not in filtered_molecules


def test_search_by_similarity(db_session: Session):
    """Tests searching for molecules similar to a query molecule"""
    # Create multiple molecules with varying similarity
    molecule1 = molecule.create_from_smiles(smiles="CC(=O)Oc1ccccc1C(=O)O", db=db_session)
    molecule2 = molecule.create_from_smiles(smiles="c1ccccc1", db=db_session)
    molecule3 = molecule.create_from_smiles(smiles="C1CCCCC1", db=db_session)

    # Call molecule.search_by_similarity with a query SMILES and threshold
    query_smiles = "c1ccccc1"
    threshold = 0.5
    similar_molecules = molecule.search_by_similarity(
        query_smiles=query_smiles, threshold=threshold, db=db_session
    )["items"]

    # Assert that molecules above the similarity threshold are returned
    assert any(mol["smiles"] == molecule2.smiles for mol in similar_molecules)

    # Assert that molecules below the similarity threshold are not returned
    assert not any(mol["smiles"] == molecule1.smiles for mol in similar_molecules)
    assert not any(mol["smiles"] == molecule3.smiles for mol in similar_molecules)

    # Assert that results are sorted by similarity (descending)
    if len(similar_molecules) > 1:
        assert similar_molecules[0]["similarity"] >= similar_molecules[1]["similarity"]

    # Test with different fingerprint types
    similar_molecules_maccs = molecule.search_by_similarity(
        query_smiles=query_smiles, threshold=threshold, fingerprint_type="maccs", db=db_session
    )["items"]
    assert isinstance(similar_molecules_maccs, list)

    # Test with different similarity thresholds
    threshold = 0.9
    similar_molecules_high_threshold = molecule.search_by_similarity(
        query_smiles=query_smiles, threshold=threshold, db=db_session
    )["items"]
    # Depending on the exact similarity, this may be empty
    assert isinstance(similar_molecules_high_threshold, list)


def test_search_by_substructure(db_session: Session):
    """Tests searching for molecules containing a substructure"""
    # Create multiple molecules with different structures
    molecule1 = molecule.create_from_smiles(smiles="CC(=O)Oc1ccccc1C(=O)O", db=db_session)
    molecule2 = molecule.create_from_smiles(smiles="c1ccccc1", db=db_session)
    molecule3 = molecule.create_from_smiles(smiles="C1CCCCC1", db=db_session)

    # Call molecule.search_by_substructure with a query substructure SMILES
    query_smiles = "c1ccccc1"
    substructure_molecules = molecule.search_by_substructure(query_smiles=query_smiles, db=db_session)["items"]

    # Assert that molecules containing the substructure are returned
    assert molecule1 in substructure_molecules
    assert molecule2 in substructure_molecules

    # Assert that molecules not containing the substructure are not returned
    assert molecule3 not in substructure_molecules

    # Test with different substructure queries
    query_smiles = "CC(=O)O"
    substructure_molecules2 = molecule.search_by_substructure(query_smiles=query_smiles, db=db_session)["items"]
    assert molecule1 in substructure_molecules2
    assert molecule2 not in substructure_molecules2
    assert molecule3 not in substructure_molecules2


def test_batch_create(db_session: Session):
    """Tests creating multiple molecules in a batch operation"""
    # Create a list of MoleculeCreate objects with different SMILES and properties
    molecule_list = [
        MoleculeCreate(smiles="CC(=O)Oc1ccccc1C(=O)O", properties=[{"name": "logp", "value": 1.2, "source": PropertySource.IMPORTED.value}]),
        MoleculeCreate(smiles="c1ccccc1"),
        MoleculeCreate(smiles="C1CCCCC1", properties=[{"name": "molecular_weight", "value": 84.16, "source": PropertySource.IMPORTED.value}]),
    ]

    # Call molecule.batch_create with the list
    batch_result = molecule.batch_create(obj_list=molecule_list, db=db_session)

    # Assert that the correct number of molecules are created
    assert batch_result["created_count"] == 3
    assert batch_result["total"] == 3

    # Assert that the returned statistics match expectations
    assert len(batch_result["created"]) == 3
    assert len(batch_result["skipped"]) == 0
    assert len(batch_result["failed"]) == 0

    # Assert that all molecules are stored in the database
    assert db_session.query(Molecule).count() == 3

    # Test with some duplicate molecules to verify handling
    molecule_list_with_duplicates = [
        MoleculeCreate(smiles="CC(=O)Oc1ccccc1C(=O)O"),
        MoleculeCreate(smiles="c1ccccc1"),
        MoleculeCreate(smiles="C1CCCCC1"),
        MoleculeCreate(smiles="CC(=O)Oc1ccccc1C(=O)O"),
    ]
    batch_result_with_duplicates = molecule.batch_create(obj_list=molecule_list_with_duplicates, db=db_session)
    assert batch_result_with_duplicates["created_count"] == 0
    assert batch_result_with_duplicates["skipped_count"] == 4
    assert batch_result_with_duplicates["failed_count"] == 0
    assert db_session.query(Molecule).count() == 3

    # Test with some invalid SMILES to verify error handling
    molecule_list_with_invalid = [
        MoleculeCreate(smiles="CC(=O)Oc1ccccc1C(=O)O"),
        MoleculeCreate(smiles="invalid smiles"),
        MoleculeCreate(smiles="C1CCCCC1"),
    ]
    batch_result_with_invalid = molecule.batch_create(obj_list=molecule_list_with_invalid, db=db_session)
    assert batch_result_with_invalid["created_count"] == 0
    assert batch_result_with_invalid["skipped_count"] == 3
    assert batch_result_with_invalid["failed_count"] == 0
    assert db_session.query(Molecule).count() == 3