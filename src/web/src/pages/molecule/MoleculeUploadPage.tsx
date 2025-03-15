import React, { useCallback } from 'react'; // react v18.0.0
import { useNavigate } from 'react-router-dom'; // react-router-dom v6.0.0
import { Box, Typography, Paper, Breadcrumbs, Link } from '@mui/material'; // @mui/material v5.0.0

import DashboardLayout from '../../components/layout/DashboardLayout';
import MoleculeUploader from '../../components/molecule/MoleculeUploader';
import { ROUTES } from '../../constants/routes';
import { MoleculeCSVProcessResult } from '../../types/molecule.types';

/**
 * Page component for uploading CSV files with molecular data
 * @returns Rendered page component
 */
const MoleculeUploadPage: React.FC = () => {
  // IE1: Initialize navigate function from useNavigate hook
  const navigate = useNavigate();

  /**
   * Handles successful CSV upload and processing completion
   * @param result - The processing result
   */
  const handleUploadComplete = useCallback((result: MoleculeCSVProcessResult) => {
    // LD1: Log the processing result for debugging
    console.log('CSV Processing Result:', result);
    // LD1: Navigate to the molecules list page to view the imported molecules
    navigate(ROUTES.MOLECULES.LIST);
    // LD1: Optionally, could add state to pass success message to the list page
  }, [navigate]);

  return (
    // LD1: Render DashboardLayout with appropriate title
    <DashboardLayout title="Upload Molecules">
      {/* LD1: Render breadcrumbs navigation */}
      <Breadcrumbs aria-label="breadcrumb" sx={{ marginBottom: 2 }}>
        <Link underline="hover" color="inherit" href={ROUTES.DASHBOARD.HOME}>
          Dashboard
        </Link>
        <Typography color="text.primary">Upload</Typography>
      </Breadcrumbs>

      {/* LD1: Render page title and description */}
      <Typography variant="h4" component="h1" gutterBottom>
        Upload Molecules
      </Typography>
      <Typography variant="body1" paragraph>
        Upload a CSV file containing molecular data to add molecules to the system.
      </Typography>

      {/* LD1: Render MoleculeUploader component with handleUploadComplete callback */}
      <Paper elevation={2} sx={{ padding: 3, marginBottom: 3 }}>
        <MoleculeUploader onUploadComplete={handleUploadComplete} />
      </Paper>

      {/* LD1: Provide information about supported file formats and requirements */}
      <Box sx={{ maxWidth: '100%', width: '100%' }}>
        <Typography variant="body2" color="textSecondary">
          Supported file format: CSV with SMILES column and property columns.
        </Typography>
        <Typography variant="body2" color="textSecondary">
          Maximum file size: 100MB.
        </Typography>
      </Box>
    </DashboardLayout>
  );
};

export default MoleculeUploadPage;