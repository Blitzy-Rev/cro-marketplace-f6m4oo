import {
  validateRequired,
  validateStringLength,
  validateNumericRange,
  validateEmail,
  validateUUID,
  validateURL,
  validateSmilesString,
  validatePropertyValue,
  validateMoleculeProperties,
  validateCSVColumnMapping,
  validateArrayLength,
  validateFormField
} from '../../src/utils/validators';
import { PropertyType } from '../../src/types/molecule.types';
import { validateSmiles } from '../../src/utils/moleculeStructure';

// Mock the validateSmiles function from moleculeStructure
jest.mock('../../src/utils/moleculeStructure', () => ({
  validateSmiles: jest.fn()
}));

describe('validateRequired', () => {
  it('should validate non-empty string values', () => {
    const result = validateRequired('test', 'Field');
    expect(result.valid).toBe(true);
    expect(result.error).toBeNull();
  });

  it('should validate numeric values including zero', () => {
    expect(validateRequired(123, 'Field').valid).toBe(true);
    expect(validateRequired(0, 'Field').valid).toBe(true);
  });

  it('should validate boolean values including false', () => {
    expect(validateRequired(true, 'Field').valid).toBe(true);
    expect(validateRequired(false, 'Field').valid).toBe(true);
  });

  it('should validate object values', () => {
    expect(validateRequired({}, 'Field').valid).toBe(true);
    expect(validateRequired({ key: 'value' }, 'Field').valid).toBe(true);
  });

  it('should validate array values including empty arrays', () => {
    expect(validateRequired([], 'Field').valid).toBe(true);
    expect(validateRequired([1, 2, 3], 'Field').valid).toBe(true);
  });

  it('should invalidate null values', () => {
    const result = validateRequired(null, 'Field');
    expect(result.valid).toBe(false);
    expect(result.error).toBe('Field is required');
  });

  it('should invalidate undefined values', () => {
    const result = validateRequired(undefined, 'Field');
    expect(result.valid).toBe(false);
    expect(result.error).toBe('Field is required');
  });

  it('should invalidate empty string values', () => {
    const result = validateRequired('', 'Field');
    expect(result.valid).toBe(false);
    expect(result.error).toBe('Field is required');
  });
});

describe('validateStringLength', () => {
  it('should validate strings within min and max length constraints', () => {
    const result = validateStringLength('test', 'Field', 2, 10);
    expect(result.valid).toBe(true);
    expect(result.error).toBeNull();
  });

  it('should invalidate strings below minimum length', () => {
    const result = validateStringLength('a', 'Field', 2, 10);
    expect(result.valid).toBe(false);
    expect(result.error).toBe('Field must be at least 2 characters');
  });

  it('should invalidate strings above maximum length', () => {
    const result = validateStringLength('abcdefghijk', 'Field', 2, 10);
    expect(result.valid).toBe(false);
    expect(result.error).toBe('Field must be at most 10 characters');
  });

  it('should validate with only minimum length constraint', () => {
    const result = validateStringLength('test', 'Field', 2);
    expect(result.valid).toBe(true);
    expect(result.error).toBeNull();
  });

  it('should validate with only maximum length constraint', () => {
    const result = validateStringLength('test', 'Field', undefined, 10);
    expect(result.valid).toBe(true);
    expect(result.error).toBeNull();
  });

  it('should validate with no length constraints', () => {
    const result = validateStringLength('any length string', 'Field');
    expect(result.valid).toBe(true);
    expect(result.error).toBeNull();
  });

  it('should invalidate non-string values', () => {
    const result = validateStringLength(123 as any, 'Field', 2, 10);
    expect(result.valid).toBe(false);
    expect(result.error).toBe('Field must be a string');
  });

  it('should invalidate null and undefined values', () => {
    expect(validateStringLength(null as any, 'Field').valid).toBe(false);
    expect(validateStringLength(undefined as any, 'Field').valid).toBe(false);
  });
});

