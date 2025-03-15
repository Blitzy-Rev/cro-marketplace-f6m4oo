import React, { useState, useRef, useCallback } from 'react';
import {
  Box,
  Typography,
  Paper,
  Button,
  CircularProgress,
  Alert
} from '@mui/material';
import CloudUploadIcon from '@mui/icons-material/CloudUpload';
import { validateFileType, validateFileSize } from '../../utils/validators';

/**
 * Props interface for the DragDropZone component
 */
interface DragDropZoneProps {
  /** Callback function called when files are accepted */
  onFilesAccepted: (files: File[]) => void;
  /** Array of accepted file extensions (e.g., ['.csv']) */
  acceptedFileTypes?: string[];
  /** Maximum allowed file size in megabytes */
  maxFileSizeMB?: number;
  /** Whether multiple file selection is allowed */
  multiple?: boolean;
  /** Whether the component is in loading state */
  loading?: boolean;
  /** Custom content to render inside the drop zone */
  children?: React.ReactNode;
}

/**
 * A reusable drag and drop component for file uploads with validation
 */
const DragDropZone: React.FC<DragDropZoneProps> = ({
  onFilesAccepted,
  acceptedFileTypes,
  maxFileSizeMB,
  multiple = false,
  loading = false,
  children
}) => {
  const [isDragging, setIsDragging] = useState(false);
  const [error, setError] = useState('');
  const fileInputRef = useRef<HTMLInputElement>(null);

  /**
   * Validates files against type and size constraints
   */
  const validateFiles = useCallback((files: FileList | File[]): boolean => {
    // Clear any existing error
    setError('');
    
    if (!files || files.length === 0) {
      setError('Please select a file');
      return false;
    }
    
    // If multiple is false, ensure only one file is selected
    if (multiple === false && files.length > 1) {
      setError('Only one file can be uploaded at a time');
      return false;
    }
    
    // Convert FileList to array for processing
    const filesArray = Array.from(files);
    
    // Validate file types if acceptedFileTypes is provided
    if (acceptedFileTypes && acceptedFileTypes.length > 0) {
      for (const file of filesArray) {
        if (!validateFileType(file, acceptedFileTypes)) {
          setError(`File type not supported. Accepted types: ${acceptedFileTypes.join(', ')}`);
          return false;
        }
      }
    }
    
    // Validate file size if maxFileSizeMB is provided
    if (maxFileSizeMB) {
      for (const file of filesArray) {
        if (!validateFileSize(file, maxFileSizeMB)) {
          setError(`File size exceeds the maximum limit of ${maxFileSizeMB} MB`);
          return false;
        }
      }
    }
    
    return true;
  }, [acceptedFileTypes, maxFileSizeMB, multiple]);

  /**
   * Handles drag enter event and updates visual state
   */
  const handleDragEnter = useCallback((e: React.DragEvent<HTMLDivElement>) => {
    e.preventDefault();
    setIsDragging(true);
  }, []);

  /**
   * Handles drag leave event and updates visual state
   */
  const handleDragLeave = useCallback((e: React.DragEvent<HTMLDivElement>) => {
    e.preventDefault();
    setIsDragging(false);
  }, []);

  /**
   * Handles drag over event
   */
  const handleDragOver = useCallback((e: React.DragEvent<HTMLDivElement>) => {
    e.preventDefault(); // Prevent default to allow drop
  }, []);

  /**
   * Handles file drop event
   */
  const handleDrop = useCallback((e: React.DragEvent<HTMLDivElement>) => {
    e.preventDefault();
    setIsDragging(false);
    
    const files = e.dataTransfer.files;
    if (validateFiles(files)) {
      // Convert FileList to array
      const filesArray = Array.from(files);
      onFilesAccepted(filesArray);
    }
  }, [onFilesAccepted, validateFiles]);

  /**
   * Handles file selection via the file input
   */
  const handleFileInputChange = useCallback((e: React.ChangeEvent<HTMLInputElement>) => {
    const files = e.target.files;
    
    if (files && validateFiles(files)) {
      // Convert FileList to array
      const filesArray = Array.from(files);
      onFilesAccepted(filesArray);
    }
    
    // Reset the input value to allow selecting the same file again
    if (fileInputRef.current) {
      fileInputRef.current.value = '';
    }
  }, [onFilesAccepted, validateFiles]);

  /**
   * Triggers the hidden file input click event
   */
  const handleBrowseClick = useCallback(() => {
    if (fileInputRef.current) {
      fileInputRef.current.click();
    }
  }, []);

  return (
    <Paper 
      elevation={2}
      sx={{
        p: 3,
        border: '2px dashed',
        borderColor: isDragging ? 'primary.main' : 'grey.400',
        backgroundColor: isDragging ? 'rgba(25, 118, 210, 0.08)' : 'background.paper',
        transition: 'all 0.3s ease',
        position: 'relative',
        minHeight: 150,
        display: 'flex',
        flexDirection: 'column',
        alignItems: 'center',
        justifyContent: 'center',
      }}
      onDragEnter={handleDragEnter}
      onDragLeave={handleDragLeave}
      onDragOver={handleDragOver}
      onDrop={handleDrop}
    >
      {loading && (
        <Box 
          sx={{ 
            position: 'absolute', 
            top: 0, 
            left: 0, 
            right: 0, 
            bottom: 0, 
            display: 'flex', 
            alignItems: 'center', 
            justifyContent: 'center', 
            backgroundColor: 'rgba(255, 255, 255, 0.8)',
            zIndex: 1
          }}
        >
          <CircularProgress />
        </Box>
      )}
      
      {children || (
        <Box sx={{ textAlign: 'center' }}>
          <CloudUploadIcon sx={{ fontSize: 48, color: 'primary.main', mb: 2 }} />
          <Typography variant="h6" gutterBottom>
            Drag and drop your {acceptedFileTypes?.includes('.csv') ? 'CSV file' : 'file'} here
          </Typography>
          <Typography variant="body2" color="textSecondary" gutterBottom>
            or
          </Typography>
          <Button 
            variant="contained" 
            color="primary" 
            disabled={loading}
            onClick={(e) => {
              e.stopPropagation();
              handleBrowseClick();
            }}
          >
            Browse
          </Button>
          {acceptedFileTypes && (
            <Typography variant="caption" display="block" sx={{ mt: 2 }}>
              Supported format: {acceptedFileTypes.includes('.csv') ? 
                'CSV with SMILES column and property columns' : 
                `Files with extension ${acceptedFileTypes.join(', ')}`}
            </Typography>
          )}
          {maxFileSizeMB && (
            <Typography variant="caption" display="block">
              Maximum file size: {maxFileSizeMB} MB
            </Typography>
          )}
        </Box>
      )}
      
      <input 
        type="file" 
        ref={fileInputRef} 
        onChange={handleFileInputChange} 
        style={{ display: 'none' }}
        accept={acceptedFileTypes?.join(',')}
        multiple={multiple}
      />
      
      {error && (
        <Alert severity="error" sx={{ mt: 2, width: '100%' }}>
          {error}
        </Alert>
      )}
    </Paper>
  );
};

export default DragDropZone;