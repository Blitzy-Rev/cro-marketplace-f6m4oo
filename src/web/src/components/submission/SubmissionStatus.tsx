import React from 'react';
import { Box, Paper, Typography, Stepper, Step, StepLabel, StepContent, Divider, Tooltip } from '@mui/material';
import { Timeline, TimelineItem, TimelineSeparator, TimelineConnector, TimelineContent, TimelineDot, TimelineOppositeContent } from '@mui/lab';
import { styled } from '@mui/material/styles';
import StatusBadge from '../common/StatusBadge';
import { SubmissionStatus as SubmissionStatusEnum } from '../../types/submission.types';
import { getStatusColor, getStatusDisplayName, getStatusDescription } from '../../constants/submissionStatus';
import { Submission } from '../../types/submission.types';
import { formatDate } from '../../utils/dateFormatter';

/**
 * Props for the SubmissionStatus component
 */
interface SubmissionStatusProps {
  /** The submission object containing status and date information */
  submission: Submission;
  /** The visualization style to use */
  variant?: 'timeline' | 'stepper' | 'badge';
  /** Optional CSS class name for additional styling */
  className?: string;
  /** Whether to show a compact version with fewer steps */
  compact?: boolean;
}

/**
 * Styled component for timeline dots with status-based colors
 */
const StyledTimelineDot = styled(TimelineDot, {
  shouldForwardProp: (prop) => prop !== 'status' && prop !== 'color',
})<{ status: 'completed' | 'active' | 'future'; color: string }>(({ status, color }) => ({
  backgroundColor: status === 'future' ? '#f5f5f5' : color,
  borderColor: color,
  color: status === 'future' ? color : '#fff',
  boxShadow: status === 'active' ? '0 0 0 3px rgba(0, 0, 0, 0.1)' : 'none',
}));

/**
 * Styled component for step labels with status-based colors
 */
const StyledStepLabel = styled(StepLabel, {
  shouldForwardProp: (prop) => prop !== 'status',
})<{ status: 'completed' | 'active' | 'future' }>(({ status }) => ({
  '& .MuiStepLabel-label': {
    fontWeight: status === 'active' ? 'bold' : 'normal',
  },
}));

/**
 * Helper function to determine if a step is completed, active, or future
 * @param currentStepIndex Current step index in the workflow
 * @param stepIndex Step index being evaluated
 * @returns The status of the step ('completed', 'active', or 'future')
 */
const getStepStatus = (currentStepIndex: number, stepIndex: number): 'completed' | 'active' | 'future' => {
  if (stepIndex < currentStepIndex) return 'completed';
  if (stepIndex === currentStepIndex) return 'active';
  return 'future';
};

/**
 * Helper function to get the date for a specific step from the submission
 * @param submission The submission object
 * @param status The status to get the date for
 * @returns Formatted date string or null if not available
 */
const getStepDate = (submission: Submission, status: SubmissionStatusEnum): string | null => {
  switch (status) {
    case SubmissionStatusEnum.DRAFT:
      return submission.created_at ? formatDate(submission.created_at) : null;
    case SubmissionStatusEnum.SUBMITTED:
      return submission.submitted_at ? formatDate(submission.submitted_at) : null;
    case SubmissionStatusEnum.APPROVED:
      return submission.approved_at ? formatDate(submission.approved_at) : null;
    case SubmissionStatusEnum.COMPLETED:
      return submission.completed_at ? formatDate(submission.completed_at) : null;
    default:
      return null;
  }
};

/**
 * A component that visualizes the status and progress of a CRO submission
 */