describe('validateNumericRange', () => {
  it('should validate numbers within min and max range constraints', () => {
    const result = validateNumericRange(50, 'Field', 0, 100);
    expect(result.valid).toBe(true);
    expect(result.error).toBeNull();
  });

  it('should invalidate numbers below minimum value', () => {
    const result = validateNumericRange(-10, 'Field', 0, 100);
    expect(result.valid).toBe(false);
    expect(result.error).toBe('Field must be at least 0');
  });

  it('should invalidate numbers above maximum value', () => {
    const result = validateNumericRange(150, 'Field', 0, 100);
    expect(result.valid).toBe(false);
    expect(result.error).toBe('Field must be at most 100');
  });

  it('should validate with only minimum value constraint', () => {
    const result = validateNumericRange(50, 'Field', 0);
    expect(result.valid).toBe(true);
    expect(result.error).toBeNull();
  });

  it('should validate with only maximum value constraint', () => {
    const result = validateNumericRange(50, 'Field', undefined, 100);
    expect(result.valid).toBe(true);
    expect(result.error).toBeNull();
  });

  it('should validate with no range constraints', () => {
    const result = validateNumericRange(1000, 'Field');
    expect(result.valid).toBe(true);
    expect(result.error).toBeNull();
  });

  it('should invalidate non-numeric values', () => {
    const result = validateNumericRange('not a number' as any, 'Field', 0, 100);
    expect(result.valid).toBe(false);
    expect(result.error).toBe('Field must be a number');
  });

  it('should invalidate null and undefined values', () => {
    expect(validateNumericRange(null as any, 'Field').valid).toBe(false);
    expect(validateNumericRange(undefined as any, 'Field').valid).toBe(false);
  });

  it('should invalidate NaN values', () => {
    const result = validateNumericRange(NaN, 'Field', 0, 100);
    expect(result.valid).toBe(false);
    expect(result.error).toBe('Field must be a number');
  });

  it('should validate zero values', () => {
    const result = validateNumericRange(0, 'Field', 0, 100);
    expect(result.valid).toBe(true);
    expect(result.error).toBeNull();
  });

  it('should validate negative values when within range', () => {
    const result = validateNumericRange(-50, 'Field', -100, 0);
    expect(result.valid).toBe(true);
    expect(result.error).toBeNull();
  });
});

describe('validateEmail', () => {
  it('should validate valid email addresses', () => {
    const result = validateEmail('test@example.com', 'Email');
    expect(result.valid).toBe(true);
    expect(result.error).toBeNull();
  });

  it('should validate email addresses with subdomains', () => {
    const result = validateEmail('test@sub.example.com', 'Email');
    expect(result.valid).toBe(true);
    expect(result.error).toBeNull();
  });

  it('should validate email addresses with plus signs', () => {
    const result = validateEmail('test+label@example.com', 'Email');
    expect(result.valid).toBe(true);
    expect(result.error).toBeNull();
  });

  it('should validate email addresses with periods in local part', () => {
    const result = validateEmail('test.name@example.com', 'Email');
    expect(result.valid).toBe(true);
    expect(result.error).toBeNull();
  });

  it('should invalidate email addresses without @ symbol', () => {
    const result = validateEmail('testexample.com', 'Email');
    expect(result.valid).toBe(false);
    expect(result.error).toBe('Email must be a valid email address');
  });

  it('should invalidate email addresses without domain', () => {
    const result = validateEmail('test@', 'Email');
    expect(result.valid).toBe(false);
    expect(result.error).toBe('Email must be a valid email address');
  });

  it('should invalidate email addresses with invalid characters', () => {
    const result = validateEmail('test@exam^ple.com', 'Email');
    expect(result.valid).toBe(false);
    expect(result.error).toBe('Email must be a valid email address');
  });

  it('should invalidate non-string values', () => {
    const result = validateEmail(123 as any, 'Email');
    expect(result.valid).toBe(false);
    expect(result.error).toBe('Email must be a string');
  });

  it('should invalidate null and undefined values', () => {
    expect(validateEmail(null as any, 'Email').valid).toBe(false);
    expect(validateEmail(undefined as any, 'Email').valid).toBe(false);
  });
});

describe('validateUUID', () => {
  it('should validate valid UUID v4 strings', () => {
    const result = validateUUID('123e4567-e89b-12d3-a456-426614174000', 'ID');
    expect(result.valid).toBe(true);
    expect(result.error).toBeNull();
  });

  it('should validate valid UUID strings with different cases', () => {
    const result = validateUUID('123E4567-E89B-12D3-A456-426614174000', 'ID');
    expect(result.valid).toBe(true);
    expect(result.error).toBeNull();
  });

  it('should invalidate UUID strings with wrong format', () => {
    const result = validateUUID('123e4567-e89b-12d3-a456', 'ID');
    expect(result.valid).toBe(false);
    expect(result.error).toBe('ID must be a valid UUID');
  });

  it('should invalidate UUID strings with wrong version', () => {
    const result = validateUUID('123e4567-e89b-62d3-a456-426614174000', 'ID');
    expect(result.valid).toBe(false);
    expect(result.error).toBe('ID must be a valid UUID');
  });

  it('should invalidate UUID strings with wrong variant', () => {
    const result = validateUUID('123e4567-e89b-12d3-1456-426614174000', 'ID');
    expect(result.valid).toBe(false);
    expect(result.error).toBe('ID must be a valid UUID');
  });

  it('should invalidate non-string values', () => {
    const result = validateUUID(123 as any, 'ID');
    expect(result.valid).toBe(false);
    expect(result.error).toBe('ID must be a string');
  });

  it('should invalidate null and undefined values', () => {
    expect(validateUUID(null as any, 'ID').valid).toBe(false);
    expect(validateUUID(undefined as any, 'ID').valid).toBe(false);
  });
});

