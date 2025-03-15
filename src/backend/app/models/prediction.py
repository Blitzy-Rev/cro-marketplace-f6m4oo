from sqlalchemy import Column, String, Float, ForeignKey, UUID, JSON
from sqlalchemy.orm import relationship, validates
from datetime import datetime
from enum import Enum

from ..db.base_class import Base
from ..constants.molecule_properties import PropertySource, PREDICTABLE_PROPERTIES, PROPERTY_UNITS


class PredictionStatus(Enum):
    """Enumeration of possible prediction statuses."""
    PENDING = "pending"
    PROCESSING = "processing"
    COMPLETED = "completed"
    FAILED = "failed"


class Prediction(Base):
    """
    SQLAlchemy model representing an AI-generated property prediction for a molecule.
    
    This model stores prediction values, confidence scores, and metadata about the
    prediction process including the AI model used and when the prediction was made.
    Predictions are linked to molecules via molecule_id.
    """
    
    # Foreign key relationship
    molecule_id = Column(UUID, ForeignKey("molecule.id"), nullable=False, index=True)
    
    # Prediction data
    property_name = Column(String(100), nullable=False, index=True)
    value = Column(Float, nullable=False)
    units = Column(String(50), nullable=True)
    confidence = Column(Float, nullable=False)
    
    # Prediction metadata
    model_name = Column(String(100), nullable=False)
    model_version = Column(String(50), nullable=False)
    metadata = Column(JSON, nullable=True, default={})
    
    # Relationships
    molecule = relationship("Molecule", back_populates="predictions")
    
    @validates('property_name')
    def validate_property_name(self, key, property_name):
        """
        Validates that the property name is in the list of predictable properties.
        
        Args:
            key: The attribute name being validated (automatically provided by SQLAlchemy)
            property_name: The property name to validate
            
        Returns:
            str: Validated property name
            
        Raises:
            ValueError: If property_name is not in the list of predictable properties
        """
        if property_name not in PREDICTABLE_PROPERTIES:
            raise ValueError(f"Property '{property_name}' is not in the list of predictable properties")
        return property_name
    
    @validates('confidence')
    def validate_confidence(self, key, confidence):
        """
        Validates that the confidence value is between 0 and 1.
        
        Args:
            key: The attribute name being validated (automatically provided by SQLAlchemy)
            confidence: The confidence value to validate
            
        Returns:
            float: Validated confidence value
            
        Raises:
            ValueError: If confidence is not between 0 and 1
        """
        if not 0 <= confidence <= 1:
            raise ValueError("Confidence must be between 0 and 1")
        return confidence
    
    def set_units_from_property(self):
        """
        Sets the appropriate units based on the property name if not provided.
        
        This method looks up the standard units for the property in the PROPERTY_UNITS
        dictionary and sets the units attribute if it's not already set.
        """
        if not self.units and self.property_name and self.property_name in PROPERTY_UNITS:
            self.units = PROPERTY_UNITS[self.property_name]
    
    def to_dict(self):
        """
        Converts prediction to dictionary representation.
        
        Returns:
            dict: Dictionary containing prediction attributes
        """
        return {
            'id': str(self.id) if self.id else None,
            'molecule_id': str(self.molecule_id) if self.molecule_id else None,
            'property_name': self.property_name,
            'value': self.value,
            'units': self.units,
            'confidence': self.confidence,
            'model_name': self.model_name,
            'model_version': self.model_version,
            'metadata': self.metadata,
            'created_at': self.created_at.isoformat() if self.created_at else None,
            'updated_at': self.updated_at.isoformat() if self.updated_at else None
        }
    
    @classmethod
    def from_dict(cls, data, instance=None):
        """
        Creates or updates a Prediction instance from dictionary data.
        
        Args:
            data: Dictionary containing model attributes
            instance: Optional existing instance to update (if None, creates new instance)
            
        Returns:
            Prediction: Prediction instance with data applied
        """
        if instance is None:
            instance = cls()
        
        for key, value in data.items():
            if hasattr(instance, key):
                setattr(instance, key, value)
        
        # Set units from property name if not provided
        instance.set_units_from_property()
        
        return instance
    
    @classmethod
    def from_ai_prediction(cls, molecule_id, property_name, value, confidence, 
                           model_name, model_version, units=None, metadata=None):
        """
        Creates a new Prediction instance from AI prediction result.
        
        Args:
            molecule_id: UUID of the molecule
            property_name: Name of the predicted property
            value: Predicted value
            confidence: Prediction confidence score (0-1)
            model_name: Name of the AI model used
            model_version: Version of the AI model
            units: Optional units for the prediction
            metadata: Optional additional metadata about the prediction
            
        Returns:
            Prediction: New Prediction instance
        """
        prediction = cls(
            molecule_id=molecule_id,
            property_name=property_name,
            value=value,
            confidence=confidence,
            model_name=model_name,
            model_version=model_version,
            units=units,
            metadata=metadata or {}
        )
        
        # Set units from property name if not provided
        if not units:
            prediction.set_units_from_property()
            
        return prediction