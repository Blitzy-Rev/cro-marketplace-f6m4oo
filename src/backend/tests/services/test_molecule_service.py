import unittest.mock as mock
import pytest
import pandas as pd
import uuid
import os
import tempfile

from typing import Dict, List, Any
from src.backend.app.core.exceptions import MoleculeException, CSVException
from src.backend.app.services.molecule_service import MoleculeService, molecule_service
from src.backend.app.models.molecule import Molecule, MoleculeStatus
from src.backend.app.models.library import Library
from src.backend.app.crud.crud_molecule import molecule
from src.backend.app.utils.csv_parser import CSVProcessor
from src.backend.app.integrations.ai_engine.client import AIEngineClient
from src.backend.app.integrations.ai_engine.models import PredictionRequest, BatchPredictionRequest
from src.backend.app.constants.molecule_properties import PropertySource, PREDICTABLE_PROPERTIES
from src.backend.app.core.exceptions import MoleculeException, CSVException, AIEngineException
from src.backend.app.integrations.ai_engine.exceptions import AIEngineException as AIEngineExceptionAlias


@pytest.fixture
def mock_molecule_service():
    """Fixture to create a MoleculeService instance with mocked dependencies."""
    with mock.patch("src.backend.app.services.molecule_service.AIEngineClient") as MockAIClient:
        mock_ai_client = MockAIClient.return_value
        yield MoleculeService(ai_client=mock_ai_client)


@pytest.mark.parametrize('smiles, expected_result', [('CC', True), ('C1=CC=CC=C1', True), ('invalid', False)])
def test_create_molecule(smiles, expected_result):
    """Test creating a new molecule from SMILES string"""
    with mock.patch("src.backend.app.crud.crud_molecule.molecule.create_from_smiles") as mock_create_from_smiles, \
            mock.patch("src.backend.app.crud.crud_molecule.molecule.get_by_smiles") as mock_get_by_smiles, \
            mock.patch("src.backend.app.utils.smiles.validate_smiles") as mock_validate_smiles:
        mock_validate_smiles.return_value = expected_result
        mock_get_by_smiles.return_value = None  # Ensure molecule doesn't already exist
        if expected_result:
            mock_create_from_smiles.return_value = mock.Mock(spec=Molecule)
            molecule_data = molecule_service.create_molecule(smiles)
            assert mock_create_from_smiles.called
        else:
            with pytest.raises(MoleculeException):
                molecule_service.create_molecule(smiles)


def test_create_molecule_existing():
    """Test creating a molecule that already exists"""
    with mock.patch("src.backend.app.crud.crud_molecule.molecule.create_from_smiles") as mock_create_from_smiles, \
            mock.patch("src.backend.app.crud.crud_molecule.molecule.get_by_smiles") as mock_get_by_smiles:
        mock_molecule = mock.Mock(spec=Molecule)
        mock_get_by_smiles.return_value = mock_molecule
        molecule_data = molecule_service.create_molecule("CC")
        assert not mock_create_from_smiles.called
        assert molecule_data == mock_molecule.to_dict()


def test_get_molecule():
    """Test retrieving a molecule by ID"""
    with mock.patch("src.backend.app.crud.crud_molecule.molecule.get") as mock_get:
        mock_molecule_id = uuid.uuid4()
        mock_molecule = mock.Mock(spec=Molecule)
        mock_get.return_value = mock_molecule
        molecule_data = molecule_service.get_molecule(mock_molecule_id)
        mock_get.assert_called_with(mock_molecule_id, db=None)
        assert molecule_data == mock_molecule.to_dict()


def test_get_molecule_by_smiles():
    """Test retrieving a molecule by SMILES string"""
    with mock.patch("src.backend.app.crud.crud_molecule.molecule.get_by_smiles") as mock_get_by_smiles:
        test_smiles = "CC"
        mock_molecule = mock.Mock(spec=Molecule)
        mock_get_by_smiles.return_value = mock_molecule
        molecule_data = molecule_service.get_molecule_by_smiles(test_smiles)
        mock_get_by_smiles.assert_called_with(test_smiles, db=None)
        assert molecule_data == mock_molecule.to_dict()


