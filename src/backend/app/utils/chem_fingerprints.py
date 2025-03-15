"""
Molecular Fingerprints Module

This module provides functionality for generating and comparing molecular fingerprints,
which are binary representations of molecular structures used for similarity searching,
clustering, and machine learning applications. It supports multiple fingerprint types
and similarity metrics for molecular comparison.
"""

# Standard library imports
from typing import Optional, List, Dict, Tuple, Union, Any

# External imports
import numpy as np  # version: 1.23+
from rdkit import Chem  # version: 2023.03+
from rdkit.Chem import AllChem  # version: 2023.03+
from rdkit import DataStructs  # version: 2023.03+

# Internal imports
from ..core.exceptions import MoleculeException
from ..constants.error_messages import MOLECULE_ERRORS
from .rdkit_utils import smiles_to_mol, validate_mol

# Dictionary of supported fingerprint types
FINGERPRINT_TYPES = {
    "morgan": "Morgan (ECFP) fingerprint",
    "maccs": "MACCS keys fingerprint",
    "rdkit": "RDKit topological fingerprint",
    "pattern": "Pattern fingerprint",
    "layered": "Layered fingerprint",
    "atom_pairs": "Atom pairs fingerprint",
    "torsion": "Topological torsion fingerprint"
}

# Dictionary of supported similarity metrics
SIMILARITY_METRICS = {
    "tanimoto": "Tanimoto coefficient (Jaccard index)",
    "dice": "Dice coefficient",
    "cosine": "Cosine similarity",
    "sokal": "Sokal-Sneath index",
    "russel": "Russel-Rao index",
    "kulczynski": "Kulczynski index",
    "mcconnaughey": "McConnaughey index"
}


def get_morgan_fingerprint(mol: Chem.rdchem.Mol, radius: int = 2, n_bits: int = 2048) -> DataStructs.cDataStructs.ExplicitBitVect:
    """Generates Morgan (ECFP) fingerprint for a molecule.
    
    Args:
        mol: RDKit molecule object
        radius: Radius for the Morgan fingerprint (default: 2)
        n_bits: Number of bits in the fingerprint (default: 2048)
        
    Returns:
        Morgan fingerprint bit vector
        
    Raises:
        MoleculeException: If the molecule is invalid
    """
    if not validate_mol(mol):
        raise MoleculeException(MOLECULE_ERRORS["INVALID_SMILES"])
    
    try:
        fingerprint = AllChem.GetMorganFingerprintAsBitVect(mol, radius, nBits=n_bits)
        return fingerprint
    except Exception:
        raise MoleculeException(MOLECULE_ERRORS["FINGERPRINT_GENERATION_FAILED"])


def get_maccs_fingerprint(mol: Chem.rdchem.Mol) -> DataStructs.cDataStructs.ExplicitBitVect:
    """Generates MACCS keys fingerprint for a molecule.
    
    Args:
        mol: RDKit molecule object
        
    Returns:
        MACCS keys fingerprint bit vector
        
    Raises:
        MoleculeException: If the molecule is invalid
    """
    if not validate_mol(mol):
        raise MoleculeException(MOLECULE_ERRORS["INVALID_SMILES"])
    
    try:
        fingerprint = AllChem.GetMACCSKeysFingerprint(mol)
        return fingerprint
    except Exception:
        raise MoleculeException(MOLECULE_ERRORS["FINGERPRINT_GENERATION_FAILED"])


def get_rdkit_fingerprint(mol: Chem.rdchem.Mol, min_path: int = 1, max_path: int = 7, n_bits: int = 2048) -> DataStructs.cDataStructs.ExplicitBitVect:
    """Generates RDKit topological fingerprint for a molecule.
    
    Args:
        mol: RDKit molecule object
        min_path: Minimum path length (default: 1)
        max_path: Maximum path length (default: 7)
        n_bits: Number of bits in the fingerprint (default: 2048)
        
    Returns:
        RDKit fingerprint bit vector
        
    Raises:
        MoleculeException: If the molecule is invalid
    """
    if not validate_mol(mol):
        raise MoleculeException(MOLECULE_ERRORS["INVALID_SMILES"])
    
    try:
        fingerprint = Chem.RDKFingerprint(mol, minPath=min_path, maxPath=max_path, fpSize=n_bits)
        return fingerprint
    except Exception:
        raise MoleculeException(MOLECULE_ERRORS["FINGERPRINT_GENERATION_FAILED"])


