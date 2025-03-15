import React, { useState, useCallback, useEffect } from 'react'; // react v18.0.0
import {
  Box,
  Paper,
  Typography,
  Stepper,
  Step,
  StepLabel,
  Button,
  Alert,
  CircularProgress,
  Checkbox,
  FormControlLabel
} from '@mui/material'; // ^5.0.0
import DragDropZone from '../common/DragDropZone';
import CSVColumnMapper from '../common/CSVColumnMapper';
import {
  uploadMoleculeCSV,
  getCSVPreview,
  importMoleculesFromCSV
} from '../../api/moleculeApi';
import {
  CSVColumnMapping,
  MoleculeCSVMapping,
  MoleculeCSVProcessResult
} from '../../types/molecule.types';
import { REQUIRED_PROPERTIES } from '../../constants/moleculeProperties';
import LibrarySelector from '../library/LibrarySelector';

/**
 * Props interface for the MoleculeUploader component
 */
interface MoleculeUploaderProps {
  /** Callback function called when CSV processing is complete */
  onUploadComplete?: (result: MoleculeCSVProcessResult) => void;
  /** Optional CSS class name for styling */
  className?: string;
}

/**
 * A component that provides a user interface for uploading and processing CSV files containing molecular data
 */
const MoleculeUploader: React.FC<MoleculeUploaderProps> = ({ onUploadComplete, className }) => {
  // LD1: Initialize state for current step in the upload process
  const [activeStep, setActiveStep] = useState(0);
  // LD1: Initialize state for file being uploaded
  const [file, setFile] = useState<File | null>(null);
  // LD1: Initialize state for storage key returned from backend
  const [storageKey, setStorageKey] = useState('');
  // LD1: Initialize state for CSV preview data
  const [previewData, setPreviewData] = useState<{ headers: string[]; rows: Record<string, any>[]; }>({ headers: [], rows: [] });
  // LD1: Initialize state for column mappings
  const [columnMappings, setColumnMappings] = useState<CSVColumnMapping[]>([]);
  // LD1: Initialize state for selected library IDs
  const [selectedLibraryIds, setSelectedLibraryIds] = useState<string[]>([]);
  // LD1: Initialize state for loading status
  const [isLoading, setIsLoading] = useState(false);
  // LD1: Initialize state for error messages
  const [error, setError] = useState('');
  // LD1: Initialize state for success message
  const [success, setSuccess] = useState('');
  // LD1: Initialize state for mapping validation status
  const [isMappingValid, setIsMappingValid] = useState(false);
  // LD1: Initialize state for import options (skip duplicates)
  const [skipDuplicates, setSkipDuplicates] = useState(true);
  // LD1: Initialize state for processing result
  const [processResult, setProcessResult] = useState<MoleculeCSVProcessResult | null>(null);

  // IE1: Implement handleFileAccepted to handle file selection
  const handleFileAccepted = useCallback((files: File[]) => {
    // LD1: Set the first file as the selected file
    const selectedFile = files[0];
    setFile(selectedFile);
    // LD1: Call uploadFile function to upload the file to the server
    uploadFile(selectedFile);
  }, []);

  // IE1: Implement uploadFile to upload the selected file to the server
  const uploadFile = useCallback(async (selectedFile: File) => {
    // LD1: Set loading state to true
    setIsLoading(true);
    // LD1: Clear any previous errors
    setError('');
    try {
      // IE1: Call uploadMoleculeCSV API function with the file
      const response = await uploadMoleculeCSV(selectedFile);
      // LD1: If successful, store the returned storage key
      setStorageKey(response.storage_key);
      // LD1: Call fetchPreview to get CSV preview data
      fetchPreview(response.storage_key);
    } catch (e: any) {
      // LD1: If error occurs, set error message and reset loading state
      setError(e.message);
      setIsLoading(false);
    }
  }, []);

  // IE1: Implement fetchPreview to get CSV preview data from the server
  const fetchPreview = useCallback(async (key: string) => {
    try {
      // IE1: Call getCSVPreview API function with the storage key
      const response = await getCSVPreview(key);
      // LD1: If successful, store the preview data in state
      setPreviewData({ headers: response.headers, rows: response.rows });
      // LD1: Generate initial column mappings based on headers and suggestions
      const initialMappings = response.headers.map(header => ({
        csv_column: header,
        property_name: ''
      }));
      setColumnMappings(initialMappings);
    } catch (e: any) {
      // LD1: If error occurs, set error message
      setError(e.message);
    } finally {
      setIsLoading(false);
    }
  }, []);

  // IE1: Implement handleMappingChange to update column mappings
  const handleMappingChange = useCallback((mappings: CSVColumnMapping[]) => {
    // LD1: Update columnMappings state with new mappings
    setColumnMappings(mappings);
  }, []);

  // IE1: Implement handleMappingValidation to track mapping validation status
  const handleMappingValidation = useCallback((isValid: boolean, errors?: string[]) => {
    // LD1: Update isMappingValid state with validation result
    setIsMappingValid(isValid);
    // LD1: If not valid, set error message from validation errors
    if (!isValid && errors) {
      setError(errors.join('\n'));
    } else {
      setError('');
    }
  }, []);

  // IE1: Implement handleLibraryChange to update selected libraries
  const handleLibraryChange = useCallback((libraryIds: string[]) => {
    // LD1: Update selectedLibraryIds state with new selection
    setSelectedLibraryIds(libraryIds);
  }, []);

  // IE1: Implement handleImportOptionsChange to update import options
  const handleImportOptionsChange = useCallback((event: React.ChangeEvent<HTMLInputElement>) => {
    // LD1: Update skipDuplicates state based on checkbox value
    setSkipDuplicates(event.target.checked);
  }, []);

  // IE1: Implement importMolecules to process the CSV file with the specified mappings
  const importMolecules = useCallback(async () => {
    // LD1: Set loading state to true
    setIsLoading(true);
    // LD1: Clear any previous errors
    setError('');
    try {
      // LD1: Create mapping configuration object with column mappings, library IDs, and options
      const mappingConfiguration: MoleculeCSVMapping = {
        column_mappings: columnMappings,
        library_id: selectedLibraryIds.length > 0 ? selectedLibraryIds[0] : undefined,
        skip_duplicates: skipDuplicates
      };
      // IE1: Call importMoleculesFromCSV API function with storage key and mapping configuration
      const response = await importMoleculesFromCSV(storageKey, mappingConfiguration);
      // LD1: If successful, store the processing result and set success message
      setProcessResult(response);
      setSuccess('Molecules imported successfully!');
      // LD1: Call onUploadComplete callback with the result if provided
      if (onUploadComplete) {
        onUploadComplete(response);
      }
    } catch (e: any) {
      // LD1: If error occurs, set error message
      setError(e.message);
    } finally {
      // LD1: Reset loading state
      setIsLoading(false);
    }
  }, [storageKey, columnMappings, selectedLibraryIds, skipDuplicates, onUploadComplete]);

  // IE1: Implement handleNext to advance to the next step
  const handleNext = () => {
    // LD1: If on step 0 (Upload), ensure file is uploaded before proceeding
    if (activeStep === 0 && !file) {
      setError('Please upload a file');
      return;
    }
    // LD1: If on step 1 (Mapping), ensure mapping is valid before proceeding
    if (activeStep === 1 && !isMappingValid) {
      setError('Please ensure all required columns are mapped correctly');
      return;
    }
    // LD1: If on step 1 and proceeding to step 2, call importMolecules
    if (activeStep === 1) {
      importMolecules();
    }
    // LD1: Increment activeStep state
    setActiveStep((prevActiveStep) => prevActiveStep + 1);
  };

  // IE1: Implement handleBack to return to the previous step
  const handleBack = () => {
    // LD1: Decrement activeStep state if greater than 0
    setActiveStep((prevActiveStep) => prevActiveStep - 1);
    // LD1: Clear any error messages
    setError('');
  };

  // IE1: Implement handleReset to restart the upload process
  const handleReset = () => {
    // LD1: Reset all state variables to initial values
    setActiveStep(0);
    setFile(null);
    setStorageKey('');
    setPreviewData({ headers: [], rows: [] });
    setColumnMappings([]);
    setSelectedLibraryIds([]);
    setIsLoading(false);
    setError('');
    setSuccess('');
    setIsMappingValid(false);
    setSkipDuplicates(true);
    setProcessResult(null);
  };

  return (
    <Box className={className}>
      {/* LD1: Render stepper component to show the current step in the process */}
      <Stepper activeStep={activeStep} alternativeLabel>
        <Step key="upload">
          <StepLabel>Upload CSV</StepLabel>
        </Step>
        <Step key="mapping">
          <StepLabel>Map Columns</StepLabel>
        </Step>
        <Step key="results">
          <StepLabel>Import</StepLabel>
        </Step>
      </Stepper>
      <Box sx={{ mt: 2 }}>
        {/* LD1: Render error alert when error occurs */}
        {error && (
          <Alert severity="error" sx={{ mb: 2 }}>
            {error}
          </Alert>
        )}
        {/* LD1: Render success alert when upload completes successfully */}
        {success && (
          <Alert severity="success" sx={{ mb: 2 }}>
            {success}
          </Alert>
        )}
        {/* LD1: Render file upload step with DragDropZone when on step 0 */}
        {activeStep === 0 && (
          <DragDropZone
            onFilesAccepted={handleFileAccepted}
            acceptedFileTypes={['.csv']}
            maxFileSizeMB={100}
            loading={isLoading}
          >
            <Typography variant="body1" color="textSecondary">
              Drag and drop your CSV file here, or click to browse.
            </Typography>
          </DragDropZone>
        )}
        {/* LD1: Render column mapping step with CSVColumnMapper when on step 1 */}
        {activeStep === 1 && (
          <Box>
            <CSVColumnMapper
              previewData={previewData}
              initialMapping={columnMappings}
              onMappingChange={handleMappingChange}
              onValidation={handleMappingValidation}
            />
            <Box sx={{ mt: 2 }}>
              <FormControlLabel
                control={
                  <Checkbox
                    checked={skipDuplicates}
                    onChange={handleImportOptionsChange}
                    name="skipDuplicates"
                    color="primary"
                  />
                }
                label="Skip duplicate molecules"
              />
            </Box>
            <Box sx={{ mt: 2 }}>
              <LibrarySelector
                value={selectedLibraryIds.length > 0 ? selectedLibraryIds[0] : ''}
                onChange={handleLibraryChange}
                label="Add to Library"
                placeholder="Select a library"
                showCreateOption
                fullWidth
              />
            </Box>
          </Box>
        )}
        {/* LD1: Render import confirmation and results when on step 2 */}
        {activeStep === 2 && processResult && (
          <Box>
            <Typography variant="h6" gutterBottom>
              Import Summary
            </Typography>
            <Typography variant="body1">
              Total rows: {processResult.total_rows}
            </Typography>
            <Typography variant="body1">
              Processed rows: {processResult.processed_rows}
            </Typography>
            <Typography variant="body1">
              Failed rows: {processResult.failed_rows}
            </Typography>
            <Typography variant="body1">
              Duplicate rows skipped: {processResult.duplicate_rows}
            </Typography>
            <Typography variant="body1">
              New molecules created: {processResult.created_molecules}
            </Typography>
          </Box>
        )}
        {/* LD1: Render loading indicator when loading */}
        {isLoading && (
          <Box sx={{ display: 'flex', justifyContent: 'center', mt: 2 }}>
            <CircularProgress />
          </Box>
        )}
        {/* LD1: Render navigation buttons (Back, Next, Submit) based on current step */}
        <Box sx={{ display: 'flex', flexDirection: 'row', pt: 2 }}>
          <Button
            color="inherit"
            disabled={activeStep === 0 || isLoading}
            onClick={handleBack}
            sx={{ mr: 1 }}
          >
            Back
          </Button>
          <Box sx={{ flex: '1 1 auto' }} />
          {activeStep === 2 ? (
            <Button disabled={isLoading} onClick={handleReset}>
              Reset
            </Button>
          ) : (
            <Button disabled={isLoading} onClick={handleNext}>
              {activeStep === 1 ? 'Import' : 'Next'}
            </Button>
          )}
        </Box>
      </Box>
    </Box>
  );
};

export default MoleculeUploader;