from pydantic import BaseModel, Field, validator, root_validator, UUID4
from typing import List, Dict, Optional, Any, Union

from ../../constants.molecule_properties import PREDICTABLE_PROPERTIES

# Constants
MAX_BATCH_SIZE = 100
DEFAULT_MODEL_NAME = "molecule_property_predictor"
DEFAULT_MODEL_VERSION = "v1.0"

def validate_properties(properties: List[str]) -> List[str]:
    """
    Validates that all properties are in the list of predictable properties
    
    Args:
        properties: List of property names to validate
        
    Returns:
        Validated list of properties
        
    Raises:
        ValueError: If properties list is empty or contains invalid properties
    """
    if not properties:
        raise ValueError("Properties list cannot be empty")
    
    invalid_properties = [prop for prop in properties if prop not in PREDICTABLE_PROPERTIES]
    if invalid_properties:
        raise ValueError(f"Invalid properties found: {', '.join(invalid_properties)}. "
                         f"Valid properties are: {', '.join(PREDICTABLE_PROPERTIES)}")
    
    return properties

class PropertyPrediction(BaseModel):
    """Model for individual property prediction"""
    value: Union[float, int, str, bool]
    confidence: float
    units: Optional[str] = None
    metadata: Optional[Dict[str, Any]] = None
    
    @validator('confidence')
    def validate_confidence(cls, v: float) -> float:
        """Validates that confidence is between 0 and 1"""
        if not 0 <= v <= 1:
            raise ValueError("Confidence must be between 0 and 1")
        return v

class MoleculePrediction(BaseModel):
    """Model for individual molecule prediction result"""
    smiles: str
    properties: Dict[str, Dict[str, Any]]  # Dict of property_name -> property prediction data
    error: Optional[str] = None

class PredictionRequest(BaseModel):
    """Model for prediction request to AI engine"""
    smiles: List[str]
    properties: List[str]
    model_name: Optional[str] = None
    model_version: Optional[str] = None
    options: Optional[Dict[str, Any]] = None
    
    @validator('smiles')
    def validate_smiles(cls, v: List[str]) -> List[str]:
        """Validates that SMILES list is not empty"""
        if not v:
            raise ValueError("SMILES list cannot be empty")
        return v
    
    @validator('properties')
    def validate_properties(cls, v: List[str]) -> List[str]:
        """Validates that properties list is not empty and contains valid properties"""
        return validate_properties(v)
    
    @root_validator(pre=True)
    def set_default_model(cls, values: dict) -> dict:
        """Sets default model name and version if not provided"""
        if 'model_name' not in values or not values['model_name']:
            values['model_name'] = DEFAULT_MODEL_NAME
        if 'model_version' not in values or not values['model_version']:
            values['model_version'] = DEFAULT_MODEL_VERSION
        return values

class PredictionResponse(BaseModel):
    """Model for prediction response from AI engine"""
    job_id: str
    status: str  # e.g., "queued", "processing", "completed", "failed"
    results: Optional[List[MoleculePrediction]] = None
    model_name: Optional[str] = None
    model_version: Optional[str] = None
    metadata: Optional[Dict[str, Any]] = None

class PredictionJobRequest(BaseModel):
    """Model for checking prediction job status"""
    job_id: str

class PredictionJobStatus(BaseModel):
    """Model for prediction job status response"""
    job_id: str
    status: str  # e.g., "queued", "processing", "completed", "failed"
    total_molecules: int
    completed_molecules: int
    model_name: Optional[str] = None
    model_version: Optional[str] = None
    metadata: Optional[Dict[str, Any]] = None

class BatchPredictionRequest(BaseModel):
    """Model for batch prediction request with molecule IDs"""
    molecule_ids: List[UUID4]
    properties: List[str]
    model_name: Optional[str] = None
    model_version: Optional[str] = None
    options: Optional[Dict[str, Any]] = None
    
    @validator('molecule_ids')
    def validate_molecule_ids(cls, v: List[UUID4]) -> List[UUID4]:
        """Validates that molecule_ids list is not empty"""
        if not v:
            raise ValueError("Molecule IDs list cannot be empty")
        if len(v) > MAX_BATCH_SIZE:
            raise ValueError(f"Batch size exceeds maximum limit of {MAX_BATCH_SIZE}")
        return v
    
    @validator('properties')
    def validate_properties(cls, v: List[str]) -> List[str]:
        """Validates that properties list is not empty and contains valid properties"""
        return validate_properties(v)
    
    @root_validator(pre=True)
    def set_default_model(cls, values: dict) -> dict:
        """Sets default model name and version if not provided"""
        if 'model_name' not in values or not values['model_name']:
            values['model_name'] = DEFAULT_MODEL_NAME
        if 'model_version' not in values or not values['model_version']:
            values['model_version'] = DEFAULT_MODEL_VERSION
        return values

class BatchPredictionResponse(BaseModel):
    """Model for batch prediction response"""
    batch_id: str
    status: str  # e.g., "queued", "processing", "completed", "failed"
    job_id: Optional[str] = None
    model_name: Optional[str] = None
    model_version: Optional[str] = None
    metadata: Optional[Dict[str, Any]] = None

class AIModelInfo(BaseModel):
    """Model for AI engine model information"""
    name: str
    version: str
    supported_properties: List[str]
    description: Optional[str] = None
    metadata: Optional[Dict[str, Any]] = None
    
    @validator('supported_properties')
    def validate_supported_properties(cls, v: List[str]) -> List[str]:
        """Validates that supported properties are valid predictable properties"""
        if not v:
            raise ValueError("Supported properties list cannot be empty")
        
        invalid_properties = [prop for prop in v if prop not in PREDICTABLE_PROPERTIES]
        if invalid_properties:
            raise ValueError(f"Invalid properties found: {', '.join(invalid_properties)}. "
                             f"Valid properties are: {', '.join(PREDICTABLE_PROPERTIES)}")
        
        return v