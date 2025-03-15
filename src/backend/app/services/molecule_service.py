# src/backend/app/services/molecule_service.py
"""
Service layer implementation for molecule-related operations in the Molecular Data Management and CRO Integration Platform.
This service provides high-level business logic for molecule management, including CSV processing, property prediction, library organization, and data validation.
"""

import typing
from typing import List, Dict, Optional, Any, Union
import uuid

from sqlalchemy.orm import Session

from ..models.molecule import Molecule, MoleculeStatus
from ..models.library import Library
from ..crud import crud_molecule
from ..utils.csv_parser import CSVProcessor, process_csv_in_chunks
from ..utils.smiles import validate_smiles
from ..integrations.ai_engine.client import AIEngineClient
from ..integrations.ai_engine.models import PredictionRequest, BatchPredictionRequest
from ..constants.molecule_properties import PropertySource, PREDICTABLE_PROPERTIES
from ..schemas import molecule
from ..schemas.molecule import MoleculeCreate, MoleculeCSVMapping
from ..db.session import get_db
from ..core.exceptions import MoleculeException, CSVException, AIEngineException
from ..core.logging import get_logger

# Initialize logger
logger = get_logger(__name__)

class MoleculeService:
    """Service class for molecule-related operations with business logic"""

    def __init__(self, ai_client: Optional[AIEngineClient] = None):
        """Initialize the molecule service with dependencies

        Args:
            ai_client: Optional AI engine client for property predictions
        """
        self._ai_client = ai_client or AIEngineClient()
        logger.info("MoleculeService initialized")

    def create_molecule(self, smiles: str, created_by: Optional[uuid.UUID] = None, properties: Optional[Dict[str, Any]] = None, db: Optional[Session] = None) -> Dict[str, Any]:
        """Create a new molecule from SMILES string

        Args:
            smiles: SMILES string representation of the molecule
            created_by: Optional user ID who created the molecule
            properties: Optional dictionary of properties to set on the molecule
            db: Optional database session

        Returns:
            Created molecule data as dictionary
        """
        db_session = db or get_db()
        try:
            # Validate SMILES string using validate_smiles
            if not validate_smiles(smiles):
                raise MoleculeException(message="Invalid SMILES string")

            # Check if molecule already exists by SMILES
            existing_molecule = crud_molecule.molecule.get_by_smiles(smiles, db=db_session)
            if existing_molecule:
                logger.debug(f"Molecule with SMILES {smiles} already exists")
                return existing_molecule.to_dict()

            # Create new molecule using molecule.create_from_smiles
            molecule = Molecule.from_smiles(smiles, created_by)
            db_session.add(molecule)
            db_session.commit()
            db_session.refresh(molecule)

            # If properties provided, set each property on molecule
            if properties:
                for name, value in properties.items():
                    molecule.set_property(name, value, PropertySource.IMPORTED.value)

            # Return molecule data as dictionary
            return molecule.to_dict()
        except Exception as e:
            db_session.rollback()
            logger.error(f"Error creating molecule: {e}")
            raise

    def get_molecule(self, molecule_id: uuid.UUID, db: Optional[Session] = None) -> Optional[Dict[str, Any]]:
        """Get a molecule by ID

        Args:
            molecule_id: ID of the molecule to retrieve
            db: Optional database session

        Returns:
            Molecule data as dictionary if found, None otherwise
        """
        db_session = db or get_db()
        try:
            # Get molecule by ID with properties
            molecule = crud_molecule.molecule.get_with_properties(molecule_id, db=db_session)

            # If not found, return None
            if not molecule:
                return None

            # Return molecule data as dictionary
            return molecule.to_dict()
        except Exception as e:
            logger.error(f"Error getting molecule: {e}")
            raise

    def get_molecule_by_smiles(self, smiles: str, db: Optional[Session] = None) -> Optional[Dict[str, Any]]:
        """Get a molecule by SMILES string

        Args:
            smiles: SMILES string to search for
            db: Optional database session

        Returns:
            Molecule data as dictionary if found, None otherwise
        """
        db_session = db or get_db()
        try:
            # Get molecule by SMILES
            molecule = crud_molecule.molecule.get_by_smiles(smiles, db=db_session)

            # If not found, return None
            if not molecule:
                return None

            # Return molecule data as dictionary
            return molecule.to_dict()
        except Exception as e:
            logger.error(f"Error getting molecule by SMILES: {e}")
            raise

    def filter_molecules(self, filter_params: Dict[str, Any], skip: int, limit: int, sort_by: Optional[str] = None, descending: bool = False, db: Optional[Session] = None) -> Dict[str, Any]:
        """Filter molecules based on various criteria

        Args:
            filter_params: Dictionary of filter parameters
            skip: Number of records to skip for pagination
            limit: Maximum number of records to return for pagination
            sort_by: Optional field to sort the results by
            descending: Optional boolean to sort in descending order
            db: Optional database session

        Returns:
            Filtered molecules with pagination info
        """
        db_session = db or get_db()
        try:
            # Call molecule.filter_molecules with parameters
            filtered_molecules = crud_molecule.molecule.filter_molecules(filter_params, db=db_session, skip=skip, limit=limit, sort_by=sort_by, descending=descending)

            # Return filtered molecules with pagination info
            return filtered_molecules
        except Exception as e:
            logger.error(f"Error filtering molecules: {e}")
            raise

    def process_csv_file(self, file_path: str, column_mapping: Dict[str, str], created_by: Optional[uuid.UUID] = None, db: Optional[Session] = None) -> Dict[str, Any]:
        """Process a CSV file containing molecular data

        Args:
            file_path: Path to the CSV file
            column_mapping: Dictionary mapping CSV columns to system properties
            created_by: Optional user ID who created the molecules
            db: Optional database session

        Returns:
            Processing results with statistics
        """
        db_session = db or get_db()
        try:
            # Create CSVProcessor instance with file_path
            csv_processor = CSVProcessor(file_path)

            # Load CSV file and validate format
            csv_processor.load_csv()

            # Set column mapping for CSV processing
            csv_processor.set_column_mapping(column_mapping)

            # Process CSV data with validation
            csv_processor.process()

            # Get valid molecules from processor
            valid_molecules_df = csv_processor.get_valid_molecules()

            # Convert DataFrame to list of MoleculeCreate objects
            molecule_creates = []
            for _, row in valid_molecules_df.iterrows():
                molecule_data = row.to_dict()
                molecule_creates.append(MoleculeCreate(**molecule_data, created_by=created_by))

            # Create molecule objects in database using batch_create
            creation_results = crud_molecule.molecule.batch_create(molecule_creates, db=db_session)

            # Return processing results with statistics
            summary = csv_processor.get_summary()
            summary.update(creation_results)
            return summary
        except Exception as e:
            db_session.rollback()
            logger.error(f"Error processing CSV file: {e}")
            raise

    def get_csv_preview(self, file_path: str, num_rows: int) -> Dict[str, Any]:
        """Get a preview of CSV data for column mapping

        Args:
            file_path: Path to the CSV file
            num_rows: Number of rows to preview

        Returns:
            Preview data with headers and sample rows
        """
        try:
            # Create CSVProcessor instance with file_path
            csv_processor = CSVProcessor(file_path)

            # Load CSV file and validate format
            csv_processor.load_csv()

            # Get preview data with specified number of rows
            preview_data = csv_processor.get_preview(num_rows)

            # Generate column mapping suggestions
            suggestions = csv_processor.get_mapping_suggestions()
            preview_data['suggestions'] = suggestions

            # Return preview data with mapping suggestions
            return preview_data
        except Exception as e:
            logger.error(f"Error getting CSV preview: {e}")
            raise

    def add_to_library(self, molecule_id: uuid.UUID, library_id: uuid.UUID, added_by: uuid.UUID, db: Optional[Session] = None) -> bool:
        """Add a molecule to a library

        Args:
            molecule_id: ID of the molecule to add
            library_id: ID of the library to add the molecule to
            added_by: User ID who is adding the molecule
            db: Optional database session

        Returns:
            True if added, False if already in library
        """
        db_session = db or get_db()
        try:
            # Call molecule.add_to_library with parameters
            result = crud_molecule.molecule.add_to_library(molecule_id, library_id, added_by, db=db_session)

            # Return result of operation
            return result
        except Exception as e:
            db_session.rollback()
            logger.error(f"Error adding molecule to library: {e}")
            raise

    def remove_from_library(self, molecule_id: uuid.UUID, library_id: uuid.UUID, db: Optional[Session] = None) -> bool:
        """Remove a molecule from a library

        Args:
            molecule_id: ID of the molecule to remove
            library_id: ID of the library to remove the molecule from
            db: Optional database session

        Returns:
            True if removed, False if not in library
        """
        db_session = db or get_db()
        try:
            # Call molecule.remove_from_library with parameters
            result = crud_molecule.molecule.remove_from_library(molecule_id, library_id, db=db_session)

            # Return result of operation
            return result
        except Exception as e:
            db_session.rollback()
            logger.error(f"Error removing molecule from library: {e}")
            raise

    def predict_properties(self, molecule_id: uuid.UUID, properties: Optional[List[str]] = None, wait_for_results: bool = True, db: Optional[Session] = None) -> Dict[str, Any]:
        """Request property predictions from AI engine for a molecule

        Args:
            molecule_id: ID of the molecule to predict properties for
            properties: Optional list of properties to predict (defaults to PREDICTABLE_PROPERTIES)
            wait_for_results: Whether to wait for the prediction to complete
            db: Optional database session

        Returns:
            Prediction results or job information
        """
        db_session = db or get_db()
        try:
            # Get molecule by ID
            molecule = crud_molecule.molecule.get(molecule_id, db=db_session)
            if not molecule:
                raise MoleculeException(message="Molecule not found")

            # If properties not specified, use PREDICTABLE_PROPERTIES
            if not properties:
                properties = PREDICTABLE_PROPERTIES

            # Create PredictionRequest with molecule SMILES and properties
            prediction_request = PredictionRequest(smiles=[molecule.smiles], properties=properties)

            # Submit prediction request to AI engine
            prediction_response = self._ai_client.predict_properties(prediction_request)

            # If wait_for_results is True, wait for prediction completion
            if wait_for_results:
                prediction_response = self._ai_client.wait_for_prediction_completion(prediction_response.job_id)

                # Store predicted properties on molecule
                if prediction_response.results:
                    self.store_prediction_results(molecule_id, prediction_response.results[0].properties, db=db_session)

            # Return prediction results or job information
            return prediction_response.dict()
        except Exception as e:
            db_session.rollback()
            logger.error(f"Error predicting properties: {e}")
            raise

    def batch_predict_properties(self, molecule_ids: List[uuid.UUID], properties: Optional[List[str]] = None, db: Optional[Session] = None) -> Dict[str, Any]:
        """Request property predictions for multiple molecules

        Args:
            molecule_ids: List of molecule IDs to predict properties for
            properties: Optional list of properties to predict (defaults to PREDICTABLE_PROPERTIES)
            db: Optional database session

        Returns:
            Batch prediction job information
        """
        db_session = db or get_db()
        try:
            # Get molecules by IDs
            molecules = [crud_molecule.molecule.get(molecule_id, db=db_session) for molecule_id in molecule_ids]
            if not all(molecules):
                raise MoleculeException(message="One or more molecules not found")

            # If properties not specified, use PREDICTABLE_PROPERTIES
            if not properties:
                properties = PREDICTABLE_PROPERTIES

            # Create BatchPredictionRequest with molecule IDs and properties
            batch_prediction_request = BatchPredictionRequest(molecule_ids=molecule_ids, properties=properties)

            # Submit batch prediction request to AI engine
            batch_prediction_response = self._ai_client.submit_batch_prediction(batch_prediction_request)

            # Return batch prediction job information
            return batch_prediction_response.dict()
        except Exception as e:
            db_session.rollback()
            logger.error(f"Error submitting batch prediction: {e}")
            raise

    def store_prediction_results(self, molecule_id: uuid.UUID, prediction_results: Dict[str, Any], db: Optional[Session] = None) -> bool:
        """Store property prediction results for a molecule

        Args:
            molecule_id: ID of the molecule to store results for
            prediction_results: Dictionary of predicted properties and values
            db: Optional database session

        Returns:
            True if results stored successfully
        """
        db_session = db or get_db()
        try:
            # Get molecule by ID
            molecule = crud_molecule.molecule.get(molecule_id, db=db_session)
            if not molecule:
                raise MoleculeException(message="Molecule not found")

            # For each property in prediction_results
            for property_name, property_data in prediction_results.items():
                # Set property on molecule with PropertySource.PREDICTED
                value = property_data.get("value")
                confidence = property_data.get("confidence")

                molecule.set_property(property_name, value, PropertySource.PREDICTED.value)

                # Store confidence score in property metadata if available
                if confidence is not None:
                    molecule.metadata = molecule.metadata or {}
                    molecule.metadata[f"{property_name}_confidence"] = confidence

            # Commit changes to database
            db_session.add(molecule)
            db_session.commit()

            logger.info(f"Stored prediction results for molecule {molecule_id}")
            return True
        except Exception as e:
            db_session.rollback()
            logger.error(f"Error storing prediction results: {e}")
            raise

    def bulk_operation(self, molecule_ids: List[uuid.UUID], operation: str, parameters: Dict[str, Any], db: Optional[Session] = None) -> Dict[str, Any]:
        """Perform bulk operations on multiple molecules

        Args:
            molecule_ids: List of molecule IDs to operate on
            operation: Operation to perform (add_to_library, remove_from_library, predict_properties, update_status)
            parameters: Operation-specific parameters
            db: Optional database session

        Returns:
            Operation results with statistics
        """
        db_session = db or get_db()
        try:
            # Validate operation is supported
            supported_operations = ["add_to_library", "remove_from_library", "predict_properties", "update_status"]
            if operation not in supported_operations:
                raise ValueError(f"Unsupported operation: {operation}")

            if operation == "add_to_library":
                # Add molecules to library
                library_id = parameters.get("library_id")
                added_by = parameters.get("added_by")
                if not library_id or not added_by:
                    raise ValueError("library_id and added_by are required for add_to_library operation")
                
                for molecule_id in molecule_ids:
                    self.add_to_library(molecule_id, library_id, added_by, db=db_session)

            elif operation == "remove_from_library":
                # Remove molecules from library
                library_id = parameters.get("library_id")
                if not library_id:
                    raise ValueError("library_id is required for remove_from_library operation")
                
                for molecule_id in molecule_ids:
                    self.remove_from_library(molecule_id, library_id, db=db_session)

            elif operation == "predict_properties":
                # Request predictions for molecules
                properties = parameters.get("properties")
                self.batch_predict_properties(molecule_ids, properties, db=db_session)

            elif operation == "update_status":
                # Update status for molecules
                status = parameters.get("status")
                if not status:
                    raise ValueError("status is required for update_status operation")
                
                for molecule_id in molecule_ids:
                    molecule = crud_molecule.molecule.get(molecule_id, db=db_session)
                    if molecule:
                        molecule.status = status
                        db_session.add(molecule)
                        db_session.commit()

            # Return operation results with statistics
            return {"success": True, "message": f"Bulk operation '{operation}' completed"}
        except Exception as e:
            db_session.rollback()
            logger.error(f"Error performing bulk operation: {e}")
            raise

# Create a singleton instance
molecule_service = MoleculeService()