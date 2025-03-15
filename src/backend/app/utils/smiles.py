"""
SMILES Utilities Module

This module provides utility functions for handling SMILES (Simplified Molecular Input Line Entry System)
strings, which are a string notation representing molecular structures. The module offers functionality
for validating, standardizing, and converting SMILES strings, as well as calculating molecular
properties and comparing structures.

These utilities are core components for molecular structure processing throughout the application,
particularly for CSV imports, library management, and AI prediction integrations.
"""

import re
from rdkit import Chem  # RDKit version 2023.03+
from rdkit.Chem import AllChem  # RDKit version 2023.03+
from rdkit.Chem import MolStandardize  # RDKit version 2023.03+
from rdkit.Chem import inchi as rdkit_inchi  # RDKit version 2023.03+

from ..core.exceptions import MoleculeException
from ..constants.error_messages import MOLECULE_ERRORS

# Basic SMILES pattern for initial validation
# This is a simplified pattern and not a comprehensive SMILES validator
SMILES_PATTERN = re.compile(r'^[A-Za-z0-9@+\-\[\]\(\)\\/=#$.%~&!*,:]{1,}$')


def validate_smiles(smiles: str) -> bool:
    """
    Validates a SMILES string for correct format and chemical validity.
    
    Args:
        smiles: The SMILES string to validate
        
    Returns:
        True if the SMILES string is valid, False otherwise
    """
    # Check if input is None or empty
    if smiles is None or not smiles.strip():
        return False
    
    # Basic format validation with regex
    if not SMILES_PATTERN.match(smiles.strip()):
        return False
    
    # Validate using RDKit
    mol = Chem.MolFromSmiles(smiles.strip())
    
    # Check if conversion was successful and molecule has atoms
    if mol is None or mol.GetNumAtoms() == 0:
        return False
    
    return True


def standardize_smiles(smiles: str) -> str:
    """
    Standardizes a SMILES string to ensure consistent representation.
    
    Args:
        smiles: The SMILES string to standardize
        
    Returns:
        Standardized SMILES string
        
    Raises:
        MoleculeException: If the SMILES string is invalid
    """
    # Check if input is None or empty
    if smiles is None or not smiles.strip():
        raise MoleculeException(
            message=MOLECULE_ERRORS["INVALID_SMILES"],
            error_code="invalid_smiles"
        )
    
    # Convert to RDKit molecule
    mol = Chem.MolFromSmiles(smiles.strip())
    
    # Check if conversion was successful
    if mol is None:
        raise MoleculeException(
            message=MOLECULE_ERRORS["INVALID_SMILES"],
            error_code="invalid_smiles"
        )
    
    # Standardize the molecule
    clean_mol = MolStandardize.standardize_mol(mol)
    
    # Convert back to SMILES
    standardized_smiles = Chem.MolToSmiles(clean_mol)
    
    return standardized_smiles


def canonicalize_smiles(smiles: str) -> str:
    """
    Converts a SMILES string to its canonical form for consistent comparison.
    
    Args:
        smiles: The SMILES string to canonicalize
        
    Returns:
        Canonical SMILES string
        
    Raises:
        MoleculeException: If the SMILES string is invalid
    """
    # Check if input is None or empty
    if smiles is None or not smiles.strip():
        raise MoleculeException(
            message=MOLECULE_ERRORS["INVALID_SMILES"],
            error_code="invalid_smiles"
        )
    
    # Convert to RDKit molecule
    mol = Chem.MolFromSmiles(smiles.strip())
    
    # Check if conversion was successful
    if mol is None:
        raise MoleculeException(
            message=MOLECULE_ERRORS["INVALID_SMILES"],
            error_code="invalid_smiles"
        )
    
    # Convert to canonical SMILES
    canonical_smiles = Chem.MolToSmiles(mol, isomericSmiles=True, canonical=True)
    
    return canonical_smiles


