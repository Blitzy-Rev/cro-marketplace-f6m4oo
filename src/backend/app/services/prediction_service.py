"""
Service layer implementation for AI property prediction operations in the Molecular Data Management and CRO Integration Platform. 
This service coordinates prediction requests, manages prediction jobs, processes results, and handles the integration with the external AI prediction engine.
"""

import uuid
from typing import List, Dict, Optional, Any
from sqlalchemy.orm import Session

from ..integrations.ai_engine.client import AIEngineClient  # version: See src/backend/app/integrations/ai_engine/client.py
from ..integrations.ai_engine.models import PredictionRequest, BatchPredictionRequest  # version: See src/backend/app/integrations/ai_engine/models.py
from ..integrations.ai_engine.exceptions import AIEngineException, AIEngineTimeoutError, AIServiceUnavailableError  # version: See src/backend/app/integrations/ai_engine/exceptions.py
from ..crud.crud_prediction import prediction  # version: See src/backend/app/crud/crud_prediction.py
from ..crud.crud_molecule import molecule  # version: See src/backend/app/crud/crud_molecule.py
from ..models.prediction import Prediction, PredictionStatus  # version: See src/backend/app/models/prediction.py
from ..schemas.prediction import PredictionBatchCreate, PredictionBatchUpdate, PredictionFilter  # version: See src/backend/app/schemas/prediction.py
from ..constants.molecule_properties import PREDICTABLE_PROPERTIES, PropertySource  # version: See src/backend/app/constants/molecule_properties.py
from ..core.exceptions import PredictionException  # version: See src/backend/app/core/exceptions.py
from ..db.session import get_db  # version: See src/backend/app/db/session.py
from ..core.logging import get_logger  # version: See src/backend/app/core/logging.py
from ..tasks.celery_app import celery_app  # version: See src/backend/app/tasks/celery_app.py

logger = get_logger(__name__)

DEFAULT_MODEL_NAME = "default"
DEFAULT_MODEL_VERSION = "latest"
MAX_WAIT_TIME = 300
POLL_INTERVAL = 5


