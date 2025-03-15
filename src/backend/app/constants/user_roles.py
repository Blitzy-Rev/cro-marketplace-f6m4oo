"""
User role constants and role hierarchy for the Molecular Data Management and CRO Integration Platform.

This module defines the role-based access control system used throughout the application for
authorization and permission management. It establishes the available roles and the hierarchy
between them, which is used to determine permission inheritance.
"""
from typing import Dict, List

# Individual role constants
SYSTEM_ADMIN = "system_admin"  # Highest level administrator with full system access
PHARMA_ADMIN = "pharma_admin"  # Pharmaceutical company administrator
PHARMA_SCIENTIST = "pharma_scientist"  # Pharmaceutical scientist/researcher
CRO_ADMIN = "cro_admin"  # Contract Research Organization administrator
CRO_TECHNICIAN = "cro_technician"  # CRO laboratory technician
AUDITOR = "auditor"  # Compliance auditor with read-only access

# Default role for new users
DEFAULT_ROLE = PHARMA_SCIENTIST

# Complete list of all available roles
ALL_ROLES = [SYSTEM_ADMIN, PHARMA_ADMIN, PHARMA_SCIENTIST, CRO_ADMIN, CRO_TECHNICIAN, AUDITOR]

# Role hierarchy defines which roles include permissions of other roles
# Key: role, Value: list of roles whose permissions this role inherits
ROLE_HIERARCHY: Dict[str, List[str]] = {
    SYSTEM_ADMIN: [PHARMA_ADMIN, CRO_ADMIN, PHARMA_SCIENTIST, CRO_TECHNICIAN, AUDITOR],
    PHARMA_ADMIN: [PHARMA_SCIENTIST],
    CRO_ADMIN: [CRO_TECHNICIAN],
    PHARMA_SCIENTIST: [],
    CRO_TECHNICIAN: [],
    AUDITOR: []
}

# Role groupings for convenience
PHARMA_ROLES = [PHARMA_ADMIN, PHARMA_SCIENTIST]
CRO_ROLES = [CRO_ADMIN, CRO_TECHNICIAN]
ADMIN_ROLES = [SYSTEM_ADMIN, PHARMA_ADMIN, CRO_ADMIN]