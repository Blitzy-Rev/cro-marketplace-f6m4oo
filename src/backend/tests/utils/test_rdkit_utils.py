"""
Unit tests for RDKit utility functions.

This module contains comprehensive tests for the utility functions that handle 
molecular structure manipulation, property calculation, and visualization using RDKit.
These tests ensure the reliability of core cheminformatics functionality used throughout
the application.
"""

import pytest
import io
import re
from rdkit import Chem  # version: 2023.03+

# Internal imports
from ...app.utils.rdkit_utils import (
    smiles_to_mol,
    validate_mol,
    mol_to_smiles,
    standardize_mol,
    mol_to_inchi,
    mol_to_inchi_key,
    inchi_to_mol,
    get_molecular_formula,
    get_molecular_weight,
    get_exact_mass,
    get_mol_image,
    get_mol_svg,
    sanitize_mol,
    compute_2d_coords,
    compute_3d_coords,
    are_same_molecule,
    get_atom_count,
    get_heavy_atom_count,
    get_ring_count,
    get_rotatable_bond_count,
    get_hydrogen_bond_donor_count,
    get_hydrogen_bond_acceptor_count,
    get_logp,
    get_tpsa,
    check_property_in_range,
    calculate_basic_properties,
    SANITIZE_OPTS
)
from ...app.core.exceptions import MoleculeException
from ...app.constants.error_messages import MOLECULE_ERRORS
from ...app.constants.molecule_properties import PROPERTY_RANGES

# Test data
VALID_SMILES_EXAMPLES = [
    "C", "CC", "CCO", "c1ccccc1", "CC(=O)O", "C1CCCCC1", 
    "N#C", "CCN(CC)CC", "CC(C)CCO", "C1=CC=C(C=C1)C(=O)O"
]

INVALID_SMILES_EXAMPLES = [
    "X", "C:C", "C(C", "1CCCCC1", "C%C", "C##C", "C1CC2", "", " ", None
]

EQUIVALENT_SMILES_PAIRS = [
    ("CCO", "OCC"),
    ("c1ccccc1", "C1=CC=CC=C1"),
    ("CC(=O)O", "CC(O)=O")
]

INCHI_TEST_CASES = [
    ("CCO", "InChI=1S/C2H6O/c1-2-3/h3H,2H2,1H3"),
    ("c1ccccc1", "InChI=1S/C6H6/c1-2-4-6-5-3-1/h1-6H")
]

PROPERTY_TEST_CASES = [
    {"smiles": "CCO", "formula": "C2H6O", "molecular_weight": 46.07, "logp": 0.14},
    {"smiles": "c1ccccc1", "formula": "C6H6", "molecular_weight": 78.11, "logp": 1.69}
]


def test_smiles_to_mol_valid():
    """Tests that smiles_to_mol correctly converts valid SMILES strings to RDKit molecules."""
    for smiles in VALID_SMILES_EXAMPLES:
        mol = smiles_to_mol(smiles)
        assert mol is not None
        assert isinstance(mol, Chem.rdchem.Mol)
        # Verify that the molecule has atoms
        assert mol.GetNumAtoms() > 0


def test_smiles_to_mol_invalid():
    """Tests that smiles_to_mol returns None for invalid SMILES strings."""
    for smiles in INVALID_SMILES_EXAMPLES:
        mol = smiles_to_mol(smiles)
        assert mol is None


def test_validate_mol():
    """Tests that validate_mol correctly identifies valid and invalid RDKit molecules."""
    # Test with valid molecules
    for smiles in VALID_SMILES_EXAMPLES:
        mol = smiles_to_mol(smiles)
        assert validate_mol(mol) is True
    
    # Test with None
    assert validate_mol(None) is False
    
    # Test with empty molecule
    empty_mol = Chem.RWMol()  # Create an empty molecule
    assert validate_mol(empty_mol) is False


