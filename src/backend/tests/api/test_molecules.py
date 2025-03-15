import pytest
from unittest import mock
import io
import uuid
import json
from typing import List

from fastapi import status

from ..conftest import app, client, db_session, test_user, test_admin, test_molecule, test_molecules, pharma_token_headers, admin_token_headers, create_test_molecule
from ..conftest import molecule_service, storage_service, AIEngineClient, MoleculeException, CSVException
from ..conftest import Molecule, User

TEST_SMILES = "CC(=O)OC1=CC=CC=C1C(=O)O"
TEST_INVALID_SMILES = "XX(=O)OC1=CC=CC=C1C(=O)O"
TEST_CSV_CONTENT = "SMILES,MolecularWeight,LogP\nCC(=O)OC1=CC=CC=C1C(=O)O,180.16,1.21\nCCN(CC)CC,101.19,0.98\nc1ccccc1,78.11,2.13"
API_PREFIX = "/api/v1"

def test_create_molecule(client, pharma_token_headers):
    """Test creating a new molecule with valid SMILES"""
    molecule_data = {"smiles": TEST_SMILES, "properties": {"logp": 1.21}}
    response = client.post(f"{API_PREFIX}/molecules/", json=molecule_data, headers=pharma_token_headers)
    assert response.status_code == 201
    data = response.json()
    assert data["smiles"] == TEST_SMILES
    assert data["properties"]["logp"] == 1.21
    assert "id" in data

def test_create_molecule_invalid_smiles(client, pharma_token_headers):
    """Test molecule creation failure with invalid SMILES"""
    molecule_data = {"smiles": TEST_INVALID_SMILES}
    response = client.post(f"{API_PREFIX}/molecules/", json=molecule_data, headers=pharma_token_headers)
    assert response.status_code == 422
    data = response.json()
    assert "detail" in data
    assert "Invalid SMILES string" in data["detail"][0]["msg"]

def test_create_molecule_duplicate(client, pharma_token_headers, test_molecule):
    """Test creating a molecule with SMILES that already exists"""
    smiles = test_molecule.smiles
    molecule_data = {"smiles": smiles}
    response = client.post(f"{API_PREFIX}/molecules/", json=molecule_data, headers=pharma_token_headers)
    assert response.status_code == 200
    data = response.json()
    assert data["id"] == str(test_molecule.id)

def test_get_molecule(client, pharma_token_headers, test_molecule):
    """Test retrieving a molecule by ID"""
    molecule_id = str(test_molecule.id)
    response = client.get(f"{API_PREFIX}/molecules/{molecule_id}", headers=pharma_token_headers)
    assert response.status_code == 200
    data = response.json()
    assert data["id"] == molecule_id
    assert data["smiles"] == test_molecule.smiles
    assert "properties" in data
    assert "libraries" in data
    assert "submissions" in data

def test_get_molecule_not_found(client, pharma_token_headers):
    """Test retrieving a non-existent molecule"""
    random_id = str(uuid.uuid4())
    response = client.get(f"{API_PREFIX}/molecules/{random_id}", headers=pharma_token_headers)
    assert response.status_code == 404
    data = response.json()
    assert "detail" in data
    assert "Molecule not found" in data["detail"]

def test_get_molecule_by_smiles(client, pharma_token_headers, test_molecule):
    """Test retrieving a molecule by SMILES string"""
    smiles = test_molecule.smiles
    response = client.get(f"{API_PREFIX}/molecules/by-smiles/?smiles={smiles}", headers=pharma_token_headers)
    assert response.status_code == 200
    data = response.json()
    assert data["smiles"] == smiles
    assert "id" in data

def test_get_molecule_by_smiles_not_found(client, pharma_token_headers):
    """Test retrieving a non-existent molecule by SMILES"""
    unused_smiles = "C1=CC=CC=CC=1"
    response = client.get(f"{API_PREFIX}/molecules/by-smiles/?smiles={unused_smiles}", headers=pharma_token_headers)
    assert response.status_code == 404
    data = response.json()
    assert "detail" in data
    assert "Molecule not found" in data["detail"]

