"""
RDKit Utilities Module

This module provides core utility functions for molecular structure handling, manipulation, 
and property calculation using RDKit. These functions serve as a foundation for molecular 
operations throughout the application.
"""

# Standard library imports
from typing import Optional, Union, List, Dict, Tuple
import io

# External imports
from rdkit import Chem  # version: 2023.03+
from rdkit.Chem import AllChem  # version: 2023.03+
from rdkit.Chem import Descriptors  # version: 2023.03+
from rdkit.Chem import MolStandardize  # version: 2023.03+
from rdkit.Chem import Draw  # version: 2023.03+

# Internal imports
from ..core.exceptions import MoleculeException
from ..constants.error_messages import MOLECULE_ERRORS
from ..constants.molecule_properties import PROPERTY_RANGES

# Default sanitization options for RDKit molecules
SANITIZE_OPTS = Chem.SanitizeFlags.SANITIZE_ALL


def smiles_to_mol(smiles: str, sanitize: bool = True) -> Optional[Chem.rdchem.Mol]:
    """Converts a SMILES string to an RDKit molecule object.
    
    Args:
        smiles: SMILES string representation of molecule
        sanitize: Whether to sanitize the molecule (default: True)
        
    Returns:
        RDKit molecule object or None if conversion fails
    """
    if not smiles or not isinstance(smiles, str):
        return None
    
    try:
        mol = Chem.MolFromSmiles(smiles, sanitize=sanitize)
        return mol
    except Exception:
        return None


def validate_mol(mol: Optional[Chem.rdchem.Mol]) -> bool:
    """Validates an RDKit molecule object.
    
    Args:
        mol: RDKit molecule object to validate
        
    Returns:
        True if molecule is valid, False otherwise
    """
    if mol is None:
        return False
    
    # Check if molecule has atoms
    if mol.GetNumAtoms() == 0:
        return False
    
    return True


def mol_to_smiles(mol: Chem.rdchem.Mol, canonical: bool = True, isomeric: bool = True) -> Optional[str]:
    """Converts an RDKit molecule to a SMILES string.
    
    Args:
        mol: RDKit molecule object
        canonical: Whether to return canonical SMILES (default: True)
        isomeric: Whether to include stereochemistry in SMILES (default: True)
        
    Returns:
        SMILES string or None if conversion fails
    """
    if not validate_mol(mol):
        return None
    
    try:
        return Chem.MolToSmiles(mol, canonical=canonical, isomericSmiles=isomeric)
    except Exception:
        return None


def standardize_mol(mol: Chem.rdchem.Mol) -> Optional[Chem.rdchem.Mol]:
    """Standardizes an RDKit molecule for consistent representation.
    
    Args:
        mol: RDKit molecule object
        
    Returns:
        Standardized molecule or None if standardization fails
    """
    if not validate_mol(mol):
        return None
    
    try:
        return MolStandardize.standardize_mol(mol)
    except Exception:
        return None


def mol_to_inchi(mol: Chem.rdchem.Mol) -> Optional[str]:
    """Converts an RDKit molecule to an InChI string.
    
    Args:
        mol: RDKit molecule object
        
    Returns:
        InChI string or None if conversion fails
    """
    if not validate_mol(mol):
        return None
    
    try:
        return Chem.MolToInchi(mol)
    except Exception:
        return None


def mol_to_inchi_key(mol: Chem.rdchem.Mol) -> Optional[str]:
    """Converts an RDKit molecule to an InChI Key.
    
    Args:
        mol: RDKit molecule object
        
    Returns:
        InChI Key or None if conversion fails
    """
    if not validate_mol(mol):
        return None
    
    try:
        return Chem.MolToInchiKey(mol)
    except Exception:
        return None


def inchi_to_mol(inchi: str) -> Optional[Chem.rdchem.Mol]:
    """Converts an InChI string to an RDKit molecule.
    
    Args:
        inchi: InChI string
        
    Returns:
        RDKit molecule or None if conversion fails
    """
    if not inchi or not isinstance(inchi, str):
        return None
    
    try:
        return Chem.MolFromInchi(inchi)
    except Exception:
        return None


def get_molecular_formula(mol: Chem.rdchem.Mol) -> Optional[str]:
    """Calculates the molecular formula from an RDKit molecule.
    
    Args:
        mol: RDKit molecule object
        
    Returns:
        Molecular formula or None if calculation fails
    """
    if not validate_mol(mol):
        return None
    
    try:
        return Chem.rdMolDescriptors.CalcMolFormula(mol)
    except Exception:
        return None


def get_molecular_weight(mol: Chem.rdchem.Mol) -> Optional[float]:
    """Calculates the molecular weight from an RDKit molecule.
    
    Args:
        mol: RDKit molecule object
        
    Returns:
        Molecular weight or None if calculation fails
    """
    if not validate_mol(mol):
        return None
    
    try:
        return Descriptors.MolWt(mol)
    except Exception:
        return None


