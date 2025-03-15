import React, { useState, useCallback } from 'react';
import {
  Box,
  Paper,
  Typography,
  Stepper,
  Step,
  StepLabel,
  Button,
  Alert,
  FormControl,
  FormControlLabel,
  Checkbox,
  TextField,
  MenuItem,
  Select
} from '@mui/material';
import DragDropZone from '../common/DragDropZone';
import CSVColumnMapper from '../common/CSVColumnMapper';
import LoadingOverlay from '../common/LoadingOverlay';
import StatusBadge from '../common/StatusBadge';
import {
  ResultCSVMapping,
  CSVColumnMapping,
  ResultCSVProcessResult
} from '../../types/result.types';
import {
  uploadResultFile,
  processResultFile
} from '../../api/resultApi';

/**
 * Props interface for the ResultsUploader component
 */
interface ResultsUploaderProps {
  /** ID of the submission to upload results for */
  submissionId: string;
  /** Callback function called when upload is complete */
  onComplete: (resultId: string) => void;
  /** Optional CSS class name for styling */
  className?: string;
}

/**
 * Interface for parsed CSV data
 */
interface CSVData {
  /** Column headers from the CSV file */
  headers: string[];
  /** Preview rows from the CSV file */
  rows: Record<string, any>[];
}

/**
 * Interface for additional information about results
 */
interface AdditionalInfo {
  /** Protocol used for the experiment */
  protocolUsed: string;
  /** Whether quality control checks passed */
  qualityControlPassed: boolean;
  /** Additional notes about the results */
  notes: string;
}

/**
 * A component that provides an interface for CRO users to upload experimental results files,
 * map CSV columns to result properties, and submit the processed results.
 */
