import { useState, useEffect, useCallback, useMemo } from 'react'; // react v18.0.0
import useToast from './useToast';
import {
  SubmissionCreate,
  SubmissionUpdate,
  Submission,
  SubmissionWithDocumentRequirements
} from '../types/submission.types';
import { Document } from '../types/document.types';
import {
  DocumentType,
  REQUIRED_DOCUMENT_TYPES
} from '../constants/documentTypes';
import {
  SubmissionStatus,
  EDITABLE_STATUSES
} from '../constants/submissionStatus';
import { CROService } from '../types/cro.types';
import { Molecule } from '../types/molecule.types';
import {
  createSubmission,
  updateSubmission,
  getSubmissionDocumentRequirements
} from '../api/submissionApi';
import { getCROService } from '../api/croApi';
import { getMolecules } from '../api/moleculeApi';
import {
  getDocumentsBySubmission,
  createDocumentUploadRequest,
  uploadDocumentFile
} from '../api/documentApi';

// Define the step count for the submission form
const TOTAL_STEPS = 3;

/**
 * Custom React hook for managing CRO submission form state and logic
 * 
 * This hook handles all aspects of the CRO submission process including:
 * - Multi-step form progression
 * - Form validation
 * - Molecule selection
 * - Document requirements and uploads
 * - Submission creation and updating
 * 
 * @param initialData - Optional initial data for editing an existing submission
 * @param submissionId - Optional ID when editing an existing submission
 * @returns Form state and handler functions for the submission form
 */