def get_exact_mass(mol: Chem.rdchem.Mol) -> Optional[float]:
    """Calculates the exact mass from an RDKit molecule.
    
    Args:
        mol: RDKit molecule object
        
    Returns:
        Exact mass or None if calculation fails
    """
    if not validate_mol(mol):
        return None
    
    try:
        return Descriptors.ExactMolWt(mol)
    except Exception:
        return None


def get_mol_image(mol: Chem.rdchem.Mol, width: int = 300, height: int = 200, kekulize: bool = True) -> Optional[bytes]:
    """Generates a 2D image of a molecule.
    
    Args:
        mol: RDKit molecule object
        width: Image width in pixels (default: 300)
        height: Image height in pixels (default: 200)
        kekulize: Whether to kekulize the molecule (default: True)
        
    Returns:
        PNG image data as bytes or None if generation fails
    """
    if not validate_mol(mol):
        return None
    
    try:
        # Generate 2D coordinates if not already present
        if not mol.GetNumConformers():
            mol = compute_2d_coords(mol)
            if mol is None:
                raise MoleculeException(MOLECULE_ERRORS["STRUCTURE_GENERATION_FAILED"])
        
        # Generate the image
        img = Draw.MolToImage(mol, size=(width, height), kekulize=kekulize)
        
        # Convert to PNG bytes
        byte_array = io.BytesIO()
        img.save(byte_array, format='PNG')
        return byte_array.getvalue()
    except Exception:
        return None


def get_mol_svg(mol: Chem.rdchem.Mol, width: int = 300, height: int = 200, kekulize: bool = True) -> Optional[str]:
    """Generates an SVG representation of a molecule.
    
    Args:
        mol: RDKit molecule object
        width: SVG width in pixels (default: 300)
        height: SVG height in pixels (default: 200)
        kekulize: Whether to kekulize the molecule (default: True)
        
    Returns:
        SVG string or None if generation fails
    """
    if not validate_mol(mol):
        return None
    
    try:
        # Generate 2D coordinates if not already present
        if not mol.GetNumConformers():
            mol = compute_2d_coords(mol)
            if mol is None:
                raise MoleculeException(MOLECULE_ERRORS["STRUCTURE_GENERATION_FAILED"])
        
        # Generate the SVG
        svg = Draw.MolToSVG(mol, size=(width, height), kekulize=kekulize)
        return svg
    except Exception:
        return None


def sanitize_mol(mol: Chem.rdchem.Mol, sanitize_ops: int = SANITIZE_OPTS) -> Optional[Chem.rdchem.Mol]:
    """Sanitizes an RDKit molecule to ensure chemical validity.
    
    Args:
        mol: RDKit molecule object
        sanitize_ops: Sanitization operations to perform (default: SANITIZE_ALL)
        
    Returns:
        Sanitized molecule or None if sanitization fails
    """
    if mol is None:
        return None
    
    try:
        # Create a copy to avoid modifying the original
        mol_copy = Chem.Mol(mol)
        Chem.SanitizeMol(mol_copy, sanitizeOps=sanitize_ops)
        return mol_copy
    except Exception:
        return None


def compute_2d_coords(mol: Chem.rdchem.Mol) -> Optional[Chem.rdchem.Mol]:
    """Computes 2D coordinates for a molecule.
    
    Args:
        mol: RDKit molecule object
        
    Returns:
        Molecule with 2D coordinates or None if computation fails
    """
    if not validate_mol(mol):
        return None
    
    try:
        # Create a copy to avoid modifying the original
        mol_copy = Chem.Mol(mol)
        AllChem.Compute2DCoords(mol_copy)
        return mol_copy
    except Exception:
        return None


def compute_3d_coords(mol: Chem.rdchem.Mol, optimize: bool = True) -> Optional[Chem.rdchem.Mol]:
    """Computes 3D coordinates for a molecule.
    
    Args:
        mol: RDKit molecule object
        optimize: Whether to optimize the 3D structure (default: True)
        
    Returns:
        Molecule with 3D coordinates or None if computation fails
    """
    if not validate_mol(mol):
        return None
    
    try:
        # Create a copy to avoid modifying the original
        mol_copy = Chem.Mol(mol)
        
        # Embed the molecule
        AllChem.EmbedMolecule(mol_copy)
        
        # Optimize if requested
        if optimize:
            AllChem.UFFOptimizeMolecule(mol_copy)
            
        return mol_copy
    except Exception:
        return None


def are_same_molecule(mol1: Chem.rdchem.Mol, mol2: Chem.rdchem.Mol) -> bool:
    """Determines if two molecules are the same based on canonical SMILES.
    
    Args:
        mol1: First RDKit molecule object
        mol2: Second RDKit molecule object
        
    Returns:
        True if molecules are the same, False otherwise
    """
    if not validate_mol(mol1) or not validate_mol(mol2):
        return False
    
    # Compare canonical SMILES
    smiles1 = mol_to_smiles(mol1, canonical=True, isomeric=True)
    smiles2 = mol_to_smiles(mol2, canonical=True, isomeric=True)
    
    return smiles1 == smiles2


