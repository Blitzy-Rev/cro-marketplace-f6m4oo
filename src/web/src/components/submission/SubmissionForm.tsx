import React, { useState, useEffect, useCallback, useMemo } from 'react'; // react ^18.0.0
import { useNavigate, useParams } from 'react-router-dom'; // react-router-dom ^6.0.0
import {
  Box,
  Paper,
  Typography,
  TextField,
  Button,
  FormControl,
  InputLabel,
  Select,
  MenuItem,
  FormHelperText,
  Grid,
  Divider,
  CircularProgress,
  Alert,
  Chip
} from '@mui/material'; // @mui/material ^5.0.0
import SubmissionStepper from './SubmissionStepper';
import DocumentUploader from '../document/DocumentUploader';
import MoleculeTable from '../molecule/MoleculeTable';
import useSubmissionForm from '../../hooks/useSubmissionForm';
import useToast from '../../hooks/useToast';
import {
  Submission,
  SubmissionCreate,
  SubmissionWithDocumentRequirements
} from '../../types/submission.types';
import {
  DocumentType,
  REQUIRED_DOCUMENT_TYPES
} from '../../constants/documentTypes';
import { SubmissionStatus } from '../../constants/submissionStatus';
import { ServiceType } from '../../types/cro.types';
import { Document } from '../../types/document.types';
import { Molecule } from '../../types/molecule.types';
import { getCROServices } from '../../api/croApi';
import { getMolecules } from '../../api/moleculeApi';
import { getSubmissionDocumentRequirements } from '../../api/submissionApi';

interface SubmissionFormProps {
  /** Optional initial data for editing an existing submission */
  initialData?: Submission;
  /** Optional submission ID for editing an existing submission */
  submissionId?: string;
  /** Callback function for successful submission */
  onSubmitSuccess?: (submission: Submission) => void;
  /** Callback function for cancellation */
  onCancel?: () => void;
}

/**
 * A multi-step form component for creating and editing CRO submissions
 */
