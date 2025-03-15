import React from 'react'; // react v18.0.0
import { useParams, useNavigate } from 'react-router-dom'; // react-router-dom v6.4.0
import { Box, Container, Paper } from '@mui/material'; // @mui/material v5.0.0
import { Helmet } from 'react-helmet-async'; // react-helmet-async v1.3.0

import ResultsDetail from '../../components/results/ResultsDetail';
import DashboardLayout from '../../components/layout/DashboardLayout';
import { ROUTES } from '../../constants/routes';
import useToast from '../../hooks/useToast';

/**
 * Page component that displays detailed information about an experimental result
 */
const ResultsDetailPage: React.FC = () => {
  // Extract result ID from URL parameters using useParams hook
  const { id } = useParams<{ id: string }>();

  // Initialize navigation hook for routing
  const navigate = useNavigate();

  // Initialize toast notification hook for displaying messages
  const toast = useToast();

  // Set up page title and metadata using Helmet
  return (
    <>
      <Helmet>
        <title>Results Detail - Molecular Data Platform</title>
        <meta name="description" content="View detailed information about experimental results" />
      </Helmet>

      {/* Render the DashboardLayout component as the page container */}
      <DashboardLayout title="Results Detail">
        {/* Render the ResultsDetail component inside the layout, passing the result ID from URL params */}
        {id ? (
          <ResultsDetail resultId={id} />
        ) : (
          <Box sx={{ p: 3 }}>
            {/* Handle any errors or loading states at the page level if needed */}
            <p>Invalid result ID.</p>
          </Box>
        )}
      </DashboardLayout>
    </>
  );
};

export default ResultsDetailPage;