def get_atom_count(mol: Chem.rdchem.Mol) -> Optional[int]:
    """Counts the total number of atoms in a molecule.
    
    Args:
        mol: RDKit molecule object
        
    Returns:
        Atom count or None if calculation fails
    """
    if not validate_mol(mol):
        return None
    
    try:
        return mol.GetNumAtoms()
    except Exception:
        return None


def get_heavy_atom_count(mol: Chem.rdchem.Mol) -> Optional[int]:
    """Counts the number of non-hydrogen atoms in a molecule.
    
    Args:
        mol: RDKit molecule object
        
    Returns:
        Heavy atom count or None if calculation fails
    """
    if not validate_mol(mol):
        return None
    
    try:
        return Chem.Lipinski.HeavyAtomCount(mol)
    except Exception:
        return None


def get_ring_count(mol: Chem.rdchem.Mol) -> Optional[int]:
    """Counts the number of rings in a molecule.
    
    Args:
        mol: RDKit molecule object
        
    Returns:
        Ring count or None if calculation fails
    """
    if not validate_mol(mol):
        return None
    
    try:
        return Chem.rdMolDescriptors.CalcNumRings(mol)
    except Exception:
        return None


def get_rotatable_bond_count(mol: Chem.rdchem.Mol) -> Optional[int]:
    """Counts the number of rotatable bonds in a molecule.
    
    Args:
        mol: RDKit molecule object
        
    Returns:
        Rotatable bond count or None if calculation fails
    """
    if not validate_mol(mol):
        return None
    
    try:
        return Chem.Lipinski.NumRotatableBonds(mol)
    except Exception:
        return None


def get_hydrogen_bond_donor_count(mol: Chem.rdchem.Mol) -> Optional[int]:
    """Counts the number of hydrogen bond donors in a molecule.
    
    Args:
        mol: RDKit molecule object
        
    Returns:
        Hydrogen bond donor count or None if calculation fails
    """
    if not validate_mol(mol):
        return None
    
    try:
        return Chem.Lipinski.NumHDonors(mol)
    except Exception:
        return None


def get_hydrogen_bond_acceptor_count(mol: Chem.rdchem.Mol) -> Optional[int]:
    """Counts the number of hydrogen bond acceptors in a molecule.
    
    Args:
        mol: RDKit molecule object
        
    Returns:
        Hydrogen bond acceptor count or None if calculation fails
    """
    if not validate_mol(mol):
        return None
    
    try:
        return Chem.Lipinski.NumHAcceptors(mol)
    except Exception:
        return None


def get_logp(mol: Chem.rdchem.Mol) -> Optional[float]:
    """Calculates the LogP (octanol-water partition coefficient) of a molecule.
    
    Args:
        mol: RDKit molecule object
        
    Returns:
        LogP value or None if calculation fails
    """
    if not validate_mol(mol):
        return None
    
    try:
        return Chem.Crippen.MolLogP(mol)
    except Exception:
        return None


def get_tpsa(mol: Chem.rdchem.Mol) -> Optional[float]:
    """Calculates the TPSA (topological polar surface area) of a molecule.
    
    Args:
        mol: RDKit molecule object
        
    Returns:
        TPSA value or None if calculation fails
    """
    if not validate_mol(mol):
        return None
    
    try:
        return Chem.rdMolDescriptors.CalcTPSA(mol)
    except Exception:
        return None


def check_property_in_range(property_name: str, value: float) -> bool:
    """Checks if a molecular property value is within the expected range.
    
    Args:
        property_name: Name of the property
        value: Property value to check
        
    Returns:
        True if value is within range, False otherwise
    """
    # If property not in defined ranges, assume it's valid
    if property_name not in PROPERTY_RANGES:
        return True
    
    # Get range and check
    prop_range = PROPERTY_RANGES[property_name]
    min_val = prop_range.get("min")
    max_val = prop_range.get("max")
    
    # Check if value is within range
    if min_val is not None and value < min_val:
        return False
    if max_val is not None and value > max_val:
        return False
    
    return True


def calculate_basic_properties(mol: Chem.rdchem.Mol) -> Dict[str, Union[float, int, str, None]]:
    """Calculates a set of basic molecular properties.
    
    Args:
        mol: RDKit molecule object
        
    Returns:
        Dictionary of property names and values
    """
    if not validate_mol(mol):
        return {}
    
    # Initialize properties dictionary
    properties = {}
    
    # Calculate basic properties
    properties["molecular_weight"] = get_molecular_weight(mol)
    properties["exact_mass"] = get_exact_mass(mol)
    properties["formula"] = get_molecular_formula(mol)
    properties["logp"] = get_logp(mol)
    properties["tpsa"] = get_tpsa(mol)
    properties["num_atoms"] = get_atom_count(mol)
    properties["num_heavy_atoms"] = get_heavy_atom_count(mol)
    properties["num_rings"] = get_ring_count(mol)
    properties["num_rotatable_bonds"] = get_rotatable_bond_count(mol)
    properties["num_h_donors"] = get_hydrogen_bond_donor_count(mol)
    properties["num_h_acceptors"] = get_hydrogen_bond_acceptor_count(mol)
    
    return properties