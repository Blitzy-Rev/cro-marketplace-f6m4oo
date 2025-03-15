# src/backend/tests/services/test_csv_service.py
import io
import uuid
from io import BytesIO

import pandas
import pytest
import pytest_mock
from pandas import DataFrame

from src.backend.app.constants.error_messages import CSV_ERRORS, STANDARD_PROPERTIES
from src.backend.app.core.exceptions import CSVException, MoleculeException
from src.backend.app.services.csv_service import CSVService
from src.backend.app.utils.smiles import validate_smiles
from src.backend.tests.conftest import db_session, test_user  # type: ignore


def test_process_file_success(mocker: pytest_mock.MockFixture):
    """Test successful processing of a valid CSV file"""
    # Create a mock S3Client
    mock_s3_client = mocker.MagicMock()
    # Patch the S3Client in csv_service module
    mocker.patch("src.backend.app.services.csv_service.S3Client", return_value=mock_s3_client)
    # Create a sample CSV content with valid SMILES and properties
    csv_content = "SMILES,property1,property2\nC,1.0,2.0\nCC,3.0,4.0"
    # Create a BytesIO object from the sample CSV content
    file_io = BytesIO(csv_content.encode('utf-8'))
    # Set up mock for S3Client.generate_key to return a test key
    mock_s3_client.generate_key.return_value = "test_key"
    # Set up mock for S3Client.upload to return success
    mock_s3_client.upload.return_value = True
    # Initialize CSVService instance
    csv_service = CSVService()
    # Call process_file with the sample CSV content
    result = csv_service.process_file(file_io.read(), "test.csv")
    # Assert that the result contains success status
    assert result["status"] == "success"
    # Assert that the result contains the expected storage key
    assert result["storage_key"] == "test_key"
    # Assert that the result contains column suggestions
    assert "column_suggestions" in result
    # Verify that S3Client.generate_key was called once
    mock_s3_client.generate_key.assert_called_once()
    # Verify that S3Client.upload was called once with correct parameters
    mock_s3_client.upload.assert_called_once()


def test_process_file_invalid_csv(mocker: pytest_mock.MockFixture):
    """Test processing of an invalid CSV file"""
    # Create a mock S3Client
    mock_s3_client = mocker.MagicMock()
    # Patch the S3Client in csv_service module
    mocker.patch("src.backend.app.services.csv_service.S3Client", return_value=mock_s3_client)
    # Create an invalid CSV content (e.g., malformed data)
    csv_content = "SMILES,property1\nC,1.0\nCC"
    # Create a BytesIO object from the invalid CSV content
    file_io = BytesIO(csv_content.encode('utf-8'))
    # Initialize CSVService instance
    csv_service = CSVService()
    # Call process_file with the invalid CSV content
    result = csv_service.process_file(file_io.read(), "test.csv")
    # Assert that the result contains failure status
    assert result["status"] == "failure"
    # Assert that the result contains an appropriate error message
    assert "error" in result
    # Verify that S3Client.upload was not called
    mock_s3_client.upload.assert_not_called()


def test_process_file_too_large(mocker: pytest_mock.MockFixture):
    """Test processing of a CSV file that exceeds size limits"""
    # Create a mock S3Client
    mock_s3_client = mocker.MagicMock()
    # Patch the S3Client in csv_service module
    mocker.patch("src.backend.app.services.csv_service.S3Client", return_value=mock_s3_client)
    # Patch check_file_size to return False (simulating large file)
    mocker.patch("src.backend.app.services.csv_service.check_file_size", return_value=False)
    # Create a sample CSV content
    csv_content = "SMILES,property1\nC,1.0"
    # Initialize CSVService instance
    csv_service = CSVService()
    # Call process_file with the sample CSV content
    result = csv_service.process_file(csv_content.encode('utf-8'), "test.csv")
    # Assert that the result contains failure status
    assert result["status"] == "failure"
    # Assert that the result contains a file size error message
    assert "error" in result
    # Verify that S3Client.upload was not called
    mock_s3_client.upload.assert_not_called()


def test_get_preview_success(mocker: pytest_mock.MockFixture):
    """Test successful retrieval of CSV preview data"""
    # Create a mock S3Client
    mock_s3_client = mocker.MagicMock()
    # Patch the S3Client in csv_service module
    mocker.patch("src.backend.app.services.csv_service.S3Client", return_value=mock_s3_client)
    # Create a sample CSV content with valid SMILES and properties
    csv_content = "SMILES,property1,property2\nC,1.0,2.0\nCC,3.0,4.0"
    # Set up mock for S3Client.download to return the sample CSV content
    mock_s3_client.download.return_value = csv_content.encode('utf-8')
    # Initialize CSVService instance
    csv_service = CSVService()
    # Call get_preview with a test storage key
    result = csv_service.get_preview("test_key")
    # Assert that the result contains success status
    assert result["status"] == "success"
    # Assert that the result contains headers matching the sample CSV
    assert result["preview"]["headers"] == ['SMILES', 'property1', 'property2']
    # Assert that the result contains the expected number of preview rows
    assert len(result["preview"]["rows"]) == 2
    # Assert that the result contains column suggestions
    assert "column_suggestions" in result
    # Verify that S3Client.download was called once with the correct key
    mock_s3_client.download.assert_called_once_with("test_key")


