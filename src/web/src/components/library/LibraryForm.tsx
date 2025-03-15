import React, { useState, useEffect } from 'react';
import { useDispatch } from 'react-redux';
import {
  Box,
  TextField,
  Button,
  FormControl,
  FormControlLabel,
  InputLabel,
  Select,
  MenuItem,
  Switch,
  Grid,
  Typography,
  CircularProgress,
  SelectChangeEvent
} from '@mui/material';

import { 
  Library, 
  LibraryCategory, 
  LibraryCreate, 
  LibraryUpdate 
} from '../../types/library.types';
import { 
  addLibrary, 
  editLibrary 
} from '../../features/library/librarySlice';
import useToast from '../../hooks/useToast';

// Component props interface
interface LibraryFormProps {
  library?: Library | null;
  onSubmitSuccess: (library: Library) => void;
  onCancel: () => void;
  initialMoleculeIds?: string[] | null;
}

// Form data interface
interface FormData {
  name: string;
  description: string;
  category: LibraryCategory | null;
  is_public: boolean;
}

// Form errors interface
interface FormErrors {
  name?: string;
  description?: string;
  category?: string;
}

/**
 * Validates the form inputs before submission
 * @param formData - The form data to validate
 * @returns Object containing validation errors if any
 */
const validateForm = (formData: FormData): FormErrors => {
  const errors: FormErrors = {};

  // Validate name (required, max length)
  if (!formData.name.trim()) {
    errors.name = 'Library name is required';
  } else if (formData.name.length > 100) {
    errors.name = 'Library name cannot exceed 100 characters';
  }

  // Validate description (max length)
  if (formData.description && formData.description.length > 500) {
    errors.description = 'Description cannot exceed 500 characters';
  }

  return errors;
};

/**
 * Form component for creating and editing molecule libraries in the
 * Molecular Data Management and CRO Integration Platform.
 */
