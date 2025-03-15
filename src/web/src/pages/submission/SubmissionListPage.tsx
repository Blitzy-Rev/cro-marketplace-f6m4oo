import React, { useCallback } from 'react'; // react ^18.0.0
import { useState, useEffect } from 'react'; // react ^18.0.0
import { useNavigate } from 'react-router-dom'; // react-router-dom ^6.4.0
import { Box, Button, Typography } from '@mui/material'; // @mui/material ^5.0.0
import { Add } from '@mui/icons-material'; // @mui/icons-material ^5.0.0

// Internal components
import DashboardLayout from '../../components/layout/DashboardLayout';
import SubmissionList from '../../components/submission/SubmissionList';

// Types
import { Submission } from '../../types/submission.types';
import { ROUTES } from '../../constants/routes';
import useAuth from '../../hooks/useAuth';
import { CRO_ROLES } from '../../constants/userRoles';

/**
 * Main component for the submission list page
 */
const SubmissionListPage: React.FC = () => {
  // Initialize navigate function from useNavigate hook
  const navigate = useNavigate();

  // Get current user information using useAuth hook
  const { user } = useAuth();

  // Define handleSubmissionClick function to navigate to submission detail page
  const handleSubmissionClick = useCallback((submission: Submission) => {
    navigate(ROUTES.generatePath(ROUTES.SUBMISSIONS.DETAIL, { id: submission.id }));
  }, [navigate]);

  // Define handleCreateSubmission function to navigate to submission form page
  const handleCreateSubmission = useCallback(() => {
    navigate(ROUTES.SUBMISSIONS.CREATE);
  }, [navigate]);

  // Determine if user is a CRO user by checking role against CRO_ROLES
  const isCROUser = user && CRO_ROLES.includes(user.role);

  return (
    <DashboardLayout title="CRO Submissions">
      {/* Render page header with title and create button (if not CRO user) */}
      <Box display="flex" justifyContent="space-between" alignItems="center" mb={2}>
        <Typography variant="h4" component="h1">
          CRO Submissions
        </Typography>
        {!isCROUser && (
          <Button
            variant="contained"
            startIcon={<Add />}
            onClick={handleCreateSubmission}
          >
            Create Submission
          </Button>
        )}
      </Box>

      {/* Render SubmissionList component with handleSubmissionClick callback */}
      <SubmissionList onSubmissionClick={handleSubmissionClick} />
    </DashboardLayout>
  );
};

export default SubmissionListPage;