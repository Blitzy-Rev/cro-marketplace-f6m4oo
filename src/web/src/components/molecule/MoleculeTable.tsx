import React, { useState, useMemo, useCallback, useEffect } from 'react'; // react ^18.0.0
import {
  Box,
  Tooltip,
  IconButton
} from '@mui/material'; // @mui/material ^5.0.0
import { styled } from '@mui/material/styles'; // @mui/material/styles ^5.0.0
import {
  Visibility,
  VisibilityOff,
  Edit,
  Delete,
  AddToPhotos
} from '@mui/icons-material'; // @mui/icons-material ^5.0.0
import DataTable from '../common/DataTable';
import MoleculeViewer from './MoleculeViewer';
import StatusBadge from '../common/StatusBadge';
import {
  Molecule,
  MoleculeStatus,
  MoleculeFilter
} from '../../types/molecule.types';
import {
  useAppDispatch,
  useAppSelector
} from '../../store';
import {
  selectSelectedMolecules,
  setSelectedMolecules
} from '../../features/molecule/moleculeSlice';

/**
 * Interface defining the properties for the MoleculeTable component
 */
interface MoleculeTableProps {
  /** Array of molecule data to display */
  molecules: Molecule[];
  /** Whether the table is in loading state */
  loading?: boolean;
  /** Callback when a row is clicked */
  onRowClick?: (molecule: Molecule) => void;
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
  /** Initial column to sort by */
  initialSortBy?: string;
  /** Initial sort direction */
  initialSortDirection?: 'asc' | 'desc';
  /** Whether rows can be selected with checkboxes */
  selectable?: boolean;
  /** Callback when selection changes */
  onSelectionChange?: (selected: string[]) => void;
  /** Callback when edit button is clicked */
  onEdit?: (molecule: Molecule) => void;
  /** Callback when delete button is clicked */
  onDelete?: (molecule: Molecule) => void;
  /** Callback when add to library button is clicked */
  onAddToLibrary?: (molecule: Molecule) => void;
  /** Current filter criteria */
  filter?: MoleculeFilter;
  /** Additional CSS class name */
  className?: string;
}

/**
 * Styled wrapper for MoleculeViewer component
 */
const StyledMoleculeViewer = styled(Box)({
  width: '100px',
  height: '100px',
  display: 'flex',
  justifyContent: 'center',
  alignItems: 'center'
});

/**
 * Container for action buttons in the table
 */
const ActionButtonsContainer = styled(Box)({
  display: 'flex',
  gap: '8px',
  justifyContent: 'center'
});

/**
 * A specialized table component for displaying molecular data with structure visualization
 * @param props - Component props
 * @returns The rendered molecule table component
 */