def test_filter_molecules():
    """Test filtering molecules based on criteria"""
    with mock.patch("src.backend.app.crud.crud_molecule.molecule.filter_molecules") as mock_filter_molecules:
        filter_params = {"mw_min": 100, "mw_max": 200}
        mock_results = {"items": [mock.Mock(spec=Molecule)], "total": 1}
        mock_filter_molecules.return_value = mock_results
        results = molecule_service.filter_molecules(filter_params, skip=0, limit=10)
        mock_filter_molecules.assert_called_with(filter_params, db=None, skip=0, limit=10, sort_by=None, descending=False)
        assert results == mock_results


def test_process_csv_file():
    """Test processing a CSV file with molecular data"""
    with tempfile.NamedTemporaryFile(mode='w', delete=False, suffix='.csv') as tmp_file, \
            mock.patch("src.backend.app.utils.csv_parser.CSVProcessor.load_csv") as mock_load_csv, \
            mock.patch("src.backend.app.utils.csv_parser.CSVProcessor.set_column_mapping") as mock_set_column_mapping, \
            mock.patch("src.backend.app.utils.csv_parser.CSVProcessor.process") as mock_process, \
            mock.patch("src.backend.app.utils.csv_parser.CSVProcessor.get_valid_molecules") as mock_get_valid_molecules, \
            mock.patch("src.backend.app.crud.crud_molecule.molecule.batch_create") as mock_batch_create, \
            mock.patch("src.backend.app.utils.csv_parser.CSVProcessor.get_summary") as mock_get_summary:
        tmp_file_path = tmp_file.name
        column_mapping = {"col1": "smiles"}
        mock_load_csv.return_value = None
        mock_set_column_mapping.return_value = None
        mock_process.return_value = None
        mock_get_valid_molecules.return_value = pd.DataFrame([{"smiles": "CC"}])
        mock_batch_create.return_value = {"created_count": 1, "failed_count": 0}
        mock_get_summary.return_value = {"total_rows": 1}
        results = molecule_service.process_csv_file(tmp_file_path, column_mapping)
        mock_load_csv.assert_called_once()
        mock_set_column_mapping.assert_called_with(column_mapping)
        mock_process.assert_called_once()
        mock_get_valid_molecules.assert_called_once()
        mock_batch_create.assert_called()
        assert results == {"total_rows": 1, "created_count": 1, "failed_count": 0}
        os.remove(tmp_file_path)


@pytest.mark.parametrize('error_type, expected_exception', [('load', CSVException), ('process', CSVException), ('batch_create', MoleculeException)])
def test_process_csv_file_error(error_type, expected_exception):
    """Test handling errors during CSV file processing"""
    with tempfile.NamedTemporaryFile(mode='w', delete=False, suffix='.csv') as tmp_file, \
            mock.patch("src.backend.app.utils.csv_parser.CSVProcessor.load_csv") as mock_load_csv, \
            mock.patch("src.backend.app.utils.csv_parser.CSVProcessor.set_column_mapping") as mock_set_column_mapping, \
            mock.patch("src.backend.app.utils.csv_parser.CSVProcessor.process") as mock_process, \
            mock.patch("src.backend.app.crud.crud_molecule.molecule.batch_create") as mock_batch_create:
        tmp_file_path = tmp_file.name
        column_mapping = {"col1": "smiles"}
        if error_type == 'load':
            mock_load_csv.side_effect = CSVException(message="Load error")
        elif error_type == 'process':
            mock_load_csv.return_value = None
            mock_set_column_mapping.return_value = None
            mock_process.side_effect = CSVException(message="Process error")
        elif error_type == 'batch_create':
            mock_load_csv.return_value = None
            mock_set_column_mapping.return_value = None
            mock_process.return_value = None
            mock_batch_create.side_effect = MoleculeException(message="Batch create error")
        with pytest.raises(expected_exception):
            molecule_service.process_csv_file(tmp_file_path, column_mapping)
        os.remove(tmp_file_path)


def test_get_csv_preview():
    """Test getting a preview of CSV data for column mapping"""
    with tempfile.NamedTemporaryFile(mode='w', delete=False, suffix='.csv') as tmp_file, \
            mock.patch("src.backend.app.utils.csv_parser.CSVProcessor.load_csv") as mock_load_csv, \
            mock.patch("src.backend.app.utils.csv_parser.CSVProcessor.get_preview") as mock_get_preview, \
            mock.patch("src.backend.app.utils.csv_parser.CSVProcessor.get_mapping_suggestions") as mock_get_mapping_suggestions:
        tmp_file_path = tmp_file.name
        mock_load_csv.return_value = None
        mock_get_preview.return_value = {"headers": ["col1"], "rows": [{"col1": "data"}], "total_rows": 1, "preview_rows": 1}
        mock_get_mapping_suggestions.return_value = {"col1": "smiles"}
        preview = molecule_service.get_csv_preview(tmp_file_path, num_rows=5)
        mock_load_csv.assert_called_once()
        mock_get_preview.assert_called_with(5)
        assert preview == {"headers": ["col1"], "rows": [{"col1": "data"}], "total_rows": 1, "preview_rows": 1, "suggestions": {"col1": "smiles"}}
        os.remove(tmp_file_path)


