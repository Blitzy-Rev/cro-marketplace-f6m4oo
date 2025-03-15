from typing import List, Dict, Any, Optional, Union
import uuid
import os
import tempfile

from fastapi import APIRouter, Depends, HTTPException, status, File, UploadFile, Form, Query, Path, Body, BackgroundTasks
from sqlalchemy.orm import Session

# Internal imports
from ...db.session import get_db
from ..deps import get_current_user, get_current_pharma_user, get_molecule_access, User
from ...schemas.molecule import MoleculeCreate, MoleculeUpdate, Molecule, MoleculeDetail, MoleculeFilter, MoleculeBulkOperation, MoleculeCSVMapping
from ...services.molecule_service import molecule_service
from ...services.storage_service import storage_service
from ...core.exceptions import MoleculeException, CSVException
from ...core.logging import get_logger

# Initialize logger
logger = get_logger(__name__)

# Define API router
router = APIRouter(prefix="/molecules", tags=["molecules"])

@router.post("/", response_model=Molecule, status_code=status.HTTP_201_CREATED)
def create_molecule(
    molecule_data: MoleculeCreate,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
) -> Molecule:
    """
    Create a new molecule from SMILES string
    """
    logger.info(f"Attempting to create molecule with SMILES: {molecule_data.smiles[:50]}...")
    try:
        # Set created_by to current_user.id if not provided
        if not molecule_data.created_by:
            molecule_data.created_by = current_user.id

        # Call molecule_service.create_molecule with SMILES and properties
        molecule = molecule_service.create_molecule(
            smiles=molecule_data.smiles,
            created_by=molecule_data.created_by,
            properties=molecule_data.properties,
            db=db
        )

        logger.info(f"Molecule created successfully with ID: {molecule['id']}")
        return Molecule(**molecule)
    except MoleculeException as e:
        logger.error(f"Error creating molecule: {e}")
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(e)
        )

@router.get("/{molecule_id}", response_model=MoleculeDetail)
def get_molecule(
    molecule_id: uuid.UUID,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
) -> MoleculeDetail:
    """
    Get a molecule by ID
    """
    logger.info(f"Attempting to retrieve molecule with ID: {molecule_id}")
    try:
        # Call molecule_service.get_molecule with molecule_id
        molecule = molecule_service.get_molecule(molecule_id=molecule_id, db=db)

        # If molecule not found, raise 404 HTTPException
        if not molecule:
            logger.warning(f"Molecule with ID {molecule_id} not found")
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Molecule not found"
            )

        # Return molecule data
        logger.info(f"Molecule {molecule_id} retrieved successfully")
        return MoleculeDetail(**molecule)
    except MoleculeException as e:
        logger.error(f"Error retrieving molecule: {e}")
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(e)
        )

@router.get("/by-smiles/", response_model=Molecule)
def get_molecule_by_smiles(
    smiles: str,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
) -> Molecule:
    """
    Get a molecule by SMILES string
    """
    logger.info(f"Attempting to retrieve molecule with SMILES: {smiles[:50]}...")
    try:
        # Call molecule_service.get_molecule_by_smiles with smiles
        molecule = molecule_service.get_molecule_by_smiles(smiles=smiles, db=db)

        # If molecule not found, raise 404 HTTPException
        if not molecule:
            logger.warning(f"Molecule with SMILES {smiles[:50]}... not found")
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Molecule not found"
            )

        # Return molecule data
        logger.info(f"Molecule with SMILES {smiles[:50]}... retrieved successfully")
        return Molecule(**molecule)
    except MoleculeException as e:
        logger.error(f"Error retrieving molecule by SMILES: {e}")
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(e)
        )

