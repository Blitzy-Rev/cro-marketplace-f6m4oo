"""
SMILES Utility Tests Module

This module contains unit tests for the SMILES utility functions that handle molecular
structure validation, standardization, and conversion operations. These tests ensure the
reliability of core molecular data processing functionality.

The tests validate critical functionality for:
- SMILES string validation and standardization
- Conversion between SMILES, InChI, and other molecular representations
- Molecular equivalence comparison
- Property and descriptor generation
"""

import pytest  # pytest version ^7.0.0
import re  # standard library

from ../../app/utils/smiles import validate_smiles
from ../../app/utils/smiles import standardize_smiles
from ../../app/utils/smiles import canonicalize_smiles
from ../../app/utils/smiles import get_inchi_from_smiles
from ../../app/utils/smiles import get_inchi_key_from_smiles
from ../../app/utils/smiles import get_molecular_formula_from_smiles
from ../../app/utils/smiles import are_same_molecule
from ../../app/utils/smiles import get_smiles_from_inchi
from ../../app/utils/smiles import sanitize_smiles
from ../../app/utils/smiles import get_smiles_complexity
from ../../app/core/exceptions import MoleculeException
from ../../app/constants/error_messages import MOLECULE_ERRORS

# Test data - Valid SMILES examples covering different chemical structures
VALID_SMILES_EXAMPLES = [
    "C",                # Methane
    "CC",               # Ethane
    "CCO",              # Ethanol
    "c1ccccc1",         # Benzene
    "CC(=O)O",          # Acetic acid
    "C1CCCCC1",         # Cyclohexane
    "N#C",              # Hydrogen cyanide
    "CCN(CC)CC",        # Triethylamine
    "CC(C)CCO",         # Isopentanol
    "C1=CC=C(C=C1)C(=O)O"  # Benzoic acid
]

# Test data - Invalid SMILES examples
INVALID_SMILES_EXAMPLES = [
    "X",                # Invalid atom
    "C:C",              # Invalid bond
    "C(C",              # Unclosed parenthesis
    "1CCCCC1",          # Invalid ring closure
    "C%C",              # Invalid character
    "C##C",             # Invalid triple bond representation
    "C1CC2",            # Incomplete ring closure
    "",                 # Empty string
    " ",                # Whitespace only
    None                # None value
]

# Test data - Pairs of SMILES strings representing the same molecule
EQUIVALENT_SMILES_PAIRS = [
    ("CCO", "OCC"),                 # Ethanol - different atom order
    ("c1ccccc1", "C1=CC=CC=C1"),    # Benzene - aromatic vs. kekulized
    ("CC(=O)O", "CC(O)=O")          # Acetic acid - resonance forms
]

# Test data - SMILES strings with their corresponding InChI representations
INCHI_TEST_CASES = [
    ("CCO", "InChI=1S/C2H6O/c1-2-3/h3H,2H2,1H3"),               # Ethanol
    ("c1ccccc1", "InChI=1S/C6H6/c1-2-4-6-5-3-1/h1-6H")          # Benzene
]


def test_validate_smiles_valid_examples():
    """Tests that validate_smiles correctly identifies valid SMILES strings."""
    for smiles in VALID_SMILES_EXAMPLES:
        assert validate_smiles(smiles) is True, f"Expected {smiles} to be valid"
    
    # Ensure all valid examples pass validation
    assert all(validate_smiles(smiles) for smiles in VALID_SMILES_EXAMPLES)


def test_validate_smiles_invalid_examples():
    """Tests that validate_smiles correctly identifies invalid SMILES strings."""
    for smiles in INVALID_SMILES_EXAMPLES:
        assert validate_smiles(smiles) is False, f"Expected {smiles} to be invalid"
    
    # Ensure all invalid examples fail validation
    assert all(not validate_smiles(smiles) for smiles in INVALID_SMILES_EXAMPLES)


def test_standardize_smiles_valid():
    """Tests that standardize_smiles correctly standardizes valid SMILES strings."""
    for smiles in VALID_SMILES_EXAMPLES:
        standardized = standardize_smiles(smiles)
        assert standardized, "Standardized SMILES should not be empty"
        assert validate_smiles(standardized), f"Standardized SMILES {standardized} should be valid"


def test_standardize_smiles_invalid():
    """Tests that standardize_smiles raises MoleculeException for invalid SMILES."""
    for smiles in INVALID_SMILES_EXAMPLES:
        if smiles is not None:  # Skip None as it's handled separately
            with pytest.raises(MoleculeException) as excinfo:
                standardize_smiles(smiles)
            assert str(excinfo.value) == MOLECULE_ERRORS["INVALID_SMILES"]


