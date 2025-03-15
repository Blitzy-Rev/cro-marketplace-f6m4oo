"""
FastAPI router implementation for AI prediction endpoints in the Molecular Data Management and CRO Integration Platform.
This file defines API routes for submitting prediction requests, checking prediction status, retrieving prediction results,
and managing prediction batches.
"""
import typing
from typing import List, Dict, Optional, Any
import uuid

from sqlalchemy.orm import Session  # sqlalchemy version: ^1.4.0
from fastapi import APIRouter, Depends, HTTPException, status  # fastapi version: ^0.95.0

from ...api.deps import get_db, get_current_active_user, get_current_pharma_user  # Internal imports
from ...services.prediction_service import prediction_service  # Internal imports
from ...integrations.ai_engine.exceptions import AIEngineException, AIServiceUnavailableError  # Internal imports
from ...core.exceptions import PredictionException  # Internal imports
from ...schemas.prediction import PredictionBatchCreate, PredictionFilter, PredictionResponse, PredictionJobStatus  # Internal imports
from ...models.user import User  # Internal imports
from ...constants.molecule_properties import PREDICTABLE_PROPERTIES  # Internal imports
from ...core.logging import get_logger  # Internal imports

router = APIRouter()
logger = get_logger(__name__)


@router.post("/molecules/{molecule_id}/predict", response_model=Dict[str, Any], status_code=status.HTTP_202_ACCEPTED)
def predict_molecule_properties(
    molecule_id: uuid.UUID,
    properties: Optional[List[str]] = None,
    model_name: Optional[str] = None,
    model_version: Optional[str] = None,
    wait_for_results: bool = False,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_active_user),
) -> Dict[str, Any]:
    """
    Endpoint to request property predictions for a single molecule
    """
    logger.info(f"Prediction request received for molecule_id: {molecule_id}, properties: {properties}")
    try:
        # Call prediction_service.predict_properties_for_molecule
        prediction_result = prediction_service.predict_properties_for_molecule(
            molecule_id=molecule_id,
            properties=properties,
            model_name=model_name,
            model_version=model_version,
            wait_for_results=wait_for_results,
            db=db
        )
        return prediction_result
    except AIServiceUnavailableError as e:
        # Handle AIServiceUnavailableError with 503 Service Unavailable response
        logger.error(f"AI Service Unavailable: {e}")
        raise HTTPException(status_code=status.HTTP_503_SERVICE_UNAVAILABLE, detail=str(e))
    except PredictionException as e:
        # Handle PredictionException with 400 Bad Request response
        logger.error(f"Prediction Exception: {e}")
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(e))
    except AIEngineException as e:
        # Handle AIEngineException with 500 Internal Server Error response
        logger.error(f"AI Engine Exception: {e}")
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail=str(e))


@router.post("/molecules/predict/batch", response_model=Dict[str, Any], status_code=status.HTTP_202_ACCEPTED)
def predict_molecules_batch(
    batch_request: PredictionBatchCreate,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_active_user),
) -> Dict[str, Any]:
    """
    Endpoint to request property predictions for multiple molecules in batch
    """
    logger.info(f"Batch prediction request received for {len(batch_request.molecule_ids)} molecules, properties: {batch_request.properties}")
    try:
        # Call prediction_service.predict_properties_for_molecules with current_user.id as created_by
        batch_prediction_info = prediction_service.predict_properties_for_molecules(
            molecule_ids=batch_request.molecule_ids,
            properties=batch_request.properties,
            model_name=batch_request.model_name,
            model_version=batch_request.model_version,
            created_by=current_user.id,
            db=db
        )
        return batch_prediction_info
    except AIServiceUnavailableError as e:
        # Handle AIServiceUnavailableError with 503 Service Unavailable response
        logger.error(f"AI Service Unavailable: {e}")
        raise HTTPException(status_code=status.HTTP_503_SERVICE_UNAVAILABLE, detail=str(e))
    except PredictionException as e:
        # Handle PredictionException with 400 Bad Request response
        logger.error(f"Prediction Exception: {e}")
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(e))
    except AIEngineException as e:
        # Handle AIEngineException with 500 Internal Server Error response
        logger.error(f"AI Engine Exception: {e}")
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail=str(e))


@router.get("/predictions/{batch_id}/status", response_model=PredictionJobStatus)
def get_prediction_job_status(
    batch_id: uuid.UUID,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_active_user),
) -> PredictionJobStatus:
    """
    Endpoint to check the status of a prediction job
    """
    logger.info(f"Status check request received for batch_id: {batch_id}")
    try:
        # Call prediction_service.get_prediction_job_status
        job_status = prediction_service.get_prediction_job_status(
            batch_id=batch_id,
            db=db
        )
        return job_status
    except PredictionException as e:
        # Handle PredictionException with 404 Not Found response
        logger.error(f"Prediction Exception: {e}")
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=str(e))
    except AIEngineException as e:
        # Handle AIEngineException with 500 Internal Server Error response
        logger.error(f"AI Engine Exception: {e}")
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail=str(e))