const ResultsUploader: React.FC<ResultsUploaderProps> = ({
  submissionId,
  onComplete,
  className
}) => {
  // Step management
  const [activeStep, setActiveStep] = useState(0);
  
  // File and data states
  const [file, setFile] = useState<File | null>(null);
  const [csvData, setCsvData] = useState<CSVData | null>(null);
  const [columnMappings, setColumnMappings] = useState<CSVColumnMapping[]>([]);
  const [mappingValid, setMappingValid] = useState(false);
  
  // Additional information
  const [additionalInfo, setAdditionalInfo] = useState<AdditionalInfo>({
    protocolUsed: '',
    qualityControlPassed: true,
    notes: ''
  });
  
  // Processing states
  const [storageKey, setStorageKey] = useState<string | null>(null);
  const [processResult, setProcessResult] = useState<ResultCSVProcessResult | null>(null);
  const [resultId, setResultId] = useState<string | null>(null);
  
  // Loading and error states
  const [loading, setLoading] = useState(false);
  const [uploadLoading, setUploadLoading] = useState(false);
  const [processLoading, setProcessLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);
  
  /**
   * Handle file acceptance from DragDropZone
   */
  const handleFileAccepted = useCallback((files: File[]) => {
    if (files && files.length > 0) {
      setFile(files[0]);
      parseCSV(files[0]);
      setError(null);
    }
  }, []);
  
  /**
   * Parse CSV file to extract headers and preview data
   */
  const parseCSV = async (file: File) => {
    setLoading(true);
    try {
      const reader = new FileReader();
      reader.onload = (e) => {
        try {
          const content = e.target?.result as string;
          if (!content) {
            throw new Error('Failed to read file content');
          }
          
          // Simple CSV parsing (could use a library for more robust parsing)
          const lines = content.split('\n');
          if (lines.length === 0) {
            throw new Error('CSV file is empty');
          }
          
          // Extract headers from first line
          const headers = lines[0].split(',').map(header => header.trim());
          
          // Extract up to 5 rows for preview
          const previewRows = lines.slice(1, Math.min(6, lines.length))
            .filter(line => line.trim().length > 0)
            .map(line => {
              const values = line.split(',').map(value => value.trim());
              const row: Record<string, any> = {};
              headers.forEach((header, index) => {
                row[header] = values[index] || '';
              });
              return row;
            });
          
          setCsvData({
            headers,
            rows: previewRows
          });
          
          // Initialize column mappings
          const initialMappings = headers.map(header => ({
            csv_column: header,
            property_name: ''
          }));
          setColumnMappings(initialMappings);
        } catch (err) {
          console.error('CSV parsing error:', err);
          setError('Failed to parse CSV file. Please check the format.');
        } finally {
          setLoading(false);
        }
      };
      
      reader.onerror = () => {
        setError('Failed to read the file. Please try again.');
        setLoading(false);
      };
      
      reader.readAsText(file);
    } catch (err) {
      console.error('File processing error:', err);
      setError('An error occurred while processing the file.');
      setLoading(false);
    }
  };
  
  /**
   * Handle column mapping changes from CSVColumnMapper
   */
  const handleMappingChange = useCallback((mappings: CSVColumnMapping[]) => {
    setColumnMappings(mappings);
  }, []);
  
  /**
   * Handle mapping validation from CSVColumnMapper
   */
  const handleMappingValidation = useCallback((isValid: boolean, errors?: string[]) => {
    setMappingValid(isValid);
    if (errors && errors.length > 0) {
      setError(errors[0]);
    } else {
      setError(null);
    }
  }, []);
  
  /**
   * Validate the additional information form
   */
  const validateAdditionalInfo = useCallback(() => {
    if (!additionalInfo.protocolUsed) {
      setError('Please specify the protocol used');
      return false;
    }
    return true;
  }, [additionalInfo]);
  
  /**
   * Upload the file to the server
   */
  const handleUpload = useCallback(async () => {
    if (!file) {
      setError('No file selected');
      return false;
    }
    
    setUploadLoading(true);
    setError(null);
    
    try {
      const additionalData = {
        submission_id: submissionId
      };
      
      const result = await uploadResultFile(file, submissionId, additionalData);
      setStorageKey(result.storage_key);
      return true;
    } catch (err) {
      console.error('File upload error:', err);
      setError('Failed to upload file. Please try again.');
      return false;
    } finally {
      setUploadLoading(false);
    }
  }, [file, submissionId]);
  
  /**
   * Process the uploaded file with column mappings
   */
  const handleProcess = useCallback(async () => {
    if (!storageKey) {
      setError('File not uploaded. Please try again.');
      return false;
    }
    
    if (!mappingValid || columnMappings.length === 0) {
      setError('Invalid column mapping');
      return false;
    }
    
    setProcessLoading(true);
    setError(null);
    
    try {
      // Find the molecule ID column mapping
      const moleculeIdMapping = columnMappings.find(mapping => 
        mapping.property_name.toLowerCase() === 'molecule_id' || 
        mapping.property_name.toLowerCase() === 'id'
      );
      
      if (!moleculeIdMapping) {
        setError('Please map a column to the Molecule ID');
        return false;
      }
      
      const mapping: ResultCSVMapping = {
        column_mappings: columnMappings,
        molecule_id_column: moleculeIdMapping.csv_column,
        skip_header: true
      };
      
      const result = await processResultFile(storageKey, mapping);
      setProcessResult(result);
      
      // In a real implementation, the resultId would come from the API response
      if (result && result.status === 'completed') {
        // This is a placeholder - in production this would be returned from the API
        setResultId(`result_${submissionId}_${Date.now()}`);
        return true;
      }
      
      return false;
    } catch (err) {
      console.error('File processing error:', err);
      setError('Failed to process file. Please check your column mappings.');
      return false;
    } finally {
      setProcessLoading(false);
    }
  }, [storageKey, columnMappings, mappingValid, submissionId]);
  
  /**
   * Handle next step button click
   */
  const handleNextStep = useCallback(async () => {
    // Validate current step before proceeding
    if (activeStep === 0) {
      // Validate file upload
      if (!file || !csvData) {
        setError('Please upload a CSV file first');
        return;
      }
    } else if (activeStep === 1) {
      // Validate column mappings
      if (!mappingValid) {
        setError('Please complete the column mapping');
        return;
      }
      
      // Check for molecule ID column mapping
      const hasIdColumn = columnMappings.some(mapping => 
        mapping.property_name.toLowerCase() === 'molecule_id' || 
        mapping.property_name.toLowerCase() === 'id'
      );
      
      if (!hasIdColumn) {
        setError('Please map a column to the Molecule ID');
        return;
      }
      
      // Upload file when moving from step 1 to 2
      const uploadSuccess = await handleUpload();
      if (!uploadSuccess) return;
    } else if (activeStep === 2) {
      // Validate additional info
      if (!validateAdditionalInfo()) {
        return;
      }
      
      // Process file when moving from step 2 to 3
      const processSuccess = await handleProcess();
      if (!processSuccess) return;
    }
    
    // Proceed to next step
    setActiveStep((prevStep) => prevStep + 1);
  }, [activeStep, file, csvData, mappingValid, columnMappings, validateAdditionalInfo, handleUpload, handleProcess]);
  
  /**
   * Handle back button click
   */
  const handlePreviousStep = useCallback(() => {
    setActiveStep((prevStep) => prevStep - 1);
    setError(null);
  }, []);
  
  /**
   * Handle completion of the upload process
   */
  const handleComplete = useCallback(() => {
    if (resultId) {
      onComplete(resultId);
    } else {
      setError('Unable to complete the process. No result ID available.');
    }
  }, [resultId, onComplete]);
  
  /**
   * Handle reset to start over
   */
  const handleReset = useCallback(() => {
    setActiveStep(0);
    setFile(null);
    setCsvData(null);
    setColumnMappings([]);
    setMappingValid(false);
    setAdditionalInfo({
      protocolUsed: '',
      qualityControlPassed: true,
      notes: ''
    });
    setStorageKey(null);
    setProcessResult(null);
    setResultId(null);
    setError(null);
  }, []);
  
  /**
   * Get content for the current step
   */
  const getStepContent = (step: number) => {
    switch (step) {
      case 0:
        return (
          <Box mb={3}>
            <Typography variant="subtitle1" gutterBottom>
              Step 1: Upload Results File
            </Typography>
            <DragDropZone
              onFilesAccepted={handleFileAccepted}
              acceptedFileTypes={['.csv']}
              maxFileSizeMB={100}
              loading={loading}
            >
              <Box sx={{ textAlign: 'center' }}>
                <Typography variant="h6" gutterBottom>
                  Drag and drop your results CSV file here, or Browse
                </Typography>
                <Typography variant="caption" display="block" sx={{ mt: 2 }}>
                  Supported format: CSV with molecule ID and result columns
                </Typography>
                <Typography variant="caption" display="block">
                  Template: <Button variant="text" size="small">Download CSV Template</Button>
                </Typography>
              </Box>
            </DragDropZone>
          </Box>
        );
      
      case 1:
        return (
          <Box mb={3}>
            <Typography variant="subtitle1" gutterBottom>
              Step 2: Map Results Columns
            </Typography>
            {csvData && (
              <CSVColumnMapper
                previewData={csvData}
                initialMapping={columnMappings}
                onMappingChange={handleMappingChange}
                onValidation={handleMappingValidation}
              />
            )}
          </Box>
        );
      
      case 2:
        return (
          <Box mb={3}>
            <Typography variant="subtitle1" gutterBottom>
              Step 3: Additional Information
            </Typography>
            <Paper sx={{ p: 3 }}>
              <FormControl fullWidth margin="normal">
                <TextField
                  label="Assay Protocol Used"
                  value={additionalInfo.protocolUsed}
                  onChange={(e) => setAdditionalInfo({
                    ...additionalInfo,
                    protocolUsed: e.target.value
                  })}
                  required
                />
              </FormControl>
              
              <Typography variant="subtitle2" gutterBottom sx={{ mt: 2 }}>
                Quality Control:
              </Typography>
              
              <FormControlLabel
                control={
                  <Checkbox
                    checked={additionalInfo.qualityControlPassed}
                    onChange={(e) => setAdditionalInfo({
                      ...additionalInfo,
                      qualityControlPassed: e.target.checked
                    })}
                  />
                }
                label="Positive controls included"
              />
              
              <FormControlLabel
                control={
                  <Checkbox
                    checked={additionalInfo.qualityControlPassed}
                    onChange={(e) => setAdditionalInfo({
                      ...additionalInfo,
                      qualityControlPassed: e.target.checked
                    })}
                  />
                }
                label="Negative controls included"
              />
              
              <FormControlLabel
                control={
                  <Checkbox
                    checked={additionalInfo.qualityControlPassed}
                    onChange={(e) => setAdditionalInfo({
                      ...additionalInfo,
                      qualityControlPassed: e.target.checked
                    })}
                  />
                }
                label="Replicate measurements performed"
              />
              
              <FormControl fullWidth margin="normal">
                <TextField
                  label="Additional Notes"
                  multiline
                  rows={4}
                  value={additionalInfo.notes}
                  onChange={(e) => setAdditionalInfo({
                    ...additionalInfo,
                    notes: e.target.value
                  })}
                />
              </FormControl>
            </Paper>
          </Box>
        );
      
      case 3:
        return (
          <Box mb={3}>
            <Typography variant="subtitle1" gutterBottom>
              Step 4: Processing Results
            </Typography>
            <Paper sx={{ p: 3 }}>
              {processResult ? (
                <Box>
                  {processResult.status === 'completed' ? (
                    <Alert severity="success" sx={{ mb: 2 }}>
                      Results file has been successfully processed!
                    </Alert>
                  ) : processResult.status === 'failed' ? (
                    <Alert severity="error" sx={{ mb: 2 }}>
                      Processing failed. Please check the errors below.
                    </Alert>
                  ) : (
                    <Alert severity="info" sx={{ mb: 2 }}>
                      Processing in progress...
                    </Alert>
                  )}
                  
                  <Typography variant="h6" gutterBottom>
                    Summary:
                  </Typography>
                  
                  <Box sx={{ mb: 2 }}>
                    <Typography>
                      Total rows: {processResult.total_rows}
                    </Typography>
                    <Typography>
                      Processed successfully: {processResult.processed_rows}
                    </Typography>
                    <Typography>
                      Failed rows: {processResult.failed_rows}
                    </Typography>
                  </Box>
                  
                  {processResult.failed_rows > 0 && processResult.errors && (
                    <Box sx={{ mb: 2 }}>
                      <Alert severity="warning" sx={{ mb: 1 }}>
                        Some rows could not be processed. Please check the error details.
                      </Alert>
                      <Box sx={{ maxHeight: '200px', overflowY: 'auto', border: '1px solid #ddd', p: 2 }}>
                        {Object.entries(processResult.errors).map(([row, errors]) => (
                          <Box key={row} sx={{ mb: 1 }}>
                            <Typography variant="subtitle2">
                              Row {row}:
                            </Typography>
                            <ul>
                              {errors.map((error, index) => (
                                <li key={index}>{error}</li>
                              ))}
                            </ul>
                          </Box>
                        ))}
                      </Box>
                    </Box>
                  )}
                  
                  <Box sx={{ mt: 3 }}>
                    <Button 
                      variant="contained" 
                      color="primary" 
                      onClick={handleComplete}
                      disabled={processResult.status !== 'completed'}
                    >
                      Complete Upload
                    </Button>
                    <Button variant="text" onClick={handleReset} sx={{ ml: 2 }}>
                      Upload Another File
                    </Button>
                  </Box>
                </Box>
              ) : (
                <Alert severity="info">
                  Processing your results file...
                </Alert>
              )}
            </Paper>
          </Box>
        );
      
      default:
        return null;
    }
  };
  
  // Steps for the stepper component
  const steps = [
    'Upload Results File',
    'Map Columns',
    'Additional Information',
    'Processing Results'
  ];
  
  return (
    <Box className={className}>
      <LoadingOverlay 
        loading={loading || uploadLoading || processLoading}
        message={
          loading ? "Reading file..." : 
          uploadLoading ? "Uploading file..." : 
          processLoading ? "Processing results..." : ""
        }
      >
        <Paper sx={{ p: 3 }}>
          <Typography variant="h5" gutterBottom>
            Upload Experimental Results
          </Typography>
          
          <Stepper activeStep={activeStep} sx={{ mb: 4 }}>
            {steps.map((label) => (
              <Step key={label}>
                <StepLabel>{label}</StepLabel>
              </Step>
            ))}
          </Stepper>
          
          {error && (
            <Alert severity="error" sx={{ mb: 3 }}>
              {error}
            </Alert>
          )}
          
          {getStepContent(activeStep)}
          
          <Box sx={{ display: 'flex', justifyContent: 'space-between', mt: 3 }}>
            <Button
              variant="outlined"
              disabled={activeStep === 0 || activeStep === steps.length - 1}
              onClick={handlePreviousStep}
            >
              Back
            </Button>
            
            <Box>
              {activeStep === steps.length - 1 ? (
                <Button
                  variant="contained"
                  color="primary"
                  onClick={handleComplete}
                  disabled={!resultId || (processResult && processResult.status !== 'completed')}
                >
                  Complete
                </Button>
              ) : (
                <Button
                  variant="contained"
                  color="primary"
                  onClick={handleNextStep}
                  disabled={
                    (activeStep === 0 && (!file || !csvData)) ||
                    (activeStep === 1 && !mappingValid) ||
                    uploadLoading || 
                    processLoading
                  }
                >
                  {uploadLoading || processLoading ? 'Processing...' : 'Next'}
                </Button>
              )}
            </Box>
          </Box>
        </Paper>
      </LoadingOverlay>
    </Box>
  );
};

export default ResultsUploader;