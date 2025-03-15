import React from 'react';
import {
  Card,
  CardContent,
  CardActions,
  Typography,
  Box,
  Checkbox,
  IconButton,
  Tooltip
} from '@mui/material';
import { styled } from '@mui/material/styles';
import {
  InfoOutlined,
  Favorite,
  FavoriteBorder,
  MoreVert
} from '@mui/icons-material';

import { Molecule, MoleculeStatus } from '../../types/molecule.types';
import MoleculeViewer from './MoleculeViewer';
import StatusBadge from '../common/StatusBadge';
import { formatMolecularProperty, getPropertyDisplayName } from '../../utils/propertyFormatters';

/**
 * Props for the MoleculeCard component
 */
interface MoleculeCardProps {
  /** Molecule data to display */
  molecule: Molecule;
  /** Whether the molecule is selected */
  selected?: boolean;
  /** Callback when selection state changes */
  onSelect?: (molecule: Molecule, selected: boolean) => void;
  /** Callback when the card is clicked */
  onClick?: (molecule: Molecule) => void;
  /** Whether to show selection checkbox */
  showCheckbox?: boolean;
  /** Whether to show action buttons */
  showActions?: boolean;
  /** Whether to show molecule status */
  showStatus?: boolean;
  /** Property names to highlight on the card */
  highlightProperties?: string[];
  /** Additional CSS class name */
  className?: string;
}

/**
 * Styled Card component with selection state styling
 */
const StyledCard = styled(Card, {
  shouldForwardProp: (prop) => prop !== 'selected' && prop !== 'clickable',
})<{ selected: boolean; clickable: boolean }>(({ theme, selected, clickable }) => ({
  width: '300px',
  height: '350px',
  margin: theme.spacing(1),
  transition: 'all 0.3s ease',
  position: 'relative',
  cursor: clickable ? 'pointer' : 'default',
  border: selected ? `2px solid ${theme.palette.primary.main}` : 'none',
  boxShadow: selected ? theme.shadows[8] : theme.shadows[1],
  '&:hover': {
    boxShadow: theme.shadows[4],
  },
}));

/**
 * Container for the molecule structure visualization
 */
const MoleculeViewerContainer = styled(Box)(({ theme }) => ({
  height: '150px',
  width: '100%',
  display: 'flex',
  justifyContent: 'center',
  alignItems: 'center',
  marginBottom: theme.spacing(1),
}));

/**
 * Container for property display
 */
const PropertyContainer = styled(Box)(({ theme }) => ({
  display: 'flex',
  flexDirection: 'column',
  gap: theme.spacing(0.5),
}));

/**
 * Row for property name and value
 */
const PropertyRow = styled(Box)(({ theme }) => ({
  display: 'flex',
  justifyContent: 'space-between',
  alignItems: 'center',
}));

/**
 * Styled checkbox for molecule selection
 */
const SelectionCheckbox = styled(Box)(({ theme }) => ({
  position: 'absolute',
  top: '8px',
  left: '8px',
  zIndex: 1,
}));

/**
 * Container for status badge
 */
const StatusContainer = styled(Box)(({ theme }) => ({
  position: 'absolute',
  top: '8px',
  right: '8px',
  zIndex: 1,
}));

/**
 * Helper function to extract and format the properties to be displayed on the card
 * 
 * @param molecule - Molecule data object
 * @param highlightProperties - Optional array of property names to highlight
 * @returns Array of formatted properties for display
 */
function getHighlightedProperties(
  molecule: Molecule,
  highlightProperties?: string[]
): Array<{ name: string; displayName: string; value: string }> {
  if (!molecule.properties || molecule.properties.length === 0) {
    return [];
  }

  let propertiesToShow = molecule.properties;

  if (highlightProperties && highlightProperties.length > 0) {
    propertiesToShow = molecule.properties.filter(prop => 
      highlightProperties.includes(prop.name)
    );
  } else {
    // Default to important properties if available
    const defaultProperties = [
      'molecular_weight',
      'logp',
      'tpsa',
      'solubility',
      'ic50'
    ];

    propertiesToShow = molecule.properties.filter(prop => 
      defaultProperties.includes(prop.name)
    );
    
    // If no default properties are found, just show up to 3 properties
    if (propertiesToShow.length === 0 && molecule.properties.length > 0) {
      propertiesToShow = molecule.properties.slice(0, 3);
    }
  }

  // Format properties for display
  return propertiesToShow.map(prop => ({
    name: prop.name,
    displayName: getPropertyDisplayName(prop.name),
    value: formatMolecularProperty(prop.value, prop.name)
  }));
}

/**
 * A component that displays a molecule in a card format with structure visualization and key properties
 */
const MoleculeCard: React.FC<MoleculeCardProps> = ({
  molecule,
  selected = false,
  onSelect,
  onClick,
  showCheckbox = false,
  showActions = true,
  showStatus = true,
  highlightProperties,
  className,
}) => {
  const { id, smiles, status, properties } = molecule;
  
  // Get properties to display
  const displayProperties = getHighlightedProperties(molecule, highlightProperties);
  
  // Click handler for the card
  const handleClick = () => {
    if (onClick) {
      onClick(molecule);
    }
  };
  
  // Handler for checkbox selection
  const handleCheckboxChange = (event: React.ChangeEvent<HTMLInputElement>) => {
    event.stopPropagation();
    if (onSelect) {
      onSelect(molecule, event.target.checked);
    }
  };
  
  return (
    <StyledCard 
      selected={selected} 
      clickable={!!onClick}
      onClick={handleClick}
      className={className}
      data-testid={`molecule-card-${id}`}
    >
      {showCheckbox && (
        <SelectionCheckbox>
          <Checkbox
            checked={selected}
            onChange={handleCheckboxChange}
            onClick={(e) => e.stopPropagation()}
            color="primary"
            inputProps={{ 'aria-label': `Select molecule ${id}` }}
          />
        </SelectionCheckbox>
      )}
      
      {showStatus && status && (
        <StatusContainer>
          <StatusBadge 
            status={status} 
            statusType="molecule" 
            size="small"
            tooltip={`Status: ${status}`}
          />
        </StatusContainer>
      )}
      
      <CardContent>
        <MoleculeViewerContainer>
          <MoleculeViewer 
            smiles={smiles} 
            width="100%" 
            height="100%" 
            interactive={false}
            showControls={false}
          />
        </MoleculeViewerContainer>
        
        <PropertyContainer>
          {displayProperties.map((prop) => (
            <PropertyRow key={prop.name}>
              <Typography variant="body2" color="textSecondary">
                {prop.displayName}:
              </Typography>
              <Typography variant="body2" fontWeight="medium">
                {prop.value || '-'}
              </Typography>
            </PropertyRow>
          ))}
          
          {displayProperties.length === 0 && (
            <Typography variant="body2" color="textSecondary" align="center">
              No property data available
            </Typography>
          )}
        </PropertyContainer>
      </CardContent>
      
      {showActions && (
        <CardActions disableSpacing>
          <Tooltip title="Add to favorites">
            <IconButton size="small" aria-label="add to favorites">
              <FavoriteBorder />
            </IconButton>
          </Tooltip>
          <Tooltip title="View details">
            <IconButton size="small" aria-label="view details">
              <InfoOutlined />
            </IconButton>
          </Tooltip>
          <Box flexGrow={1} />
          <Tooltip title="More options">
            <IconButton size="small" aria-label="more options">
              <MoreVert />
            </IconButton>
          </Tooltip>
        </CardActions>
      )}
    </StyledCard>
  );
};

export default MoleculeCard;