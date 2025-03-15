"""
CRUD operations for molecule data in the Molecular Data Management and CRO Integration Platform.

This module extends the base CRUD class with molecule-specific operations including property
management, library associations, and specialized search capabilities.
"""

from typing import List, Dict, Optional, Any, Union, Tuple
import uuid
from datetime import datetime

from sqlalchemy.orm import Session
from sqlalchemy import select, func, or_, and_, desc, asc

from .base import CRUDBase
from ..models.molecule import Molecule, MoleculeStatus, library_molecule, molecule_property
from ..models.library import Library
from ..constants.molecule_properties import PropertySource
from ..schemas.molecule import MoleculeCreate, MoleculeUpdate
from ..core.logging import get_logger
from ..utils.chem_fingerprints import calculate_fingerprint, calculate_similarity
from ..utils.rdkit_utils import check_substructure_match
from ..utils.smiles import validate_smiles

# Initialize logger
logger = get_logger(__name__)


class CRUDMolecule(CRUDBase[Molecule, MoleculeCreate, MoleculeUpdate]):
    """CRUD operations for molecule data with specialized methods for molecular operations."""
    
    def __init__(self):
        """Initialize the CRUD molecule class with the Molecule model."""
        super().__init__(Molecule)
    
    def create_from_smiles(self, smiles: str, created_by: Optional[uuid.UUID] = None, db: Optional[Session] = None) -> Molecule:
        """
        Create a new molecule from a SMILES string.
        
        Args:
            smiles: SMILES string representation of the molecule
            created_by: ID of the user creating the molecule
            db: Database session
            
        Returns:
            Created molecule instance
        """
        db_session = db or self.db
        
        # Validate SMILES
        if not validate_smiles(smiles):
            logger.error(f"Invalid SMILES string: {smiles}")
            raise ValueError("Invalid SMILES string")
        
        # Check if molecule already exists by SMILES
        existing_molecule = self.get_by_smiles(smiles, db=db_session)
        if existing_molecule:
            logger.debug(f"Molecule with SMILES {smiles} already exists")
            return existing_molecule
        
        # Create new molecule from SMILES
        try:
            molecule = Molecule.from_smiles(smiles, created_by)
            molecule.status = MoleculeStatus.AVAILABLE.value
            
            # Add to database
            db_session.add(molecule)
            db_session.commit()
            db_session.refresh(molecule)
            
            logger.info(f"Created new molecule from SMILES: {smiles[:50]}...")
            return molecule
        except Exception as e:
            db_session.rollback()
            logger.error(f"Failed to create molecule from SMILES: {str(e)}")
            raise
    
    def create_with_properties(self, obj_in: MoleculeCreate, db: Optional[Session] = None) -> Molecule:
        """
        Create a new molecule with properties.
        
        Args:
            obj_in: Molecule creation data including properties
            db: Database session
            
        Returns:
            Created molecule instance
        """
        db_session = db or self.db
        
        # Create base molecule
        molecule = super().create(obj_in, db=db_session)
        
        # Add properties if provided
        if obj_in.properties:
            for prop in obj_in.properties:
                molecule.set_property(
                    prop.name,
                    prop.value,
                    PropertySource.IMPORTED.value,
                    prop.units
                )
        
        # Calculate additional properties
        molecule.calculate_properties()
        
        # Commit changes
        db_session.add(molecule)
        db_session.commit()
        db_session.refresh(molecule)
        
        logger.info(f"Created molecule with ID: {molecule.id} and properties")
        return molecule
    
    def update_with_properties(self, db_obj: Molecule, obj_in: MoleculeUpdate, db: Optional[Session] = None) -> Molecule:
        """
        Update a molecule with new data including properties.
        
        Args:
            db_obj: Existing molecule instance
            obj_in: Molecule update data
            db: Database session
            
        Returns:
            Updated molecule instance
        """
        db_session = db or self.db
        
        # Track if SMILES was updated to recalculate properties
        old_smiles = db_obj.smiles
        
        # Update base attributes
        molecule = super().update(db_obj, obj_in, db=db_session)
        
        # Update properties if provided
        if obj_in.properties:
            for prop in obj_in.properties:
                molecule.set_property(
                    prop.name,
                    prop.value,
                    PropertySource.IMPORTED.value,
                    prop.units
                )
        
        # Recalculate properties if SMILES was updated
        if obj_in.smiles and obj_in.smiles != old_smiles:
            molecule.calculate_properties()
        
        # Commit changes
        db_session.add(molecule)
        db_session.commit()
        db_session.refresh(molecule)
        
        logger.info(f"Updated molecule with ID: {molecule.id}")
        return molecule
    
    def get_by_smiles(self, smiles: str, db: Optional[Session] = None) -> Optional[Molecule]:
        """
        Get a molecule by its SMILES string.
        
        Args:
            smiles: SMILES string to search for
            db: Database session
            
        Returns:
            Molecule instance if found, None otherwise
        """
        db_session = db or self.db
        return db_session.query(Molecule).filter(Molecule.smiles == smiles).first()
    
    def get_by_inchi_key(self, inchi_key: str, db: Optional[Session] = None) -> Optional[Molecule]:
        """
        Get a molecule by its InChI Key.
        
        Args:
            inchi_key: InChI Key to search for
            db: Database session
            
        Returns:
            Molecule instance if found, None otherwise
        """
        db_session = db or self.db
        return db_session.query(Molecule).filter(Molecule.inchi_key == inchi_key).first()
    
    def get_with_properties(self, molecule_id: uuid.UUID, db: Optional[Session] = None) -> Optional[Molecule]:
        """
        Get a molecule by ID with all its properties.
        
        Args:
            molecule_id: Molecule ID
            db: Database session
            
        Returns:
            Molecule instance with properties if found, None otherwise
        """
        db_session = db or self.db
        
        # Query molecule with properties relationship joined
        return db_session.query(Molecule).options(
            db_session.joinedload(Molecule.properties)
        ).filter(Molecule.id == molecule_id).first()
    
    def get_by_library(self, library_id: uuid.UUID, db: Optional[Session] = None, 
                       skip: int = 0, limit: int = 100) -> Dict[str, Any]:
        """
        Get molecules in a specific library with pagination.
        
        Args:
            library_id: Library ID
            db: Database session
            skip: Number of records to skip
            limit: Maximum number of records to return
            
        Returns:
            Dictionary with molecules and pagination info
        """
        db_session = db or self.db
        
        # Query molecules joined with library_molecule table
        query = db_session.query(Molecule).join(
            library_molecule,
            Molecule.id == library_molecule.c.molecule_id
        ).filter(
            library_molecule.c.library_id == library_id
        )
        
        # Count total molecules in library
        total = query.count()
        
        # Apply pagination
        molecules = query.offset(skip).limit(limit).all()
        
        # Return dictionary with items and pagination metadata
        return {
            "items": molecules,
            "total": total,
            "page": skip // limit + 1 if limit > 0 else 1,
            "size": limit,
            "pages": (total + limit - 1) // limit if limit > 0 else 1
        }
    
    def add_to_library(self, molecule_id: uuid.UUID, library_id: uuid.UUID, 
                       added_by: uuid.UUID, db: Optional[Session] = None) -> bool:
        """
        Add a molecule to a library.
        
        Args:
            molecule_id: Molecule ID
            library_id: Library ID
            added_by: User ID who is adding the molecule
            db: Database session
            
        Returns:
            True if added, False if already in library
        """
        db_session = db or self.db
        
        # Get molecule and library
        molecule = self.get(molecule_id, db=db_session)
        library = db_session.query(Library).get(library_id)
        
        if not molecule or not library:
            logger.error(f"Molecule or library not found: molecule_id={molecule_id}, library_id={library_id}")
            return False
        
        # Check if molecule is already in library
        existing = db_session.query(library_molecule).filter(
            library_molecule.c.molecule_id == molecule_id,
            library_molecule.c.library_id == library_id
        ).first()
        
        if existing:
            logger.debug(f"Molecule {molecule_id} already in library {library_id}")
            return False
        
        # Add molecule to library
        try:
            db_session.execute(
                library_molecule.insert().values(
                    molecule_id=molecule_id,
                    library_id=library_id,
                    added_by=added_by,
                    added_at=datetime.utcnow()
                )
            )
            db_session.commit()
            logger.info(f"Added molecule {molecule_id} to library {library_id}")
            return True
        except Exception as e:
            db_session.rollback()
            logger.error(f"Failed to add molecule to library: {str(e)}")
            raise
    
    def remove_from_library(self, molecule_id: uuid.UUID, library_id: uuid.UUID, 
                           db: Optional[Session] = None) -> bool:
        """
        Remove a molecule from a library.
        
        Args:
            molecule_id: Molecule ID
            library_id: Library ID
            db: Database session
            
        Returns:
            True if removed, False if not in library
        """
        db_session = db or self.db
        
        # Check if molecule is in library
        existing = db_session.query(library_molecule).filter(
            library_molecule.c.molecule_id == molecule_id,
            library_molecule.c.library_id == library_id
        ).first()
        
        if not existing:
            logger.debug(f"Molecule {molecule_id} not in library {library_id}")
            return False
        
        # Remove molecule from library
        try:
            db_session.execute(
                library_molecule.delete().where(
                    library_molecule.c.molecule_id == molecule_id,
                    library_molecule.c.library_id == library_id
                )
            )
            db_session.commit()
            logger.info(f"Removed molecule {molecule_id} from library {library_id}")
            return True
        except Exception as e:
            db_session.rollback()
            logger.error(f"Failed to remove molecule from library: {str(e)}")
            raise
    
    def set_property(self, molecule_id: uuid.UUID, property_name: str, value: Any, 
                    source: PropertySource, units: Optional[str] = None, 
                    db: Optional[Session] = None) -> bool:
        """
        Set a property value on a molecule.
        
        Args:
            molecule_id: Molecule ID
            property_name: Property name
            value: Property value
            source: Source of the property value
            units: Units of measurement (optional)
            db: Database session
            
        Returns:
            True if property was set, False otherwise
        """
        db_session = db or self.db
        
        # Get molecule
        molecule = self.get(molecule_id, db=db_session)
        if not molecule:
            logger.error(f"Molecule not found: {molecule_id}")
            return False
        
        try:
            # Set property
            molecule.set_property(property_name, value, source, units)
            
            # Commit changes
            db_session.add(molecule)
            db_session.commit()
            
            logger.debug(f"Set property {property_name}={value} on molecule {molecule_id}")
            return True
        except Exception as e:
            db_session.rollback()
            logger.error(f"Failed to set property: {str(e)}")
            raise
    
    def get_property(self, molecule_id: uuid.UUID, property_name: str, 
                     source: Optional[PropertySource] = None, 
                     db: Optional[Session] = None) -> Optional[Any]:
        """
        Get a property value from a molecule.
        
        Args:
            molecule_id: Molecule ID
            property_name: Property name
            source: Filter by property source (optional)
            db: Database session
            
        Returns:
            Property value if found, None otherwise
        """
        db_session = db or self.db
        
        # Get molecule
        molecule = self.get(molecule_id, db=db_session)
        if not molecule:
            logger.error(f"Molecule not found: {molecule_id}")
            return None
        
        # Get property value
        return molecule.get_property(property_name, source.value if source else None)
    
    def filter_molecules(self, filter_params: Dict[str, Any], db: Optional[Session] = None,
                         skip: int = 0, limit: int = 100, sort_by: Optional[str] = None,
                         descending: bool = False) -> Dict[str, Any]:
        """
        Filter molecules based on various criteria.
        
        Args:
            filter_params: Dictionary of filter parameters
            db: Database session
            skip: Number of records to skip
            limit: Maximum number of records to return
            sort_by: Field to sort by
            descending: Whether to sort in descending order
            
        Returns:
            Dictionary with filtered molecules and pagination info
        """
        db_session = db or self.db
        
        # Start with a base query
        query = db_session.query(Molecule)
        
        # Apply text filters
        if filter_params.get("smiles_contains"):
            query = query.filter(Molecule.smiles.ilike(f"%{filter_params['smiles_contains']}%"))
        
        if filter_params.get("formula_contains"):
            query = query.filter(Molecule.formula.ilike(f"%{filter_params['formula_contains']}%"))
        
        # Apply status filter
        if filter_params.get("status"):
            query = query.filter(Molecule.status == filter_params["status"])
        
        # Apply creator filter
        if filter_params.get("created_by"):
            query = query.filter(Molecule.created_by == filter_params["created_by"])
        
        # Apply library filter
        if filter_params.get("library_id"):
            query = query.join(
                library_molecule,
                Molecule.id == library_molecule.c.molecule_id
            ).filter(
                library_molecule.c.library_id == filter_params["library_id"]
            )
        
        # Apply property range filters
        if filter_params.get("property_ranges"):
            for prop_name, range_dict in filter_params["property_ranges"].items():
                min_value = range_dict.get("min")
                max_value = range_dict.get("max")
                
                # Join with property table
                subquery = db_session.query(molecule_property.c.molecule_id).filter(
                    molecule_property.c.name == prop_name
                )
                
                # Apply min/max filters
                if min_value is not None:
                    subquery = subquery.filter(molecule_property.c.value >= min_value)
                
                if max_value is not None:
                    subquery = subquery.filter(molecule_property.c.value <= max_value)
                
                # Apply subquery filter
                query = query.filter(Molecule.id.in_(subquery))
        
        # Apply sorting
        if sort_by:
            # Sort by standard fields
            if hasattr(Molecule, sort_by):
                order_func = desc if descending else asc
                query = query.order_by(order_func(getattr(Molecule, sort_by)))
            # Sort by property
            elif filter_params.get("property_sort"):
                # This is more complex and would require a specific join and ordering
                # Simplified implementation here
                pass
        else:
            # Default sort by created_at descending
            query = query.order_by(desc(Molecule.created_at))
        
        # Count total filtered molecules
        total = query.count()
        
        # Apply pagination
        molecules = query.offset(skip).limit(limit).all()
        
        # Return dictionary with items and pagination metadata
        return {
            "items": molecules,
            "total": total,
            "page": skip // limit + 1 if limit > 0 else 1,
            "size": limit,
            "pages": (total + limit - 1) // limit if limit > 0 else 1
        }
    
    def search_by_similarity(self, query_smiles: str, threshold: float = 0.7,
                            fingerprint_type: str = "morgan", db: Optional[Session] = None,
                            skip: int = 0, limit: int = 100) -> Dict[str, Any]:
        """
        Search for molecules similar to a query molecule.
        
        Args:
            query_smiles: SMILES string of the query molecule
            threshold: Minimum similarity threshold (0-1)
            fingerprint_type: Type of fingerprint to use
            db: Database session
            skip: Number of records to skip
            limit: Maximum number of records to return
            
        Returns:
            Dictionary with similar molecules and similarity scores
        """
        db_session = db or self.db
        
        # Validate query SMILES
        if not validate_smiles(query_smiles):
            logger.error(f"Invalid query SMILES: {query_smiles}")
            raise ValueError("Invalid query SMILES string")
        
        # Calculate query fingerprint
        query_fp = calculate_fingerprint(query_smiles, fingerprint_type)
        
        # Get all molecules
        molecules = db_session.query(Molecule).all()
        
        # Calculate similarity for each molecule
        results = []
        for molecule in molecules:
            try:
                similarity = calculate_similarity(query_fp, molecule.smiles, fingerprint_type)
                
                if similarity >= threshold:
                    results.append((molecule, similarity))
            except Exception as e:
                logger.warning(f"Error calculating similarity for molecule {molecule.id}: {str(e)}")
                continue
        
        # Sort by similarity (descending)
        results.sort(key=lambda x: x[1], reverse=True)
        
        # Apply pagination
        paginated_results = results[skip:skip + limit]
        
        # Format results
        items = []
        for molecule, similarity in paginated_results:
            molecule_dict = molecule.to_dict()
            molecule_dict["similarity"] = similarity
            items.append(molecule_dict)
        
        # Return dictionary with items and pagination metadata
        return {
            "items": items,
            "total": len(results),
            "page": skip // limit + 1 if limit > 0 else 1,
            "size": limit,
            "pages": (len(results) + limit - 1) // limit if limit > 0 else 1
        }
    
    def search_by_substructure(self, query_smiles: str, db: Optional[Session] = None,
                              skip: int = 0, limit: int = 100) -> Dict[str, Any]:
        """
        Search for molecules containing a substructure.
        
        Args:
            query_smiles: SMILES string of the substructure
            db: Database session
            skip: Number of records to skip
            limit: Maximum number of records to return
            
        Returns:
            Dictionary with matching molecules
        """
        db_session = db or self.db
        
        # Validate query SMILES
        if not validate_smiles(query_smiles):
            logger.error(f"Invalid query SMILES: {query_smiles}")
            raise ValueError("Invalid query SMILES string")
        
        # Get all molecules
        molecules = db_session.query(Molecule).all()
        
        # Check for substructure match
        results = []
        for molecule in molecules:
            try:
                if check_substructure_match(molecule.smiles, query_smiles):
                    results.append(molecule)
            except Exception as e:
                logger.warning(f"Error checking substructure for molecule {molecule.id}: {str(e)}")
                continue
        
        # Apply pagination
        total = len(results)
        paginated_results = results[skip:skip + limit]
        
        # Return dictionary with items and pagination metadata
        return {
            "items": paginated_results,
            "total": total,
            "page": skip // limit + 1 if limit > 0 else 1,
            "size": limit,
            "pages": (total + limit - 1) // limit if limit > 0 else 1
        }
    
    def batch_create(self, obj_list: List[MoleculeCreate], db: Optional[Session] = None) -> Dict[str, Any]:
        """
        Create multiple molecules in a batch operation.
        
        Args:
            obj_list: List of molecule creation data
            db: Database session
            
        Returns:
            Dictionary with created molecules and statistics
        """
        db_session = db or self.db
        
        # Track statistics
        created = []
        skipped = []
        failed = []
        
        for obj in obj_list:
            try:
                # Check if molecule already exists
                existing = self.get_by_smiles(obj.smiles, db=db_session)
                if existing:
                    skipped.append({"smiles": obj.smiles, "id": str(existing.id)})
                    continue
                
                # Create new molecule with properties
                molecule = self.create_with_properties(obj, db=db_session)
                created.append(molecule)
            except Exception as e:
                logger.error(f"Failed to create molecule: {str(e)}")
                failed.append({"smiles": obj.smiles, "error": str(e)})
        
        # Commit all changes
        try:
            db_session.commit()
        except Exception as e:
            db_session.rollback()
            logger.error(f"Failed to commit batch creation: {str(e)}")
            raise
        
        # Return statistics
        return {
            "created": created,
            "skipped": skipped,
            "failed": failed,
            "total": len(obj_list),
            "created_count": len(created),
            "skipped_count": len(skipped),
            "failed_count": len(failed)
        }


# Create a singleton instance
molecule = CRUDMolecule()