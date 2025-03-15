import React, { useState, useEffect, useCallback } from 'react';
import { useParams, useNavigate } from 'react-router-dom'; // version ^6.0.0
import { Box, Grid, Paper, Typography, Divider, Button, Chip, Tabs, Tab, CircularProgress } from '@mui/material'; // version ^5.0.0
import { styled } from '@mui/material/styles'; // version ^5.0.0
import { AddCircleOutline, Edit, Flag, Send } from '@mui/icons-material'; // version ^5.0.0

import {
  Molecule,
  MoleculeProperty,
  PropertySource,
  MoleculeStatus
} from '../../types/molecule.types';
import MoleculeViewer from './MoleculeViewer';
import PropertyTable from './PropertyTable';
import { getMolecule, getMoleculePredictions } from '../../api/moleculeApi';
import { getSubmissionsByMolecule } from '../../api/submissionApi';
import useToast from '../../hooks/useToast';

/**
 * Interface for TabPanel props
 */
interface TabPanelProps {
  children?: React.ReactNode;
  value: number;
  index: number;
}

/**
 * Component that renders content for a specific tab
 */
function TabPanel(props: TabPanelProps) {
  const { children, value, index, ...other } = props;

  return (
    <div
      role="tabpanel"
      hidden={value !== index}
      id={`molecule-tabpanel-${index}`}
      aria-labelledby={`molecule-tab-${index}`}
      {...other}
    >
      {value === index && (
        <Box sx={{ p: 3 }}>
          <Typography component={'span'}>{children}</Typography>
        </Box>
      )}
    </div>
  );
}

/**
 * Styled component for sections in the molecule detail view
 */
const DetailSection = styled(Paper)(({ theme }) => ({
  padding: theme.spacing(3),
  marginBottom: theme.spacing(3)
}));

/**
 * Styled component for section titles
 */
const SectionTitle = styled(Typography)({
  marginBottom: '16px',
  fontWeight: 500
});

/**
 * Styled component for action buttons
 */
const ActionButton = styled(Button)({
  margin: '8px'
});

/**
 * Styled component for status chips
 */
const StatusChip = styled(Chip)({
  marginLeft: '8px'
});

/**
 * Component that displays detailed information about a molecule
 */