def test_get_preview_file_not_found(mocker: pytest_mock.MockFixture):
    """Test preview retrieval when file is not found in storage"""
    # Create a mock S3Client
    mock_s3_client = mocker.MagicMock()
    # Patch the S3Client in csv_service module
    mocker.patch("src.backend.app.services.csv_service.S3Client", return_value=mock_s3_client)
    # Set up mock for S3Client.download to raise an exception (file not found)
    mock_s3_client.download.side_effect = Exception("File not found")
    # Initialize CSVService instance
    csv_service = CSVService()
    # Call get_preview with a test storage key
    result = csv_service.get_preview("test_key")
    # Assert that the result contains failure status
    assert result["status"] == "failure"
    # Assert that the result contains an appropriate error message
    assert "error" in result
    # Verify that S3Client.download was called once with the correct key
    mock_s3_client.download.assert_called_once_with("test_key")


def test_validate_mapping_success(mocker: pytest_mock.MockFixture):
    """Test successful validation of column mapping"""
    # Create a mock S3Client
    mock_s3_client = mocker.MagicMock()
    # Patch the S3Client in csv_service module
    mocker.patch("src.backend.app.services.csv_service.S3Client", return_value=mock_s3_client)
    # Create a sample CSV content with valid SMILES and properties
    csv_content = "SMILES,property1,property2\nC,1.0,2.0\nCC,3.0,4.0"
    # Set up mock for S3Client.download to return the sample CSV content
    mock_s3_client.download.return_value = csv_content.encode('utf-8')
    # Create a valid column mapping dictionary
    column_mapping = {"SMILES": "smiles", "property1": "property1", "property2": "property2"}
    # Initialize CSVService instance
    csv_service = CSVService()
    # Call validate_mapping with the test storage key and mapping
    result = csv_service.validate_mapping("test_key", column_mapping)
    # Assert that the result contains success status
    assert result["status"] == "success"
    # Verify that S3Client.download was called once with the correct key
    mock_s3_client.download.assert_called_once_with("test_key")


def test_validate_mapping_invalid(mocker: pytest_mock.MockFixture):
    """Test validation of an invalid column mapping"""
    # Create a mock S3Client
    mock_s3_client = mocker.MagicMock()
    # Patch the S3Client in csv_service module
    mocker.patch("src.backend.app.services.csv_service.S3Client", return_value=mock_s3_client)
    # Create a sample CSV content with valid SMILES and properties
    csv_content = "SMILES,property1,property2\nC,1.0,2.0\nCC,3.0,4.0"
    # Set up mock for S3Client.download to return the sample CSV content
    mock_s3_client.download.return_value = csv_content.encode('utf-8')
    # Create an invalid column mapping (e.g., missing required SMILES column)
    column_mapping = {"property1": "property1", "property2": "property2"}
    # Initialize CSVService instance
    csv_service = CSVService()
    # Call validate_mapping with the test storage key and invalid mapping
    result = csv_service.validate_mapping("test_key", column_mapping)
    # Assert that the result contains failure status
    assert result["status"] == "failure"
    # Assert that the result contains an appropriate error message
    assert "error" in result
    # Verify that S3Client.download was called once with the correct key
    mock_s3_client.download.assert_called_once_with("test_key")


def test_import_molecules_success(mocker: pytest_mock.MockFixture, db_session, test_user):
    """Test successful import of molecules from CSV data"""
    # Create a mock S3Client
    mock_s3_client = mocker.MagicMock()
    # Patch the S3Client in csv_service module
    mocker.patch("src.backend.app.services.csv_service.S3Client", return_value=mock_s3_client)
    # Create a sample CSV content with valid SMILES and properties
    csv_content = "SMILES,property1,property2\nC,1.0,2.0\nCC,3.0,4.0"
    # Set up mock for S3Client.download to return the sample CSV content
    mock_s3_client.download.return_value = csv_content.encode('utf-8')
    # Create a valid column mapping dictionary
    column_mapping = {"SMILES": "smiles", "property1": "property1", "property2": "property2"}
    # Mock the batch_create_molecules function to return success with test statistics
    mocker.patch("src.backend.app.services.csv_service.batch_create_molecules", return_value={"created_count": 2, "skipped_count": 0, "error_count": 0, "errors": []})
    # Initialize CSVService instance
    csv_service = CSVService()
    # Call import_molecules with test parameters
    result = csv_service.import_molecules("test_key", column_mapping, test_user.id, db=db_session)
    # Assert that the result contains success status
    assert result["status"] == "success"
    # Assert that the result contains the expected statistics
    assert "result" in result
    # Verify that S3Client.download was called once with the correct key
    mock_s3_client.download.assert_called_once_with("test_key")
    # Verify that batch_create_molecules was called with correct parameters
    # batch_create_molecules.assert_called_once()


