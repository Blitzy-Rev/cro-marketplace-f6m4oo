import React, { useState, useEffect, useCallback, useMemo } from 'react';
import {
  Box,
  Paper,
  Typography,
  Divider,
  FormControl,
  FormGroup,
  FormControlLabel,
  Checkbox,
  Select,
  MenuItem,
  InputLabel,
  Button,
  Accordion,
  AccordionSummary,
  AccordionDetails,
  Chip
} from '@mui/material'; // ^5.0.0
import { ExpandMore, FilterList, Clear } from '@mui/icons-material'; // ^5.0.0
import { styled } from '@mui/material/styles'; // ^5.0.0

// Import types and components
import {
  MoleculeFilter as MoleculeFilterType,
  PropertyFilter,
  MoleculeStatus
} from '../../types/molecule.types';
import {
  FILTERABLE_PROPERTIES,
  PROPERTY_DISPLAY_NAMES,
  PROPERTY_RANGES,
  PROPERTY_UNITS
} from '../../constants/moleculeProperties';
import useMoleculeFilterParams from '../../hooks/useMoleculeFilterParams';
import PropertyRangeSlider from '../common/PropertyRangeSlider';
import SearchField from '../common/SearchField';

// Define interface for component props
interface MoleculeFilterProps {
  initialFilters?: Partial<MoleculeFilterType>;
  onFilterChange?: (filters: MoleculeFilterType) => void;
  libraryOptions?: Array<{ id: string; name: string }>;
  className?: string;
}

// Define interface for filter chip props
interface ActiveFilterChipProps {
  label: string;
  onDelete: () => void;
}

// Styled components
const FilterContainer = styled(Paper)(({ theme }) => ({
  padding: theme.spacing(2),
  marginBottom: theme.spacing(2),
}));

const FilterSection = styled(Box)(({ theme }) => ({
  marginBottom: theme.spacing(2),
}));

const FilterHeader = styled(Box)(({ theme }) => ({
  display: 'flex',
  alignItems: 'center',
  marginBottom: theme.spacing(1),
}));

const FilterTitle = styled(Typography)(({ theme }) => ({
  fontWeight: 500,
  display: 'flex',
  alignItems: 'center',
}));

const FilterIcon = styled(FilterList)(({ theme }) => ({
  marginRight: theme.spacing(1),
  fontSize: 20,
}));

const ActiveFiltersContainer = styled(Box)(({ theme }) => ({
  display: 'flex',
  flexWrap: 'wrap',
  gap: theme.spacing(1),
  marginTop: theme.spacing(2),
}));

const FilterChip = styled(Chip)(({ theme }) => ({
  margin: theme.spacing(0.5),
}));

const ResetButton = styled(Button)(({ theme }) => ({
  marginTop: theme.spacing(1),
}));

// ActiveFilterChip component to display active filters
const ActiveFilterChip: React.FC<ActiveFilterChipProps> = ({ label, onDelete }) => {
  return <FilterChip label={label} onDelete={onDelete} color="primary" variant="outlined" />;
};

/**
 * A component that provides comprehensive filtering options for molecules
 */
