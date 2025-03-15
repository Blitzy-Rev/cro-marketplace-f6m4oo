/**
 * Utility functions for validating data in the frontend application, including
 * form inputs, molecule properties, SMILES strings, and other domain-specific validations.
 * This module provides reusable validation functions that can be used across the application
 * to ensure data integrity and proper user feedback.
 */

import { PropertyType, MoleculeCSVMapping } from '../types/molecule.types';
import { 
  PROPERTY_RANGES, 
  REQUIRED_PROPERTIES, 
  PROPERTY_DEFINITIONS 
} from '../constants/moleculeProperties';
import { validateSmiles } from './moleculeStructure';

// Regular expression patterns for common validations
const EMAIL_REGEX = /^[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}$/;
const UUID_REGEX = /^[0-9a-f]{8}-[0-9a-f]{4}-[1-5][0-9a-f]{3}-[89ab][0-9a-f]{3}-[0-9a-f]{12}$/i;
const URL_REGEX = /^(https?:\/\/)?([a-z\d.-]+)\.([a-z.]{2,6})([/\w .-]*)*\/?$/;

/**
 * Validates that a required field has a value
 * @param value The value to validate
 * @param fieldName The name of the field being validated
 * @returns Validation result with valid flag and error message if invalid
 */
export function validateRequired(value: any, fieldName: string): { valid: boolean, error: string | null } {
  if (value === undefined || value === null || value === '') {
    return { valid: false, error: `${fieldName} is required` };
  }
  return { valid: true, error: null };
}

/**
 * Validates string length constraints
 * @param value The string to validate
 * @param fieldName The name of the field being validated
 * @param minLength Minimum length requirement (optional)
 * @param maxLength Maximum length requirement (optional)
 * @returns Validation result with valid flag and error message if invalid
 */
export function validateStringLength(
  value: string,
  fieldName: string,
  minLength?: number,
  maxLength?: number
): { valid: boolean, error: string | null } {
  if (typeof value !== 'string') {
    return { valid: false, error: `${fieldName} must be a string` };
  }

  if (minLength !== undefined && value.length < minLength) {
    return { valid: false, error: `${fieldName} must be at least ${minLength} characters` };
  }

  if (maxLength !== undefined && value.length > maxLength) {
    return { valid: false, error: `${fieldName} must be at most ${maxLength} characters` };
  }

  return { valid: true, error: null };
}

/**
 * Validates numeric value constraints
 * @param value The number to validate
 * @param fieldName The name of the field being validated
 * @param minValue Minimum value requirement (optional)
 * @param maxValue Maximum value requirement (optional)
 * @returns Validation result with valid flag and error message if invalid
 */
export function validateNumericRange(
  value: number,
  fieldName: string,
  minValue?: number,
  maxValue?: number
): { valid: boolean, error: string | null } {
  if (typeof value !== 'number' || isNaN(value)) {
    return { valid: false, error: `${fieldName} must be a number` };
  }

  if (minValue !== undefined && value < minValue) {
    return { valid: false, error: `${fieldName} must be at least ${minValue}` };
  }

  if (maxValue !== undefined && value > maxValue) {
    return { valid: false, error: `${fieldName} must be at most ${maxValue}` };
  }

  return { valid: true, error: null };
}

/**
 * Validates email address format
 * @param value The email address to validate
 * @param fieldName The name of the field being validated
 * @returns Validation result with valid flag and error message if invalid
 */
export function validateEmail(
  value: string,
  fieldName: string
): { valid: boolean, error: string | null } {
  if (typeof value !== 'string') {
    return { valid: false, error: `${fieldName} must be a string` };
  }

  if (!EMAIL_REGEX.test(value)) {
    return { valid: false, error: `${fieldName} must be a valid email address` };
  }

  return { valid: true, error: null };
}

/**
 * Validates UUID format
 * @param value The UUID to validate
 * @param fieldName The name of the field being validated
 * @returns Validation result with valid flag and error message if invalid
 */
export function validateUUID(
  value: string,
  fieldName: string
): { valid: boolean, error: string | null } {
  if (typeof value !== 'string') {
    return { valid: false, error: `${fieldName} must be a string` };
  }

  if (!UUID_REGEX.test(value)) {
    return { valid: false, error: `${fieldName} must be a valid UUID` };
  }

  return { valid: true, error: null };
}

/**
 * Validates URL format
 * @param value The URL to validate
 * @param fieldName The name of the field being validated
 * @returns Validation result with valid flag and error message if invalid
 */
