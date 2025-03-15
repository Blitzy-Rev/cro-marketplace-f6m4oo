from typing import List, Dict, Any, Optional, Union  # Typing for type hints
import uuid  # UUID for unique identifiers

from fastapi import APIRouter, Depends, HTTPException, status, Query, Path, Body  # FastAPI for API endpoints
from sqlalchemy.orm import Session  # SQLAlchemy for database interaction

# Internal imports for dependency injection, CRUD operations, models, and schemas
from ...api.deps import get_db, get_current_user, get_current_pharma_user, get_current_cro_user, get_submission_access
from ...crud.crud_submission import submission  # CRUD operations for submission management
from ...crud.crud_document import document  # CRUD operations for document management
from ...crud.crud_result import result  # CRUD operations for result management
from ...crud.crud_cro_service import cro_service  # CRUD operations for CRO service management
from ...schemas.submission import SubmissionCreate, SubmissionUpdate, SubmissionFilter, SubmissionAction, SubmissionPricingUpdate, Submission, SubmissionWithDocumentRequirements, SubmissionStatusCount  # Pydantic schemas for submission data
from ...models.user import User  # User model for authentication and authorization
from ...constants.submission_status import SubmissionStatus, ACTIVE_STATUSES, TERMINAL_STATUSES, EDITABLE_STATUSES, PHARMA_EDITABLE_STATUSES, CRO_EDITABLE_STATUSES  # Constants for submission status management
from ...core.logging import get_logger  # Get logger for consistent log formatting
from ...core.exceptions import NotFoundException, ValidationException, AuthorizationException  # Exception classes for error handling

# Initialize logger
logger = get_logger(__name__)

# Create API router for submission endpoints
router = APIRouter(prefix="/submissions", tags=["submissions"])


@router.post("/", response_model=Submission, status_code=status.HTTP_201_CREATED)
def create_submission(
    submission_data: SubmissionCreate,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
) -> Submission:
    """
    Create a new submission
    """
    logger.info(f"Attempting to create a new submission by user: {current_user.id}")
    
    # Set created_by to current user's ID if not provided
    if not submission_data.created_by:
        submission_data.created_by = current_user.id
    
    # Create submission using submission.create_submission
    try:
        created_submission = submission.create_submission(submission_data, current_user, db)
        logger.info(f"Successfully created submission with ID: {created_submission.id}")
        return created_submission
    except Exception as e:
        logger.error(f"Failed to create submission: {str(e)}")
        raise


@router.get("/{submission_id}", response_model=Submission)
def get_submission(
    submission_id: uuid.UUID,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
) -> Submission:
    """
    Get a submission by ID with all relationships
    """
    logger.info(f"Attempting to get submission with ID: {submission_id} by user: {current_user.id}")
    
    # Get submission with relationships using submission.get_with_relationships
    submission_data = submission.get_with_relationships(submission_id, db)
    
    # If submission not found, raise NotFoundException
    if not submission_data:
        logger.warning(f"Submission with ID: {submission_id} not found")
        raise NotFoundException(message=f"Submission with ID: {submission_id} not found", resource_type="Submission")
    
    # Check if user has access to the submission
    try:
        get_submission_access(submission_data, current_user)
    except AuthorizationException as e:
        logger.warning(f"User {current_user.id} does not have access to submission {submission_id}: {str(e)}")
        raise
    
    logger.info(f"Successfully retrieved submission with ID: {submission_id}")
    return submission_data


@router.put("/{submission_id}", response_model=Submission)
def update_submission(
    submission_id: uuid.UUID,
    submission_data: SubmissionUpdate,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
) -> Submission:
    """
    Update an existing submission
    """
    logger.info(f"Attempting to update submission with ID: {submission_id} by user: {current_user.id}")
    
    # Get submission by ID
    db_submission = submission.get(submission_id, db)
    
    # If submission not found, raise NotFoundException
    if not db_submission:
        logger.warning(f"Submission with ID: {submission_id} not found")
        raise NotFoundException(message=f"Submission with ID: {submission_id} not found", resource_type="Submission")
    
    # Check if user has permission to update the submission
    try:
        get_submission_access(db_submission, current_user)
    except AuthorizationException as e:
        logger.warning(f"User {current_user.id} does not have permission to update submission {submission_id}: {str(e)}")
        raise
    
    # Check if submission is in editable state
    if db_submission.status not in EDITABLE_STATUSES:
        logger.warning(f"Submission with ID: {submission_id} is not in an editable state")
        raise ValidationException(message="Submission is not in an editable state")
    
    # Update submission using submission.update_submission
    try:
        updated_submission = submission.update_submission(db_submission, submission_data, db)
        logger.info(f"Successfully updated submission with ID: {submission_id}")
        return updated_submission
    except Exception as e:
        logger.error(f"Failed to update submission: {str(e)}")
        raise


