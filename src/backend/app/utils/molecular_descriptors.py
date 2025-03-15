"""
Molecular Descriptors Module

This module provides functionality for calculating molecular descriptors, which are
numerical values that characterize molecular structures and properties. It supports
a wide range of descriptors including physicochemical properties, topological indices,
and drug-likeness metrics that are essential for molecular analysis, filtering, and 
AI prediction.
"""

# Standard library imports
from typing import Dict, List, Optional, Union, Any

# RDKit imports
from rdkit import Chem  # version: 2023.03+
from rdkit.Chem import Descriptors  # version: 2023.03+
from rdkit.Chem import Lipinski  # version: 2023.03+
from rdkit.Chem import QED  # version: 2023.03+
from rdkit.Chem import rdMolDescriptors  # version: 2023.03+
from rdkit.Chem import Crippen  # version: 2023.03+
from rdkit.Chem import MolSurf  # version: 2023.03+
from rdkit.Chem import GraphDescriptors  # version: 2023.03+

# Internal imports
from ..core.exceptions import MoleculeException
from ..constants.error_messages import MOLECULE_ERRORS
from ..constants.molecule_properties import PROPERTY_RANGES
from .rdkit_utils import smiles_to_mol, validate_mol

# Categorized descriptor definitions
DESCRIPTOR_CATEGORIES = {
    "physicochemical": "Basic physicochemical properties",
    "topological": "Topological and connectivity indices",
    "constitutional": "Atom and bond counts",
    "electronic": "Electronic and charge-related properties",
    "drug_likeness": "Drug-likeness and bioavailability metrics"
}


def calculate_molecular_weight(mol: Chem.rdchem.Mol) -> Optional[float]:
    """Calculates the molecular weight of a molecule.
    
    Args:
        mol: RDKit molecule object
        
    Returns:
        Molecular weight in g/mol or None if calculation fails
    """
    if not validate_mol(mol):
        return None
    
    try:
        return Descriptors.MolWt(mol)
    except Exception:
        return None


def calculate_exact_mass(mol: Chem.rdchem.Mol) -> Optional[float]:
    """Calculates the exact mass of a molecule.
    
    Args:
        mol: RDKit molecule object
        
    Returns:
        Exact mass in g/mol or None if calculation fails
    """
    if not validate_mol(mol):
        return None
    
    try:
        return Descriptors.ExactMolWt(mol)
    except Exception:
        return None


def calculate_logp(mol: Chem.rdchem.Mol) -> Optional[float]:
    """Calculates the LogP (octanol-water partition coefficient) of a molecule.
    
    Args:
        mol: RDKit molecule object
        
    Returns:
        LogP value or None if calculation fails
    """
    if not validate_mol(mol):
        return None
    
    try:
        return Crippen.MolLogP(mol)
    except Exception:
        return None


def calculate_tpsa(mol: Chem.rdchem.Mol) -> Optional[float]:
    """Calculates the TPSA (topological polar surface area) of a molecule.
    
    Args:
        mol: RDKit molecule object
        
    Returns:
        TPSA value in Å² or None if calculation fails
    """
    if not validate_mol(mol):
        return None
    
    try:
        return rdMolDescriptors.CalcTPSA(mol)
    except Exception:
        return None


def calculate_num_atoms(mol: Chem.rdchem.Mol) -> Optional[int]:
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


def calculate_num_heavy_atoms(mol: Chem.rdchem.Mol) -> Optional[int]:
    """Counts the number of non-hydrogen atoms in a molecule.
    
    Args:
        mol: RDKit molecule object
        
    Returns:
        Heavy atom count or None if calculation fails
    """
    if not validate_mol(mol):
        return None
    
    try:
        return Lipinski.HeavyAtomCount(mol)
    except Exception:
        return None


