import React, { useState, useEffect } from 'react';
import { Box, Grid, Paper, Typography, Button, Card, CardContent, CardActions, Divider, Chip, CircularProgress, IconButton } from '@mui/material'; // Material UI v5.0.0
import { useTheme } from '@mui/material/styles'; // Material UI v5.0.0
import { useNavigate } from 'react-router-dom'; // react-router-dom v6.0.0
import { UploadFile, AddCircle, Send, Refresh } from '@mui/icons-material'; // Material UI v5.0.0

import DashboardLayout from '../../components/layout/DashboardLayout';
import { useAuthContext } from '../../contexts/AuthContext';
import { USER_ROLES } from '../../constants/userRoles';
import StatusBadge from '../../components/common/StatusBadge';
import DataTable from '../../components/common/DataTable';
import { useAppDispatch, useAppSelector } from '../../store';
import { selectMolecules, fetchMolecules } from '../../features/molecule/moleculeSlice';
import { selectLibraries, fetchMyLibraries } from '../../features/library/librarySlice';
import { selectSubmissions, fetchSubmissions, fetchStatusCounts, selectStatusCounts } from '../../features/submission/submissionSlice';
import { getResultsBySubmission } from '../../api/resultApi';
import { ROUTES } from '../../constants/routes';
import { formatDate } from '../../utils/dateFormatter';

/**
 * Main dashboard page component that displays different views based on user role
 */
