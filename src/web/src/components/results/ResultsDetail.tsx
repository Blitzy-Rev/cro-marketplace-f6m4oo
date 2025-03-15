import React, { useState, useEffect, useMemo } from 'react'; // react v18.0.0
import { useParams, useNavigate } from 'react-router-dom'; // react-router-dom v6.4.0
import {
  Box,
  Paper,
  Typography,
  Tabs,
  Tab,
  Button,
  Divider,
  Grid,
  Chip,
  CircularProgress,
} from '@mui/material'; // @mui/material v5.0.0
import {
  ArrowBack,
  Download,
  BarChart,
  TableChart,
  Science,
  Description,
  Assignment
} from '@mui/icons-material'; // @mui/icons-material v5.0.0

import {
  Result,
  ResultStatus,
  ResultProperty,
} from '../../types/result.types';
import { Submission } from '../../types/submission.types';
import { Document } from '../../types/document.types';
import { Molecule } from '../../types/molecule.types';
import { ROUTES } from '../../constants/routes';
import TabPanel, { a11yProps } from '../common/TabPanel';
import StatusBadge from '../common/StatusBadge';
import ResultsTable from './ResultsTable';
import ResultsVisualizer from './ResultsVisualizer';
import MoleculeTable from '../molecule/MoleculeTable';
import DocumentList from '../document/DocumentList';
import { formatDateTime } from '../../utils/dateFormatter';
import { getResult, downloadResultData, reviewResult } from '../../api/resultApi';
import { getSubmission } from '../../api/submissionApi';
import useToast from '../../hooks/useToast';
import { styled } from '@mui/material/styles';

// Styled components
const HeaderContainer = styled(Box)({
  display: 'flex',
  justifyContent: 'space-between',
  alignItems: 'center',
  marginBottom: (theme) => theme.spacing(3),
});

const HeaderActions = styled(Box)({
  display: 'flex',
  gap: (theme) => theme.spacing(2),
});

const ContentContainer = styled(Box)({
  marginTop: (theme) => theme.spacing(2),
});

const MetadataGrid = styled(Grid)({
  marginTop: (theme) => theme.spacing(2),
  marginBottom: (theme) => theme.spacing(3),
});

const MetadataItem = styled(Grid)({
  display: 'flex',
  flexDirection: 'column',
});

const PropertyTable = styled(Box)({
  width: '100%',
  borderCollapse: 'collapse',
  marginTop: (theme) => theme.spacing(2),
  marginBottom: (theme) => theme.spacing(2),
  '& th, & td': {
    padding: (theme) => theme.spacing(1, 2),
    borderBottom: '1px solid',
    borderColor: (theme) => theme.palette.divider,
    textAlign: 'left',
  },
  '& th': {
    backgroundColor: (theme) => theme.palette.action.hover,
  },
});

interface ResultsDetailProps {
  className?: string;
}

/**
 * Component that displays detailed information about an experimental result
 */