def calculate_num_rings(mol: Chem.rdchem.Mol) -> Optional[int]:
    """Counts the number of rings in a molecule.
    
    Args:
        mol: RDKit molecule object
        
    Returns:
        Ring count or None if calculation fails
    """
    if not validate_mol(mol):
        return None
    
    try:
        return rdMolDescriptors.CalcNumRings(mol)
    except Exception:
        return None


def calculate_num_rotatable_bonds(mol: Chem.rdchem.Mol) -> Optional[int]:
    """Counts the number of rotatable bonds in a molecule.
    
    Args:
        mol: RDKit molecule object
        
    Returns:
        Rotatable bond count or None if calculation fails
    """
    if not validate_mol(mol):
        return None
    
    try:
        return Lipinski.NumRotatableBonds(mol)
    except Exception:
        return None


def calculate_num_h_donors(mol: Chem.rdchem.Mol) -> Optional[int]:
    """Counts the number of hydrogen bond donors in a molecule.
    
    Args:
        mol: RDKit molecule object
        
    Returns:
        Hydrogen bond donor count or None if calculation fails
    """
    if not validate_mol(mol):
        return None
    
    try:
        return Lipinski.NumHDonors(mol)
    except Exception:
        return None


def calculate_num_h_acceptors(mol: Chem.rdchem.Mol) -> Optional[int]:
    """Counts the number of hydrogen bond acceptors in a molecule.
    
    Args:
        mol: RDKit molecule object
        
    Returns:
        Hydrogen bond acceptor count or None if calculation fails
    """
    if not validate_mol(mol):
        return None
    
    try:
        return Lipinski.NumHAcceptors(mol)
    except Exception:
        return None


def calculate_num_heteroatoms(mol: Chem.rdchem.Mol) -> Optional[int]:
    """Counts the number of heteroatoms (non-carbon, non-hydrogen) in a molecule.
    
    Args:
        mol: RDKit molecule object
        
    Returns:
        Heteroatom count or None if calculation fails
    """
    if not validate_mol(mol):
        return None
    
    try:
        return Lipinski.NumHeteroatoms(mol)
    except Exception:
        return None


def calculate_num_aromatic_rings(mol: Chem.rdchem.Mol) -> Optional[int]:
    """Counts the number of aromatic rings in a molecule.
    
    Args:
        mol: RDKit molecule object
        
    Returns:
        Aromatic ring count or None if calculation fails
    """
    if not validate_mol(mol):
        return None
    
    try:
        return rdMolDescriptors.CalcNumAromaticRings(mol)
    except Exception:
        return None


def calculate_num_aliphatic_rings(mol: Chem.rdchem.Mol) -> Optional[int]:
    """Counts the number of aliphatic rings in a molecule.
    
    Args:
        mol: RDKit molecule object
        
    Returns:
        Aliphatic ring count or None if calculation fails
    """
    if not validate_mol(mol):
        return None
    
    try:
        return rdMolDescriptors.CalcNumAliphaticRings(mol)
    except Exception:
        return None


def calculate_qed(mol: Chem.rdchem.Mol) -> Optional[float]:
    """Calculates the QED (Quantitative Estimate of Drug-likeness) score of a molecule.
    
    Args:
        mol: RDKit molecule object
        
    Returns:
        QED score (0-1 range) or None if calculation fails
    """
    if not validate_mol(mol):
        return None
    
    try:
        return QED.qed(mol)
    except Exception:
        return None


def calculate_lipinski_violations(mol: Chem.rdchem.Mol) -> Optional[int]:
    """Calculates the number of Lipinski's Rule of Five violations for a molecule.
    
    Args:
        mol: RDKit molecule object
        
    Returns:
        Number of violations (0-4) or None if calculation fails
    """
    if not validate_mol(mol):
        return None
    
    try:
        violations = 0
        
        # Calculate properties
        mw = Descriptors.MolWt(mol)
        logp = Crippen.MolLogP(mol)
        h_donors = Lipinski.NumHDonors(mol)
        h_acceptors = Lipinski.NumHAcceptors(mol)
        
        # Count violations
        if mw > 500:
            violations += 1
        if logp > 5:
            violations += 1
        if h_donors > 5:
            violations += 1
        if h_acceptors > 10:
            violations += 1
            
        return violations
    except Exception:
        return None


