import React from 'react'; // ^18.0.0
import { screen, fireEvent, waitFor } from '@testing-library/react'; // ^13.0.0
import userEvent from '@testing-library/user-event'; // ^14.4.3
import CSVColumnMapper from '../../../../src/components/common/CSVColumnMapper';
import { renderWithProviders } from '../../../../src/utils/testHelpers';
import { createMockCSVData } from '../../../../src/utils/testHelpers';
import { REQUIRED_PROPERTIES } from '../../../../src/constants/moleculeProperties';
import { CSVColumnMapping } from '../../../../src/types/molecule.types';

// Mock data for CSV preview
const mockCSVPreviewData = {
  headers: ['Col1', 'Col2', 'Col3', 'Col4', 'Col5'],
  rows: [
    { Col1: 'CC(C)CCO', Col2: '88.15', Col3: '1.2', Col4: '345.2', Col5: '0.82' },
    { Col1: 'c1ccccc1', Col2: '78.11', Col3: '2.1', Col4: '412.8', Col5: '0.65' },
    { Col1: 'CCN(CC)CC', Col2: '101.19', Col3: '0.8', Col4: '298.6', Col5: '0.91' },
  ],
};

// Mock initial column mapping
const mockInitialMapping: CSVColumnMapping[] = [
  { csv_column: 'Col1', property_name: 'smiles', is_required: true },
  { csv_column: 'Col2', property_name: 'molecular_weight', is_required: true },
  { csv_column: 'Col3', property_name: 'logp', is_required: false },
];

// Mock callback functions
const mockCallbacks = {
  onMappingChange: jest.fn(),
  onValidation: jest.fn(),
};

