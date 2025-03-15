"""
Database session management module for the Molecular Data Management and CRO Integration Platform.

This module establishes the SQLAlchemy engine, session factory, and connection pooling
configuration based on application settings. It provides the core database connectivity
used throughout the application.
"""

import logging  # standard library

from sqlalchemy import create_engine  # sqlalchemy ^1.4.0
from sqlalchemy.orm import sessionmaker, scoped_session  # sqlalchemy ^1.4.0

from ..core.config import settings, get_database_connection_parameters

# Configure logger for database operations
logger = logging.getLogger(__name__)

# Create SQLAlchemy engine with connection pooling configuration
# This uses the database connection parameters from settings which include:
# - pool_size: Number of connections to keep open
# - pool_overflow: Maximum number of connections to create beyond pool_size
# - max_connections: Maximum total number of connections
engine = create_engine(
    settings.DATABASE_URL,
    **settings.get_database_connection_parameters()
)

# Create session factory for database operations
# autocommit=False: Transactions must be explicitly committed
# autoflush=False: Changes won't be automatically flushed to the database
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)

# Create thread-local scoped session for thread-safe database operations
# This ensures each thread gets its own session instance
db_session = scoped_session(SessionLocal)


def get_db():
    """
    Dependency function to get a database session for use in FastAPI endpoints.
    
    This function is intended to be used with FastAPI's dependency injection system
    to provide a database session for the lifetime of a request.
    
    Yields:
        SessionLocal: Database session that will be automatically closed after use
    """
    session = SessionLocal()
    try:
        yield session
    finally:
        # Ensure the session is closed even if an exception occurs
        session.close()


def close_db_connections():
    """
    Close all database connections in the engine pool.
    
    This function should be called during application shutdown to ensure
    all database connections are properly closed.
    
    Returns:
        None: Function performs side effects only
    """
    engine.dispose()
    logger.info("All database connections have been closed")