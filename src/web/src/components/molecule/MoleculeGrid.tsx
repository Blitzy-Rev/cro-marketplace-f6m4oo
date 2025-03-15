import React, { useState, useEffect, useMemo, useCallback } from 'react'; // react v18.0.0
import { Grid, Box, Typography, CircularProgress } from '@mui/material'; // ^5.0.0
import { styled } from '@mui/material/styles'; // ^5.0.0

import MoleculeCard from './MoleculeCard';
import { Molecule } from '../../types/molecule.types';
import Pagination from '../common/Pagination';
import { useAppDispatch, useAppSelector } from '../../store';
import { selectSelectedMolecules, setSelectedMolecules } from '../../features/molecule/moleculeSlice';

/**
 * Interface for the MoleculeGrid component properties
 */
interface MoleculeGridProps {
  /** Array of molecule data to display */
  molecules: Molecule[];
  /** Whether the grid is in loading state */
  loading?: boolean;
  /** Callback when a molecule card is clicked */
  onMoleculeClick?: (molecule: Molecule) => void;
  /** Whether to enable pagination */
  pagination?: boolean;
  /** Total number of molecules (for pagination) */
  totalCount?: number;
  /** Current page number (for pagination) */
  currentPage?: number;
  /** Number of molecules per page (for pagination) */
  pageSize?: number;
  /** Callback when page changes */
  onPageChange?: (page: number) => void;
  /** Callback when page size changes */
  onPageSizeChange?: (pageSize: number) => void;
  /** Whether molecules can be selected with checkboxes */
  selectable?: boolean;
  /** Callback when selection changes */
  onSelectionChange?: (selected: string[]) => void;
  /** Property names to highlight on the cards */
  highlightProperties?: string[];
  /** Additional CSS class name */
  className?: string;
}

/**
 * Styled container for the molecule grid
 */
const GridContainer = styled(Box)(({ theme }) => ({
  width: '100%',
  padding: theme.spacing(2),
  position: 'relative'
}));

/**
 * Overlay component for displaying loading state
 */
const LoadingOverlay = styled(Box)(({ theme }) => ({
  display: 'flex',
  justifyContent: 'center',
  alignItems: 'center',
  position: 'absolute',
  top: '0',
  left: '0',
  right: '0',
  bottom: '0',
  backgroundColor: 'rgba(255, 255, 255, 0.7)',
  zIndex: '1'
}));

/**
 * Component for displaying empty state message
 */
const EmptyMessage = styled(Typography)(({ theme }) => ({
  padding: theme.spacing(2),
  textAlign: 'center',
  color: theme.palette.text.secondary
}));

/**
 * Container for pagination controls
 */
const PaginationContainer = styled(Box)(({ theme }) => ({
  display: 'flex',
  justifyContent: 'center',
  padding: theme.spacing(2),
  marginTop: theme.spacing(2)
}));

/**
 * A component that displays molecules in a grid layout with selection capabilities
 */
const MoleculeGrid: React.FC<MoleculeGridProps> = ({
  molecules,
  loading = false,
  onMoleculeClick,
  pagination = true,
  totalCount,
  currentPage = 1,
  pageSize = 12,
  onPageChange,
  onPageSizeChange,
  selectable = false,
  onSelectionChange,
  highlightProperties,
  className
}) => {
  // Get selected molecules from Redux state using useAppSelector and selectSelectedMolecules
  const selectedMolecules = useAppSelector(selectSelectedMolecules);

  // Get dispatch function using useAppDispatch
  const dispatch = useAppDispatch();

  // Handle molecule selection by updating Redux state with setSelectedMolecules
  const handleMoleculeSelect = useCallback((molecule: Molecule, selected: boolean) => {
    const moleculeId = molecule.id;
    let newSelection: string[];

    if (selected) {
      newSelection = [...selectedMolecules, moleculeId];
    } else {
      newSelection = selectedMolecules.filter(id => id !== moleculeId);
    }

    dispatch(setSelectedMolecules(newSelection));

    if (onSelectionChange) {
      onSelectionChange(newSelection);
    }
  }, [dispatch, selectedMolecules, onSelectionChange]);

  // Handle molecule click to navigate to molecule detail page
  const handleCardClick = useCallback((molecule: Molecule) => {
    if (onMoleculeClick) {
      onMoleculeClick(molecule);
    }
  }, [onMoleculeClick]);

  return (
    <GridContainer className={className}>
      {/* Render loading indicator when loading is true */}
      {loading && (
        <LoadingOverlay>
          <CircularProgress />
        </LoadingOverlay>
      )}

      {/* Render empty message when no molecules are available */}
      {!loading && molecules.length === 0 && (
        <EmptyMessage>No molecules found</EmptyMessage>
      )}

      {/* Render Grid container with MoleculeCard components for each molecule */}
      {!loading && molecules.length > 0 && (
        <Grid container spacing={2} justifyContent="flex-start">
          {molecules.map((molecule) => (
            <Grid item key={molecule.id} xs={12} sm={6} md={4} lg={3}>
              <MoleculeCard
                molecule={molecule}
                selected={selectable && selectedMolecules.includes(molecule.id)}
                onSelect={selectable ? handleMoleculeSelect : undefined}
                onClick={handleCardClick}
                showCheckbox={selectable}
                highlightProperties={highlightProperties}
              />
            </Grid>
          ))}
        </Grid>
      )}

      {/* Render pagination component if pagination is enabled */}
      {pagination && totalCount && (
        <PaginationContainer>
          <Pagination
            page={currentPage}
            pageSize={pageSize}
            totalCount={totalCount}
            onPageChange={onPageChange}
            onPageSizeChange={onPageSizeChange}
          />
        </PaginationContainer>
      )}
    </GridContainer>
  );
};

export default MoleculeGrid;