def test_mol_to_smiles():
    """Tests that mol_to_smiles correctly converts RDKit molecules to SMILES strings."""
    # Test with valid molecules
    for smiles in VALID_SMILES_EXAMPLES:
        mol = smiles_to_mol(smiles)
        result = mol_to_smiles(mol)
        assert result is not None
        assert isinstance(result, str)
        assert len(result) > 0
    
    # Test with None
    assert mol_to_smiles(None) is None
    
    # Test canonical parameter
    for smiles_pair in EQUIVALENT_SMILES_PAIRS:
        mol1 = smiles_to_mol(smiles_pair[0])
        mol2 = smiles_to_mol(smiles_pair[1])
        
        # With canonical=True, they should be identical
        assert mol_to_smiles(mol1, canonical=True) == mol_to_smiles(mol2, canonical=True)
        
    # Test isomeric parameter with a molecule that has stereochemistry
    mol = smiles_to_mol("C[C@H](O)CC")
    smiles_iso = mol_to_smiles(mol, isomeric=True)
    smiles_non_iso = mol_to_smiles(mol, isomeric=False)
    # The isomeric version should contain the stereochemistry information
    assert smiles_iso != smiles_non_iso


def test_standardize_mol():
    """Tests that standardize_mol correctly standardizes RDKit molecules."""
    # Test with valid molecules
    for smiles in VALID_SMILES_EXAMPLES:
        mol = smiles_to_mol(smiles)
        std_mol = standardize_mol(mol)
        assert std_mol is not None
        assert isinstance(std_mol, Chem.rdchem.Mol)
    
    # Test with None
    assert standardize_mol(None) is None


def test_mol_to_inchi():
    """Tests that mol_to_inchi correctly generates InChI strings from RDKit molecules."""
    # Test with known InChI values
    for smiles, expected_inchi in INCHI_TEST_CASES:
        mol = smiles_to_mol(smiles)
        inchi = mol_to_inchi(mol)
        assert inchi == expected_inchi
    
    # Test with None
    assert mol_to_inchi(None) is None


def test_mol_to_inchi_key():
    """Tests that mol_to_inchi_key correctly generates InChI Keys from RDKit molecules."""
    # InChI Keys should be 27 characters and follow a specific format
    for smiles in VALID_SMILES_EXAMPLES:
        mol = smiles_to_mol(smiles)
        inchi_key = mol_to_inchi_key(mol)
        assert inchi_key is not None
        assert isinstance(inchi_key, str)
        assert len(inchi_key) == 27
        # InChI Keys have a specific format: 14 chars + hyphen + 10 chars + letter
        assert re.match(r'^[A-Z]{14}-[A-Z]{10}[A-Z]$', inchi_key)
    
    # Test with None
    assert mol_to_inchi_key(None) is None


def test_inchi_to_mol():
    """Tests that inchi_to_mol correctly converts InChI strings to RDKit molecules."""
    # Test with known InChI values
    for _, inchi in INCHI_TEST_CASES:
        mol = inchi_to_mol(inchi)
        assert mol is not None
        assert isinstance(mol, Chem.rdchem.Mol)
    
    # Test with None and empty string
    assert inchi_to_mol(None) is None
    assert inchi_to_mol("") is None
    
    # Test with invalid InChI
    assert inchi_to_mol("Invalid InChI") is None


def test_get_molecular_formula():
    """Tests that get_molecular_formula correctly calculates molecular formulas."""
    # Test with known formulas
    for test_case in PROPERTY_TEST_CASES:
        mol = smiles_to_mol(test_case["smiles"])
        formula = get_molecular_formula(mol)
        assert formula == test_case["formula"]
    
    # Test with None
    assert get_molecular_formula(None) is None


def test_get_molecular_weight():
    """Tests that get_molecular_weight correctly calculates molecular weights."""
    # Test with known molecular weights (allow small tolerance for floating point comparison)
    for test_case in PROPERTY_TEST_CASES:
        mol = smiles_to_mol(test_case["smiles"])
        mw = get_molecular_weight(mol)
        assert abs(mw - test_case["molecular_weight"]) < 0.1
    
    # Test with None
    assert get_molecular_weight(None) is None


def test_get_exact_mass():
    """Tests that get_exact_mass correctly calculates exact masses."""
    # Exact mass should be a positive float and slightly different from molecular weight
    for test_case in PROPERTY_TEST_CASES:
        mol = smiles_to_mol(test_case["smiles"])
        exact_mass = get_exact_mass(mol)
        mw = get_molecular_weight(mol)
        
        assert exact_mass > 0
        assert isinstance(exact_mass, float)
        # Exact mass should be close to but not exactly the same as molecular weight
        assert abs(exact_mass - mw) < 1.0
    
    # Test with None
    assert get_exact_mass(None) is None


