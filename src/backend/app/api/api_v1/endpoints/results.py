from typing import List, Dict, Optional, Any, Union
import uuid
import io
import csv

from fastapi import APIRouter, Depends, HTTPException, status, Query, Path, Body, File, UploadFile, Form
from sqlalchemy.orm import Session

# Internal imports
from ...api.deps import get_db, get_current_user, get_current_pharma_user, get_current_cro_user, get_submission_access
from ...services.result_service import result_service, ResultServiceException
from ...schemas.result import ResultCreate, ResultUpdate, ResultFilter, ResultProcessRequest, ResultReviewRequest, ResultCSVMapping, Result
from ...models.user import User
from ...models.result import ResultStatus
from ...constants.document_types import DocumentType
from ...core.logging import get_logger
from ...core.exceptions import ResultServiceException, NotFoundException, ValidationException, AuthorizationException

# FastAPI router for result endpoints
router = APIRouter(prefix="/results", tags=["results"])

# Initialize logger
logger = get_logger(__name__)

@router.post("/", response_model=Result, status_code=status.HTTP_201_CREATED)
def create_result(
    result_data: ResultCreate,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
) -> Result:
    """Create a new result record for a CRO submission"""
    logger.info(f"Attempting to create result for submission {result_data.submission_id}")
    try:
        # Set uploaded_by to current user's ID if not provided
        result_data.uploaded_by = current_user.id
        # Create result using result_service.create_result
        created_result = result_service.create_result(result_data, db=db)
        # Return created result data
        return Result(**created_result)
    except Exception as e:
        logger.error(f"Error creating result: {e}")
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail=str(e))

@router.get("/{result_id}", response_model=Result)
def get_result(
    result_id: uuid.UUID,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
) -> Result:
    """Get a result by ID with all relationships"""
    try:
        # Get result with relationships using result_service.get_result
        result_data = result_service.get_result(result_id, db=db)
        # If result not found, raise NotFoundException
        if not result_data:
            raise NotFoundException(message=f"Result with ID {result_id} not found", resource_type="Result")
        # Check if user has access to the result's submission
        get_submission_access(result_data['submission_id'], current_user, db)
        # Return result data with relationships
        return Result(**result_data)
    except NotFoundException as e:
        logger.error(f"Result not found: {e}")
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=e.message)
    except AuthorizationException as e:
        logger.error(f"Authorization error: {e}")
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail=e.message)
    except Exception as e:
        logger.error(f"Error getting result: {e}")
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail=str(e))

@router.put("/{result_id}", response_model=Result)
def update_result(
    result_id: uuid.UUID,
    result_data: ResultUpdate,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
) -> Result:
    """Update an existing result"""
    logger.info(f"Attempting to update result with ID {result_id}")
    try:
        # Get result by ID
        existing_result = result_service.get_result(result_id, db=db)
        # If result not found, raise NotFoundException
        if not existing_result:
            raise NotFoundException(message=f"Result with ID {result_id} not found", resource_type="Result")
        # Check if user has permission to update the result
        get_submission_access(existing_result['submission_id'], current_user, db)
        # Update result using result_service.update_result
        updated_result = result_service.update_result(result_id, result_data, db=db)
        # Return updated result data
        return Result(**updated_result)
    except NotFoundException as e:
        logger.error(f"Result not found: {e}")
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=e.message)
    except AuthorizationException as e:
        logger.error(f"Authorization error: {e}")
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail=e.message)
    except Exception as e:
        logger.error(f"Error updating result: {e}")
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail=str(e))

@router.get("/", response_model=Dict[str, Any])
def list_results(
    filter_params: Optional[ResultFilter] = Depends(),
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
    skip: int = Query(0, description="Skip n results"),
    limit: int = Query(100, description="Maximum results per page")
) -> Dict[str, Any]:
    """List results with optional filtering"""
    try:
        # Call result_service.filter_results with filter parameters
        filtered_results = result_service.filter_results(filter_params, skip, limit, db=db)
        # Return filtered results with pagination metadata
        return filtered_results
    except Exception as e:
        logger.error(f"Error listing results: {e}")
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail=str(e))