export function validateURL(
  value: string,
  fieldName: string
): { valid: boolean, error: string | null } {
  if (typeof value !== 'string') {
    return { valid: false, error: `${fieldName} must be a string` };
  }

  if (!URL_REGEX.test(value)) {
    return { valid: false, error: `${fieldName} must be a valid URL` };
  }

  return { valid: true, error: null };
}

/**
 * Validates a SMILES string using the moleculeStructure utility
 * @param value The SMILES string to validate
 * @param fieldName The name of the field being validated
 * @returns Validation result with valid flag and error message if invalid
 */
export function validateSmilesString(
  value: string,
  fieldName: string
): { valid: boolean, error: string | null } {
  if (typeof value !== 'string') {
    return { valid: false, error: `${fieldName} must be a string` };
  }

  if (!validateSmiles(value)) {
    return { valid: false, error: `${fieldName} must be a valid SMILES string` };
  }

  return { valid: true, error: null };
}

/**
 * Validates a molecular property value based on its type and constraints
 * @param value The property value to validate
 * @param propertyName The name of the property
 * @param propertyType The data type of the property
 * @returns Validation result with valid flag and error message if invalid
 */
export function validatePropertyValue(
  value: any,
  propertyName: string,
  propertyType: PropertyType
): { valid: boolean, error: string | null } {
  // Get property constraints from definitions
  const propertyDef = PROPERTY_DEFINITIONS[propertyName];
  const propertyRange = PROPERTY_RANGES[propertyName];
  
  // Handle different property types
  switch (propertyType) {
    case PropertyType.STRING:
      if (typeof value !== 'string') {
        return { valid: false, error: `${propertyName} must be a string` };
      }
      return { valid: true, error: null };
      
    case PropertyType.NUMERIC:
      if (typeof value !== 'number' || isNaN(value)) {
        return { valid: false, error: `${propertyName} must be a number` };
      }
      
      // Check range constraints if defined
      if (propertyRange) {
        if (value < propertyRange.min) {
          return { valid: false, error: `${propertyName} must be at least ${propertyRange.min}` };
        }
        if (value > propertyRange.max) {
          return { valid: false, error: `${propertyName} must be at most ${propertyRange.max}` };
        }
      } else if (propertyDef && propertyDef.min !== undefined && propertyDef.max !== undefined) {
        if (value < propertyDef.min) {
          return { valid: false, error: `${propertyName} must be at least ${propertyDef.min}` };
        }
        if (value > propertyDef.max) {
          return { valid: false, error: `${propertyName} must be at most ${propertyDef.max}` };
        }
      }
      
      return { valid: true, error: null };
      
    case PropertyType.INTEGER:
      if (typeof value !== 'number' || isNaN(value) || !Number.isInteger(value)) {
        return { valid: false, error: `${propertyName} must be an integer` };
      }
      
      // Check range constraints if defined
      if (propertyRange) {
        if (value < propertyRange.min) {
          return { valid: false, error: `${propertyName} must be at least ${propertyRange.min}` };
        }
        if (value > propertyRange.max) {
          return { valid: false, error: `${propertyName} must be at most ${propertyRange.max}` };
        }
      } else if (propertyDef && propertyDef.min !== undefined && propertyDef.max !== undefined) {
        if (value < propertyDef.min) {
          return { valid: false, error: `${propertyName} must be at least ${propertyDef.min}` };
        }
        if (value > propertyDef.max) {
          return { valid: false, error: `${propertyName} must be at most ${propertyDef.max}` };
        }
      }
      
      return { valid: true, error: null };
      
    case PropertyType.BOOLEAN:
      if (typeof value !== 'boolean') {
        return { valid: false, error: `${propertyName} must be a boolean` };
      }
      return { valid: true, error: null };
      
    default:
      return { valid: false, error: `Unknown property type for ${propertyName}` };
  }
}

/**
 * Validates a dictionary of molecular properties
 * @param properties The properties to validate
 * @returns Validation result with valid flag and errors by property
 */
export function validateMoleculeProperties(
  properties: Record<string, any>
): { valid: boolean, errors: Record<string, string> } {
  const errors: Record<string, string> = {};
  let valid = true;
  
  // Check required properties
  for (const required of REQUIRED_PROPERTIES) {
    if (properties[required] === undefined || properties[required] === null) {
      errors[required] = `${required} is required`;
      valid = false;
    }
  }
  
  // Validate each property
  for (const [propertyName, value] of Object.entries(properties)) {
    // Skip already validated required properties that are missing
    if (errors[propertyName]) continue;
    
    // Skip null/undefined optional properties
    if (value === null || value === undefined) continue;
    
    // Get property type from definitions
    const propertyDef = PROPERTY_DEFINITIONS[propertyName];
    if (!propertyDef) {
      // Custom property - skip validation
      continue;
    }
    
    const result = validatePropertyValue(value, propertyName, propertyDef.property_type);
    if (!result.valid && result.error) {
      errors[propertyName] = result.error;
      valid = false;
    }
  }
  
  return { valid, errors };
}