def calculate_bertz_index(mol: Chem.rdchem.Mol) -> Optional[float]:
    """Calculates the Bertz complexity index of a molecule.
    
    Args:
        mol: RDKit molecule object
        
    Returns:
        Bertz index or None if calculation fails
    """
    if not validate_mol(mol):
        return None
    
    try:
        return GraphDescriptors.BertzCT(mol)
    except Exception:
        return None


def calculate_chi_indices(mol: Chem.rdchem.Mol) -> Optional[Dict[str, float]]:
    """Calculates the Chi molecular connectivity indices of a molecule.
    
    Args:
        mol: RDKit molecule object
        
    Returns:
        Dictionary of Chi indices or None if calculation fails
    """
    if not validate_mol(mol):
        return None
    
    try:
        chi_indices = {
            "chi0v": rdMolDescriptors.CalcChi0v(mol),
            "chi1v": rdMolDescriptors.CalcChi1v(mol),
            "chi2v": rdMolDescriptors.CalcChi2v(mol),
            "chi3v": rdMolDescriptors.CalcChi3v(mol),
            "chi4v": rdMolDescriptors.CalcChi4v(mol)
        }
        return chi_indices
    except Exception:
        return None


def calculate_kappa_indices(mol: Chem.rdchem.Mol) -> Optional[Dict[str, float]]:
    """Calculates the Kappa shape indices of a molecule.
    
    Args:
        mol: RDKit molecule object
        
    Returns:
        Dictionary of Kappa indices or None if calculation fails
    """
    if not validate_mol(mol):
        return None
    
    try:
        kappa_indices = {
            "kappa1": rdMolDescriptors.CalcKappa1(mol),
            "kappa2": rdMolDescriptors.CalcKappa2(mol),
            "kappa3": rdMolDescriptors.CalcKappa3(mol)
        }
        return kappa_indices
    except Exception:
        return None


def calculate_labute_asa(mol: Chem.rdchem.Mol) -> Optional[float]:
    """Calculates the Labute's Approximate Surface Area of a molecule.
    
    Args:
        mol: RDKit molecule object
        
    Returns:
        Labute ASA value or None if calculation fails
    """
    if not validate_mol(mol):
        return None
    
    try:
        return rdMolDescriptors.CalcLabuteASA(mol)
    except Exception:
        return None


def calculate_slogp_vsa(mol: Chem.rdchem.Mol) -> Optional[List[float]]:
    """Calculates the SlogP-based VSA descriptors of a molecule.
    
    Args:
        mol: RDKit molecule object
        
    Returns:
        List of SlogP_VSA descriptors or None if calculation fails
    """
    if not validate_mol(mol):
        return None
    
    try:
        return list(rdMolDescriptors.SlogP_VSA_(mol))
    except Exception:
        return None


def calculate_smr_vsa(mol: Chem.rdchem.Mol) -> Optional[List[float]]:
    """Calculates the SMR-based VSA descriptors of a molecule.
    
    Args:
        mol: RDKit molecule object
        
    Returns:
        List of SMR_VSA descriptors or None if calculation fails
    """
    if not validate_mol(mol):
        return None
    
    try:
        return list(rdMolDescriptors.SMR_VSA_(mol))
    except Exception:
        return None


def calculate_peoe_vsa(mol: Chem.rdchem.Mol) -> Optional[List[float]]:
    """Calculates the PEOE-based VSA descriptors of a molecule.
    
    Args:
        mol: RDKit molecule object
        
    Returns:
        List of PEOE_VSA descriptors or None if calculation fails
    """
    if not validate_mol(mol):
        return None
    
    try:
        return list(rdMolDescriptors.PEOE_VSA_(mol))
    except Exception:
        return None