def test_update_molecule(client, pharma_token_headers, test_molecule):
    """Test updating an existing molecule"""
    molecule_id = str(test_molecule.id)
    update_data = {"status": "testing", "metadata": {"test": "value"}}
    response = client.put(f"{API_PREFIX}/molecules/{molecule_id}", json=update_data, headers=pharma_token_headers)
    assert response.status_code == 200
    data = response.json()
    assert data["status"] == "testing"
    assert data["metadata"]["test"] == "value"
    assert data["smiles"] == test_molecule.smiles

def test_update_molecule_not_found(client, pharma_token_headers):
    """Test updating a non-existent molecule"""
    random_id = str(uuid.uuid4())
    update_data = {"status": "testing"}
    response = client.put(f"{API_PREFIX}/molecules/{random_id}", json=update_data, headers=pharma_token_headers)
    assert response.status_code == 404
    data = response.json()
    assert "detail" in data
    assert "Molecule not found" in data["detail"]

def test_delete_molecule(client, pharma_token_headers, db_session):
    """Test deleting a molecule"""
    delete_molecule = create_test_molecule(db_session, "C1=CC=CC=C1")
    molecule_id = str(delete_molecule.id)
    response = client.delete(f"{API_PREFIX}/molecules/{molecule_id}", headers=pharma_token_headers)
    assert response.status_code == 200
    data = response.json()
    assert "message" in data
    assert "success" in data["message"]
    response = client.get(f"{API_PREFIX}/molecules/{molecule_id}", headers=pharma_token_headers)
    assert response.status_code == 404

def test_delete_molecule_not_found(client, pharma_token_headers):
    """Test deleting a non-existent molecule"""
    random_id = str(uuid.uuid4())
    response = client.delete(f"{API_PREFIX}/molecules/{random_id}", headers=pharma_token_headers)
    assert response.status_code == 404
    data = response.json()
    assert "detail" in data
    assert "Molecule not found" in data["detail"]

def test_filter_molecules(client, pharma_token_headers, test_molecules):
    """Test filtering molecules based on various criteria"""
    filter_data = {"smiles_contains": "C(=O)O"}
    response = client.post(f"{API_PREFIX}/molecules/filter/", json=filter_data, headers=pharma_token_headers)
    assert response.status_code == 200
    data = response.json()
    assert "items" in data
    assert "total" in data
    assert len(data["items"]) > 0
    for molecule in data["items"]:
        assert "C(=O)O" in molecule["smiles"]

def test_filter_molecules_by_property_range(client, pharma_token_headers, test_molecules):
    """Test filtering molecules by property value ranges"""
    filter_data = {"property_ranges": {"molecular_weight": {"min": 100, "max": 200}}}
    response = client.post(f"{API_PREFIX}/molecules/filter/", json=filter_data, headers=pharma_token_headers)
    assert response.status_code == 200
    data = response.json()
    assert "items" in data
    assert "total" in data
    assert len(data["items"]) > 0
    for molecule in data["items"]:
        assert 100 <= molecule["molecular_weight"] <= 200

def test_filter_molecules_pagination(client, pharma_token_headers, test_molecules):
    """Test molecule filtering with pagination"""
    filter_data = {}
    response = client.post(f"{API_PREFIX}/molecules/filter/?skip=1&limit=2", json=filter_data, headers=pharma_token_headers)
    assert response.status_code == 200
    data = response.json()
    assert "items" in data
    assert len(data["items"]) == 2
    assert data["total"] >= 3
    assert data["page"] == 1

@mock.patch('src.backend.app.services.storage_service.store_csv_file')
def test_upload_csv(mock_store_csv_file, client, pharma_token_headers):
    """Test uploading a CSV file with molecular data"""
    mock_store_csv_file.return_value = "test_url"
    file = io.BytesIO(TEST_CSV_CONTENT.encode())
    response = client.post(
        f"{API_PREFIX}/molecules/upload-csv/",
        files={"file": ("test.csv", file, "text/csv")},
        headers=pharma_token_headers,
    )
    assert response.status_code == 202
    data = response.json()
    assert data["file_url"] == "test_url"
    assert "status" in data
    mock_store_csv_file.assert_called_once()

def test_upload_csv_invalid_format(client, pharma_token_headers):
    """Test uploading a CSV file with invalid format"""
    invalid_csv_content = "Invalid,CSV,Format"
    file = io.BytesIO(invalid_csv_content.encode())
    response = client.post(
        f"{API_PREFIX}/molecules/upload-csv/",
        files={"file": ("test.csv", file, "text/csv")},
        headers=pharma_token_headers,
    )
    assert response.status_code == 400
    data = response.json()
    assert "detail" in data
    assert "Invalid CSV format" in data["detail"]