@router.get("/submission/{submission_id}", response_model=Dict[str, Any])
def list_results_by_submission(
    submission_id: uuid.UUID,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
    skip: int = Query(0, description="Skip n results"),
    limit: int = Query(100, description="Maximum results per page")
) -> Dict[str, Any]:
    """List results for a specific submission"""
    try:
        # Check if user has access to the submission
        get_submission_access(submission_id, current_user, db)
        # Call result_service.get_results_by_submission with submission_id
        submission_results = result_service.get_results_by_submission(submission_id, skip, limit, db=db)
        # Return submission results with pagination metadata
        return submission_results
    except AuthorizationException as e:
        logger.error(f"Authorization error: {e}")
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail=e.message)
    except Exception as e:
        logger.error(f"Error listing results by submission: {e}")
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail=str(e))

@router.get("/molecule/{molecule_id}", response_model=Dict[str, Any])
def list_results_by_molecule(
    molecule_id: uuid.UUID,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
    skip: int = Query(0, description="Skip n results"),
    limit: int = Query(100, description="Maximum results per page")
) -> Dict[str, Any]:
    """List results that include a specific molecule"""
    try:
        # Call result_service.get_results_by_molecule with molecule_id
        molecule_results = result_service.get_results_by_molecule(molecule_id, skip, limit, db=db)
        # Return molecule results with pagination metadata
        return molecule_results
    except Exception as e:
        logger.error(f"Error listing results by molecule: {e}")
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail=str(e))

@router.post("/process", response_model=Dict[str, Any])
def process_result(
    process_data: ResultProcessRequest,
    current_user: User = Depends(get_current_cro_user),
    db: Session = Depends(get_db)
) -> Dict[str, Any]:
    """Process a result and mark it as processed"""
    logger.info(f"Attempting to process result with ID {process_data.result_id}")
    try:
        # Process result using result_service.process_result
        processing_result = result_service.process_result(process_data, db=db)
        # Log processing outcome
        logger.info(f"Processing outcome for result {process_data.result_id}: {processing_result}")
        # Return processing result with success flag and message
        return processing_result
    except Exception as e:
        logger.error(f"Error processing result: {e}")
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail=str(e))

@router.post("/review", response_model=Dict[str, Any])
def review_result(
    review_data: ResultReviewRequest,
    current_user: User = Depends(get_current_pharma_user),
    db: Session = Depends(get_db)
) -> Dict[str, Any]:
    """Review a result and apply to molecules"""
    logger.info(f"Attempting to review result with ID {review_data.result_id}")
    try:
        # Review result using result_service.review_result
        review_result = result_service.review_result(review_data, db=db)
        # Log review outcome
        logger.info(f"Review outcome for result {review_data.result_id}: {review_result}")
        # Return review result with success flag and message
        return review_result
    except Exception as e:
        logger.error(f"Error reviewing result: {e}")
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail=str(e))

@router.post("/{result_id}/reject", response_model=Dict[str, Any])
def reject_result(
    result_id: uuid.UUID,
    rejection_reason: str = Body(..., description="Reason for rejecting the result"),
    current_user: User = Depends(get_current_pharma_user),
    db: Session = Depends(get_db)
) -> Dict[str, Any]:
    """Reject a result"""
    logger.info(f"Attempting to reject result with ID {result_id}")
    try:
        # Reject result using result_service.reject_result
        rejection_result = result_service.reject_result(result_id, rejection_reason, db=db)
        # Log rejection outcome
        logger.info(f"Rejection outcome for result {result_id}: {rejection_result}")
        # Return rejection result with success flag and message
        return rejection_result
    except Exception as e:
        logger.error(f"Error rejecting result: {e}")
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail=str(e))

@router.post("/{result_id}/apply", response_model=Dict[str, Any])
def apply_to_molecules(
    result_id: uuid.UUID,
    current_user: User = Depends(get_current_pharma_user),
    db: Session = Depends(get_db)
) -> Dict[str, Any]:
    """Apply result properties to molecules"""
    logger.info(f"Attempting to apply result with ID {result_id} to molecules")
    try:
        # Apply result to molecules using result_service.apply_to_molecules
        application_result = result_service.apply_to_molecules(result_id, db=db)
        # Log application outcome
        logger.info(f"Application outcome for result {result_id}: {application_result}")
        # Return application result with success flag, message, and count of updated molecules
        return application_result
    except Exception as e:
        logger.error(f"Error applying result to molecules: {e}")
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail=str(e))