const LibraryForm: React.FC<LibraryFormProps> = ({
  library = null,
  onSubmitSuccess,
  onCancel,
  initialMoleculeIds = null
}) => {
  // Redux dispatch
  const dispatch = useDispatch();
  
  // Toast notifications
  const toast = useToast();

  // Form state
  const [formData, setFormData] = useState<FormData>({
    name: library?.name || '',
    description: library?.description || '',
    category: library?.category || null,
    is_public: library?.is_public || false
  });

  // Form errors state
  const [errors, setErrors] = useState<FormErrors>({});
  
  // Loading state
  const [isSubmitting, setIsSubmitting] = useState(false);

  // Initialize form data when library prop changes
  useEffect(() => {
    if (library) {
      setFormData({
        name: library.name,
        description: library.description || '',
        category: library.category,
        is_public: library.is_public
      });
    }
  }, [library]);

  // Handle text input changes
  const handleInputChange = (event: React.ChangeEvent<HTMLInputElement>) => {
    const { name, value } = event.target;
    setFormData(prev => ({ ...prev, [name]: value }));
    
    // Clear error when field is modified
    if (errors[name as keyof FormErrors]) {
      setErrors(prev => ({ ...prev, [name]: undefined }));
    }
  };

  // Handle select input changes
  const handleSelectChange = (event: SelectChangeEvent) => {
    const { name, value } = event.target;
    // Convert empty string to null for category
    const normalizedValue = value === '' ? null : value as LibraryCategory;
    setFormData(prev => ({ ...prev, [name]: normalizedValue }));
    
    // Clear error when field is modified
    if (errors[name as keyof FormErrors]) {
      setErrors(prev => ({ ...prev, [name]: undefined }));
    }
  };

  // Handle switch input changes
  const handleSwitchChange = (event: React.ChangeEvent<HTMLInputElement>) => {
    const { name, checked } = event.target;
    setFormData(prev => ({ ...prev, [name]: checked }));
  };

  // Handle form submission
  const handleSubmit = async (event: React.FormEvent<HTMLFormElement>) => {
    event.preventDefault();
    
    // Validate form
    const validationErrors = validateForm(formData);
    if (Object.keys(validationErrors).length > 0) {
      setErrors(validationErrors);
      return;
    }
    
    // Set loading state
    setIsSubmitting(true);
    
    try {
      let resultLibrary: Library;
      
      if (library) {
        // Update existing library
        const updateData: LibraryUpdate = {
          name: formData.name,
          description: formData.description,
          category: formData.category,
          is_public: formData.is_public
        };
        
        resultLibrary = await dispatch(editLibrary({
          id: library.id,
          library: updateData
        })).unwrap();
        
        toast.success('Library updated successfully');
      } else {
        // Create new library
        const createData: LibraryCreate = {
          name: formData.name,
          description: formData.description,
          category: formData.category,
          is_public: formData.is_public,
          molecule_ids: initialMoleculeIds
        };
        
        resultLibrary = await dispatch(addLibrary(createData)).unwrap();
        
        toast.success('Library created successfully');
      }
      
      // Call success callback
      onSubmitSuccess(resultLibrary);
      
    } catch (error) {
      // Show error notification
      toast.error(toast.formatError(error));
    } finally {
      // Reset loading state
      setIsSubmitting(false);
    }
  };

  return (
    <Box sx={{ p: 2 }}>
      <form onSubmit={handleSubmit}>
        <Grid container spacing={3}>
          {/* Library Name */}
          <Grid item xs={12}>
            <TextField
              fullWidth
              required
              id="name"
              name="name"
              label="Library Name"
              value={formData.name}
              onChange={handleInputChange}
              error={!!errors.name}
              helperText={errors.name || 'Enter a unique name for this library'}
              disabled={isSubmitting}
              inputProps={{ maxLength: 100 }}
            />
          </Grid>
          
          {/* Library Description */}
          <Grid item xs={12}>
            <TextField
              fullWidth
              multiline
              rows={4}
              id="description"
              name="description"
              label="Description"
              value={formData.description}
              onChange={handleInputChange}
              error={!!errors.description}
              helperText={errors.description || 'Optional: Describe the purpose or contents of this library'}
              disabled={isSubmitting}
              inputProps={{ maxLength: 500 }}
            />
          </Grid>
          
          {/* Library Category */}
          <Grid item xs={12} md={6}>
            <FormControl fullWidth>
              <InputLabel id="category-label">Category</InputLabel>
              <Select
                labelId="category-label"
                id="category"
                name="category"
                value={formData.category || ''}
                onChange={handleSelectChange}
                label="Category"
                disabled={isSubmitting}
              >
                <MenuItem value="">
                  <em>None</em>
                </MenuItem>
                {Object.values(LibraryCategory).map((category) => (
                  <MenuItem key={category} value={category}>
                    {category.replace(/_/g, ' ')}
                  </MenuItem>
                ))}
              </Select>
            </FormControl>
          </Grid>
          
          {/* Public/Private Toggle */}
          <Grid item xs={12} md={6}>
            <FormControlLabel
              control={
                <Switch
                  checked={formData.is_public}
                  onChange={handleSwitchChange}
                  name="is_public"
                  color="primary"
                  disabled={isSubmitting}
                />
              }
              label="Make library visible to other users"
            />
          </Grid>
          
          {/* Form Buttons */}
          <Grid item xs={12} sx={{ mt: 2, display: 'flex', justifyContent: 'flex-end' }}>
            <Button
              variant="outlined"
              color="secondary"
              onClick={onCancel}
              disabled={isSubmitting}
              sx={{ mr: 2 }}
            >
              Cancel
            </Button>
            <Button
              type="submit"
              variant="contained"
              color="primary"
              disabled={isSubmitting}
              startIcon={isSubmitting ? <CircularProgress size={20} /> : null}
            >
              {library ? 'Update Library' : 'Create Library'}
            </Button>
          </Grid>
        </Grid>
      </form>
    </Box>
  );
};

export default LibraryForm;