def test_add_to_library():
    """Test adding a molecule to a library"""
    with mock.patch("src.backend.app.crud.crud_molecule.molecule.add_to_library") as mock_add_to_library:
        mock_molecule_id = uuid.uuid4()
        mock_library_id = uuid.uuid4()
        mock_user_id = uuid.uuid4()
        mock_add_to_library.return_value = True
        result = molecule_service.add_to_library(mock_molecule_id, mock_library_id, mock_user_id)
        mock_add_to_library.assert_called_with(mock_molecule_id, mock_library_id, mock_user_id, db=None)
        assert result is True


def test_remove_from_library():
    """Test removing a molecule from a library"""
    with mock.patch("src.backend.app.crud.crud_molecule.molecule.remove_from_library") as mock_remove_from_library:
        mock_molecule_id = uuid.uuid4()
        mock_library_id = uuid.uuid4()
        mock_remove_from_library.return_value = True
        result = molecule_service.remove_from_library(mock_molecule_id, mock_library_id)
        mock_remove_from_library.assert_called_with(mock_molecule_id, mock_library_id, db=None)
        assert result is True


def test_predict_properties(mock_molecule_service):
    """Test requesting property predictions from AI engine"""
    mock_molecule_id = uuid.uuid4()
    mock_molecule = mock.Mock(spec=Molecule, smiles="CC")
    mock_prediction_response = mock.Mock()
    mock_prediction_response.dict.return_value = {"job_id": "123"}
    mock_prediction_results = [{"property1": {"value": 1.0, "confidence": 0.9}}]

    mock_molecule_service._ai_client.predict_properties.return_value = mock_prediction_response
    mock_molecule_service._ai_client.wait_for_prediction_completion.return_value.results = [mock.Mock(properties=mock_prediction_results)]
    with mock.patch("src.backend.app.crud.crud_molecule.molecule.get") as mock_get:
        mock_get.return_value = mock_molecule
        with mock.patch.object(mock_molecule_service, "store_prediction_results") as mock_store_prediction_results:
            results = mock_molecule_service.predict_properties(mock_molecule_id)
            mock_molecule_service._ai_client.predict_properties.assert_called_with(PredictionRequest(smiles=[mock_molecule.smiles], properties=PREDICTABLE_PROPERTIES))
            mock_molecule_service._ai_client.wait_for_prediction_completion.assert_called_with("123")
            mock_store_prediction_results.assert_called_with(mock_molecule_id, mock_prediction_results, db=None)
            assert results == {"job_id": "123"}


def test_predict_properties_wait_false(mock_molecule_service):
    """Test requesting property predictions without waiting for results"""
    mock_molecule_id = uuid.uuid4()
    mock_molecule = mock.Mock(spec=Molecule, smiles="CC")
    mock_prediction_response = mock.Mock()
    mock_prediction_response.dict.return_value = {"job_id": "123"}
    with mock.patch("src.backend.app.crud.crud_molecule.molecule.get") as mock_get:
        mock_get.return_value = mock_molecule
        results = mock_molecule_service.predict_properties(mock_molecule_id, wait_for_results=False)
        mock_molecule_service._ai_client.predict_properties.assert_called_with(PredictionRequest(smiles=[mock_molecule.smiles], properties=PREDICTABLE_PROPERTIES))
        mock_molecule_service._ai_client.wait_for_prediction_completion.assert_not_called()
        assert results == {"job_id": "123"}


def test_predict_properties_molecule_not_found(mock_molecule_service):
    """Test handling molecule not found during prediction"""
    mock_molecule_id = uuid.uuid4()
    with mock.patch("src.backend.app.crud.crud_molecule.molecule.get") as mock_get:
        mock_get.return_value = None
        with pytest.raises(MoleculeException):
            mock_molecule_service.predict_properties(mock_molecule_id)


