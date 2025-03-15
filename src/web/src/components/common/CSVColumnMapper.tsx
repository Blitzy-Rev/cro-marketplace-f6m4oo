import React, { useState, useEffect, useCallback } from 'react';
import {
  Box,
  Typography,
  Paper,
  FormControl,
  InputLabel,
  Select,
  MenuItem,
  Table,
  TableBody,
  TableCell,
  TableContainer,
  TableHead,
  TableRow,
  Alert,
  Chip
} from '@mui/material'; // ^5.0.0
import DataTable from './DataTable';
import {
  MoleculeCSVMapping,
  CSVColumnMapping,
  PropertyType
} from '../../types/molecule.types';
import {
  PROPERTY_DISPLAY_NAMES,
  PROPERTY_DEFINITIONS,
  REQUIRED_PROPERTIES
} from '../../constants/moleculeProperties';

/**
 * Props for the CSVColumnMapper component
 */
interface CSVColumnMapperProps {
  /**
   * Preview data from the CSV file including headers and sample rows
   */
  previewData: {
    headers: string[];
    rows: Record<string, any>[];
  };
  /**
   * Initial column mapping configuration, if available
   */
  initialMapping?: CSVColumnMapping[];
  /**
   * Callback function triggered when mappings are changed
   */
  onMappingChange: (mappings: CSVColumnMapping[]) => void;
  /**
   * Callback function triggered when validation status changes
   */
  onValidation: (isValid: boolean, errors?: string[]) => void;
  /**
   * Optional CSS class name for styling
   */
  className?: string;
}

/**
 * A component that provides an interface for mapping CSV columns to molecular properties
 * 
 * This component displays a preview of CSV data and allows users to select which system
 * property each column should be mapped to, with validation for required properties.
 */
