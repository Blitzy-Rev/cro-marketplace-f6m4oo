import pytest  # pytest version: ^7.0.0
from fastapi.testclient import TestClient  # fastapi.testclient version: ^0.95.0
from fastapi import status  # fastapi version: ^0.95.0

from src.backend.app.main import app, get_app  # Import the FastAPI application
from src.backend.app.core.config import settings  # Import application settings


def test_app_creation():
    """Test that the FastAPI application is created correctly"""
    # Create a new application instance using get_app()
    test_app = get_app()

    # Verify that the application title matches settings.PROJECT_NAME
    assert test_app.title == settings.PROJECT_NAME

    # Verify that the application version matches settings.VERSION
    assert test_app.version == settings.VERSION

    # Verify that the application has the expected documentation URLs configured
    assert test_app.docs_url == '/docs'
    assert test_app.redoc_url == '/redoc'
    assert test_app.openapi_url == '/openapi.json'


def test_api_router_configuration():
    """Test that the API router is configured correctly"""
    # Create a new application instance using get_app()
    test_app = get_app()

    # Verify that the API router is included with the correct prefix
    assert any(route.path.startswith(settings.API_V1_STR) for route in test_app.routes)

    # Verify that the router contains the expected endpoints
    # This is a basic check; more detailed checks can be added
    assert any(route.path == f"{settings.API_V1_STR}/health" for route in test_app.routes)


def test_middleware_configuration():
    """Test that middleware is configured correctly"""
    # Create a new application instance using get_app()
    test_app = get_app()

    middleware_names = [middleware.cls.__name__ for middleware in test_app.user_middleware]

    # Verify that CORS middleware is configured
    assert "CORSMiddleware" in middleware_names

    # Verify that logging middleware is configured
    assert "LoggingMiddleware" in middleware_names

    # Verify that rate limiting middleware is configured
    assert "RateLimitMiddleware" in middleware_names

    # Verify that authentication middleware is configured
    assert "AuthMiddleware" in middleware_names

    # Verify that audit middleware is configured
    assert "AuditMiddleware" in middleware_names


def test_health_endpoint():
    """Test the health check endpoint"""
    # Create a test client for the FastAPI application
    client = TestClient(app)

    # Make a GET request to the health endpoint
    response = client.get("/health")

    # Verify that the response status code is 200 OK
    assert response.status_code == status.HTTP_200_OK

    # Verify that the response contains the expected health information
    data = response.json()
    assert data["status"] == "healthy"
    assert data["message"].startswith("Health check completed")

    # Verify that the application name and version are correct
    assert data["data"]["app_name"] == settings.PROJECT_NAME
    assert data["data"]["version"] == settings.VERSION

    # Verify that the database status is included and healthy
    assert data["data"]["components"]["database"]["status"] == "healthy"


def test_readiness_endpoint():
    """Test the readiness probe endpoint"""
    # Create a test client for the FastAPI application
    client = TestClient(app)

    # Make a GET request to the readiness endpoint
    response = client.get("/readiness")

    # Verify that the response status code is 200 OK
    assert response.status_code == status.HTTP_200_OK

    # Verify that the response indicates the application is ready
    data = response.json()
    assert data["ready"] is True
    assert data["message"] == "Application is ready to serve requests"


def test_liveness_endpoint():
    """Test the liveness probe endpoint"""
    # Create a test client for the FastAPI application
    client = TestClient(app)

    # Make a GET request to the liveness endpoint
    response = client.get("/liveness")

    # Verify that the response status code is 200 OK
    assert response.status_code == status.HTTP_200_OK

    # Verify that the response indicates the application is alive
    data = response.json()
    assert data["alive"] is True
    assert data["message"] == "Application is alive"


def test_docs_endpoints():
    """Test that the API documentation endpoints are accessible"""
    # Create a test client for the FastAPI application
    client = TestClient(app)

    # Make a GET request to the /docs endpoint
    response = client.get("/docs")

    # Verify that the response status code is 200 OK
    assert response.status_code == status.HTTP_200_OK

    # Make a GET request to the /redoc endpoint
    response = client.get("/redoc")

    # Verify that the response status code is 200 OK
    assert response.status_code == status.HTTP_200_OK

    # Make a GET request to the /openapi.json endpoint
    response = client.get("/openapi.json")

    # Verify that the response status code is 200 OK
    assert response.status_code == status.HTTP_200_OK

    # Verify that the OpenAPI schema contains the expected information
    data = response.json()
    assert data["info"]["title"] == settings.PROJECT_NAME
    assert data["info"]["version"] == settings.VERSION


def test_404_handler():
    """Test that the 404 error handler works correctly"""
    # Create a test client for the FastAPI application
    client = TestClient(app)

    # Make a GET request to a non-existent endpoint
    response = client.get("/nonexistent")

    # Verify that the response status code is 404 Not Found
    assert response.status_code == status.HTTP_404_NOT_FOUND

    # Verify that the response contains a properly formatted error message
    data = response.json()
    assert data["error_code"] == "http_404"
    assert data["message"] == "Not Found"