class PredictionService:
    """Service class for AI property prediction operations"""

    def __init__(self, ai_client: Optional[AIEngineClient] = None):
        """
        Initialize the prediction service with dependencies.
        
        Args:
            ai_client: Optional AI engine client (for dependency injection)
        """
        self.AIEngineClient = ai_client or AIEngineClient()
        logger.info("Prediction service initialized")

    def predict_properties_for_molecule(
        self,
        molecule_id: uuid.UUID,
        properties: Optional[List[str]] = None,
        model_name: Optional[str] = None,
        model_version: Optional[str] = None,
        wait_for_results: bool = False,
        db: Optional[Session] = None
    ) -> Dict[str, Any]:
        """
        Request property predictions from AI engine for a single molecule
        
        Args:
            molecule_id: ID of the molecule to predict properties for
            properties: List of properties to predict (optional, defaults to all)
            model_name: Name of the AI model to use (optional, defaults to DEFAULT_MODEL_NAME)
            model_version: Version of the AI model to use (optional, defaults to DEFAULT_MODEL_VERSION)
            wait_for_results: Whether to wait for the prediction to complete before returning
            db: Database session (optional)
        
        Returns:
            Prediction results or job information
        """
        db_session = next(get_db()) if db is None else db

        molecule_obj = molecule.get(molecule_id, db=db_session)
        if not molecule_obj:
            raise PredictionException(f"Molecule with id {molecule_id} not found")

        properties = properties or PREDICTABLE_PROPERTIES
        if not all(prop in PREDICTABLE_PROPERTIES for prop in properties):
            raise PredictionException("Invalid property specified")

        model_name = model_name or DEFAULT_MODEL_NAME
        model_version = model_version or DEFAULT_MODEL_VERSION

        request = PredictionRequest(
            smiles=[molecule_obj.smiles],
            properties=properties,
            model_name=model_name,
            model_version=model_version
        )

        try:
            prediction_response = self.AIEngineClient.predict_properties(request)
            batch_id = uuid.uuid4()

            # Create prediction batch record in database
            prediction_batch_create = PredictionBatchCreate(
                molecule_ids=[molecule_id],
                properties=properties,
                model_name=model_name,
                model_version=model_version,
                created_by=None,  # TODO: Get user ID
                external_job_id=prediction_response.job_id
            )
            batch_id = prediction.create_batch(batch_data=prediction_batch_create, db=db_session)["id"]

            if wait_for_results:
                # Wait for prediction completion
                results = self.AIEngineClient.wait_for_prediction_completion(prediction_response.job_id)
                # Process and store prediction results
                process_result = self.process_prediction_results(batch_id, prediction_response.job_id, db=db_session)
                return process_result

            return {"batch_id": batch_id, "job_id": prediction_response.job_id}

        except AIEngineException as e:
            logger.error(f"AI Engine error: {e}")
            raise
        except Exception as e:
            logger.error(f"Unexpected error: {e}")
            raise

    def predict_properties_for_molecules(
        self,
        molecule_ids: List[uuid.UUID],
        properties: Optional[List[str]] = None,
        model_name: Optional[str] = None,
        model_version: Optional[str] = None,
        created_by: Optional[uuid.UUID] = None,
        db: Optional[Session] = None
    ) -> Dict[str, Any]:
        """
        Request property predictions for multiple molecules in batch
        
        Args:
            molecule_ids: List of molecule IDs to predict properties for
            properties: List of properties to predict (optional, defaults to all)
            model_name: Name of the AI model to use (optional, defaults to DEFAULT_MODEL_NAME)
            model_version: Version of the AI model to use (optional, defaults to DEFAULT_MODEL_VERSION)
            created_by: ID of the user creating the prediction batch
            db: Database session (optional)
        
        Returns:
            Batch prediction information
        """
        db_session = next(get_db()) if db is None else db

        molecules = molecule.get_multi(db=db_session)
        if not molecules:
            raise PredictionException("No molecules found")

        properties = properties or PREDICTABLE_PROPERTIES
        if not all(prop in PREDICTABLE_PROPERTIES for prop in properties):
            raise PredictionException("Invalid property specified")

        model_name = model_name or DEFAULT_MODEL_NAME
        model_version = model_version or DEFAULT_MODEL_VERSION

        # Create batch prediction record in database
        prediction_batch_create = PredictionBatchCreate(
            molecule_ids=molecule_ids,
            properties=properties,
            model_name=model_name,
            model_version=model_version,
            created_by=created_by,
        )
        batch_id = prediction.create_batch(batch_data=prediction_batch_create, db=db_session)["id"]

        # Create BatchPredictionRequest with molecule SMILES and properties
        smiles_list = [molecule.smiles for molecule in molecules["items"] if molecule.id in molecule_ids]
        request = BatchPredictionRequest(
            molecule_ids=molecule_ids,
            properties=properties,
            model_name=model_name,
            model_version=model_version
        )

        try:
            # Submit batch prediction request to AI engine
            batch_prediction_response = self.AIEngineClient.submit_batch_prediction(request)

            # Update batch record with external job ID
            prediction_batch_update = PredictionBatchUpdate(
                external_job_id=batch_prediction_response.job_id,
                status=PredictionStatus.PROCESSING
            )
            prediction.update_batch(batch_id=batch_id, batch_data=prediction_batch_update, db=db_session)

            # Schedule asynchronous task to monitor prediction status
            check_prediction_job_task.delay(str(batch_id), batch_prediction_response.job_id)

            return {"batch_id": batch_id, "job_id": batch_prediction_response.job_id}

        except AIEngineException as e:
            logger.error(f"AI Engine error: {e}")
            raise
        except Exception as e:
            logger.error(f"Unexpected error: {e}")
            raise

    def get_prediction_job_status(
        self,
        batch_id: uuid.UUID,
        db: Optional[Session] = None
    ) -> Dict[str, Any]:
        """
        Check the status of a prediction job
        
        Args:
            batch_id: ID of the prediction batch to check
            db: Database session (optional)
        
        Returns:
            Current status of the prediction job
        """
        db_session = next(get_db()) if db is None else db

        batch = prediction.get_batch(batch_id, db=db_session)
        if not batch:
            raise PredictionException(f"Prediction batch with id {batch_id} not found")

        try:
            # Check status with AI engine if external_job_id exists
            if batch["external_job_id"]:
                job_status = self.AIEngineClient.get_prediction_status(batch["external_job_id"])

                # Update batch status based on AI engine response
                prediction_batch_update = PredictionBatchUpdate(
                    status=PredictionStatus(job_status.status),
                    completed_count=job_status.completed_molecules,
                    total_count=job_status.total_molecules
                )
                prediction.update_batch(batch_id=batch_id, batch_data=prediction_batch_update, db=db_session)

                return {
                    "batch_id": batch_id,
                    "status": job_status.status,
                    "completed_count": job_status.completed_molecules,
                    "total_count": job_status.total_molecules
                }
            else:
                return {"batch_id": batch_id, "status": batch["status"]}

        except AIEngineException as e:
            logger.error(f"AI Engine error: {e}")
            raise
        except Exception as e:
            logger.error(f"Unexpected error: {e}")
            raise

    def check_and_update_prediction_job(
        self,
        batch_id: uuid.UUID,
        job_id: str,
        db: Optional[Session] = None
    ) -> Dict[str, Any]:
        """
        Check prediction job status and update database
        
        Args:
            batch_id: ID of the prediction batch
            job_id: ID of the prediction job
            db: Database session (optional)
        
        Returns:
            Updated job status information
        """
        db_session = next(get_db()) if db is None else db

        batch = prediction.get_batch(batch_id, db=db_session)
        if not batch:
            raise PredictionException(f"Prediction batch with id {batch_id} not found")

        try:
            # Get job status from AI engine
            job_status = self.AIEngineClient.get_prediction_status(job_id)

            # Update batch status and completion counts
            prediction_batch_update = PredictionBatchUpdate(
                status=PredictionStatus(job_status.status),
                completed_count=job_status.completed_molecules,
                total_count=job_status.total_molecules
            )
            prediction.update_batch(batch_id=batch_id, batch_data=prediction_batch_update, db=db_session)

            if job_status.status == "completed":
                # Process results
                self.process_prediction_results(batch_id, job_id, db=db_session)
            elif job_status.status == "failed":
                # Handle failure
                self.handle_prediction_failure(batch_id, "AI Engine prediction failed", db=db_session)

            return {
                "batch_id": batch_id,
                "status": job_status.status,
                "completed_count": job_status.completed_molecules,
                "total_count": job_status.total_molecules
            }

        except AIEngineException as e:
            logger.error(f"AI Engine error: {e}")
            raise
        except Exception as e:
            logger.error(f"Unexpected error: {e}")
            raise

    def process_prediction_results(
        self,
        batch_id: uuid.UUID,
        job_id: str,
        db: Optional[Session] = None
    ) -> Dict[str, Any]:
        """
        Process and store prediction results from AI engine
        
        Args:
            batch_id: ID of the prediction batch
            job_id: ID of the prediction job
            db: Database session (optional)
        
        Returns:
            Processing results summary
        """
        db_session = next(get_db()) if db is None else db

        batch = prediction.get_batch(batch_id, db=db_session)
        if not batch:
            raise PredictionException(f"Prediction batch with id {batch_id} not found")

        try:
            # Get prediction results from AI engine
            results = self.AIEngineClient.get_prediction_results(job_id)

            success_count = 0
            failure_count = 0

            # Process each molecule in results
            for molecule_result in results.results:
                molecule_id = next((mol_id for mol_id in batch["molecule_ids"] if str(mol_id) == molecule_result.smiles), None)
                if not molecule_id:
                    logger.warning(f"Molecule ID {molecule_result.smiles} not found in batch {batch_id}")
                    failure_count += 1
                    continue

                # Process each property in molecule results
                for property_name, property_data in molecule_result.properties.items():
                    try:
                        # Create or update prediction record in database
                        prediction.create_prediction(
                            molecule_id=molecule_id,
                            property_name=property_name,
                            value=property_data["value"],
                            confidence=property_data["confidence"],
                            model_name=batch["model_name"],
                            model_version=batch["model_version"],
                            units=property_data.get("units"),
                            db=db_session
                        )
                        success_count += 1
                    except Exception as e:
                        logger.error(f"Failed to store prediction for molecule {molecule_id}, property {property_name}: {str(e)}")
                        failure_count += 1

            # Update batch completion counts
            prediction_batch_update = PredictionBatchUpdate(
                completed_count=success_count,
                failed_count=failure_count
            )
            prediction.update_batch(batch_id=batch_id, batch_data=prediction_batch_update, db=db_session)

            return {
                "batch_id": batch_id,
                "success_count": success_count,
                "failure_count": failure_count
            }

        except AIEngineException as e:
            logger.error(f"AI Engine error: {e}")
            raise
        except Exception as e:
            logger.error(f"Unexpected error: {e}")
            raise

    def handle_prediction_failure(
        self,
        batch_id: uuid.UUID,
        error_message: str,
        db: Optional[Session] = None
    ) -> Dict[str, Any]:
        """
        Handle failed prediction job
        
        Args:
            batch_id: ID of the prediction batch
            error_message: Error message
            db: Database session (optional)
        
        Returns:
            Failure handling result
        """
        db_session = next(get_db()) if db is None else db

        batch = prediction.get_batch(batch_id, db=db_session)
        if not batch:
            raise PredictionException(f"Prediction batch with id {batch_id} not found")

        try:
            # Update batch status to FAILED with error message
            prediction_batch_update = PredictionBatchUpdate(
                status=PredictionStatus.FAILED,
                error_message=error_message
            )
            prediction.update_batch(batch_id=batch_id, batch_data=prediction_batch_update, db=db_session)

            # Update all pending predictions in batch to FAILED
            # TODO: Implement this logic

            return {"batch_id": batch_id, "status": PredictionStatus.FAILED, "error_message": error_message}

        except Exception as e:
            logger.error(f"Unexpected error: {e}")
            raise

    def get_molecule_predictions(
        self,
        molecule_id: uuid.UUID,
        confidence_threshold: Optional[float] = None,
        db: Optional[Session] = None
    ) -> List[Dict[str, Any]]:
        """
        Get all predictions for a specific molecule
        
        Args:
            molecule_id: ID of the molecule
            confidence_threshold: Minimum confidence threshold (optional)
            db: Database session (optional)
        
        Returns:
            List of predictions for the molecule
        """
        db_session = next(get_db()) if db is None else db

        molecule_obj = molecule.get(molecule_id, db=db_session)
        if not molecule_obj:
            raise PredictionException(f"Molecule with id {molecule_id} not found")

        # Get predictions for molecule
        predictions = prediction.get_by_molecule_id(molecule_id, db=db_session, min_confidence=confidence_threshold)

        # Convert predictions to dictionary format
        prediction_list = [p.to_dict() for p in predictions]

        return prediction_list

    def get_latest_predictions(
        self,
        molecule_id: uuid.UUID,
        properties: Optional[List[str]] = None,
        db: Optional[Session] = None
    ) -> Dict[str, Dict[str, Any]]:
        """
        Get the latest predictions for each property of a molecule
        
        Args:
            molecule_id: ID of the molecule
            properties: List of properties to retrieve (optional, defaults to all)
            db: Database session (optional)
        
        Returns:
            Dictionary of latest predictions by property
        """
        db_session = next(get_db()) if db is None else db

        molecule_obj = molecule.get(molecule_id, db=db_session)
        if not molecule_obj:
            raise PredictionException(f"Molecule with id {molecule_id} not found")

        properties = properties or PREDICTABLE_PROPERTIES
        result = {}

        for prop in properties:
            latest_prediction = prediction.get_latest_prediction(molecule_id, prop, db=db_session)
            if latest_prediction:
                result[prop] = latest_prediction.to_dict()

        return result

    def filter_predictions(
        self,
        filter_params: PredictionFilter,
        skip: int,
        limit: int,
        db: Optional[Session] = None
    ) -> Dict[str, Any]:
        """
        Filter predictions based on various criteria
        
        Args:
            filter_params: Filter parameters
            skip: Number of records to skip
            limit: Maximum number of records to return
            db: Database session (optional)
        
        Returns:
            Filtered predictions with pagination info
        """
        db_session = next(get_db()) if db is None else db
        return prediction.filter_predictions(filter_params, skip, limit, db=db_session)

    def cancel_prediction_job(
        self,
        batch_id: uuid.UUID,
        db: Optional[Session] = None
    ) -> Dict[str, Any]:
        """
        Cancel an ongoing prediction job
        
        Args:
            batch_id: ID of the prediction batch
            db: Database session (optional)
        
        Returns:
            Cancellation result
        """
        db_session = next(get_db()) if db is None else db

        batch = prediction.get_batch(batch_id, db=db_session)
        if not batch:
            raise PredictionException(f"Prediction batch with id {batch_id} not found")

        if batch["status"] not in [PredictionStatus.PENDING, PredictionStatus.PROCESSING]:
            return {"batch_id": batch_id, "status": "error", "message": "Job is not pending or processing"}

        try:
            # Try to cancel job with AI engine if external_job_id exists
            if batch["external_job_id"]:
                # TODO: Implement cancellation with AI engine
                pass

            # Update batch status to FAILED with cancellation message
            prediction_batch_update = PredictionBatchUpdate(
                status=PredictionStatus.FAILED,
                error_message="Job cancelled by user"
            )
            prediction.update_batch(batch_id=batch_id, batch_data=prediction_batch_update, db=db_session)

            return {"batch_id": batch_id, "status": "cancelled"}

        except Exception as e:
            logger.error(f"Unexpected error: {e}")
            raise

    def retry_failed_prediction(
        self,
        batch_id: uuid.UUID,
        db: Optional[Session] = None
    ) -> Dict[str, Any]:
        """
        Retry a failed prediction job
        
        Args:
            batch_id: ID of the prediction batch
            db: Database session (optional)
        
        Returns:
            Retry result
        """
        db_session = next(get_db()) if db is None else db

        batch = prediction.get_batch(batch_id, db=db_session)
        if not batch:
            raise PredictionException(f"Prediction batch with id {batch_id} not found")

        if batch["status"] != PredictionStatus.FAILED:
            return {"batch_id": batch_id, "status": "error", "message": "Job is not in failed state"}

        try:
            # Reset batch status to PENDING
            prediction_batch_update = PredictionBatchUpdate(
                status=PredictionStatus.PENDING,
                error_message=None
            )
            prediction.update_batch(batch_id=batch_id, batch_data=prediction_batch_update, db=db_session)

            # Schedule task to resubmit prediction batch
            # TODO: Implement task scheduling
            # check_prediction_job_task.delay(str(batch_id), batch["external_job_id"])

            return {"batch_id": batch_id, "status": "retrying"}

        except Exception as e:
            logger.error(f"Unexpected error: {e}")
            raise


# Create a singleton instance
prediction_service = PredictionService()


@celery_app.task(name="tasks.ai_predictions.check_prediction_job")
def check_prediction_job_task(batch_id: str, job_id: str):
    """Celery task to check prediction job status and update database"""
    logger.info(f"Checking prediction job status: batch_id={batch_id}, job_id={job_id}")
    try:
        db_session = next(get_db())
        prediction_service.check_and_update_prediction_job(uuid.UUID(batch_id), job_id, db=db_session)
    except Exception as e:
        logger.error(f"Error checking prediction job status: {e}")
        raise