import React, { useState, useEffect, useCallback, useMemo } from 'react'; // react v18.0.0
import {
  Box,
  Paper,
  Typography,
  Button,
  IconButton,
  Tooltip,
  Dialog,
  DialogTitle,
  DialogContent,
  DialogActions,
  TextField,
  MenuItem,
  Select,
  FormControl,
  InputLabel,
  Grid,
  Divider,
} from '@mui/material'; // ^5.0.0
import VisibilityIcon from '@mui/icons-material/Visibility'; // ^5.0.0
import GetAppIcon from '@mui/icons-material/GetApp'; // ^5.0.0
import DeleteIcon from '@mui/icons-material/Delete'; // ^5.0.0
import AddIcon from '@mui/icons-material/Add'; // ^5.0.0
import FilterListIcon from '@mui/icons-material/FilterList'; // ^5.0.0

import DataTable from '../common/DataTable';
import StatusBadge from '../common/StatusBadge';
import DocumentUploader from './DocumentUploader';
import DocumentViewer from './DocumentViewer';
import {
  Document,
  DocumentStatus,
  DocumentFilterParams,
} from '../../types/document.types';
import { DocumentType, DOCUMENT_STATUS, DOCUMENT_TYPE_DESCRIPTIONS } from '../../constants/documentTypes';
import {
  getDocuments,
  getDocumentsBySubmission,
  downloadDocument,
  deleteDocument,
} from '../../api/documentApi';
import useToast from '../../hooks/useToast';

/**
 * Props interface for the DocumentList component
 */
interface DocumentListProps {
  /** Optional ID of the submission to filter documents by */
  submissionId?: string;
  /** Callback function called when a document is added */
  onDocumentAdded?: (document: Document) => void;
  /** Callback function called when a document is deleted */
  onDocumentDeleted?: (documentId: string) => void;
  /** Whether to allow document uploads */
  allowUpload?: boolean;
  /** Whether to allow document deletion */
  allowDelete?: boolean;
  /** Title to display above the document list */
  title?: string;
  /** Maximum height of the document list container */
  maxHeight?: string | number;
  /** Initial filter values */
  initialFilters?: Partial<DocumentFilterParams>;
  /** Type of CRO service for determining required documents */
  serviceType?: string;
  /** List of document types that can be uploaded */
  allowedDocumentTypes?: DocumentType[];
}

/**
 * A component that displays a list of documents with filtering, sorting, and pagination
 * @param props - Component props
 * @returns The rendered component
 */
