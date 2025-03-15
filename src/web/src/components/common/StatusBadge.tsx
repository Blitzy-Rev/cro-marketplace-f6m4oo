import React from 'react';
import { Chip, Tooltip } from '@mui/material';
import { styled } from '@mui/material/styles';
import { SubmissionStatus } from '../../types/submission.types';
import { MoleculeStatus } from '../../types/molecule.types';
import { getStatusColor, getStatusDisplayName } from '../../constants/submissionStatus';

/**
 * Props for the StatusBadge component
 */
interface StatusBadgeProps {
  /** The status to display */
  status: SubmissionStatus | MoleculeStatus | string;
  /** The type of status being displayed */
  statusType?: 'submission' | 'molecule' | 'custom';
  /** Size variant for the badge */
  size?: 'small' | 'medium';
  /** Optional tooltip text to display on hover */
  tooltip?: string;
  /** Optional CSS class name for additional styling */
  className?: string;
  /** Optional custom color for the badge (used when statusType is 'custom') */
  customColor?: string;
  /** Optional custom label for the badge (used when statusType is 'custom') */
  customLabel?: string;
}

/**
 * Helper function to get the color for a molecule status
 * @param status The molecule status
 * @returns Hex color code for the status
 */
const getMoleculeStatusColor = (status: MoleculeStatus): string => {
  const colors: Record<MoleculeStatus, string> = {
    [MoleculeStatus.AVAILABLE]: '#4caf50', // Green
    [MoleculeStatus.PENDING]: '#ff9800',   // Orange
    [MoleculeStatus.TESTING]: '#2196f3',   // Blue
    [MoleculeStatus.RESULTS]: '#9c27b0',   // Purple
    [MoleculeStatus.ARCHIVED]: '#9e9e9e',  // Gray
  };
  
  return colors[status as MoleculeStatus] || '#9e9e9e';
};

/**
 * Helper function to get the display name for a molecule status
 * @param status The molecule status
 * @returns Human-readable status name
 */
const getMoleculeStatusDisplayName = (status: MoleculeStatus): string => {
  const displayNames: Record<MoleculeStatus, string> = {
    [MoleculeStatus.AVAILABLE]: 'Available',
    [MoleculeStatus.PENDING]: 'Pending',
    [MoleculeStatus.TESTING]: 'Testing',
    [MoleculeStatus.RESULTS]: 'Results Available',
    [MoleculeStatus.ARCHIVED]: 'Archived',
  };
  
  return displayNames[status as MoleculeStatus] || status.toString();
};

/**
 * Helper function to get contrasting text color for a background color
 * @param backgroundColor The background color in hex format
 * @returns Black or white text color based on background brightness
 */
const getContrastTextColor = (backgroundColor: string): string => {
  // Simple algorithm to determine if text should be light or dark
  // Convert hex to rgb
  const hex = backgroundColor.replace('#', '');
  const r = parseInt(hex.substr(0, 2), 16);
  const g = parseInt(hex.substr(2, 2), 16);
  const b = parseInt(hex.substr(4, 2), 16);
  
  // Calculate brightness
  const brightness = (r * 299 + g * 587 + b * 114) / 1000;
  
  // Return black or white depending on brightness
  return brightness > 128 ? 'rgba(0, 0, 0, 0.87)' : '#ffffff';
};

/**
 * Styled Chip component with customizable background color
 */
const StyledChip = styled(Chip, {
  shouldForwardProp: (prop) => prop !== 'color',
})<{ color: string }>(({ color }) => ({
  backgroundColor: color,
  color: getContrastTextColor(color),
  fontWeight: 500,
  borderRadius: '16px',
}));

/**
 * A component that displays a status badge with appropriate styling based on the status type
 */
const StatusBadge: React.FC<StatusBadgeProps> = ({
  status,
  statusType = 'submission',
  size = 'medium',
  tooltip,
  className,
  customColor,
  customLabel,
}) => {
  // Determine color based on status type
  let color: string;
  let label: string;
  
  if (statusType === 'custom' && customColor) {
    color = customColor;
    label = customLabel || String(status);
  } else if (statusType === 'molecule') {
    color = getMoleculeStatusColor(status as MoleculeStatus);
    label = getMoleculeStatusDisplayName(status as MoleculeStatus);
  } else { // Default to submission status
    color = getStatusColor(status as SubmissionStatus);
    label = getStatusDisplayName(status as SubmissionStatus);
  }
  
  // Render chip, optionally wrapped in tooltip
  const badge = (
    <StyledChip
      label={label}
      color={color}
      size={size}
      className={className}
    />
  );
  
  return tooltip ? (
    <Tooltip title={tooltip}>
      {badge}
    </Tooltip>
  ) : badge;
};

export default StatusBadge;