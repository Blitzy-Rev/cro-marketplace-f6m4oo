"""
Central import file for SQLAlchemy models in the Molecular Data Management and CRO Integration Platform.

This file imports the Base class and all models to ensure they are registered with SQLAlchemy's
declarative base system. It serves as a single point of import for database initialization and
migration scripts.

Usage example:
    from app.db.base import Base, User, Molecule, ...
"""

# Import the Base class from base_class
from .base_class import Base

# Import all models to register them with SQLAlchemy
# Each model being imported here will be registered with SQLAlchemy's metadata
from ..models.user import User
from ..models.molecule import Molecule, MoleculeProperty, library_molecule, submission_molecule
from ..models.library import Library
from ..models.cro_service import CROService
from ..models.document import Document
from ..models.submission import Submission
from ..models.prediction import Prediction
from ..models.result import Result
from ..models.audit import Audit

# All imported models are automatically exported and can be imported from this module
# This single import point simplifies database initialization and migration scripts
# by providing access to all models through one import statement