def get_pattern_fingerprint(mol: Chem.rdchem.Mol) -> DataStructs.cDataStructs.ExplicitBitVect:
    """Generates pattern fingerprint for a molecule.
    
    Args:
        mol: RDKit molecule object
        
    Returns:
        Pattern fingerprint bit vector
        
    Raises:
        MoleculeException: If the molecule is invalid
    """
    if not validate_mol(mol):
        raise MoleculeException(MOLECULE_ERRORS["INVALID_SMILES"])
    
    try:
        fingerprint = Chem.PatternFingerprint(mol)
        return fingerprint
    except Exception:
        raise MoleculeException(MOLECULE_ERRORS["FINGERPRINT_GENERATION_FAILED"])


def get_layered_fingerprint(mol: Chem.rdchem.Mol, n_bits: int = 2048) -> DataStructs.cDataStructs.ExplicitBitVect:
    """Generates layered fingerprint for a molecule.
    
    Args:
        mol: RDKit molecule object
        n_bits: Number of bits in the fingerprint (default: 2048)
        
    Returns:
        Layered fingerprint bit vector
        
    Raises:
        MoleculeException: If the molecule is invalid
    """
    if not validate_mol(mol):
        raise MoleculeException(MOLECULE_ERRORS["INVALID_SMILES"])
    
    try:
        fingerprint = Chem.LayeredFingerprint(mol, fpSize=n_bits)
        return fingerprint
    except Exception:
        raise MoleculeException(MOLECULE_ERRORS["FINGERPRINT_GENERATION_FAILED"])


def get_atom_pairs_fingerprint(mol: Chem.rdchem.Mol) -> DataStructs.cDataStructs.IntSparseIntVect:
    """Generates atom pairs fingerprint for a molecule.
    
    Args:
        mol: RDKit molecule object
        
    Returns:
        Atom pairs fingerprint vector
        
    Raises:
        MoleculeException: If the molecule is invalid
    """
    if not validate_mol(mol):
        raise MoleculeException(MOLECULE_ERRORS["INVALID_SMILES"])
    
    try:
        fingerprint = AllChem.GetAtomPairFingerprint(mol)
        return fingerprint
    except Exception:
        raise MoleculeException(MOLECULE_ERRORS["FINGERPRINT_GENERATION_FAILED"])


def get_torsion_fingerprint(mol: Chem.rdchem.Mol) -> DataStructs.cDataStructs.IntSparseIntVect:
    """Generates topological torsion fingerprint for a molecule.
    
    Args:
        mol: RDKit molecule object
        
    Returns:
        Torsion fingerprint vector
        
    Raises:
        MoleculeException: If the molecule is invalid
    """
    if not validate_mol(mol):
        raise MoleculeException(MOLECULE_ERRORS["INVALID_SMILES"])
    
    try:
        fingerprint = AllChem.GetTopologicalTorsionFingerprint(mol)
        return fingerprint
    except Exception:
        raise MoleculeException(MOLECULE_ERRORS["FINGERPRINT_GENERATION_FAILED"])


def get_fingerprint(
    mol: Chem.rdchem.Mol, 
    fingerprint_type: str = "morgan", 
    params: Dict[str, Any] = None
) -> Union[DataStructs.cDataStructs.ExplicitBitVect, DataStructs.cDataStructs.IntSparseIntVect]:
    """Generates a fingerprint of the specified type for a molecule.
    
    Args:
        mol: RDKit molecule object
        fingerprint_type: Type of fingerprint to generate (default: "morgan")
        params: Additional parameters for fingerprint generation
        
    Returns:
        Fingerprint vector
        
    Raises:
        MoleculeException: If the molecule is invalid
        ValueError: If the fingerprint type is invalid
    """
    if not validate_mol(mol):
        raise MoleculeException(MOLECULE_ERRORS["INVALID_SMILES"])
    
    if fingerprint_type not in FINGERPRINT_TYPES:
        raise ValueError(f"Invalid fingerprint type: {fingerprint_type}. Available types: {list(FINGERPRINT_TYPES.keys())}")
    
    params = params or {}
    
    try:
        if fingerprint_type == "morgan":
            radius = params.get("radius", 2)
            n_bits = params.get("n_bits", 2048)
            return get_morgan_fingerprint(mol, radius, n_bits)
        elif fingerprint_type == "maccs":
            return get_maccs_fingerprint(mol)
        elif fingerprint_type == "rdkit":
            min_path = params.get("min_path", 1)
            max_path = params.get("max_path", 7)
            n_bits = params.get("n_bits", 2048)
            return get_rdkit_fingerprint(mol, min_path, max_path, n_bits)
        elif fingerprint_type == "pattern":
            return get_pattern_fingerprint(mol)
        elif fingerprint_type == "layered":
            n_bits = params.get("n_bits", 2048)
            return get_layered_fingerprint(mol, n_bits)
        elif fingerprint_type == "atom_pairs":
            return get_atom_pairs_fingerprint(mol)
        elif fingerprint_type == "torsion":
            return get_torsion_fingerprint(mol)
        else:
            # This should never happen due to the validation above
            raise ValueError(f"Unsupported fingerprint type: {fingerprint_type}")
    except Exception as e:
        if isinstance(e, MoleculeException):
            raise
        raise MoleculeException(MOLECULE_ERRORS["FINGERPRINT_GENERATION_FAILED"])


