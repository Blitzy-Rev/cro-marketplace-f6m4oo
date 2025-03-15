import pytest
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from fastapi.testclient import TestClient
from typing import Dict

from ..app.main import app
from ..app.db.base import Base
from ..app.api.deps import get_db
from ..app.core.config import settings
from ..app.models.user import User
from ..app.models.molecule import Molecule
from ..app.models.library import Library
from ..app.models.cro_service import CROService
from ..constants.user_roles import SYSTEM_ADMIN, PHARMA_ADMIN, PHARMA_SCIENTIST, CRO_ADMIN
from passlib.context import CryptContext  # passlib version: ^1.7.4
import uuid
from datetime import datetime
import os

# Define a global password context for hashing passwords
pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")

# Define a test database URL, using in-memory SQLite for testing
TEST_DATABASE_URL = "sqlite:///./test.db"

@pytest.fixture(scope="session")
def get_test_db_url() -> str:
    """Get the database URL for testing, using in-memory SQLite by default"""
    # Check if TEST_DATABASE_URL environment variable is set
    test_db_url = os.environ.get("TEST_DATABASE_URL")
    if test_db_url:
        # If set, return the environment variable value
        return test_db_url
    else:
        # Otherwise, return the default in-memory SQLite URL
        return TEST_DATABASE_URL

# Create a SQLAlchemy engine for the test database
engine = create_engine(TEST_DATABASE_URL, connect_args={"check_same_thread": False})

# Create a session factory for creating database sessions
TestingSessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)

@pytest.fixture(scope="session")
def test_db_session():
    """Fixture providing a database session for tests"""
    # Create all tables in the test database
    Base.metadata.create_all(bind=engine)
    db = TestingSessionLocal()
    try:
        yield db
    finally:
        db.close()

@pytest.fixture()
def client(test_db_session):
    """Fixture providing a TestClient for API testing"""
    def override_get_db():
        try:
            yield test_db_session
        finally:
            test_db_session.close()

    app.dependency_overrides[get_db] = override_get_db
    yield TestClient(app)
    app.dependency_overrides.clear()

@pytest.fixture()
def test_db(test_db_session):
    """Fixture setting up and tearing down the test database"""
    # Set up the test database with tables and initial test data
    Base.metadata.create_all(bind=engine)
    db = TestingSessionLocal()
    try:
        # Create all tables defined in Base.metadata
        Base.metadata.create_all(bind=engine)
        # Create a database session
        db = TestingSessionLocal()
        # Add test users with different roles
        create_test_user(db, "system_admin@example.com", "password", "System Admin", SYSTEM_ADMIN)
        create_test_user(db, "pharma_admin@example.com", "password", "Pharma Admin", PHARMA_ADMIN)
        create_test_user(db, "pharma_scientist@example.com", "password", "Pharma Scientist", PHARMA_SCIENTIST)
        create_test_user(db, "cro_admin@example.com", "password", "CRO Admin", CRO_ADMIN)
        # Add test CRO services
        create_test_cro_services(db)
        # Add test molecules with properties
        create_test_molecules(db, 5)
        # Add test libraries
        molecules = db.query(Molecule).all()
        user = db.query(User).filter(User.email == "pharma_admin@example.com").first()
        create_test_libraries(db, user, molecules)
        # Commit the session
        db.commit()
        # Close the session
        db.close()
        yield
    finally:
        # Drop all tables after the test is finished
        Base.metadata.drop_all(bind=engine)

@pytest.fixture()
def test_user(test_db_session):
    """Fixture providing a standard test user"""
    # Create a test user with specified role and credentials
    return create_test_user(test_db_session, "test_user@example.com", "password", "Test User", PHARMA_SCIENTIST)

@pytest.fixture()
def test_admin_user(test_db_session):
    """Fixture providing an admin test user"""
    # Create a test user with specified role and credentials
    return create_test_user(test_db_session, "test_admin@example.com", "password", "Test Admin", SYSTEM_ADMIN)

@pytest.fixture()
def test_molecules(test_db_session):
    """Fixture providing test molecules"""
    # Create test molecules with properties for testing
    return create_test_molecules(test_db_session, 3)

@pytest.fixture()
def test_libraries(test_db_session, test_user, test_molecules):
    """Fixture providing test libraries"""
    # Create test libraries with molecules for testing
    return create_test_libraries(test_db_session, test_user, test_molecules)

@pytest.fixture()
def test_cro_services(test_db_session):
    """Fixture providing test CRO services"""
    # Create test CRO services for testing
    return create_test_cro_services(test_db_session)

@pytest.fixture()
def auth_headers(client, test_user):
    """Fixture providing authentication headers for API requests"""
    # Authenticate the test user and return the authorization headers
    login_data = {
        "username": test_user.email,
        "password": "password"
    }
    response = client.post("/api/v1/auth/login", data=login_data)
    assert response.status_code == 200
    token = response.json()["access_token"]
    headers = {"Authorization": f"Bearer {token}"}
    return headers

def create_test_user(db, email, password, name, role):
    """Create a test user with specified role and credentials"""
    # Create a new User object with provided details
    user = User(
        email=email,
        full_name=name,
        hashed_password=pwd_context.hash(password),
        role=role,
        is_active=True
    )
    # Hash the password using pwd_context
    user.hashed_password = pwd_context.hash(password)
    # Set user as active
    user.is_active = True
    # Add user to database session
    db.add(user)
    # Return the created user object
    return user

def create_test_molecules(db, count):
    """Create test molecules with properties for testing"""
    # Create a list to store created molecules
    molecules = []
    # Generate 'count' number of test molecules with valid SMILES
    for i in range(count):
        molecule = Molecule(
            smiles=f"CC(=O)Oc1ccccc1C(=O)O{i}",
            inchi_key=f"InChIKey=ABCDEFGHIJKLMNOPQRSTUVWY{i}",
            molecular_weight=180.16,
            formula="C9H8O4",
            created_at=datetime.now(),
            created_by=None
        )
        # Add properties to each molecule (MW, LogP, etc.)
        # Add molecules to database session
        db.add(molecule)
        molecules.append(molecule)
    # Return the list of created molecules
    return molecules

def create_test_libraries(db, user, molecules):
    """Create test libraries with molecules for testing"""
    # Create test libraries with names and descriptions
    libraries = []
    for i in range(2):
        library = Library(
            name=f"Library {i+1}",
            description=f"Test Library {i+1} Description",
            owner_id=user.id,
            created_at=datetime.now()
        )
        # Associate molecules with libraries
        library.molecules.extend(molecules)
        # Set the owner to the provided user
        library.owner = user
        # Add libraries to database session
        db.add(library)
        libraries.append(library)
    # Return the list of created libraries
    return libraries

def create_test_cro_services(db):
    """Create test CRO services for testing"""
    # Create standard CRO services (Binding Assay, ADME Panel, etc.)
    services = []
    service1 = CROService(
        name="Binding Assay",
        description="Radioligand binding assay for target protein interactions",
        provider="BioCRO Inc.",
        service_type=ServiceType.BINDING_ASSAY,
        base_price=1000.00,
        price_currency="USD",
        typical_turnaround_days=14,
        active=True
    )
    service2 = CROService(
        name="ADME Panel",
        description="Comprehensive ADME property testing panel",
        provider="PharmaTest Labs",
        service_type=ServiceType.ADME,
        base_price=1500.00,
        price_currency="USD",
        typical_turnaround_days=21,
        active=True
    )
    # Set service details including provider and description
    # Add services to database session
    db.add(service1)
    db.add(service2)
    services.append(service1)
    services.append(service2)
    # Return the list of created services
    return services