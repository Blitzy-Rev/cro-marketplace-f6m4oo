import React, { useState, useEffect, useCallback } from 'react';
import { Box, Grid, Paper, Typography, Divider, Button, Card, CardContent, CardHeader, Chip } from '@mui/material'; // @mui/material ^5.0.0
import { Assignment, CheckCircle, Pending, Timeline, Assessment } from '@mui/icons-material'; // @mui/icons-material ^5.0.0
import { useNavigate } from 'react-router-dom'; // react-router-dom ^6.0.0

import DashboardLayout from '../../components/layout/DashboardLayout';
import CROList from '../../components/cro/CROList';
import SubmissionList from '../../components/submission/SubmissionList';
import ResultsList from '../../components/results/ResultsList';
import StatusBadge from '../../components/common/StatusBadge';
import LoadingOverlay from '../../components/common/LoadingOverlay';
import { getCROServices } from '../../api/croApi';
import useAuth from '../../hooks/useAuth';
import { Submission } from '../../types/submission.types';
import { Result } from '../../types/result.types';
import { CROService } from '../../types/cro.types';

/**
 * Interface for dashboard metrics data
 */
interface DashboardMetrics {
  newSubmissions: number;
  activeProjects: number;
  pendingResults: number;
  completedThisMonth: number;
}

/**
 * Interface for MetricCard props
 */
interface MetricCardProps {
  title: string;
  count: number;
  icon: React.ReactNode;
  color?: string; // Optional color theme for the card (default: "primary.main")
}

/**
 * Main component for the CRO dashboard page
 * @returns The rendered CRO dashboard page
 */