def calculate_molecular_formula(mol: Chem.rdchem.Mol) -> Optional[str]:
    """Calculates the molecular formula of a molecule.
    
    Args:
        mol: RDKit molecule object
        
    Returns:
        Molecular formula or None if calculation fails
    """
    if not validate_mol(mol):
        return None
    
    try:
        return rdMolDescriptors.CalcMolFormula(mol)
    except Exception:
        return None


def calculate_descriptor(mol: Chem.rdchem.Mol, descriptor_name: str) -> Optional[Union[float, int, str, List[float], Dict[str, float]]]:
    """Calculates a specific molecular descriptor by name.
    
    Args:
        mol: RDKit molecule object
        descriptor_name: Name of the descriptor to calculate
        
    Returns:
        Calculated descriptor value or None if calculation fails
    """
    if not validate_mol(mol):
        return None
    
    descriptor_functions = {
        "molecular_weight": calculate_molecular_weight,
        "exact_mass": calculate_exact_mass,
        "logp": calculate_logp,
        "tpsa": calculate_tpsa,
        "num_atoms": calculate_num_atoms,
        "num_heavy_atoms": calculate_num_heavy_atoms,
        "num_rings": calculate_num_rings,
        "num_rotatable_bonds": calculate_num_rotatable_bonds,
        "num_h_donors": calculate_num_h_donors,
        "num_h_acceptors": calculate_num_h_acceptors,
        "num_heteroatoms": calculate_num_heteroatoms,
        "num_aromatic_rings": calculate_num_aromatic_rings,
        "num_aliphatic_rings": calculate_num_aliphatic_rings,
        "qed": calculate_qed,
        "lipinski_violations": calculate_lipinski_violations,
        "bertz_index": calculate_bertz_index,
        "chi_indices": calculate_chi_indices,
        "kappa_indices": calculate_kappa_indices,
        "labute_asa": calculate_labute_asa,
        "slogp_vsa": calculate_slogp_vsa,
        "smr_vsa": calculate_smr_vsa,
        "peoe_vsa": calculate_peoe_vsa,
        "molecular_formula": calculate_molecular_formula
    }
    
    if descriptor_name in descriptor_functions:
        return descriptor_functions[descriptor_name](mol)
    else:
        return None


def calculate_descriptor_from_smiles(smiles: str, descriptor_name: str) -> Optional[Union[float, int, str, List[float], Dict[str, float]]]:
    """Calculates a specific molecular descriptor from a SMILES string.
    
    Args:
        smiles: SMILES string
        descriptor_name: Name of the descriptor to calculate
        
    Returns:
        Calculated descriptor value or None if calculation fails
    """
    try:
        mol = smiles_to_mol(smiles)
        if mol is None:
            raise MoleculeException(MOLECULE_ERRORS["INVALID_SMILES"])
        
        result = calculate_descriptor(mol, descriptor_name)
        if result is None:
            raise MoleculeException(MOLECULE_ERRORS["DESCRIPTOR_CALCULATION_FAILED"])
            
        return result
    except Exception as e:
        if isinstance(e, MoleculeException):
            raise
        raise MoleculeException(MOLECULE_ERRORS["DESCRIPTOR_CALCULATION_FAILED"])