describe('validateURL', () => {
  it('should validate valid URLs with http protocol', () => {
    const result = validateURL('http://example.com', 'URL');
    expect(result.valid).toBe(true);
    expect(result.error).toBeNull();
  });

  it('should validate valid URLs with https protocol', () => {
    const result = validateURL('https://example.com', 'URL');
    expect(result.valid).toBe(true);
    expect(result.error).toBeNull();
  });

  it('should validate valid URLs without protocol', () => {
    const result = validateURL('example.com', 'URL');
    expect(result.valid).toBe(true);
    expect(result.error).toBeNull();
  });

  it('should validate valid URLs with subdomains', () => {
    const result = validateURL('https://sub.example.com', 'URL');
    expect(result.valid).toBe(true);
    expect(result.error).toBeNull();
  });

  it('should validate valid URLs with paths', () => {
    const result = validateURL('https://example.com/path/to/resource', 'URL');
    expect(result.valid).toBe(true);
    expect(result.error).toBeNull();
  });

  it('should validate valid URLs with query parameters', () => {
    const result = validateURL('https://example.com/search?q=term', 'URL');
    expect(result.valid).toBe(true);
    expect(result.error).toBeNull();
  });

  it('should invalidate URLs without domain', () => {
    const result = validateURL('http://', 'URL');
    expect(result.valid).toBe(false);
    expect(result.error).toBe('URL must be a valid URL');
  });

  it('should invalidate URLs with invalid characters', () => {
    const result = validateURL('http://exam^ple.com', 'URL');
    expect(result.valid).toBe(false);
    expect(result.error).toBe('URL must be a valid URL');
  });

  it('should invalidate non-string values', () => {
    const result = validateURL(123 as any, 'URL');
    expect(result.valid).toBe(false);
    expect(result.error).toBe('URL must be a string');
  });

  it('should invalidate null and undefined values', () => {
    expect(validateURL(null as any, 'URL').valid).toBe(false);
    expect(validateURL(undefined as any, 'URL').valid).toBe(false);
  });
});

describe('validateSmilesString', () => {
  // Mock the validateSmiles function from moleculeStructure
  beforeEach(() => {
    (validateSmiles as jest.Mock).mockReset();
  });

  it('should validate valid SMILES strings', () => {
    (validateSmiles as jest.Mock).mockReturnValue(true);
    
    const result = validateSmilesString('CC(C)CCO', 'SMILES');
    expect(result.valid).toBe(true);
    expect(result.error).toBeNull();
    expect(validateSmiles).toHaveBeenCalledWith('CC(C)CCO');
  });

  it('should invalidate invalid SMILES strings', () => {
    (validateSmiles as jest.Mock).mockReturnValue(false);
    
    const result = validateSmilesString('invalid-smiles', 'SMILES');
    expect(result.valid).toBe(false);
    expect(result.error).toBe('SMILES must be a valid SMILES string');
    expect(validateSmiles).toHaveBeenCalledWith('invalid-smiles');
  });

  it('should invalidate non-string values', () => {
    const result = validateSmilesString(123 as any, 'SMILES');
    expect(result.valid).toBe(false);
    expect(result.error).toBe('SMILES must be a string');
    expect(validateSmiles).not.toHaveBeenCalled();
  });

  it('should invalidate null and undefined values', () => {
    expect(validateSmilesString(null as any, 'SMILES').valid).toBe(false);
    expect(validateSmilesString(undefined as any, 'SMILES').valid).toBe(false);
    expect(validateSmiles).not.toHaveBeenCalled();
  });

  it('should attempt to validate empty string', () => {
    (validateSmiles as jest.Mock).mockReturnValue(false);
    
    const result = validateSmilesString('', 'SMILES');
    expect(result.valid).toBe(false);
    expect(validateSmiles).toHaveBeenCalledWith('');
  });
});