const CSVColumnMapper: React.FC<CSVColumnMapperProps> = ({
  previewData,
  initialMapping,
  onMappingChange,
  onValidation,
  className
}) => {
  // State for column mappings
  const [mappings, setMappings] = useState<CSVColumnMapping[]>(
    initialMapping || []
  );
  
  // State for validation errors
  const [validationErrors, setValidationErrors] = useState<string[]>([]);

  // Update mappings when initialMapping changes
  useEffect(() => {
    if (initialMapping) {
      setMappings(initialMapping);
    } else if (previewData.headers.length > 0 && mappings.length === 0) {
      // Initialize with empty mappings if none provided
      const initialMappings = previewData.headers.map(header => ({
        csv_column: header,
        property_name: ''
      }));
      setMappings(initialMappings);
    }
  }, [initialMapping, previewData.headers, mappings.length]);

  // Handle mapping change
  const handleMappingChange = useCallback(
    (columnName: string, propertyName: string) => {
      const updatedMappings = mappings.map(mapping => {
        if (mapping.csv_column === columnName) {
          return {
            ...mapping,
            property_name: propertyName,
            is_required: REQUIRED_PROPERTIES.includes(propertyName)
          };
        }
        return mapping;
      });
      
      setMappings(updatedMappings);
      onMappingChange(updatedMappings);
    },
    [mappings, onMappingChange]
  );

  // Validate mappings
  const validateMappings = useCallback(() => {
    const errors: string[] = [];
    const mappedProperties = mappings
      .filter(m => m.property_name)
      .map(m => m.property_name);
    
    // Check for required properties
    REQUIRED_PROPERTIES.forEach(requiredProp => {
      if (!mappedProperties.includes(requiredProp)) {
        errors.push(`Required property "${PROPERTY_DISPLAY_NAMES[requiredProp] || requiredProp}" is not mapped.`);
      }
    });
    
    // Check for duplicate mappings
    const propertyCount: Record<string, number> = {};
    mappedProperties.forEach(prop => {
      propertyCount[prop] = (propertyCount[prop] || 0) + 1;
    });
    
    Object.entries(propertyCount).forEach(([prop, count]) => {
      if (count > 1 && prop !== '') {
        errors.push(`Property "${PROPERTY_DISPLAY_NAMES[prop] || prop}" is mapped multiple times.`);
      }
    });
    
    setValidationErrors(errors);
    return errors.length === 0;
  }, [mappings]);

  // Trigger validation and call onValidation when mappings change
  useEffect(() => {
    const isValid = validateMappings();
    onValidation(isValid, validationErrors);
  }, [mappings, validateMappings, onValidation, validationErrors]);

  // Get available property options
  const getPropertyOptions = () => {
    const options = [
      { value: '', display: 'Select property...' },
      ...Object.entries(PROPERTY_DEFINITIONS).map(([key, def]) => ({
        value: key,
        display: def.display_name,
        required: REQUIRED_PROPERTIES.includes(key)
      }))
    ];
    
    return options;
  };

  // Check if a property is required
  const isRequiredProperty = (propertyName: string) => {
    return REQUIRED_PROPERTIES.includes(propertyName);
  };

  // Check if a mapping is valid
  const isMappingValid = (mapping: CSVColumnMapping) => {
    if (!mapping.property_name) return true; // Empty mapping is valid (not all columns need to be mapped)
    
    // Check if this property is mapped multiple times
    const propertyCount = mappings.filter(m => m.property_name === mapping.property_name).length;
    return propertyCount === 1;
  };

  // Format the data for preview table
  const previewColumns = previewData.headers.map(header => ({
    id: header,
    label: header
  }));

  return (
    <Box className={className}>
      <Typography variant="h6" gutterBottom>
        Map CSV Columns to Molecule Properties
      </Typography>
      
      {/* CSV Preview Section */}
      <Paper sx={{ mb: 3, p: 2 }}>
        <Typography variant="subtitle1" gutterBottom>
          CSV Preview (first {previewData.rows.length} rows):
        </Typography>
        <DataTable
          columns={previewColumns}
          data={previewData.rows}
          emptyMessage="No preview data available"
        />
      </Paper>
      
      {/* Column Mapping Section */}
      <Paper sx={{ p: 2 }}>
        <Typography variant="subtitle1" gutterBottom>
          Map Columns to Properties:
        </Typography>
        
        {validationErrors.length > 0 && (
          <Alert severity="warning" sx={{ mb: 2 }}>
            {validationErrors.map((error, index) => (
              <div key={index}>{error}</div>
            ))}
          </Alert>
        )}
        
        <TableContainer>
          <Table>
            <TableHead>
              <TableRow>
                <TableCell>CSV Column</TableCell>
                <TableCell>System Property</TableCell>
                <TableCell>Required</TableCell>
                <TableCell>Status</TableCell>
              </TableRow>
            </TableHead>
            <TableBody>
              {mappings.map((mapping) => (
                <TableRow key={mapping.csv_column}>
                  <TableCell>{mapping.csv_column}</TableCell>
                  <TableCell>
                    <FormControl fullWidth size="small">
                      <Select
                        value={mapping.property_name}
                        onChange={(e) => handleMappingChange(mapping.csv_column, e.target.value as string)}
                        displayEmpty
                      >
                        {getPropertyOptions().map((option) => (
                          <MenuItem 
                            key={option.value} 
                            value={option.value}
                            sx={option.required ? { fontWeight: 'bold' } : {}}
                          >
                            {option.display}
                            {option.required ? ' *' : ''}
                          </MenuItem>
                        ))}
                      </Select>
                    </FormControl>
                  </TableCell>
                  <TableCell>
                    {isRequiredProperty(mapping.property_name) ? (
                      <Chip label="Required" color="primary" size="small" />
                    ) : mapping.property_name ? (
                      <Chip label="Optional" color="default" size="small" />
                    ) : (
                      '-'
                    )}
                  </TableCell>
                  <TableCell>
                    {mapping.property_name ? (
                      isMappingValid(mapping) ? (
                        <Chip label="Valid" color="success" size="small" />
                      ) : (
                        <Chip label="Invalid" color="error" size="small" />
                      )
                    ) : (
                      <Chip label="Not mapped" color="default" size="small" />
                    )}
                  </TableCell>
                </TableRow>
              ))}
            </TableBody>
          </Table>
        </TableContainer>
        
        <Typography variant="body2" color="text.secondary" sx={{ mt: 2 }}>
          * Indicates required properties. The SMILES column must be mapped for molecular structure validation.
        </Typography>
      </Paper>
    </Box>
  );
};

export default CSVColumnMapper;