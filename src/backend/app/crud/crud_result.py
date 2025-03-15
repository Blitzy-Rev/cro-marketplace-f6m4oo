from typing import List, Dict, Optional, Any, Union
from sqlalchemy import select, and_, or_
from sqlalchemy.orm import Session
import uuid
from datetime import datetime
import csv
import io

from .base import CRUDBase
from ..models.result import Result, ResultStatus
from ..schemas.result import ResultCreate, ResultUpdate, ResultFilter, ResultProcessRequest, ResultReviewRequest
from ..db.session import db_session
from ..models.submission import Submission
from .crud_molecule import molecule
from .crud_document import document
from ..core.logging import get_logger
from ..constants.document_types import DocumentType
from ..constants.submission_status import SubmissionStatus

# Initialize logger
logger = get_logger(__name__)


class CRUDResult(CRUDBase[Result, ResultCreate, ResultUpdate]):
    """
    CRUD operations for Result model with specialized methods for result workflow management
    """

    def __init__(self):
        """Initialize the CRUDResult class with the Result model"""
        super().__init__(Result)

    def create_result(
        self, 
        obj_in: ResultCreate, 
        db: Optional[Session] = None
    ) -> Result:
        """
        Create a new result with validation

        Args:
            obj_in: ResultCreate schema object
            db: Optional database session

        Returns:
            Result: The created result instance
        """
        db_session_local = db or db_session

        # Directly query Submission model to verify submission exists
        submission = db_session_local.query(Submission).filter(Submission.id == obj_in.submission_id).first()
        if not submission:
            raise ValueError(f"Submission with id {obj_in.submission_id} not found")

        # Create Result instance using Result.create method
        result = Result.create(
            submission_id=obj_in.submission_id,
            uploaded_by=obj_in.uploaded_by,
            protocol_used=obj_in.protocol_used,
            notes=obj_in.notes,
            metadata=obj_in.metadata
        )

        # If properties provided, add each property to result
        if obj_in.properties:
            for prop in obj_in.properties:
                result.add_property(
                    molecule_id=prop.molecule_id,
                    property_name=prop.name,
                    value=prop.value,
                    units=prop.units
                )

        # Add to session and commit
        db_session_local.add(result)
        db_session_local.commit()
        db_session_local.refresh(result)

        logger.info(f"Created new result with ID: {result.id}")
        return result

    def update_result(
        self,
        db_obj: Result,
        obj_in: ResultUpdate,
        db: Optional[Session] = None
    ) -> Result:
        """
        Update an existing result

        Args:
            db_obj: Existing Result instance to update
            obj_in: ResultUpdate schema object
            db: Optional database session

        Returns:
            Result: The updated result instance
        """
        db_session_local = db or db_session

        # Update basic result attributes using parent update method
        updated_result = super().update(db_obj, obj_in, db=db_session_local)

        # If status provided, update result status
        if obj_in.status:
            updated_result.update_status(obj_in.status)

        # If properties provided, add each property to result
        if obj_in.properties:
            for prop in obj_in.properties:
                updated_result.add_property(
                    molecule_id=prop.molecule_id,
                    property_name=prop.name,
                    value=prop.value,
                    units=prop.units
                )

        # Commit changes
        db_session_local.add(updated_result)
        db_session_local.commit()
        db_session_local.refresh(updated_result)

        logger.info(f"Updated result with ID: {updated_result.id}")
        return updated_result

    def get_with_relationships(
        self, 
        result_id: uuid.UUID, 
        db: Optional[Session] = None
    ) -> Optional[Dict[str, Any]]:
        """
        Get a result with all related data (submission, molecules, properties)

        Args:
            result_id: ID of the result to retrieve
            db: Optional database session

        Returns:
            Optional[Dict[str, Any]]: Result data with relationships or None if not found
        """
        db_session_local = db or db_session

        # Get result by ID using parent get method
        result = self.get(result_id, db=db_session_local)
        if not result:
            logger.warning(f"Result with ID {result_id} not found")
            return None

        # Convert result to dictionary with relationships
        result_data = result.to_dict(include_relationships=True)

        logger.debug(f"Retrieved result with relationships: {result_id}")
        return result_data

    def get_by_submission(
        self, 
        submission_id: uuid.UUID, 
        db: Optional[Session] = None, 
        skip: int = 0, 
        limit: int = 100
    ) -> Dict[str, Any]:
        """
        Get results for a specific submission

        Args:
            submission_id: ID of the submission
            db: Optional database session
            skip: Number of records to skip
            limit: Maximum number of records to return

        Returns:
            Dict[str, Any]: Dictionary with results and pagination metadata
        """
        db_session_local = db or db_session

        # Create filter dictionary with submission_id filter
        filter_params = {"submission_id": submission_id}

        # Call self.filter method with filter parameters
        return self.filter(filter_params, db=db_session_local, skip=skip, limit=limit)

    def get_by_uploader(
        self, 
        user_id: uuid.UUID, 
        db: Optional[Session] = None, 
        skip: int = 0, 
        limit: int = 100
    ) -> Dict[str, Any]:
        """
        Get results uploaded by a specific user

        Args:
            user_id: ID of the user
            db: Optional database session
            skip: Number of records to skip
            limit: Maximum number of records to return

        Returns:
            Dict[str, Any]: Dictionary with results and pagination metadata
        """
        db_session_local = db or db_session

        # Create filter dictionary with uploaded_by filter
        filter_params = {"uploaded_by": user_id}

        # Call self.filter method with filter parameters
        return self.filter(filter_params, db=db_session_local, skip=skip, limit=limit)

    def get_by_status(
        self, 
        status_values: List[str], 
        db: Optional[Session] = None, 
        skip: int = 0, 
        limit: int = 100
    ) -> Dict[str, Any]:
        """
        Get results with specific status values

        Args:
            status_values: List of status values to filter by
            db: Optional database session
            skip: Number of records to skip
            limit: Maximum number of records to return

        Returns:
            Dict[str, Any]: Dictionary with results and pagination metadata
        """
        db_session_local = db or db_session

        # Create filter dictionary with status filter
        filter_params = {"status": status_values}

        # Call self.filter method with filter parameters
        return self.filter(filter_params, db=db_session_local, skip=skip, limit=limit)

    def get_by_molecule(
        self, 
        molecule_id: uuid.UUID, 
        db: Optional[Session] = None, 
        skip: int = 0, 
        limit: int = 100
    ) -> Dict[str, Any]:
        """
        Get results that include a specific molecule

        Args:
            molecule_id: ID of the molecule
            db: Optional database session
            skip: Number of records to skip
            limit: Maximum number of records to return

        Returns:
            Dict[str, Any]: Dictionary with results and pagination metadata
        """
        db_session_local = db or db_session

        # Create query joining Result with molecules relationship
        query = db_session_local.query(Result).join(Result.molecules)

        # Filter query by molecule_id
        query = query.filter(Result.molecules.any(id=molecule_id))

        # Apply pagination with skip and limit parameters
        total = query.count()
        items = query.offset(skip).limit(limit).all()

        # Return results with pagination metadata
        return {
            "items": items,
            "total": total,
            "page": skip // limit + 1 if limit > 0 else 1,
            "size": limit,
            "pages": (total + limit - 1) // limit if limit > 0 else 1
        }

    def filter_results(
        self, 
        filter_params: ResultFilter, 
        db: Optional[Session] = None, 
        skip: int = 0, 
        limit: int = 100
    ) -> Dict[str, Any]:
        """
        Filter results based on multiple criteria

        Args:
            filter_params: ResultFilter schema object
            db: Optional database session
            skip: Number of records to skip
            limit: Maximum number of records to return

        Returns:
            Dict[str, Any]: Dictionary with filtered results and pagination metadata
        """
        db_session_local = db or db_session

        # Convert filter_params to dictionary
        filter_dict = filter_params.model_dump(exclude_unset=True)

        # Call self.filter method with constructed filter
        return self.filter(filter_dict, db=db_session_local, skip=skip, limit=limit)

    def update_status(
        self, 
        result_id: uuid.UUID, 
        new_status: str, 
        db: Optional[Session] = None
    ) -> Optional[Result]:
        """
        Update the status of a result

        Args:
            result_id: ID of the result to update
            new_status: New status value
            db: Optional database session

        Returns:
            Optional[Result]: The updated result instance or None if not found
        """
        db_session_local = db or db_session

        # Get result by ID
        result = self.get(result_id, db=db_session_local)
        if not result:
            logger.warning(f"Result with ID {result_id} not found")
            return None

        # Call result.update_status method with new_status
        success = result.update_status(new_status)
        if not success:
            logger.warning(f"Failed to update status for result {result_id} to {new_status}")
            return None

        # Commit changes
        db_session_local.add(result)
        db_session_local.commit()
        db_session_local.refresh(result)

        logger.info(f"Updated status for result {result_id} to {new_status}")
        return result

    def add_property(
        self, 
        result_id: uuid.UUID, 
        molecule_id: uuid.UUID, 
        property_name: str, 
        value: float, 
        units: Optional[str] = None, 
        db: Optional[Session] = None
    ) -> bool:
        """
        Add a property to a result

        Args:
            result_id: ID of the result
            molecule_id: ID of the molecule
            property_name: Name of the property
            value: Value of the property
            units: Optional units for the property
            db: Optional database session

        Returns:
            bool: True if property was added, False if already exists
        """
        db_session_local = db or db_session

        # Get result by ID
        result = self.get(result_id, db=db_session_local)
        if not result:
            logger.warning(f"Result with ID {result_id} not found")
            return False
        
        # Validate molecule exists
        if not molecule.get(molecule_id, db=db_session_local):
            logger.warning(f"Molecule with ID {molecule_id} not found")
            return False

        # Call result.add_property method with parameters
        success = result.add_property(
            molecule_id=molecule_id,
            property_name=property_name,
            value=value,
            units=units
        )
        if not success:
            logger.warning(f"Failed to add property {property_name} to result {result_id}")
            return False

        # Commit changes
        db_session_local.add(result)
        db_session_local.commit()
        db_session_local.refresh(result)

        logger.info(f"Added property {property_name} to result {result_id}")
        return True

    def process_result(
        self, 
        process_data: ResultProcessRequest, 
        db: Optional[Session] = None
    ) -> Dict[str, Any]:
        """
        Process a result and mark it as processed

        Args:
            process_data: ResultProcessRequest schema object
            db: Optional database session

        Returns:
            Dict[str, Any]: Result with success flag and message
        """
        db_session_local = db or db_session

        # Get result by ID from process_data.result_id
        result = self.get(process_data.result_id, db=db_session_local)
        if not result:
            logger.warning(f"Result with ID {process_data.result_id} not found")
            return {"success": False, "message": f"Result with ID {process_data.result_id} not found"}

        # Call result.mark_as_processed with quality_control_passed
        success = result.mark_as_processed(process_data.quality_control_passed)
        if not success:
            logger.warning(f"Failed to process result {process_data.result_id}")
            return {"success": False, "message": f"Failed to process result {process_data.result_id}"}

        # Commit changes
        db_session_local.add(result)
        db_session_local.commit()
        db_session_local.refresh(result)

        logger.info(f"Processed result with ID {process_data.result_id}")
        return {"success": True, "message": f"Result {process_data.result_id} processed successfully"}

    def review_result(
        self, 
        review_data: ResultReviewRequest, 
        db: Optional[Session] = None
    ) -> Dict[str, Any]:
        """
        Review a result and apply to molecules

        Args:
            review_data: ResultReviewRequest schema object
            db: Optional database session

        Returns:
            Dict[str, Any]: Result with success flag and message
        """
        db_session_local = db or db_session

        # Get result by ID from review_data.result_id
        result = self.get(review_data.result_id, db=db_session_local)
        if not result:
            logger.warning(f"Result with ID {review_data.result_id} not found")
            return {"success": False, "message": f"Result with ID {review_data.result_id} not found"}

        # Call result.mark_as_reviewed
        success = result.mark_as_reviewed()
        if not success:
            logger.warning(f"Failed to review result {review_data.result_id}")
            return {"success": False, "message": f"Failed to review result {review_data.result_id}"}
        
        # Get associated submission directly from the database
        submission = db_session_local.query(Submission).filter(Submission.id == result.submission_id).first()
        if submission:
            # Update submission status to RESULTS_REVIEWED using Submission.update_status
            submission.update_status(SubmissionStatus.RESULTS_REVIEWED.value)
            db_session_local.add(submission)

        # Commit changes
        db_session_local.add(result)
        db_session_local.commit()
        db_session_local.refresh(result)

        logger.info(f"Reviewed result with ID {review_data.result_id}")
        return {"success": True, "message": f"Result {review_data.result_id} reviewed successfully"}

    def reject_result(
        self, 
        result_id: uuid.UUID, 
        rejection_reason: str, 
        db: Optional[Session] = None
    ) -> Dict[str, Any]:
        """
        Reject a result

        Args:
            result_id: ID of the result to reject
            rejection_reason: Reason for rejection
            db: Optional database session

        Returns:
            Dict[str, Any]: Result with success flag and message
        """
        db_session_local = db or db_session

        # Get result by ID
        result = self.get(result_id, db=db_session_local)
        if not result:
            logger.warning(f"Result with ID {result_id} not found")
            return {"success": False, "message": f"Result with ID {result_id} not found"}

        # Call result.reject method with rejection_reason
        success = result.reject(rejection_reason)
        if not success:
            logger.warning(f"Failed to reject result {result_id}")
            return {"success": False, "message": f"Failed to reject result {result_id}"}

        # Commit changes
        db_session_local.add(result)
        db_session_local.commit()
        db_session_local.refresh(result)

        logger.info(f"Rejected result with ID {result_id}")
        return {"success": True, "message": f"Result {result_id} rejected successfully"}

    def apply_to_molecules(
        self, 
        result_id: uuid.UUID, 
        db: Optional[Session] = None
    ) -> Dict[str, Any]:
        """
        Apply result properties to molecules

        Args:
            result_id: ID of the result
            db: Optional database session

        Returns:
            Dict[str, Any]: Result with success flag, message, and count of updated molecules
        """
        db_session_local = db or db_session

        # Get result by ID
        result = self.get(result_id, db=db_session_local)
        if not result:
            logger.warning(f"Result with ID {result_id} not found")
            return {"success": False, "message": f"Result with ID {result_id} not found"}

        # Call result.apply_to_molecules method
        count = result.apply_to_molecules()

        # Commit changes
        db_session_local.add(result)
        db_session_local.commit()
        db_session_local.refresh(result)

        logger.info(f"Applied result {result_id} to {count} molecules")
        return {"success": True, "message": f"Result {result_id} applied to {count} molecules", "count": count}

    def import_from_csv(
        self,
        result_id: uuid.UUID,
        csv_file: io.BytesIO,
        column_mapping: Dict[str, str],
        has_header: bool,
        delimiter: str,
        db: Optional[Session] = None
    ) -> Dict[str, Any]:
        """
        Import result data from CSV file

        Args:
            result_id: ID of the result
            csv_file: CSV file as BytesIO object
            column_mapping: Mapping of CSV columns to result properties
            has_header: Whether the CSV file has a header row
            delimiter: Delimiter character
            db: Optional database session

        Returns:
            Dict[str, Any]: Import summary with success count, error count, and errors
        """
        db_session_local = db or db_session

        # Get result by ID
        result = self.get(result_id, db=db_session_local)
        if not result:
            logger.warning(f"Result with ID {result_id} not found")
            return {"success": False, "message": f"Result with ID {result_id} not found"}

        # Validate column_mapping contains required fields
        if 'molecule_id' not in column_mapping.values():
            logger.error("Column mapping must include a column mapped to 'molecule_id'")
            return {"success": False, "message": "Column mapping must include a column mapped to 'molecule_id'"}

        # Track successful imports and errors
        success_count = 0
        error_count = 0
        errors = []

        try:
            # Parse CSV file using csv module
            csv_reader = csv.DictReader(io.TextIOWrapper(csv_file, encoding='utf-8'), delimiter=delimiter)

            # Skip header row if has_header is True
            if has_header:
                next(csv_reader)

            # For each row in CSV:
            for row in csv_reader:
                try:
                    # Extract molecule_id from mapped column
                    molecule_id_column = next((col for col, mapped in column_mapping.items() if mapped == 'molecule_id'), None)
                    if not molecule_id_column:
                        raise ValueError("No column mapped to molecule_id")
                    molecule_id = row[molecule_id_column]

                    # Validate molecule exists
                    if not molecule.get(molecule_id, db=db_session_local):
                        raise ValueError(f"Molecule with ID {molecule_id} not found")

                    # For each property column in mapping:
                    for csv_col, property_name in column_mapping.items():
                        if property_name != 'molecule_id':
                            # Extract property name and value
                            property_value = row[csv_col]

                            # Add property to result
                            result.add_property(
                                molecule_id=uuid.UUID(molecule_id),
                                property_name=property_name,
                                value=float(property_value),
                                units=None  # Units would need to be extracted from CSV if available
                            )

                    success_count += 1
                except Exception as e:
                    error_count += 1
                    errors.append(f"Error processing row: {str(e)}")

            # Commit session to save changes
            db_session_local.add(result)
            db_session_local.commit()
            db_session_local.refresh(result)

            logger.info(f"Imported {success_count} rows from CSV for result {result_id} with {error_count} errors")
            return {"success": True, "message": f"Imported {success_count} rows with {error_count} errors", "success_count": success_count, "error_count": error_count, "errors": errors}

        except Exception as e:
            db_session_local.rollback()
            logger.error(f"Failed to import from CSV: {str(e)}")
            return {"success": False, "message": f"Failed to import from CSV: {str(e)}", "success_count": success_count, "error_count": error_count, "errors": errors}

    def create_result_document(
        self,
        result_id: uuid.UUID,
        document_type: str,
        file_name: str,
        file_url: str,
        uploaded_by: uuid.UUID,
        db: Optional[Session] = None
    ) -> Dict[str, Any]:
        """
        Create a document associated with a result

        Args:
            result_id: ID of the result
            document_type: Type of document (RESULTS_REPORT or QUALITY_CONTROL)
            file_name: Name of the file
            file_url: URL of the file
            uploaded_by: ID of the user uploading the document
            db: Optional database session

        Returns:
            Dict[str, Any]: Created document data or error
        """
        db_session_local = db or db_session

        # Get result by ID
        result = self.get(result_id, db=db_session_local)
        if not result:
            logger.warning(f"Result with ID {result_id} not found")
            return {"success": False, "message": f"Result with ID {result_id} not found"}

        # Validate document_type is valid for results (RESULTS_REPORT or QUALITY_CONTROL)
        if document_type not in [DocumentType.RESULTS_REPORT.name, DocumentType.QUALITY_CONTROL.name]:
            logger.warning(f"Invalid document type {document_type} for result {result_id}")
            return {"success": False, "message": f"Invalid document type {document_type} for result {result_id}"}

        try:
            # Create document using document.create with result's submission_id
            doc_data = {
                "name": file_name,
                "type": DocumentType[document_type],
                "submission_id": result.submission_id,
                "uploaded_by": uploaded_by,
                "url": file_url,
                "signature_required": False,
                "status": "UPLOADED"
            }
            new_document = document.create(doc_data, db=db_session_local)

            # Commit changes
            db_session_local.add(new_document)
            db_session_local.commit()
            db_session_local.refresh(new_document)

            logger.info(f"Created document {new_document.id} for result {result_id}")
            return {"success": True, "message": f"Created document {new_document.id} for result {result_id}", "document": new_document.to_dict()}

        except Exception as e:
            db_session_local.rollback()
            logger.error(f"Failed to create document for result {result_id}: {str(e)}")
            return {"success": False, "message": f"Failed to create document for result {result_id}: {str(e)}"}

    def get_result_statistics(
        self,
        submission_id: Optional[uuid.UUID] = None,
        db: Optional[Session] = None
    ) -> Dict[str, Any]:
        """
        Get statistics about results

        Args:
            submission_id: Optional ID of the submission to filter by
            db: Optional database session

        Returns:
            Dict[str, Any]: Statistics about results
        """
        db_session_local = db or db_session

        # Create query to count results grouped by status
        query = db_session_local.query(Result.status, func.count(Result.id))

        # If submission_id provided, filter by submission_id
        if submission_id:
            query = query.filter(Result.submission_id == submission_id)

        # Group by status
        query = query.group_by(Result.status)

        # Execute query and format results
        results = query.all()
        status_counts = {status: count for status, count in results}

        # Get additional statistics (avg processing time, property counts)
        total_results = sum(status_counts.values())
        # avg_processing_time = self.calculate_average_processing_time(submission_id, db=db_session_local) # TODO: Implement this
        # avg_property_count = self.calculate_average_property_count(submission_id, db=db_session_local) # TODO: Implement this

        # Return dictionary with statistics
        return {
            "total_results": total_results,
            "status_counts": status_counts,
            # "avg_processing_time": avg_processing_time,
            # "avg_property_count": avg_property_count
        }

    def update_submission_status(
        self,
        submission_id: uuid.UUID,
        new_status: str,
        db: Optional[Session] = None
    ) -> bool:
        """
        Update the status of a submission associated with a result

        Args:
            submission_id: ID of the submission to update
            new_status: New status value
            db: Optional database session

        Returns:
            bool: True if status was updated, False if submission not found
        """
        db_session_local = db or db_session

        # Query database directly to get Submission by ID
        submission = db_session_local.query(Submission).filter(Submission.id == submission_id).first()
        if not submission:
            logger.warning(f"Submission with ID {submission_id} not found")
            return False

        # Update submission status using Submission.update_status method
        success = submission.update_status(new_status)
        if not success:
            logger.warning(f"Failed to update status for submission {submission_id} to {new_status}")
            return False

        # Commit changes
        db_session_local.add(submission)
        db_session_local.commit()
        db_session_local.refresh(submission)

        logger.info(f"Updated status for submission {submission_id} to {new_status}")
        return True


# Create a singleton instance
result = CRUDResult()