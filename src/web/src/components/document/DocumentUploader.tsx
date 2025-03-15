import React, { useState, useEffect, useCallback } from 'react';
import {
  Box,
  Typography,
  Paper,
  Button,
  TextField,
  FormControl,
  InputLabel,
  Select,
  MenuItem,
  FormHelperText,
  Checkbox,
  FormControlLabel,
  CircularProgress,
  Alert
} from '@mui/material'; // v5.0+

import DragDropZone from '../common/DragDropZone';
import {
  DocumentType,
  getDocumentTypeInfo,
  isSignatureRequired
} from '../../constants/documentTypes';
import {
  DocumentCreateRequest,
  DocumentUploadResult,
  Document
} from '../../types/document.types';
import {
  createDocumentUploadRequest,
  uploadDocumentFile
} from '../../api/documentApi';
import useToast from '../../hooks/useToast';

/**
 * Props interface for DocumentUploader component
 */
interface DocumentUploaderProps {
  /** Callback function called when document upload is complete */
  onUploadComplete: (document: Document) => void;
  /** ID of the submission the document is associated with */
  submissionId: string;
  /** Type of CRO service for determining required documents */
  serviceType?: string | null;
  /** List of document types that can be uploaded */
  allowedDocumentTypes?: DocumentType[];
  /** Pre-selected document type */
  initialDocumentType?: DocumentType;
  /** Maximum allowed file size in megabytes */
  maxFileSizeMB?: number;
}

/**
 * Interface for document form data
 */
interface DocumentFormData {
  name: string;
  type: DocumentType;
  description: string;
  signatureRequired: boolean;
}

/**
 * A component that provides a user interface for uploading documents to the
 * Molecular Data Management and CRO Integration Platform.
 */
