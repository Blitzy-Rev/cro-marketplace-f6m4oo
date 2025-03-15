"""
Implements asynchronous tasks for processing experimental results from Contract Research Organizations (CROs) in the Molecular Data Management and CRO Integration Platform.
This module handles the validation, processing, and integration of result data with molecules, including CSV result imports and notification of result availability.
"""

from typing import Dict, List, Optional, Any
from uuid import UUID
import io

import pandas  # pandas ^1.5.0

from .celery_app import celery_app  # celery ^5.2.0
from ..core.logging import get_logger
from ..db.session import db_session
from ..models.result import Result, ResultStatus
from ..crud.crud_result import result
from ..services.result_service import ResultService
from ..utils.csv_parser import CSVProcessor
from ..integrations.aws.s3 import S3Client
from .notification import notify_results_available
from ..constants.molecule_properties import PropertySource

# Initialize logger
logger = get_logger(__name__)

# Initialize S3 client
s3_client = S3Client()

# Initialize ResultService
result_service = ResultService()


@celery_app.task(name='tasks.process_result', queue='result_processing')
def process_result(
    result_id: UUID,
    quality_control_passed: bool,
    metadata: Optional[Dict[str, Any]] = None
) -> Dict[str, Any]:
    """
    Process a result by validating and integrating the data

    Args:
        result_id: UUID of the result
        quality_control_passed: Whether the quality control checks passed
        metadata: Optional metadata for the result

    Returns:
        Processing result with success flag and message
    """
    logger.info(f"Processing result task started for result_id: {result_id}")

    session = db_session()
    try:
        # Retrieve result by ID
        db_result = result.get(result_id, db=session)

        if not db_result:
            logger.error(f"Result not found with ID: {result_id}")
            return {"success": False, "message": f"Result not found with ID: {result_id}"}

        # Update result status to PROCESSING
        if db_result.status != ResultStatus.PENDING.value:
            logger.warning(f"Result {result_id} is not in PENDING state, skipping processing.")
            return {"success": False, "message": f"Result {result_id} is not in PENDING state, skipping processing."}

        db_result.update_status(ResultStatus.PROCESSING.value)
        session.add(db_result)
        session.commit()

        # Try to process result with quality_control_passed flag
        try:
            process_data = {"result_id": result_id, "quality_control_passed": quality_control_passed}
            processing_result = result.process_result(process_data, db=session)

            if processing_result["success"]:
                # Update result status to COMPLETED
                db_result.update_status(ResultStatus.COMPLETED.value)
                session.add(db_result)
                session.commit()

                # If quality_control_passed is True, trigger notification for results availability
                if quality_control_passed:
                    notify_results_available.delay(submission_id=db_result.submission_id, result_id=result_id)
            else:
                # Update result status to FAILED
                db_result.update_status(ResultStatus.FAILED.value)
                session.add(db_result)
                session.commit()
                logger.error(f"Result processing failed for result_id: {result_id}. Error: {processing_result['message']}")
                return {"success": False, "message": f"Result processing failed: {processing_result['message']}"}

        except Exception as e:
            # Update result status to FAILED
            db_result.update_status(ResultStatus.FAILED.value)
            session.add(db_result)
            session.commit()
            logger.error(f"Result processing failed with exception for result_id: {result_id}. Error: {str(e)}", exc_info=True)
            return {"success": False, "message": f"Result processing failed with exception: {str(e)}"}

    finally:
        session.close()

    logger.info(f"Processing result task completed for result_id: {result_id}")
    return {"success": True, "message": f"Result processed successfully"}


@celery_app.task(name='tasks.apply_result_to_molecules', queue='result_processing')
def apply_result_to_molecules(result_id: UUID) -> Dict[str, Any]:
    """
    Apply result properties to associated molecules

    Args:
        result_id: UUID of the result

    Returns:
        Application result with success flag, message, and count
    """
    logger.info(f"Applying result to molecules task started for result_id: {result_id}")

    session = db_session()
    try:
        # Retrieve result by ID
        db_result = result.get(result_id, db=session)

        if not db_result:
            logger.error(f"Result not found with ID: {result_id}")
            return {"success": False, "message": f"Result not found with ID: {result_id}"}

        # Check if result status is COMPLETED
        if db_result.status != ResultStatus.COMPLETED.value:
            logger.error(f"Result is not in COMPLETED state, skipping application to molecules. Current status: {db_result.status}")
            return {"success": False, "message": f"Result is not in COMPLETED state, skipping application to molecules. Current status: {db_result.status}"}

        # Apply result properties to molecules using Result.apply_to_molecules
        count = db_result.apply_to_molecules()

        # Commit changes
        session.add(db_result)
        session.commit()

        logger.info(f"Applied result to molecules task completed for result_id: {result_id}. Updated {count} molecules.")
        return {"success": True, "message": f"Result applied to {count} molecules", "count": count}

    finally:
        session.close()


