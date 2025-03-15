import React, { useState, useEffect, useCallback } from 'react';
import { Box, Slider, Typography, TextField, InputAdornment } from '@mui/material'; // v5.0.0
import { styled } from '@mui/material/styles'; // v5.0.0
import { debounce } from 'lodash'; // v4.17.21
import { validateNumericRange } from '../../utils/validators';

// Interface for component props
interface PropertyRangeSliderProps {
  propertyName: string;
  displayName: string;
  minValue: number;
  maxValue: number;
  currentMin?: number | null;
  currentMax?: number | null;
  units?: string;
  step?: number;
  logarithmic?: boolean;
  onChange: (min: number | null, max: number | null) => void;
  className?: string;
}

// Styled components for consistent look and feel
const SliderContainer = styled(Box)(({ theme }) => ({
  display: 'flex',
  flexDirection: 'column',
  width: '100%',
  marginBottom: theme.spacing(2),
}));

const SliderLabel = styled(Typography)(({ theme }) => ({
  fontWeight: 500,
  marginBottom: theme.spacing(1),
}));

const InputContainer = styled(Box)(({ theme }) => ({
  display: 'flex',
  justifyContent: 'space-between',
  marginTop: theme.spacing(1),
}));

const ValueInput = styled(TextField)({
  width: '45%',
  '& input': {
    textAlign: 'right',
  },
});

const StyledSlider = styled(Slider)(({ theme }) => ({
  marginTop: theme.spacing(1),
  marginBottom: theme.spacing(1),
}));

/**
 * Formats numeric values for display, handling scientific notation for very small or large numbers
 */
const formatValue = (value: number, useScientificNotation: boolean = false): string => {
  if (value === null || value === undefined) {
    return '';
  }
  
  // Use scientific notation for very small or large numbers
  if (useScientificNotation && (Math.abs(value) < 0.001 || Math.abs(value) > 9999)) {
    return value.toExponential(2);
  }
  
  // Format based on value magnitude
  if (Math.abs(value) >= 100) {
    return value.toFixed(0);
  } else if (Math.abs(value) >= 10) {
    return value.toFixed(1);
  } else if (Math.abs(value) >= 1) {
    return value.toFixed(2);
  } else {
    return value.toFixed(3);
  }
};

/**
 * A reusable component that provides a dual-handle slider for selecting minimum and maximum values 
 * for molecular property filtering. This component is used throughout the application to enable 
 * users to filter molecules based on numeric property ranges.
 */
