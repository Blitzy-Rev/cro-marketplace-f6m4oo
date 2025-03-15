import pytest
from fastapi import FastAPI, status
from fastapi.testclient import TestClient
from typing import Dict
import unittest.mock
import uuid
import json

from ..conftest import app, client, db_session, admin_token_headers, pharma_token_headers, cro_token_headers, test_admin
from ...app.models.cro_service import ServiceType, CROService
from ...app.crud.crud_cro_service import cro_service
from ...app.core.exceptions import NotFoundException, ConflictException

API_PREFIX = "/api/v1"
TEST_SERVICE_NAME = "Binding Assay Service"
TEST_SERVICE_PROVIDER = "BioCRO Inc."
TEST_SERVICE_DESCRIPTION = "Radioligand binding assay for target protein XYZ"

def create_test_cro_service(db, name, provider, service_type, base_price, typical_turnaround_days, description, active):
    """Helper function to create a test CRO service in the database"""
    service = CROService.create(
        name=name,
        provider=provider,
        service_type=service_type,
        base_price=base_price,
        typical_turnaround_days=typical_turnaround_days,
        description=description,
        active=active
    )
    db.add(service)
    db.commit()
    return service

def test_get_cro_services(client, pharma_token_headers, db_session):
    """Test retrieving a list of CRO services"""
    service1 = create_test_cro_service(db_session, "Service 1", "Provider A", ServiceType.BINDING_ASSAY, 1000.0, 14, "Description 1", True)
    service2 = create_test_cro_service(db_session, "Service 2", "Provider B", ServiceType.ADME, 1500.0, 21, "Description 2", False)
    db_session.commit()

    response = client.get(f"{API_PREFIX}/cro/", headers=pharma_token_headers)
    assert response.status_code == 200

    data = response.json()
    assert "items" in data
    assert "total" in data
    assert data["total"] == 2

    services = data["items"]
    assert len(services) == 2
    assert services[0]["name"] == "Service 1"
    assert services[1]["name"] == "Service 2"

def test_get_cro_services_with_filters(client, pharma_token_headers, db_session):
    """Test retrieving CRO services with filtering parameters"""
    service1 = create_test_cro_service(db_session, "Binding Assay 1", "BioCRO Inc.", ServiceType.BINDING_ASSAY, 1000.0, 14, "Description 1", True)
    service2 = create_test_cro_service(db_session, "ADME Panel 1", "PharmaTest Labs", ServiceType.ADME, 1500.0, 21, "Description 2", False)
    db_session.commit()

    response = client.get(f"{API_PREFIX}/cro/?name_contains=Binding&provider=BioCRO", headers=pharma_token_headers)
    assert response.status_code == 200

    data = response.json()
    assert "items" in data
    assert "total" in data
    assert data["total"] == 1

    services = data["items"]
    assert len(services) == 1
    assert services[0]["name"] == "Binding Assay 1"

def test_get_active_cro_services(client, pharma_token_headers, db_session):
    """Test retrieving only active CRO services"""
    service1 = create_test_cro_service(db_session, "Service 1", "Provider A", ServiceType.BINDING_ASSAY, 1000.0, 14, "Description 1", True)
    service2 = create_test_cro_service(db_session, "Service 2", "Provider B", ServiceType.ADME, 1500.0, 21, "Description 2", False)
    db_session.commit()

    response = client.get(f"{API_PREFIX}/cro/active", headers=pharma_token_headers)
    assert response.status_code == 200

    data = response.json()
    assert "items" in data
    assert "total" in data
    assert data["total"] == 1

    services = data["items"]
    assert len(services) == 1
    assert services[0]["name"] == "Service 1"

def test_search_cro_services(client, pharma_token_headers, db_session):
    """Test searching CRO services by name or description"""
    service1 = create_test_cro_service(db_session, "Binding Assay 1", "Provider A", ServiceType.BINDING_ASSAY, 1000.0, 14, "Description 1", True)
    service2 = create_test_cro_service(db_session, "ADME Panel 1", "Provider B", ServiceType.ADME, 1500.0, 21, "Description 2", False)
    db_session.commit()

    response = client.get(f"{API_PREFIX}/cro/search?q=binding", headers=pharma_token_headers)
    assert response.status_code == 200

    data = response.json()
    assert "items" in data
    assert "total" in data
    assert data["total"] == 1

    services = data["items"]
    assert len(services) == 1
    assert services[0]["name"] == "Binding Assay 1"

def test_get_cro_service_by_id(client, pharma_token_headers, db_session):
    """Test retrieving a specific CRO service by ID"""
    service = create_test_cro_service(db_session, "Service 1", "Provider A", ServiceType.BINDING_ASSAY, 1000.0, 14, "Description 1", True)
    db_session.commit()

    response = client.get(f"{API_PREFIX}/cro/{service.id}", headers=pharma_token_headers)
    assert response.status_code == 200

    data = response.json()
    assert data["name"] == "Service 1"
    assert data["provider"] == "Provider A"
    assert data["service_type"] == "BINDING_ASSAY"
    assert data["base_price"] == 1000.0
    assert data["typical_turnaround_days"] == 14
    assert data["description"] == "Description 1"
    assert data["active"] == True