const CRODashboardPage: React.FC = () => {
  // State for dashboard metrics, submissions, results, and loading status
  const [dashboardMetrics, setDashboardMetrics] = useState<DashboardMetrics>({
    newSubmissions: 0,
    activeProjects: 0,
    pendingResults: 0,
    completedThisMonth: 0,
  });
  const [submissions, setSubmissions] = useState<Submission[]>([]);
  const [results, setResults] = useState<Result[]>([]);
  const [loading, setLoading] = useState<boolean>(false);

  // Get current user information and permissions using useAuth hook
  const { user, hasPermission } = useAuth();

  // Initialize navigation function using useNavigate hook
  const navigate = useNavigate();

  /**
   * Fetches dashboard data including metrics, submissions, and results
   */
  const fetchDashboardData = useCallback(async () => {
    setLoading(true);
    try {
      // Mock data for dashboard metrics
      const mockMetrics: DashboardMetrics = {
        newSubmissions: 5,
        activeProjects: 12,
        pendingResults: 3,
        completedThisMonth: 7,
      };
      setDashboardMetrics(mockMetrics);

      // Mock data for submissions
      const mockSubmissions: Submission[] = [
        {
          id: 'SUB001',
          name: 'Binding Assay 1',
          cro_service_id: 'CRO001',
          description: 'Radioligand binding assay for target protein XYZ',
          specifications: {},
          status: 'PENDING_REVIEW',
          metadata: {},
          created_by: 'user123',
          created_at: '2023-09-15T10:00:00Z',
          updated_at: '2023-09-15T10:00:00Z',
          submitted_at: '2023-09-15T10:00:00Z',
          approved_at: null,
          completed_at: null,
          price: null,
          price_currency: null,
          estimated_turnaround_days: null,
          estimated_completion_date: null,
          cro_service: null,
          creator: null,
          molecules: null,
          documents: null,
          results: null,
          status_description: null,
          document_count: null,
          molecule_count: 5,
          is_editable: false,
          is_active: true,
        },
        {
          id: 'SUB002',
          name: 'ADME Panel 2',
          cro_service_id: 'CRO002',
          description: 'ADME panel for lead compound series',
          specifications: {},
          status: 'IN_PROGRESS',
          metadata: {},
          created_by: 'user456',
          created_at: '2023-09-10T14:30:00Z',
          updated_at: '2023-09-12T09:15:00Z',
          submitted_at: '2023-09-10T14:30:00Z',
          approved_at: '2023-09-11T16:00:00Z',
          completed_at: null,
          price: 5000,
          price_currency: 'USD',
          estimated_turnaround_days: 14,
          estimated_completion_date: '2023-09-24T00:00:00Z',
          cro_service: null,
          creator: null,
          molecules: null,
          documents: null,
          results: null,
          status_description: null,
          document_count: null,
          molecule_count: 12,
          is_editable: false,
          is_active: true,
        },
      ];
      setSubmissions(mockSubmissions);

      // Mock data for results
      const mockResults: Result[] = [
        {
          id: 'RES001',
          submission_id: 'SUB001',
          status: 'COMPLETED',
          protocol_used: 'Standard Protocol A',
          quality_control_passed: true,
          notes: 'Good data quality',
          metadata: {},
          properties: [],
          molecules: null,
          documents: null,
          uploaded_by: 'croUser123',
          uploaded_at: '2023-09-22T16:00:00Z',
          processed_at: '2023-09-22T17:30:00Z',
          reviewed_at: '2023-09-23T10:00:00Z',
          created_at: '2023-09-22T15:00:00Z',
          updated_at: '2023-09-23T10:00:00Z',
        },
        {
          id: 'RES002',
          submission_id: 'SUB002',
          status: 'PENDING',
          protocol_used: 'Standard Protocol B',
          quality_control_passed: null,
          notes: 'Awaiting review',
          metadata: {},
          properties: [],
          molecules: null,
          documents: null,
          uploaded_by: 'croUser456',
          uploaded_at: '2023-09-20T12:00:00Z',
          processed_at: null,
          reviewed_at: null,
          created_at: '2023-09-20T11:00:00Z',
          updated_at: '2023-09-20T12:00:00Z',
        },
      ];
      setResults(mockResults);
    } catch (error) {
      console.error('Error fetching dashboard data:', error);
    } finally {
      setLoading(false);
    }
  }, []);

  // Load dashboard data when component mounts
  useEffect(() => {
    fetchDashboardData();
  }, [fetchDashboardData]);

  // Handle submission click to navigate to submission detail page
  const handleSubmissionClick = (submission: Submission) => {
    // Navigate to submission detail page
    console.log('Submission clicked:', submission);
  };

  // Handle result click to navigate to result detail page
  const handleResultClick = (result: Result) => {
    // Navigate to result detail page
    console.log('Result clicked:', result);
  };

  return (
    <DashboardLayout title="CRO Dashboard">
      {/* Metrics cards */}
      <Grid container spacing={3} mb={3}>
        <Grid item xs={12} sm={6} md={3}>
          <MetricCard
            title="New Submissions"
            count={dashboardMetrics.newSubmissions}
            icon={<Assignment color="primary" />}
          />
        </Grid>
        <Grid item xs={12} sm={6} md={3}>
          <MetricCard
            title="Active Projects"
            count={dashboardMetrics.activeProjects}
            icon={<Timeline color="primary" />}
          />
        </Grid>
        <Grid item xs={12} sm={6} md={3}>
          <MetricCard
            title="Pending Results"
            count={dashboardMetrics.pendingResults}
            icon={<Pending color="primary" />}
          />
        </Grid>
        <Grid item xs={12} sm={6} md={3}>
          <MetricCard
            title="Completed This Month"
            count={dashboardMetrics.completedThisMonth}
            icon={<CheckCircle color="primary" />}
          />
        </Grid>
      </Grid>

      {/* New Submissions section */}
      <Paper sx={{ p: 2, mb: 3 }}>
        <Typography variant="h6" component="h2" mb={1}>
          New Submissions
        </Typography>
        <SubmissionList
          submissions={submissions}
          onSubmissionClick={handleSubmissionClick}
        />
      </Paper>

      {/* Pending Results section */}
      <Paper sx={{ p: 2 }}>
        <Typography variant="h6" component="h2" mb={1}>
          Pending Results
        </Typography>
        <ResultsList
          results={results}
          onResultSelect={handleResultClick}
        />
      </Paper>

      {/* Loading overlay */}
      {loading && <LoadingOverlay loading={loading} />}
    </DashboardLayout>
  );
};

/**
 * Component for displaying a metric card with count and label
 */
const MetricCard: React.FC<MetricCardProps> = ({ title, count, icon, color = "primary.main" }) => {
  return (
    <Card>
      <CardContent>
        <Box display="flex" alignItems="center" justifyContent="space-between">
          <Box>{icon}</Box>
          <Box textAlign="right">
            <Typography variant="h5" component="div">
              {count}
            </Typography>
            <Typography variant="subtitle2" color="textSecondary">
              {title}
            </Typography>
          </Box>
        </Box>
      </CardContent>
    </Card>
  );
};

export default CRODashboardPage;