def test_get_mol_image():
    """Tests that get_mol_image correctly generates molecule images."""
    # Test image generation for valid molecules
    for smiles in VALID_SMILES_EXAMPLES:
        mol = smiles_to_mol(smiles)
        img_data = get_mol_image(mol)
        
        assert img_data is not None
        assert isinstance(img_data, bytes)
        # Check that it's a PNG by verifying the PNG signature
        assert img_data.startswith(b'\x89PNG\r\n\x1a\n')
    
    # Test with different dimensions
    mol = smiles_to_mol("CCO")
    img_data_1 = get_mol_image(mol, width=200, height=150)
    img_data_2 = get_mol_image(mol, width=300, height=200)
    
    # Different dimensions should produce different image data
    assert img_data_1 != img_data_2
    
    # Test with None
    assert get_mol_image(None) is None


def test_get_mol_svg():
    """Tests that get_mol_svg correctly generates SVG representations."""
    # Test SVG generation for valid molecules
    for smiles in VALID_SMILES_EXAMPLES:
        mol = smiles_to_mol(smiles)
        svg = get_mol_svg(mol)
        
        assert svg is not None
        assert isinstance(svg, str)
        # Check that it's an SVG by verifying the SVG tag
        assert '<svg' in svg and '</svg>' in svg
    
    # Test with different dimensions
    mol = smiles_to_mol("CCO")
    svg_1 = get_mol_svg(mol, width=200, height=150)
    svg_2 = get_mol_svg(mol, width=300, height=200)
    
    # Different dimensions should produce different SVG data
    assert svg_1 != svg_2
    
    # Test with None
    assert get_mol_svg(None) is None


def test_sanitize_mol():
    """Tests that sanitize_mol correctly sanitizes RDKit molecules."""
    # Test sanitization for valid molecules
    for smiles in VALID_SMILES_EXAMPLES:
        mol = smiles_to_mol(smiles, sanitize=False)  # Create unsanitized molecule
        sanitized_mol = sanitize_mol(mol)
        
        assert sanitized_mol is not None
        assert isinstance(sanitized_mol, Chem.rdchem.Mol)
    
    # Test with custom sanitize_ops
    mol = smiles_to_mol("CCO", sanitize=False)
    sanitized_mol = sanitize_mol(mol, sanitize_ops=Chem.SanitizeFlags.SANITIZE_FINDRADICALS)
    
    assert sanitized_mol is not None
    
    # Test with None
    assert sanitize_mol(None) is None


def test_compute_2d_coords():
    """Tests that compute_2d_coords correctly computes 2D coordinates."""
    # Test 2D coordinate computation for valid molecules
    for smiles in VALID_SMILES_EXAMPLES:
        mol = smiles_to_mol(smiles)
        mol_2d = compute_2d_coords(mol)
        
        assert mol_2d is not None
        assert isinstance(mol_2d, Chem.rdchem.Mol)
        # Check that the molecule has conformers
        assert mol_2d.GetNumConformers() > 0
    
    # Test with None
    assert compute_2d_coords(None) is None


def test_compute_3d_coords():
    """Tests that compute_3d_coords correctly computes 3D coordinates."""
    # Test 3D coordinate computation for valid molecules
    for smiles in VALID_SMILES_EXAMPLES:
        mol = smiles_to_mol(smiles)
        mol_3d = compute_3d_coords(mol)
        
        assert mol_3d is not None
        assert isinstance(mol_3d, Chem.rdchem.Mol)
        # Check that the molecule has conformers
        assert mol_3d.GetNumConformers() > 0
    
    # Test with optimize=True and optimize=False
    mol = smiles_to_mol("CCO")
    mol_3d_opt = compute_3d_coords(mol, optimize=True)
    mol_3d_no_opt = compute_3d_coords(mol, optimize=False)
    
    assert mol_3d_opt is not None
    assert mol_3d_no_opt is not None
    
    # Test with None
    assert compute_3d_coords(None) is None