def calculate_all_descriptors(mol: Chem.rdchem.Mol) -> Dict[str, Union[float, int, str, List[float], Dict[str, float]]]:
    """Calculates all available molecular descriptors for a molecule.
    
    Args:
        mol: RDKit molecule object
        
    Returns:
        Dictionary of all calculated descriptors
    """
    if not validate_mol(mol):
        raise MoleculeException(MOLECULE_ERRORS["INVALID_SMILES"])
    
    descriptors = {}
    
    # Physicochemical properties
    descriptors["molecular_weight"] = calculate_molecular_weight(mol)
    descriptors["exact_mass"] = calculate_exact_mass(mol)
    descriptors["logp"] = calculate_logp(mol)
    descriptors["tpsa"] = calculate_tpsa(mol)
    
    # Constitutional descriptors
    descriptors["num_atoms"] = calculate_num_atoms(mol)
    descriptors["num_heavy_atoms"] = calculate_num_heavy_atoms(mol)
    descriptors["num_rings"] = calculate_num_rings(mol)
    descriptors["num_rotatable_bonds"] = calculate_num_rotatable_bonds(mol)
    descriptors["num_h_donors"] = calculate_num_h_donors(mol)
    descriptors["num_h_acceptors"] = calculate_num_h_acceptors(mol)
    descriptors["num_heteroatoms"] = calculate_num_heteroatoms(mol)
    descriptors["num_aromatic_rings"] = calculate_num_aromatic_rings(mol)
    descriptors["num_aliphatic_rings"] = calculate_num_aliphatic_rings(mol)
    
    # Drug-likeness descriptors
    descriptors["qed"] = calculate_qed(mol)
    descriptors["lipinski_violations"] = calculate_lipinski_violations(mol)
    
    # Topological descriptors
    descriptors["bertz_index"] = calculate_bertz_index(mol)
    descriptors["chi_indices"] = calculate_chi_indices(mol)
    descriptors["kappa_indices"] = calculate_kappa_indices(mol)
    descriptors["labute_asa"] = calculate_labute_asa(mol)
    
    # Molecular formula
    descriptors["molecular_formula"] = calculate_molecular_formula(mol)
    
    return descriptors


def calculate_all_descriptors_from_smiles(smiles: str) -> Dict[str, Union[float, int, str, List[float], Dict[str, float]]]:
    """Calculates all available molecular descriptors from a SMILES string.
    
    Args:
        smiles: SMILES string
        
    Returns:
        Dictionary of all calculated descriptors
    """
    mol = smiles_to_mol(smiles)
    if mol is None:
        raise MoleculeException(MOLECULE_ERRORS["INVALID_SMILES"])
    
    return calculate_all_descriptors(mol)


def calculate_descriptors_by_category(mol: Chem.rdchem.Mol, category: str) -> Dict[str, Union[float, int, str, List[float], Dict[str, float]]]:
    """Calculates molecular descriptors by category.
    
    Args:
        mol: RDKit molecule object
        category: Category of descriptors to calculate
        
    Returns:
        Dictionary of calculated descriptors in the specified category
    """
    if not validate_mol(mol):
        raise MoleculeException(MOLECULE_ERRORS["INVALID_SMILES"])
    
    if category not in DESCRIPTOR_CATEGORIES:
        categories = ", ".join(DESCRIPTOR_CATEGORIES.keys())
        raise ValueError(f"Invalid category. Available categories: {categories}")
    
    descriptors = {}
    
    if category == "physicochemical":
        descriptors["molecular_weight"] = calculate_molecular_weight(mol)
        descriptors["exact_mass"] = calculate_exact_mass(mol)
        descriptors["logp"] = calculate_logp(mol)
        descriptors["tpsa"] = calculate_tpsa(mol)
        descriptors["labute_asa"] = calculate_labute_asa(mol)
        
    elif category == "topological":
        descriptors["bertz_index"] = calculate_bertz_index(mol)
        descriptors["chi_indices"] = calculate_chi_indices(mol)
        descriptors["kappa_indices"] = calculate_kappa_indices(mol)
        
    elif category == "constitutional":
        descriptors["num_atoms"] = calculate_num_atoms(mol)
        descriptors["num_heavy_atoms"] = calculate_num_heavy_atoms(mol)
        descriptors["num_rings"] = calculate_num_rings(mol)
        descriptors["num_rotatable_bonds"] = calculate_num_rotatable_bonds(mol)
        descriptors["num_h_donors"] = calculate_num_h_donors(mol)
        descriptors["num_h_acceptors"] = calculate_num_h_acceptors(mol)
        descriptors["num_heteroatoms"] = calculate_num_heteroatoms(mol)
        descriptors["num_aromatic_rings"] = calculate_num_aromatic_rings(mol)
        descriptors["num_aliphatic_rings"] = calculate_num_aliphatic_rings(mol)
        descriptors["molecular_formula"] = calculate_molecular_formula(mol)
        
    elif category == "electronic":
        descriptors["peoe_vsa"] = calculate_peoe_vsa(mol)
        
    elif category == "drug_likeness":
        descriptors["qed"] = calculate_qed(mol)
        descriptors["lipinski_violations"] = calculate_lipinski_violations(mol)
        descriptors["slogp_vsa"] = calculate_slogp_vsa(mol)
        descriptors["smr_vsa"] = calculate_smr_vsa(mol)
    
    return descriptors