@mock.patch('src.backend.app.services.storage_service.get_download_url')
@mock.patch('src.backend.app.services.molecule_service.get_csv_preview')
def test_get_csv_preview(mock_get_csv_preview, mock_get_download_url, client, pharma_token_headers):
    """Test getting a preview of CSV data for column mapping"""
    mock_get_download_url.return_value = "test_url"
    mock_get_csv_preview.return_value = {"headers": ["SMILES", "MW"], "rows": [["C", 12]], "mapping_suggestions": {}}
    response = client.get(f"{API_PREFIX}/molecules/csv-preview/?file_url=test_url&num_rows=3", headers=pharma_token_headers)
    assert response.status_code == 200
    data = response.json()
    assert "headers" in data
    assert "rows" in data
    assert "mapping_suggestions" in data
    mock_get_download_url.assert_called_once_with("test_url")
    mock_get_csv_preview.assert_called_once()

@mock.patch('src.backend.app.services.storage_service.get_download_url')
@mock.patch('src.backend.app.services.molecule_service.process_csv_file')
def test_process_csv(mock_process_csv_file, mock_get_download_url, client, pharma_token_headers):
    """Test processing a previously uploaded CSV file"""
    mock_get_download_url.return_value = "test_url"
    mock_process_csv_file.return_value = {"created": 1, "skipped": 0, "failed": 0}
    mapping_data = {"column_mapping": {"SMILES": "smiles"}}
    response = client.post(f"{API_PREFIX}/molecules/process-csv/?file_url=test_url", json=mapping_data, headers=pharma_token_headers)
    assert response.status_code == 200
    data = response.json()
    assert "created" in data
    assert "skipped" in data
    assert "failed" in data
    mock_get_download_url.assert_called_once_with("test_url")
    mock_process_csv_file.assert_called_once()

@mock.patch('src.backend.app.services.molecule_service.predict_properties')
def test_predict_properties(mock_predict_properties, client, pharma_token_headers, test_molecule):
    """Test requesting property predictions for a molecule"""
    mock_predict_properties.return_value = {"job_id": "123"}
    molecule_id = str(test_molecule.id)
    response = client.post(f"{API_PREFIX}/molecules/{molecule_id}/predict/?properties=logp", headers=pharma_token_headers)
    assert response.status_code == 200
    data = response.json()
    assert "job_id" in data
    mock_predict_properties.assert_called_once()

@mock.patch('src.backend.app.services.molecule_service.batch_predict_properties')
def test_batch_predict_properties(mock_batch_predict_properties, client, pharma_token_headers, test_molecules):
    """Test requesting property predictions for multiple molecules"""
    mock_batch_predict_properties.return_value = {"batch_id": "123"}
    molecule_ids = [str(molecule.id) for molecule in test_molecules]
    request_data = {"molecule_ids": molecule_ids}
    response = client.post(f"{API_PREFIX}/molecules/batch-predict/?properties=logp", json=request_data, headers=pharma_token_headers)
    assert response.status_code == 202
    data = response.json()
    assert "batch_id" in data
    mock_batch_predict_properties.assert_called_once()

@mock.patch('src.backend.app.services.molecule_service.bulk_operation')
def test_bulk_operation(mock_bulk_operation, client, pharma_token_headers, test_molecules):
    """Test performing bulk operations on multiple molecules"""
    mock_bulk_operation.return_value = {"success": True}
    molecule_ids = [str(molecule.id) for molecule in test_molecules]
    operation_data = {"molecule_ids": molecule_ids, "operation": "add_to_library"}
    response = client.post(f"{API_PREFIX}/molecules/bulk-operation/", json=operation_data, headers=pharma_token_headers)
    assert response.status_code == 200
    data = response.json()
    assert "success" in data
    mock_bulk_operation.assert_called_once()

def test_unauthorized_access(client):
    """Test unauthorized access to molecule endpoints"""
    response = client.get(f"{API_PREFIX}/molecules/")
    assert response.status_code == 401
    data = response.json()
    assert "detail" in data
    assert "Not authenticated" in data["detail"]
    response = client.post(f"{API_PREFIX}/molecules/")
    assert response.status_code == 401