const useSubmissionForm = (
  initialData?: Submission,
  submissionId?: string
) => {
  // Initialize form state with default values or provided initial data
  const [formData, setFormData] = useState<Partial<SubmissionCreate | SubmissionUpdate>>({
    name: initialData?.name || '',
    cro_service_id: initialData?.cro_service_id || '',
    description: initialData?.description || null,
    specifications: initialData?.specifications || null,
    molecule_ids: initialData?.molecules?.map(m => m.id) || [],
  });

  // State for form validation and UI
  const [errors, setErrors] = useState<Record<string, string>>({});
  const [isValid, setIsValid] = useState<boolean>(false);
  const [currentStep, setCurrentStep] = useState<number>(1);
  const [loading, setLoading] = useState<boolean>(false);
  
  // State for related data
  const [selectedMolecules, setSelectedMolecules] = useState<Molecule[]>([]);
  const [documentRequirements, setDocumentRequirements] = useState<SubmissionWithDocumentRequirements | null>(null);
  const [croService, setCroService] = useState<CROService | null>(null);

  // Toast notifications
  const toast = useToast();

  // Fetch document requirements when editing an existing submission
  useEffect(() => {
    if (submissionId) {
      const fetchDocumentRequirements = async () => {
        try {
          setLoading(true);
          const requirements = await getSubmissionDocumentRequirements(submissionId);
          setDocumentRequirements(requirements);
        } catch (error) {
          toast.error(`Failed to load document requirements: ${toast.formatError(error)}`);
        } finally {
          setLoading(false);
        }
      };

      fetchDocumentRequirements();
    }
  }, [submissionId, toast]);

  // Fetch CRO service details when service ID changes
  useEffect(() => {
    const fetchCROService = async () => {
      if (!formData.cro_service_id) {
        setCroService(null);
        return;
      }

      try {
        setLoading(true);
        const response = await getCROService(formData.cro_service_id);
        setCroService(response.service);
      } catch (error) {
        toast.error(`Failed to load CRO service: ${toast.formatError(error)}`);
        setFormData(prev => ({
          ...prev,
          cro_service_id: ''
        }));
      } finally {
        setLoading(false);
      }
    };

    if (formData.cro_service_id) {
      fetchCROService();
    }
  }, [formData.cro_service_id, toast]);

  // Fetch molecule data when molecule IDs are set
  useEffect(() => {
    const fetchMolecules = async () => {
      if (!formData.molecule_ids || formData.molecule_ids.length === 0) {
        setSelectedMolecules([]);
        return;
      }

      try {
        setLoading(true);
        // In a real implementation, you would want a more efficient way to get molecules by ID
        // This is a simplified approach that might not be suitable for large datasets
        const response = await getMolecules();
        
        // Filter molecules by ID client-side
        const filteredMolecules = response.items.filter(
          molecule => formData.molecule_ids?.includes(molecule.id)
        );
        
        setSelectedMolecules(filteredMolecules);
      } catch (error) {
        toast.error(`Failed to load molecules: ${toast.formatError(error)}`);
      } finally {
        setLoading(false);
      }
    };

    if (formData.molecule_ids && formData.molecule_ids.length > 0) {
      fetchMolecules();
    }
  }, [formData.molecule_ids, toast]);

  // Validate form data
  const validateForm = useCallback(() => {
    const newErrors: Record<string, string> = {};
    
    // Step 1 validation - CRO service selection
    if (currentStep === 1) {
      if (!formData.name || !formData.name.trim()) {
        newErrors.name = 'Submission name is required';
      }
      
      if (!formData.cro_service_id) {
        newErrors.cro_service_id = 'CRO service is required';
      }
    }
    
    // Step 2 validation - Molecule selection
    if (currentStep === 2) {
      if (!formData.molecule_ids || formData.molecule_ids.length === 0) {
        newErrors.molecule_ids = 'At least one molecule must be selected';
      }
    }
    
    // Step 3 validation - Documents
    if (currentStep === 3 && submissionId) {
      if (documentRequirements) {
        const missingRequiredDocs = documentRequirements.required_documents.filter(doc => !doc.exists);
        if (missingRequiredDocs.length > 0) {
          newErrors.documents = `Missing required documents: ${missingRequiredDocs.map(d => d.type).join(', ')}`;
        }
      } else {
        newErrors.documents = 'Document requirements not loaded';
      }
    }
    
    setErrors(newErrors);
    return Object.keys(newErrors).length === 0;
  }, [currentStep, formData, documentRequirements, submissionId]);

  // Validate on form data or step change
  useEffect(() => {
    const isCurrentStepValid = validateForm();
    setIsValid(isCurrentStepValid);
  }, [formData, currentStep, validateForm]);

  // Handle form input changes
  const handleInputChange = useCallback((
    field: keyof (SubmissionCreate | SubmissionUpdate),
    value: any
  ) => {
    setFormData(prev => ({
      ...prev,
      [field]: value
    }));
  }, []);

  // Handle CRO service change
  const handleCROServiceChange = useCallback((serviceId: string) => {
    setFormData(prev => ({
      ...prev,
      cro_service_id: serviceId,
      // Reset specifications when service changes
      specifications: null
    }));
  }, []);

  // Handle molecule selection
  const handleMoleculeSelection = useCallback((molecules: Molecule[]) => {
    const moleculeIds = molecules.map(m => m.id);
    setFormData(prev => ({
      ...prev,
      molecule_ids: moleculeIds
    }));
    setSelectedMolecules(molecules);
  }, []);

  // Handle document upload
  const handleDocumentUpload = useCallback(async (
    documentType: DocumentType,
    file: File,
    name: string,
    description?: string
  ) => {
    if (!submissionId) {
      toast.error('Cannot upload documents before creating a submission');
      return null;
    }

    try {
      setLoading(true);
      
      // First, create an upload request
      const uploadRequest = await createDocumentUploadRequest({
        name,
        type: documentType,
        submission_id: submissionId,
        description: description || null,
        signature_required: REQUIRED_DOCUMENT_TYPES[croService?.service_type || '']?.includes(documentType) || false,
        content_type: file.type,
        file_size: file.size
      });
      
      // Then upload the actual file
      const uploadedDocument = await uploadDocumentFile(uploadRequest, file);
      
      // Refresh document requirements
      const requirements = await getSubmissionDocumentRequirements(submissionId);
      setDocumentRequirements(requirements);
      
      toast.success(`Document "${name}" uploaded successfully`);
      return uploadedDocument;
    } catch (error) {
      toast.error(`Failed to upload document: ${toast.formatError(error)}`);
      return null;
    } finally {
      setLoading(false);
    }
  }, [submissionId, toast, croService]);

  // Move to next step
  const handleNext = useCallback(() => {
    if (currentStep < TOTAL_STEPS && isValid) {
      setCurrentStep(prev => prev + 1);
    } else if (!isValid) {
      toast.warning('Please fix the errors before proceeding');
    }
  }, [currentStep, isValid, toast]);

  // Move to previous step
  const handleBack = useCallback(() => {
    if (currentStep > 1) {
      setCurrentStep(prev => prev - 1);
    }
  }, [currentStep]);

  // Check if a step is complete
  const isStepComplete = useCallback((step: number) => {
    if (step === 1) {
      return !!formData.name && !!formData.cro_service_id;
    }
    if (step === 2) {
      return !!formData.molecule_ids && formData.molecule_ids.length > 0;
    }
    if (step === 3) {
      if (!submissionId || !documentRequirements) return false;
      return documentRequirements.required_documents.every(doc => doc.exists);
    }
    return false;
  }, [formData, documentRequirements, submissionId]);

  // Submit the form (create or update submission)
  const handleSubmit = useCallback(async () => {
    try {
      setLoading(true);
      
      if (!isValid) {
        toast.error('Please fix the errors before submitting');
        return null;
      }
      
      let result;
      if (submissionId) {
        // Update existing submission
        const updateData: SubmissionUpdate = {
          name: formData.name,
          cro_service_id: formData.cro_service_id,
          description: formData.description,
          specifications: formData.specifications,
          molecule_ids: formData.molecule_ids,
          status: SubmissionStatus.SUBMITTED // Change status to SUBMITTED
        };
        result = await updateSubmission(submissionId, updateData);
        toast.success('Submission updated and sent to CRO');
      } else {
        // Create new submission
        const createData: SubmissionCreate = {
          name: formData.name!,
          cro_service_id: formData.cro_service_id!,
          description: formData.description,
          specifications: formData.specifications,
          molecule_ids: formData.molecule_ids,
          created_by: 'current-user-id' // In a real app, get this from auth context
        };
        result = await createSubmission(createData);
        toast.success('Submission created successfully');
      }
      
      return result;
    } catch (error) {
      toast.error(`Failed to submit: ${toast.formatError(error)}`);
      return null;
    } finally {
      setLoading(false);
    }
  }, [formData, isValid, submissionId, toast]);

  // Save form as draft
  const handleSaveDraft = useCallback(async () => {
    try {
      setLoading(true);
      
      // For drafts, we don't need all validations to pass
      let draftName = formData.name;
      if (!draftName || draftName.trim() === '') {
        draftName = 'Draft Submission';
      }
      
      let result;
      if (submissionId) {
        // Update existing draft
        const updateData: SubmissionUpdate = {
          name: draftName,
          cro_service_id: formData.cro_service_id,
          description: formData.description,
          specifications: formData.specifications,
          molecule_ids: formData.molecule_ids,
          status: SubmissionStatus.DRAFT
        };
        result = await updateSubmission(submissionId, updateData);
        toast.success('Draft updated successfully');
      } else {
        // Create new draft
        const createData: SubmissionCreate = {
          name: draftName,
          cro_service_id: formData.cro_service_id || '',
          description: formData.description,
          specifications: formData.specifications,
          molecule_ids: formData.molecule_ids,
          created_by: 'current-user-id' // In a real app, get this from auth context
        };
        result = await createSubmission(createData);
        toast.success('Draft saved successfully');
      }
      
      return result;
    } catch (error) {
      toast.error(`Failed to save draft: ${toast.formatError(error)}`);
      return null;
    } finally {
      setLoading(false);
    }
  }, [formData, submissionId, toast]);

  // Reset form to initial state
  const resetForm = useCallback(() => {
    setFormData({
      name: '',
      cro_service_id: '',
      description: null,
      specifications: null,
      molecule_ids: [],
    });
    setErrors({});
    setCurrentStep(1);
    setDocumentRequirements(null);
    setSelectedMolecules([]);
    setCroService(null);
  }, []);

  // Compute total steps
  const totalSteps = useMemo(() => TOTAL_STEPS, []);

  return {
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
  };
};

export default useSubmissionForm;