import { PropertyType } from '../types/molecule.types';
import { PROPERTY_UNITS } from '../constants/moleculeProperties';
import numeral from 'numeral'; // version ^2.0.6

export const DEFAULT_DECIMAL_PRECISION = 2;
const FILE_SIZE_UNITS = ['B', 'KB', 'MB', 'GB', 'TB'];

/**
 * Formats a number with the specified precision and thousands separators
 * @param value - The number value to format
 * @param precision - The number of decimal places to include (default: 2)
 * @returns Formatted number string or empty string if input is invalid
 */
export function formatNumber(value: number | string | null | undefined, precision: number = DEFAULT_DECIMAL_PRECISION): string {
  if (value === null || value === undefined || value === '') {
    return '';
  }
  
  const numValue = typeof value === 'string' ? parseFloat(value) : value;
  
  if (isNaN(numValue)) {
    return '';
  }
  
  return numeral(numValue).format(`0,0.${'0'.repeat(precision)}`);
}

/**
 * Formats a decimal value as a percentage with the specified precision
 * @param value - The decimal or percentage value to format
 * @param precision - The number of decimal places to include (default: 2)
 * @returns Formatted percentage string or empty string if input is invalid
 */
export function formatPercentage(value: number | string | null | undefined, precision: number = DEFAULT_DECIMAL_PRECISION): string {
  if (value === null || value === undefined || value === '') {
    return '';
  }
  
  let numValue = typeof value === 'string' ? parseFloat(value) : value;
  
  if (isNaN(numValue)) {
    return '';
  }
  
  // Assume values <= 1 are already in decimal form (0.XX)
  if (numValue <= 1) {
    numValue = numValue * 100;
  }
  
  return `${formatNumber(numValue, precision)}%`;
}

/**
 * Formats molecular weight with appropriate precision and units
 * @param value - The molecular weight value
 * @returns Formatted molecular weight with units or empty string if input is invalid
 */
export function formatMolecularWeight(value: number | string | null | undefined): string {
  if (value === null || value === undefined || value === '') {
    return '';
  }
  
  return `${formatNumber(value, 2)} g/mol`;
}

/**
 * Formats LogP value with appropriate precision
 * @param value - The LogP value
 * @returns Formatted LogP value or empty string if input is invalid
 */
export function formatLogP(value: number | string | null | undefined): string {
  if (value === null || value === undefined || value === '') {
    return '';
  }
  
  return formatNumber(value, 2);
}

/**
 * Truncates a string to the specified maximum length and adds ellipsis if needed
 * @param str - The input string to truncate
 * @param maxLength - The maximum allowed length
 * @returns Truncated string or original string if shorter than maxLength
 */
export function truncateString(str: string | null | undefined, maxLength: number): string {
  if (str === null || str === undefined || str === '') {
    return '';
  }
  
  if (str.length <= maxLength) {
    return str;
  }
  
  return str.substring(0, maxLength - 3) + '...';
}

/**
 * Formats a file size in bytes to a human-readable format with appropriate units
 * @param bytes - The file size in bytes
 * @returns Formatted file size with units or empty string if input is invalid
 */
export function formatFileSize(bytes: number | string | null | undefined): string {
  if (bytes === null || bytes === undefined || bytes === '' || isNaN(Number(bytes)) || Number(bytes) < 0) {
    return '';
  }
  
  const numBytes = typeof bytes === 'string' ? parseInt(bytes, 10) : bytes;
  
  if (numBytes === 0) {
    return '0 B';
  }
  
  const k = 1024;
  const i = Math.floor(Math.log(numBytes) / Math.log(k));
  
  return `${parseFloat((numBytes / Math.pow(k, i)).toFixed(2))} ${FILE_SIZE_UNITS[i]}`;
}

/**
 * Formats an AI prediction confidence score as a percentage
 * @param value - The confidence score (0-1)
 * @returns Formatted confidence score as percentage or empty string if input is invalid
 */
export function formatConfidenceScore(value: number | string | null | undefined): string {
  if (value === null || value === undefined || value === '') {
    return '';
  }
  
  let numValue = typeof value === 'string' ? parseFloat(value) : value;
  
  if (isNaN(numValue)) {
    return '';
  }
  
  // Ensure value is between 0 and 1
  numValue = Math.max(0, Math.min(1, numValue));
  
  return formatPercentage(numValue, 0);
}

/**
 * Formats a property value based on its type and name, applying appropriate formatting and units
 * @param value - The property value to format
 * @param propertyName - The name of the property
 * @param propertyType - The data type of the property
 * @returns Formatted property value with appropriate formatting and units
 */
export function formatPropertyValue(value: any, propertyName: string, propertyType: PropertyType): string {
  if (value === null || value === undefined) {
    return '';
  }
  
  // Handle boolean values
  if (propertyType === PropertyType.BOOLEAN) {
    return value ? 'Yes' : 'No';
  }
  
  // Handle string values
  if (propertyType === PropertyType.STRING) {
    return String(value);
  }
  
  // Handle integer values
  if (propertyType === PropertyType.INTEGER) {
    return formatNumber(value, 0);
  }
  
  // Handle numeric values with special cases
  if (propertyType === PropertyType.NUMERIC) {
    // Special case for molecular weight
    if (propertyName === 'molecular_weight') {
      return formatMolecularWeight(value);
    }
    
    // Special case for LogP
    if (propertyName === 'logp') {
      return formatLogP(value);
    }
    
    // For other numeric properties, use standard formatting with units if available
    const formattedValue = formatNumber(value);
    const unit = PROPERTY_UNITS[propertyName] || '';
    
    return unit ? `${formattedValue} ${unit}` : formattedValue;
  }
  
  // Default fallback for any other type
  return String(value);
}

/**
 * Converts a property name to a user-friendly display name
 * @param propertyName - The property name to convert
 * @returns User-friendly display name
 */
export function getDisplayName(propertyName: string): string {
  // Replace underscores with spaces
  const spacedName = propertyName.replace(/_/g, ' ');
  
  // Split by spaces and capitalize each word
  const words = spacedName.split(' ');
  const capitalizedWords = words.map(word => 
    word.length > 0 ? word.charAt(0).toUpperCase() + word.slice(1) : word
  );
  
  // Join the words back together
  return capitalizedWords.join(' ');
}