describe('validatePropertyValue', () => {
  it('should validate string properties', () => {
    const result = validatePropertyValue('test', 'formula', PropertyType.STRING);
    expect(result.valid).toBe(true);
    expect(result.error).toBeNull();
  });

  it('should validate numeric properties within range', () => {
    const result = validatePropertyValue(5, 'logp', PropertyType.NUMERIC);
    expect(result.valid).toBe(true);
    expect(result.error).toBeNull();
  });

  it('should invalidate numeric properties outside range', () => {
    const result = validatePropertyValue(15, 'logp', PropertyType.NUMERIC);
    expect(result.valid).toBe(false);
    expect(result.error).toBe('logp must be at most 10');
  });

  it('should invalidate integer properties with decimal values', () => {
    const result = validatePropertyValue(5.5, 'num_rings', PropertyType.INTEGER);
    expect(result.valid).toBe(false);
    expect(result.error).toBe('num_rings must be an integer');
  });

  it('should validate boolean properties', () => {
    const result = validatePropertyValue(true, 'is_active', PropertyType.BOOLEAN);
    expect(result.valid).toBe(true);
    expect(result.error).toBeNull();
  });

  it('should invalidate properties with invalid types', () => {
    const result = validatePropertyValue('not a number', 'logp', PropertyType.NUMERIC);
    expect(result.valid).toBe(false);
    expect(result.error).toBe('logp must be a number');
  });

  it('should invalidate null and undefined values', () => {
    expect(validatePropertyValue(null, 'logp', PropertyType.NUMERIC).valid).toBe(false);
    expect(validatePropertyValue(undefined, 'logp', PropertyType.NUMERIC).valid).toBe(false);
  });

  it('should validate specific properties like molecular_weight, logp', () => {
    expect(validatePropertyValue(150, 'molecular_weight', PropertyType.NUMERIC).valid).toBe(true);
    expect(validatePropertyValue(8, 'logp', PropertyType.NUMERIC).valid).toBe(true);
    expect(validatePropertyValue(0.5, 'solubility', PropertyType.NUMERIC).valid).toBe(true);
  });
});

describe('validateMoleculeProperties', () => {
  it('should validate valid molecule properties', () => {
    const properties = {
      smiles: 'CC(C)CCO',
      inchi_key: 'KFZMGEQAYNKOFK-UHFFFAOYSA-N',
      formula: 'C5H12O',
      molecular_weight: 88.15
    };
    
    const result = validateMoleculeProperties(properties);
    expect(result.valid).toBe(true);
    expect(Object.keys(result.errors)).toHaveLength(0);
  });

  it('should invalidate molecule properties with missing required properties', () => {
    const properties = {
      smiles: 'CC(C)CCO',
      inchi_key: 'KFZMGEQAYNKOFK-UHFFFAOYSA-N'
      // missing formula and molecular_weight
    };
    
    const result = validateMoleculeProperties(properties);
    expect(result.valid).toBe(false);
    expect(result.errors).toHaveProperty('formula');
    expect(result.errors).toHaveProperty('molecular_weight');
  });

  it('should invalidate molecule properties with invalid property values', () => {
    const properties = {
      smiles: 'CC(C)CCO',
      inchi_key: 'KFZMGEQAYNKOFK-UHFFFAOYSA-N',
      formula: 'C5H12O',
      molecular_weight: -10 // Invalid negative weight
    };
    
    const result = validateMoleculeProperties(properties);
    expect(result.valid).toBe(false);
    expect(result.errors).toHaveProperty('molecular_weight');
  });

  it('should validate molecule properties with mixed valid and invalid properties', () => {
    const properties = {
      smiles: 'CC(C)CCO',
      inchi_key: 'KFZMGEQAYNKOFK-UHFFFAOYSA-N',
      formula: 'C5H12O',
      molecular_weight: 88.15,
      logp: 15 // Invalid: outside range
    };
    
    const result = validateMoleculeProperties(properties);
    expect(result.valid).toBe(false);
    expect(result.errors).toHaveProperty('logp');
    expect(result.errors).not.toHaveProperty('molecular_weight');
  });

  it('should invalidate empty properties object', () => {
    const result = validateMoleculeProperties({});
    expect(result.valid).toBe(false);
    expect(Object.keys(result.errors).length).toBeGreaterThan(0);
  });

  it('should invalidate null and undefined values', () => {
    expect(validateMoleculeProperties(null as any).valid).toBe(false);
    expect(validateMoleculeProperties(undefined as any).valid).toBe(false);
  });
});

