"""
Molecule Model Module

This module defines the Molecule model for the Molecular Data Management and CRO Integration Platform.
It represents the core molecular entity with chemical structure information, properties, and
relationships to other entities such as libraries, submissions, predictions, and results.
"""
from enum import Enum
from sqlalchemy import Column, String, Text, Float, Boolean, DateTime, ForeignKey, Table, UUID, JSON, Index
from sqlalchemy.orm import relationship, validates
from datetime import datetime
from uuid import uuid4

from ..db.base_class import Base
from ..utils.smiles import validate_smiles, get_inchi_key_from_smiles, get_molecular_formula_from_smiles
from ..utils.rdkit_utils import calculate_basic_properties
from ..core.exceptions import MoleculeException
from ..constants.molecule_properties import PropertySource, REQUIRED_PROPERTIES

# Association table for many-to-many relationship between libraries and molecules
library_molecule = Table(
    'library_molecule', 
    Base.metadata,
    Column('library_id', UUID, ForeignKey('library.id'), primary_key=True),
    Column('molecule_id', UUID, ForeignKey('molecule.id'), primary_key=True),
    Column('added_at', DateTime, default=datetime.utcnow),
    Column('added_by', UUID, ForeignKey('user.id'))
)

# Table for storing molecule properties with values and sources
molecule_property = Table(
    'molecule_property', 
    Base.metadata,
    Column('molecule_id', UUID, ForeignKey('molecule.id'), primary_key=True),
    Column('name', String(100), primary_key=True),
    Column('value', Float),
    Column('units', String(50)),
    Column('source', String(50)),
    Column('created_at', DateTime, default=datetime.utcnow)
)

class MoleculeStatus(Enum):
    """Enumeration of possible molecule statuses in the workflow."""
    AVAILABLE = "available"  # Available for use
    PENDING = "pending"      # Pending submission
    TESTING = "testing"      # Currently in testing at CRO
    RESULTS = "results"      # Results received
    ARCHIVED = "archived"    # Archived/inactive