def get_fingerprint_from_smiles(
    smiles: str, 
    fingerprint_type: str = "morgan", 
    params: Dict[str, Any] = None
) -> Union[DataStructs.cDataStructs.ExplicitBitVect, DataStructs.cDataStructs.IntSparseIntVect]:
    """Generates a fingerprint of the specified type from a SMILES string.
    
    Args:
        smiles: SMILES string representation of the molecule
        fingerprint_type: Type of fingerprint to generate (default: "morgan")
        params: Additional parameters for fingerprint generation
        
    Returns:
        Fingerprint vector
        
    Raises:
        MoleculeException: If the SMILES string is invalid
        ValueError: If the fingerprint type is invalid
    """
    mol = smiles_to_mol(smiles)
    if mol is None:
        raise MoleculeException(MOLECULE_ERRORS["INVALID_SMILES"])
    
    return get_fingerprint(mol, fingerprint_type, params)


def calculate_similarity(
    fp1: Union[DataStructs.cDataStructs.ExplicitBitVect, DataStructs.cDataStructs.IntSparseIntVect],
    fp2: Union[DataStructs.cDataStructs.ExplicitBitVect, DataStructs.cDataStructs.IntSparseIntVect],
    metric: str = "tanimoto"
) -> float:
    """Calculates similarity between two fingerprints using the specified metric.
    
    Args:
        fp1: First fingerprint
        fp2: Second fingerprint
        metric: Similarity metric to use (default: "tanimoto")
        
    Returns:
        Similarity score (0-1 range)
        
    Raises:
        ValueError: If the metric is invalid or fingerprints are incompatible
    """
    if metric not in SIMILARITY_METRICS:
        raise ValueError(f"Invalid similarity metric: {metric}. Available metrics: {list(SIMILARITY_METRICS.keys())}")
    
    try:
        if metric == "tanimoto":
            return DataStructs.TanimotoSimilarity(fp1, fp2)
        elif metric == "dice":
            return DataStructs.DiceSimilarity(fp1, fp2)
        elif metric == "cosine":
            return DataStructs.CosineSimilarity(fp1, fp2)
        elif metric == "sokal":
            return DataStructs.SokalSimilarity(fp1, fp2)
        elif metric == "russel":
            return DataStructs.RusselSimilarity(fp1, fp2)
        elif metric == "kulczynski":
            return DataStructs.KulczynskiSimilarity(fp1, fp2)
        elif metric == "mcconnaughey":
            return DataStructs.McConnaugheySimilarity(fp1, fp2)
        else:
            # This should never happen due to the validation above
            raise ValueError(f"Unsupported similarity metric: {metric}")
    except Exception as e:
        if isinstance(e, ValueError):
            raise
        raise ValueError(f"Error calculating similarity: {str(e)}")


