import React, { useState } from 'react';
import { 
  Dialog,
  DialogTitle,
  DialogContent,
  DialogActions,
  Button,
  TextField,
  Box,
  Typography,
  IconButton,
  CircularProgress,
  Grid,
  Divider
} from '@mui/material'; // v5.0.0
import AddIcon from '@mui/icons-material/Add'; // v5.0.0
import DeleteIcon from '@mui/icons-material/Delete'; // v5.0.0
import { 
  DocumentSignatureRequest, 
  DocumentSignatureResponse,
  Document
} from '../../types/document.types';
import { requestDocumentSignature } from '../../api/documentApi';
import useToast from '../../hooks/useToast';

/**
 * Props for the signature request component
 */
interface SignatureRequestProps {
  /** Whether the signature request dialog is open */
  open: boolean;
  /** Callback function called when the dialog is closed */
  onClose: () => void;
  /** Document to request signatures for */
  document: Document;
  /** Callback function called when signature request is complete */
  onRequestComplete: (response: DocumentSignatureResponse) => void;
  /** URL to redirect to after signing */
  redirectUrl?: string;
}

/**
 * Form data structure for signature requests
 */
interface SignatureFormData {
  /** List of signers for the document */
  signers: Array<{ name: string, email: string, role?: string }>;
  /** Subject line for the signature request email */
  emailSubject: string;
  /** Message body for the signature request email */
  emailMessage: string;
}

/**
 * A component that provides an interface for requesting electronic signatures for documents
 * that complies with 21 CFR Part 11 requirements through DocuSign integration.
 */
