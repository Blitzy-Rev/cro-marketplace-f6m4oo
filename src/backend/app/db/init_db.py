"""
Database initialization module for the Molecular Data Management and CRO Integration Platform.

This module provides functionality to create initial database tables, seed the database with
required data, and create a default superuser account. It is used during application startup
and for testing environments.
"""

import logging
from sqlalchemy import inspect

# Import all models to ensure they are registered with SQLAlchemy
from .base import Base
from .session import engine, db_session
from ..core.config import settings
from ..crud.crud_user import user
from ..crud.crud_cro_service import cro_service
from ..schemas.user import UserCreate
from ..schemas.cro_service import CROServiceCreate
from ..constants.user_roles import SYSTEM_ADMIN

# Configure module logger
logger = logging.getLogger(__name__)

# Initial CRO services to be created if they don't exist
INITIAL_CRO_SERVICES = [
    {
        'name': 'Binding Assay',
        'description': 'Radioligand binding assay for target protein interactions',
        'provider': 'BioCRO Inc.',
        'active': True
    },
    {
        'name': 'ADME Panel',
        'description': 'Comprehensive ADME property testing panel',
        'provider': 'PharmaTest Labs',
        'active': True
    },
    {
        'name': 'Solubility Testing',
        'description': 'Aqueous solubility determination',
        'provider': 'BioCRO Inc.',
        'active': True
    },
    {
        'name': 'Metabolic Stability',
        'description': 'In vitro metabolic stability assessment',
        'provider': 'MetaboCRO',
        'active': True
    },
    {
        'name': 'Toxicity Screening',
        'description': 'In vitro toxicity and safety screening',
        'provider': 'SafetyScreen CRO',
        'active': True
    }
]


def init_db():
    """Initialize the database with tables and seed data."""
    logger.info("Initializing database")
    create_tables()
    seed_db()
    logger.info("Database initialization completed successfully")


def create_tables():
    """Create all database tables defined in the models."""
    logger.info("Creating database tables")
    
    # Create all tables in the metadata
    inspector = inspect(engine)
    existing_tables = inspector.get_table_names()
    
    if not existing_tables:
        Base.metadata.create_all(engine)
        logger.info("All database tables created successfully")
    else:
        logger.info(f"Database already contains tables: {existing_tables}")


def seed_db():
    """Seed the database with initial required data."""
    logger.info("Seeding database with initial data")
    
    # Create initial superuser
    create_first_superuser()
    
    # Create initial CRO services
    create_initial_cro_services()
    
    logger.info("Database seeding completed successfully")


def create_first_superuser():
    """Create the initial superuser account if it doesn't exist."""
    logger.info("Creating first superuser")
    
    # Check if superuser email is configured
    if not settings.FIRST_SUPERUSER_EMAIL:
        logger.warning("Superuser email not configured. Skipping superuser creation.")
        return
    
    # Check if superuser already exists
    db_user = user.get_by_email(settings.FIRST_SUPERUSER_EMAIL, db=db_session)
    if db_user:
        logger.info(f"Superuser with email {settings.FIRST_SUPERUSER_EMAIL} already exists")
        return
    
    # Create superuser
    user_in = UserCreate(
        email=settings.FIRST_SUPERUSER_EMAIL,
        password=settings.FIRST_SUPERUSER_PASSWORD,
        full_name=settings.FIRST_SUPERUSER_NAME,
        role=SYSTEM_ADMIN,
        is_superuser=True
    )
    
    try:
        created_user = user.create(user_in, db=db_session)
        logger.info(f"Superuser created successfully: {created_user.email}")
    except Exception as e:
        logger.error(f"Failed to create superuser: {str(e)}")


def create_initial_cro_services():
    """Create initial CRO services if they don't exist."""
    logger.info("Creating initial CRO services")
    
    # Iterate through initial services
    for service_data in INITIAL_CRO_SERVICES:
        # Check if service already exists by name
        db_service = cro_service.get_by_name(service_data['name'], db=db_session)
        if db_service:
            logger.info(f"CRO service '{service_data['name']}' already exists")
            continue
        
        # Create schema from service data
        try:
            # Add required service_type field based on service name
            if 'Binding Assay' in service_data['name']:
                service_data['service_type'] = 'BINDING_ASSAY'
            elif 'ADME' in service_data['name']:
                service_data['service_type'] = 'ADME'
            elif 'Solubility' in service_data['name']:
                service_data['service_type'] = 'SOLUBILITY'
            elif 'Metabolic' in service_data['name']:
                service_data['service_type'] = 'METABOLIC_STABILITY'
            elif 'Toxicity' in service_data['name']:
                service_data['service_type'] = 'TOXICITY'
            else:
                service_data['service_type'] = 'CUSTOM'
            
            # Add required base_price and typical_turnaround_days if not present
            if 'base_price' not in service_data:
                service_data['base_price'] = 1000.0
            
            if 'typical_turnaround_days' not in service_data:
                service_data['typical_turnaround_days'] = 14
                
            if 'price_currency' not in service_data:
                service_data['price_currency'] = 'USD'
                
            service_in = CROServiceCreate(**service_data)
            
            # Create service
            created_service = cro_service.create(service_in, db=db_session)
            logger.info(f"Created CRO service: {created_service.name}")
            
        except Exception as e:
            logger.error(f"Failed to create CRO service '{service_data['name']}': {str(e)}")