const DocumentList: React.FC<DocumentListProps> = (props) => {
  // Destructure props
  const {
    submissionId,
    onDocumentAdded,
    onDocumentDeleted,
    allowUpload = true,
    allowDelete = true,
    title = 'Documents',
    maxHeight,
    initialFilters,
    serviceType,
    allowedDocumentTypes,
  } = props;

  // Initialize state for documents, loading, pagination, filters, selected document for viewing
  const [documents, setDocuments] = useState<Document[]>([]);
  const [totalCount, setTotalCount] = useState<number>(0);
  const [loading, setLoading] = useState<boolean>(false);
  const [page, setPage] = useState<number>(1);
  const [pageSize, setPageSize] = useState<number>(10);
  const [filters, setFilters] = useState<DocumentFilterParams>(
    initialFilters || { submission_id: submissionId || null, name_contains: null, type: null, status: null }
  );
  const [selectedDocument, setSelectedDocument] = useState<Document | null>(null);

  // Initialize state for upload dialog and view dialog visibility
  const [uploadDialogOpen, setUploadDialogOpen] = useState<boolean>(false);
  const [viewDialogOpen, setViewDialogOpen] = useState<boolean>(false);
  const [confirmDeleteDialogOpen, setConfirmDeleteDialogOpen] = useState<boolean>(false);
  const [documentToDelete, setDocumentToDelete] = useState<Document | null>(null);

  // Get toast notification functions from useToast hook
  const toast = useToast();

  /**
   * Fetches documents based on current filters and pagination
   */
  const fetchDocuments = useCallback(async () => {
    setLoading(true);
    try {
      let result;
      if (submissionId) {
        result = await getDocumentsBySubmission(submissionId, page, pageSize);
      } else {
        result = await getDocuments(filters, page, pageSize);
      }
      setDocuments(result.documents);
      setTotalCount(result.total);
    } catch (err) {
      toast.error(`Failed to fetch documents: ${toast.formatError(err)}`);
    } finally {
      setLoading(false);
    }
  }, [filters, page, pageSize, submissionId, toast]);

  // Implement useEffect to fetch documents when component mounts or filters/pagination change
  useEffect(() => {
    fetchDocuments();
  }, [fetchDocuments]);

  /**
   * Gets a human-readable label for a document type
   * @param type The document type
   * @returns Human-readable document type label
   */
  const getDocumentTypeLabel = (type: DocumentType): string => {
    return DOCUMENT_TYPE_DESCRIPTIONS[type] || type;
  };

  /**
   * Formats file size in bytes to a human-readable string
   * @param bytes File size in bytes
   * @returns Formatted file size string
   */
  const formatFileSize = (bytes: number | null): string => {
    if (bytes === null) return 'N/A';
    if (bytes < 1024) return `${bytes} bytes`;
    const kb = bytes / 1024;
    if (kb < 1024) return `${kb.toFixed(2)} KB`;
    const mb = kb / 1024;
    if (mb < 1024) return `${mb.toFixed(2)} MB`;
    const gb = mb / 1024;
    return `${gb.toFixed(2)} GB`;
  };

  /**
   * Gets the color code for a document status
   * @param status The document status
   * @returns Color code for the status
   */
  const getDocumentStatusColor = (status: DocumentStatus): string => {
    switch (status) {
      case DocumentStatus.DRAFT:
        return '#9e9e9e'; // Gray
      case DocumentStatus.PENDING_SIGNATURE:
        return '#ff9800'; // Orange
      case DocumentStatus.SIGNED:
        return '#4caf50'; // Green
      case DocumentStatus.REJECTED:
      case DocumentStatus.EXPIRED:
        return '#f44336'; // Red
      case DocumentStatus.ARCHIVED:
        return '#607d8b'; // Blue-gray
      default:
        return '#9e9e9e'; // Default to gray
    }
  };

  // Define table columns with document properties and action buttons
  const columns = useMemo(() => [
    {
      id: 'name',
      label: 'Name',
      sortable: true,
      width: '25%',
    },
    {
      id: 'type',
      label: 'Type',
      sortable: true,
      width: '20%',
      format: (value: DocumentType) => getDocumentTypeLabel(value),
    },
    {
      id: 'status',
      label: 'Status',
      sortable: true,
      width: '15%',
      renderCell: (row: Document) => (
        <StatusBadge status={row.status} statusType="custom" customColor={getDocumentStatusColor(row.status)} />
      ),
    },
    {
      id: 'file_size',
      label: 'Size',
      sortable: true,
      width: '10%',
      format: (value: number) => formatFileSize(value),
    },
    {
      id: 'uploaded_at',
      label: 'Uploaded',
      sortable: true,
      width: '15%',
      format: (value: string) => new Date(value).toLocaleDateString(),
    },
    {
      id: 'actions',
      label: 'Actions',
      sortable: false,
      width: '15%',
      renderCell: (row: Document) => (
        <Box>
          <Tooltip title="View">
            <IconButton onClick={() => handleViewDocument(row)}>
              <VisibilityIcon />
            </IconButton>
          </Tooltip>
          <Tooltip title="Download">
            <IconButton onClick={() => handleDownloadDocument(row)}>
              <GetAppIcon />
            </IconButton>
          </Tooltip>
          {allowDelete && (
            <Tooltip title="Delete">
              <IconButton onClick={() => handleDeleteDocument(row)}>
                <DeleteIcon />
              </IconButton>
            </Tooltip>
          )}
        </Box>
      ),
    },
  ], [allowDelete, handleDownloadDocument, handleDeleteDocument, handleViewDocument]);

  /**
   * Handles page change in pagination
   * @param newPage New page number
   */
  const handlePageChange = (newPage: number) => {
    setPage(newPage);
  };

  /**
   * Handles page size change in pagination
   * @param newPageSize New page size
   */
  const handlePageSizeChange = (newPageSize: number) => {
    setPageSize(newPageSize);
    setPage(1); // Reset to first page
  };

  /**
   * Handles changes to document filters
   * @param filterName Name of the filter to change
   * @param value New value for the filter
   */
  const handleFilterChange = (filterName: keyof DocumentFilterParams, value: any) => {
    setFilters(prevFilters => ({
      ...prevFilters,
      [filterName]: value,
    }));
    setPage(1); // Reset to first page
  };

  /**
   * Handles opening the document viewer
   * @param document Document to view
   */
  const handleViewDocument = (document: Document) => {
    setSelectedDocument(document);
    setViewDialogOpen(true);
  };

  /**
   * Handles document download
   * @param document Document to download
   */
  const handleDownloadDocument = async (document: Document) => {
    try {
      await downloadDocument(document.id, document.name);
      toast.success('Document downloaded successfully');
    } catch (err) {
      toast.error(`Failed to download document: ${toast.formatError(err)}`);
    }
  };

  /**
   * Handles document deletion
   * @param document Document to delete
   */
  const handleDeleteDocument = (document: Document) => {
    setDocumentToDelete(document);
    setConfirmDeleteDialogOpen(true);
  };

  /**
   * Confirms and executes document deletion
   */
  const confirmDeleteDocument = async () => {
    if (!documentToDelete) return;

    try {
      await deleteDocument(documentToDelete.id);
      setConfirmDeleteDialogOpen(false);
      toast.success('Document deleted successfully');
      onDocumentDeleted?.(documentToDelete.id);
      fetchDocuments();
    } catch (err) {
      toast.error(`Failed to delete document: ${toast.formatError(err)}`);
    } finally {
      setDocumentToDelete(null);
    }
  };

  /**
   * Opens the document upload dialog
   */
  const handleOpenUploadDialog = () => {
    setUploadDialogOpen(true);
  };

  /**
   * Closes the document upload dialog
   */
  const handleCloseUploadDialog = () => {
    setUploadDialogOpen(false);
  };

  /**
   * Closes the document viewer dialog
   */
  const handleCloseViewDialog = () => {
    setViewDialogOpen(false);
    setSelectedDocument(null);
  };

  /**
   * Handles completion of document upload
   * @param document Uploaded document
   */
  const handleUploadComplete = (document: Document) => {
    handleCloseUploadDialog();
    onDocumentAdded?.(document);
    fetchDocuments();
    toast.success('Document uploaded successfully');
  };

  return (
    <Box>
      <Box sx={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', mb: 2 }}>
        <Typography variant="h6">{title}</Typography>
        <Box>
          <Tooltip title="Filter Documents">
            <IconButton>
              <FilterListIcon />
            </IconButton>
          </Tooltip>
          {allowUpload && (
            <Button
              variant="contained"
              startIcon={<AddIcon />}
              onClick={handleOpenUploadDialog}
            >
              Add Document
            </Button>
          )}
        </Box>
      </Box>

      <DataTable
        columns={columns}
        data={documents}
        loading={loading}
        totalCount={totalCount}
        currentPage={page}
        pageSize={pageSize}
        onPageChange={handlePageChange}
        onPageSizeChange={handlePageSizeChange}
        maxHeight={maxHeight}
        getRowId={(row) => row.id}
      />

      {/* Upload Dialog */}
      <Dialog open={uploadDialogOpen} onClose={handleCloseUploadDialog} fullWidth maxWidth="md">
        <DialogTitle>Upload Document</DialogTitle>
        <DialogContent>
          <DocumentUploader
            onUploadComplete={handleUploadComplete}
            submissionId={submissionId}
            serviceType={serviceType}
            allowedDocumentTypes={allowedDocumentTypes}
          />
        </DialogContent>
        <DialogActions>
          <Button onClick={handleCloseUploadDialog}>Cancel</Button>
        </DialogActions>
      </Dialog>

      {/* View Dialog */}
      <Dialog
        open={viewDialogOpen}
        onClose={handleCloseViewDialog}
        fullWidth
        maxWidth="lg"
      >
        <DialogContent>
          <DocumentViewer
            document={selectedDocument}
            onClose={handleCloseViewDialog}
          />
        </DialogContent>
      </Dialog>

      {/* Confirm Delete Dialog */}
      <Dialog
        open={confirmDeleteDialogOpen}
        onClose={() => setConfirmDeleteDialogOpen(false)}
        aria-labelledby="alert-dialog-title"
        aria-describedby="alert-dialog-description"
      >
        <DialogTitle id="alert-dialog-title">Confirm Delete</DialogTitle>
        <DialogContent>
          <Typography>Are you sure you want to delete this document?</Typography>
        </DialogContent>
        <DialogActions>
          <Button onClick={() => setConfirmDeleteDialogOpen(false)}>Cancel</Button>
          <Button onClick={confirmDeleteDocument} autoFocus>
            Delete
          </Button>
        </DialogActions>
      </Dialog>
    </Box>
  );
};

export default DocumentList;