def test_get_cro_service_not_found(client, pharma_token_headers):
    """Test retrieving a non-existent CRO service"""
    random_id = uuid.uuid4()
    response = client.get(f"{API_PREFIX}/cro/{random_id}", headers=pharma_token_headers)
    assert response.status_code == 404
    data = response.json()
    assert data["message"] == f"CRO service with ID {random_id} not found"

def test_create_cro_service(client, admin_token_headers):
    """Test creating a new CRO service"""
    service_data = {
        "name": "New Service",
        "provider": "New Provider",
        "service_type": "ADME",
        "base_price": 2000.0,
        "typical_turnaround_days": 28,
        "description": "New Description",
        "active": True
    }
    response = client.post(f"{API_PREFIX}/cro/", json=service_data, headers=admin_token_headers)
    assert response.status_code == 201

    data = response.json()
    assert data["name"] == "New Service"
    assert data["provider"] == "New Provider"
    assert data["service_type"] == "ADME"
    assert data["base_price"] == 2000.0
    assert data["typical_turnaround_days"] == 28
    assert data["description"] == "New Description"
    assert data["active"] == True

def test_create_cro_service_validation_error(client, admin_token_headers):
    """Test validation errors when creating a CRO service"""
    service_data = {
        "provider": "New Provider",
        "service_type": "ADME",
        "base_price": 2000.0,
        "typical_turnaround_days": 28,
        "description": "New Description",
        "active": True
    }
    response = client.post(f"{API_PREFIX}/cro/", json=service_data, headers=admin_token_headers)
    assert response.status_code == 422
    data = response.json()
    assert "detail" in data

def test_create_cro_service_unauthorized(client, pharma_token_headers):
    """Test unauthorized creation of CRO service"""
    service_data = {
        "name": "New Service",
        "provider": "New Provider",
        "service_type": "ADME",
        "base_price": 2000.0,
        "typical_turnaround_days": 28,
        "description": "New Description",
        "active": True
    }
    response = client.post(f"{API_PREFIX}/cro/", json=service_data, headers=pharma_token_headers)
    assert response.status_code == 403
    data = response.json()
    assert data["message"] == "Admin privileges required"

def test_create_duplicate_cro_service(client, admin_token_headers, db_session):
    """Test creating a CRO service with a name that already exists"""
    create_test_cro_service(db_session, "Existing Service", "Provider A", ServiceType.BINDING_ASSAY, 1000.0, 14, "Description 1", True)
    db_session.commit()

    service_data = {
        "name": "Existing Service",
        "provider": "New Provider",
        "service_type": "ADME",
        "base_price": 2000.0,
        "typical_turnaround_days": 28,
        "description": "New Description",
        "active": True
    }
    response = client.post(f"{API_PREFIX}/cro/", json=service_data, headers=admin_token_headers)
    assert response.status_code == 409
    data = response.json()
    assert data["message"] == "CRO service with name 'Existing Service' already exists"

def test_update_cro_service(client, admin_token_headers, db_session):
    """Test updating an existing CRO service"""
    service = create_test_cro_service(db_session, "Service 1", "Provider A", ServiceType.BINDING_ASSAY, 1000.0, 14, "Description 1", True)
    db_session.commit()

    update_data = {
        "description": "Updated Description",
        "base_price": 1200.0
    }
    response = client.put(f"{API_PREFIX}/cro/{service.id}", json=update_data, headers=admin_token_headers)
    assert response.status_code == 200

    data = response.json()
    assert data["name"] == "Service 1"
    assert data["provider"] == "Provider A"
    assert data["service_type"] == "BINDING_ASSAY"
    assert data["base_price"] == 1200.0
    assert data["typical_turnaround_days"] == 14
    assert data["description"] == "Updated Description"
    assert data["active"] == True

def test_update_cro_service_not_found(client, admin_token_headers):
    """Test updating a non-existent CRO service"""
    random_id = uuid.uuid4()
    update_data = {
        "description": "Updated Description",
        "base_price": 1200.0
    }
    response = client.put(f"{API_PREFIX}/cro/{random_id}", json=update_data, headers=admin_token_headers)
    assert response.status_code == 404
    data = response.json()
    assert data["message"] == f"CRO service with ID {random_id} not found"

def test_update_cro_service_unauthorized(client, pharma_token_headers, db_session):
    """Test unauthorized update of CRO service"""
    service = create_test_cro_service(db_session, "Service 1", "Provider A", ServiceType.BINDING_ASSAY, 1000.0, 14, "Description 1", True)
    db_session.commit()

    update_data = {
        "description": "Updated Description",
        "base_price": 1200.0
    }
    response = client.put(f"{API_PREFIX}/cro/{service.id}", json=update_data, headers=pharma_token_headers)
    assert response.status_code == 403
    data = response.json()
    assert data["message"] == "Admin privileges required"

