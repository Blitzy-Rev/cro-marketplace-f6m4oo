import { createSlice, createAsyncThunk, PayloadAction } from '@reduxjs/toolkit';
import { 
  Submission, 
  SubmissionCreate, 
  SubmissionUpdate, 
  SubmissionFilter, 
  SubmissionResponse, 
  SubmissionStatusCount,
  SubmissionActionRequest,
  SubmissionWithDocumentRequirements,
  SubmissionState
} from '../../types/submission.types';
import { SubmissionAction, SubmissionStatus } from '../../constants/submissionStatus';
import { 
  getSubmissions, 
  getSubmission, 
  createSubmission, 
  updateSubmission, 
  deleteSubmission,
  getSubmissionDocumentRequirements,
  performSubmissionAction,
  getSubmissionStatusCounts,
  submitPricing,
  approveSubmission,
  rejectSubmission,
  cancelSubmission,
  startExperiment,
  completeSubmission
} from '../../api/submissionApi';
import { setLoading, clearLoading, addNotification } from '../ui/uiSlice';

// Initial state
const initialState: SubmissionState = {
  submissions: [],
  selectedSubmission: null,
  documentRequirements: null,
  loading: false,
  error: null,
  totalCount: 0,
  currentPage: 1,
  pageSize: 10,
  totalPages: 0,
  filters: {
    name_contains: null,
    status: null,
    cro_service_id: null,
    active_only: true,
    created_by: null,
    molecule_id: null,
    created_after: null,
    created_before: null
  },
  statusCounts: []
};

// Async thunk for fetching submissions with pagination and filtering
export const fetchSubmissions = createAsyncThunk(
  'submissions/fetchSubmissions',
  async ({ page, size, filter }: { page: number; size: number; filter: SubmissionFilter }, { dispatch }) => {
    try {
      dispatch(setLoading('fetchSubmissions'));
      const response = await getSubmissions(page - 1, size, filter); // Adjust page for 0-based indexing in API
      dispatch(clearLoading('fetchSubmissions'));
      return response;
    } catch (error) {
      dispatch(clearLoading('fetchSubmissions'));
      dispatch(addNotification({
        type: 'error',
        message: `Failed to fetch submissions: ${error instanceof Error ? error.message : 'Unknown error'}`
      }));
      throw error;
    }
  }
);

// Async thunk for fetching a single submission by ID
export const fetchSubmission = createAsyncThunk(
  'submissions/fetchSubmission',
  async (id: string, { dispatch }) => {
    try {
      dispatch(setLoading('fetchSubmission'));
      const response = await getSubmission(id);
      dispatch(clearLoading('fetchSubmission'));
      return response;
    } catch (error) {
      dispatch(clearLoading('fetchSubmission'));
      dispatch(addNotification({
        type: 'error',
        message: `Failed to fetch submission: ${error instanceof Error ? error.message : 'Unknown error'}`
      }));
      throw error;
    }
  }
);

// Async thunk for fetching document requirements for a submission
export const fetchSubmissionDocumentRequirements = createAsyncThunk(
  'submissions/fetchDocumentRequirements',
  async (id: string, { dispatch }) => {
    try {
      dispatch(setLoading('fetchSubmissionDocumentRequirements'));
      const response = await getSubmissionDocumentRequirements(id);
      dispatch(clearLoading('fetchSubmissionDocumentRequirements'));
      return response;
    } catch (error) {
      dispatch(clearLoading('fetchSubmissionDocumentRequirements'));
      dispatch(addNotification({
        type: 'error',
        message: `Failed to fetch document requirements: ${error instanceof Error ? error.message : 'Unknown error'}`
      }));
      throw error;
    }
  }
);

// Async thunk for creating a new submission
export const createNewSubmission = createAsyncThunk(
  'submissions/createSubmission',
  async (submission: SubmissionCreate, { dispatch }) => {
    try {
      dispatch(setLoading('createSubmission'));
      const response = await createSubmission(submission);
      dispatch(clearLoading('createSubmission'));
      dispatch(addNotification({
        type: 'success',
        message: 'Submission created successfully'
      }));
      return response;
    } catch (error) {
      dispatch(clearLoading('createSubmission'));
      dispatch(addNotification({
        type: 'error',
        message: `Failed to create submission: ${error instanceof Error ? error.message : 'Unknown error'}`
      }));
      throw error;
    }
  }
);

