import {
  formatNumber,
  formatPercentage,
  formatMolecularWeight,
  formatLogP,
  truncateString,
  formatFileSize,
  formatConfidenceScore,
  formatPropertyValue,
  getDisplayName
} from '../../src/utils/formatters';
import { PropertyType } from '../../src/types/molecule.types';

describe('formatNumber', () => {
  it('should format numbers with default precision (2 decimal places)', () => {
    expect(formatNumber(1234.5678)).toBe('1,234.57');
    expect(formatNumber(0.123456)).toBe('0.12');
    expect(formatNumber(1000000)).toBe('1,000,000.00');
  });

  it('should format numbers with custom precision', () => {
    expect(formatNumber(1234.5678, 3)).toBe('1,234.568');
    expect(formatNumber(0.123456, 4)).toBe('0.1235');
    expect(formatNumber(1000000, 0)).toBe('1,000,000');
  });

  it('should handle string inputs by converting them to numbers', () => {
    expect(formatNumber('1234.5678')).toBe('1,234.57');
    expect(formatNumber('0.123456')).toBe('0.12');
  });

  it('should return empty string for null or undefined values', () => {
    expect(formatNumber(null)).toBe('');
    expect(formatNumber(undefined)).toBe('');
    expect(formatNumber('')).toBe('');
  });

  it('should return empty string for invalid number strings', () => {
    expect(formatNumber('abc')).toBe('');
    expect(formatNumber('123abc')).toBe('');
  });

  it('should handle zero correctly', () => {
    expect(formatNumber(0)).toBe('0.00');
    expect(formatNumber('0')).toBe('0.00');
    expect(formatNumber(0, 3)).toBe('0.000');
  });

  it('should handle negative numbers', () => {
    expect(formatNumber(-1234.5678)).toBe('-1,234.57');
    expect(formatNumber('-1234.5678')).toBe('-1,234.57');
  });
});

describe('formatPercentage', () => {
  it('should format decimal values (0-1) as percentages', () => {
    expect(formatPercentage(0.1234)).toBe('12.34%');
    expect(formatPercentage(0.5)).toBe('50.00%');
    expect(formatPercentage(1)).toBe('100.00%');
  });

  it('should format percentage values (0-100) as percentages', () => {
    expect(formatPercentage(12.34)).toBe('12.34%');
    expect(formatPercentage(50)).toBe('50.00%');
    expect(formatPercentage(100)).toBe('100.00%');
  });

  it('should format with different precision levels', () => {
    expect(formatPercentage(0.12345, 3)).toBe('12.345%');
    expect(formatPercentage(12.345, 1)).toBe('12.3%');
    expect(formatPercentage(50, 0)).toBe('50%');
  });

  it('should handle string inputs by converting them to numbers', () => {
    expect(formatPercentage('0.5')).toBe('50.00%');
    expect(formatPercentage('50')).toBe('50.00%');
  });

  it('should return empty string for null or undefined values', () => {
    expect(formatPercentage(null)).toBe('');
    expect(formatPercentage(undefined)).toBe('');
    expect(formatPercentage('')).toBe('');
  });

  it('should return empty string for invalid percentage strings', () => {
    expect(formatPercentage('abc')).toBe('');
    expect(formatPercentage('50%')).toBe(''); // The % symbol makes it invalid
  });

  it('should handle zero values', () => {
    expect(formatPercentage(0)).toBe('0.00%');
    expect(formatPercentage('0')).toBe('0.00%');
  });

  it('should handle negative values', () => {
    expect(formatPercentage(-0.5)).toBe('-50.00%');
    expect(formatPercentage(-50)).toBe('-50.00%');
  });
});