def calculate_similarity_from_smiles(
    smiles1: str,
    smiles2: str,
    fingerprint_type: str = "morgan",
    metric: str = "tanimoto",
    params: Dict[str, Any] = None
) -> float:
    """Calculates similarity between two molecules represented as SMILES strings.
    
    Args:
        smiles1: SMILES string of the first molecule
        smiles2: SMILES string of the second molecule
        fingerprint_type: Type of fingerprint to use (default: "morgan")
        metric: Similarity metric to use (default: "tanimoto")
        params: Additional parameters for fingerprint generation
        
    Returns:
        Similarity score (0-1 range)
        
    Raises:
        MoleculeException: If either SMILES string is invalid
        ValueError: If the fingerprint type or metric is invalid
    """
    fp1 = get_fingerprint_from_smiles(smiles1, fingerprint_type, params)
    fp2 = get_fingerprint_from_smiles(smiles2, fingerprint_type, params)
    
    return calculate_similarity(fp1, fp2, metric)


def find_similar_molecules(
    query_mol: Chem.rdchem.Mol,
    mol_database: List[Chem.rdchem.Mol],
    fingerprint_type: str = "morgan",
    metric: str = "tanimoto",
    threshold: float = 0.7,
    params: Dict[str, Any] = None
) -> List[Tuple[Chem.rdchem.Mol, float]]:
    """Finds molecules similar to a query molecule based on fingerprint similarity.
    
    Args:
        query_mol: Query molecule
        mol_database: List of molecules to search
        fingerprint_type: Type of fingerprint to use (default: "morgan")
        metric: Similarity metric to use (default: "tanimoto")
        threshold: Minimum similarity threshold (default: 0.7)
        params: Additional parameters for fingerprint generation
        
    Returns:
        List of (molecule, similarity) pairs above threshold, sorted by similarity
        
    Raises:
        MoleculeException: If the query molecule is invalid
        ValueError: If the fingerprint type or metric is invalid
    """
    if not validate_mol(query_mol):
        raise MoleculeException(MOLECULE_ERRORS["INVALID_SMILES"])
    
    query_fp = get_fingerprint(query_mol, fingerprint_type, params)
    
    results = []
    for mol in mol_database:
        if validate_mol(mol):
            mol_fp = get_fingerprint(mol, fingerprint_type, params)
            similarity = calculate_similarity(query_fp, mol_fp, metric)
            
            if similarity >= threshold:
                results.append((mol, similarity))
    
    # Sort by similarity in descending order
    results.sort(key=lambda x: x[1], reverse=True)
    
    return results


def find_similar_molecules_from_smiles(
    query_smiles: str,
    smiles_database: List[str],
    fingerprint_type: str = "morgan",
    metric: str = "tanimoto",
    threshold: float = 0.7,
    params: Dict[str, Any] = None
) -> List[Tuple[str, float]]:
    """Finds molecules similar to a query SMILES string based on fingerprint similarity.
    
    Args:
        query_smiles: Query molecule SMILES
        smiles_database: List of SMILES strings to search
        fingerprint_type: Type of fingerprint to use (default: "morgan")
        metric: Similarity metric to use (default: "tanimoto")
        threshold: Minimum similarity threshold (default: 0.7)
        params: Additional parameters for fingerprint generation
        
    Returns:
        List of (SMILES, similarity) pairs above threshold, sorted by similarity
        
    Raises:
        MoleculeException: If the query SMILES is invalid
        ValueError: If the fingerprint type or metric is invalid
    """
    query_mol = smiles_to_mol(query_smiles)
    if query_mol is None:
        raise MoleculeException(MOLECULE_ERRORS["INVALID_SMILES"])
    
    query_fp = get_fingerprint(query_mol, fingerprint_type, params)
    
    results = []
    for smiles in smiles_database:
        mol = smiles_to_mol(smiles)
        if mol is not None:
            mol_fp = get_fingerprint(mol, fingerprint_type, params)
            similarity = calculate_similarity(query_fp, mol_fp, metric)
            
            if similarity >= threshold:
                results.append((smiles, similarity))
    
    # Sort by similarity in descending order
    results.sort(key=lambda x: x[1], reverse=True)
    
    return results


def has_substructure(mol: Chem.rdchem.Mol, substructure: Chem.rdchem.Mol) -> bool:
    """Checks if a molecule contains a specified substructure.
    
    Args:
        mol: Molecule to check
        substructure: Substructure to search for
        
    Returns:
        True if the molecule contains the substructure, False otherwise
        
    Raises:
        MoleculeException: If either molecule is invalid
    """
    if not validate_mol(mol):
        raise MoleculeException(MOLECULE_ERRORS["INVALID_SMILES"])
    
    if not validate_mol(substructure):
        raise MoleculeException(MOLECULE_ERRORS["INVALID_SMILES"])
    
    return mol.HasSubstructMatch(substructure)