export default function MoleculeDetail() {
  // Extract molecule ID from URL parameters
  const { id } = useParams<{ id: string }>();

  // Initialize state for molecule data, loading status, error status, active tab, and predictions
  const [molecule, setMolecule] = useState<Molecule | null>(null);
  const [loading, setLoading] = useState<boolean>(true);
  const [error, setError] = useState<boolean>(false);
  const [activeTab, setActiveTab] = useState<number>(0);
  const [predictions, setPredictions] = useState<any[]>([]);
  const [submissions, setSubmissions] = useState<any[]>([]);

  // Initialize toast notification hook
  const toast = useToast();

  // Create a navigate function for routing
  const navigate = useNavigate();

  // Fetch molecule data when component mounts or ID changes
  useEffect(() => {
    if (!id) return;

    const fetchMoleculeData = async () => {
      setLoading(true);
      setError(false);
      try {
        const response = await getMolecule(id);
        setMolecule(response);
      } catch (e: any) {
        setError(true);
        toast.error(toast.formatError(e));
      } finally {
        setLoading(false);
      }
    };

    fetchMoleculeData();
  }, [id, toast]);

  // Fetch molecule predictions when molecule data is loaded
  useEffect(() => {
    if (!molecule) return;

    const fetchPredictions = async () => {
      try {
        const response = await getMoleculePredictions(molecule.id);
        setPredictions(response);
      } catch (e: any) {
        toast.error(toast.formatError(e));
      }
    };

    fetchPredictions();
  }, [molecule, toast]);

  // Fetch submissions related to the molecule when molecule data is loaded
  useEffect(() => {
    if (!molecule) return;

    const fetchSubmissions = async () => {
      try {
        const response = await getSubmissionsByMolecule(molecule.id);
        setSubmissions(response.items);
      } catch (e: any) {
        toast.error(toast.formatError(e));
      }
    };

    fetchSubmissions();
  }, [molecule, toast]);

  // Handle tab change function for switching between tabs
  const handleTabChange = (event: React.SyntheticEvent, newValue: number) => {
    setActiveTab(newValue);
  };

  // Implement handleSubmitToCRO function to navigate to submission form
  const handleSubmitToCRO = useCallback(() => {
    if (molecule) {
      navigate(`/submissions/create?moleculeId=${molecule.id}`);
    }
  }, [molecule, navigate]);

  // Implement handleAddToLibrary function to add molecule to a library
  const handleAddToLibrary = useCallback(() => {
    // TODO: Implement add to library functionality
    toast.info('Add to library functionality is not yet implemented');
  }, [toast]);

  // Implement handleEditProperties function to edit molecule properties
  const handleEditProperties = useCallback(() => {
    // TODO: Implement edit properties functionality
    toast.info('Edit properties functionality is not yet implemented');
  }, [toast]);

  // Implement handleAddFlag function to flag the molecule
  const handleAddFlag = useCallback(() => {
    // TODO: Implement add flag functionality
    toast.info('Add flag functionality is not yet implemented');
  }, [toast]);

  // Render loading state while data is being fetched
  if (loading) {
    return (
      <Box display="flex" justifyContent="center" alignItems="center" height="50vh">
        <CircularProgress />
      </Box>
    );
  }

  // Render error state if data fetching fails
  if (error) {
    return (
      <Box display="flex" justifyContent="center" alignItems="center" height="50vh">
        <Typography variant="h6" color="error">
          Failed to load molecule details.
        </Typography>
      </Box>
    );
  }

  // Render molecule details with structure visualization, properties, predictions, and history
  return (
    <Box>
      <Grid container spacing={3}>
        <Grid item xs={12}>
          <Box display="flex" justifyContent="space-between" alignItems="center">
            <Typography variant="h4" component="h1">
              Molecule Detail: {molecule?.id}
            </Typography>
            <Button variant="outlined" onClick={() => navigate(-1)}>
              Back to Library
            </Button>
          </Box>
        </Grid>

        <Grid item xs={12} md={6}>
          <DetailSection>
            <SectionTitle variant="h6" component="h2">
              Structure
            </SectionTitle>
            {molecule?.smiles && (
              <MoleculeViewer smiles={molecule.smiles} width="100%" height={400} showControls />
            )}
          </DetailSection>
        </Grid>

        <Grid item xs={12} md={6}>
          <DetailSection>
            <SectionTitle variant="h6" component="h2">
              Properties
              {molecule?.status && (
                <StatusChip label={molecule.status} color="primary" size="small" />
              )}
            </SectionTitle>
            <PropertyTable properties={molecule?.properties || []} />
          </DetailSection>
        </Grid>
      </Grid>

      <DetailSection>
        <Box sx={{ borderBottom: 1, borderColor: 'divider' }}>
          <Tabs value={activeTab} onChange={handleTabChange} aria-label="molecule detail tabs">
            <Tab label="Properties" id="molecule-tab-0" aria-controls="molecule-tabpanel-0" />
            <Tab label="Predictions" id="molecule-tab-1" aria-controls="molecule-tabpanel-1" />
            <Tab label="History & Status" id="molecule-tab-2" aria-controls="molecule-tabpanel-2" />
          </Tabs>
        </Box>
        <TabPanel value={activeTab} index={0}>
          <PropertyTable properties={molecule?.properties || []} />
        </TabPanel>
        <TabPanel value={activeTab} index={1}>
          {predictions && predictions.length > 0 ? (
            <PropertyTable properties={predictions} showSource showConfidence />
          ) : (
            <Typography>No predictions available for this molecule.</Typography>
          )}
        </TabPanel>
        <TabPanel value={activeTab} index={2}>
          <Typography>
            <strong>Status:</strong> {molecule?.status}
            <br />
            <strong>Created At:</strong> {molecule?.created_at}
            <br />
            <strong>Updated At:</strong> {molecule?.updated_at}
            <br />
            <strong>Submissions:</strong>
            {submissions && submissions.length > 0 ? (
              <ul>
                {submissions.map((submission: any) => (
                  <li key={submission.id}>
                    {submission.name} - {submission.status}
                  </li>
                ))}
              </ul>
            ) : (
              'No submissions found for this molecule.'
            )}
          </Typography>
        </TabPanel>
      </DetailSection>

      <Box mt={3}>
        <ActionButton variant="outlined" size="small" startIcon={<Edit />} onClick={handleEditProperties}>
          Edit Properties
        </ActionButton>
        <ActionButton variant="outlined" size="small" startIcon={<AddCircleOutline />} onClick={handleAddToLibrary}>
          Add to Library
        </ActionButton>
        <ActionButton variant="outlined" size="small" startIcon={<Flag />} onClick={handleAddFlag}>
          Add Flag
        </ActionButton>
        <ActionButton variant="contained" size="small" startIcon={<Send />} onClick={handleSubmitToCRO}>
          Submit to CRO
        </ActionButton>
      </Box>
    </Box>
  );
}