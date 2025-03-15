"""
Initialization file for the services module that exports all service classes and functions for the Molecular Data Management and CRO Integration Platform.
This file serves as the central entry point for accessing service layer functionality throughout the application.
"""

# Molecule-related services
from .molecule_service import MoleculeService, molecule_service

# Library-related services
from .library_service import LibraryService, library_service

# Document-related services and exceptions
from .document_service import DocumentService, DocumentServiceException

# Authentication-related functions
from .auth_service import (
    authenticate_user,
    register_user,
    confirm_registration,
    refresh_token,
    get_current_user,
    get_user_permissions,
    change_password,
    forgot_password,
    reset_password,
    setup_mfa,
    verify_mfa_setup,
    sign_out,
)

# CRO-related functions
from .cro_service import (
    get_cro_service,
    get_cro_service_by_name,
    list_cro_services,
    list_active_cro_services,
    create_cro_service,
    update_cro_service,
    update_cro_service_specifications,
    activate_cro_service,
    deactivate_cro_service,
    delete_cro_service,
    get_service_types,
    search_cro_services,
    get_service_counts_by_type,
    get_service_counts_by_provider,
)

# Export all service classes and instances
__all__ = [
    "MoleculeService",
    "molecule_service",
    "LibraryService",
    "library_service",
    "DocumentService",
    "DocumentServiceException",
    "authenticate_user",
    "register_user",
    "confirm_registration",
    "refresh_token",
    "get_current_user",
    "get_user_permissions",
    "change_password",
    "forgot_password",
    "reset_password",
    "setup_mfa",
    "verify_mfa_setup",
    "sign_out",
    "get_cro_service",
    "get_cro_service_by_name",
    "list_cro_services",
    "list_active_cro_services",
    "create_cro_service",
    "update_cro_service",
    "update_cro_service_specifications",
    "activate_cro_service",
    "deactivate_cro_service",
    "delete_cro_service",
    "get_service_types",
    "search_cro_services",
    "get_service_counts_by_type",
    "get_service_counts_by_provider",
]