def has_substructure_from_smiles(smiles: str, substructure_smiles: str) -> bool:
    """Checks if a molecule contains a specified substructure using SMILES strings.
    
    Args:
        smiles: SMILES string of the molecule to check
        substructure_smiles: SMILES string of the substructure to search for
        
    Returns:
        True if the molecule contains the substructure, False otherwise
        
    Raises:
        MoleculeException: If either SMILES string is invalid
    """
    mol = smiles_to_mol(smiles)
    if mol is None:
        raise MoleculeException(MOLECULE_ERRORS["INVALID_SMILES"])
    
    substructure = smiles_to_mol(substructure_smiles)
    if substructure is None:
        raise MoleculeException(MOLECULE_ERRORS["INVALID_SMILES"])
    
    return has_substructure(mol, substructure)


def find_molecules_with_substructure(
    substructure: Chem.rdchem.Mol,
    mol_database: List[Chem.rdchem.Mol]
) -> List[Chem.rdchem.Mol]:
    """Finds molecules containing a specified substructure.
    
    Args:
        substructure: Substructure to search for
        mol_database: List of molecules to search
        
    Returns:
        List of molecules containing the substructure
        
    Raises:
        MoleculeException: If the substructure is invalid
    """
    if not validate_mol(substructure):
        raise MoleculeException(MOLECULE_ERRORS["INVALID_SMILES"])
    
    results = []
    for mol in mol_database:
        if validate_mol(mol) and has_substructure(mol, substructure):
            results.append(mol)
    
    return results


def find_molecules_with_substructure_from_smiles(
    substructure_smiles: str,
    smiles_database: List[str]
) -> List[str]:
    """Finds molecules containing a specified substructure using SMILES strings.
    
    Args:
        substructure_smiles: SMILES string of the substructure to search for
        smiles_database: List of SMILES strings to search
        
    Returns:
        List of SMILES strings containing the substructure
        
    Raises:
        MoleculeException: If the substructure SMILES is invalid
    """
    substructure = smiles_to_mol(substructure_smiles)
    if substructure is None:
        raise MoleculeException(MOLECULE_ERRORS["INVALID_SMILES"])
    
    results = []
    for smiles in smiles_database:
        mol = smiles_to_mol(smiles)
        if mol is not None and has_substructure(mol, substructure):
            results.append(smiles)
    
    return results


def fingerprint_to_numpy(
    fingerprint: Union[DataStructs.cDataStructs.ExplicitBitVect, DataStructs.cDataStructs.IntSparseIntVect]
) -> np.ndarray:
    """Converts a fingerprint to a numpy array for machine learning applications.
    
    Args:
        fingerprint: RDKit fingerprint (bit vector or int vector)
        
    Returns:
        Numpy array representation of the fingerprint
        
    Raises:
        ValueError: If the fingerprint type is not supported
    """
    if isinstance(fingerprint, DataStructs.cDataStructs.ExplicitBitVect):
        # Convert bit vector to numpy array
        array = np.zeros((1,), dtype=np.int8)
        DataStructs.ConvertToNumpyArray(fingerprint, array)
        return array
    elif isinstance(fingerprint, DataStructs.cDataStructs.IntSparseIntVect):
        # Convert sparse int vector to numpy array
        size = fingerprint.GetLength()
        array = np.zeros(size, dtype=np.int32)
        for idx, value in fingerprint.GetNonzeroElements().items():
            array[idx] = value
        return array
    else:
        raise ValueError(f"Unsupported fingerprint type: {type(fingerprint)}")


def batch_fingerprints_to_numpy(
    fingerprints: List[Union[DataStructs.cDataStructs.ExplicitBitVect, DataStructs.cDataStructs.IntSparseIntVect]]
) -> np.ndarray:
    """Converts a batch of fingerprints to a numpy array for machine learning applications.
    
    Args:
        fingerprints: List of RDKit fingerprints
        
    Returns:
        2D numpy array with fingerprints as rows
        
    Raises:
        ValueError: If any fingerprint type is not supported or fingerprints are inconsistent
    """
    if not fingerprints:
        return np.array([])
    
    # Convert each fingerprint to a numpy array
    arrays = []
    for fp in fingerprints:
        arrays.append(fingerprint_to_numpy(fp))
    
    # Stack arrays into a 2D array
    return np.vstack(arrays)