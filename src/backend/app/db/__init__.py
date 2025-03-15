"""
Database package initialization module for the Molecular Data Management and CRO Integration Platform.
This file exports essential database components and provides a clean interface for database access throughout the application.
"""

# Import the SQLAlchemy declarative base class
from .base_class import Base  # Import the SQLAlchemy declarative base class

# Import SQLAlchemy engine for database operations
from .session import engine  # Import SQLAlchemy engine for database operations

# Import session factory for database operations
from .session import SessionLocal  # Import session factory for database operations

# Import thread-local session for database operations
from .session import db_session  # Import thread-local session for database operations

# Import dependency function for FastAPI to get a database session
from .session import get_db  # Import dependency function for FastAPI to get a database session

# Import database initialization function
from .init_db import init_db  # Import database initialization function

# Import function to create database tables
from .init_db import create_tables  # Import function to create database tables

# Import function to seed database with initial data
from .init_db import seed_db  # Import function to seed database with initial data

__all__ = [
    "Base",
    "engine",
    "SessionLocal",
    "db_session",
    "get_db",
    "init_db",
    "create_tables",
    "seed_db",
]