const PropertyRangeSlider: React.FC<PropertyRangeSliderProps> = ({
  propertyName,
  displayName,
  minValue,
  maxValue,
  currentMin = null,
  currentMax = null,
  units,
  step,
  logarithmic = false,
  onChange,
  className,
}) => {
  // Calculate default step if not provided
  const calculatedStep = step || Math.max((maxValue - minValue) / 100, 0.001);
  
  // Initialize internal state with provided values or defaults
  const initialMin = currentMin ?? minValue;
  const initialMax = currentMax ?? maxValue;
  
  // Internal state for slider value
  const [internalValue, setInternalValue] = useState<[number, number]>([initialMin, initialMax]);
  
  // Text input values
  const [minInputValue, setMinInputValue] = useState(formatValue(initialMin, logarithmic));
  const [maxInputValue, setMaxInputValue] = useState(formatValue(initialMax, logarithmic));
  
  // Track if user is editing the input fields
  const [isEditing, setIsEditing] = useState(false);

  // Create debounced onChange to prevent excessive updates
  const debouncedOnChange = useCallback(
    debounce((min: number | null, max: number | null) => {
      onChange(min, max);
    }, 300),
    [onChange]
  );

  // Update internal state when props change (unless user is editing)
  useEffect(() => {
    if (!isEditing) {
      const newMin = currentMin ?? minValue;
      const newMax = currentMax ?? maxValue;
      
      setInternalValue([newMin, newMax]);
      setMinInputValue(formatValue(newMin, logarithmic));
      setMaxInputValue(formatValue(newMax, logarithmic));
    }
  }, [currentMin, currentMax, minValue, maxValue, logarithmic, isEditing]);

  // Handle slider change (while dragging)
  const handleSliderChange = (_event: Event, newValue: number | number[]) => {
    if (Array.isArray(newValue)) {
      setInternalValue(newValue as [number, number]);
      setMinInputValue(formatValue(newValue[0], logarithmic));
      setMaxInputValue(formatValue(newValue[1], logarithmic));
    }
  };

  // Handle slider change completion (after drag ends)
  const handleSliderChangeCommitted = (_event: React.SyntheticEvent | Event, newValue: number | number[]) => {
    if (Array.isArray(newValue)) {
      // Check if the value has actually changed
      if (
        newValue[0] !== (currentMin ?? minValue) ||
        newValue[1] !== (currentMax ?? maxValue)
      ) {
        debouncedOnChange(newValue[0], newValue[1]);
      }
    }
  };

  // Handle minimum input field change
  const handleMinInputChange = (event: React.ChangeEvent<HTMLInputElement>) => {
    setIsEditing(true);
    setMinInputValue(event.target.value);
  };

  // Handle maximum input field change
  const handleMaxInputChange = (event: React.ChangeEvent<HTMLInputElement>) => {
    setIsEditing(true);
    setMaxInputValue(event.target.value);
  };

  // Handle input field blur (validate and commit)
  const handleInputBlur = () => {
    // Parse input values
    const parsedMin = parseFloat(minInputValue);
    const parsedMax = parseFloat(maxInputValue);
    
    // Validate input values using validator utility
    const minValidation = !isNaN(parsedMin) 
      ? validateNumericRange(parsedMin, propertyName, minValue, maxValue)
      : { valid: true, error: null };
      
    const maxValidation = !isNaN(parsedMax)
      ? validateNumericRange(parsedMax, propertyName, minValue, maxValue)
      : { valid: true, error: null };
    
    // Use validated or default values
    const validMin = !isNaN(parsedMin) && minValidation.valid
      ? parsedMin
      : (currentMin ?? minValue);
      
    const validMax = !isNaN(parsedMax) && maxValidation.valid
      ? parsedMax
      : (currentMax ?? maxValue);
    
    // Ensure min <= max
    const finalMin = Math.min(validMin, validMax);
    const finalMax = Math.max(validMin, validMax);
    
    // Update state
    setInternalValue([finalMin, finalMax]);
    setMinInputValue(formatValue(finalMin, logarithmic));
    setMaxInputValue(formatValue(finalMax, logarithmic));
    
    // Notify parent if values have changed
    if (
      finalMin !== (currentMin ?? minValue) ||
      finalMax !== (currentMax ?? maxValue)
    ) {
      debouncedOnChange(finalMin, finalMax);
    }
    
    setIsEditing(false);
  };

  // Handle Enter key in input field
  const handleInputKeyDown = (event: React.KeyboardEvent) => {
    if (event.key === 'Enter') {
      handleInputBlur();
    }
  };

  return (
    <SliderContainer className={className}>
      <SliderLabel variant="body1" id={`${propertyName}-label`}>{displayName}</SliderLabel>
      
      <StyledSlider
        value={internalValue}
        onChange={handleSliderChange}
        onChangeCommitted={handleSliderChangeCommitted}
        valueLabelDisplay="auto"
        min={minValue}
        max={maxValue}
        step={calculatedStep}
        aria-labelledby={`${propertyName}-label`}
        disableSwap // Prevents handles from swapping positions
        getAriaValueText={(value) => `${value}${units ? ` ${units}` : ''}`}
        valueLabelFormat={(value) => formatValue(value, logarithmic)}
      />
      
      <InputContainer>
        <ValueInput
          value={minInputValue}
          onChange={handleMinInputChange}
          onBlur={handleInputBlur}
          onKeyDown={handleInputKeyDown}
          size="small"
          label="Min"
          variant="outlined"
          InputProps={{
            endAdornment: units ? (
              <InputAdornment position="end">{units}</InputAdornment>
            ) : null,
          }}
          inputProps={{
            'aria-labelledby': `${propertyName}-min-input`,
            'aria-label': `Minimum ${displayName}`,
          }}
        />
        
        <ValueInput
          value={maxInputValue}
          onChange={handleMaxInputChange}
          onBlur={handleInputBlur}
          onKeyDown={handleInputKeyDown}
          size="small"
          label="Max"
          variant="outlined"
          InputProps={{
            endAdornment: units ? (
              <InputAdornment position="end">{units}</InputAdornment>
            ) : null,
          }}
          inputProps={{
            'aria-labelledby': `${propertyName}-max-input`,
            'aria-label': `Maximum ${displayName}`,
          }}
        />
      </InputContainer>
    </SliderContainer>
  );
};

export default PropertyRangeSlider;