describe('validateCSVColumnMapping', () => {
  it('should validate valid CSV column mapping with required SMILES mapping', () => {
    const mapping = {
      column_mappings: [
        { csv_column: 'Col1', property_name: 'smiles', is_required: true },
        { csv_column: 'Col2', property_name: 'molecular_weight' },
        { csv_column: 'Col3', property_name: 'logp' }
      ],
      skip_header: true
    };
    
    const result = validateCSVColumnMapping(mapping);
    expect(result.valid).toBe(true);
    expect(result.errors).toHaveLength(0);
  });

  it('should invalidate CSV column mapping without SMILES mapping', () => {
    const mapping = {
      column_mappings: [
        { csv_column: 'Col1', property_name: 'molecular_weight' },
        { csv_column: 'Col2', property_name: 'logp' }
      ],
      skip_header: true
    };
    
    const result = validateCSVColumnMapping(mapping);
    expect(result.valid).toBe(false);
    expect(result.errors).toContain('Column mapping must include a mapping for SMILES');
  });

  it('should invalidate CSV column mapping with duplicate property mappings', () => {
    const mapping = {
      column_mappings: [
        { csv_column: 'Col1', property_name: 'smiles' },
        { csv_column: 'Col2', property_name: 'logp' },
        { csv_column: 'Col3', property_name: 'logp' } // Duplicate
      ],
      skip_header: true
    };
    
    const result = validateCSVColumnMapping(mapping);
    expect(result.valid).toBe(false);
    expect(result.errors).toContain('Duplicate mapping for property: logp');
  });

  it('should invalidate CSV column mapping with non-existent properties', () => {
    const mapping = {
      column_mappings: [
        { csv_column: 'Col1', property_name: 'smiles' },
        { csv_column: 'Col2', property_name: 'nonexistent_property' } // Not in PROPERTY_DEFINITIONS
      ],
      skip_header: true
    };
    
    const result = validateCSVColumnMapping(mapping);
    expect(result.valid).toBe(false);
    expect(result.errors).toContain('Unknown property: nonexistent_property');
  });

  it('should invalidate CSV column mapping with empty mappings array', () => {
    const mapping = {
      column_mappings: [],
      skip_header: true
    };
    
    const result = validateCSVColumnMapping(mapping);
    expect(result.valid).toBe(false);
    expect(result.errors).toContain('Column mapping must include a mapping for SMILES');
  });

  it('should invalidate null and undefined values', () => {
    expect(validateCSVColumnMapping(null as any).valid).toBe(false);
    expect(validateCSVColumnMapping(undefined as any).valid).toBe(false);
  });
});

describe('validateArrayLength', () => {
  it('should validate arrays within min and max length constraints', () => {
    const result = validateArrayLength([1, 2, 3], 'Field', 1, 5);
    expect(result.valid).toBe(true);
    expect(result.error).toBeNull();
  });

  it('should invalidate arrays below minimum length', () => {
    const result = validateArrayLength([1], 'Field', 2, 5);
    expect(result.valid).toBe(false);
    expect(result.error).toBe('Field must contain at least 2 items');
  });

  it('should invalidate arrays above maximum length', () => {
    const result = validateArrayLength([1, 2, 3, 4, 5, 6], 'Field', 1, 5);
    expect(result.valid).toBe(false);
    expect(result.error).toBe('Field must contain at most 5 items');
  });

  it('should validate with only minimum length constraint', () => {
    const result = validateArrayLength([1, 2, 3], 'Field', 2);
    expect(result.valid).toBe(true);
    expect(result.error).toBeNull();
  });

  it('should validate with only maximum length constraint', () => {
    const result = validateArrayLength([1, 2, 3], 'Field', undefined, 5);
    expect(result.valid).toBe(true);
    expect(result.error).toBeNull();
  });

  it('should validate with no length constraints', () => {
    const result = validateArrayLength([1, 2, 3, 4, 5, 6, 7, 8, 9, 10], 'Field');
    expect(result.valid).toBe(true);
    expect(result.error).toBeNull();
  });

  it('should invalidate non-array values', () => {
    const result = validateArrayLength('not an array' as any, 'Field', 1, 5);
    expect(result.valid).toBe(false);
    expect(result.error).toBe('Field must be an array');
  });

  it('should invalidate null and undefined values', () => {
    expect(validateArrayLength(null as any, 'Field').valid).toBe(false);
    expect(validateArrayLength(undefined as any, 'Field').valid).toBe(false);
  });
});