describe('formatMolecularWeight', () => {
  it('should format valid molecular weights with units', () => {
    expect(formatMolecularWeight(123.456)).toBe('123.46 g/mol');
    expect(formatMolecularWeight(78.9)).toBe('78.90 g/mol');
  });

  it('should handle null and undefined values', () => {
    expect(formatMolecularWeight(null)).toBe('');
    expect(formatMolecularWeight(undefined)).toBe('');
    expect(formatMolecularWeight('')).toBe('');
  });

  it('should handle invalid molecular weight strings', () => {
    expect(formatMolecularWeight('abc')).toBe('');
  });

  it('should handle zero values', () => {
    expect(formatMolecularWeight(0)).toBe('0.00 g/mol');
    expect(formatMolecularWeight('0')).toBe('0.00 g/mol');
  });
});

describe('formatLogP', () => {
  it('should format valid LogP values', () => {
    expect(formatLogP(1.23)).toBe('1.23');
    expect(formatLogP(4.5678)).toBe('4.57');
  });

  it('should handle null and undefined values', () => {
    expect(formatLogP(null)).toBe('');
    expect(formatLogP(undefined)).toBe('');
    expect(formatLogP('')).toBe('');
  });

  it('should handle invalid LogP strings', () => {
    expect(formatLogP('abc')).toBe('');
  });

  it('should handle zero values', () => {
    expect(formatLogP(0)).toBe('0.00');
    expect(formatLogP('0')).toBe('0.00');
  });

  it('should handle negative values', () => {
    expect(formatLogP(-2.5)).toBe('-2.50');
    expect(formatLogP('-2.5')).toBe('-2.50');
  });
});

describe('truncateString', () => {
  it('should truncate strings longer than maxLength', () => {
    expect(truncateString('This is a long string', 10)).toBe('This is...');
    expect(truncateString('Short string', 5)).toBe('Sh...');
  });

  it('should handle strings shorter than maxLength', () => {
    expect(truncateString('Short', 10)).toBe('Short');
    expect(truncateString('Five', 5)).toBe('Five');
  });

  it('should handle strings equal to maxLength', () => {
    expect(truncateString('Exact', 5)).toBe('Exact');
  });

  it('should handle null and undefined values', () => {
    expect(truncateString(null, 10)).toBe('');
    expect(truncateString(undefined, 10)).toBe('');
    expect(truncateString('', 10)).toBe('');
  });

  it('should handle empty strings', () => {
    expect(truncateString('', 5)).toBe('');
  });

  it('should handle very short maxLength values', () => {
    expect(truncateString('Hello', 3)).toBe('...');
    expect(truncateString('Hello', 0)).toBe('...');
  });
});

describe('formatFileSize', () => {
  it('should format bytes', () => {
    expect(formatFileSize(512)).toBe('512 B');
    expect(formatFileSize(1023)).toBe('1023 B');
  });

  it('should format kilobytes', () => {
    expect(formatFileSize(1024)).toBe('1 KB');
    expect(formatFileSize(1536)).toBe('1.5 KB');
    expect(formatFileSize(10240)).toBe('10 KB');
  });

  it('should format megabytes', () => {
    expect(formatFileSize(1048576)).toBe('1 MB');
    expect(formatFileSize(2097152)).toBe('2 MB');
    expect(formatFileSize(5242880)).toBe('5 MB');
  });

  it('should format gigabytes', () => {
    expect(formatFileSize(1073741824)).toBe('1 GB');
    expect(formatFileSize(5368709120)).toBe('5 GB');
  });

  it('should format terabytes', () => {
    expect(formatFileSize(1099511627776)).toBe('1 TB');
    expect(formatFileSize(2199023255552)).toBe('2 TB');
  });

  it('should handle null and undefined values', () => {
    expect(formatFileSize(null)).toBe('');
    expect(formatFileSize(undefined)).toBe('');
    expect(formatFileSize('')).toBe('');
  });

  it('should handle invalid file size strings', () => {
    expect(formatFileSize('abc')).toBe('');
    expect(formatFileSize('1MB')).toBe('');
  });

  it('should handle zero values', () => {
    expect(formatFileSize(0)).toBe('0 B');
    expect(formatFileSize('0')).toBe('0 B');
  });

  it('should handle negative values', () => {
    expect(formatFileSize(-1024)).toBe('');
    expect(formatFileSize('-1024')).toBe('');
  });
});

