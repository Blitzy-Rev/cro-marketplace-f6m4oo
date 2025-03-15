from typing import List, Dict, Optional, Any, Union
import uuid
import io
import csv

from sqlalchemy.orm import Session
import pandas  # pandas ^1.5.0

from ..crud.crud_result import result
from ..models.result import Result, ResultStatus
from ..schemas.result import ResultCreate, ResultUpdate, ResultFilter, ResultProcessRequest, ResultReviewRequest, ResultCSVMapping
from ..constants.document_types import DocumentType
from ..constants.molecule_properties import PropertySource
from ..integrations.aws.s3 import S3Client  # boto3 ^1.26.0
from .document_service import DocumentService
from ..core.logging import get_logger
from ..core.exceptions import ServiceException

# Initialize logger
logger = get_logger(__name__)

# Constants
RESULT_STORAGE_FOLDER = "result_uploads"
DEFAULT_PREVIEW_ROWS = 5


class ResultServiceException(ServiceException):
    """Exception class for result service errors"""
    def __init__(self, message: str):
        super().__init__(message)


class ResultService:
    """Service for managing experimental results from CROs, including processing, validation, and integration with molecules"""

    def __init__(self, document_service: Optional[DocumentService] = None):
        """Initialize the ResultService with required dependencies"""
        # Initialize _s3_client as a new S3Client instance
        self._s3_client = S3Client()
        # Initialize _document_service from parameter or create new instance
        self._document_service = document_service or DocumentService()
        # Log service initialization
        logger.info("ResultService initialized")

    def create_result(self, result_data: ResultCreate, db: Optional[Session] = None) -> Dict[str, Any]:
        """Create a new result record for a CRO submission"""
        # Log result creation attempt
        logger.info(f"Attempting to create result for submission {result_data.submission_id}")
        # Create result using result.create_result
        created_result = result.create_result(result_data, db=db)
        # Log successful result creation
        logger.info(f"Successfully created result with ID {created_result.id}")
        # Return created result as dictionary
        return created_result.to_dict()

    def get_result(self, result_id: uuid.UUID, db: Optional[Session] = None) -> Optional[Dict[str, Any]]:
        """Get a result by ID with all relationships"""
        # Get result with relationships using result.get_with_relationships
        result_data = result.get_with_relationships(result_id, db=db)
        # Return result data or None if not found
        return result_data

    def update_result(self, result_id: uuid.UUID, result_data: ResultUpdate, db: Optional[Session] = None) -> Dict[str, Any]:
        """Update an existing result"""
        # Log result update attempt
        logger.info(f"Attempting to update result with ID {result_id}")
        # Get result by ID
        db_obj = result.get(result_id, db=db)
        # If result not found, return error result
        if not db_obj:
            logger.warning(f"Result with ID {result_id} not found")
            return {"success": False, "message": f"Result with ID {result_id} not found"}
        # Update result using result.update_result
        updated_result = result.update_result(db_obj, result_data, db=db)
        # Log successful result update
        logger.info(f"Successfully updated result with ID {result_id}")
        # Return updated result as dictionary
        return updated_result.to_dict()

    def filter_results(self, filter_params: ResultFilter, skip: int, limit: int, db: Optional[Session] = None) -> Dict[str, Any]:
        """Filter results based on multiple criteria"""
        # Filter results using result.filter_results
        filtered_results = result.filter_results(filter_params, skip, limit, db=db)
        # Return filtered results with pagination metadata
        return filtered_results

    def get_results_by_submission(self, submission_id: uuid.UUID, skip: int, limit: int, db: Optional[Session] = None) -> Dict[str, Any]:
        """Get all results for a specific submission"""
        # Create filter with submission_id
        filter_params = ResultFilter(submission_id=submission_id)
        # Call self.filter_results with the filter
        filtered_results = self.filter_results(filter_params, skip, limit, db=db)
        # Return filtered results with pagination metadata
        return filtered_results

    def get_results_by_molecule(self, molecule_id: uuid.UUID, skip: int, limit: int, db: Optional[Session] = None) -> Dict[str, Any]:
        """Get results that include a specific molecule"""
        # Create filter with molecule_id
        filter_params = ResultFilter(molecule_id=molecule_id)
        # Call self.filter_results with the filter
        filtered_results = self.filter_results(filter_params, skip, limit, db=db)
        # Return filtered results with pagination metadata
        return filtered_results

    def process_result(self, process_data: ResultProcessRequest, db: Optional[Session] = None) -> Dict[str, Any]:
        """Process a result and mark it as processed"""
        # Log result processing attempt
        logger.info(f"Attempting to process result with ID {process_data.result_id}")
        # Process result using result.process_result
        processing_result = result.process_result(process_data, db=db)
        # Log processing outcome
        logger.info(f"Processing outcome for result {process_data.result_id}: {processing_result}")
        # Return processing result with success flag and message
        return processing_result

    def review_result(self, review_data: ResultReviewRequest, db: Optional[Session] = None) -> Dict[str, Any]:
        """Review a result and apply to molecules"""
        # Log result review attempt
        logger.info(f"Attempting to review result with ID {review_data.result_id}")
        # Review result using result.review_result
        review_result = result.review_result(review_data, db=db)
        # Log review outcome
        logger.info(f"Review outcome for result {review_data.result_id}: {review_result}")
        # Return review result with success flag and message
        return review_result

    def reject_result(self, result_id: uuid.UUID, rejection_reason: str, db: Optional[Session] = None) -> Dict[str, Any]:
        """Reject a result"""
        # Log result rejection attempt
        logger.info(f"Attempting to reject result with ID {result_id}")
        # Reject result using result.reject_result
        rejection_result = result.reject_result(result_id, rejection_reason, db=db)
        # Log rejection outcome
        logger.info(f"Rejection outcome for result {result_id}: {rejection_result}")
        # Return rejection result with success flag and message
        return rejection_result

    def apply_to_molecules(self, result_id: uuid.UUID, db: Optional[Session] = None) -> Dict[str, Any]:
        """Apply result properties to molecules"""
        # Log application attempt
        logger.info(f"Attempting to apply result with ID {result_id} to molecules")
        # Apply result to molecules using result.apply_to_molecules
        application_result = result.apply_to_molecules(result_id, db=db)
        # Log application outcome
        logger.info(f"Application outcome for result {result_id}: {application_result}")
        # Return application result with success flag, message, and count of updated molecules
        return application_result

    def upload_result_file(self, file_content: bytes, filename: str, result_id: uuid.UUID) -> Dict[str, Any]:
        """Upload a result file to S3 storage"""
        # Log file upload attempt
        logger.info(f"Attempting to upload file {filename} for result {result_id}")
        # Generate S3 key for result file
        s3_key = f"{RESULT_STORAGE_FOLDER}/{result_id}/{filename}"
        # Upload file to S3 using s3_client.upload
        self._s3_client.upload(content=file_content, key=s3_key)
        # Create document record for the uploaded file
        document_data = {
            "result_id": result_id,
            "document_type": DocumentType.RESULTS_REPORT.value,
            "file_name": filename,
            "file_url": s3_key
        }
        # Log successful upload
        logger.info(f"Successfully uploaded file {filename} to S3 for result {result_id}")
        # Return upload result with file URL
        return {"success": True, "message": f"File {filename} uploaded successfully", "file_url": s3_key}

    def generate_result_upload_url(self, filename: str, result_id: uuid.UUID, uploaded_by: uuid.UUID, content_type: Optional[str] = None) -> Dict[str, Any]:
        """Generate a presigned URL for result file upload"""
        # Log URL generation attempt
        logger.info(f"Attempting to generate upload URL for file {filename} for result {result_id}")
        # Get result by ID to verify it exists
        existing_result = result.get(result_id)
        # If result not found, raise ResultServiceException
        if not existing_result:
            raise ResultServiceException(f"Result with ID {result_id} not found")
        # Get submission_id from result
        submission_id = existing_result.submission_id
        # Generate upload URL using document_service.generate_upload_url
        upload_response = self._document_service.generate_upload_url(
            filename=filename,
            document_type=DocumentType.RESULTS_REPORT,
            submission_id=submission_id,
            owner_id=uploaded_by,
            content_type=content_type
        )
        # Log successful URL generation
        logger.info(f"Successfully generated upload URL for file {filename} for result {result_id}")
        # Return upload URL and document ID
        return upload_response

    def import_from_csv(self, result_id: uuid.UUID, csv_file: io.BytesIO, mapping: ResultCSVMapping, db: Optional[Session] = None) -> Dict[str, Any]:
        """Import result data from CSV file"""
        # Log CSV import attempt
        logger.info(f"Attempting to import CSV data for result {result_id}")
        # Import result data from CSV using result.import_from_csv
        import_summary = result.import_from_csv(
            result_id=result_id,
            csv_file=csv_file,
            column_mapping=mapping.column_mapping,
            has_header=mapping.has_header,
            delimiter=mapping.delimiter,
            db=db
        )
        # Log import outcome
        logger.info(f"Import outcome for result {result_id}: {import_summary}")
        # Return import summary with counts and errors
        return import_summary

    def get_csv_preview(self, csv_file: io.BytesIO, preview_rows: int = DEFAULT_PREVIEW_ROWS) -> Dict[str, Any]:
        """Get a preview of CSV file contents for column mapping"""
        # Read CSV file into pandas DataFrame
        df = pandas.read_csv(csv_file)
        # Get headers and sample rows up to preview_rows
        headers = list(df.columns)
        sample_rows = df.head(preview_rows).to_dict('records')
        # Generate column mapping suggestions based on headers
        mapping_suggestions = {}
        for header in headers:
            mapping_suggestions[header] = None  # Implement logic to suggest mappings
        # Return preview data with headers, sample rows, and mapping suggestions
        return {"headers": headers, "sample_rows": sample_rows, "mapping_suggestions": mapping_suggestions}

    def create_result_document(self, result_id: uuid.UUID, document_type: str, file_name: str, file_url: str, uploaded_by: uuid.UUID, db: Optional[Session] = None) -> Dict[str, Any]:
        """Create a document associated with a result"""
        # Log document creation attempt
        logger.info(f"Attempting to create document {file_name} for result {result_id}")
        # Create result document using result.create_result_document
        document_data = result.create_result_document(
            result_id=result_id,
            document_type=document_type,
            file_name=file_name,
            file_url=file_url,
            uploaded_by=uploaded_by,
            db=db
        )
        # Log successful document creation
        logger.info(f"Successfully created document {file_name} for result {result_id}")
        # Return created document data
        return document_data

    def get_result_statistics(self, submission_id: Optional[uuid.UUID] = None, db: Optional[Session] = None) -> Dict[str, Any]:
        """Get statistics about results"""
        # Get result statistics using result.get_result_statistics
        statistics = result.get_result_statistics(submission_id=submission_id, db=db)
        # Return statistics dictionary
        return statistics


# Create a singleton instance
result_service = ResultService()