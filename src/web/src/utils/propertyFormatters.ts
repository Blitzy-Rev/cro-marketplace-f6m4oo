import { PropertyType } from '../types/molecule.types';
import { PROPERTY_UNITS, PROPERTY_DISPLAY_NAMES } from '../constants/moleculeProperties';
import { formatNumber, formatPercentage } from './formatters';

/**
 * Formats a molecular property value with appropriate precision and units based on property name
 * @param value - The property value to format
 * @param propertyName - The name of the property
 * @returns Formatted property value with appropriate units
 */
export function formatMolecularProperty(value: any, propertyName: string): string {
  if (value === null || value === undefined || value === '') {
    return '';
  }
  
  // Handle special cases for common properties
  switch (propertyName) {
    case 'molecular_weight':
      return `${formatNumber(value, 2)} g/mol`;
    case 'logp':
      return formatNumber(value, 2);
    case 'tpsa':
      return `${formatNumber(value, 1)} Å²`;
    case 'solubility':
      return `${formatNumber(value, 2)} mg/mL`;
    case 'ic50':
    case 'ec50':
      return `${formatNumber(value, 2)} nM`;
    case 'binding_affinity':
      return `${formatNumber(value, 2)} nM`;
    case 'bioavailability':
      return formatPercentage(value, 1);
    case 'half_life':
      return `${formatNumber(value, 1)} h`;
    case 'permeability':
      return `${formatNumber(value, 6)} cm/s`;
    default:
      // For Boolean properties
      if (typeof value === 'boolean') {
        return value ? 'Yes' : 'No';
      }
      
      // For numeric properties
      if (typeof value === 'number' || (typeof value === 'string' && !isNaN(parseFloat(value)))) {
        const precision = propertyName.startsWith('num_') ? 0 : getPropertyPrecision(propertyName);
        return formatPropertyWithUnit(value, propertyName, precision);
      }
      
      // For String properties
      return String(value);
  }
}

/**
 * Formats a property value and appends its unit if available
 * @param value - The property value to format
 * @param propertyName - The name of the property
 * @param precision - The number of decimal places to include
 * @returns Formatted value with unit
 */
export function formatPropertyWithUnit(value: any, propertyName: string, precision: number = 2): string {
  const formattedValue = formatNumber(value, precision);
  const unit = PROPERTY_UNITS[propertyName] || '';
  
  return unit ? `${formattedValue} ${unit}` : formattedValue;
}

/**
 * Gets the user-friendly display name for a property
 * @param propertyName - The property name
 * @returns User-friendly display name
 */
export function getPropertyDisplayName(propertyName: string): string {
  // Check if we have a predefined display name
  if (PROPERTY_DISPLAY_NAMES[propertyName]) {
    return PROPERTY_DISPLAY_NAMES[propertyName];
  }
  
  // Otherwise generate a display name by capitalizing words and replacing underscores
  const words = propertyName.split('_');
  const capitalizedWords = words.map(word => 
    word.length > 0 ? word.charAt(0).toUpperCase() + word.slice(1) : word
  );
  
  return capitalizedWords.join(' ');
}

/**
 * Formats an AI prediction confidence score as a percentage with color coding information
 * @param confidence - The confidence score (0-1)
 * @returns Object with formatted value and color code
 */
export function formatPredictionConfidence(confidence: number | string | null | undefined): { value: string, color: string } {
  if (confidence === null || confidence === undefined || confidence === '') {
    return { value: '', color: 'default' };
  }
  
  const numConfidence = typeof confidence === 'string' ? parseFloat(confidence) : confidence;
  
  if (isNaN(numConfidence)) {
    return { value: '', color: 'default' };
  }
  
  // Format the confidence as a percentage
  const formattedValue = formatPercentage(numConfidence);
  
  // Determine color based on confidence level
  let color = 'default';
  if (numConfidence >= 0.8) {
    color = 'success';
  } else if (numConfidence >= 0.6) {
    color = 'warning';
  } else {
    color = 'error';
  }
  
  return { value: formattedValue, color };
}

/**
 * Determines the appropriate decimal precision for a property based on its name
 * @param propertyName - The property name
 * @returns Number of decimal places
 */
export function getPropertyPrecision(propertyName: string): number {
  // Integer properties (no decimals)
  if (['num_atoms', 'num_heavy_atoms', 'num_rings', 'num_rotatable_bonds', 'num_h_donors', 'num_h_acceptors', 'lipinski_violations'].includes(propertyName)) {
    return 0;
  }
  
  // Properties requiring high precision
  if (['logp', 'pka', 'pkb', 'ic50', 'ec50', 'binding_affinity'].includes(propertyName)) {
    return 3;
  }
  
  // Properties requiring medium precision
  if (['molecular_weight', 'exact_mass', 'solubility', 'melting_point', 'boiling_point'].includes(propertyName)) {
    return 2;
  }
  
  // Percentage properties
  if (['bioavailability'].includes(propertyName)) {
    return 1;
  }
  
  // Default precision
  return 2;
}