@router.post("/{result_id}/csv", response_model=Dict[str, Any])
async def upload_csv(
    result_id: uuid.UUID,
    file: UploadFile = File(..., description="CSV file containing result data"),
    mapping: ResultCSVMapping = Depends(),
    current_user: User = Depends(get_current_cro_user),
    db: Session = Depends(get_db)
) -> Dict[str, Any]:
    """Upload and import result data from CSV file"""
    logger.info(f"Attempting to upload CSV data for result {result_id}")
    try:
        # Read file contents into BytesIO object
        csv_file = io.BytesIO(await file.read())
        # Import result data from CSV using result_service.import_from_csv
        import_summary = result_service.import_from_csv(result_id, csv_file, mapping, db=db)
        # Log import outcome
        logger.info(f"Import outcome for result {result_id}: {import_summary}")
        # Return import summary with counts and errors
        return import_summary
    except Exception as e:
        logger.error(f"Error uploading CSV: {e}")
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail=str(e))

@router.post("/csv/preview", response_model=Dict[str, Any])
async def preview_csv(
    file: UploadFile = File(..., description="CSV file to preview"),
    preview_rows: int = Form(5, description="Number of rows to preview"),
    current_user: User = Depends(get_current_user)
) -> Dict[str, Any]:
    """Get a preview of CSV file contents for column mapping"""
    try:
        # Read file contents into BytesIO object
        csv_file = io.BytesIO(await file.read())
        # Get CSV preview using result_service.get_csv_preview
        preview_data = result_service.get_csv_preview(csv_file, preview_rows)
        # Return preview data with headers, sample rows, and mapping suggestions
        return preview_data
    except Exception as e:
        logger.error(f"Error previewing CSV: {e}")
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail=str(e))

@router.post("/{result_id}/upload-url", response_model=Dict[str, Any])
def generate_upload_url(
    result_id: uuid.UUID,
    filename: str = Body(..., description="Name of the file to be uploaded"),
    content_type: Optional[str] = Body(None, description="Content type of the file"),
    current_user: User = Depends(get_current_cro_user),
    db: Session = Depends(get_db)
) -> Dict[str, Any]:
    """Generate a presigned URL for result file upload"""
    logger.info(f"Attempting to generate upload URL for file {filename} for result {result_id}")
    try:
        # Generate upload URL using result_service.generate_result_upload_url
        upload_url_data = result_service.generate_result_upload_url(filename, result_id, current_user.id, content_type, db=db)
        # Log successful URL generation
        logger.info(f"Successfully generated upload URL for file {filename} for result {result_id}")
        # Return upload URL and document ID
        return upload_url_data
    except Exception as e:
        logger.error(f"Error generating upload URL: {e}")
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail=str(e))

@router.post("/{result_id}/documents", response_model=Dict[str, Any])
def create_result_document(
    result_id: uuid.UUID,
    document_type: str = Body(..., description="Type of document (RESULTS_REPORT or QUALITY_CONTROL)"),
    file_name: str = Body(..., description="Name of the file"),
    file_url: str = Body(..., description="URL of the file"),
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
) -> Dict[str, Any]:
    """Create a document associated with a result"""
    logger.info(f"Attempting to create document {file_name} for result {result_id}")
    try:
        # Create result document using result_service.create_result_document
        document_data = result_service.create_result_document(result_id, document_type, file_name, file_url, current_user.id, db=db)
        # Log successful document creation
        logger.info(f"Successfully created document {file_name} for result {result_id}")
        # Return created document data
        return document_data
    except Exception as e:
        logger.error(f"Error creating document: {e}")
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail=str(e))

@router.get("/statistics", response_model=Dict[str, Any])
def get_result_statistics(
    submission_id: Optional[uuid.UUID] = Query(None, description="Filter statistics by submission ID"),
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
) -> Dict[str, Any]:
    """Get statistics about results"""
    try:
        # Get result statistics using result_service.get_result_statistics
        statistics = result_service.get_result_statistics(submission_id=submission_id, db=db)
        # Return statistics dictionary
        return statistics
    except Exception as e:
        logger.error(f"Error getting result statistics: {e}")
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail=str(e))

def handle_exception(exc: Exception) -> HTTPException:
    """Exception handler for result endpoints"""
    logger.error(f"Exception occurred: {exc}")
    if isinstance(exc, ResultServiceException):
        return HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(exc))
    elif isinstance(exc, NotFoundException):
        return HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=str(exc))
    elif isinstance(exc, ValidationException):
        return HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(exc))
    elif isinstance(exc, AuthorizationException):
        return HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail=str(exc))
    else:
        return HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail="An unexpected error occurred")

# Export the router