class Molecule(Base):
    """SQLAlchemy model representing a molecular structure with its properties and relationships."""
    
    # Basic molecule attributes
    smiles = Column(Text, nullable=False)
    inchi_key = Column(String(27), unique=True, index=True, nullable=False)
    formula = Column(String(255))
    molecular_weight = Column(Float)
    metadata = Column(JSON)
    status = Column(String(50), default=MoleculeStatus.AVAILABLE.value)
    
    # Foreign keys
    created_by = Column(UUID, ForeignKey('user.id'))
    
    # Relationships
    properties = relationship("MoleculeProperty", backref="molecule", cascade="all, delete-orphan")
    libraries = relationship("Library", secondary=library_molecule, back_populates="molecules")
    submissions = relationship("Submission", secondary="submission_molecule", back_populates="molecules")
    predictions = relationship("Prediction", back_populates="molecule")
    results = relationship("Result", back_populates="molecule")
    creator = relationship("User")
    
    # Create indexes for efficient querying
    __table_args__ = (
        Index('ix_molecule_status', 'status'),
        Index('ix_molecule_created_at', 'created_at')
    )
    
    @validates('smiles')
    def validate_smiles(self, key, smiles):
        """Validates SMILES string format and chemical validity."""
        if not smiles:
            raise MoleculeException("SMILES string cannot be empty")
            
        if not validate_smiles(smiles):
            raise MoleculeException("Invalid SMILES string")
            
        return smiles
    
    def generate_inchi_key(self):
        """Generates InChI Key from SMILES if not already set."""
        if not self.inchi_key and self.smiles:
            try:
                self.inchi_key = get_inchi_key_from_smiles(self.smiles)
            except Exception as e:
                raise MoleculeException(f"Failed to generate InChI Key: {str(e)}")
                
        return self.inchi_key
    
    def calculate_properties(self):
        """Calculates and stores basic molecular properties."""
        if not self.smiles:
            raise MoleculeException("SMILES string is required to calculate properties")
            
        # Calculate basic properties
        try:
            properties = calculate_basic_properties(self.smiles)
            
            # Update basic attributes if not already set
            if not self.molecular_weight and "molecular_weight" in properties:
                self.molecular_weight = properties["molecular_weight"]
                
            if not self.formula and "formula" in properties:
                self.formula = properties["formula"]
                
            # Create property entries for each calculated property
            for name, value in properties.items():
                if name not in ["molecular_weight", "formula"]:  # These are already stored as attributes
                    self.set_property(name, value, PropertySource.CALCULATED.value)
                    
            return properties
        except Exception as e:
            raise MoleculeException(f"Failed to calculate properties: {str(e)}")
    
    def get_property(self, name, source=None):
        """Gets a specific property value by name."""
        for prop in self.properties:
            if prop.name == name:
                if source is None or prop.source == source:
                    return prop.value
        return None
    
    def set_property(self, name, value, source=PropertySource.IMPORTED.value, units=None):
        """Sets a property value with specified source."""
        # Find existing property
        for prop in self.properties:
            if prop.name == name:
                # Update existing property
                prop.value = value
                prop.source = source
                if units:
                    prop.units = units
                self.updated_at = datetime.utcnow()
                return
                
        # Create new property
        from .molecule_property import MoleculeProperty
        new_prop = MoleculeProperty(
            molecule_id=self.id,
            name=name,
            value=value,
            source=source,
            units=units
        )
        self.properties.append(new_prop)
        self.updated_at = datetime.utcnow()
    
    def get_properties_by_source(self, source):
        """Gets all properties from a specific source."""
        result = {}
        for prop in self.properties:
            if prop.source == source:
                result[prop.name] = prop.value
        return result
    
    def has_required_properties(self):
        """Checks if molecule has all required properties."""
        # Check basic attributes
        if not self.smiles or not self.inchi_key:
            return False
            
        # Check other required properties
        for prop_name in REQUIRED_PROPERTIES:
            if prop_name not in ["smiles", "inchi_key"]:  # These are already checked above
                if prop_name == "molecular_weight":
                    if not self.molecular_weight:
                        return False
                elif prop_name == "formula":
                    if not self.formula:
                        return False
                else:
                    # Check if property exists in properties collection
                    if not any(prop.name == prop_name for prop in self.properties):
                        return False
                        
        return True
    
    def to_dict(self, include_properties=True, include_relationships=False):
        """Converts molecule to dictionary representation."""
        result = {
            "id": str(self.id),
            "smiles": self.smiles,
            "inchi_key": self.inchi_key,
            "formula": self.formula,
            "molecular_weight": self.molecular_weight,
            "status": self.status,
            "created_at": self.created_at.isoformat() if self.created_at else None,
            "updated_at": self.updated_at.isoformat() if self.updated_at else None,
            "created_by": str(self.created_by) if self.created_by else None
        }
        
        # Include metadata if available
        if self.metadata:
            result["metadata"] = self.metadata
            
        # Include properties if requested
        if include_properties:
            props = {}
            for prop in self.properties:
                props[prop.name] = {
                    "value": prop.value,
                    "units": prop.units,
                    "source": prop.source
                }
            result["properties"] = props
            
        # Include relationships if requested
        if include_relationships:
            result["libraries"] = [str(lib.id) for lib in self.libraries]
            result["submissions"] = [str(sub.id) for sub in self.submissions]
            
        return result
    
    @classmethod
    def from_dict(cls, data, instance=None):
        """Creates or updates a Molecule instance from dictionary data."""
        if instance is None:
            instance = cls()
            
        # Update basic attributes
        for key in ["smiles", "inchi_key", "formula", "molecular_weight", "status", "metadata", "created_by"]:
            if key in data:
                setattr(instance, key, data[key])
                
        # Update properties if provided
        if "properties" in data and isinstance(data["properties"], dict):
            for name, prop_data in data["properties"].items():
                value = prop_data.get("value")
                units = prop_data.get("units")
                source = prop_data.get("source", PropertySource.IMPORTED.value)
                
                if value is not None:
                    instance.set_property(name, value, source, units)
                    
        # Calculate additional properties if SMILES is provided
        if "smiles" in data and not instance.properties:
            instance.calculate_properties()
            
        return instance
    
    @classmethod
    def from_smiles(cls, smiles, created_by=None):
        """Creates a new Molecule instance from a SMILES string."""
        # Validate SMILES
        if not validate_smiles(smiles):
            raise MoleculeException("Invalid SMILES string")
            
        # Create new instance
        instance = cls(smiles=smiles)
        
        # Generate InChI Key
        instance.inchi_key = get_inchi_key_from_smiles(smiles)
        
        # Set molecular formula
        instance.formula = get_molecular_formula_from_smiles(smiles)
        
        # Calculate basic properties
        instance.calculate_properties()
        
        # Set creator if provided
        if created_by:
            instance.created_by = created_by
            
        return instance