import React, { useState, useMemo } from 'react';
import {
  Table, TableBody, TableCell, TableContainer, TableHead, TableRow,
  Paper, Typography, Box, Chip
} from '@mui/material'; // ^5.0.0
import { styled } from '@mui/material/styles'; // ^5.0.0
import {
  ScienceOutlined, CalculateOutlined, ImportExportOutlined, BiotechOutlined
} from '@mui/icons-material'; // ^5.0.0
import { MoleculeProperty, PropertySource, PropertyType } from '../../types/molecule.types';
import DataTable from '../common/DataTable';
import {
  formatMolecularProperty,
  getPropertyDisplayName,
  formatPredictionConfidence
} from '../../utils/propertyFormatters';
import {
  PROPERTY_CATEGORIES,
  PROPERTY_DISPLAY_NAMES
} from '../../constants/moleculeProperties';

/**
 * Props for the PropertyTable component
 */
interface PropertyTableProps {
  /** Array of molecular properties to display */
  properties: MoleculeProperty[];
  /** Whether to group properties by category */
  groupByCategory?: boolean;
  /** Whether to show the property source */
  showSource?: boolean;
  /** Whether to show confidence for predicted properties */
  showConfidence?: boolean;
  /** Whether to show predicted properties */
  filterPredicted?: boolean;
  /** Whether to show experimental properties */
  filterExperimental?: boolean;
  /** Message to display when no properties are available */
  emptyMessage?: string;
  /** Maximum height of the table container */
  maxHeight?: string | number;
  /** Additional CSS class name */
  className?: string;
}

/**
 * Definition for table columns
 */
interface PropertyTableColumn {
  /** Unique identifier for the column */
  id: string;
  /** Display label for the column */
  label: string;
  /** Text alignment for the column */
  align?: 'left' | 'right' | 'center';
  /** Width of the column */
  width?: string | number;
  /** Function to format the cell value */
  format?: (value: any) => React.ReactNode;
}

/**
 * Styled container for the property table
 */
const StyledTableContainer = styled(TableContainer, {
  shouldForwardProp: (prop) => prop !== 'maxHeight',
})<{ maxHeight?: string | number }>(({ theme, maxHeight }) => ({
  maxHeight: maxHeight || 'none',
  overflow: 'auto',
  marginBottom: theme.spacing(2)
}));

/**
 * Header component for property categories
 */
const CategoryHeader = styled(Typography)(({ theme }) => ({
  fontWeight: 500,
  marginTop: theme.spacing(2),
  marginBottom: theme.spacing(1)
}));

/**
 * Chip component for displaying property sources
 */
const PropertySourceChip = styled(Chip)(({ theme }) => ({
  marginLeft: theme.spacing(1)
}));

/**
 * Chip component for displaying prediction confidence
 */
