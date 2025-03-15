"""
Initialization file for the scripts package.

This package contains utility scripts for command-line execution related to
the Molecular Data Management and CRO Integration Platform. These scripts
support database management, system administration, and audit mechanisms.

The scripts are designed to be importable as modules while maintaining proper
Python package structure, allowing for both programmatic and CLI usage.
"""

# List of scripts exposed by this package
__all__ = [
    'create_superuser',  # Script for creating administrative users
    'seed_db',           # Script for initializing the database with seed data
    'generate_test_data', # Script for generating test data for development/testing
    'precompute_fingerprints', # Script for precomputing molecular fingerprints for faster searching
    'molecule_import'    # Script for importing molecule data from various sources
]