def test_update_cro_service_specifications(client, admin_token_headers, db_session):
    """Test updating specifications for a CRO service"""
    service = create_test_cro_service(db_session, "Service 1", "Provider A", ServiceType.BINDING_ASSAY, 1000.0, 14, "Description 1", True)
    db_session.commit()

    specifications_data = {
        "assay_type": "Radioligand Binding",
        "target": "5-HT2A Receptor"
    }
    response = client.patch(f"{API_PREFIX}/cro/{service.id}/specifications", json=specifications_data, headers=admin_token_headers)
    assert response.status_code == 200

    data = response.json()
    assert data["specifications"] == specifications_data

def test_activate_cro_service(client, admin_token_headers, db_session):
    """Test activating a CRO service"""
    service = create_test_cro_service(db_session, "Service 1", "Provider A", ServiceType.BINDING_ASSAY, 1000.0, 14, "Description 1", False)
    db_session.commit()

    response = client.post(f"{API_PREFIX}/cro/{service.id}/activate", headers=admin_token_headers)
    assert response.status_code == 200

    data = response.json()
    assert data["active"] == True

def test_deactivate_cro_service(client, admin_token_headers, db_session):
    """Test deactivating a CRO service"""
    service = create_test_cro_service(db_session, "Service 1", "Provider A", ServiceType.BINDING_ASSAY, 1000.0, 14, "Description 1", True)
    db_session.commit()

    response = client.post(f"{API_PREFIX}/cro/{service.id}/deactivate", headers=admin_token_headers)
    assert response.status_code == 200

    data = response.json()
    assert data["active"] == False

def test_delete_cro_service(client, admin_token_headers, db_session):
    """Test deleting a CRO service"""
    service = create_test_cro_service(db_session, "Service 1", "Provider A", ServiceType.BINDING_ASSAY, 1000.0, 14, "Description 1", True)
    db_session.commit()

    response = client.delete(f"{API_PREFIX}/cro/{service.id}", headers=admin_token_headers)
    assert response.status_code == 200
    data = response.json()
    assert data["message"] == "CRO service deleted successfully"

@unittest.mock.patch('src.backend.app.services.cro_service.delete_cro_service')
def test_delete_cro_service_with_submissions(mock_delete_cro_service, client, admin_token_headers, db_session):
    """Test deleting a CRO service that has associated submissions"""
    service = create_test_cro_service(db_session, "Service 1", "Provider A", ServiceType.BINDING_ASSAY, 1000.0, 14, "Description 1", True)
    db_session.commit()

    mock_delete_cro_service.side_effect = ConflictException("Cannot delete service with existing submissions")

    response = client.delete(f"{API_PREFIX}/cro/{service.id}", headers=admin_token_headers)
    assert response.status_code == 409
    data = response.json()
    assert data["message"] == "Cannot delete service with existing submissions"

def test_get_service_types(client, pharma_token_headers):
    """Test retrieving available CRO service types"""
    response = client.get(f"{API_PREFIX}/cro/types", headers=pharma_token_headers)
    assert response.status_code == 200

    data = response.json()
    assert isinstance(data, list)
    assert len(data) > 0
    assert {"id": "BINDING_ASSAY", "name": "BINDING_ASSAY"} in data
    assert {"id": "ADME", "name": "ADME"} in data

def test_get_service_type_counts(client, pharma_token_headers, db_session):
    """Test retrieving count of services grouped by service type"""
    create_test_cro_service(db_session, "Service 1", "Provider A", ServiceType.BINDING_ASSAY, 1000.0, 14, "Description 1", True)
    create_test_cro_service(db_session, "Service 2", "Provider B", ServiceType.BINDING_ASSAY, 1500.0, 21, "Description 2", False)
    create_test_cro_service(db_session, "Service 3", "Provider C", ServiceType.ADME, 2000.0, 28, "Description 3", True)
    db_session.commit()

    response = client.get(f"{API_PREFIX}/cro/stats/by-type", headers=pharma_token_headers)
    assert response.status_code == 200

    data = response.json()
    assert isinstance(data, list)
    assert len(data) > 0
    assert {"service_type": "BINDING_ASSAY", "count": 2} in data
    assert {"service_type": "ADME", "count": 1} in data

def test_get_service_provider_counts(client, pharma_token_headers, db_session):
    """Test retrieving count of services grouped by provider"""
    create_test_cro_service(db_session, "Service 1", "Provider A", ServiceType.BINDING_ASSAY, 1000.0, 14, "Description 1", True)
    create_test_cro_service(db_session, "Service 2", "Provider A", ServiceType.ADME, 1500.0, 21, "Description 2", False)
    create_test_cro_service(db_session, "Service 3", "Provider B", ServiceType.BINDING_ASSAY, 2000.0, 28, "Description 3", True)
    db_session.commit()

    response = client.get(f"{API_PREFIX}/cro/stats/by-provider", headers=pharma_token_headers)
    assert response.status_code == 200

    data = response.json()
    assert isinstance(data, list)
    assert len(data) > 0
    assert {"provider": "Provider A", "count": 2} in data
    assert {"provider": "Provider B", "count": 1} in data