const MoleculeFilter: React.FC<MoleculeFilterProps> = ({
  initialFilters,
  onFilterChange,
  libraryOptions,
  className,
}) => {
  // Use the filter params hook to manage filter state
  const {
    filters,
    setSearchTerm,
    setPropertyFilter,
    setStatusFilter,
    setLibraryFilter,
    resetFilters
  } = useMoleculeFilterParams(initialFilters);

  // Track expanded accordion sections
  const [expandedProperty, setExpandedProperty] = useState<string | null>(null);

  // Notify parent component when filters change
  useEffect(() => {
    if (onFilterChange) {
      onFilterChange(filters);
    }
  }, [filters, onFilterChange]);

  // Handle search term changes
  const handleSearchChange = useCallback((value: string) => {
    setSearchTerm(value);
  }, [setSearchTerm]);

  // Handle property filter changes
  const handlePropertyFilterChange = useCallback((name: string, min: number | null, max: number | null) => {
    setPropertyFilter(name, min, max);
  }, [setPropertyFilter]);

  // Handle status filter changes
  const handleStatusFilterChange = useCallback((event: React.ChangeEvent<HTMLInputElement>, checked: boolean) => {
    const status = event.target.name as MoleculeStatus;
    
    // If filters.status is null or string, initialize as array
    let updatedStatus: MoleculeStatus[] = [];
    
    if (filters.status) {
      if (Array.isArray(filters.status)) {
        updatedStatus = [...filters.status];
      } else {
        updatedStatus = [filters.status];
      }
    }
    
    if (checked) {
      // Add the status if it doesn't exist
      if (!updatedStatus.includes(status)) {
        updatedStatus.push(status);
      }
    } else {
      // Remove the status
      updatedStatus = updatedStatus.filter(s => s !== status);
    }
    
    // If we have no statuses selected, set to null
    // If we have only one, use it directly
    // Otherwise use the array
    if (updatedStatus.length === 0) {
      setStatusFilter(null);
    } else if (updatedStatus.length === 1) {
      setStatusFilter(updatedStatus[0]);
    } else {
      setStatusFilter(updatedStatus);
    }
  }, [filters.status, setStatusFilter]);

  // Handle library change
  const handleLibraryChange = useCallback((event: React.ChangeEvent<{ value: unknown }>) => {
    const value = event.target.value as string;
    setLibraryFilter(value || null);
  }, [setLibraryFilter]);

  // Handle reset filters
  const handleResetFilters = useCallback(() => {
    resetFilters();
  }, [resetFilters]);

  // Handle accordion expansion
  const handleAccordionChange = useCallback((panel: string) => (event: React.SyntheticEvent, isExpanded: boolean) => {
    setExpandedProperty(isExpanded ? panel : null);
  }, []);

  // Handle removing a specific filter
  const handleRemoveFilter = useCallback((type: string, name?: string) => {
    if (type === 'search') {
      setSearchTerm('');
    } else if (type === 'library') {
      setLibraryFilter(null);
    } else if (type === 'status') {
      setStatusFilter(null);
    } else if (type === 'property' && name) {
      setPropertyFilter(name, null, null);
    }
  }, [setSearchTerm, setLibraryFilter, setStatusFilter, setPropertyFilter]);

  // Create active filter chips from current filters
  const activeFilters = useMemo(() => {
    const chips: { label: string; onDelete: () => void }[] = [];
    
    // Search filter
    if (filters.search) {
      chips.push({
        label: `Search: ${filters.search}`,
        onDelete: () => handleRemoveFilter('search')
      });
    }
    
    // Library filter
    if (filters.library_id && libraryOptions) {
      const library = libraryOptions.find(lib => lib.id === filters.library_id);
      if (library) {
        chips.push({
          label: `Library: ${library.name}`,
          onDelete: () => handleRemoveFilter('library')
        });
      }
    }
    
    // Status filter
    if (filters.status) {
      if (Array.isArray(filters.status)) {
        chips.push({
          label: `Status: ${filters.status.join(', ')}`,
          onDelete: () => handleRemoveFilter('status')
        });
      } else {
        chips.push({
          label: `Status: ${filters.status}`,
          onDelete: () => handleRemoveFilter('status')
        });
      }
    }
    
    // Property filters
    if (filters.properties && filters.properties.length > 0) {
      filters.properties.forEach(prop => {
        const displayName = PROPERTY_DISPLAY_NAMES[prop.name] || prop.name;
        const units = PROPERTY_UNITS[prop.name] || '';
        
        if (prop.min_value !== null && prop.max_value !== null) {
          chips.push({
            label: `${displayName}: ${prop.min_value}${units ? ` ${units}` : ''} - ${prop.max_value}${units ? ` ${units}` : ''}`,
            onDelete: () => handleRemoveFilter('property', prop.name)
          });
        } else if (prop.min_value !== null) {
          chips.push({
            label: `${displayName}: ≥ ${prop.min_value}${units ? ` ${units}` : ''}`,
            onDelete: () => handleRemoveFilter('property', prop.name)
          });
        } else if (prop.max_value !== null) {
          chips.push({
            label: `${displayName}: ≤ ${prop.max_value}${units ? ` ${units}` : ''}`,
            onDelete: () => handleRemoveFilter('property', prop.name)
          });
        }
      });
    }
    
    return chips;
  }, [filters, libraryOptions, handleRemoveFilter]);

  // Check if a status is selected
  const isStatusSelected = useCallback((status: MoleculeStatus): boolean => {
    if (!filters.status) return false;
    
    if (Array.isArray(filters.status)) {
      return filters.status.includes(status);
    }
    
    return filters.status === status;
  }, [filters.status]);

  return (
    <FilterContainer className={className}>
      {/* Search filter */}
      <FilterSection>
        <FilterHeader>
          <FilterTitle variant="subtitle1">
            <FilterIcon />
            Search
          </FilterTitle>
        </FilterHeader>
        <SearchField
          value={filters.search || ''}
          onChange={handleSearchChange}
          placeholder="Search by SMILES, formula, or ID"
          fullWidth
          size="small"
        />
      </FilterSection>

      {/* Library filter */}
      {libraryOptions && libraryOptions.length > 0 && (
        <FilterSection>
          <FilterHeader>
            <FilterTitle variant="subtitle1">
              <FilterIcon />
              Library
            </FilterTitle>
          </FilterHeader>
          <FormControl fullWidth size="small">
            <InputLabel id="library-select-label">Select Library</InputLabel>
            <Select
              labelId="library-select-label"
              id="library-select"
              value={filters.library_id || ''}
              onChange={handleLibraryChange as any}
              label="Select Library"
            >
              <MenuItem value="">All Libraries</MenuItem>
              {libraryOptions.map(library => (
                <MenuItem key={library.id} value={library.id}>
                  {library.name}
                </MenuItem>
              ))}
            </Select>
          </FormControl>
        </FilterSection>
      )}

      {/* Status filter */}
      <FilterSection>
        <FilterHeader>
          <FilterTitle variant="subtitle1">
            <FilterIcon />
            Status
          </FilterTitle>
        </FilterHeader>
        <FormGroup row>
          <FormControlLabel
            control={
              <Checkbox
                checked={isStatusSelected(MoleculeStatus.AVAILABLE)}
                onChange={handleStatusFilterChange}
                name={MoleculeStatus.AVAILABLE}
                size="small"
              />
            }
            label="Available"
          />
          <FormControlLabel
            control={
              <Checkbox
                checked={isStatusSelected(MoleculeStatus.TESTING)}
                onChange={handleStatusFilterChange}
                name={MoleculeStatus.TESTING}
                size="small"
              />
            }
            label="Testing"
          />
          <FormControlLabel
            control={
              <Checkbox
                checked={isStatusSelected(MoleculeStatus.RESULTS)}
                onChange={handleStatusFilterChange}
                name={MoleculeStatus.RESULTS}
                size="small"
              />
            }
            label="Results"
          />
          <FormControlLabel
            control={
              <Checkbox
                checked={isStatusSelected(MoleculeStatus.PENDING)}
                onChange={handleStatusFilterChange}
                name={MoleculeStatus.PENDING}
                size="small"
              />
            }
            label="Pending"
          />
          <FormControlLabel
            control={
              <Checkbox
                checked={isStatusSelected(MoleculeStatus.ARCHIVED)}
                onChange={handleStatusFilterChange}
                name={MoleculeStatus.ARCHIVED}
                size="small"
              />
            }
            label="Archived"
          />
        </FormGroup>
      </FilterSection>

      {/* Property filters */}
      <FilterSection>
        <FilterHeader>
          <FilterTitle variant="subtitle1">
            <FilterIcon />
            Properties
          </FilterTitle>
        </FilterHeader>
        
        {FILTERABLE_PROPERTIES.map(property => {
          // Get current values for this property filter
          const currentPropertyFilter = filters.properties?.find(p => p.name === property);
          const minValue = currentPropertyFilter?.min_value || null;
          const maxValue = currentPropertyFilter?.max_value || null;
          
          // Get display name and range for this property
          const displayName = PROPERTY_DISPLAY_NAMES[property] || property;
          const range = PROPERTY_RANGES[property] || { min: 0, max: 100 };
          const units = PROPERTY_UNITS[property] || '';
          
          return (
            <Accordion
              key={property}
              expanded={expandedProperty === property}
              onChange={handleAccordionChange(property)}
            >
              <AccordionSummary
                expandIcon={<ExpandMore />}
                aria-controls={`${property}-content`}
                id={`${property}-header`}
              >
                <Typography>{displayName}</Typography>
              </AccordionSummary>
              <AccordionDetails>
                <PropertyRangeSlider
                  propertyName={property}
                  displayName={displayName}
                  minValue={range.min}
                  maxValue={range.max}
                  currentMin={minValue}
                  currentMax={maxValue}
                  units={units}
                  onChange={(min, max) => handlePropertyFilterChange(property, min, max)}
                />
              </AccordionDetails>
            </Accordion>
          );
        })}
      </FilterSection>

      {/* Active filters */}
      {activeFilters.length > 0 && (
        <FilterSection>
          <FilterHeader>
            <FilterTitle variant="subtitle1">
              <FilterIcon />
              Active Filters
            </FilterTitle>
          </FilterHeader>
          <ActiveFiltersContainer>
            {activeFilters.map((chip, index) => (
              <ActiveFilterChip
                key={index}
                label={chip.label}
                onDelete={chip.onDelete}
              />
            ))}
          </ActiveFiltersContainer>
          <ResetButton
            startIcon={<Clear />}
            onClick={handleResetFilters}
            variant="outlined"
            size="small"
            color="primary"
          >
            Reset Filters
          </ResetButton>
        </FilterSection>
      )}
    </FilterContainer>
  );
};

export default MoleculeFilter;