const SignatureRequest: React.FC<SignatureRequestProps> = ({
  open,
  onClose,
  document,
  onRequestComplete,
  redirectUrl
}) => {
  // Initialize form state with default values
  const [formData, setFormData] = useState<SignatureFormData>({
    signers: [{ name: '', email: '', role: '' }],
    emailSubject: `Please sign: ${document?.name || 'Document'}`,
    emailMessage: `Please review and sign the attached document: ${document?.name || 'Document'}`
  });

  // Track form errors
  const [errors, setErrors] = useState<{ [key: string]: string }>({});
  
  // Track loading state for form submission
  const [loading, setLoading] = useState(false);
  
  // Get toast notification functions
  const { success, error: showError, formatError } = useToast();

  /**
   * Add a new signer to the form
   */
  const handleAddSigner = () => {
    const updatedSigners = [...formData.signers, { name: '', email: '', role: '' }];
    setFormData({ ...formData, signers: updatedSigners });
    
    // Clear any errors for the new signer
    const updatedErrors = { ...errors };
    delete updatedErrors[`signers.${formData.signers.length}.name`];
    delete updatedErrors[`signers.${formData.signers.length}.email`];
    setErrors(updatedErrors);
  };

  /**
   * Remove a signer from the form
   */
  const handleRemoveSigner = (index: number) => {
    // Ensure we always have at least one signer
    if (formData.signers.length <= 1) {
      return;
    }
    
    const updatedSigners = [...formData.signers];
    updatedSigners.splice(index, 1);
    setFormData({ ...formData, signers: updatedSigners });
    
    // Clear errors for removed signer
    const updatedErrors = { ...errors };
    delete updatedErrors[`signers.${index}.name`];
    delete updatedErrors[`signers.${index}.email`];
    delete updatedErrors[`signers.${index}.role`];
    setErrors(updatedErrors);
  };

  /**
   * Update a signer's information
   */
  const handleSignerChange = (index: number, field: string, value: string) => {
    const updatedSigners = [...formData.signers];
    updatedSigners[index] = { ...updatedSigners[index], [field]: value };
    setFormData({ ...formData, signers: updatedSigners });
    
    // Clear error for this field if it has a value now
    if (value.trim() !== '') {
      const updatedErrors = { ...errors };
      delete updatedErrors[`signers.${index}.${field}`];
      setErrors(updatedErrors);
    }
  };

  /**
   * Update email subject
   */
  const handleEmailSubjectChange = (e: React.ChangeEvent<HTMLInputElement>) => {
    const subject = e.target.value;
    setFormData({ ...formData, emailSubject: subject });
    
    // Clear error if field is now valid
    if (subject.trim() !== '') {
      const updatedErrors = { ...errors };
      delete updatedErrors['emailSubject'];
      setErrors(updatedErrors);
    }
  };

  /**
   * Update email message
   */
  const handleEmailMessageChange = (e: React.ChangeEvent<HTMLTextAreaElement>) => {
    const message = e.target.value;
    setFormData({ ...formData, emailMessage: message });
    
    // Clear error if field is now valid
    if (message.trim() !== '') {
      const updatedErrors = { ...errors };
      delete updatedErrors['emailMessage'];
      setErrors(updatedErrors);
    }
  };

  /**
   * Validate email format
   */
  const validateEmail = (email: string): boolean => {
    // Basic email validation regex
    const emailRegex = /^[^\s@]+@[^\s@]+\.[^\s@]+$/;
    return emailRegex.test(email);
  };

  /**
   * Validate the entire form
   * @returns True if the form is valid, false otherwise
   */
  const validateForm = (): boolean => {
    const newErrors: { [key: string]: string } = {};
    
    // Validate email subject
    if (!formData.emailSubject.trim()) {
      newErrors['emailSubject'] = 'Email subject is required';
    }
    
    // Validate email message
    if (!formData.emailMessage.trim()) {
      newErrors['emailMessage'] = 'Email message is required';
    }
    
    // Validate signers
    formData.signers.forEach((signer, index) => {
      if (!signer.name.trim()) {
        newErrors[`signers.${index}.name`] = 'Name is required';
      }
      
      if (!signer.email.trim()) {
        newErrors[`signers.${index}.email`] = 'Email is required';
      } else if (!validateEmail(signer.email)) {
        newErrors[`signers.${index}.email`] = 'Invalid email format';
      }
    });
    
    setErrors(newErrors);
    return Object.keys(newErrors).length === 0;
  };

  /**
   * Submit the signature request
   */
  const handleSubmit = async () => {
    if (!validateForm()) {
      return;
    }
    
    setLoading(true);
    
    try {
      const signatureRequest: DocumentSignatureRequest = {
        document_id: document.id,
        signers: formData.signers,
        email_subject: formData.emailSubject,
        email_message: formData.emailMessage,
        redirect_url: redirectUrl || null
      };
      
      const response = await requestDocumentSignature(document.id, signatureRequest);
      
      success('Signature request sent successfully');
      onRequestComplete(response);
      onClose();
    } catch (err) {
      showError(`Failed to send signature request: ${formatError(err)}`);
    } finally {
      setLoading(false);
    }
  };

  return (
    <Dialog 
      open={open} 
      onClose={loading ? undefined : onClose} 
      maxWidth="md" 
      fullWidth 
      aria-labelledby="signature-request-dialog-title"
    >
      <DialogTitle id="signature-request-dialog-title">Request Signatures</DialogTitle>
      <DialogContent>
        <Box mt={2}>
          <Typography variant="subtitle1" gutterBottom>
            Document: {document?.name}
          </Typography>
          
          <Divider sx={{ my: 2 }} />
          
          <Typography variant="h6" gutterBottom>
            Signers
          </Typography>
          
          {formData.signers.map((signer, index) => (
            <Grid container spacing={2} key={index} sx={{ mb: 2 }}>
              <Grid item xs={12} sm={4}>
                <TextField
                  label="Name"
                  fullWidth
                  value={signer.name}
                  onChange={(e) => handleSignerChange(index, 'name', e.target.value)}
                  error={!!errors[`signers.${index}.name`]}
                  helperText={errors[`signers.${index}.name`]}
                  disabled={loading}
                  required
                  inputProps={{ 'aria-label': `Signer ${index + 1} name` }}
                />
              </Grid>
              <Grid item xs={12} sm={4}>
                <TextField
                  label="Email"
                  fullWidth
                  type="email"
                  value={signer.email}
                  onChange={(e) => handleSignerChange(index, 'email', e.target.value)}
                  error={!!errors[`signers.${index}.email`]}
                  helperText={errors[`signers.${index}.email`]}
                  disabled={loading}
                  required
                  inputProps={{ 'aria-label': `Signer ${index + 1} email` }}
                />
              </Grid>
              <Grid item xs={12} sm={3}>
                <TextField
                  label="Role (Optional)"
                  fullWidth
                  value={signer.role || ''}
                  onChange={(e) => handleSignerChange(index, 'role', e.target.value)}
                  disabled={loading}
                  inputProps={{ 'aria-label': `Signer ${index + 1} role` }}
                />
              </Grid>
              <Grid item xs={12} sm={1} sx={{ display: 'flex', alignItems: 'center' }}>
                <IconButton 
                  color="error" 
                  onClick={() => handleRemoveSigner(index)}
                  disabled={formData.signers.length <= 1 || loading}
                  aria-label={`Remove signer ${index + 1}`}
                >
                  <DeleteIcon />
                </IconButton>
              </Grid>
            </Grid>
          ))}
          
          <Button
            startIcon={<AddIcon />}
            onClick={handleAddSigner}
            disabled={loading}
            sx={{ mb: 3 }}
            aria-label="Add another signer"
          >
            Add Another Signer
          </Button>
          
          <Divider sx={{ my: 2 }} />
          
          <Typography variant="h6" gutterBottom>
            Email Settings
          </Typography>
          
          <TextField
            label="Email Subject"
            fullWidth
            value={formData.emailSubject}
            onChange={handleEmailSubjectChange}
            error={!!errors['emailSubject']}
            helperText={errors['emailSubject']}
            disabled={loading}
            required
            sx={{ mb: 2 }}
            inputProps={{ 'aria-label': 'Email subject' }}
          />
          
          <TextField
            label="Email Message"
            fullWidth
            multiline
            rows={4}
            value={formData.emailMessage}
            onChange={handleEmailMessageChange}
            error={!!errors['emailMessage']}
            helperText={errors['emailMessage']}
            disabled={loading}
            required
            inputProps={{ 'aria-label': 'Email message' }}
          />
        </Box>
      </DialogContent>
      <DialogActions>
        <Button onClick={onClose} disabled={loading}>
          Cancel
        </Button>
        <Button 
          onClick={handleSubmit} 
          variant="contained" 
          color="primary"
          disabled={loading}
          startIcon={loading ? <CircularProgress size={20} /> : null}
        >
          {loading ? 'Sending...' : 'Send Signature Request'}
        </Button>
      </DialogActions>
    </Dialog>
  );
};

export default SignatureRequest;