@router.get("/", response_model=Dict[str, Any])
def list_submissions(
    filter_params: Optional[SubmissionFilter] = Depends(),
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
    skip: int = Query(0, description="Number of records to skip"),
    limit: int = Query(100, description="Maximum number of records to return")
) -> Dict[str, Any]:
    """
    List submissions with optional filtering
    """
    logger.info(f"Attempting to list submissions by user: {current_user.id}")
    
    # If filter_params is None, initialize empty filter
    if filter_params is None:
        filter_params = SubmissionFilter()
    
    # If user is pharma user, filter by created_by = current_user.id
    if current_user.is_pharma_user():
        filter_params.created_by = current_user.id
    
    # If user is CRO user, filter by CRO organization
    if current_user.is_cro_user():
        # TODO: Implement filtering by CRO organization
        pass
    
    # Call submission.filter_submissions with filter parameters
    try:
        filtered_submissions = submission.filter_submissions(filter_params, db, skip, limit)
        logger.info(f"Successfully listed submissions")
        return filtered_submissions
    except Exception as e:
        logger.error(f"Failed to list submissions: {str(e)}")
        raise


@router.get("/active", response_model=Dict[str, Any])
def list_active_submissions(
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
    skip: int = Query(0, description="Number of records to skip"),
    limit: int = Query(100, description="Maximum number of records to return")
) -> Dict[str, Any]:
    """
    List active submissions (not in terminal state)
    """
    logger.info(f"Attempting to list active submissions by user: {current_user.id}")
    
    # Call submission.get_active_submissions with pagination parameters
    try:
        active_submissions = submission.get_active_submissions(db, skip, limit)
        logger.info(f"Successfully listed active submissions")
        return active_submissions
    except Exception as e:
        logger.error(f"Failed to list active submissions: {str(e)}")
        raise


@router.get("/my", response_model=Dict[str, Any])
def list_my_submissions(
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
    skip: int = Query(0, description="Number of records to skip"),
    limit: int = Query(100, description="Maximum number of records to return")
) -> Dict[str, Any]:
    """
    List submissions created by the current user
    """
    logger.info(f"Attempting to list submissions created by user: {current_user.id}")
    
    # Call submission.get_by_creator with current_user.id
    try:
        my_submissions = submission.get_by_creator(current_user.id, db, skip, limit)
        logger.info(f"Successfully listed submissions created by user: {current_user.id}")
        return my_submissions
    except Exception as e:
        logger.error(f"Failed to list submissions created by user: {str(e)}")
        raise


@router.get("/status/{status}", response_model=Dict[str, Any])
def list_submissions_by_status(
    status: List[str] = Path(..., description="List of submission statuses to filter by"),
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
    skip: int = Query(0, description="Number of records to skip"),
    limit: int = Query(100, description="Maximum number of records to return")
) -> Dict[str, Any]:
    """
    List submissions with specific status values
    """
    logger.info(f"Attempting to list submissions with status: {status} by user: {current_user.id}")
    
    # Validate status values against SubmissionStatus enum
    for s in status:
        try:
            SubmissionStatus(s)
        except ValueError:
            raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=f"Invalid status: {s}")
    
    # Call submission.get_by_status with status values
    try:
        status_submissions = submission.get_by_status(status, db, skip, limit)
        logger.info(f"Successfully listed submissions with status: {status}")
        return status_submissions
    except Exception as e:
        logger.error(f"Failed to list submissions with status: {str(e)}")
        raise


@router.post("/{submission_id}/actions", response_model=Dict[str, Any])
def process_submission_action(
    submission_id: uuid.UUID,
    action_data: SubmissionAction,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
) -> Dict[str, Any]:
    """
    Process an action on a submission
    """
    logger.info(f"Attempting to process action: {action_data.action} on submission with ID: {submission_id} by user: {current_user.id}")
    
    # Get submission by ID
    db_submission = submission.get(submission_id, db)
    
    # If submission not found, raise NotFoundException
    if not db_submission:
        logger.warning(f"Submission with ID: {submission_id} not found")
        raise NotFoundException(message=f"Submission with ID: {submission_id} not found", resource_type="Submission")
    
    # Check if user has permission to perform the action
    try:
        get_submission_access(db_submission, current_user)
    except AuthorizationException as e:
        logger.warning(f"User {current_user.id} does not have permission to perform action on submission {submission_id}: {str(e)}")
        raise
    
    # Call submission.process_submission_action with action_data
    try:
        action_result = submission.process_submission_action(submission_id, action_data, current_user, db)
        logger.info(f"Successfully processed action: {action_data.action} on submission with ID: {submission_id}")
        return action_result
    except Exception as e:
        logger.error(f"Failed to process action: {str(e)}")
        raise


@router.get("/counts", response_model=List[SubmissionStatusCount])
def get_submission_counts(
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
) -> List[SubmissionStatusCount]:
    """
    Get count of submissions grouped by status
    """
    logger.info(f"Attempting to get submission counts by user: {current_user.id}")
    
    # If user is pharma user, get counts for user's submissions
    if current_user.is_pharma_user():
        # TODO: Implement filtering by user's submissions
        pass
    
    # If user is CRO user, get counts for CRO's submissions
    if current_user.is_cro_user():
        # TODO: Implement filtering by CRO's submissions
        pass
    
    # Call submission.get_submission_counts_by_status
    try:
        status_counts = submission.get_submission_counts_by_status(db)
        logger.info(f"Successfully retrieved submission counts")
        return status_counts
    except Exception as e:
        logger.error(f"Failed to retrieve submission counts: {str(e)}")
        raise


