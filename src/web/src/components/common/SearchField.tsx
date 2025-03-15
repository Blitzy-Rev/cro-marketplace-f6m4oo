import React, { useState, useEffect, useCallback } from 'react';
import { TextField, InputAdornment, IconButton } from '@mui/material'; // ^5.0.0
import { Search, Clear } from '@mui/icons-material'; // ^5.0.0
import { styled } from '@mui/material/styles'; // ^5.0.0
import useDebounce from '../../hooks/useDebounce';

/**
 * Props for the SearchField component
 */
interface SearchFieldProps {
  /** Current search value */
  value: string;
  /** Callback function when search value changes (debounced) */
  onChange: (value: string) => void;
  /** Placeholder text for the search field */
  placeholder?: string;
  /** Debounce time in milliseconds */
  debounceTime?: number;
  /** Whether the search field should take full width */
  fullWidth?: boolean;
  /** Material UI TextField variant */
  variant?: 'outlined' | 'filled' | 'standard';
  /** Material UI TextField size */
  size?: 'small' | 'medium';
  /** Additional CSS class name */
  className?: string;
  /** Whether the search field is disabled */
  disabled?: boolean;
  /** Whether the search field should auto-focus */
  autoFocus?: boolean;
  /** Whether to show a clear button */
  clearable?: boolean;
  /** Callback function when clear button is clicked */
  onClear?: () => void;
}

/**
 * Styled TextField component with customized appearance
 */
const StyledTextField = styled(TextField)({
  '& .MuiOutlinedInput-root': {
    borderRadius: '20px',
  },
  '& .MuiInputBase-input': {
    padding: '10px 14px',
  },
});

/**
 * A reusable search input component with debounced search functionality.
 * This component is used throughout the application for searching various data types,
 * particularly for molecule searching by SMILES patterns or other properties.
 */
const SearchField = ({
  value,
  onChange,
  placeholder = 'Search...',
  debounceTime = 300,
  fullWidth = false,
  variant = 'outlined',
  size = 'medium',
  className,
  disabled = false,
  autoFocus = false,
  clearable = true,
  onClear,
}: SearchFieldProps): JSX.Element => {
  // Internal state for the input value
  const [inputValue, setInputValue] = useState<string>(value);

  // Debounced value using the useDebounce hook
  const debouncedValue = useDebounce(inputValue, debounceTime);

  // Trigger onChange callback when debounced value changes
  useEffect(() => {
    onChange(debouncedValue);
  }, [debouncedValue, onChange]);

  // Update internal state when external value changes
  useEffect(() => {
    if (value !== inputValue) {
      setInputValue(value);
    }
  }, [value]);

  // Handle input change
  const handleChange = useCallback((e: React.ChangeEvent<HTMLInputElement>) => {
    setInputValue(e.target.value);
  }, []);

  // Handle clear button click
  const handleClear = useCallback(() => {
    setInputValue('');
    if (onClear) {
      onClear();
    }
  }, [onClear]);

  return (
    <StyledTextField
      value={inputValue}
      onChange={handleChange}
      placeholder={placeholder}
      variant={variant}
      size={size}
      fullWidth={fullWidth}
      className={className}
      disabled={disabled}
      autoFocus={autoFocus}
      InputProps={{
        startAdornment: (
          <InputAdornment position="start">
            <Search color="action" />
          </InputAdornment>
        ),
        endAdornment: clearable && inputValue ? (
          <InputAdornment position="end">
            <IconButton
              aria-label="clear search"
              onClick={handleClear}
              edge="end"
              size="small"
            >
              <Clear fontSize="small" />
            </IconButton>
          </InputAdornment>
        ) : null,
      }}
      aria-label="search field"
      data-testid="search-field"
    />
  );
};

export default SearchField;