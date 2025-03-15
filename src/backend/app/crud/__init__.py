# src/backend/app/crud/__init__.py
from .base import CRUDBase
from .crud_user import CRUDUser, user
from .crud_molecule import CRUDMolecule, molecule
from .crud_library import CRUDLibrary, library
from .crud_cro_service import CRUDCROService, cro_service
from .crud_document import CRUDDocument, document
from .crud_submission import CRUDSubmission, submission
from .crud_prediction import CRUDPrediction, prediction
from .crud_result import CRUDResult, result

# Classes
__all__ = [
    "CRUDBase",
    "CRUDUser",
    "CRUDMolecule",
    "CRUDLibrary",
    "CRUDCROService",
    "CRUDDocument",
    "CRUDSubmission",
    "CRUDPrediction",
    "CRUDResult",
]

# Instances
__all__ += [
    "user",
    "molecule",
    "library",
    "cro_service",
    "document",
    "submission",
    "prediction",
    "result",
]