@router.get("/{submission_id}/documents/check", response_model=SubmissionWithDocumentRequirements)
def check_required_documents(
    submission_id: uuid.UUID,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
) -> SubmissionWithDocumentRequirements:
    """
    Check if a submission has all required documents
    """
    logger.info(f"Attempting to check required documents for submission with ID: {submission_id} by user: {current_user.id}")
    
    # Get submission by ID
    db_submission = submission.get(submission_id, db)
    
    # If submission not found, raise NotFoundException
    if not db_submission:
        logger.warning(f"Submission with ID: {submission_id} not found")
        raise NotFoundException(message=f"Submission with ID: {submission_id} not found", resource_type="Submission")
    
    # Check if user has access to the submission
    try:
        get_submission_access(db_submission, current_user)
    except AuthorizationException as e:
        logger.warning(f"User {current_user.id} does not have access to submission {submission_id}: {str(e)}")
        raise
    
    # Call submission.check_required_documents
    try:
        document_requirements = submission.check_required_documents(submission_id, db)
        logger.info(f"Successfully checked required documents for submission with ID: {submission_id}")
        return document_requirements
    except Exception as e:
        logger.error(f"Failed to check required documents: {str(e)}")
        raise


@router.get("/{submission_id}/timeline", response_model=List[Dict[str, Any]])
def get_submission_timeline(
    submission_id: uuid.UUID,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
) -> List[Dict[str, Any]]:
    """
    Get timeline of status changes for a submission
    """
    logger.info(f"Attempting to get timeline for submission with ID: {submission_id} by user: {current_user.id}")
    
    # Get submission by ID
    db_submission = submission.get(submission_id, db)
    
    # If submission not found, raise NotFoundException
    if not db_submission:
        logger.warning(f"Submission with ID: {submission_id} not found")
        raise NotFoundException(message=f"Submission with ID: {submission_id} not found", resource_type="Submission")
    
    # Check if user has access to the submission
    try:
        get_submission_access(db_submission, current_user)
    except AuthorizationException as e:
        logger.warning(f"User {current_user.id} does not have access to submission {submission_id}: {str(e)}")
        raise
    
    # Call submission.get_submission_timeline
    try:
        timeline = submission.get_submission_timeline(submission_id, db)
        logger.info(f"Successfully retrieved timeline for submission with ID: {submission_id}")
        return timeline
    except Exception as e:
        logger.error(f"Failed to retrieve timeline: {str(e)}")
        raise


@router.post("/{submission_id}/pricing", response_model=Submission)
def set_submission_pricing(
    submission_id: uuid.UUID,
    pricing_data: SubmissionPricingUpdate,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
) -> Submission:
    """
    Set pricing and timeline information for a submission (CRO only)
    """
    logger.info(f"Attempting to set pricing for submission with ID: {submission_id} by user: {current_user.id}")
    
    # Verify user is a CRO user
    if not current_user.is_cro_user():
        logger.warning(f"User {current_user.id} is not a CRO user")
        raise AuthorizationException(message="Only CRO users can set pricing")
    
    # Get submission by ID
    db_submission = submission.get(submission_id, db)
    
    # If submission not found, raise NotFoundException
    if not db_submission:
        logger.warning(f"Submission with ID: {submission_id} not found")
        raise NotFoundException(message=f"Submission with ID: {submission_id} not found", resource_type="Submission")
    
    # Check if submission is in PENDING_REVIEW status
    if db_submission.status != SubmissionStatus.PENDING_REVIEW.value:
        logger.warning(f"Submission with ID: {submission_id} is not in PENDING_REVIEW status")
        raise ValidationException(message="Submission must be in PENDING_REVIEW status to set pricing")
    
    # Create action data with PROVIDE_PRICING action and pricing_data
    action_data = SubmissionAction(action=SubmissionStatus.PRICING_PROVIDED.value, data=pricing_data.model_dump())
    
    # Call submission.process_submission_action
    try:
        updated_submission = submission.process_submission_action(submission_id, action_data, current_user, db)
        logger.info(f"Successfully set pricing for submission with ID: {submission_id}")
        return updated_submission
    except Exception as e:
        logger.error(f"Failed to set pricing: {str(e)}")
        raise


@router.exception_handler(Exception)
async def handle_exception(exc: Exception):
    """
    Exception handler for submission endpoints
    """
    logger.error(f"Exception occurred: {type(exc).__name__} - {str(exc)}")
    
    if isinstance(exc, NotFoundException):
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=exc.message)
    elif isinstance(exc, ValidationException):
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=exc.message)
    elif isinstance(exc, AuthorizationException):
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail=exc.message)
    else:
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail="An internal server error occurred")