const MoleculeTable: React.FC<MoleculeTableProps> = (props) => {
  // Destructure props: molecules, loading, onRowClick, pagination, totalCount, currentPage, pageSize, onPageChange, onPageSizeChange, initialSortBy, initialSortDirection, selectable, onSelectionChange, onEdit, onDelete, onAddToLibrary, filter, className
  const {
    molecules,
    loading = false,
    onRowClick,
    pagination = true,
    totalCount,
    currentPage = 1,
    pageSize = 10,
    onPageChange,
    onPageSizeChange,
    initialSortBy = 'molecular_weight',
    initialSortDirection = 'asc',
    selectable = false,
    onSelectionChange,
    onEdit,
    onDelete,
    onAddToLibrary,
    filter,
    className
  } = props;

  // Get selected molecules from Redux state using useAppSelector and selectSelectedMolecules
  const selectedMolecules = useAppSelector(selectSelectedMolecules);

  // Get dispatch function using useAppDispatch
  const dispatch = useAppDispatch();

  /**
   * Formats a molecule property value for display
   * @param value - The property value
   * @param propertyName - The name of the property
   * @returns Formatted property value
   */
  const formatPropertyValue = useCallback((value: any, propertyName: string): string => {
    // Check if value is null or undefined and return '-' if so
    if (value === null || value === undefined) {
      return '-';
    }

    // Format numerical values with appropriate precision
    if (typeof value === 'number') {
      if (propertyName === 'molecular_weight') {
        return value.toFixed(2);
      }
      return value.toFixed(3);
    }

    // Format special properties like molecular weight with units
    if (propertyName === 'molecular_weight') {
      return `${value} g/mol`;
    }

    // Return string representation of the value
    return String(value);
  }, []);

  // Define columns for the DataTable with appropriate formatters for each column type
  const columns = useMemo(() => [
    {
      id: 'structure',
      label: 'Structure',
      sortable: false,
      width: '120px',
      align: 'center',
      renderCell: (molecule: Molecule) => (
        // Create a structure column with MoleculeViewer component
        <StyledMoleculeViewer>
          <MoleculeViewer smiles={molecule.smiles} />
        </StyledMoleculeViewer>
      )
    },
    {
      id: 'molecular_weight',
      label: 'MW',
      sortable: true,
      width: '100px',
      align: 'center',
      format: (value: any, molecule: Molecule) => formatPropertyValue(value, 'molecular_weight')
    },
    {
      id: 'formula',
      label: 'Formula',
      sortable: true,
      width: '120px',
      align: 'center'
    },
    {
      id: 'logp',
      label: 'LogP',
      sortable: true,
      width: '80px',
      align: 'center',
      format: (value: any, molecule: Molecule) => formatPropertyValue(value, 'logp')
    },
    {
      id: 'status',
      label: 'Status',
      sortable: true,
      width: '120px',
      align: 'center',
      renderCell: (molecule: Molecule) => (
        // Create a status column with StatusBadge component
        <StatusBadge status={molecule.status || MoleculeStatus.AVAILABLE} statusType="molecule" />
      )
    },
    {
      id: 'actions',
      label: 'Actions',
      sortable: false,
      width: '150px',
      align: 'center',
      renderCell: (molecule: Molecule) => (
        // Create an actions column with edit, delete, and add to library buttons
        <ActionButtonsContainer>
          {onEdit && (
            <Tooltip title="Edit Molecule">
              <IconButton onClick={(e) => {
                e.stopPropagation();
                onEdit(molecule);
              }} aria-label="edit">
                <Edit />
              </IconButton>
            </Tooltip>
          )}
          {onDelete && (
            <Tooltip title="Delete Molecule">
              <IconButton onClick={(e) => {
                e.stopPropagation();
                onDelete(molecule);
              }} aria-label="delete">
                <Delete />
              </IconButton>
            </Tooltip>
          )}
          {onAddToLibrary && (
            <Tooltip title="Add to Library">
              <IconButton onClick={(e) => {
                e.stopPropagation();
                onAddToLibrary(molecule);
              }} aria-label="add to library">
                <AddToPhotos />
              </IconButton>
            </Tooltip>
          )}
        </ActionButtonsContainer>
      )
    }
  ], [onEdit, onDelete, onAddToLibrary, formatPropertyValue]);

  // Handle selection changes by dispatching setSelectedMolecules action
  const handleSelectionChange = useCallback((selected: string[]) => {
    dispatch(setSelectedMolecules(selected));
    if (onSelectionChange) {
      onSelectionChange(selected);
    }
  }, [dispatch, onSelectionChange]);

  // Handle row click to navigate to molecule detail page
  const handleRowClick = useCallback((molecule: Molecule) => {
    if (onRowClick) {
      onRowClick(molecule);
    }
  }, [onRowClick]);

  // Return DataTable component with molecule-specific columns and props
  return (
    <DataTable
      columns={columns}
      data={molecules}
      loading={loading}
      selectable={selectable}
      selected={selectedMolecules}
      onSelectionChange={handleSelectionChange}
      onRowClick={handleRowClick}
      pagination={pagination}
      totalCount={totalCount}
      currentPage={currentPage}
      pageSize={pageSize}
      onPageChange={onPageChange}
      onPageSizeChange={onPageSizeChange}
      initialSortBy={initialSortBy}
      initialSortDirection={initialSortDirection}
      className={className}
      getRowId={(row) => row.id}
    />
  );
};

export default MoleculeTable;