def test_canonicalize_smiles_valid():
    """Tests that canonicalize_smiles correctly produces canonical SMILES."""
    for smiles in VALID_SMILES_EXAMPLES:
        canonical = canonicalize_smiles(smiles)
        assert canonical, "Canonical SMILES should not be empty"
        
        # Canonicalization should be idempotent - running it twice should give the same result
        assert canonicalize_smiles(canonical) == canonical, "Canonicalization should be idempotent"


def test_canonicalize_smiles_invalid():
    """Tests that canonicalize_smiles raises MoleculeException for invalid SMILES."""
    for smiles in INVALID_SMILES_EXAMPLES:
        if smiles is not None:  # Skip None as it's handled separately
            with pytest.raises(MoleculeException) as excinfo:
                canonicalize_smiles(smiles)
            assert str(excinfo.value) == MOLECULE_ERRORS["INVALID_SMILES"]


def test_get_inchi_from_smiles():
    """Tests that get_inchi_from_smiles correctly generates InChI strings."""
    for smiles, expected_inchi in INCHI_TEST_CASES:
        inchi = get_inchi_from_smiles(smiles)
        assert inchi == expected_inchi, f"Expected InChI {expected_inchi}, got {inchi}"


def test_get_inchi_key_from_smiles():
    """Tests that get_inchi_key_from_smiles correctly generates InChI Keys."""
    for smiles in VALID_SMILES_EXAMPLES:
        inchi_key = get_inchi_key_from_smiles(smiles)
        assert inchi_key, "InChI Key should not be empty"
        
        # InChI Keys are always 27 characters with a specific format
        assert len(inchi_key) == 27, "InChI Key should be 27 characters long"
        assert re.match(r'^[A-Z]{14}-[A-Z]{10}-[A-Z]$', inchi_key), f"Invalid InChI Key format: {inchi_key}"


def test_get_molecular_formula_from_smiles():
    """Tests that get_molecular_formula_from_smiles correctly generates molecular formulas."""
    # Test specific molecules with known formulas
    assert get_molecular_formula_from_smiles("CCO") == "C2H6O", "Ethanol formula should be C2H6O"
    assert get_molecular_formula_from_smiles("c1ccccc1") == "C6H6", "Benzene formula should be C6H6"
    assert get_molecular_formula_from_smiles("CC(=O)O") == "C2H4O2", "Acetic acid formula should be C2H4O2"


def test_are_same_molecule():
    """Tests that are_same_molecule correctly identifies equivalent SMILES representations."""
    # Test equivalent SMILES pairs
    for smiles1, smiles2 in EQUIVALENT_SMILES_PAIRS:
        assert are_same_molecule(smiles1, smiles2), f"{smiles1} and {smiles2} should be identified as the same molecule"
    
    # Test non-equivalent SMILES
    assert not are_same_molecule("CCO", "CCC"), "Ethanol and propane should not be the same molecule"
    assert not are_same_molecule("c1ccccc1", "c1ccccc1C"), "Benzene and toluene should not be the same molecule"


def test_get_smiles_from_inchi():
    """Tests that get_smiles_from_inchi correctly converts InChI to SMILES."""
    for expected_smiles, inchi in INCHI_TEST_CASES:
        smiles = get_smiles_from_inchi(inchi)
        assert are_same_molecule(smiles, expected_smiles), \
            f"SMILES generated from InChI should represent the same molecule: {smiles} vs {expected_smiles}"


def test_sanitize_smiles():
    """Tests that sanitize_smiles correctly fixes common SMILES formatting issues."""
    # Test with whitespace
    assert validate_smiles(sanitize_smiles(" CCO ")), "Sanitized SMILES with whitespace should be valid"
    
    # Test with different representations
    assert validate_smiles(sanitize_smiles("C1=CC=CC=C1")), "Sanitized kekulized benzene should be valid"
    assert validate_smiles(sanitize_smiles("c1ccccc1")), "Sanitized aromatic benzene should be valid"
    
    # Test exception for invalid SMILES
    with pytest.raises(MoleculeException) as excinfo:
        sanitize_smiles("X")
    assert str(excinfo.value) == MOLECULE_ERRORS["INVALID_SMILES"]


def test_get_smiles_complexity():
    """Tests that get_smiles_complexity correctly calculates molecular complexity."""
    # Simpler molecules should have lower complexity
    methane_complexity = get_smiles_complexity("C")
    ethane_complexity = get_smiles_complexity("CC")
    benzene_complexity = get_smiles_complexity("c1ccccc1")
    
    # Check that complexity scores are positive
    assert methane_complexity > 0, "Complexity should be a positive value"
    assert ethane_complexity > 0, "Complexity should be a positive value"
    assert benzene_complexity > 0, "Complexity should be a positive value"
    
    # More complex molecules should have higher complexity scores
    assert ethane_complexity > methane_complexity, "Ethane should be more complex than methane"
    assert benzene_complexity > ethane_complexity, "Benzene should be more complex than ethane"