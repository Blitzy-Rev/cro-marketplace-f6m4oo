import React, { useState, useEffect, useCallback } from 'react'; // react ^18.0.0
import { useParams, useNavigate, Link } from 'react-router-dom'; // react-router-dom ^6.0.0
import { Box, Paper, Typography, Stepper, Step, StepLabel, Button, Alert, Breadcrumbs } from '@mui/material'; // @mui/material ^5.0.0

import DashboardLayout from '../../components/layout/DashboardLayout';
import ResultsUploader from '../../components/results/ResultsUploader';
import LoadingOverlay from '../../components/common/LoadingOverlay';
import { useAuth } from '../../hooks/useAuth';
import useToast from '../../hooks/useToast';
import { getSubmission } from '../../api/submissionApi';
import { Submission } from '../../types/submission.types';
import { ROUTES, getSubmissionDetailPath } from '../../constants/routes';

/**
 * Page component for uploading experimental results for a submission
 * @returns Rendered page component
 */
const ResultsUploadPage: React.FC = () => {
  // Extract submissionId from URL parameters using useParams
  const { id: submissionId } = useParams<{ id: string }>();
  
  // Initialize state for submission data, loading state, and error state
  const [submission, setSubmission] = useState<Submission | null>(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);
  
  // Get user information and permission checking function from useAuth hook
  const { user, hasPermission } = useAuth();
  
  // Get toast notification functions from useToast hook
  const { success, error: toastError } = useToast();
  
  // Get navigation function from useNavigate hook
  const navigate = useNavigate();
  
  /**
   * Fetches submission data for the current submissionId
   */
  const fetchSubmission = useCallback(async () => {
    setLoading(true);
    setError(null);
    
    try {
      if (!submissionId) {
        throw new Error('Submission ID is required');
      }
      
      const submissionData = await getSubmission(submissionId);
      setSubmission(submissionData);
    } catch (err: any) {
      console.error('Failed to fetch submission:', err);
      setError(`Failed to load submission. ${err.message || 'Please try again later.'}`);
      toastError(`Failed to load submission. ${err.message || 'Please try again later.'}`);
    } finally {
      setLoading(false);
    }
  }, [submissionId, toastError]);
  
  // Fetch submission data when component mounts or submissionId changes
  useEffect(() => {
    fetchSubmission();
  }, [fetchSubmission]);
  
  /**
   * Checks if the current user has permission to upload results
   */
  const checkPermission = useCallback(() => {
    // Check if user is a CRO user with appropriate role
    if (!user || !hasPermission(['cro_admin', 'cro_technician'])) {
      return false;
    }
    
    // Check if user is associated with the CRO for this submission
    if (submission && submission.cro_service?.provider !== user.organization_name) {
      return false;
    }
    
    return true;
  }, [user, hasPermission, submission]);
  
  // Check permission on submission load
  const [hasUploadPermission, setHasUploadPermission] = useState(false);
  useEffect(() => {
    setHasUploadPermission(checkPermission());
  }, [checkPermission]);
  
  /**
   * Handles completion of the results upload process
   */
  const handleResultsComplete = useCallback((resultId: string) => {
    success('Results uploaded successfully!');
    navigate(getSubmissionDetailPath(submissionId));
  }, [success, navigate, submissionId]);
  
  // Render loading state while fetching submission data
  if (loading) {
    return (
      <DashboardLayout title="Upload Results">
        <LoadingOverlay loading message="Loading submission details..." />
      </DashboardLayout>
    );
  }
  
  // Render error message if submission not found or user lacks permission
  if (error || !submission || !hasUploadPermission) {
    let errorMessage = error || 'Submission not found.';
    if (!hasUploadPermission) {
      errorMessage = 'You do not have permission to upload results for this submission.';
    }
    
    return (
      <DashboardLayout title="Upload Results">
        <Alert severity="error">{errorMessage}</Alert>
      </DashboardLayout>
    );
  }
  
  // Render page with DashboardLayout, breadcrumbs, and ResultsUploader component
  return (
    <DashboardLayout title="Upload Results">
      <Breadcrumbs aria-label="breadcrumb" sx={{ mb: 3 }}>
        <Link underline="hover" color="inherit" to={ROUTES.DASHBOARD.HOME}>
          Dashboard
        </Link>
        <Link underline="hover" color="inherit" to={ROUTES.SUBMISSIONS.LIST}>
          Submissions
        </Link>
        <Link underline="hover" color="inherit" to={getSubmissionDetailPath(submissionId)}>
          {submission.name}
        </Link>
        <Typography color="text.primary">Upload Results</Typography>
      </Breadcrumbs>
      
      <ResultsUploader 
        submissionId={submissionId} 
        onComplete={handleResultsComplete} 
      />
    </DashboardLayout>
  );
};

export default ResultsUploadPage;