const SubmissionStatus: React.FC<SubmissionStatusProps> = ({
  submission,
  variant = 'timeline',
  className,
  compact = false,
}) => {
  // Define the workflow steps based on compact mode
  const workflowSteps = compact
    ? [
        SubmissionStatusEnum.DRAFT,
        SubmissionStatusEnum.SUBMITTED,
        SubmissionStatusEnum.APPROVED,
        SubmissionStatusEnum.IN_PROGRESS,
        SubmissionStatusEnum.COMPLETED,
      ]
    : [
        SubmissionStatusEnum.DRAFT,
        SubmissionStatusEnum.SUBMITTED,
        SubmissionStatusEnum.PENDING_REVIEW,
        SubmissionStatusEnum.PRICING_PROVIDED,
        SubmissionStatusEnum.APPROVED,
        SubmissionStatusEnum.IN_PROGRESS,
        SubmissionStatusEnum.RESULTS_UPLOADED,
        SubmissionStatusEnum.RESULTS_REVIEWED,
        SubmissionStatusEnum.COMPLETED,
      ];

  // Handle rejected and cancelled statuses
  const terminalStatuses = [SubmissionStatusEnum.REJECTED, SubmissionStatusEnum.CANCELLED];
  
  // Find the current step index
  let currentStepIndex = workflowSteps.findIndex(step => step === submission.status);
  
  // If the status is not in our workflow steps (like REJECTED or CANCELLED),
  // use the last known status from the workflow
  if (currentStepIndex === -1) {
    if (terminalStatuses.includes(submission.status)) {
      // For terminal statuses, show as a special case
      currentStepIndex = -2; // Special case for terminal statuses
    } else {
      // For any other status not in our workflow, default to the first step
      currentStepIndex = 0;
    }
  }

  // Timeline variant
  if (variant === 'timeline') {
    return (
      <Box className={className}>
        <Timeline position="alternate" sx={{ p: 0, m: 0 }}>
          {workflowSteps.map((step, index) => {
            const stepStatus = getStepStatus(currentStepIndex, index);
            const stepDate = getStepDate(submission, step);
            const color = getStatusColor(step);
            
            return (
              <TimelineItem key={step}>
                <TimelineOppositeContent sx={{ m: 'auto 0' }}>
                  {stepDate && <Typography variant="body2" color="text.secondary">{stepDate}</Typography>}
                </TimelineOppositeContent>
                
                <TimelineSeparator>
                  <Tooltip title={getStatusDescription(step)}>
                    <StyledTimelineDot
                      status={stepStatus}
                      color={color}
                      variant={stepStatus === 'future' ? 'outlined' : 'filled'}
                    />
                  </Tooltip>
                  {index < workflowSteps.length - 1 && <TimelineConnector />}
                </TimelineSeparator>
                
                <TimelineContent sx={{ py: '12px', px: 2 }}>
                  <Typography 
                    variant="body1" 
                    fontWeight={stepStatus === 'active' ? 'bold' : 'normal'}
                  >
                    {getStatusDisplayName(step)}
                  </Typography>
                </TimelineContent>
              </TimelineItem>
            );
          })}
          
          {/* Add special item for rejected or cancelled status */}
          {terminalStatuses.includes(submission.status) && (
            <TimelineItem>
              <TimelineOppositeContent sx={{ m: 'auto 0' }}>
                {formatDate(submission.updated_at)}
              </TimelineOppositeContent>
              
              <TimelineSeparator>
                <Tooltip title={getStatusDescription(submission.status)}>
                  <StyledTimelineDot
                    status="active"
                    color={getStatusColor(submission.status)}
                    variant="filled"
                  />
                </Tooltip>
              </TimelineSeparator>
              
              <TimelineContent sx={{ py: '12px', px: 2 }}>
                <Typography 
                  variant="body1" 
                  fontWeight="bold"
                >
                  {getStatusDisplayName(submission.status)}
                </Typography>
              </TimelineContent>
            </TimelineItem>
          )}
        </Timeline>
      </Box>
    );
  }
  
  // Stepper variant
  if (variant === 'stepper') {
    return (
      <Box className={className}>
        <Stepper activeStep={currentStepIndex} alternativeLabel orientation="horizontal">
          {workflowSteps.map((step, index) => {
            const stepStatus = getStepStatus(currentStepIndex, index);
            const stepDate = getStepDate(submission, step);
            
            return (
              <Step key={step} completed={stepStatus === 'completed'}>
                <Tooltip title={getStatusDescription(step)}>
                  <StyledStepLabel
                    status={stepStatus}
                    StepIconProps={{
                      style: {
                        color: stepStatus === 'future' ? undefined : getStatusColor(step),
                      },
                    }}
                  >
                    {getStatusDisplayName(step)}
                    {stepDate && (
                      <Typography variant="caption" display="block" color="text.secondary">
                        {stepDate}
                      </Typography>
                    )}
                  </StyledStepLabel>
                </Tooltip>
              </Step>
            );
          })}
        </Stepper>
        
        {/* Show terminal status message if applicable */}
        {terminalStatuses.includes(submission.status) && (
          <Box mt={2} textAlign="center">
            <Paper elevation={0} sx={{ p: 2, bgcolor: 'background.default' }}>
              <Typography color="error">
                This submission was {submission.status.toLowerCase()} on {formatDate(submission.updated_at)}
              </Typography>
            </Paper>
          </Box>
        )}
      </Box>
    );
  }
  
  // Badge variant (simplest form)
  return (
    <StatusBadge
      status={submission.status}
      statusType="submission"
      className={className}
      tooltip={getStatusDescription(submission.status)}
    />
  );
};

export default SubmissionStatus;