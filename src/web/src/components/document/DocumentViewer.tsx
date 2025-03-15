import React, { useState, useEffect, useRef } from 'react';
import {
  Box,
  Typography,
  Paper,
  Button,
  IconButton,
  Tooltip,
  CircularProgress,
  Alert,
  Chip,
  Divider,
} from '@mui/material'; // v5.0+
import {
  GetAppIcon,
  FullscreenIcon,
  FullscreenExitIcon,
  ZoomInIcon,
  ZoomOutIcon,
  HowToRegIcon,
} from '@mui/icons-material'; // v5.0+

import {
  Document,
  DocumentWithPresignedUrl,
  DocumentStatus,
  DocumentType,
} from '../../types/document.types';
import { DOCUMENT_TYPE_DESCRIPTIONS } from '../../constants/documentTypes';
import {
  getDocumentWithDownloadUrl,
  requestDocumentSignature,
  getDocumentSignatureStatus,
} from '../../api/documentApi';
import useToast from '../../hooks/useToast';

/**
 * Props for the DocumentViewer component
 */
interface DocumentViewerProps {
  /** ID of the document to view, required if document object is not provided */
  documentId?: string;
  /** Document object to view, required if documentId is not provided */
  document?: Document;
  /** Callback function called when the viewer is closed */
  onClose?: () => void;
  /** Whether to allow document signature requests */
  allowSignature?: boolean;
  /** Whether to allow document downloads */
  allowDownload?: boolean;
  /** Initial zoom level for the document */
  initialZoom?: number;
}

/**
 * Form data for signature requests
 */
interface SignatureRequestFormData {
  /** List of signers for the document */
  signers: Array<{ name: string; email: string; role?: string }>;
  /** Subject line for the signature request email */
  emailSubject: string;
  /** Message body for the signature request email */
  emailMessage: string;
}

/**
 * A component that provides a secure document viewing interface for the 
 * Molecular Data Management and CRO Integration Platform.
 */
