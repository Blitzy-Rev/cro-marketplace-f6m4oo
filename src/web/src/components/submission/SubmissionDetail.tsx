import React, { useState, useEffect, useCallback } from 'react'; // react ^18.0.0
import {
  Box,
  Paper,
  Typography,
  Tabs,
  Tab,
  Button,
  TextField,
  Grid,
  Divider,
  Dialog,
  DialogTitle,
  DialogContent,
  DialogActions,
  CircularProgress,
  Chip
} from '@mui/material'; // @mui/material ^5.0.0
import { useParams, useNavigate } from 'react-router-dom'; // react-router-dom ^6.0.0

import SubmissionStatus from './SubmissionStatus';
import DocumentList from '../document/DocumentList';
import MoleculeTable from '../molecule/MoleculeTable';
import ConfirmDialog from '../common/ConfirmDialog';
import LoadingOverlay from '../common/LoadingOverlay';
import { useAppDispatch, useAppSelector } from '../../store';
import {
  fetchSubmission,
  fetchSubmissionDocumentRequirements,
  performAction,
  submitPricingInfo,
  approveSubmissionWithPricing,
  rejectSubmissionRequest,
  cancelSubmissionRequest,
  startExperimentProcess,
  completeSubmissionProcess,
  selectSelectedSubmission,
  selectDocumentRequirements,
  selectSubmissionLoading
} from '../../features/submission/submissionSlice';
import { Submission, SubmissionWithDocumentRequirements } from '../../types/submission.types';
import { SubmissionStatus as SubmissionStatusEnum, SubmissionAction } from '../../constants/submissionStatus';
import { getStatusDisplayName } from '../../constants/submissionStatus';
import useToast from '../../hooks/useToast';
import useAuth from '../../hooks/useAuth';

/**
 * Interface for confirmation dialog state
 */
interface ConfirmationDialogState {
  open: boolean;
  title: string;
  message: string;
  action: () => void;
}

/**
 * Interface for pricing form state
 */
interface PricingFormState {
  open: boolean;
  price: number | string;
  currency: string;
  turnaroundDays: number | string;
  comment: string;
}

/**
 * Main component for displaying detailed information about a CRO submission
 */