@router.post("/filter/", response_model=Dict[str, Any])
def filter_molecules(
    filter_params: MoleculeFilter,
    skip: int = 0,
    limit: int = 100,
    sort_by: Optional[str] = None,
    descending: bool = False,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
) -> Dict[str, Any]:
    """
    Filter molecules based on various criteria
    """
    logger.info(f"Attempting to filter molecules with parameters: {filter_params}")
    try:
        # Convert filter_params to dictionary
        filter_dict = filter_params.model_dump(exclude_unset=True)

        # Call molecule_service.filter_molecules with parameters
        filtered_molecules = molecule_service.filter_molecules(
            filter_params=filter_dict,
            skip=skip,
            limit=limit,
            sort_by=sort_by,
            descending=descending,
            db=db
        )

        # Return filtered molecules with pagination info
        logger.info(f"Successfully filtered molecules, returning {filtered_molecules['total']} results")
        return filtered_molecules
    except MoleculeException as e:
        logger.error(f"Error filtering molecules: {e}")
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(e)
        )

@router.post("/upload-csv/", status_code=status.HTTP_202_ACCEPTED)
async def upload_csv(
    file: UploadFile = File(...),
    current_user: User = Depends(get_current_user),
    background_tasks: BackgroundTasks = Depends(),
    db: Session = Depends(get_db)
) -> Dict[str, Any]:
    """
    Upload a CSV file containing molecular data
    """
    logger.info(f"Attempting to upload CSV file: {file.filename}")
    try:
        # Validate file is provided and is a CSV
        if not file:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="No file provided"
            )
        if file.content_type not in ["text/csv", "application/vnd.ms-excel"]:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Invalid file type. Only CSV files are allowed."
            )

        # Create temporary file for processing
        suffix = os.path.splitext(file.filename)[1]
        with tempfile.NamedTemporaryFile(delete=False, suffix=suffix) as temp_file:
            # Save uploaded file content to temporary file
            content = await file.read()
            temp_file.write(content)
            temp_file_path = temp_file.name

        # Store CSV file in storage service
        file_url = storage_service.store_csv_file(
            file_content=content,
            filename=file.filename
        )

        # Add background task for processing CSV file
        background_tasks.add_task(process_csv_background, file_url, current_user.id)

        # Return upload status with file information
        logger.info(f"CSV file {file.filename} uploaded successfully, processing in background")
        return {
            "filename": file.filename,
            "file_url": file_url,
            "message": "CSV file uploaded successfully, processing in background"
        }
    except Exception as e:
        logger.error(f"Error uploading CSV file: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=str(e)
        )

@router.post("/process-csv/", status_code=status.HTTP_200_OK)
async def process_csv(
    file_url: str = Form(...),
    mapping: MoleculeCSVMapping = Depends(),
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
) -> Dict[str, Any]:
    """
    Process a previously uploaded CSV file
    """
    logger.info(f"Attempting to process CSV file from URL: {file_url}")
    try:
        # Download CSV file from storage
        file_content = storage_service.retrieve_file(file_url)

        # Create temporary file for processing
        with tempfile.NamedTemporaryFile(delete=False, suffix=".csv") as temp_file:
            # Write downloaded content to temporary file
            temp_file.write(file_content)
            temp_file_path = temp_file.name

        # Call molecule_service.process_csv_file with file path and mapping
        processing_results = molecule_service.process_csv_file(
            file_path=temp_file_path,
            column_mapping=mapping.column_mapping,
            created_by=current_user.id,
            db=db
        )

        # Return processing results with statistics
        logger.info(f"CSV file processed successfully, results: {processing_results}")
        return processing_results
    except Exception as e:
        logger.error(f"Error processing CSV file: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=str(e)
        )