// Async thunk for updating an existing submission
export const updateExistingSubmission = createAsyncThunk(
  'submissions/updateSubmission',
  async ({ id, submission }: { id: string; submission: SubmissionUpdate }, { dispatch }) => {
    try {
      dispatch(setLoading('updateSubmission'));
      const response = await updateSubmission(id, submission);
      dispatch(clearLoading('updateSubmission'));
      dispatch(addNotification({
        type: 'success',
        message: 'Submission updated successfully'
      }));
      return response;
    } catch (error) {
      dispatch(clearLoading('updateSubmission'));
      dispatch(addNotification({
        type: 'error',
        message: `Failed to update submission: ${error instanceof Error ? error.message : 'Unknown error'}`
      }));
      throw error;
    }
  }
);

// Async thunk for deleting a submission
export const deleteExistingSubmission = createAsyncThunk(
  'submissions/deleteSubmission',
  async (id: string, { dispatch }) => {
    try {
      dispatch(setLoading('deleteSubmission'));
      await deleteSubmission(id);
      dispatch(clearLoading('deleteSubmission'));
      dispatch(addNotification({
        type: 'success',
        message: 'Submission deleted successfully'
      }));
      return id;
    } catch (error) {
      dispatch(clearLoading('deleteSubmission'));
      dispatch(addNotification({
        type: 'error',
        message: `Failed to delete submission: ${error instanceof Error ? error.message : 'Unknown error'}`
      }));
      throw error;
    }
  }
);

// Async thunk for performing an action on a submission
export const performAction = createAsyncThunk(
  'submissions/performAction',
  async ({ id, action, data, comment }: { id: string; action: SubmissionAction; data?: Record<string, any>; comment?: string }, { dispatch }) => {
    try {
      dispatch(setLoading('performAction'));
      const actionRequest: SubmissionActionRequest = {
        action,
        data: data || null,
        comment: comment || null
      };
      const response = await performSubmissionAction(id, actionRequest);
      dispatch(clearLoading('performAction'));
      
      // Different success messages based on action
      let message = 'Submission action performed successfully';
      switch (action) {
        case SubmissionAction.SUBMIT:
          message = 'Submission submitted successfully';
          break;
        case SubmissionAction.PROVIDE_PRICING:
          message = 'Pricing information provided successfully';
          break;
        case SubmissionAction.APPROVE:
          message = 'Submission approved successfully';
          break;
        case SubmissionAction.REJECT:
          message = 'Submission rejected successfully';
          break;
        case SubmissionAction.CANCEL:
          message = 'Submission cancelled successfully';
          break;
        case SubmissionAction.START_EXPERIMENT:
          message = 'Experiment started successfully';
          break;
        case SubmissionAction.UPLOAD_RESULTS:
          message = 'Results uploaded successfully';
          break;
        case SubmissionAction.REVIEW_RESULTS:
          message = 'Results reviewed successfully';
          break;
        case SubmissionAction.COMPLETE:
          message = 'Submission completed successfully';
          break;
      }
      
      dispatch(addNotification({
        type: 'success',
        message
      }));
      
      return response;
    } catch (error) {
      dispatch(clearLoading('performAction'));
      dispatch(addNotification({
        type: 'error',
        message: `Failed to perform action: ${error instanceof Error ? error.message : 'Unknown error'}`
      }));
      throw error;
    }
  }
);

