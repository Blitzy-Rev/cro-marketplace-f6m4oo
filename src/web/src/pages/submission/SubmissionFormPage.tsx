import React, { useState, useEffect, useCallback } from 'react'; // react ^18.0.0
import { useParams, useNavigate } from 'react-router-dom'; // react-router-dom ^6.0.0
import {
  Box,
  Typography,
  CircularProgress,
  Alert
} from '@mui/material'; // @mui/material ^5.0.0
import DashboardLayout from '../../components/layout/DashboardLayout';
import SubmissionForm from '../../components/submission/SubmissionForm';
import useToast from '../../hooks/useToast';
import { getSubmission } from '../../api/submissionApi';
import { ROUTES, getSubmissionDetailPath } from '../../constants/routes';

/**
 * Page component for creating or editing CRO submissions
 */
const SubmissionFormPage: React.FC = () => {
  // Extract submissionId from URL parameters using useParams
  const { id: submissionId } = useParams<{ id: string }>();

  // Initialize navigate function for programmatic navigation
  const navigate = useNavigate();

  // Initialize toast notification hook
  const toast = useToast();

  // Set up state for loading, error, and submission data
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const [initialData, setInitialData] = useState(null);

  // Fetch submission data if submissionId is provided (edit mode)
  useEffect(() => {
    const fetchSubmissionData = async () => {
      if (submissionId) {
        setLoading(true);
        try {
          const submission = await getSubmission(submissionId);
          setInitialData(submission);
        } catch (err) {
          setError(toast.formatError(err));
        } finally {
          setLoading(false);
        }
      }
    };

    fetchSubmissionData();
  }, [submissionId, toast]);

  // Define success handler for form submission
  const handleSubmitSuccess = useCallback(() => {
    navigate(ROUTES.SUBMISSIONS.LIST);
  }, [navigate]);

  // Define cancel handler for form cancellation
  const handleCancel = useCallback(() => {
    navigate(ROUTES.SUBMISSIONS.LIST);
  }, [navigate]);

  // Render DashboardLayout with appropriate title based on edit/create mode
  return (
    <DashboardLayout title={submissionId ? 'Edit Submission' : 'Create Submission'}>
      {loading && (
        <Box display="flex" justifyContent="center" alignItems="center" height={200}>
          <CircularProgress />
        </Box>
      )}
      {error && (
        <Alert severity="error" sx={{ mb: 2 }}>
          {error}
        </Alert>
      )}
      {/* Render SubmissionForm component with appropriate props */}
      {!loading && !error && (
        <SubmissionForm
          initialData={initialData}
          submissionId={submissionId}
          onSubmitSuccess={handleSubmitSuccess}
          onCancel={handleCancel}
        />
      )}
    </DashboardLayout>
  );
};

export default SubmissionFormPage;