@router.get("/molecules/{molecule_id}/predictions", response_model=List[PredictionResponse])
def get_molecule_predictions(
    molecule_id: uuid.UUID,
    min_confidence: Optional[float] = None,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_active_user),
) -> List[PredictionResponse]:
    """
    Endpoint to get all predictions for a specific molecule
    """
    logger.info(f"Request received for molecule predictions, molecule_id: {molecule_id}")
    try:
        # Call prediction_service.get_molecule_predictions with optional confidence threshold
        predictions = prediction_service.get_molecule_predictions(
            molecule_id=molecule_id,
            confidence_threshold=min_confidence,
            db=db
        )
        return predictions
    except PredictionException as e:
        # Handle PredictionException with 404 Not Found response
        logger.error(f"Prediction Exception: {e}")
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=str(e))


@router.get("/molecules/{molecule_id}/predictions/latest", response_model=Dict[str, PredictionResponse])
def get_latest_molecule_predictions(
    molecule_id: uuid.UUID,
    properties: Optional[List[str]] = None,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_active_user),
) -> Dict[str, PredictionResponse]:
    """
    Endpoint to get the latest predictions for each property of a molecule
    """
    logger.info(f"Request received for latest molecule predictions, molecule_id: {molecule_id}")
    try:
        # Call prediction_service.get_latest_predictions with optional properties list
        latest_predictions = prediction_service.get_latest_predictions(
            molecule_id=molecule_id,
            properties=properties,
            db=db
        )
        return latest_predictions
    except PredictionException as e:
        # Handle PredictionException with 404 Not Found response
        logger.error(f"Prediction Exception: {e}")
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=str(e))


@router.post("/predictions/filter", response_model=Dict[str, Any])
def filter_predictions(
    filter_params: PredictionFilter,
    skip: int = 0,
    limit: int = 100,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_active_user),
) -> Dict[str, Any]:
    """
    Endpoint to filter predictions based on various criteria
    """
    logger.info(f"Prediction filter request received with filter_params: {filter_params}")
    # Call prediction_service.filter_predictions with filter parameters
    filtered_predictions = prediction_service.filter_predictions(
        filter_params=filter_params,
        skip=skip,
        limit=limit,
        db=db
    )
    return filtered_predictions


@router.delete("/predictions/{batch_id}", response_model=Dict[str, Any])
def cancel_prediction_job(
    batch_id: uuid.UUID,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_active_user),
) -> Dict[str, Any]:
    """
    Endpoint to cancel an ongoing prediction job
    """
    logger.info(f"Prediction job cancellation request received for batch_id: {batch_id}")
    try:
        # Call prediction_service.cancel_prediction_job
        cancellation_result = prediction_service.cancel_prediction_job(
            batch_id=batch_id,
            db=db
        )
        return cancellation_result
    except PredictionException as e:
        # Handle PredictionException with 404 Not Found response
        logger.error(f"Prediction Exception: {e}")
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=str(e))
    except AIEngineException as e:
        # Handle AIEngineException with 500 Internal Server Error response
        logger.error(f"AI Engine Exception: {e}")
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail=str(e))


@router.post("/predictions/{batch_id}/retry", response_model=Dict[str, Any])
def retry_failed_prediction(
    batch_id: uuid.UUID,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_active_user),
) -> Dict[str, Any]:
    """
    Endpoint to retry a failed prediction job
    """
    logger.info(f"Prediction job retry request received for batch_id: {batch_id}")
    try:
        # Call prediction_service.retry_failed_prediction
        retry_result = prediction_service.retry_failed_prediction(
            batch_id=batch_id,
            db=db
        )
        return retry_result
    except PredictionException as e:
        # Handle PredictionException with 404 Not Found or 400 Bad Request response
        logger.error(f"Prediction Exception: {e}")
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=str(e))
    except AIEngineException as e:
        # Handle AIEngineException with 500 Internal Server Error response
        logger.error(f"AI Engine Exception: {e}")
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail=str(e))


@router.get("/predictions/properties", response_model=Dict[str, List[str]])
def get_available_properties() -> Dict[str, List[str]]:
    """
    Endpoint to get the list of properties that can be predicted by AI
    """
    logger.info("Request received for available prediction properties")
    # Return dictionary with PREDICTABLE_PROPERTIES list
    return {"properties": PREDICTABLE_PROPERTIES}