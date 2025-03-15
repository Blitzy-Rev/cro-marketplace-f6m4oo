"""
Centralizes imports and exports of all SQLAlchemy models for the Molecular Data Management and CRO Integration Platform.

This file serves as the public API for the models package, making all model classes available to other parts
of the application through a single import point.
"""

# User models for authentication and user management
from .user import User

# Molecule models for molecular data management
from .molecule import (
    Molecule,
    MoleculeStatus,
    library_molecule,
    molecule_property
)

# Library model for molecule organization
from .library import Library

# CRO service models
from .cro_service import CROService

# Document models for document management
from .document import Document

# Submission models for CRO submissions
from .submission import (
    Submission,
    SubmissionStatus,
    submission_molecule
)

# Prediction models for AI property predictions
from .prediction import Prediction

# Result models for experimental results
from .result import (
    Result,
    ResultProperty
)

# Audit model for system audit logging
from .audit import Audit

# Re-export all models for use in other modules
__all__ = [
    'User',
    'Molecule',
    'MoleculeStatus',
    'library_molecule',
    'molecule_property',
    'Library',
    'CROService',
    'Document',
    'Submission',
    'SubmissionStatus',
    'submission_molecule',
    'Prediction',
    'Result',
    'ResultProperty',
    'Audit'
]