// Async thunk for submitting pricing information (CRO user)
export const submitPricingInfo = createAsyncThunk(
  'submissions/submitPricing',
  async ({ id, price, price_currency, estimated_turnaround_days, comment }: { id: string; price: number; price_currency: string; estimated_turnaround_days: number; comment?: string }, { dispatch }) => {
    try {
      dispatch(setLoading('submitPricing'));
      const response = await submitPricing(id, {
        price,
        price_currency,
        estimated_turnaround_days,
        comment: comment || null
      });
      dispatch(clearLoading('submitPricing'));
      dispatch(addNotification({
        type: 'success',
        message: 'Pricing information submitted successfully'
      }));
      return response;
    } catch (error) {
      dispatch(clearLoading('submitPricing'));
      dispatch(addNotification({
        type: 'error',
        message: `Failed to submit pricing: ${error instanceof Error ? error.message : 'Unknown error'}`
      }));
      throw error;
    }
  }
);

// Async thunk for approving a submission with pricing (Pharma user)
export const approveSubmissionWithPricing = createAsyncThunk(
  'submissions/approveSubmission',
  async ({ id, comment }: { id: string; comment?: string }, { dispatch }) => {
    try {
      dispatch(setLoading('approveSubmission'));
      const response = await approveSubmission(id, comment);
      dispatch(clearLoading('approveSubmission'));
      dispatch(addNotification({
        type: 'success',
        message: 'Submission approved successfully'
      }));
      return response;
    } catch (error) {
      dispatch(clearLoading('approveSubmission'));
      dispatch(addNotification({
        type: 'error',
        message: `Failed to approve submission: ${error instanceof Error ? error.message : 'Unknown error'}`
      }));
      throw error;
    }
  }
);

// Async thunk for rejecting a submission
export const rejectSubmissionRequest = createAsyncThunk(
  'submissions/rejectSubmission',
  async ({ id, comment }: { id: string; comment: string }, { dispatch }) => {
    try {
      dispatch(setLoading('rejectSubmission'));
      const response = await rejectSubmission(id, comment);
      dispatch(clearLoading('rejectSubmission'));
      dispatch(addNotification({
        type: 'success',
        message: 'Submission rejected successfully'
      }));
      return response;
    } catch (error) {
      dispatch(clearLoading('rejectSubmission'));
      dispatch(addNotification({
        type: 'error',
        message: `Failed to reject submission: ${error instanceof Error ? error.message : 'Unknown error'}`
      }));
      throw error;
    }
  }
);

// Async thunk for cancelling a submission
export const cancelSubmissionRequest = createAsyncThunk(
  'submissions/cancelSubmission',
  async ({ id, comment }: { id: string; comment: string }, { dispatch }) => {
    try {
      dispatch(setLoading('cancelSubmission'));
      const response = await cancelSubmission(id, comment);
      dispatch(clearLoading('cancelSubmission'));
      dispatch(addNotification({
        type: 'success',
        message: 'Submission cancelled successfully'
      }));
      return response;
    } catch (error) {
      dispatch(clearLoading('cancelSubmission'));
      dispatch(addNotification({
        type: 'error',
        message: `Failed to cancel submission: ${error instanceof Error ? error.message : 'Unknown error'}`
      }));
      throw error;
    }
  }
);

// Async thunk for starting the experiment (CRO user)
export const startExperimentProcess = createAsyncThunk(
  'submissions/startExperiment',
  async ({ id, comment }: { id: string; comment?: string }, { dispatch }) => {
    try {
      dispatch(setLoading('startExperiment'));
      const response = await startExperiment(id, comment);
      dispatch(clearLoading('startExperiment'));
      dispatch(addNotification({
        type: 'success',
        message: 'Experiment started successfully'
      }));
      return response;
    } catch (error) {
      dispatch(clearLoading('startExperiment'));
      dispatch(addNotification({
        type: 'error',
        message: `Failed to start experiment: ${error instanceof Error ? error.message : 'Unknown error'}`
      }));
      throw error;
    }
  }
);