/**
 * Validates CSV column mapping configuration
 * @param mapping The column mapping configuration to validate
 * @returns Validation result with valid flag and error messages
 */
export function validateCSVColumnMapping(
  mapping: MoleculeCSVMapping
): { valid: boolean, errors: string[] } {
  const errors: string[] = [];
  let valid = true;
  
  // Check if mapping is defined and column_mappings is an array
  if (!mapping || !Array.isArray(mapping.column_mappings)) {
    errors.push('Column mappings must be an array');
    return { valid: false, errors };
  }
  
  // Check for required SMILES mapping
  const hasSmiles = mapping.column_mappings.some(
    mapping => mapping.property_name.toLowerCase() === 'smiles'
  );
  
  if (!hasSmiles) {
    errors.push('Column mapping must include a mapping for SMILES');
    valid = false;
  }
  
  // Check for duplicate property mappings
  const mappedProperties = new Set<string>();
  for (const columnMapping of mapping.column_mappings) {
    if (mappedProperties.has(columnMapping.property_name)) {
      errors.push(`Duplicate mapping for property: ${columnMapping.property_name}`);
      valid = false;
    }
    mappedProperties.add(columnMapping.property_name);
    
    // Validate property exists in property definitions
    if (
      columnMapping.property_name.toLowerCase() !== 'smiles' && 
      !PROPERTY_DEFINITIONS[columnMapping.property_name]
    ) {
      errors.push(`Unknown property: ${columnMapping.property_name}`);
      valid = false;
    }
  }
  
  return { valid, errors };
}

/**
 * Validates array length constraints
 * @param value The array to validate
 * @param fieldName The name of the field being validated
 * @param minLength Minimum length requirement (optional)
 * @param maxLength Maximum length requirement (optional)
 * @returns Validation result with valid flag and error message if invalid
 */
export function validateArrayLength(
  value: any[],
  fieldName: string,
  minLength?: number,
  maxLength?: number
): { valid: boolean, error: string | null } {
  if (!Array.isArray(value)) {
    return { valid: false, error: `${fieldName} must be an array` };
  }

  if (minLength !== undefined && value.length < minLength) {
    return { valid: false, error: `${fieldName} must contain at least ${minLength} items` };
  }

  if (maxLength !== undefined && value.length > maxLength) {
    return { valid: false, error: `${fieldName} must contain at most ${maxLength} items` };
  }

  return { valid: true, error: null };
}

/**
 * Generic form field validator that applies appropriate validation based on field type
 * @param value The field value to validate
 * @param fieldName The name of the field being validated
 * @param options Validation options including field type and constraints
 * @returns Validation result with valid flag and error message if invalid
 */
export function validateFormField(
  value: any,
  fieldName: string,
  options: {
    required?: boolean;
    type?: 'string' | 'number' | 'email' | 'uuid' | 'url' | 'smiles' | 'array';
    minLength?: number;
    maxLength?: number;
    minValue?: number;
    maxValue?: number;
  } = {}
): { valid: boolean, error: string | null } {
  // Check if field is required
  if (options.required) {
    const requiredCheck = validateRequired(value, fieldName);
    if (!requiredCheck.valid) {
      return requiredCheck;
    }
  }
  
  // If value is undefined or null and not required, it's valid
  if (value === undefined || value === null) {
    return { valid: true, error: null };
  }
  
  // Apply appropriate validation based on field type
  switch (options.type) {
    case 'string':
      return validateStringLength(value, fieldName, options.minLength, options.maxLength);
    case 'number':
      return validateNumericRange(value, fieldName, options.minValue, options.maxValue);
    case 'email':
      return validateEmail(value, fieldName);
    case 'uuid':
      return validateUUID(value, fieldName);
    case 'url':
      return validateURL(value, fieldName);
    case 'smiles':
      return validateSmilesString(value, fieldName);
    case 'array':
      return validateArrayLength(value, fieldName, options.minLength, options.maxLength);
    default:
      // Default to string validation if type not specified
      return validateStringLength(value, fieldName, options.minLength, options.maxLength);
  }
}