def test_are_same_molecule():
    """Tests that are_same_molecule correctly identifies equivalent molecules."""
    # Test with known equivalent SMILES pairs
    for smiles1, smiles2 in EQUIVALENT_SMILES_PAIRS:
        mol1 = smiles_to_mol(smiles1)
        mol2 = smiles_to_mol(smiles2)
        assert are_same_molecule(mol1, mol2) is True
    
    # Test with different molecules
    mol1 = smiles_to_mol("CCO")  # Ethanol
    mol2 = smiles_to_mol("CC(=O)O")  # Acetic acid
    assert are_same_molecule(mol1, mol2) is False
    
    # Test with None
    assert are_same_molecule(None, smiles_to_mol("CCO")) is False
    assert are_same_molecule(smiles_to_mol("CCO"), None) is False
    assert are_same_molecule(None, None) is False


def test_get_atom_count():
    """Tests that get_atom_count correctly counts atoms."""
    # Test atom counting for valid molecules
    for smiles in VALID_SMILES_EXAMPLES:
        mol = smiles_to_mol(smiles)
        atom_count = get_atom_count(mol)
        
        assert atom_count is not None
        assert isinstance(atom_count, int)
        assert atom_count > 0
        # Verify that the count matches the actual number of atoms
        assert atom_count == mol.GetNumAtoms()
    
    # Test with None
    assert get_atom_count(None) is None


def test_get_heavy_atom_count():
    """Tests that get_heavy_atom_count correctly counts non-hydrogen atoms."""
    # Test heavy atom counting for valid molecules
    for smiles in VALID_SMILES_EXAMPLES:
        mol = smiles_to_mol(smiles)
        heavy_atom_count = get_heavy_atom_count(mol)
        atom_count = get_atom_count(mol)
        
        assert heavy_atom_count is not None
        assert isinstance(heavy_atom_count, int)
        assert heavy_atom_count > 0
        # Heavy atom count should be less than or equal to total atom count
        assert heavy_atom_count <= atom_count
    
    # Test with None
    assert get_heavy_atom_count(None) is None


def test_get_ring_count():
    """Tests that get_ring_count correctly counts rings."""
    # Test molecules with known ring counts
    ring_test_cases = [
        ("CCO", 0),  # Ethanol - no rings
        ("c1ccccc1", 1),  # Benzene - 1 ring
        ("c1ccccc1c2ccccc2", 2),  # Biphenyl - 2 rings
        ("C1CC2CCC1CC2", 2)  # Decalin - 2 rings
    ]
    
    for smiles, expected_rings in ring_test_cases:
        mol = smiles_to_mol(smiles)
        ring_count = get_ring_count(mol)
        
        assert ring_count == expected_rings
    
    # Test with None
    assert get_ring_count(None) is None


def test_get_rotatable_bond_count():
    """Tests that get_rotatable_bond_count correctly counts rotatable bonds."""
    # Test molecules with known rotatable bond counts
    rotatable_bond_test_cases = [
        ("C", 0),  # Methane - no rotatable bonds
        ("CC", 0),  # Ethane - technically has a rotatable bond, but RDKit doesn't count it
        ("CCCC", 1),  # Butane - 1 rotatable bond
        ("CCCCC", 2),  # Pentane - 2 rotatable bonds
        ("c1ccccc1", 0),  # Benzene - 0 rotatable bonds
        ("c1ccccc1-c2ccccc2", 1)  # Biphenyl - 1 rotatable bond
    ]
    
    for smiles, expected_count in rotatable_bond_test_cases:
        mol = smiles_to_mol(smiles)
        rotatable_count = get_rotatable_bond_count(mol)
        
        assert rotatable_count == expected_count
    
    # Test with None
    assert get_rotatable_bond_count(None) is None


def test_get_hydrogen_bond_donor_count():
    """Tests that get_hydrogen_bond_donor_count correctly counts H-bond donors."""
    # Test molecules with known H-bond donor counts
    hbd_test_cases = [
        ("CC", 0),  # Ethane - 0 donors
        ("CCO", 1),  # Ethanol - 1 donor
        ("CC(O)C(O)CC", 2),  # 2,3-butanediol - 2 donors
        ("c1ccccc1", 0),  # Benzene - 0 donors
        ("c1ccccc1O", 1)  # Phenol - 1 donor
    ]
    
    for smiles, expected_count in hbd_test_cases:
        mol = smiles_to_mol(smiles)
        hbd_count = get_hydrogen_bond_donor_count(mol)
        
        assert hbd_count == expected_count
    
    # Test with None
    assert get_hydrogen_bond_donor_count(None) is None