describe('formatConfidenceScore', () => {
  it('should format decimal confidence scores (0-1)', () => {
    expect(formatConfidenceScore(0.75)).toBe('75%');
    expect(formatConfidenceScore(0.123)).toBe('12%');
    expect(formatConfidenceScore(1)).toBe('100%');
    expect(formatConfidenceScore(0)).toBe('0%');
  });

  it('should handle values outside the 0-1 range (should clamp)', () => {
    expect(formatConfidenceScore(1.5)).toBe('100%');
    expect(formatConfidenceScore(-0.5)).toBe('0%');
    expect(formatConfidenceScore(2)).toBe('100%');
  });

  it('should handle null and undefined values', () => {
    expect(formatConfidenceScore(null)).toBe('');
    expect(formatConfidenceScore(undefined)).toBe('');
    expect(formatConfidenceScore('')).toBe('');
  });

  it('should handle invalid confidence score strings', () => {
    expect(formatConfidenceScore('abc')).toBe('');
    expect(formatConfidenceScore('75%')).toBe('');
  });
});

describe('formatPropertyValue', () => {
  it('should format string properties', () => {
    expect(formatPropertyValue('CC(C)CCO', 'smiles', PropertyType.STRING)).toBe('CC(C)CCO');
    expect(formatPropertyValue('Test value', 'notes', PropertyType.STRING)).toBe('Test value');
  });

  it('should format numeric properties', () => {
    expect(formatPropertyValue(123.456, 'custom_property', PropertyType.NUMERIC)).toBe('123.46');
    expect(formatPropertyValue(0.789, 'solubility', PropertyType.NUMERIC)).toBe('0.79 mg/mL');
  });

  it('should format integer properties', () => {
    expect(formatPropertyValue(123.456, 'atom_count', PropertyType.INTEGER)).toBe('123');
    expect(formatPropertyValue(123, 'atom_count', PropertyType.INTEGER)).toBe('123');
  });

  it('should format boolean properties', () => {
    expect(formatPropertyValue(true, 'is_active', PropertyType.BOOLEAN)).toBe('Yes');
    expect(formatPropertyValue(false, 'is_active', PropertyType.BOOLEAN)).toBe('No');
  });

  it('should format molecular_weight property', () => {
    expect(formatPropertyValue(123.456, 'molecular_weight', PropertyType.NUMERIC)).toBe('123.46 g/mol');
  });

  it('should format logp property', () => {
    expect(formatPropertyValue(2.345, 'logp', PropertyType.NUMERIC)).toBe('2.35');
  });

  it('should handle null and undefined values', () => {
    expect(formatPropertyValue(null, 'any_property', PropertyType.STRING)).toBe('');
    expect(formatPropertyValue(undefined, 'any_property', PropertyType.NUMERIC)).toBe('');
  });

  it('should handle properties with units', () => {
    expect(formatPropertyValue(5.67, 'ic50', PropertyType.NUMERIC)).toBe('5.67 nM');
    expect(formatPropertyValue(42, 'half_life', PropertyType.NUMERIC)).toBe('42.00 h');
  });
});

describe('getDisplayName', () => {
  it('should convert snake_case property names to display names', () => {
    expect(getDisplayName('molecular_weight')).toBe('Molecular Weight');
    expect(getDisplayName('binding_affinity')).toBe('Binding Affinity');
  });

  it('should handle single word property names', () => {
    expect(getDisplayName('logp')).toBe('Logp');
    expect(getDisplayName('smiles')).toBe('Smiles');
  });

  it('should handle property names with multiple underscores', () => {
    expect(getDisplayName('number_of_rotatable_bonds')).toBe('Number Of Rotatable Bonds');
    expect(getDisplayName('volume_of_distribution')).toBe('Volume Of Distribution');
  });

  it('should handle property names with mixed case', () => {
    expect(getDisplayName('LogP')).toBe('LogP');
    expect(getDisplayName('molecular_Weight')).toBe('Molecular Weight');
    expect(getDisplayName('pKa_value')).toBe('PKa Value');
  });
});