const DashboardPage: React.FC = () => {
  // Get authentication state using useAuthContext hook
  const { authState } = useAuthContext();

  // Get theme using useTheme hook
  const theme = useTheme();

  // Get navigation function using useNavigate hook
  const navigate = useNavigate();

  // Get Redux dispatch function using useAppDispatch hook
  const dispatch = useAppDispatch();

  // Initialize state for recent results
  const [recentResults, setRecentResults] = useState<any[]>([]);

  // Initialize state for loading indicators
  const [resultsLoading, setResultsLoading] = useState(false);

  // Select molecules, libraries, submissions, and status counts from Redux store
  const molecules = useAppSelector(selectMolecules);
  const libraries = useAppSelector(selectLibraries);
  const submissions = useAppSelector(selectSubmissions);
  const statusCounts = useAppSelector(selectStatusCounts);

  // Determine if user is a CRO user based on role
  const isCROUser = authState.user?.role === USER_ROLES.CRO_USER;

  // Function to fetch all required data for the dashboard
  const fetchDashboardData = async () => {
    try {
      // Set loading state to true
      // Dispatch actions to fetch molecules with pagination
      dispatch(fetchMolecules({ page: 1, pageSize: 5 }));
      // Dispatch actions to fetch user's libraries
      dispatch(fetchMyLibraries({ page: 1, pageSize: 5 }));
      // Dispatch actions to fetch submissions with pagination
      dispatch(fetchSubmissions({ page: 1, pageSize: 5, filter: { active_only: true } }));
      // Dispatch action to fetch submission status counts
      dispatch(fetchStatusCounts({}));
    } catch (error) {
      console.error('Error fetching dashboard data:', error);
    }
  };

  // Function to fetch recent experimental results
  const fetchRecentResults = async () => {
    try {
      setResultsLoading(true);
      // Get recent submissions with completed status
      const recentSubmissions = submissions.slice(0, 5);
      // For each submission, fetch associated results
      const resultsPromises = recentSubmissions.map(submission =>
        getResultsBySubmission(submission.id, 1, 1)
      );
      const resultsArrays = await Promise.all(resultsPromises);
      // Combine and sort results by date
      const combinedResults = resultsArrays.flatMap(result => result.items);
      combinedResults.sort((a, b) => new Date(b.uploaded_at).getTime() - new Date(a.uploaded_at).getTime());
      // Take the most recent results (up to 5)
      setRecentResults(combinedResults.slice(0, 5));
    } catch (error) {
      console.error('Error fetching recent results:', error);
    } finally {
      setResultsLoading(false);
    }
  };

  // Fetch dashboard data on component mount
  useEffect(() => {
    fetchDashboardData();
    if (authState.user?.role === USER_ROLES.PHARMA_USER) {
      fetchRecentResults();
    }
  }, [authState.user?.role, dispatch, submissions]);

  // Function to render a metric card
  const renderMetricCard = (title: string, value: number | string, isLoading: boolean) => (
    <Card>
      <CardContent>
        <Typography variant="h6" color="textSecondary" gutterBottom>
          {title}
        </Typography>
        <Typography variant="h4" component="div">
          {isLoading ? <CircularProgress size={24} /> : value}
        </Typography>
      </CardContent>
    </Card>
  );

  // Function to render a list of recent activities
  const renderRecentActivity = () => {
    const recentUploads = [];
    const recentSubmissions = submissions.slice(0, 2).map(submission => ({
      type: 'submission',
      description: `Submitted to ${submission.cro_service?.provider || 'Unknown CRO'}`,
      time: submission.created_at,
    }));
    const recentResultsData = recentResults.map(result => ({
      type: 'result',
      description: `Results received`,
      time: result.uploaded_at,
    }));
    const combinedActivity = [...recentUploads, ...recentSubmissions, ...recentResultsData];
    combinedActivity.sort((a, b) => new Date(b.time).getTime() - new Date(a.time).getTime());
    const recentActivity = combinedActivity.slice(0, 5);

    return (
      <Paper sx={{ p: 2 }}>
        <Typography variant="h6" gutterBottom>
          Recent Activity
        </Typography>
        {resultsLoading ? (
          <Box display="flex" justifyContent="center">
            <CircularProgress />
          </Box>
        ) : recentActivity.length > 0 ? (
          recentActivity.map((activity, index) => (
            <Box key={index} sx={{ display: 'flex', alignItems: 'center', mb: 1 }}>
              <Typography variant="body2">
                {activity.description} - {formatDate(activity.time)}
              </Typography>
            </Box>
          ))
        ) : (
          <Typography variant="body2" color="textSecondary">
            No recent activity
          </Typography>
        )}
      </Paper>
    );
  };

  // Function to render quick action buttons
  const renderQuickActions = () => (
    <Paper sx={{ p: 2 }}>
      <Typography variant="h6" gutterBottom>
        Quick Actions
      </Typography>
      {isCROUser ? (
        <>
          <Button variant="contained" startIcon={<UploadFile />} onClick={() => navigate(ROUTES.RESULTS.UPLOAD)}>
            Upload Results
          </Button>
        </>
      ) : (
        <>
          <Button variant="contained" startIcon={<UploadFile />} onClick={() => navigate(ROUTES.MOLECULE_UPLOAD)}>
            Upload Molecules
          </Button>
          <Button variant="contained" startIcon={<AddCircle />} onClick={() => navigate(ROUTES.LIBRARY_CREATE)}>
            Create Library
          </Button>
          <Button variant="contained" startIcon={<Send />} onClick={() => navigate(ROUTES.SUBMISSION_CREATE)}>
            Submit to CRO
          </Button>
        </>
      )}
    </Paper>
  );

  // Function to render the dashboard view for pharmaceutical users
  const renderPharmaUserDashboard = () => (
    <Grid container spacing={3}>
      <Grid item xs={12} md={4}>
        {renderMetricCard('Active Molecules', molecules.length, false)}
      </Grid>
      <Grid item xs={12} md={4}>
        {renderMetricCard('Libraries', libraries.length, false)}
      </Grid>
      <Grid item xs={12} md={4}>
        {renderMetricCard('Pending Submissions', statusCounts.find(s => s.status === SubmissionStatus.SUBMITTED)?.count || 0, false)}
      </Grid>
      <Grid item xs={12} md={6}>
        {renderRecentActivity()}
      </Grid>
      <Grid item xs={12} md={6}>
        {renderQuickActions()}
      </Grid>
    </Grid>
  );

  // Function to render the dashboard view for CRO users
  const renderCROUserDashboard = () => (
    <Grid container spacing={3}>
      <Grid item xs={12} md={3}>
        {renderMetricCard('New Submissions', statusCounts.find(s => s.status === SubmissionStatus.SUBMITTED)?.count || 0, false)}
      </Grid>
      <Grid item xs={12} md={3}>
        {renderMetricCard('Active Projects', statusCounts.find(s => s.status === SubmissionStatus.IN_PROGRESS)?.count || 0, false)}
      </Grid>
      <Grid item xs={12} md={3}>
        {renderMetricCard('Pending Results', statusCounts.find(s => s.status === SubmissionStatus.RESULTS_UPLOADED)?.count || 0, false)}
      </Grid>
      <Grid item xs={12} md={3}>
        {renderMetricCard('Completed This Month', 10, false)}
      </Grid>
      <Grid item xs={12} md={6}>
        {renderNewSubmissionsTable()}
      </Grid>
      <Grid item xs={12} md={6}>
        {renderPendingResultsTable()}
      </Grid>
      <Grid item xs={12}>
        {renderQuickActions()}
      </Grid>
    </Grid>
  );

  // Function to render a table of new submissions for CRO users
  const renderNewSubmissionsTable = () => {
    const newSubmissions = submissions.filter(submission => submission.status === SubmissionStatus.SUBMITTED);

    const columns = [
      { id: 'id', label: 'ID' },
      { id: 'cro_service.name', label: 'Service Type' },
      { id: 'molecule_count', label: 'Molecules' },
      { id: 'created_at', label: 'Received' },
    ];

    return (
      <Paper sx={{ p: 2 }}>
        <Typography variant="h6" gutterBottom>
          New Submissions
        </Typography>
        {newSubmissions.length > 0 ? (
          <DataTable
            columns={columns}
            data={newSubmissions}
            loading={false}
          />
        ) : (
          <Typography variant="body2" color="textSecondary">
            No new submissions
          </Typography>
        )}
      </Paper>
    );
  };

  // Function to render a table of submissions pending results upload
  const renderPendingResultsTable = () => {
    const pendingResults = submissions.filter(submission => submission.status === SubmissionStatus.IN_PROGRESS);

    const columns = [
      { id: 'id', label: 'ID' },
      { id: 'cro_service.name', label: 'Service Type' },
      { id: 'estimated_completion_date', label: 'Due Date' },
      { id: 'status', label: 'Status' },
    ];

    return (
      <Paper sx={{ p: 2 }}>
        <Typography variant="h6" gutterBottom>
          Pending Results
        </Typography>
        {pendingResults.length > 0 ? (
          <DataTable
            columns={columns}
            data={pendingResults}
            loading={false}
          />
        ) : (
          <Typography variant="body2" color="textSecondary">
            No pending results
          </Typography>
        )}
      </Paper>
    );
  };

  // Render different dashboard views based on user role
  return (
    <DashboardLayout title="Dashboard">
      {isCROUser ? renderCROUserDashboard() : renderPharmaUserDashboard()}
    </DashboardLayout>
  );
};

export default DashboardPage;