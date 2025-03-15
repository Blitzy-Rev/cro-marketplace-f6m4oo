import React from 'react';
import {
  Stepper,
  Step,
  StepLabel,
  StepContent,
  StepButton,
  StepConnector,
  Box,
  Typography,
  Button,
  styled
} from '@mui/material'; // @mui/material ^5.0.0
import { Check as CheckIcon } from '@mui/icons-material'; // @mui/icons-material ^5.0.0
import TabPanel, { a11yProps } from '../common/TabPanel';
import StatusBadge from '../common/StatusBadge';

/**
 * Styled StepConnector component for custom connector appearance
 */
const StyledStepConnector = styled(StepConnector)(({ theme }) => ({
  '& .MuiStepConnector-line': {
    borderColor: theme.palette.primary.light,
    borderWidth: '2px',
  },
}));

/**
 * Styled StepLabel component for custom label appearance
 */
const StyledStepLabel = styled(StepLabel)(({ theme }) => ({
  '& .MuiStepLabel-label': {
    fontWeight: 500,
  },
  '& .MuiStepLabel-label.Mui-active': {
    fontWeight: 700,
    color: theme.palette.primary.main,
  },
  '& .MuiStepLabel-label.Mui-completed': {
    fontWeight: 700,
    color: theme.palette.success.main,
  },
}));

/**
 * Interface for the step content component
 */
interface StepContentProps {
  children: React.ReactNode;
  activeStep: number;
  index: number;
}

/**
 * Main props interface for the SubmissionStepper component
 */
interface SubmissionStepperProps {
  /** Current active step index */
  activeStep: number;
  /** Array of step definitions with labels and optional flags */
  steps: Array<{ label: string; optional?: boolean; completed?: boolean }>;
  /** Callback function when step changes */
  onStepChange: (step: number) => void;
  /** Content for each step */
  children: React.ReactNode | React.ReactNode[];
  /** Orientation of the stepper */
  orientation?: 'horizontal' | 'vertical';
  /** Visual variant of the stepper */
  variant?: 'standard' | 'outlined' | 'contained';
  /** Function to determine if a step is complete */
  isStepComplete?: (step: number) => boolean;
  /** Function to determine if a step is optional */
  isStepOptional?: (step: number) => boolean;
  /** Function to determine if a step is skipped */
  isStepSkipped?: (step: number) => boolean;
  /** Additional CSS class name */
  className?: string;
}

/**
 * A component that renders a multi-step stepper interface for the CRO submission workflow.
 * 
 * This component implements a Material-UI Stepper with enhanced accessibility and
 * supports both horizontal and vertical layouts. It provides visual indication of
 * progress through the submission process and manages the display of different form steps.
 */
const SubmissionStepper: React.FC<SubmissionStepperProps> = ({
  activeStep,
  steps,
  onStepChange,
  children,
  orientation = 'horizontal',
  variant = 'standard',
  isStepComplete,
  isStepOptional,
  isStepSkipped,
  className,
}) => {
  // Helper to check if a step is completed
  const handleStepComplete = (step: number): boolean => {
    if (isStepComplete) {
      return isStepComplete(step);
    }
    return Boolean(steps[step]?.completed);
  };

  // Helper to check if a step is optional
  const handleStepOptional = (step: number): boolean => {
    if (isStepOptional) {
      return isStepOptional(step);
    }
    return Boolean(steps[step]?.optional);
  };

  // Helper to check if a step is skipped
  const handleStepSkipped = (step: number): boolean => {
    if (isStepSkipped) {
      return isStepSkipped(step);
    }
    return false;
  };

  // Handle step change
  const handleStep = (step: number) => {
    onStepChange(step);
  };

  // Handle next button click
  const handleNext = () => {
    onStepChange(activeStep + 1);
  };

  // Handle back button click
  const handleBack = () => {
    onStepChange(activeStep - 1);
  };

  // Cast children to array for easier handling
  const childrenArray = React.Children.toArray(children);

  return (
    <Box className={className} sx={{ width: '100%' }}>
      <Stepper 
        activeStep={activeStep} 
        orientation={orientation}
        connector={<StyledStepConnector />}
        sx={{ mb: 3 }}
      >
        {steps.map((step, index) => {
          const isStepOptionalValue = handleStepOptional(index);
          const isStepCompletedValue = handleStepComplete(index);
          const isStepSkippedValue = handleStepSkipped(index);
          
          return (
            <Step 
              key={step.label} 
              completed={!isStepSkippedValue && isStepCompletedValue}
            >
              <StepButton 
                onClick={() => handleStep(index)}
                aria-label={`Go to step ${index + 1}: ${step.label}`}
                aria-current={activeStep === index ? 'step' : undefined}
              >
                <StyledStepLabel
                  StepIconProps={{
                    icon: isStepCompletedValue ? <CheckIcon /> : index + 1,
                  }}
                  optional={
                    isStepOptionalValue ? (
                      <Typography variant="caption" color="text.secondary">
                        Optional
                      </Typography>
                    ) : undefined
                  }
                >
                  {step.label}
                  {isStepCompletedValue && (
                    <Box component="span" sx={{ ml: 1, display: 'inline-flex', alignItems: 'center' }}>
                      <StatusBadge 
                        status="completed" 
                        statusType="custom" 
                        customColor="#4caf50" 
                        customLabel="Completed"
                        size="small"
                      />
                    </Box>
                  )}
                </StyledStepLabel>
              </StepButton>
              
              {orientation === 'vertical' && (
                <StepContent>
                  {childrenArray[index]}
                  <Box sx={{ display: 'flex', flexDirection: 'row', pt: 2 }}>
                    <Button
                      color="inherit"
                      disabled={index === 0}
                      onClick={handleBack}
                      sx={{ mr: 1 }}
                      aria-label="Go to previous step"
                    >
                      Back
                    </Button>
                    <Box sx={{ flex: '1 1 auto' }} />
                    <Button 
                      onClick={handleNext}
                      variant="contained"
                      disabled={index >= steps.length - 1}
                      aria-label={index === steps.length - 2 ? 'Finish submission' : 'Go to next step'}
                    >
                      {index === steps.length - 2 ? 'Finish' : 'Next'}
                    </Button>
                  </Box>
                </StepContent>
              )}
            </Step>
          );
        })}
      </Stepper>
      
      {orientation === 'horizontal' && (
        <>
          {/* Render step content for horizontal orientation */}
          {childrenArray.map((child, index) => (
            <TabPanel key={index} value={activeStep} index={index} {...a11yProps(index)}>
              {child}
            </TabPanel>
          ))}
          
          <Box sx={{ display: 'flex', flexDirection: 'row', pt: 2 }}>
            <Button
              color="inherit"
              disabled={activeStep === 0}
              onClick={handleBack}
              sx={{ mr: 1 }}
              aria-label="Go to previous step"
            >
              Back
            </Button>
            <Box sx={{ flex: '1 1 auto' }} />
            <Button 
              onClick={handleNext}
              variant="contained"
              disabled={activeStep >= steps.length - 1}
              aria-label={activeStep === steps.length - 2 ? 'Finish submission' : 'Go to next step'}
            >
              {activeStep === steps.length - 2 ? 'Finish' : 'Next'}
            </Button>
          </Box>
        </>
      )}
    </Box>
  );
};

export default SubmissionStepper;