def get_inchi_from_smiles(smiles: str) -> str:
    """
    Generates an InChI string from a SMILES string.
    
    Args:
        smiles: The SMILES string to convert
        
    Returns:
        InChI string
        
    Raises:
        MoleculeException: If the SMILES string is invalid
    """
    # Check if input is None or empty
    if smiles is None or not smiles.strip():
        raise MoleculeException(
            message=MOLECULE_ERRORS["INVALID_SMILES"],
            error_code="invalid_smiles"
        )
    
    # Convert to RDKit molecule
    mol = Chem.MolFromSmiles(smiles.strip())
    
    # Check if conversion was successful
    if mol is None:
        raise MoleculeException(
            message=MOLECULE_ERRORS["INVALID_SMILES"],
            error_code="invalid_smiles"
        )
    
    # Generate InChI
    inchi_string = rdkit_inchi.MolToInchi(mol)
    
    return inchi_string


def get_inchi_key_from_smiles(smiles: str) -> str:
    """
    Generates an InChI Key from a SMILES string.
    
    Args:
        smiles: The SMILES string to convert
        
    Returns:
        InChI Key string
        
    Raises:
        MoleculeException: If the SMILES string is invalid
    """
    # Check if input is None or empty
    if smiles is None or not smiles.strip():
        raise MoleculeException(
            message=MOLECULE_ERRORS["INVALID_SMILES"],
            error_code="invalid_smiles"
        )
    
    # Convert to RDKit molecule
    mol = Chem.MolFromSmiles(smiles.strip())
    
    # Check if conversion was successful
    if mol is None:
        raise MoleculeException(
            message=MOLECULE_ERRORS["INVALID_SMILES"],
            error_code="invalid_smiles"
        )
    
    # Generate InChI Key
    inchi_key = rdkit_inchi.MolToInchiKey(mol)
    
    return inchi_key


def get_molecular_formula_from_smiles(smiles: str) -> str:
    """
    Calculates the molecular formula from a SMILES string.
    
    Args:
        smiles: The SMILES string to convert
        
    Returns:
        Molecular formula
        
    Raises:
        MoleculeException: If the SMILES string is invalid
    """
    # Check if input is None or empty
    if smiles is None or not smiles.strip():
        raise MoleculeException(
            message=MOLECULE_ERRORS["INVALID_SMILES"],
            error_code="invalid_smiles"
        )
    
    # Convert to RDKit molecule
    mol = Chem.MolFromSmiles(smiles.strip())
    
    # Check if conversion was successful
    if mol is None:
        raise MoleculeException(
            message=MOLECULE_ERRORS["INVALID_SMILES"],
            error_code="invalid_smiles"
        )
    
    # Calculate molecular formula
    formula = Chem.rdMolDescriptors.CalcMolFormula(mol)
    
    return formula


def are_same_molecule(smiles1: str, smiles2: str) -> bool:
    """
    Compares two SMILES strings to determine if they represent the same molecule.
    
    Args:
        smiles1: First SMILES string
        smiles2: Second SMILES string
        
    Returns:
        True if the SMILES strings represent the same molecule, False otherwise
        
    Raises:
        MoleculeException: If either SMILES string is invalid
    """
    # Check if either input is None or empty
    if (smiles1 is None or not smiles1.strip() or 
        smiles2 is None or not smiles2.strip()):
        raise MoleculeException(
            message=MOLECULE_ERRORS["INVALID_SMILES"],
            error_code="invalid_smiles"
        )
    
    # Convert both to canonical SMILES
    try:
        canonical_smiles1 = canonicalize_smiles(smiles1)
        canonical_smiles2 = canonicalize_smiles(smiles2)
    except MoleculeException:
        return False
    
    # Compare the canonical SMILES
    return canonical_smiles1 == canonical_smiles2