def test_batch_predict_properties(mock_molecule_service):
    """Test requesting property predictions for multiple molecules"""
    mock_molecule_ids = [uuid.uuid4(), uuid.uuid4()]
    mock_batch_response = mock.Mock()
    mock_batch_response.dict.return_value = {"batch_id": "batch123"}
    with mock.patch("src.backend.app.crud.crud_molecule.molecule.get") as mock_get:
        mock_get.return_value = mock.Mock(spec=Molecule)
        mock_molecule_service._ai_client.submit_batch_prediction.return_value = mock_batch_response
        results = mock_molecule_service.batch_predict_properties(mock_molecule_ids)
        mock_molecule_service._ai_client.submit_batch_prediction.assert_called_with(BatchPredictionRequest(molecule_ids=mock_molecule_ids, properties=PREDICTABLE_PROPERTIES))
        assert results == {"batch_id": "batch123"}


def test_store_prediction_results():
    """Test storing property prediction results for a molecule"""
    with mock.patch("src.backend.app.crud.crud_molecule.molecule.get") as mock_get:
        mock_molecule_id = uuid.uuid4()
        mock_molecule = mock.Mock(spec=Molecule)
        mock_get.return_value = mock_molecule
        prediction_results = {"logp": {"value": 2.5, "confidence": 0.8}}
        result = molecule_service.store_prediction_results(mock_molecule_id, prediction_results)
        mock_molecule.set_property.assert_called_with("logp", 2.5, PropertySource.PREDICTED.value)
        assert result is True


def test_store_prediction_results_molecule_not_found():
    """Test handling molecule not found when storing prediction results"""
    with mock.patch("src.backend.app.crud.crud_molecule.molecule.get") as mock_get:
        mock_molecule_id = uuid.uuid4()
        mock_get.return_value = None
        prediction_results = {"logp": {"value": 2.5, "confidence": 0.8}}
        with pytest.raises(MoleculeException):
            molecule_service.store_prediction_results(mock_molecule_id, prediction_results)


def test_bulk_operation_add_to_library():
    """Test bulk operation to add molecules to a library"""
    with mock.patch("src.backend.app.crud.crud_molecule.molecule.add_to_library") as mock_add_to_library:
        mock_molecule_ids = [uuid.uuid4(), uuid.uuid4()]
        mock_library_id = uuid.uuid4()
        mock_user_id = uuid.uuid4()
        mock_add_to_library.return_value = True
        results = molecule_service.bulk_operation(mock_molecule_ids, "add_to_library", {"library_id": mock_library_id, "added_by": mock_user_id})
        assert mock_add_to_library.call_count == len(mock_molecule_ids)
        assert results == {"success": True, "message": "Bulk operation 'add_to_library' completed"}


def test_bulk_operation_remove_from_library():
    """Test bulk operation to remove molecules from a library"""
    with mock.patch("src.backend.app.crud.crud_molecule.molecule.remove_from_library") as mock_remove_from_library:
        mock_molecule_ids = [uuid.uuid4(), uuid.uuid4()]
        mock_library_id = uuid.uuid4()
        mock_remove_from_library.return_value = True
        results = molecule_service.bulk_operation(mock_molecule_ids, "remove_from_library", {"library_id": mock_library_id})
        assert mock_remove_from_library.call_count == len(mock_molecule_ids)
        assert results == {"success": True, "message": "Bulk operation 'remove_from_library' completed"}


def test_bulk_operation_predict_properties(mock_molecule_service):
    """Test bulk operation to predict properties for multiple molecules"""
    mock_molecule_ids = [uuid.uuid4(), uuid.uuid4()]
    mock_batch_response = {"batch_id": "batch123"}
    mock_molecule_service.batch_predict_properties.return_value = mock_batch_response
    results = mock_molecule_service.bulk_operation(mock_molecule_ids, "predict_properties", {"properties": ["logp"]})
    mock_molecule_service.batch_predict_properties.assert_called_with(mock_molecule_ids, properties=["logp"], db=None)
    assert results == mock_batch_response


def test_bulk_operation_invalid_operation():
    """Test handling invalid bulk operation type"""
    mock_molecule_ids = [uuid.uuid4(), uuid.uuid4()]
    with pytest.raises(ValueError):
        molecule_service.bulk_operation(mock_molecule_ids, "invalid_operation", {})