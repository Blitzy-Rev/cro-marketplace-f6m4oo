"""
Utilities Module for the Molecular Data Management and CRO Integration Platform.

This module provides a collection of utility functions used throughout the application
for various tasks including:
- SMILES structure validation and processing
- Data validation and verification
- CSV file parsing and processing
- File handling operations
- Pagination utilities for API endpoints
- Molecular structure handling with RDKit

These utilities support core features such as molecular data ingestion, library management,
and CRO submission workflows.
"""

# SMILES-related utilities
from .smiles import (
    validate_smiles,
    standardize_smiles,
    canonicalize_smiles,
    get_inchi_from_smiles,
    get_inchi_key_from_smiles,
)

# Validation utilities
from .validators import (
    validate_required,
    validate_string,
    validate_numeric,
    validate_email,
    validate_property_value,
    validate_molecule_properties,
)

# RDKit utilities
from .rdkit_utils import (
    smiles_to_mol,
    calculate_basic_properties,
    get_mol_image,
    get_mol_svg,
)

# CSV parsing utilities
from .csv_parser import (
    parse_csv_file,
    validate_csv_columns,
    map_csv_columns,
    CSVProcessor,
)

# File handling utilities
from .file_handlers import (
    FileHandler,
    validate_file_type,
    validate_file_size,
)

# Pagination utilities
from .pagination import (
    get_pagination_params,
    paginate_response,
)