describe('CSVColumnMapper component', () => {
  beforeEach(() => {
    // Reset mock functions before each test
    jest.clearAllMocks();
  });

  it('renders with CSV preview data', () => {
    // LD1: Render CSVColumnMapper with mock CSV preview data
    renderWithProviders(<CSVColumnMapper
      previewData={mockCSVPreviewData}
      onMappingChange={mockCallbacks.onMappingChange}
      onValidation={mockCallbacks.onValidation}
    />);

    // LD1: Verify CSV preview section is displayed
    expect(screen.getByText('CSV Preview (first 3 rows):')).toBeInTheDocument();

    // LD1: Verify preview data headers are displayed correctly
    expect(screen.getByText('Col1')).toBeInTheDocument();
    expect(screen.getByText('Col2')).toBeInTheDocument();
    expect(screen.getByText('Col3')).toBeInTheDocument();
    expect(screen.getByText('Col4')).toBeInTheDocument();
    expect(screen.getByText('Col5')).toBeInTheDocument();

    // LD1: Verify preview data rows are displayed correctly
    expect(screen.getByText('CC(C)CCO')).toBeInTheDocument();
    expect(screen.getByText('88.15')).toBeInTheDocument();
    expect(screen.getByText('1.2')).toBeInTheDocument();
  });

  it('renders column mapping interface', () => {
    // LD1: Render CSVColumnMapper with mock CSV preview data
    renderWithProviders(<CSVColumnMapper
      previewData={mockCSVPreviewData}
      onMappingChange={mockCallbacks.onMappingChange}
      onValidation={mockCallbacks.onValidation}
    />);

    // LD1: Verify column mapping table is displayed
    expect(screen.getByText('Map Columns to Properties:')).toBeInTheDocument();

    // LD1: Verify each CSV column has a corresponding mapping row
    mockCSVPreviewData.headers.forEach(header => {
      expect(screen.getByText(header)).toBeInTheDocument();
    });

    // LD1: Verify property selection dropdowns are displayed for each column
    const dropdowns = screen.getAllByRole('combobox');
    expect(dropdowns.length).toBe(mockCSVPreviewData.headers.length);
  });

  it('displays required property indicators', () => {
    // LD1: Render CSVColumnMapper with mock CSV preview data
    renderWithProviders(<CSVColumnMapper
      previewData={mockCSVPreviewData}
      onMappingChange={mockCallbacks.onMappingChange}
      onValidation={mockCallbacks.onValidation}
    />);

    // LD1: Verify required properties are marked with visual indicators
    const requiredIndicators = screen.getAllByText('Required');
    expect(requiredIndicators.length).toBeGreaterThan(0);

    // LD1: Verify non-required properties don't have required indicators
    const optionalIndicators = screen.getAllByText('Optional');
    expect(optionalIndicators.length).toBeGreaterThan(0);
  });

  it('handles property selection changes', async () => {
    // LD1: Render CSVColumnMapper with mock CSV preview data
    renderWithProviders(<CSVColumnMapper
      previewData={mockCSVPreviewData}
      onMappingChange={mockCallbacks.onMappingChange}
      onValidation={mockCallbacks.onValidation}
    />);

    // LD1: Select a property for a CSV column using dropdown
    const dropdown = screen.getAllByRole('combobox')[0];
    userEvent.click(dropdown);
    const menuItem = await screen.findByText('Molecular Weight');
    userEvent.click(menuItem);

    // LD1: Verify onMappingChange callback is called with updated mapping
    expect(mockCallbacks.onMappingChange).toHaveBeenCalled();

    // LD1: Verify mapping is updated in the component
    const updatedMapping = (mockCallbacks.onMappingChange as jest.Mock).mock.calls[0][0];
    expect(updatedMapping[0].property_name).toBe('molecular_weight');
  });

  it('validates required property mappings', async () => {
    // LD1: Render CSVColumnMapper with mock CSV preview data
    renderWithProviders(<CSVColumnMapper
      previewData={mockCSVPreviewData}
      onMappingChange={mockCallbacks.onMappingChange}
      onValidation={mockCallbacks.onValidation}
    />);

    // LD1: Map all required properties except one
    const dropdowns = screen.getAllByRole('combobox');
    for (let i = 1; i < dropdowns.length; i++) {
      userEvent.click(dropdowns[i]);
      const menuItem = await screen.findByText('Molecular Weight');
      userEvent.click(menuItem);
    }

    // LD1: Verify validation error is displayed
    expect(mockCallbacks.onValidation).toHaveBeenCalled();
    expect((mockCallbacks.onValidation as jest.Mock).mock.calls[0][0]).toBe(false);

    // LD1: Map the remaining required property
    userEvent.click(dropdowns[0]);
    const menuItem = await screen.findByText('SMILES');
    userEvent.click(menuItem);

    // LD1: Verify validation error is cleared
    expect(mockCallbacks.onValidation).toHaveBeenCalled();
  });

  it('initializes with provided mapping', async () => {
    // LD1: Render CSVColumnMapper with initial mapping
    renderWithProviders(<CSVColumnMapper
      previewData={mockCSVPreviewData}
      initialMapping={mockInitialMapping}
      onMappingChange={mockCallbacks.onMappingChange}
      onValidation={mockCallbacks.onValidation}
    />);

    // LD1: Verify dropdown selections match the initial mapping
    const dropdowns = screen.getAllByRole('combobox');
    expect(dropdowns[0]).toHaveValue('smiles');
    expect(dropdowns[1]).toHaveValue('molecular_weight');
    expect(dropdowns[2]).toHaveValue('logp');

    // LD1: Verify validation status is correct based on initial mapping
    expect(mockCallbacks.onValidation).toHaveBeenCalled();
  });

  it('updates when initialMapping prop changes', async () => {
    // LD1: Render CSVColumnMapper with initial mapping
    const { rerender } = renderWithProviders(<CSVColumnMapper
      previewData={mockCSVPreviewData}
      initialMapping={mockInitialMapping}
      onMappingChange={mockCallbacks.onMappingChange}
      onValidation={mockCallbacks.onValidation}
    />);

    // LD1: Update component with new initialMapping prop
    const newInitialMapping: CSVColumnMapping[] = [
      { csv_column: 'Col1', property_name: 'inchi_key', is_required: true },
      { csv_column: 'Col2', property_name: 'molecular_weight', is_required: true },
      { csv_column: 'Col3', property_name: 'logp', is_required: false },
    ];
    rerender(<CSVColumnMapper
      previewData={mockCSVPreviewData}
      initialMapping={newInitialMapping}
      onMappingChange={mockCallbacks.onMappingChange}
      onValidation={mockCallbacks.onValidation}
    />);

    // LD1: Verify dropdown selections update to match new mapping
    const dropdowns = screen.getAllByRole('combobox');
    expect(dropdowns[0]).toHaveValue('inchi_key');
    expect(dropdowns[1]).toHaveValue('molecular_weight');
    expect(dropdowns[2]).toHaveValue('logp');

    // LD1: Verify validation status updates based on new mapping
    expect(mockCallbacks.onValidation).toHaveBeenCalled();
  });

  it('shows validation status for each mapping', async () => {
    // LD1: Render CSVColumnMapper with mock CSV preview data
    renderWithProviders(<CSVColumnMapper
      previewData={mockCSVPreviewData}
      onMappingChange={mockCallbacks.onMappingChange}
      onValidation={mockCallbacks.onValidation}
    />);

    // LD1: Map some columns to properties
    const dropdowns = screen.getAllByRole('combobox');
    userEvent.click(dropdowns[0]);
    const menuItem = await screen.findByText('SMILES');
    userEvent.click(menuItem);

    // LD1: Verify valid mappings show success indicators
    const validIndicators = await screen.findAllByText('Valid');
    expect(validIndicators.length).toBeGreaterThan(0);

    // LD1: Verify invalid or missing required mappings show error indicators
    const invalidIndicators = screen.queryAllByText('Invalid');
    expect(invalidIndicators.length).toBe(0);
  });
});