const SubmissionDetail: React.FC = () => {
  // Get submission ID from URL parameters
  const { id } = useParams<{ id: string }>();

  // Get navigation function
  const navigate = useNavigate();

  // Get Redux dispatch function
  const dispatch = useAppDispatch();

  // Get current user information
  const { user, hasPermission } = useAuth();

  // Get toast notification functions
  const toast = useToast();

  // Select submission data, document requirements, and loading state from Redux
  const submission = useAppSelector(selectSelectedSubmission);
  const documentRequirements = useAppSelector(selectDocumentRequirements);
  const loading = useAppSelector(selectSubmissionLoading);

  // Initialize state for active tab, confirmation dialogs, and form inputs
  const [activeTab, setActiveTab] = useState(0);
  const [confirmDialog, setConfirmDialog] = useState<ConfirmationDialogState>({
    open: false,
    title: '',
    message: '',
    action: () => {}
  });
  const [pricingForm, setPricingForm] = useState<PricingFormState>({
    open: false,
    price: '',
    currency: 'USD',
    turnaroundDays: '',
    comment: ''
  });
  const [commentInput, setCommentInput] = useState('');

  // Fetch submission data and document requirements when component mounts or ID changes
  useEffect(() => {
    if (id) {
      dispatch(fetchSubmission(id));
      dispatch(fetchSubmissionDocumentRequirements(id));
    }
  }, [id, dispatch]);

  /**
   * Handles tab change events
   */
  const handleTabChange = (event: React.SyntheticEvent, newValue: number) => {
    setActiveTab(newValue);
  };

  /**
   * Handles submission of a draft submission to CRO
   */
  const handleSubmit = () => {
    setConfirmDialog({
      open: true,
      title: 'Submit Submission',
      message: 'Are you sure you want to submit this submission to the CRO?',
      action: () => {
        if (id) {
          dispatch(performAction({ id, action: SubmissionAction.SUBMIT }));
        }
      }
    });
  };

  /**
   * Handles opening the pricing form dialog for CRO users
   */
  const handleProvidePricing = () => {
    if (!submission) return;

    setPricingForm({
      open: true,
      price: submission.price !== null ? submission.price : '',
      currency: submission.price_currency || 'USD',
      turnaroundDays: submission.estimated_turnaround_days !== null ? submission.estimated_turnaround_days : '',
      comment: submission.description || ''
    });
  };

  /**
   * Handles submission of pricing information by CRO
   */
  const handlePricingSubmit = () => {
    if (!id) return;

    // Validate form inputs
    if (!pricingForm.price || !pricingForm.currency || !pricingForm.turnaroundDays) {
      toast.error('Please fill in all required fields');
      return;
    }

    // Dispatch submitPricingInfo action with form values
    dispatch(
      submitPricingInfo({
        id,
        price: Number(pricingForm.price),
        price_currency: pricingForm.currency,
        estimated_turnaround_days: Number(pricingForm.turnaroundDays),
        comment: pricingForm.comment
      })
    );

    // Close pricing form dialog on success
    setPricingForm({ ...pricingForm, open: false });
  };

  /**
   * Handles approval of submission with pricing by pharma user
   */
  const handleApprove = () => {
    setConfirmDialog({
      open: true,
      title: 'Approve Submission',
      message: 'Are you sure you want to approve this submission with the provided pricing?',
      action: () => {
        if (id) {
          dispatch(
            approveSubmissionWithPricing({
              id,
              comment: commentInput
            })
          );
        }
      }
    });
  };

  /**
   * Handles rejection of a submission
   */
  const handleReject = () => {
    setConfirmDialog({
      open: true,
      title: 'Reject Submission',
      message: 'Are you sure you want to reject this submission?',
      action: () => {
        if (id) {
          dispatch(
            rejectSubmissionRequest({
              id,
              comment: commentInput
            })
          );
        }
      }
    });
  };

  /**
   * Handles cancellation of a submission
   */
  const handleCancel = () => {
    setConfirmDialog({
      open: true,
      title: 'Cancel Submission',
      message: 'Are you sure you want to cancel this submission?',
      action: () => {
        if (id) {
          dispatch(
            cancelSubmissionRequest({
              id,
              comment: commentInput
            })
          );
        }
      }
    });
  };

  /**
   * Handles starting the experiment process by CRO
   */
  const handleStartExperiment = () => {
    setConfirmDialog({
      open: true,
      title: 'Start Experiment',
      message: 'Are you sure you want to start the experiment process for this submission?',
      action: () => {
        if (id) {
          dispatch(
            startExperimentProcess({
              id,
              comment: commentInput
            })
          );
        }
      }
    });
  };

  /**
   * Handles marking a submission as completed by CRO
   */
  const handleCompleteSubmission = () => {
    setConfirmDialog({
      open: true,
      title: 'Complete Submission',
      message: 'Are you sure you want to mark this submission as completed?',
      action: () => {
        if (id) {
          dispatch(
            completeSubmissionProcess({
              id,
              comment: commentInput
            })
          );
        }
      }
    });
  };

  /**
   * Handles document addition event
   */
  const handleDocumentAdded = useCallback(() => {
    if (id) {
      dispatch(fetchSubmission(id));
      dispatch(fetchSubmissionDocumentRequirements(id));
    }
  }, [id, dispatch]);

  /**
   * Handles document deletion event
   */
  const handleDocumentDeleted = useCallback(() => {
    if (id) {
      dispatch(fetchSubmission(id));
      dispatch(fetchSubmissionDocumentRequirements(id));
    }
  }, [id, dispatch]);

  /**
   * Handles closing the confirmation dialog
   */
  const handleCloseConfirmDialog = () => {
    setConfirmDialog({ ...confirmDialog, open: false });
  };

  /**
   * Handles closing the pricing form dialog
   */
  const handleClosePricingForm = () => {
    setPricingForm({ ...pricingForm, open: false });
  };

  // Render loading overlay when data is being fetched
  if (loading) {
    return <LoadingOverlay />;
  }

  // Render error message if submission not found
  if (!submission) {
    return <Typography variant="h6">Submission not found</Typography>;
  }

  /**
   * Determines which actions are available based on submission status and user role
   */
  const getAvailableActions = () => {
    const actions = [];

    if (submission.status === SubmissionStatusEnum.DRAFT && hasPermission('submission.submit')) {
      actions.push({ action: SubmissionAction.SUBMIT, label: 'Submit to CRO', color: 'primary', disabled: false });
    }

    if (submission.status === SubmissionStatusEnum.PENDING_REVIEW && hasPermission('submission.provide_pricing')) {
        actions.push({ action: SubmissionAction.PROVIDE_PRICING, label: 'Provide Pricing', color: 'primary', disabled: false });
    }

    if (submission.status === SubmissionStatusEnum.PRICING_PROVIDED && hasPermission('submission.approve')) {
        actions.push({ action: SubmissionAction.APPROVE, label: 'Approve Pricing', color: 'success', disabled: false });
        actions.push({ action: SubmissionAction.REJECT, label: 'Reject Submission', color: 'error', disabled: false });
    }

    if (submission.status === SubmissionStatusEnum.APPROVED && hasPermission('submission.start_experiment')) {
        actions.push({ action: SubmissionAction.START_EXPERIMENT, label: 'Start Experiment', color: 'primary', disabled: false });
    }

    if (submission.status === SubmissionStatusEnum.IN_PROGRESS && hasPermission('submission.upload_results')) {
        actions.push({ action: SubmissionAction.UPLOAD_RESULTS, label: 'Upload Results', color: 'primary', disabled: false });
    }

    if (submission.status === SubmissionStatusEnum.RESULTS_UPLOADED && hasPermission('submission.review_results')) {
        actions.push({ action: SubmissionAction.REVIEW_RESULTS, label: 'Review Results', color: 'primary', disabled: false });
    }

    if (submission.status === SubmissionStatusEnum.RESULTS_REVIEWED && hasPermission('submission.complete')) {
        actions.push({ action: SubmissionAction.COMPLETE, label: 'Complete Submission', color: 'success', disabled: false });
    }

    if (submission.status !== SubmissionStatusEnum.COMPLETED && hasPermission('submission.cancel')) {
        actions.push({ action: SubmissionAction.CANCEL, label: 'Cancel Submission', color: 'warning', disabled: false });
    }

    return actions;
  };

  /**
   * Renders action buttons based on available actions
   */
  const renderActionButtons = () => {
    const availableActions = getAvailableActions();

    return (
      <Box sx={{ mt: 2, display: 'flex', gap: 1 }}>
        {availableActions.map((action) => (
          <Button
            key={action.action}
            variant="contained"
            color={action.color}
            onClick={() => {
              switch (action.action) {
                case SubmissionAction.SUBMIT:
                  handleSubmit();
                  break;
                case SubmissionAction.PROVIDE_PRICING:
                  handleProvidePricing();
                  break;
                case SubmissionAction.APPROVE:
                  handleApprove();
                  break;
                case SubmissionAction.REJECT:
                  handleReject();
                  break;
                case SubmissionAction.CANCEL:
                  handleCancel();
                  break;
                case SubmissionAction.START_EXPERIMENT:
                  handleStartExperiment();
                  break;
                case SubmissionAction.UPLOAD_RESULTS:
                  navigate(`/submissions/${id}/results/upload`);
                  break;
                case SubmissionAction.REVIEW_RESULTS:
                  navigate(`/submissions/${id}/results`);
                  break;
                case SubmissionAction.COMPLETE:
                  handleCompleteSubmission();
                  break;
                default:
                  break;
              }
            }}
          >
            {action.label}
          </Button>
        ))}
      </Box>
    );
  };

  /**
   * Renders the submission information tab content
   */
  const renderSubmissionInfo = () => (
    <Box sx={{ p: 3 }}>
      <Typography variant="h6" gutterBottom>
        General Information
      </Typography>
      <Typography variant="body1">Name: {submission.name}</Typography>
      <Typography variant="body1">Description: {submission.description || 'N/A'}</Typography>
      <Typography variant="body1">Created At: {submission.created_at}</Typography>
      <Typography variant="body1">Updated At: {submission.updated_at}</Typography>
      <Divider sx={{ my: 2 }} />

      <Typography variant="h6" gutterBottom>
        CRO Service Information
      </Typography>
      <Typography variant="body1">Service: {submission.cro_service?.name || 'N/A'}</Typography>
      <Typography variant="body1">Provider: {submission.cro_service?.provider || 'N/A'}</Typography>
      <Divider sx={{ my: 2 }} />

      <Typography variant="h6" gutterBottom>
        Pricing Information
      </Typography>
      <Typography variant="body1">Price: {submission.price || 'N/A'}</Typography>
      <Typography variant="body1">Currency: {submission.price_currency || 'N/A'}</Typography>
      <Typography variant="body1">Estimated Turnaround Days: {submission.estimated_turnaround_days || 'N/A'}</Typography>
    </Box>
  );

  /**
   * Renders the documents tab content
   */
  const renderDocumentsTab = () => (
    <Box sx={{ p: 3 }}>
      <DocumentList
        submissionId={id}
        onDocumentAdded={handleDocumentAdded}
        onDocumentDeleted={handleDocumentDeleted}
      />
    </Box>
  );

  /**
   * Renders the molecules tab content
   */
  const renderMoleculesTab = () => (
    <Box sx={{ p: 3 }}>
      <MoleculeTable molecules={submission.molecules || []} />
    </Box>
  );

  return (
    <Box>
      <Paper sx={{ p: 2, mb: 2 }}>
        <Typography variant="h4" component="h1" gutterBottom>
          Submission Detail
        </Typography>
        <Typography variant="subtitle1">
          Status: {getStatusDisplayName(submission.status)}
        </Typography>
        <SubmissionStatus submission={submission} />
      </Paper>

      <Tabs value={activeTab} onChange={handleTabChange} aria-label="submission tabs">
        <Tab label="Information" />
        <Tab label="Documents" />
        <Tab label="Molecules" />
      </Tabs>

      {activeTab === 0 && renderSubmissionInfo()}
      {activeTab === 1 && renderDocumentsTab()}
      {activeTab === 2 && renderMoleculesTab()}

      {renderActionButtons()}

      <ConfirmDialog
        open={confirmDialog.open}
        title={confirmDialog.title}
        message={confirmDialog.message}
        onConfirm={confirmDialog.action}
        onClose={handleCloseConfirmDialog}
      />

      <Dialog open={pricingForm.open} onClose={handleClosePricingForm}>
        <DialogTitle>Provide Pricing Information</DialogTitle>
        <DialogContent>
          <Grid container spacing={2}>
            <Grid item xs={12} sm={6}>
              <TextField
                autoFocus
                margin="dense"
                id="price"
                label="Price"
                type="number"
                fullWidth
                value={pricingForm.price}
                onChange={(e) => setPricingForm({ ...pricingForm, price: e.target.value })}
              />
            </Grid>
            <Grid item xs={12} sm={6}>
              <TextField
                margin="dense"
                id="currency"
                label="Currency"
                type="text"
                fullWidth
                value={pricingForm.currency}
                onChange={(e) => setPricingForm({ ...pricingForm, currency: e.target.value })}
              />
            </Grid>
            <Grid item xs={12} sm={6}>
              <TextField
                margin="dense"
                id="turnaroundDays"
                label="Turnaround Days"
                type="number"
                fullWidth
                value={pricingForm.turnaroundDays}
                onChange={(e) => setPricingForm({ ...pricingForm, turnaroundDays: e.target.value })}
              />
            </Grid>
            <Grid item xs={12}>
              <TextField
                margin="dense"
                id="comment"
                label="Comment"
                type="text"
                fullWidth
                multiline
                rows={4}
                value={pricingForm.comment}
                onChange={(e) => setPricingForm({ ...pricingForm, comment: e.target.value })}
              />
            </Grid>
          </Grid>
        </DialogContent>
        <DialogActions>
          <Button onClick={handleClosePricingForm}>Cancel</Button>
          <Button onClick={handlePricingSubmit} color="primary">
            Submit
          </Button>
        </DialogActions>
      </Dialog>
    </Box>
  );
};

export default SubmissionDetail;