const DocumentUploader: React.FC<DocumentUploaderProps> = ({
  onUploadComplete,
  submissionId,
  serviceType = null,
  allowedDocumentTypes,
  initialDocumentType,
  maxFileSizeMB = 50
}) => {
  // Form state
  const [formData, setFormData] = useState<DocumentFormData>({
    name: '',
    type: initialDocumentType || DocumentType.ADDITIONAL_INSTRUCTIONS,
    description: '',
    signatureRequired: false
  });

  // File and status state
  const [file, setFile] = useState<File | null>(null);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState('');
  const [success, setSuccess] = useState(false);
  
  // Hooks
  const toast = useToast();

  // Update signature required when document type changes
  useEffect(() => {
    if (formData.type) {
      const isRequired = isSignatureRequired(formData.type);
      setFormData(prev => ({
        ...prev,
        signatureRequired: isRequired
      }));
    }
  }, [formData.type]);

  /**
   * Handles document type selection change
   */
  const handleDocumentTypeChange = (e: React.ChangeEvent<HTMLInputElement>) => {
    const selectedType = e.target.value as DocumentType;
    const typeInfo = getDocumentTypeInfo(selectedType, serviceType);
    
    setFormData(prev => ({
      ...prev,
      type: selectedType,
      signatureRequired: typeInfo.signature_required
    }));
  };

  /**
   * Handles document name input change
   */
  const handleNameChange = (e: React.ChangeEvent<HTMLInputElement>) => {
    setFormData(prev => ({
      ...prev,
      name: e.target.value
    }));
  };

  /**
   * Handles document description input change
   */
  const handleDescriptionChange = (e: React.ChangeEvent<HTMLInputElement>) => {
    setFormData(prev => ({
      ...prev,
      description: e.target.value
    }));
  };

  /**
   * Handles signature required checkbox change
   */
  const handleSignatureRequiredChange = (e: React.ChangeEvent<HTMLInputElement>) => {
    setFormData(prev => ({
      ...prev,
      signatureRequired: e.target.checked
    }));
  };

  /**
   * Handles file selection from DragDropZone
   */
  const handleFileAccepted = (files: File[]) => {
    if (files.length > 0) {
      setFile(files[0]);
      
      // If no name is set, use the file name without extension
      if (!formData.name) {
        const fileName = files[0].name.split('.').slice(0, -1).join('.');
        setFormData(prev => ({
          ...prev,
          name: fileName
        }));
      }
      
      // Reset error and success states
      setError('');
      setSuccess(false);
    }
  };

  /**
   * Validates form data before submission
   */
  const validateForm = (): boolean => {
    if (!formData.name.trim()) {
      setError('Document name is required');
      return false;
    }
    
    if (!file) {
      setError('Please select a file to upload');
      return false;
    }
    
    return true;
  };

  /**
   * Resets form state after successful upload
   */
  const resetForm = () => {
    setFormData({
      name: '',
      type: initialDocumentType || DocumentType.ADDITIONAL_INSTRUCTIONS,
      description: '',
      signatureRequired: isSignatureRequired(initialDocumentType || DocumentType.ADDITIONAL_INSTRUCTIONS)
    });
    setFile(null);
    setError('');
  };

  /**
   * Uploads the document to the server
   */
  const uploadDocument = async (): Promise<void> => {
    setLoading(true);
    
    try {
      // Create document request object
      const documentRequest: DocumentCreateRequest = {
        name: formData.name,
        type: formData.type,
        submission_id: submissionId,
        description: formData.description || null,
        signature_required: formData.signatureRequired,
        content_type: file?.type || null,
        file_size: file?.size || null
      };
      
      // Create upload request
      const uploadResult = await createDocumentUploadRequest(documentRequest);
      
      // Upload the file
      if (file) {
        const uploadedDocument = await uploadDocumentFile(uploadResult, file);
        
        // Call onUploadComplete callback
        onUploadComplete(uploadedDocument);
        
        // Show success state
        setSuccess(true);
        toast.success('Document uploaded successfully');
        
        // Reset form for new upload
        resetForm();
      }
    } catch (error) {
      setError(toast.formatError(error));
      toast.error('Failed to upload document: ' + toast.formatError(error));
    } finally {
      setLoading(false);
    }
  };

  /**
   * Handles form submission
   */
  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    
    // Validate form
    if (!validateForm()) {
      return;
    }
    
    // Upload document
    await uploadDocument();
  };

  // Determine which document types to show
  const documentTypesToShow = allowedDocumentTypes || Object.values(DocumentType);

  return (
    <Box component="form" onSubmit={handleSubmit} noValidate sx={{ width: '100%' }}>
      <Typography variant="h6" gutterBottom>
        Upload Document
      </Typography>
      
      {/* Document Type Selection */}
      <FormControl fullWidth margin="normal" required>
        <InputLabel id="document-type-label">Document Type</InputLabel>
        <Select
          labelId="document-type-label"
          id="document-type"
          value={formData.type}
          label="Document Type"
          onChange={handleDocumentTypeChange}
          disabled={loading}
        >
          {documentTypesToShow.map((type) => {
            const typeInfo = getDocumentTypeInfo(type, serviceType);
            return (
              <MenuItem key={type} value={type}>
                {typeInfo.description.split(' - ')[0]}
                {typeInfo.required && ' (Required)'}
              </MenuItem>
            );
          })}
        </Select>
        <FormHelperText>
          {getDocumentTypeInfo(formData.type, serviceType).description.split(' - ')[1] || ''}
        </FormHelperText>
      </FormControl>
      
      {/* Document Name */}
      <TextField
        margin="normal"
        required
        fullWidth
        id="document-name"
        label="Document Name"
        name="name"
        value={formData.name}
        onChange={handleNameChange}
        disabled={loading}
        error={!!error && error.includes('name')}
        helperText={error && error.includes('name') ? error : ''}
      />
      
      {/* Document Description */}
      <TextField
        margin="normal"
        fullWidth
        id="document-description"
        label="Description"
        name="description"
        value={formData.description}
        onChange={handleDescriptionChange}
        multiline
        rows={2}
        disabled={loading}
      />
      
      {/* Signature Required */}
      <FormControlLabel
        control={
          <Checkbox
            checked={formData.signatureRequired}
            onChange={handleSignatureRequiredChange}
            disabled={loading || isSignatureRequired(formData.type)}
            name="signatureRequired"
            color="primary"
          />
        }
        label="Requires Electronic Signature"
      />
      
      {/* File Upload */}
      <Box mt={2} mb={2}>
        <DragDropZone
          onFilesAccepted={handleFileAccepted}
          acceptedFileTypes={['.pdf', '.doc', '.docx', '.xls', '.xlsx', '.ppt', '.pptx', '.txt']}
          maxFileSizeMB={maxFileSizeMB}
          loading={loading}
        >
          <Box sx={{ textAlign: 'center', p: 2 }}>
            <Typography variant="h6" gutterBottom>
              Drag and drop your document here
            </Typography>
            <Typography variant="body2" color="textSecondary" gutterBottom>
              or
            </Typography>
            <Button 
              variant="contained" 
              component="span"
              disabled={loading}
            >
              Browse Files
            </Button>
            <Typography variant="caption" display="block" sx={{ mt: 1 }}>
              Supported formats: PDF, DOC, DOCX, XLS, XLSX, PPT, PPTX, TXT
            </Typography>
            <Typography variant="caption" display="block">
              Maximum file size: {maxFileSizeMB} MB
            </Typography>
          </Box>
        </DragDropZone>
      </Box>
      
      {/* File Info */}
      {file && (
        <Box mt={2} p={2} bgcolor="background.paper" borderRadius={1}>
          <Typography variant="subtitle2">Selected File:</Typography>
          <Typography variant="body2">{file.name} ({(file.size / (1024 * 1024)).toFixed(2)} MB)</Typography>
        </Box>
      )}
      
      {/* Error and Success Messages */}
      {error && !error.includes('name') && (
        <Alert severity="error" sx={{ mt: 2, mb: 2 }}>
          {error}
        </Alert>
      )}
      
      {success && (
        <Alert severity="success" sx={{ mt: 2, mb: 2 }}>
          Document uploaded successfully
        </Alert>
      )}
      
      {/* Submit Button */}
      <Button
        type="submit"
        fullWidth
        variant="contained"
        color="primary"
        disabled={loading || !file}
        sx={{ mt: 2 }}
      >
        {loading ? (
          <Box sx={{ display: 'flex', alignItems: 'center' }}>
            <CircularProgress size={24} sx={{ mr: 1 }} />
            Uploading...
          </Box>
        ) : 'Upload Document'}
      </Button>
    </Box>
  );
};

export default DocumentUploader;