const ConfidenceChip = styled(Chip)(({ theme }) => ({
  marginLeft: theme.spacing(1)
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
 * Component that displays molecular properties in a tabular format
 * with support for grouping and filtering
 * 
 * @param props - Component props
 * @returns The rendered property table component
 */
const PropertyTable: React.FC<PropertyTableProps> = ({
  properties,
  groupByCategory = false,
  showSource = true,
  showConfidence = true,
  filterPredicted = true,
  filterExperimental = true,
  emptyMessage = 'No properties available',
  maxHeight,
  className
}) => {
  // Filter properties based on source if needed
  const filteredProperties = useMemo(() => {
    if (!properties || properties.length === 0) return [];
    
    return properties.filter(property => {
      if (!property.source) return true;
      
      if (property.source === PropertySource.PREDICTED && !filterPredicted) {
        return false;
      }
      
      if (property.source === PropertySource.EXPERIMENTAL && !filterExperimental) {
        return false;
      }
      
      return true;
    });
  }, [properties, filterPredicted, filterExperimental]);
  
  // Group properties by category if requested
  const propertyGroups = useMemo(() => {
    if (groupByCategory) {
      return groupPropertiesByCategory(filteredProperties);
    }
    return null;
  }, [filteredProperties, groupByCategory]);
  
  // Define columns for the property table
  const columns: PropertyTableColumn[] = useMemo(() => {
    const cols: PropertyTableColumn[] = [
      { 
        id: 'name', 
        label: 'Property', 
        width: '40%',
        format: (value) => getPropertyDisplayName(value)
      },
      { 
        id: 'value', 
        label: 'Value', 
        width: '40%',
        format: (value) => {
          const propertyName = (value.name || '') as string;
          return formatMolecularProperty(value, propertyName);
        }
      }
    ];
    
    // Add source column if needed
    if (showSource) {
      cols.push({
        id: 'source',
        label: 'Source',
        width: '20%',
        format: (value) => {
          if (!value) return '';
          
          const label = PropertySource[value] || value;
          return (
            <PropertySourceChip
              size="small"
              variant="outlined"
              label={label.charAt(0) + label.slice(1).toLowerCase()}
              icon={renderSourceIcon(value)}
            />
          );
        }
      });
    }
    
    // Add confidence column for predicted properties if needed
    if (showConfidence) {
      cols.push({
        id: 'confidence',
        label: 'Confidence',
        width: '20%',
        format: (value) => {
          if (!value || typeof value !== 'number') return '';
          
          const { value: formattedValue, color } = formatPredictionConfidence(value);
          return (
            <ConfidenceChip
              size="small"
              label={formattedValue}
              color={color as any}
            />
          );
        }
      });
    }
    
    return cols;
  }, [showSource, showConfidence]);
  
  // If no properties to display, show empty message
  if (!filteredProperties || filteredProperties.length === 0) {
    return (
      <Paper className={className}>
        <EmptyMessage variant="body2">
          {emptyMessage}
        </EmptyMessage>
      </Paper>
    );
  }
  
  // If grouping by category, render properties in groups
  if (groupByCategory && propertyGroups) {
    return (
      <Box className={className}>
        {Object.entries(propertyGroups).map(([category, props]) => (
          <div key={category}>
            <CategoryHeader variant="subtitle1" component="h3">
              {category}
            </CategoryHeader>
            <StyledTableContainer component={Paper} maxHeight={maxHeight}>
              <Table size="small" aria-label={`${category} properties`}>
                <TableHead>
                  <TableRow>
                    {columns.map((column) => (
                      <TableCell
                        key={column.id}
                        align={column.align || 'left'}
                        style={{ width: column.width }}
                      >
                        {column.label}
                      </TableCell>
                    ))}
                  </TableRow>
                </TableHead>
                <TableBody>
                  {props.map((property, index) => (
                    <TableRow key={`${property.name}-${index}`}>
                      {columns.map((column) => {
                        const value = property[column.id as keyof MoleculeProperty];
                        return (
                          <TableCell key={column.id} align={column.align || 'left'}>
                            {column.format ? column.format(value) : value}
                          </TableCell>
                        );
                      })}
                    </TableRow>
                  ))}
                </TableBody>
              </Table>
            </StyledTableContainer>
          </div>
        ))}
      </Box>
    );
  }
  
  // If not grouping by category, render a single table with all properties
  return (
    <StyledTableContainer component={Paper} maxHeight={maxHeight} className={className}>
      <Table size="small" aria-label="property table">
        <TableHead>
          <TableRow>
            {columns.map((column) => (
              <TableCell
                key={column.id}
                align={column.align || 'left'}
                style={{ width: column.width }}
              >
                {column.label}
              </TableCell>
            ))}
          </TableRow>
        </TableHead>
        <TableBody>
          {filteredProperties.map((property, index) => (
            <TableRow key={`${property.name}-${index}`}>
              {columns.map((column) => {
                const value = property[column.id as keyof MoleculeProperty];
                return (
                  <TableCell key={column.id} align={column.align || 'left'}>
                    {column.format ? column.format(value) : value}
                  </TableCell>
                );
              })}
            </TableRow>
          ))}
        </TableBody>
      </Table>
    </StyledTableContainer>
  );
};

/**
 * Groups properties by their category for organized display
 * 
 * @param properties - Array of molecule properties
 * @returns Properties grouped by category
 */
function groupPropertiesByCategory(properties: MoleculeProperty[]): Record<string, MoleculeProperty[]> {
  const groups: Record<string, MoleculeProperty[]> = {};
  
  properties.forEach(property => {
    const category = getPropertyCategory(property.name);
    
    if (!groups[category]) {
      groups[category] = [];
    }
    
    groups[category].push(property);
  });
  
  return groups;
}

/**
 * Determines the category for a property based on its name
 * 
 * @param propertyName - The property name
 * @returns Category name
 */
function getPropertyCategory(propertyName: string): string {
  // Use heuristics to determine category based on property name
  if (['molecular_weight', 'logp', 'tpsa', 'solubility', 'melting_point', 'boiling_point', 'exact_mass'].includes(propertyName)) {
    return 'Physical Properties';
  }
  
  if (['num_atoms', 'num_heavy_atoms', 'num_rings', 'num_rotatable_bonds', 'formula'].includes(propertyName)) {
    return 'Structural Properties';
  }
  
  if (['ic50', 'ec50', 'binding_affinity', 'bioavailability', 'clearance', 'half_life', 'permeability'].includes(propertyName)) {
    return 'Biological Properties';
  }
  
  if (['smiles', 'inchi_key'].includes(propertyName)) {
    return 'Identifiers';
  }
  
  if (['pka', 'pkb'].includes(propertyName)) {
    return 'Chemical Properties';
  }
  
  // Default category for properties that don't match any specific category
  return 'Other Properties';
}

/**
 * Renders an appropriate icon for the property source
 * 
 * @param source - The property source
 * @returns Icon component for the source
 */
function renderSourceIcon(source: PropertySource | undefined): JSX.Element | null {
  if (!source) return null;
  
  switch (source) {
    case PropertySource.CALCULATED:
      return <CalculateOutlined fontSize="small" />;
    case PropertySource.IMPORTED:
      return <ImportExportOutlined fontSize="small" />;
    case PropertySource.PREDICTED:
      return <ScienceOutlined fontSize="small" />;
    case PropertySource.EXPERIMENTAL:
      return <BiotechOutlined fontSize="small" />;
    default:
      return null;
  }
}

export default PropertyTable;