const DocumentViewer: React.FC<DocumentViewerProps> = ({
  documentId,
  document,
  onClose,
  allowSignature = false,
  allowDownload = true,
  initialZoom = 1,
}) => {
  // State
  const [loading, setLoading] = useState<boolean>(true);
  const [error, setError] = useState<string | null>(null);
  const [documentWithUrl, setDocumentWithUrl] = useState<DocumentWithPresignedUrl | null>(null);
  const [isFullscreen, setIsFullscreen] = useState<boolean>(false);
  const [zoomLevel, setZoomLevel] = useState<number>(initialZoom);
  
  // Signature related state
  const [signatureRequestDialogOpen, setSignatureRequestDialogOpen] = useState<boolean>(false);
  const [signatureRequestFormData, setSignatureRequestFormData] = useState<SignatureRequestFormData>({
    signers: [{ name: '', email: '' }],
    emailSubject: '',
    emailMessage: '',
  });
  const [signatureStatus, setSignatureStatus] = useState<{
    status: string;
    completed: boolean;
    signers: Array<{ email: string; status: string; signed_at: string | null }>;
  } | null>(null);
  const [checkingSignatureStatus, setCheckingSignatureStatus] = useState<boolean>(false);
  
  // Get toast notification functions
  const { success, error: showError, info } = useToast();
  
  // Ref for the document viewer container
  const containerRef = useRef<HTMLDivElement>(null);
  
  // Effect to fetch document on mount
  useEffect(() => {
    fetchDocument();
  }, [documentId, document]);
  
  /**
   * Fetches document with presigned URL for viewing
   */
  const fetchDocument = async () => {
    setLoading(true);
    setError(null);
    
    try {
      // Determine document ID from props
      const id = documentId || (document ? document.id : null);
      
      if (!id) {
        throw new Error('Document ID is required');
      }
      
      const result = await getDocumentWithDownloadUrl(id);
      setDocumentWithUrl(result);
      
      // Check signature status if document requires signature
      if (result.document.signature_required || 
          result.document.status === DocumentStatus.SIGNED || 
          result.document.status === DocumentStatus.PENDING_SIGNATURE) {
        handleCheckSignatureStatus();
      }
    } catch (err) {
      const errorMsg = `Failed to load document: ${err instanceof Error ? err.message : 'Unknown error'}`;
      setError(errorMsg);
      showError(errorMsg);
    } finally {
      setLoading(false);
    }
  };
  
  /**
   * Toggles fullscreen mode for the document viewer
   */
  const handleFullscreenToggle = () => {
    if (!isFullscreen) {
      // Enter fullscreen
      if (containerRef.current && containerRef.current.requestFullscreen) {
        containerRef.current.requestFullscreen()
          .then(() => setIsFullscreen(true))
          .catch((err) => showError(`Failed to enter fullscreen: ${err instanceof Error ? err.message : 'Unknown error'}`));
      }
    } else {
      // Exit fullscreen
      if (document.exitFullscreen) {
        document.exitFullscreen()
          .then(() => setIsFullscreen(false))
          .catch((err) => showError(`Failed to exit fullscreen: ${err instanceof Error ? err.message : 'Unknown error'}`));
      }
    }
  };
  
  /**
   * Increases zoom level for the document
   */
  const handleZoomIn = () => {
    setZoomLevel((prevZoom) => Math.min(prevZoom + 0.1, 3.0));
  };
  
  /**
   * Decreases zoom level for the document
   */
  const handleZoomOut = () => {
    setZoomLevel((prevZoom) => Math.max(prevZoom - 0.1, 0.5));
  };
  
  /**
   * Handles document signature request
   */
  const handleRequestSignature = () => {
    if (!documentWithUrl) {
      showError('Document not loaded');
      return;
    }
    
    // For this implementation, we'll use a simplified signature request with default values
    const documentId = documentWithUrl.document.id;
    
    // Using simplified default values for the signature request
    const signatureRequest = {
      document_id: documentId,
      signers: [
        {
          name: 'Default Signer',
          email: 'signer@example.com',
          role: 'signer',
        }
      ],
      email_subject: `Signature Request: ${documentWithUrl.document.name}`,
      email_message: 'Please sign the attached document',
      redirect_url: null,
    };
    
    // Show confirmation before sending
    if (window.confirm('Send signature request to signer@example.com?')) {
      requestDocumentSignature(documentId, signatureRequest)
        .then(() => {
          success('Signature request sent successfully');
          // Refresh document to update status
          fetchDocument();
        })
        .catch((err) => {
          showError(`Failed to request signature: ${err instanceof Error ? err.message : 'Unknown error'}`);
        });
    }
  };
  
  /**
   * Checks the status of a document signature request
   */
  const handleCheckSignatureStatus = async () => {
    if (!documentWithUrl) {
      return;
    }
    
    setCheckingSignatureStatus(true);
    
    try {
      const documentId = documentWithUrl.document.id;
      const status = await getDocumentSignatureStatus(documentId);
      
      setSignatureStatus(status);
      
      if (status.completed) {
        success('Document has been signed by all parties');
      } else {
        info('Document signature is still pending from some parties');
      }
    } catch (err) {
      showError(`Failed to check signature status: ${err instanceof Error ? err.message : 'Unknown error'}`);
    } finally {
      setCheckingSignatureStatus(false);
    }
  };
  
  /**
   * Gets a human-readable label for a document type
   */
  const getDocumentTypeLabel = (type: DocumentType): string => {
    return DOCUMENT_TYPE_DESCRIPTIONS[type] || type;
  };
  
  /**
   * Renders the appropriate document viewer based on content type
   */
  const renderDocumentViewer = () => {
    if (!documentWithUrl) {
      return null;
    }
    
    const { document, presigned_url } = documentWithUrl;
    
    // Determine content type and render appropriate viewer
    const contentType = document.content_type || '';
    
    // Style based on zoom level and fullscreen state
    const viewerStyle = {
      transform: `scale(${zoomLevel})`,
      transformOrigin: 'center top',
      transition: 'transform 0.2s ease-in-out',
      width: isFullscreen ? '100%' : '100%',
      height: isFullscreen ? '100%' : '600px',
      boxSizing: 'border-box' as const,
    };
    
    if (contentType.includes('pdf')) {
      // Render PDF viewer
      return (
        <Box sx={{ ...viewerStyle, overflow: 'auto' }}>
          <iframe
            src={`${presigned_url}#toolbar=0`}
            title={document.name}
            width="100%"
            height="100%"
            style={{ border: 'none' }}
          />
        </Box>
      );
    } else if (contentType.includes('image')) {
      // Render image viewer
      return (
        <Box sx={{ ...viewerStyle, overflow: 'auto', textAlign: 'center' }}>
          <img
            src={presigned_url}
            alt={document.name}
            style={{ maxWidth: '100%', maxHeight: '100%' }}
          />
        </Box>
      );
    } else if (contentType.includes('text')) {
      // Render text viewer
      return (
        <Box sx={{ ...viewerStyle, overflow: 'auto' }}>
          <iframe
            src={presigned_url}
            title={document.name}
            width="100%"
            height="100%"
            style={{ border: 'none' }}
          />
        </Box>
      );
    } else {
      // Unsupported format
      return (
        <Box sx={{ p: 3, textAlign: 'center' }}>
          <Typography variant="body1">
            This document format ({contentType}) cannot be previewed directly.
            Please download the document to view it.
          </Typography>
          {allowDownload && (
            <Button
              variant="contained"
              color="primary"
              startIcon={<GetAppIcon />}
              onClick={() => window.open(presigned_url, '_blank')}
              sx={{ mt: 2 }}
            >
              Download Document
            </Button>
          )}
        </Box>
      );
    }
  };
  
  /**
   * Renders the signature status information
   */
  const renderSignatureStatus = () => {
    if (!signatureStatus) {
      return null;
    }
    
    return (
      <Box sx={{ mt: 2, p: 2, bgcolor: 'background.paper', borderRadius: 1 }}>
        <Typography variant="subtitle1" gutterBottom>
          Signature Status: {signatureStatus.completed ? 'Completed' : 'Pending'}
        </Typography>
        
        <Box sx={{ mt: 1 }}>
          <Typography variant="body2" gutterBottom>
            Signers:
          </Typography>
          {signatureStatus.signers.map((signer, index) => (
            <Box key={index} sx={{ display: 'flex', justifyContent: 'space-between', mb: 0.5 }}>
              <Typography variant="body2">{signer.email}</Typography>
              <Chip
                label={signer.signed_at ? 'Signed' : 'Pending'}
                color={signer.signed_at ? 'success' : 'warning'}
                size="small"
              />
            </Box>
          ))}
        </Box>
        
        <Button
          size="small"
          onClick={handleCheckSignatureStatus}
          disabled={checkingSignatureStatus}
          sx={{ mt: 1 }}
        >
          {checkingSignatureStatus ? 'Checking...' : 'Refresh Status'}
          {checkingSignatureStatus && (
            <CircularProgress size={16} sx={{ ml: 1 }} />
          )}
        </Button>
      </Box>
    );
  };
  
  /**
   * Validates an email address format
   */
  const validateEmail = (email: string): boolean => {
    const emailPattern = /^[a-zA-Z0-9._-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}$/;
    return emailPattern.test(email);
  };
  
  // Main render
  if (loading) {
    return (
      <Box sx={{ display: 'flex', justifyContent: 'center', p: 4 }}>
        <CircularProgress />
      </Box>
    );
  }
  
  if (error) {
    return (
      <Alert severity="error" sx={{ m: 2 }}>
        {error}
      </Alert>
    );
  }
  
  if (!documentWithUrl) {
    return (
      <Alert severity="warning" sx={{ m: 2 }}>
        No document available for display
      </Alert>
    );
  }
  
  const { document } = documentWithUrl;
  
  return (
    <Box ref={containerRef} sx={{ width: '100%', height: '100%', overflow: 'hidden' }}>
      {/* Document header */}
      <Paper elevation={1} sx={{ p: 2, mb: 2 }}>
        <Box sx={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center' }}>
          <Box>
            <Typography variant="h6" component="h2">
              {document.name}
            </Typography>
            <Typography variant="body2" color="text.secondary">
              Type: {getDocumentTypeLabel(document.type)}
            </Typography>
          </Box>
          
          <Box sx={{ display: 'flex', alignItems: 'center' }}>
            <Chip
              label={document.status}
              color={
                document.status === DocumentStatus.SIGNED
                  ? 'success'
                  : document.status === DocumentStatus.PENDING_SIGNATURE
                  ? 'warning'
                  : 'default'
              }
              size="small"
              sx={{ mr: 2 }}
            />
            
            {onClose && (
              <Button 
                onClick={onClose}
                size="small"
                variant="outlined"
              >
                Close
              </Button>
            )}
          </Box>
        </Box>
      </Paper>
      
      {/* Document viewer */}
      <Paper elevation={3} sx={{ width: '100%', height: 'calc(100% - 140px)', overflow: 'hidden' }}>
        {renderDocumentViewer()}
      </Paper>
      
      {/* Controls */}
      <Paper elevation={1} sx={{ p: 1, mt: 2, display: 'flex', justifyContent: 'space-between' }}>
        <Box>
          <Tooltip title="Zoom Out">
            <IconButton onClick={handleZoomOut} disabled={zoomLevel <= 0.5}>
              <ZoomOutIcon />
            </IconButton>
          </Tooltip>
          
          <Typography component="span" sx={{ mx: 1 }}>
            {Math.round(zoomLevel * 100)}%
          </Typography>
          
          <Tooltip title="Zoom In">
            <IconButton onClick={handleZoomIn} disabled={zoomLevel >= 3}>
              <ZoomInIcon />
            </IconButton>
          </Tooltip>
          
          <Tooltip title={isFullscreen ? "Exit Fullscreen" : "Fullscreen"}>
            <IconButton onClick={handleFullscreenToggle}>
              {isFullscreen ? <FullscreenExitIcon /> : <FullscreenIcon />}
            </IconButton>
          </Tooltip>
        </Box>
        
        <Box>
          {allowSignature && !document.is_signed && (
            <Tooltip title="Request Signature">
              <Button
                startIcon={<HowToRegIcon />}
                variant="outlined"
                onClick={handleRequestSignature}
                sx={{ mr: 1 }}
              >
                Request Signature
              </Button>
            </Tooltip>
          )}
          
          {allowDownload && (
            <Tooltip title="Download">
              <Button
                startIcon={<GetAppIcon />}
                variant="contained"
                onClick={() => window.open(documentWithUrl.presigned_url, '_blank')}
              >
                Download
              </Button>
            </Tooltip>
          )}
        </Box>
      </Paper>
      
      {/* Signature status */}
      {renderSignatureStatus()}
    </Box>
  );
};

export default DocumentViewer;