def is_descriptor_in_range(descriptor_name: str, value: Union[float, int]) -> bool:
    """Checks if a descriptor value is within the expected range.
    
    Args:
        descriptor_name: Name of the descriptor
        value: Descriptor value
        
    Returns:
        True if value is within range, False otherwise
    """
    # If descriptor not in defined ranges, assume it's valid
    if descriptor_name not in PROPERTY_RANGES:
        return True
    
    # Get range and check
    prop_range = PROPERTY_RANGES[descriptor_name]
    min_val = prop_range.get("min")
    max_val = prop_range.get("max")
    
    # Check if value is within range
    if min_val is not None and value < min_val:
        return False
    if max_val is not None and value > max_val:
        return False
    
    return True


def validate_descriptors(descriptors: Dict[str, Union[float, int, str, List[float], Dict[str, float]]]) -> Dict[str, bool]:
    """Validates a set of molecular descriptors against expected ranges.
    
    Args:
        descriptors: Dictionary of descriptor names and values
        
    Returns:
        Dictionary of validation results (descriptor_name: is_valid)
    """
    validation_results = {}
    
    for name, value in descriptors.items():
        # Only check numeric values
        if isinstance(value, (int, float)):
            validation_results[name] = is_descriptor_in_range(name, value)
        else:
            # Non-numeric values are considered valid
            validation_results[name] = True
    
    return validation_results


def get_available_descriptors() -> List[str]:
    """Returns a list of all available molecular descriptors.
    
    Returns:
        List of available descriptor names
    """
    return [
        "molecular_weight",
        "exact_mass",
        "logp",
        "tpsa",
        "num_atoms",
        "num_heavy_atoms",
        "num_rings",
        "num_rotatable_bonds",
        "num_h_donors",
        "num_h_acceptors",
        "num_heteroatoms",
        "num_aromatic_rings",
        "num_aliphatic_rings",
        "qed",
        "lipinski_violations",
        "bertz_index",
        "chi_indices",
        "kappa_indices",
        "labute_asa",
        "slogp_vsa",
        "smr_vsa",
        "peoe_vsa",
        "molecular_formula"
    ]


def get_descriptors_by_category() -> Dict[str, List[str]]:
    """Returns a dictionary of descriptor names organized by category.
    
    Returns:
        Dictionary of descriptor names by category
    """
    descriptor_categories = {
        "physicochemical": [
            "molecular_weight",
            "exact_mass",
            "logp",
            "tpsa",
            "labute_asa"
        ],
        "topological": [
            "bertz_index",
            "chi_indices",
            "kappa_indices"
        ],
        "constitutional": [
            "num_atoms",
            "num_heavy_atoms",
            "num_rings",
            "num_rotatable_bonds",
            "num_h_donors",
            "num_h_acceptors",
            "num_heteroatoms",
            "num_aromatic_rings",
            "num_aliphatic_rings",
            "molecular_formula"
        ],
        "electronic": [
            "peoe_vsa"
        ],
        "drug_likeness": [
            "qed",
            "lipinski_violations",
            "slogp_vsa",
            "smr_vsa"
        ]
    }
    
    return descriptor_categories