// Async thunk for completing a submission (CRO user)
export const completeSubmissionProcess = createAsyncThunk(
  'submissions/completeSubmission',
  async ({ id, comment }: { id: string; comment?: string }, { dispatch }) => {
    try {
      dispatch(setLoading('completeSubmission'));
      const response = await completeSubmission(id, comment);
      dispatch(clearLoading('completeSubmission'));
      dispatch(addNotification({
        type: 'success',
        message: 'Submission completed successfully'
      }));
      return response;
    } catch (error) {
      dispatch(clearLoading('completeSubmission'));
      dispatch(addNotification({
        type: 'error',
        message: `Failed to complete submission: ${error instanceof Error ? error.message : 'Unknown error'}`
      }));
      throw error;
    }
  }
);

// Async thunk for fetching submission counts by status
export const fetchStatusCounts = createAsyncThunk(
  'submissions/fetchStatusCounts',
  async (filter: SubmissionFilter, { dispatch }) => {
    try {
      dispatch(setLoading('fetchStatusCounts'));
      const response = await getSubmissionStatusCounts(filter);
      dispatch(clearLoading('fetchStatusCounts'));
      return response;
    } catch (error) {
      dispatch(clearLoading('fetchStatusCounts'));
      dispatch(addNotification({
        type: 'error',
        message: `Failed to fetch status counts: ${error instanceof Error ? error.message : 'Unknown error'}`
      }));
      throw error;
    }
  }
);

