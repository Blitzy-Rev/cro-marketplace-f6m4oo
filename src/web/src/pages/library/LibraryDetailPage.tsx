import React, { useState, useEffect } from 'react'; // react ^18.0.0
import { useParams, useNavigate } from 'react-router-dom'; // react-router-dom ^6.0.0
import { useDispatch, useSelector } from 'react-redux'; // react-redux ^8.0.0
import {
  Box,
  Typography,
  Breadcrumbs,
  Link
} from '@mui/material'; // @mui/material ^5.0.0

import LibraryDetail from '../../components/library/LibraryDetail';
import DashboardLayout from '../../components/layout/DashboardLayout';
import LoadingOverlay from '../../components/common/LoadingOverlay';
import {
  fetchLibraryWithMolecules,
  selectCurrentLibrary,
  selectLibraryLoading
} from '../../features/library/librarySlice';
import { ROUTES } from '../../constants/routes';
import useToast from '../../hooks/useToast';

/**
 * Page component that displays detailed information about a molecule library
 */
const LibraryDetailPage: React.FC = () => {
  // Get libraryId from URL parameters using useParams hook
  const { id: libraryId } = useParams<{ id: string }>();

  // Get navigate function from useNavigate hook
  const navigate = useNavigate();

  // Get dispatch function from useDispatch hook
  const dispatch = useDispatch();

  // Get toast notification function from useToast hook
  const toast = useToast();

  // Get library data and loading state from Redux store using useSelector
  const library = useSelector(selectCurrentLibrary);
  const loading = useSelector(selectLibraryLoading);

  // Use useEffect to fetch library data when component mounts or libraryId changes
  useEffect(() => {
    if (libraryId) {
      dispatch(fetchLibraryWithMolecules({
        id: libraryId,
        pagination: {
          page: 1,
          page_size: 10,
          sort_by: null,
          sort_order: null
        }
      })).catch((error) => {
        toast.error(toast.formatError(error));
      });
    }
  }, [dispatch, libraryId, toast]);

  // Define handleBack function to navigate back to libraries list
  const handleBack = () => {
    navigate(ROUTES.LIBRARIES.LIST);
  };

  return (
    <DashboardLayout title={library?.name}>
      <Breadcrumbs aria-label="breadcrumb">
        <Link underline="hover" color="inherit" onClick={handleBack} style={{ cursor: 'pointer' }}>
          Libraries
        </Link>
        <Typography color="text.primary">{library?.name}</Typography>
      </Breadcrumbs>

      <LoadingOverlay loading={loading}>
        {library ? (
          <LibraryDetail
            libraryId={libraryId}
            onBack={handleBack}
          />
        ) : (
          <Box>
            <Typography variant="h6">Library not found</Typography>
          </Box>
        )}
      </LoadingOverlay>
    </DashboardLayout>
  );
};

export default LibraryDetailPage;