@router.get("/csv-preview/", status_code=status.HTTP_200_OK)
async def get_csv_preview(
    file_url: str = Query(...),
    num_rows: int = Query(5, le=20),
    current_user: User = Depends(get_current_user)
) -> Dict[str, Any]:
    """
    Get a preview of CSV data for column mapping
    """
    logger.info(f"Attempting to get CSV preview from URL: {file_url}")
    try:
        # Download CSV file from storage
        file_content = storage_service.retrieve_file(file_url)

        # Create temporary file for processing
        with tempfile.NamedTemporaryFile(delete=False, suffix=".csv") as temp_file:
            # Write downloaded content to temporary file
            temp_file.write(file_content)
            temp_file_path = temp_file.name

        # Call molecule_service.get_csv_preview with file path and num_rows
        preview_data = molecule_service.get_csv_preview(
            file_path=temp_file_path,
            num_rows=num_rows
        )

        # Return preview data with headers and sample rows
        logger.info(f"CSV preview generated successfully")
        return preview_data
    except Exception as e:
        logger.error(f"Error getting CSV preview: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=str(e)
        )

@router.post("/{molecule_id}/predict/", status_code=status.HTTP_200_OK)
def predict_properties(
    molecule_id: uuid.UUID,
    properties: Optional[List[str]] = Query(None),
    wait_for_results: bool = Query(True),
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
) -> Dict[str, Any]:
    """
    Request property predictions from AI engine for a molecule
    """
    logger.info(f"Attempting to predict properties for molecule ID: {molecule_id}")
    try:
        # Call molecule_service.predict_properties with parameters
        prediction_results = molecule_service.predict_properties(
            molecule_id=molecule_id,
            properties=properties,
            wait_for_results=wait_for_results,
            db=db
        )

        # Return prediction results or job information
        logger.info(f"Prediction request submitted successfully for molecule {molecule_id}")
        return prediction_results
    except MoleculeException as e:
        logger.error(f"Error predicting properties: {e}")
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(e)
        )

@router.post("/batch-predict/", status_code=status.HTTP_202_ACCEPTED)
def batch_predict_properties(
    molecule_ids: List[uuid.UUID] = Body(...),
    properties: Optional[List[str]] = Query(None),
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
) -> Dict[str, Any]:
    """
    Request property predictions for multiple molecules
    """
    logger.info(f"Attempting to batch predict properties for {len(molecule_ids)} molecules")
    try:
        # Call molecule_service.batch_predict_properties with parameters
        batch_prediction_info = molecule_service.batch_predict_properties(
            molecule_ids=molecule_ids,
            properties=properties,
            db=db
        )

        # Return batch prediction job information
        logger.info(f"Batch prediction request submitted successfully, batch ID: {batch_prediction_info['batch_id']}")
        return batch_prediction_info
    except MoleculeException as e:
        logger.error(f"Error submitting batch prediction: {e}")
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(e)
        )

@router.post("/bulk-operation/", status_code=status.HTTP_200_OK)
def bulk_operation(
    operation_data: MoleculeBulkOperation,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
) -> Dict[str, Any]:
    """
    Perform bulk operations on multiple molecules
    """
    logger.info(f"Attempting bulk operation: {operation_data.operation} for {len(operation_data.molecule_ids)} molecules")
    try:
        # Call molecule_service.bulk_operation with parameters
        operation_results = molecule_service.bulk_operation(
            molecule_ids=operation_data.molecule_ids,
            operation=operation_data.operation,
            parameters=operation_data.parameters,
            db=db
        )

        # Return operation results with statistics
        logger.info(f"Bulk operation completed successfully, results: {operation_results}")
        return operation_results
    except MoleculeException as e:
        logger.error(f"Error performing bulk operation: {e}")
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(e)
        )

def process_csv_background(file_url: str, user_id: uuid.UUID):
    """
    Background task for processing CSV files
    """
    db_session = get_db().__next__()
    try:
        logger.info(f"Starting background processing for CSV file: {file_url}")
        # Call molecule_service.process_csv_file with default column mapping
        processing_results = molecule_service.process_csv_file(
            file_path=file_url,
            column_mapping={},  # Default column mapping
            created_by=user_id,
            db=db_session
        )

        # Log processing results
        logger.info(f"Background processing completed for CSV file: {file_url}, results: {processing_results}")
    except Exception as e:
        logger.error(f"Error in background processing for CSV file: {file_url}, error: {e}")
    finally:
        db_session.close()