describe('validateFormField', () => {
  it('should validate required fields with various value types', () => {
    expect(validateFormField('test', 'Field', { required: true }).valid).toBe(true);
    expect(validateFormField(123, 'Field', { required: true }).valid).toBe(true);
    expect(validateFormField(true, 'Field', { required: true }).valid).toBe(true);
    expect(validateFormField(false, 'Field', { required: true }).valid).toBe(true);
    expect(validateFormField([], 'Field', { required: true }).valid).toBe(true);
    expect(validateFormField({}, 'Field', { required: true }).valid).toBe(true);
  });

  it('should invalidate required fields with null/undefined values', () => {
    expect(validateFormField(null, 'Field', { required: true }).valid).toBe(false);
    expect(validateFormField(undefined, 'Field', { required: true }).valid).toBe(false);
    expect(validateFormField('', 'Field', { required: true }).valid).toBe(false);
  });

  it('should validate optional fields with null/undefined values', () => {
    expect(validateFormField(null, 'Field', { required: false }).valid).toBe(true);
    expect(validateFormField(undefined, 'Field', { required: false }).valid).toBe(true);
    expect(validateFormField(null, 'Field').valid).toBe(true);
    expect(validateFormField(undefined, 'Field').valid).toBe(true);
  });

  it('should validate string fields with length constraints', () => {
    const options = { type: 'string' as const, minLength: 2, maxLength: 10 };
    expect(validateFormField('test', 'Field', options).valid).toBe(true);
    expect(validateFormField('a', 'Field', options).valid).toBe(false);
    expect(validateFormField('abcdefghijk', 'Field', options).valid).toBe(false);
  });

  it('should validate numeric fields with range constraints', () => {
    const options = { type: 'number' as const, minValue: 0, maxValue: 100 };
    expect(validateFormField(50, 'Field', options).valid).toBe(true);
    expect(validateFormField(-10, 'Field', options).valid).toBe(false);
    expect(validateFormField(150, 'Field', options).valid).toBe(false);
    expect(validateFormField('not a number', 'Field', options).valid).toBe(false);
  });

  it('should validate email fields', () => {
    const options = { type: 'email' as const };
    expect(validateFormField('test@example.com', 'Field', options).valid).toBe(true);
    expect(validateFormField('invalid-email', 'Field', options).valid).toBe(false);
  });

  it('should validate URL fields', () => {
    const options = { type: 'url' as const };
    expect(validateFormField('https://example.com', 'Field', options).valid).toBe(true);
    expect(validateFormField('not a url', 'Field', options).valid).toBe(false);
  });

  it('should validate UUID fields', () => {
    const options = { type: 'uuid' as const };
    expect(validateFormField('123e4567-e89b-12d3-a456-426614174000', 'Field', options).valid).toBe(true);
    expect(validateFormField('not-a-uuid', 'Field', options).valid).toBe(false);
  });

  it('should validate SMILES fields', () => {
    // Mock validateSmiles to return true for valid SMILES
    (validateSmiles as jest.Mock).mockReturnValue(true);
    
    const options = { type: 'smiles' as const };
    expect(validateFormField('CC(C)CCO', 'Field', options).valid).toBe(true);
    
    // Mock validateSmiles to return false for invalid SMILES
    (validateSmiles as jest.Mock).mockReturnValue(false);
    expect(validateFormField('invalid-smiles', 'Field', options).valid).toBe(false);
  });

  it('should validate array fields with length constraints', () => {
    const options = { type: 'array' as const, minLength: 1, maxLength: 5 };
    expect(validateFormField([1, 2, 3], 'Field', options).valid).toBe(true);
    expect(validateFormField([], 'Field', options).valid).toBe(false);
    expect(validateFormField([1, 2, 3, 4, 5, 6], 'Field', options).valid).toBe(false);
    expect(validateFormField('not an array', 'Field', options).valid).toBe(false);
  });

  it('should validate with unsupported field types', () => {
    const options = { type: 'custom' as any, minLength: 2, maxLength: 10 };
    expect(validateFormField('test', 'Field', options).valid).toBe(true);
    expect(validateFormField('a', 'Field', options).valid).toBe(false);
    expect(validateFormField('abcdefghijk', 'Field', options).valid).toBe(false);
  });
});