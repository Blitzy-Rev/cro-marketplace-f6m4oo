"""
Initialization file for the API test package in the Molecular Data Management and CRO Integration Platform.

This module marks the api directory as a Python package, enabling proper import resolution for API test modules
and provides common test utilities and fixtures specific to API testing.
"""

import pytest  # pytest 7.0.0

# Version identifier for the API test suite
API_TEST_VERSION = "0.1.0"


def setup_api_test_fixtures():
    """
    Helper function to set up common fixtures for API tests.
    
    Returns:
        dict: Dictionary of common test data and configurations
    """
    # Define common test data like valid SMILES strings
    valid_smiles = [
        "CC(C)CCO",        # Isopentanol
        "c1ccccc1",        # Benzene
        "CCN(CC)CC",       # Triethylamine
        "CC(=O)O",         # Acetic acid
        "C1CCCCC1",        # Cyclohexane
    ]
    
    invalid_smiles = [
        "CC(C)CCQ",        # Invalid atom 'Q'
        "c1ccccc",         # Incomplete aromatic ring
        "CC(=O)(=O)",      # Too many double bonds
    ]
    
    # Define common test configurations
    test_configs = {
        "api_version": "v1",
        "timeout": 5,
        "batch_size": 10,
    }
    
    # Return dictionary with test data and configurations
    return {
        "valid_smiles": valid_smiles,
        "invalid_smiles": invalid_smiles,
        "test_configs": test_configs,
    }