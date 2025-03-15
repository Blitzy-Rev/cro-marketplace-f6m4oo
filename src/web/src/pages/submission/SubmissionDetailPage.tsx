import React, { useEffect } from 'react'; // React v18.0.0
import { Box, Typography } from '@mui/material'; // @mui/material ^5.0.0
import { useParams, useNavigate } from 'react-router-dom'; // react-router-dom ^6.0.0

import DashboardLayout from '../../components/layout/DashboardLayout';
import SubmissionDetail from '../../components/submission/SubmissionDetail';
import { useAppDispatch } from '../../store';
import { fetchSubmission, clearSelectedSubmission } from '../../features/submission/submissionSlice';
import { ROUTES } from '../../constants/routes';

/**
 * Page component that displays detailed information about a CRO submission
 */
const SubmissionDetailPage: React.FC = () => {
  // Extract submission ID from URL parameters using useParams hook
  const { id } = useParams<{ id: string }>();

  // Get navigation function using useNavigate hook
  const navigate = useNavigate();

  // Get Redux dispatch function using useAppDispatch hook
  const dispatch = useAppDispatch();

  // Fetch submission data when component mounts or ID changes
  useEffect(() => {
    if (id) {
      dispatch(fetchSubmission(id));
    }
  }, [id, dispatch]);

  // Clear selected submission when component unmounts
  useEffect(() => {
    return () => {
      dispatch(clearSelectedSubmission());
    };
  }, [dispatch]);

  // Handle navigation back to submissions list
  const handleBack = () => {
    navigate(ROUTES.SUBMISSIONS.LIST);
  };

  // Render DashboardLayout with SubmissionDetail component
  return (
    <DashboardLayout title="Submission Detail">
      {/* Pass submission ID to SubmissionDetail component */}
      {id ? (
        <SubmissionDetail submissionId={id} onBack={handleBack} />
      ) : (
        <Typography variant="body1">
          Invalid submission ID.
        </Typography>
      )}
    </DashboardLayout>
  );
};

export default SubmissionDetailPage;