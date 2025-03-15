"""
Alembic migration environment configuration for the Molecular Data Management and CRO Integration Platform.

This file configures the database connection, metadata, and migration context for Alembic to generate
and run database migrations. It integrates with the application's SQLAlchemy models to ensure schema
changes are properly tracked and applied.
"""

import logging

from alembic import context
from alembic.config import from_config
from sqlalchemy import engine_from_config, pool, create_engine

# Import application metadata and config
from ..base import Base  # Import SQLAlchemy models metadata for migration generation
from ...core.config import settings  # Import database configuration settings

# Create logger
logger = logging.getLogger("alembic")

# Access Alembic config
config = context.config

# Set the metadata target for the migrations
target_metadata = Base.metadata

def get_database_url():
    """
    Get the database URL from Alembic config or application settings.
    
    Returns:
        str: Database connection URL
    """
    # Check if set in Alembic config
    url = config.get_main_option("sqlalchemy.url")
    if not url:
        # If not, use the URL from application settings
        url = str(settings.DATABASE_URL)
    return url

def run_migrations_offline():
    """
    Run migrations in 'offline' mode, generating SQL scripts without connecting to the database.
    
    This function generates SQL scripts that can be run manually, particularly in production
    environments where direct database access might be restricted.
    """
    url = get_database_url()
    context.configure(
        url=url,
        target_metadata=target_metadata,
        literal_binds=True,
        dialect_opts={"paramstyle": "named"},
    )

    with context.begin_transaction():
        context.run_migrations()

def run_migrations_online():
    """
    Run migrations in 'online' mode, directly applying changes to the connected database.
    
    This function connects to the database, compares the current schema with the target metadata,
    and applies any necessary changes to bring the database schema up to date.
    """
    # Get database connection URL and parameters
    url = get_database_url()
    connection_params = settings.get_database_connection_parameters()
    
    # Create engine with application connection parameters
    engine = create_engine(
        url,
        poolclass=pool.NullPool,
        **connection_params
    )
    
    with engine.connect() as connection:
        context.configure(
            connection=connection,
            target_metadata=target_metadata,
            compare_type=True,  # Compare column types during migrations
            compare_server_default=True,  # Compare default values
            # PostgreSQL-specific config
            include_schemas=True,  # Include schema support for PostgreSQL
        )

        with context.begin_transaction():
            context.run_migrations()

# Check if running in offline or online mode
if context.is_offline_mode():
    logger.info("Running migrations offline")
    run_migrations_offline()
else:
    logger.info("Running migrations online")
    run_migrations_online()