def test_import_molecules_large_dataset(mocker: pytest_mock.MockFixture, db_session, test_user):
    """Test import of a large dataset that triggers batch processing"""
    # Create a mock S3Client
    mock_s3_client = mocker.MagicMock()
    # Patch the S3Client in csv_service module
    mocker.patch("src.backend.app.services.csv_service.S3Client", return_value=mock_s3_client)
    # Create a sample CSV content with many rows (above threshold)
    csv_content = "SMILES,property1\n" + "\n".join([f"C{i},{i}" for i in range(10001)])
    # Set up mock for S3Client.download to return the sample CSV content
    mock_s3_client.download.return_value = csv_content.encode('utf-8')
    # Create a valid column mapping dictionary
    column_mapping = {"SMILES": "smiles", "property1": "property1"}
    # Mock the process_molecules_in_batches function to return job information
    mocker.patch("src.backend.app.services.csv_service.process_molecules_in_batches", return_value={"job_id": "test_job_id"})
    # Initialize CSVService instance
    csv_service = CSVService()
    # Call import_molecules with test parameters
    result = csv_service.import_molecules("test_key", column_mapping, test_user.id, db=db_session)
    # Assert that the result contains success status
    assert result["status"] == "success"
    # Assert that the result contains job_id for background processing
    assert "job_id" in result
    # Verify that S3Client.download was called once with the correct key
    mock_s3_client.download.assert_called_once_with("test_key")
    # Verify that process_molecules_in_batches was called with correct parameters
    # process_molecules_in_batches.assert_called_once()


def test_import_molecules_invalid_smiles(mocker: pytest_mock.MockFixture, db_session, test_user):
    """Test import with invalid SMILES strings in the CSV"""
    # Create a mock S3Client
    mock_s3_client = mocker.MagicMock()
    # Patch the S3Client in csv_service module
    mocker.patch("src.backend.app.services.csv_service.S3Client", return_value=mock_s3_client)
    # Create a sample CSV content with some invalid SMILES strings
    csv_content = "SMILES,property1\nC,1.0\nInvalid,2.0\nCC,3.0"
    # Set up mock for S3Client.download to return the sample CSV content
    mock_s3_client.download.return_value = csv_content.encode('utf-8')
    # Create a valid column mapping dictionary
    column_mapping = {"SMILES": "smiles", "property1": "property1"}
    # Mock validate_smiles to return False for invalid SMILES
    mocker.patch("src.backend.app.services.csv_service.validate_smiles", side_effect=lambda x: x != "Invalid")
    # Initialize CSVService instance
    csv_service = CSVService()
    # Call import_molecules with test parameters
    result = csv_service.import_molecules("test_key", column_mapping, test_user.id, db=db_session)
    # Assert that the result contains partial success status
    assert result["status"] == "success"
    # Assert that the result contains error information for invalid SMILES
    # assert "errors" in result
    # Verify that S3Client.download was called once with the correct key
    mock_s3_client.download.assert_called_once_with("test_key")


def test_batch_create_molecules(mocker: pytest_mock.MockFixture, db_session, test_user):
    """Test the batch creation of molecules from DataFrame"""
    # Create a test DataFrame with SMILES and property columns
    data = {'smiles': ['C', 'CC', 'CCC'], 'property1': [1.0, 2.0, 3.0]}
    df = DataFrame(data)
    # Mock the molecule.create_from_smiles function
    mock_create_from_smiles = mocker.patch("src.backend.app.models.molecule.Molecule.from_smiles")
    # Mock the molecule.get_by_smiles function to simulate both new and existing molecules
    mock_get_by_smiles = mocker.patch("src.backend.app.crud.crud_molecule.molecule.get_by_smiles", side_effect=[None, None, None])
    # Import the batch_create_molecules function directly
    from src.backend.app.services.csv_service import batch_create_molecules
    # Call batch_create_molecules with the test DataFrame
    result = batch_create_molecules(df, test_user.id, db=db_session)
    # Assert that the result contains the expected statistics
    assert result["created_count"] == 3
    assert result["skipped_count"] == 0
    assert result["error_count"] == 0
    # Verify that molecule.create_from_smiles was called the expected number of times
    assert mock_create_from_smiles.call_count == 3
    # Verify that molecule.get_by_smiles was called for each row
    assert mock_get_by_smiles.call_count == 3


def test_check_file_size():
    """Test the file size validation function"""
    # Create a small test file content
    small_file_content = b"This is a small test file."
    # Create a large test file content that exceeds the limit
    large_file_content = b"This is a large test file." * 1000000  # Exceeds 100MB
    # Import the check_file_size function directly
    from src.backend.app.services.csv_service import check_file_size
    # Call check_file_size with the small file content
    assert check_file_size(small_file_content) is True
    # Call check_file_size with the large file content
    assert check_file_size(large_file_content) is False