const ResultsDetail: React.FC<ResultsDetailProps> = ({ className }) => {
  // Extract result ID from URL parameters
  const { id } = useParams<{ id: string }>();
  
  // Initialize state for result data, submission data, loading state, and active tab
  const [result, setResult] = useState<Result | null>(null);
  const [submission, setSubmission] = useState<Submission | null>(null);
  const [loading, setLoading] = useState<boolean>(true);
  const [activeTab, setActiveTab] = useState<number>(0); // 0: Overview, 1: Visualization, 2: Molecules, 3: Documents
  
  // Initialize navigation hook for routing
  const navigate = useNavigate();
  
  // Initialize toast notification hook
  const toast = useToast();

  // Fetch result data when component mounts or result ID changes
  useEffect(() => {
    const fetchResultData = async () => {
      if (!id) {
        toast.error('Result ID is missing');
        setLoading(false);
        return;
      }

      setLoading(true);
      try {
        const resultData = await getResult(id);
        setResult(resultData);
      } catch (err) {
        toast.error(`Failed to fetch result: ${toast.formatError(err)}`);
      } finally {
        setLoading(false);
      }
    };

    fetchResultData();
  }, [id, toast]);

  // Fetch associated submission data when result data is loaded
  useEffect(() => {
    const fetchSubmissionData = async () => {
      if (result?.submission_id) {
        try {
          const submissionData = await getSubmission(result.submission_id);
          setSubmission(submissionData);
        } catch (err) {
          toast.error(`Failed to fetch submission: ${toast.formatError(err)}`);
        }
      }
    };

    fetchSubmissionData();
  }, [result, toast]);

  // Handle tab change to switch between Overview, Visualization, Molecules, and Documents views
  const handleTabChange = (event: React.SyntheticEvent, newValue: number) => {
    setActiveTab(newValue);
  };

  // Handle download action to download result data as CSV
  const handleDownload = async () => {
    if (!result) {
      toast.error('No result to download');
      return;
    }

    try {
      await downloadResultData(result.id, `result-${result.id}.csv`);
      toast.success('Result data downloaded successfully');
    } catch (err) {
      toast.error(`Failed to download result data: ${toast.formatError(err)}`);
    }
  };

  // Handle apply to molecules action to integrate experimental results with molecule data
  const handleApplyToMolecules = async () => {
    if (!result) {
      toast.error('No result to apply');
      return;
    }

    try {
      // For this implementation, we'll use a simplified review request with default values
      const reviewRequest = {
        result_id: result.id,
        apply_to_molecules: true,
        notes: 'Applying results to molecules'
      };

      await reviewResult(reviewRequest);
      toast.success('Results applied to molecules successfully');
    } catch (err) {
      toast.error(`Failed to apply results to molecules: ${toast.formatError(err)}`);
    }
  };

  // Handle navigation back to results list
  const handleBackToList = () => {
    navigate(ROUTES.RESULTS.LIST);
  };

  // Render loading state when data is being fetched
  if (loading) {
    return (
      <Box sx={{ display: 'flex', justifyContent: 'center', alignItems: 'center', height: '200px' }}>
        <CircularProgress />
      </Box>
    );
  }

  // Render error state if result cannot be found
  if (!result) {
    return (
      <Box sx={{ p: 3 }}>
        <Typography variant="h6" color="error">
          Result not found
        </Typography>
      </Box>
    );
  }

  // Render header with result ID, status badge, and action buttons
  return (
    <Box className={className}>
      <HeaderContainer>
        <Box sx={{ display: 'flex', alignItems: 'center' }}>
          <Button startIcon={<ArrowBack />} onClick={handleBackToList}>
            Back to Results
          </Button>
          <Typography variant="h6" sx={{ ml: 2 }}>
            Result: {result.id}
          </Typography>
        </Box>
        <HeaderActions>
          <StatusBadge status={result.status} />
          <Button startIcon={<Download />} onClick={handleDownload}>
            Download
          </Button>
          <Button startIcon={<Assignment />} onClick={handleApplyToMolecules}>
            Apply to Molecules
          </Button>
        </HeaderActions>
      </HeaderContainer>

      {/* Render tabs for different views of the result data */}
      <Paper elevation={1} sx={{ width: '100%', bgcolor: 'background.paper' }}>
        <Tabs
          value={activeTab}
          onChange={handleTabChange}
          aria-label="result data tabs"
          indicatorColor="primary"
          textColor="primary"
        >
          <Tab label="Overview" {...a11yProps(0)} icon={<Description />} iconPosition="start" />
          <Tab label="Visualization" {...a11yProps(1)} icon={<BarChart />} iconPosition="start" />
          <Tab label="Molecules" {...a11yProps(2)} icon={<Science />} iconPosition="start" />
          <Tab label="Documents" {...a11yProps(3)} icon={<TableChart />} iconPosition="start" />
        </Tabs>
      </Paper>

      <ContentContainer>
        {/* Render Overview tab with result metadata, protocol information, and properties */}
        <TabPanel value={activeTab} index={0}>
          <Typography variant="h6" gutterBottom>
            Result Information
          </Typography>
          <MetadataGrid container spacing={2}>
            <MetadataItem item xs={12} sm={6} md={4}>
              <Typography variant="subtitle2">Submission</Typography>
              <Typography>{submission?.name || 'N/A'}</Typography>
            </MetadataItem>
            <MetadataItem item xs={12} sm={6} md={4}>
              <Typography variant="subtitle2">Protocol Used</Typography>
              <Typography>{result.protocol_used || 'N/A'}</Typography>
            </MetadataItem>
            <MetadataItem item xs={12} sm={6} md={4}>
              <Typography variant="subtitle2">Uploaded At</Typography>
              <Typography>{formatDateTime(result.uploaded_at)}</Typography>
            </MetadataItem>
          </MetadataGrid>
          <Divider sx={{ mb: 3 }} />
          <Typography variant="h6" gutterBottom>
            Properties
          </Typography>
          <PropertyTable>
            <thead>
              <tr>
                <th>Molecule ID</th>
                <th>Name</th>
                <th>Value</th>
                <th>Units</th>
              </tr>
            </thead>
            <tbody>
              {result.properties.map((property) => (
                <tr key={`${result.id}-${property.molecule_id}-${property.name}`}>
                  <td>{property.molecule_id}</td>
                  <td>{property.name}</td>
                  <td>{property.value}</td>
                  <td>{property.units || 'N/A'}</td>
                </tr>
              ))}
            </tbody>
          </PropertyTable>
        </TabPanel>

        {/* Render Visualization tab with ResultsVisualizer component */}
        <TabPanel value={activeTab} index={1}>
          <ResultsVisualizer result={result} />
        </TabPanel>

        {/* Render Molecules tab with MoleculeTable component showing molecules in the result */}
        <TabPanel value={activeTab} index={2}>
          <MoleculeTable molecules={result.molecules || []} />
        </TabPanel>

        {/* Render Documents tab with DocumentList component showing related documents */}
        <TabPanel value={activeTab} index={3}>
          <DocumentList documents={result.documents} />
        </TabPanel>
      </ContentContainer>
    </Box>
  );
};

export default ResultsDetail;