@celery_app.task(name='tasks.import_result_from_csv', queue='result_processing')
def import_result_from_csv(result_id: UUID, file_key: str, column_mapping: Dict[str, str]) -> Dict[str, Any]:
    """
    Import result data from a CSV file stored in S3

    Args:
        result_id: UUID of the result
        file_key: S3 key of the CSV file
        column_mapping: Mapping of CSV columns to result properties

    Returns:
        Import summary with success count, error count, and errors
    """
    logger.info(f"Import result from CSV task started for result_id: {result_id}, file_key: {file_key}")

    session = db_session()
    try:
        # Retrieve result by ID
        db_result = result.get(result_id, db=session)

        if not db_result:
            logger.error(f"Result not found with ID: {result_id}")
            return {"success": False, "message": f"Result not found with ID: {result_id}"}

        # Update result status to PROCESSING
        db_result.update_status(ResultStatus.PROCESSING.value)
        session.add(db_result)
        session.commit()

        # Download CSV file from S3 using file_key
        try:
            file_content = s3_client.download(file_key)
            csv_file = io.BytesIO(file_content)
        except Exception as e:
            db_result.update_status(ResultStatus.FAILED.value)
            session.add(db_result)
            session.commit()
            logger.error(f"Failed to download CSV file from S3: {str(e)}", exc_info=True)
            return {"success": False, "message": f"Failed to download CSV file from S3: {str(e)}"}

        # Create CSVProcessor instance with downloaded file
        try:
            csv_processor = CSVProcessor(file_path=file_key)
            csv_processor.load_csv()
            csv_processor.set_column_mapping(column_mapping)
            csv_processor.process()
            valid_molecules = csv_processor.get_valid_molecules()
            invalid_rows = csv_processor.get_invalid_rows()
            summary = csv_processor.get_summary()

            # Import valid data into result properties
            for index, row in valid_molecules.iterrows():
                for property_name, property_value in row.items():
                    if property_name != 'molecule_id':
                        db_result.add_property(
                            molecule_id=row['molecule_id'],
                            property_name=property_name,
                            value=property_value,
                            units=None  # Units would need to be extracted from CSV if available
                        )

            # Update result metadata with import summary
            db_result.metadata = {
                "total_rows": summary['total_rows'],
                "valid_rows": summary['valid_rows'],
                "invalid_rows": summary['invalid_rows'],
                "invalid_percentage": summary['invalid_percentage'],
                "mapped_columns": summary['mapped_columns']
            }
            session.add(db_result)
            session.commit()

            # Update result status to COMPLETED
            db_result.update_status(ResultStatus.COMPLETED.value)
            session.add(db_result)
            session.commit()

            logger.info(f"Import from CSV task completed for result_id: {result_id}. Imported {summary['valid_rows']} rows with {summary['invalid_rows']} errors.")
            return {"success": True, "message": f"Imported {summary['valid_rows']} rows with {summary['invalid_rows']} errors", "success_count": summary['valid_rows'], "error_count": summary['invalid_rows'], "errors": invalid_rows}

        except Exception as e:
            db_result.update_status(ResultStatus.FAILED.value)
            session.add(db_result)
            session.commit()
            logger.error(f"Failed to process CSV file: {str(e)}", exc_info=True)
            return {"success": False, "message": f"Failed to process CSV file: {str(e)}"}

    finally:
        session.close()


@celery_app.task(name='tasks.validate_result_data', queue='result_processing')
def validate_result_data(result_id: UUID, validation_rules: Dict[str, Any]) -> Dict[str, Any]:
    """
    Validate result data against expected format and value ranges

    Args:
        result_id: UUID of the result
        validation_rules: Dictionary of validation rules

    Returns:
        Validation result with success flag and errors
    """
    logger.info(f"Validating result data task started for result_id: {result_id}")

    session = db_session()
    try:
        # Retrieve result by ID with properties
        db_result = result.get_with_relationships(result_id, db=session)

        if not db_result:
            logger.error(f"Result not found with ID: {result_id}")
            return {"success": False, "message": f"Result not found with ID: {result_id}"}

        # Initialize empty errors list
        errors = []

        # For each property in result, validate against rules
        for prop in db_result['properties']:
            # Check for required properties
            if 'required' in validation_rules and prop['name'] in validation_rules['required']:
                if not prop['value']:
                    errors.append({"field": prop['name'], "message": "Required property is missing"})

            # Check value ranges for numeric properties
            if 'numeric_ranges' in validation_rules and prop['name'] in validation_rules['numeric_ranges']:
                range_rules = validation_rules['numeric_ranges'][prop['name']]
                if 'min' in range_rules and prop['value'] < range_rules['min']:
                    errors.append({"field": prop['name'], "message": f"Value is below minimum: {range_rules['min']}"})
                if 'max' in range_rules and prop['value'] > range_rules['max']:
                    errors.append({"field": prop['name'], "message": f"Value is above maximum: {range_rules['max']}"})

            # Check for unexpected outliers in data
            if 'outlier_detection' in validation_rules:
                # Implement outlier detection logic here
                pass

        # If validation errors found, log details
        if errors:
            logger.warning(f"Validation errors found for result_id: {result_id}. Errors: {errors}")

    finally:
        session.close()

    logger.info(f"Validating result data task completed for result_id: {result_id}. Found {len(errors)} errors.")
    return {"success": not errors, "message": f"Validation completed with {len(errors)} errors", "errors": errors}


@celery_app.task(name='tasks.cleanup_result_processing', queue='result_processing')
def cleanup_result_processing(result_id: UUID) -> Dict[str, Any]:
    """
    Clean up temporary files and resources after result processing

    Args:
        result_id: UUID of the result

    Returns:
        Cleanup result with success flag
    """
    logger.info(f"Cleaning up result processing task started for result_id: {result_id}")

    session = db_session()
    try:
        # Retrieve result by ID
        db_result = result.get(result_id, db=session)

        if not db_result:
            logger.error(f"Result not found with ID: {result_id}")
            return {"success": False, "message": f"Result not found with ID: {result_id}"}

        # Remove any temporary files created during processing
        # Implement file removal logic here

        # Update result metadata to indicate cleanup completed
        db_result.metadata = db_result.metadata or {}
        db_result.metadata['cleanup_completed'] = True
        session.add(db_result)
        session.commit()

    finally:
        session.close()

    logger.info(f"Cleaning up result processing task completed for result_id: {result_id}")
    return {"success": True, "message": "Cleanup completed successfully"}