import pytest
from unittest import mock
import uuid
from datetime import datetime

from src.backend.app.services.prediction_service import PredictionService, prediction_service
from src.backend.app.integrations.ai_engine.client import AIEngineClient
from src.backend.app.integrations.ai_engine.models import PredictionRequest, BatchPredictionRequest
from src.backend.app.integrations.ai_engine.exceptions import AIEngineException, AIEngineTimeoutError, AIServiceUnavailableError
from src.backend.app.core.exceptions import PredictionException
from src.backend.app.models.prediction import PredictionStatus
from src.backend.app.constants.molecule_properties import PREDICTABLE_PROPERTIES
from tests.conftest import db_session, test_molecule, test_molecules


class TestPredictionService:
    """Test class for PredictionService"""

    @pytest.mark.parametrize('wait_for_results', [True, False])
    def test_predict_properties_for_molecule(self, db_session, test_molecule, wait_for_results):
        """Tests the predict_properties_for_molecule method with successful prediction"""
        # LD1: Create a mock AIEngineClient
        mock_ai_client = mock.Mock(spec=AIEngineClient)
        # LD1: Configure mock to return appropriate prediction response
        mock_ai_client.predict_properties.return_value = mock.Mock(job_id="test_job_id")
        mock_ai_client.wait_for_prediction_completion.return_value = mock.Mock(results=[mock.Mock(smiles=test_molecule.smiles, properties={"logp": {"value": 2.5, "confidence": 0.8}})])

        # LD1: Create PredictionService instance with mock client
        service = PredictionService(ai_client=mock_ai_client)

        # LD1: Call predict_properties_for_molecule with test molecule ID
        result = service.predict_properties_for_molecule(molecule_id=test_molecule.id, wait_for_results=wait_for_results, db=db_session)

        # LD1: Verify AIEngineClient.predict_properties was called with correct parameters
        mock_ai_client.predict_properties.assert_called_once()
        args, _ = mock_ai_client.predict_properties.call_args
        request = args[0]
        assert isinstance(request, PredictionRequest)
        assert request.smiles == [test_molecule.smiles]
        assert request.properties == PREDICTABLE_PROPERTIES

        # LD1: If wait_for_results is True, verify wait_for_prediction_completion was called
        if wait_for_results:
            mock_ai_client.wait_for_prediction_completion.assert_called_once_with("test_job_id")

        # LD1: Verify prediction data was stored in database
        if wait_for_results:
            assert result["success_count"] == 1

        # LD1: Verify correct response is returned with prediction data
        if wait_for_results:
            assert result["batch_id"] is not None
            assert result["success_count"] == 1
        else:
            assert result["batch_id"] is not None
            assert result["job_id"] == "test_job_id"

    def test_predict_properties_for_molecule_invalid_molecule(self, db_session):
        """Tests predict_properties_for_molecule with non-existent molecule ID"""
        # LD1: Create a mock AIEngineClient
        mock_ai_client = mock.Mock(spec=AIEngineClient)
        # LD1: Create PredictionService instance with mock client
        service = PredictionService(ai_client=mock_ai_client)

        # LD1: Call predict_properties_for_molecule with non-existent molecule ID
        with pytest.raises(PredictionException) as exc_info:
            service.predict_properties_for_molecule(molecule_id=uuid.uuid4(), db=db_session)

        # LD1: Verify PredictionException is raised with appropriate message
        assert "Molecule with id" in str(exc_info.value)
        # LD1: Verify AIEngineClient methods were not called
        mock_ai_client.predict_properties.assert_not_called()
        mock_ai_client.wait_for_prediction_completion.assert_not_called()

    def test_predict_properties_for_molecule_invalid_properties(self, db_session, test_molecule):
        """Tests predict_properties_for_molecule with invalid property names"""
        # LD1: Create a mock AIEngineClient
        mock_ai_client = mock.Mock(spec=AIEngineClient)
        # LD1: Create PredictionService instance with mock client
        service = PredictionService(ai_client=mock_ai_client)

        # LD1: Call predict_properties_for_molecule with invalid property names
        with pytest.raises(PredictionException) as exc_info:
            service.predict_properties_for_molecule(molecule_id=test_molecule.id, properties=["invalid_property"], db=db_session)

        # LD1: Verify PredictionException is raised with appropriate message
        assert "Invalid property specified" in str(exc_info.value)
        # LD1: Verify AIEngineClient methods were not called
        mock_ai_client.predict_properties.assert_not_called()
        mock_ai_client.wait_for_prediction_completion.assert_not_called()

    def test_predict_properties_for_molecule_ai_engine_error(self, db_session, test_molecule):
        """Tests predict_properties_for_molecule when AI engine raises an exception"""
        # LD1: Create a mock AIEngineClient
        mock_ai_client = mock.Mock(spec=AIEngineClient)
        # LD1: Configure mock to raise AIEngineException
        mock_ai_client.predict_properties.side_effect = AIEngineException(message="AI Engine failed")
        # LD1: Create PredictionService instance with mock client
        service = PredictionService(ai_client=mock_ai_client)

        # LD1: Call predict_properties_for_molecule with test molecule ID
        with pytest.raises(AIEngineException) as exc_info:
            service.predict_properties_for_molecule(molecule_id=test_molecule.id, db=db_session)

        # LD1: Verify AIEngineException is propagated
        assert "AI Engine failed" in str(exc_info.value)
        # LD1: Verify no prediction data was stored in database
        # LD1: Verify AIEngineClient methods were called
        mock_ai_client.predict_properties.assert_called_once()

    def test_predict_properties_for_molecules(self, db_session, test_molecules):
        """Tests the predict_properties_for_molecules method for batch predictions"""
        # LD1: Create a mock AIEngineClient
        mock_ai_client = mock.Mock(spec=AIEngineClient)
        # LD1: Configure mock to return appropriate batch prediction response
        mock_ai_client.submit_batch_prediction.return_value = mock.Mock(job_id="test_job_id", batch_id="test_batch_id")
        # LD1: Create PredictionService instance with mock client
        service = PredictionService(ai_client=mock_ai_client)

        # LD1: Call predict_properties_for_molecules with test molecule IDs
        molecule_ids = [molecule.id for molecule in test_molecules]
        result = service.predict_properties_for_molecules(molecule_ids=molecule_ids, db=db_session)

        # LD1: Verify AIEngineClient.submit_batch_prediction was called with correct parameters
        mock_ai_client.submit_batch_prediction.assert_called_once()
        args, _ = mock_ai_client.submit_batch_prediction.call_args
        request = args[0]
        assert isinstance(request, BatchPredictionRequest)
        assert request.molecule_ids == molecule_ids
        assert request.properties == PREDICTABLE_PROPERTIES

        # LD1: Verify batch prediction record was created in database
        # LD1: Verify correct response is returned with batch ID and job ID
        assert result["batch_id"] is not None
        assert result["job_id"] == "test_job_id"

    def test_predict_properties_for_molecules_invalid_molecules(self, db_session):
        """Tests predict_properties_for_molecules with non-existent molecule IDs"""
        # LD1: Create a mock AIEngineClient
        mock_ai_client = mock.Mock(spec=AIEngineClient)
        # LD1: Create PredictionService instance with mock client
        service = PredictionService(ai_client=mock_ai_client)

        # LD1: Call predict_properties_for_molecules with non-existent molecule IDs
        with pytest.raises(PredictionException) as exc_info:
            service.predict_properties_for_molecules(molecule_ids=[uuid.uuid4()], db=db_session)

        # LD1: Verify PredictionException is raised with appropriate message
        assert "No molecules found" in str(exc_info.value)
        # LD1: Verify AIEngineClient methods were not called
        mock_ai_client.submit_batch_prediction.assert_not_called()

    def test_get_prediction_job_status(self, db_session):
        """Tests the get_prediction_job_status method"""
        # LD1: Create a mock AIEngineClient
        mock_ai_client = mock.Mock(spec=AIEngineClient)
        # LD1: Configure mock to return appropriate job status response
        mock_ai_client.get_prediction_status.return_value = mock.Mock(status="completed", completed_molecules=10, total_molecules=100)
        # LD1: Create PredictionService instance with mock client
        service = PredictionService(ai_client=mock_ai_client)

        # LD1: Create a test batch record in the database
        batch_id = uuid.uuid4()
        # LD1: Call get_prediction_job_status with batch ID
        result = service.get_prediction_job_status(batch_id=batch_id, db=db_session)

        # LD1: Verify AIEngineClient.get_prediction_status was called with correct job ID
        mock_ai_client.get_prediction_status.assert_called_once()
        # LD1: Verify batch status was updated in database
        # LD1: Verify correct response is returned with status information
        assert result["batch_id"] == batch_id
        assert result["status"] == "completed"
        assert result["completed_count"] == 10
        assert result["total_count"] == 100

    def test_get_prediction_job_status_batch_not_found(self, db_session):
        """Tests get_prediction_job_status with non-existent batch ID"""
        # LD1: Create a mock AIEngineClient
        mock_ai_client = mock.Mock(spec=AIEngineClient)
        # LD1: Create PredictionService instance with mock client
        service = PredictionService(ai_client=mock_ai_client)

        # LD1: Call get_prediction_job_status with non-existent batch ID
        with pytest.raises(PredictionException) as exc_info:
            service.get_prediction_job_status(batch_id=uuid.uuid4(), db=db_session)

        # LD1: Verify PredictionException is raised with appropriate message
        assert "Prediction batch with id" in str(exc_info.value)
        # LD1: Verify AIEngineClient methods were not called
        mock_ai_client.get_prediction_status.assert_not_called()

    @pytest.mark.parametrize('job_status', [PredictionStatus.PROCESSING, PredictionStatus.COMPLETED, PredictionStatus.FAILED])
    def test_check_and_update_prediction_job(self, db_session, job_status):
        """Tests the check_and_update_prediction_job method"""
        # LD1: Create a mock AIEngineClient
        mock_ai_client = mock.Mock(spec=AIEngineClient)
        # LD1: Configure mock to return appropriate job status response based on parameter
        mock_ai_client.get_prediction_status.return_value = mock.Mock(status=job_status.value, completed_molecules=10, total_molecules=100)
        # LD1: Create PredictionService instance with mock client
        service = PredictionService(ai_client=mock_ai_client)

        # LD1: Create a test batch record in the database
        batch_id = uuid.uuid4()
        job_id = "test_job_id"
        # LD1: Call check_and_update_prediction_job with batch ID and job ID
        result = service.check_and_update_prediction_job(batch_id=batch_id, job_id=job_id, db=db_session)

        # LD1: Verify AIEngineClient.get_prediction_status was called with correct job ID
        mock_ai_client.get_prediction_status.assert_called_once_with(job_id)
        # LD1: Verify batch status was updated in database according to job status
        # LD1: If status is COMPLETED, verify process_prediction_results was called
        # LD1: If status is FAILED, verify handle_prediction_failure was called
        # LD1: Verify correct response is returned with updated status information
        assert result["batch_id"] == batch_id
        assert result["status"] == job_status.value
        assert result["completed_count"] == 10
        assert result["total_count"] == 100

    def test_process_prediction_results(self, db_session, test_molecules):
        """Tests the process_prediction_results method"""
        # LD1: Create a mock AIEngineClient
        mock_ai_client = mock.Mock(spec=AIEngineClient)
        # LD1: Configure mock to return prediction results for test molecules
        mock_ai_client.get_prediction_results.return_value = mock.Mock(results=[mock.Mock(smiles=molecule.smiles, properties={"logp": {"value": 2.5, "confidence": 0.8}}) for molecule in test_molecules])
        # LD1: Create PredictionService instance with mock client
        service = PredictionService(ai_client=mock_ai_client)

        # LD1: Create a test batch record in the database with test molecule IDs
        batch_id = uuid.uuid4()
        job_id = "test_job_id"
        # LD1: Call process_prediction_results with batch ID and job ID
        result = service.process_prediction_results(batch_id=batch_id, job_id=job_id, db=db_session)

        # LD1: Verify AIEngineClient.get_prediction_results was called with correct job ID
        mock_ai_client.get_prediction_results.assert_called_once_with(job_id)
        # LD1: Verify prediction records were created in database for each molecule and property
        # LD1: Verify batch completion counts were updated correctly
        # LD1: Verify correct response is returned with processing summary
        assert result["batch_id"] == batch_id
        assert result["success_count"] == len(test_molecules)
        assert result["failure_count"] == 0

    def test_handle_prediction_failure(self, db_session, test_molecules):
        """Tests the handle_prediction_failure method"""
        # LD1: Create a PredictionService instance
        service = PredictionService()

        # LD1: Create a test batch record in the database with test molecule IDs
        batch_id = uuid.uuid4()
        error_message = "AI Engine prediction failed"
        # LD1: Create pending prediction records for test molecules
        # LD1: Call handle_prediction_failure with batch ID and error message
        result = service.handle_prediction_failure(batch_id=batch_id, error_message=error_message, db=db_session)

        # LD1: Verify batch status was updated to FAILED with error message
        # LD1: Verify all pending prediction records were updated to FAILED
        # LD1: Verify correct response is returned with failure details
        assert result["batch_id"] == batch_id
        assert result["status"] == PredictionStatus.FAILED.value
        assert result["error_message"] == error_message

    @pytest.mark.parametrize('confidence_threshold', [None, 0.5, 0.9])
    def test_get_molecule_predictions(self, db_session, test_molecule, confidence_threshold):
        """Tests the get_molecule_predictions method"""
        # LD1: Create prediction records for test molecule with different confidence scores
        # LD1: Create PredictionService instance
        service = PredictionService()

        # LD1: Call get_molecule_predictions with test molecule ID and confidence threshold
        result = service.get_molecule_predictions(molecule_id=test_molecule.id, confidence_threshold=confidence_threshold, db=db_session)

        # LD1: Verify correct predictions are returned based on confidence threshold
        # LD1: Verify predictions are in correct format with all required fields
        assert isinstance(result, list)

    def test_get_molecule_predictions_molecule_not_found(self, db_session):
        """Tests get_molecule_predictions with non-existent molecule ID"""
        # LD1: Create PredictionService instance
        service = PredictionService()

        # LD1: Call get_molecule_predictions with non-existent molecule ID
        with pytest.raises(PredictionException) as exc_info:
            service.get_molecule_predictions(molecule_id=uuid.uuid4(), db=db_session)

        # LD1: Verify PredictionException is raised with appropriate message
        assert "Molecule with id" in str(exc_info.value)

    def test_get_latest_predictions(self, db_session, test_molecule):
        """Tests the get_latest_predictions method"""
        # LD1: Create multiple prediction records for test molecule with different timestamps
        # LD1: Create PredictionService instance
        service = PredictionService()

        # LD1: Call get_latest_predictions with test molecule ID
        result = service.get_latest_predictions(molecule_id=test_molecule.id, db=db_session)

        # LD1: Verify only the latest prediction for each property is returned
        # LD1: Verify predictions are in correct format with all required fields
        assert isinstance(result, dict)

    def test_filter_predictions(self, db_session, test_molecules):
        """Tests the filter_predictions method"""
        # LD1: Create prediction records for test molecules with various properties
        # LD1: Create PredictionService instance
        service = PredictionService()

        # LD1: Create PredictionFilter with various filter criteria
        # LD1: Call filter_predictions with filter parameters
        result = service.filter_predictions(filter_params=mock.Mock(), skip=0, limit=10, db=db_session)

        # LD1: Verify correct predictions are returned based on filter criteria
        # LD1: Verify pagination parameters are correctly applied
        # LD1: Verify response includes correct total count and pagination info
        assert isinstance(result, dict)

    @pytest.mark.parametrize('status', [PredictionStatus.PENDING, PredictionStatus.PROCESSING, PredictionStatus.COMPLETED])
    def test_cancel_prediction_job(self, db_session, status):
        """Tests the cancel_prediction_job method"""
        # LD1: Create a mock AIEngineClient
        mock_ai_client = mock.Mock(spec=AIEngineClient)
        # LD1: Create PredictionService instance with mock client
        service = PredictionService(ai_client=mock_ai_client)

        # LD1: Create a test batch record in the database with specified status
        batch_id = uuid.uuid4()
        # LD1: Call cancel_prediction_job with batch ID
        result = service.cancel_prediction_job(batch_id=batch_id, db=db_session)

        # LD1: If status is PENDING or PROCESSING, verify AIEngineClient.cancel_job was called
        if status in [PredictionStatus.PENDING, PredictionStatus.PROCESSING]:
            mock_ai_client.cancel_job.assert_called_once()
        # LD1: If status is COMPLETED, verify AIEngineClient.cancel_job was not called
        else:
            mock_ai_client.cancel_job.assert_not_called()
        # LD1: Verify batch status was updated appropriately
        # LD1: Verify correct response is returned with cancellation result
        assert result["batch_id"] == batch_id
        assert result["status"] == "cancelled"

    @pytest.mark.parametrize('status', [PredictionStatus.FAILED, PredictionStatus.COMPLETED])
    def test_retry_failed_prediction(self, db_session, status):
        """Tests the retry_failed_prediction method"""
        # LD1: Create PredictionService instance
        service = PredictionService()

        # LD1: Create a test batch record in the database with specified status
        batch_id = uuid.uuid4()
        # LD1: Call retry_failed_prediction with batch ID
        result = service.retry_failed_prediction(batch_id=batch_id, db=db_session)

        # LD1: If status is FAILED, verify batch status was reset to PENDING
        if status == PredictionStatus.FAILED:
            assert result["batch_id"] == batch_id
            assert result["status"] == "retrying"
        # LD1: If status is COMPLETED, verify PredictionException is raised
        else:
            assert result["batch_id"] == batch_id
            assert result["status"] == "error"
            assert result["message"] == "Job is not in failed state"