def test_get_hydrogen_bond_acceptor_count():
    """Tests that get_hydrogen_bond_acceptor_count correctly counts H-bond acceptors."""
    # Test molecules with known H-bond acceptor counts
    hba_test_cases = [
        ("CC", 0),  # Ethane - 0 acceptors
        ("CCO", 1),  # Ethanol - 1 acceptor
        ("CC(=O)O", 2),  # Acetic acid - 2 acceptors
        ("c1ccccc1", 0),  # Benzene - 0 acceptors
        ("c1ccccc1O", 1)  # Phenol - 1 acceptor
    ]
    
    for smiles, expected_count in hba_test_cases:
        mol = smiles_to_mol(smiles)
        hba_count = get_hydrogen_bond_acceptor_count(mol)
        
        assert hba_count == expected_count
    
    # Test with None
    assert get_hydrogen_bond_acceptor_count(None) is None


def test_get_logp():
    """Tests that get_logp correctly calculates LogP values."""
    # Test with known LogP values
    for test_case in PROPERTY_TEST_CASES:
        mol = smiles_to_mol(test_case["smiles"])
        logp = get_logp(mol)
        
        # LogP calculations can vary slightly depending on the method, so we use a tolerance
        assert abs(logp - test_case["logp"]) < 0.1
    
    # Test with None
    assert get_logp(None) is None


def test_get_tpsa():
    """Tests that get_tpsa correctly calculates topological polar surface area."""
    # TPSA should be a non-negative float
    for smiles in VALID_SMILES_EXAMPLES:
        mol = smiles_to_mol(smiles)
        tpsa = get_tpsa(mol)
        
        assert tpsa is not None
        assert isinstance(tpsa, float)
        assert tpsa >= 0
    
    # Test with molecules containing polar vs non-polar atoms
    mol_nonpolar = smiles_to_mol("C1=CC=CC=C1")  # Benzene - no polar atoms
    mol_polar = smiles_to_mol("CCO")  # Ethanol - has oxygen
    
    assert get_tpsa(mol_nonpolar) < get_tpsa(mol_polar)
    
    # Test with None
    assert get_tpsa(None) is None


def test_check_property_in_range():
    """Tests that check_property_in_range correctly validates property values."""
    # Test properties defined in PROPERTY_RANGES
    for prop_name, range_dict in PROPERTY_RANGES.items():
        min_val = range_dict.get("min")
        max_val = range_dict.get("max")
        
        if min_val is not None:
            # Test value below range
            assert check_property_in_range(prop_name, min_val - 1) is False
            # Test value at lower bound
            assert check_property_in_range(prop_name, min_val) is True
        
        if max_val is not None:
            # Test value at upper bound
            assert check_property_in_range(prop_name, max_val) is True
            # Test value above range
            assert check_property_in_range(prop_name, max_val + 1) is False
        
        # Test value in middle of range
        if min_val is not None and max_val is not None:
            mid_val = (min_val + max_val) / 2
            assert check_property_in_range(prop_name, mid_val) is True
    
    # Test property not in defined ranges (should return True)
    assert check_property_in_range("undefined_property", 100) is True


def test_calculate_basic_properties():
    """Tests that calculate_basic_properties correctly calculates multiple properties."""
    # Test property calculation for valid molecules
    for smiles in VALID_SMILES_EXAMPLES:
        mol = smiles_to_mol(smiles)
        properties = calculate_basic_properties(mol)
        
        assert properties is not None
        assert isinstance(properties, dict)
        
        # Check that all expected properties are present
        expected_properties = [
            "molecular_weight", "exact_mass", "formula", "logp", "tpsa",
            "num_atoms", "num_heavy_atoms", "num_rings", "num_rotatable_bonds",
            "num_h_donors", "num_h_acceptors"
        ]
        
        for prop in expected_properties:
            assert prop in properties
        
        # Verify that property values match the individual property functions
        assert properties["molecular_weight"] == get_molecular_weight(mol)
        assert properties["logp"] == get_logp(mol)
        assert properties["formula"] == get_molecular_formula(mol)
        assert properties["num_atoms"] == get_atom_count(mol)
        assert properties["tpsa"] == get_tpsa(mol)
    
    # Test with None
    assert calculate_basic_properties(None) == {}