export const submissionSlice = createSlice({
  name: 'submission',
  initialState,
  reducers: {
    // Set submission filter
    setSubmissionFilter: (state, action: PayloadAction<Partial<SubmissionFilter>>) => {
      state.filters = {
        ...state.filters,
        ...action.payload
      };
    },
    
    // Reset submission filter to default values
    resetSubmissionFilter: (state) => {
      state.filters = {
        name_contains: null,
        status: null,
        cro_service_id: null,
        active_only: true,
        created_by: null,
        molecule_id: null,
        created_after: null,
        created_before: null
      };
    },
    
    // Set current page for pagination
    setCurrentPage: (state, action: PayloadAction<number>) => {
      state.currentPage = action.payload;
    },
    
    // Set page size for pagination
    setPageSize: (state, action: PayloadAction<number>) => {
      state.pageSize = action.payload;
    },
    
    // Clear the selected submission
    clearSelectedSubmission: (state) => {
      state.selectedSubmission = null;
    },
    
    // Clear document requirements
    clearDocumentRequirements: (state) => {
      state.documentRequirements = null;
    }
  },
  extraReducers: (builder) => {
    // Handle fetchSubmissions
    builder
      .addCase(fetchSubmissions.pending, (state) => {
        state.loading = true;
        state.error = null;
      })
      .addCase(fetchSubmissions.fulfilled, (state, action) => {
        state.loading = false;
        state.submissions = action.payload.items;
        state.totalCount = action.payload.total;
        state.totalPages = action.payload.pages;
      })
      .addCase(fetchSubmissions.rejected, (state, action) => {
        state.loading = false;
        state.error = action.error.message || 'Failed to fetch submissions';
      })
    
    // Handle fetchSubmission
    builder
      .addCase(fetchSubmission.pending, (state) => {
        state.loading = true;
        state.error = null;
      })
      .addCase(fetchSubmission.fulfilled, (state, action) => {
        state.loading = false;
        state.selectedSubmission = action.payload;
      })
      .addCase(fetchSubmission.rejected, (state, action) => {
        state.loading = false;
        state.error = action.error.message || 'Failed to fetch submission';
      })
    
    // Handle fetchSubmissionDocumentRequirements
    builder
      .addCase(fetchSubmissionDocumentRequirements.pending, (state) => {
        state.loading = true;
        state.error = null;
      })
      .addCase(fetchSubmissionDocumentRequirements.fulfilled, (state, action) => {
        state.loading = false;
        state.documentRequirements = action.payload;
      })
      .addCase(fetchSubmissionDocumentRequirements.rejected, (state, action) => {
        state.loading = false;
        state.error = action.error.message || 'Failed to fetch document requirements';
      })
    
    // Handle createNewSubmission
    builder
      .addCase(createNewSubmission.pending, (state) => {
        state.loading = true;
        state.error = null;
      })
      .addCase(createNewSubmission.fulfilled, (state, action) => {
        state.loading = false;
        state.submissions = [...state.submissions, action.payload];
        state.selectedSubmission = action.payload;
      })
      .addCase(createNewSubmission.rejected, (state, action) => {
        state.loading = false;
        state.error = action.error.message || 'Failed to create submission';
      })
    
    // Handle updateExistingSubmission
    builder
      .addCase(updateExistingSubmission.pending, (state) => {
        state.loading = true;
        state.error = null;
      })
      .addCase(updateExistingSubmission.fulfilled, (state, action) => {
        state.loading = false;
        state.submissions = state.submissions.map(submission => 
          submission.id === action.payload.id ? action.payload : submission
        );
        if (state.selectedSubmission && state.selectedSubmission.id === action.payload.id) {
          state.selectedSubmission = action.payload;
        }
      })
      .addCase(updateExistingSubmission.rejected, (state, action) => {
        state.loading = false;
        state.error = action.error.message || 'Failed to update submission';
      })
    
    // Handle deleteExistingSubmission
    builder
      .addCase(deleteExistingSubmission.pending, (state) => {
        state.loading = true;
        state.error = null;
      })
      .addCase(deleteExistingSubmission.fulfilled, (state, action) => {
        state.loading = false;
        state.submissions = state.submissions.filter(submission => submission.id !== action.payload);
        if (state.selectedSubmission && state.selectedSubmission.id === action.payload) {
          state.selectedSubmission = null;
        }
      })
      .addCase(deleteExistingSubmission.rejected, (state, action) => {
        state.loading = false;
        state.error = action.error.message || 'Failed to delete submission';
      })
    
    // Handle performAction
    builder
      .addCase(performAction.pending, (state) => {
        state.loading = true;
        state.error = null;
      })
      .addCase(performAction.fulfilled, (state, action) => {
        state.loading = false;
        state.submissions = state.submissions.map(submission => 
          submission.id === action.payload.id ? action.payload : submission
        );
        if (state.selectedSubmission && state.selectedSubmission.id === action.payload.id) {
          state.selectedSubmission = action.payload;
        }
      })
      .addCase(performAction.rejected, (state, action) => {
        state.loading = false;
        state.error = action.error.message || 'Failed to perform action on submission';
      })
    
    // Handle submitPricingInfo
    builder
      .addCase(submitPricingInfo.pending, (state) => {
        state.loading = true;
        state.error = null;
      })
      .addCase(submitPricingInfo.fulfilled, (state, action) => {
        state.loading = false;
        state.submissions = state.submissions.map(submission => 
          submission.id === action.payload.id ? action.payload : submission
        );
        if (state.selectedSubmission && state.selectedSubmission.id === action.payload.id) {
          state.selectedSubmission = action.payload;
        }
      })
      .addCase(submitPricingInfo.rejected, (state, action) => {
        state.loading = false;
        state.error = action.error.message || 'Failed to submit pricing information';
      })
    
    // Handle approveSubmissionWithPricing
    builder
      .addCase(approveSubmissionWithPricing.pending, (state) => {
        state.loading = true;
        state.error = null;
      })
      .addCase(approveSubmissionWithPricing.fulfilled, (state, action) => {
        state.loading = false;
        state.submissions = state.submissions.map(submission => 
          submission.id === action.payload.id ? action.payload : submission
        );
        if (state.selectedSubmission && state.selectedSubmission.id === action.payload.id) {
          state.selectedSubmission = action.payload;
        }
      })
      .addCase(approveSubmissionWithPricing.rejected, (state, action) => {
        state.loading = false;
        state.error = action.error.message || 'Failed to approve submission';
      })
    
    // Handle rejectSubmissionRequest
    builder
      .addCase(rejectSubmissionRequest.pending, (state) => {
        state.loading = true;
        state.error = null;
      })
      .addCase(rejectSubmissionRequest.fulfilled, (state, action) => {
        state.loading = false;
        state.submissions = state.submissions.map(submission => 
          submission.id === action.payload.id ? action.payload : submission
        );
        if (state.selectedSubmission && state.selectedSubmission.id === action.payload.id) {
          state.selectedSubmission = action.payload;
        }
      })
      .addCase(rejectSubmissionRequest.rejected, (state, action) => {
        state.loading = false;
        state.error = action.error.message || 'Failed to reject submission';
      })
    
    // Handle cancelSubmissionRequest
    builder
      .addCase(cancelSubmissionRequest.pending, (state) => {
        state.loading = true;
        state.error = null;
      })
      .addCase(cancelSubmissionRequest.fulfilled, (state, action) => {
        state.loading = false;
        state.submissions = state.submissions.map(submission => 
          submission.id === action.payload.id ? action.payload : submission
        );
        if (state.selectedSubmission && state.selectedSubmission.id === action.payload.id) {
          state.selectedSubmission = action.payload;
        }
      })
      .addCase(cancelSubmissionRequest.rejected, (state, action) => {
        state.loading = false;
        state.error = action.error.message || 'Failed to cancel submission';
      })
    
    // Handle startExperimentProcess
    builder
      .addCase(startExperimentProcess.pending, (state) => {
        state.loading = true;
        state.error = null;
      })
      .addCase(startExperimentProcess.fulfilled, (state, action) => {
        state.loading = false;
        state.submissions = state.submissions.map(submission => 
          submission.id === action.payload.id ? action.payload : submission
        );
        if (state.selectedSubmission && state.selectedSubmission.id === action.payload.id) {
          state.selectedSubmission = action.payload;
        }
      })
      .addCase(startExperimentProcess.rejected, (state, action) => {
        state.loading = false;
        state.error = action.error.message || 'Failed to start experiment';
      })
    
    // Handle completeSubmissionProcess
    builder
      .addCase(completeSubmissionProcess.pending, (state) => {
        state.loading = true;
        state.error = null;
      })
      .addCase(completeSubmissionProcess.fulfilled, (state, action) => {
        state.loading = false;
        state.submissions = state.submissions.map(submission => 
          submission.id === action.payload.id ? action.payload : submission
        );
        if (state.selectedSubmission && state.selectedSubmission.id === action.payload.id) {
          state.selectedSubmission = action.payload;
        }
      })
      .addCase(completeSubmissionProcess.rejected, (state, action) => {
        state.loading = false;
        state.error = action.error.message || 'Failed to complete submission';
      })
    
    // Handle fetchStatusCounts
    builder
      .addCase(fetchStatusCounts.pending, (state) => {
        state.loading = true;
        state.error = null;
      })
      .addCase(fetchStatusCounts.fulfilled, (state, action) => {
        state.loading = false;
        state.statusCounts = action.payload;
      })
      .addCase(fetchStatusCounts.rejected, (state, action) => {
        state.loading = false;
        state.error = action.error.message || 'Failed to fetch status counts';
      });
  }
});

// Extract the action creators and reducer
export const { 
  setSubmissionFilter, 
  resetSubmissionFilter, 
  setCurrentPage, 
  setPageSize,
  clearSelectedSubmission,
  clearDocumentRequirements
} = submissionSlice.actions;

// Define selectors
export const selectSubmissions = (state: { submission: SubmissionState }) => state.submission.submissions;
export const selectSelectedSubmission = (state: { submission: SubmissionState }) => state.submission.selectedSubmission;
export const selectDocumentRequirements = (state: { submission: SubmissionState }) => state.submission.documentRequirements;
export const selectSubmissionLoading = (state: { submission: SubmissionState }) => state.submission.loading;
export const selectSubmissionError = (state: { submission: SubmissionState }) => state.submission.error;
export const selectPagination = (state: { submission: SubmissionState }) => ({
  totalCount: state.submission.totalCount,
  currentPage: state.submission.currentPage,
  pageSize: state.submission.pageSize,
  totalPages: state.submission.totalPages
});
export const selectFilters = (state: { submission: SubmissionState }) => state.submission.filters;
export const selectStatusCounts = (state: { submission: SubmissionState }) => state.submission.statusCounts;

export default submissionSlice.reducer;