def get_smiles_from_inchi(inchi: str) -> str:
    """
    Converts an InChI string to a SMILES string.
    
    Args:
        inchi: The InChI string to convert
        
    Returns:
        SMILES string
        
    Raises:
        MoleculeException: If the InChI string is invalid
    """
    # Check if input is None or empty
    if inchi is None or not inchi.strip():
        raise MoleculeException(
            message="Invalid InChI string",
            error_code="invalid_inchi"
        )
    
    # Convert InChI to molecule
    mol = Chem.MolFromInchi(inchi.strip())
    
    # Check if conversion was successful
    if mol is None:
        raise MoleculeException(
            message="Invalid InChI string",
            error_code="invalid_inchi"
        )
    
    # Convert to SMILES
    smiles = Chem.MolToSmiles(mol, isomericSmiles=True, canonical=True)
    
    return smiles


def get_smiles_from_inchi_key(inchi_key: str) -> str:
    """
    Attempts to resolve an InChI Key to a SMILES string using external services.
    
    Args:
        inchi_key: The InChI Key to resolve
        
    Returns:
        SMILES string if resolvable, None otherwise
        
    Raises:
        MoleculeException: If the InChI Key is invalid
        NotImplementedError: As this requires external chemical databases
    """
    # Check if input is None or empty
    if inchi_key is None or not inchi_key.strip():
        raise MoleculeException(
            message="Invalid InChI Key",
            error_code="invalid_inchi_key"
        )
    
    # Direct InChI Key to SMILES conversion requires external services
    # This would typically involve querying chemical databases like PubChem or ChemSpider
    raise NotImplementedError(
        "Direct InChI Key to SMILES conversion requires external chemical databases. "
        "Please use an external service like PubChem or ChemSpider for this operation."
    )


def sanitize_smiles(smiles: str) -> str:
    """
    Sanitizes a SMILES string by removing any invalid characters or formatting issues.
    
    Args:
        smiles: The SMILES string to sanitize
        
    Returns:
        Sanitized SMILES string
        
    Raises:
        MoleculeException: If the SMILES string is invalid and cannot be sanitized
    """
    # Check if input is None or empty
    if smiles is None or not smiles.strip():
        raise MoleculeException(
            message=MOLECULE_ERRORS["INVALID_SMILES"],
            error_code="invalid_smiles"
        )
    
    # Remove whitespace and normalize
    cleaned_smiles = smiles.strip()
    
    # Try to convert to RDKit molecule with sanitization
    mol = Chem.MolFromSmiles(cleaned_smiles, sanitize=True)
    
    # If conversion fails, try to identify and fix common issues
    if mol is None:
        # Try without sanitization
        mol = Chem.MolFromSmiles(cleaned_smiles, sanitize=False)
        
        if mol is not None:
            # Try to sanitize now
            try:
                Chem.SanitizeMol(mol)
            except:
                # If sanitization fails, the SMILES is likely invalid
                mol = None
    
    # If still null, the SMILES is invalid
    if mol is None:
        raise MoleculeException(
            message=MOLECULE_ERRORS["INVALID_SMILES"],
            error_code="invalid_smiles"
        )
    
    # Convert back to SMILES
    sanitized_smiles = Chem.MolToSmiles(mol)
    
    return sanitized_smiles


def get_smiles_complexity(smiles: str) -> float:
    """
    Calculates a complexity score for a SMILES string based on structure.
    
    Args:
        smiles: The SMILES string to analyze
        
    Returns:
        Complexity score as a float
        
    Raises:
        MoleculeException: If the SMILES string is invalid
    """
    # Check if input is None or empty
    if smiles is None or not smiles.strip():
        raise MoleculeException(
            message=MOLECULE_ERRORS["INVALID_SMILES"],
            error_code="invalid_smiles"
        )
    
    # Convert to RDKit molecule
    mol = Chem.MolFromSmiles(smiles.strip())
    
    # Check if conversion was successful
    if mol is None:
        raise MoleculeException(
            message=MOLECULE_ERRORS["INVALID_SMILES"],
            error_code="invalid_smiles"
        )
    
    # Calculate Bertz complexity index
    complexity = Chem.GraphDescriptors.BertzCT(mol)
    
    return complexity