const SubmissionForm: React.FC<SubmissionFormProps> = (props) => {
  // Extract props: initialData, submissionId, onSubmitSuccess, onCancel
  const { initialData, submissionId, onSubmitSuccess, onCancel } = props;

  // Initialize navigation and URL parameters hooks
  const navigate = useNavigate();
  const { id } = useParams<{ id: string }>();

  // Initialize toast notification hook
  const toast = useToast();

  // Initialize submission form hook with initialData and submissionId
  const {
    formData,
    setFormData,
    errors,
    isValid,
    currentStep,
    setCurrentStep,
    totalSteps,
    handleInputChange,
    handleSubmit,
    handleSaveDraft,
    handleNext,
    handleBack,
    loading,
    documentRequirements,
    selectedMolecules,
    handleMoleculeSelection,
    handleCROServiceChange,
    handleDocumentUpload,
    isStepComplete,
    resetForm
  } = useSubmissionForm(initialData, submissionId || id);

  // Initialize state for CRO services, molecules, and loading states
  const [croServices, setCROServices] = useState<any[]>([]);
  const [molecules, setMolecules] = useState<Molecule[]>([]);
  const [servicesLoading, setServicesLoading] = useState(false);
  const [moleculesLoading, setMoleculesLoading] = useState(false);

  // Fetch available CRO services on component mount
  useEffect(() => {
    const fetchServices = async () => {
      try {
        setServicesLoading(true);
        const response = await getCROServices();
        setCROServices(response.items);
      } catch (error) {
        toast.error(`Failed to load CRO services: ${toast.formatError(error)}`);
      } finally {
        setServicesLoading(false);
      }
    };

    fetchServices();
  }, [toast]);

  // Define step configuration for the multi-step form
  const steps = useMemo(() => [
    { label: 'CRO Service Selection' },
    { label: 'Molecule Selection' },
    { label: 'Document Management' }
  ], []);

  // Implement form submission handler
  const handleFormSubmit = async () => {
    const submission = await handleSubmit();
    if (submission && onSubmitSuccess) {
      onSubmitSuccess(submission);
      navigate('/submissions');
    }
  };

  // Implement form cancellation handler
  const handleFormCancel = () => {
    if (onCancel) {
      onCancel();
    }
    navigate('/submissions');
  };

  // Render SubmissionStepper component with step configuration
  return (
    <Paper elevation={2} sx={{ p: 3, width: '100%' }}>
      <Typography variant="h5" gutterBottom>
        {submissionId ? 'Edit Submission' : 'Create Submission'}
      </Typography>
      <SubmissionStepper
        activeStep={currentStep}
        steps={steps}
        onStepChange={setCurrentStep}
        isStepComplete={isStepComplete}
      >
        {/* Render Step 1: CRO Service Selection form */}
        <Box>
          <Typography variant="h6" gutterBottom>
            Step 1: CRO Service Selection
          </Typography>
          <Grid container spacing={2}>
            <Grid item xs={12} md={6}>
              <TextField
                fullWidth
                label="Submission Name"
                value={formData.name || ''}
                onChange={(e) => handleInputChange('name', e.target.value)}
                error={!!errors.name}
                helperText={errors.name}
                required
              />
            </Grid>
            <Grid item xs={12} md={6}>
              <FormControl fullWidth required error={!!errors.cro_service_id}>
                <InputLabel id="cro-service-label">CRO Service</InputLabel>
                <Select
                  labelId="cro-service-label"
                  value={formData.cro_service_id || ''}
                  label="CRO Service"
                  onChange={(e) => handleCROServiceChange(e.target.value)}
                >
                  {servicesLoading ? (
                    <MenuItem value="" disabled>
                      Loading...
                    </MenuItem>
                  ) : (
                    croServices.map((service) => (
                      <MenuItem key={service.id} value={service.id}>
                        {service.name}
                      </MenuItem>
                    ))
                  )}
                </Select>
                {errors.cro_service_id && (
                  <FormHelperText>{errors.cro_service_id}</FormHelperText>
                )}
              </FormControl>
            </Grid>
            <Grid item xs={12}>
              <TextField
                fullWidth
                label="Description"
                multiline
                rows={3}
                value={formData.description || ''}
                onChange={(e) => handleInputChange('description', e.target.value)}
              />
            </Grid>
          </Grid>
        </Box>

        {/* Render Step 2: Molecule Selection form with MoleculeTable */}
        <Box>
          <Typography variant="h6" gutterBottom>
            Step 2: Molecule Selection
          </Typography>
          <MoleculeTable
            molecules={molecules}
            loading={moleculesLoading}
            selectable
            selected={formData.molecule_ids || []}
            onSelectionChange={(selected) => {
              setFormData(prev => ({ ...prev, molecule_ids: selected }));
            }}
          />
        </Box>

        {/* Render Step 3: Document Management form with DocumentUploader */}
        <Box>
          <Typography variant="h6" gutterBottom>
            Step 3: Document Management
          </Typography>
          {documentRequirements ? (
            <>
              <Typography variant="subtitle1">Required Documents:</Typography>
              {documentRequirements.required_documents.map((doc) => (
                <Box key={doc.type} display="flex" alignItems="center" mb={1}>
                  <Typography variant="body1">{doc.description}</Typography>
                  {doc.exists ? (
                    <Chip label="Uploaded" color="success" size="small" sx={{ ml: 1 }} />
                  ) : (
                    <Chip label="Missing" color="error" size="small" sx={{ ml: 1 }} />
                  )}
                </Box>
              ))}
              <Divider sx={{ my: 2 }} />
              <DocumentUploader
                submissionId={submissionId}
                serviceType={croService?.service_type || '' as ServiceType}
                onUploadComplete={() => {
                  // Refresh document requirements after upload
                  getSubmissionDocumentRequirements(submissionId)
                    .then(setDocumentRequirements)
                    .catch((error) => {
                      toast.error(`Failed to refresh document requirements: ${toast.formatError(error)}`);
                    });
                }}
              />
            </>
          ) : (
            <CircularProgress />
          )}
        </Box>
      </SubmissionStepper>

      {/* Render navigation buttons for each step */}
      <Box sx={{ display: 'flex', justifyContent: 'space-between', mt: 3 }}>
        <Button
          variant="outlined"
          color="primary"
          disabled={loading}
          onClick={handleSaveDraft}
        >
          Save Draft
        </Button>
        <div>
          <Button
            disabled={loading || currentStep === 1}
            onClick={handleBack}
            sx={{ mr: 2 }}
          >
            Back
          </Button>
          <Button
            variant="contained"
            color="primary"
            disabled={loading || !isValid}
            onClick={currentStep === totalSteps ? handleFormSubmit : handleNext}
          >
            {currentStep === totalSteps ? 'Submit' : 'Next'}
          </Button>
        </div>
      </Box>
    </Paper>
  );
};

export default SubmissionForm;