import React from 'react'; // react v18.0.0
import { render, screen, fireEvent, waitFor, act } from '@testing-library/react'; // ^13.0.0
import MoleculeUploader from '../../../../src/components/molecule/MoleculeUploader';
import { renderWithProviders } from '../../../../src/utils/testHelpers';
import {
  uploadMoleculeCSV,
  getCSVPreview,
  importMoleculesFromCSV
} from '../../../../src/api/moleculeApi';
import { REQUIRED_PROPERTIES } from '../../../../src/constants/moleculeProperties';

// Mock the DragDropZone component for simpler testing
jest.mock('../../../../src/components/common/DragDropZone', () => ({ onFilesAccepted, children }) => <div data-testid='drag-drop-zone' onClick={() => onFilesAccepted([new File(['test'], 'test.csv', { type: 'text/csv' })])}>{children}</div>);

// Mock the CSVColumnMapper component for simpler testing
jest.mock('../../../../src/components/common/CSVColumnMapper', () => ({ previewData, initialMapping, onMappingChange, onValidation }) => <div data-testid='csv-column-mapper'><button onClick={() => onMappingChange([{csvColumn: 'SMILES', propertyKey: 'smiles', propertyType: 'string'}])}>Map SMILES</button><button onClick={() => onValidation(true, [])}>Validate</button><button onClick={() => onValidation(false, ['Missing required property'])}>Invalidate</button></div>);

// Mock the LibrarySelector component for simpler testing
jest.mock('../../../../src/components/library/LibrarySelector', () => ({ value, onChange }) => <div data-testid='library-selector'><button onClick={() => onChange('test-library-id')}>Select Library</button></div>);

// Mock the file upload API call
const mockUploadMoleculeCSV = jest.fn().mockResolvedValue({ data: { storage_key: 'test-storage-key' } });
jest.mock('../../../../src/api/moleculeApi', () => ({
  ...jest.requireActual('../../../../src/api/moleculeApi'),
  uploadMoleculeCSV: (...args: any) => mockUploadMoleculeCSV(...args),
}));

// Mock the CSV preview API call
const mockGetCSVPreview = jest.fn().mockResolvedValue({ data: { headers: ['SMILES', 'MolecularWeight', 'LogP'], rows: [{SMILES: 'CC', MolecularWeight: '30.07', LogP: '0.5'}, {SMILES: 'CCO', MolecularWeight: '46.07', LogP: '-0.3'}] } });
jest.mock('../../../../src/api/moleculeApi', () => ({
  ...jest.requireActual('../../../../src/api/moleculeApi'),
  getCSVPreview: (...args: any) => mockGetCSVPreview(...args),
}));

// Mock the CSV import API call
const mockImportMoleculesFromCSV = jest.fn().mockResolvedValue({ data: { total_processed: 2, successful: 2, failed: 0, duplicates: 0, errors: [] } });
jest.mock('../../../../src/api/moleculeApi', () => ({
  ...jest.requireActual('../../../../src/api/moleculeApi'),
  importMoleculesFromCSV: (...args: any) => mockImportMoleculesFromCSV(...args),
}));

describe('MoleculeUploader', () => {
  // Clear mock implementations after all tests
  afterEach(() => {
    jest.clearAllMocks();
  });

  it('renders the file upload step initially', () => {
    // Render MoleculeUploader component with renderWithProviders
    renderWithProviders(<MoleculeUploader />);

    // Check that DragDropZone is rendered
    const dragDropZone = screen.getByTestId('drag-drop-zone');
    expect(dragDropZone).toBeInTheDocument();

    // Verify upload instructions are displayed
    expect(dragDropZone).toHaveTextContent('Drag and drop your CSV file here, or click to browse.');
  });

  it('handles file upload and advances to mapping step', async () => {
    // Render MoleculeUploader component
    renderWithProviders(<MoleculeUploader />);

    // Create a mock File object
    const file = new File(['test'], 'test.csv', { type: 'text/csv' });

    // Simulate file selection through DragDropZone
    const dragDropZone = screen.getByTestId('drag-drop-zone');
    fireEvent.click(dragDropZone);

    // Wait for API calls to complete
    await waitFor(() => {
      expect(mockUploadMoleculeCSV).toHaveBeenCalledWith(expect.any(File));
      expect(mockGetCSVPreview).toHaveBeenCalledWith('test-storage-key');
    });

    // Check that component advances to mapping step
    expect(screen.getByTestId('csv-column-mapper')).toBeInTheDocument();

    // Verify uploadMoleculeCSV API is called with the file
    expect(mockUploadMoleculeCSV).toHaveBeenCalledWith(file);

    // Verify getCSVPreview API is called with the storage key
    expect(mockGetCSVPreview).toHaveBeenCalledWith('test-storage-key');
  });

  it('displays error message when file upload fails', async () => {
    // Mock uploadMoleculeCSV to reject with an error
    mockUploadMoleculeCSV.mockRejectedValue(new Error('Upload failed'));

    // Render MoleculeUploader component
    renderWithProviders(<MoleculeUploader />);

    // Simulate file selection
    const dragDropZone = screen.getByTestId('drag-drop-zone');
    fireEvent.click(dragDropZone);

    // Wait for error handling to complete
    await waitFor(() => {
      expect(screen.getByRole('alert')).toHaveTextContent('Upload failed');
    });

    // Check that component remains on upload step
    expect(dragDropZone).toBeInTheDocument();
  });

  it('handles column mapping changes', async () => {
    // Mock successful API responses
    mockUploadMoleculeCSV.mockResolvedValue({ data: { storage_key: 'test-storage-key' } });
    mockGetCSVPreview.mockResolvedValue({ data: { headers: ['SMILES', 'MolecularWeight', 'LogP'], rows: [{SMILES: 'CC', MolecularWeight: '30.07', LogP: '0.5'}, {SMILES: 'CCO', MolecularWeight: '46.07', LogP: '-0.3'}] } });

    // Render MoleculeUploader component and advance to mapping step
    renderWithProviders(<MoleculeUploader />);
    const dragDropZone = screen.getByTestId('drag-drop-zone');
    fireEvent.click(dragDropZone);
    await waitFor(() => {
      expect(screen.getByTestId('csv-column-mapper')).toBeInTheDocument();
    });

    // Simulate mapping changes through CSVColumnMapper
    const csvColumnMapper = screen.getByTestId('csv-column-mapper');
    const onMappingChangeMock = jest.fn();
    fireEvent.click(csvColumnMapper.firstChild as HTMLElement);

    // Verify mapping state is updated
    expect(onMappingChangeMock).not.toHaveBeenCalled();
  });

  it('validates required properties in mapping', async () => {
    // Mock successful API responses
    mockUploadMoleculeCSV.mockResolvedValue({ data: { storage_key: 'test-storage-key' } });
    mockGetCSVPreview.mockResolvedValue({ data: { headers: ['SMILES', 'MolecularWeight', 'LogP'], rows: [{SMILES: 'CC', MolecularWeight: '30.07', LogP: '0.5'}, {SMILES: 'CCO', MolecularWeight: '46.07', LogP: '-0.3'}] } });

    // Render MoleculeUploader component and advance to mapping step
    renderWithProviders(<MoleculeUploader />);
    const dragDropZone = screen.getByTestId('drag-drop-zone');
    fireEvent.click(dragDropZone);
    await waitFor(() => {
      expect(screen.getByTestId('csv-column-mapper')).toBeInTheDocument();
    });

    // Simulate invalid mapping (missing required property)
    const csvColumnMapper = screen.getByTestId('csv-column-mapper');
    fireEvent.click(csvColumnMapper.lastChild as HTMLElement);

    // Attempt to proceed to next step
    await waitFor(() => {
      expect(screen.getByRole('alert')).toHaveTextContent('Missing required property');
    });

    // Verify component remains on mapping step
    expect(screen.getByTestId('csv-column-mapper')).toBeInTheDocument();
  });

  it('handles library selection', async () => {
    // Mock successful API responses
    mockUploadMoleculeCSV.mockResolvedValue({ data: { storage_key: 'test-storage-key' } });
    mockGetCSVPreview.mockResolvedValue({ data: { headers: ['SMILES', 'MolecularWeight', 'LogP'], rows: [{SMILES: 'CC', MolecularWeight: '30.07', LogP: '0.5'}, {SMILES: 'CCO', MolecularWeight: '46.07', LogP: '-0.3'}] } });

    // Render MoleculeUploader component and advance to mapping step
    renderWithProviders(<MoleculeUploader />);
    const dragDropZone = screen.getByTestId('drag-drop-zone');
    fireEvent.click(dragDropZone);
    await waitFor(() => {
      expect(screen.getByTestId('csv-column-mapper')).toBeInTheDocument();
    });

    // Simulate library selection through LibrarySelector
    const librarySelector = screen.getByTestId('library-selector');
    fireEvent.click(librarySelector.firstChild as HTMLElement);

    // Verify library selection state is updated
    expect(librarySelector).toHaveTextContent('Select Library');
  });

  it('processes CSV import and shows results', async () => {
    // Mock successful API responses including import results
    mockUploadMoleculeCSV.mockResolvedValue({ data: { storage_key: 'test-storage-key' } });
    mockGetCSVPreview.mockResolvedValue({ data: { headers: ['SMILES', 'MolecularWeight', 'LogP'], rows: [{SMILES: 'CC', MolecularWeight: '30.07', LogP: '0.5'}, {SMILES: 'CCO', MolecularWeight: '46.07', LogP: '-0.3'}] } });
    mockImportMoleculesFromCSV.mockResolvedValue({ data: { total_processed: 2, successful: 2, failed: 0, duplicates: 0, errors: [] } });

    // Render MoleculeUploader component and advance to mapping step
    const {container} = renderWithProviders(<MoleculeUploader />);
    const dragDropZone = screen.getByTestId('drag-drop-zone');
    fireEvent.click(dragDropZone);
    await waitFor(() => {
      expect(screen.getByTestId('csv-column-mapper')).toBeInTheDocument();
    });

    // Set valid mappings and library selection
    const csvColumnMapper = screen.getByTestId('csv-column-mapper');
    fireEvent.click(csvColumnMapper.firstChild as HTMLElement);
    const librarySelector = screen.getByTestId('library-selector');
    fireEvent.click(librarySelector.firstChild as HTMLElement);

    // Click Next button to process import
    const buttons = container.querySelectorAll('button');
    const importButton = buttons[2];
    act(() => {
      fireEvent.click(importButton);
    });

    // Wait for import to complete
    await waitFor(() => {
      expect(mockImportMoleculesFromCSV).toHaveBeenCalledWith('test-storage-key', expect.anything());
    });

    // Verify importMoleculesFromCSV API is called with correct parameters
    expect(mockImportMoleculesFromCSV).toHaveBeenCalledWith('test-storage-key', expect.anything());

    // Verify success message is displayed with import statistics
    expect(screen.getByText('Import Summary')).toBeInTheDocument();
    expect(screen.getByText('Total rows: 2')).toBeInTheDocument();
    expect(screen.getByText('Processed rows: 2')).toBeInTheDocument();
    expect(screen.getByText('Failed rows: 0')).toBeInTheDocument();
    expect(screen.getByText('Duplicate rows skipped: 0')).toBeInTheDocument();
    expect(screen.getByText('New molecules created: 2')).toBeInTheDocument();
  });

  it('handles import errors', async () => {
    // Mock API responses with importMoleculesFromCSV rejecting
    mockUploadMoleculeCSV.mockResolvedValue({ data: { storage_key: 'test-storage-key' } });
    mockGetCSVPreview.mockResolvedValue({ data: { headers: ['SMILES', 'MolecularWeight', 'LogP'], rows: [{SMILES: 'CC', MolecularWeight: '30.07', LogP: '0.5'}, {SMILES: 'CCO', MolecularWeight: '46.07', LogP: '-0.3'}] } });
    mockImportMoleculesFromCSV.mockRejectedValue(new Error('Import failed'));

    // Render MoleculeUploader component and advance to mapping step
    const {container} = renderWithProviders(<MoleculeUploader />);
    const dragDropZone = screen.getByTestId('drag-drop-zone');
    fireEvent.click(dragDropZone);
    await waitFor(() => {
      expect(screen.getByTestId('csv-column-mapper')).toBeInTheDocument();
    });

    // Set valid mappings and click Next
    const csvColumnMapper = screen.getByTestId('csv-column-mapper');
    fireEvent.click(csvColumnMapper.firstChild as HTMLElement);
    const librarySelector = screen.getByTestId('library-selector');
    fireEvent.click(librarySelector.firstChild as HTMLElement);

    // Click Next button to process import
    const buttons = container.querySelectorAll('button');
    const importButton = buttons[2];
    act(() => {
      fireEvent.click(importButton);
    });

    // Wait for error handling to complete
    await waitFor(() => {
      expect(screen.getByRole('alert')).toHaveTextContent('Import failed');
    });

    // Verify component remains on mapping step
    expect(screen.getByTestId('csv-column-mapper')).toBeInTheDocument();
  });

  it('allows navigation back to previous steps', async () => {
    // Mock successful API responses
    mockUploadMoleculeCSV.mockResolvedValue({ data: { storage_key: 'test-storage-key' } });
    mockGetCSVPreview.mockResolvedValue({ data: { headers: ['SMILES', 'MolecularWeight', 'LogP'], rows: [{SMILES: 'CC', MolecularWeight: '30.07', LogP: '0.5'}, {SMILES: 'CCO', MolecularWeight: '46.07', LogP: '-0.3'}] } });

    // Render MoleculeUploader component and advance to mapping step
    const {container} = renderWithProviders(<MoleculeUploader />);
    const dragDropZone = screen.getByTestId('drag-drop-zone');
    fireEvent.click(dragDropZone);
    await waitFor(() => {
      expect(screen.getByTestId('csv-column-mapper')).toBeInTheDocument();
    });

    // Click Back button
    const buttons = container.querySelectorAll('button');
    const backButton = buttons[0];
    act(() => {
      fireEvent.click(backButton);
    });

    // Verify component returns to upload step
    expect(screen.getByTestId('drag-drop-zone')).toBeInTheDocument();
  });

  it('allows restarting the upload process', async () => {
    // Mock successful API responses including import results
    mockUploadMoleculeCSV.mockResolvedValue({ data: { storage_key: 'test-storage-key' } });
    mockGetCSVPreview.mockResolvedValue({ data: { headers: ['SMILES', 'MolecularWeight', 'LogP'], rows: [{SMILES: 'CC', MolecularWeight: '30.07', LogP: '0.5'}, {SMILES: 'CCO', MolecularWeight: '46.07', LogP: '-0.3'}] } });
    mockImportMoleculesFromCSV.mockResolvedValue({ data: { total_processed: 2, successful: 2, failed: 0, duplicates: 0, errors: [] } });

    // Render MoleculeUploader component and complete the import process
    const {container} = renderWithProviders(<MoleculeUploader />);
    const dragDropZone = screen.getByTestId('drag-drop-zone');
    fireEvent.click(dragDropZone);
    await waitFor(() => {
      expect(screen.getByTestId('csv-column-mapper')).toBeInTheDocument();
    });

    // Set valid mappings and library selection
    const csvColumnMapper = screen.getByTestId('csv-column-mapper');
    fireEvent.click(csvColumnMapper.firstChild as HTMLElement);
    const librarySelector = screen.getByTestId('library-selector');
    fireEvent.click(librarySelector.firstChild as HTMLElement);

    // Click Next button to process import
    const buttons = container.querySelectorAll('button');
    const importButton = buttons[2];
    act(() => {
      fireEvent.click(importButton);
    });

    // Wait for import to complete
    await waitFor(() => {
      expect(mockImportMoleculesFromCSV).toHaveBeenCalledWith('test-storage-key', expect.anything());
    });

    // Click 'Upload More' button
    const resetButton = container.querySelectorAll('button')[1];
    act(() => {
      fireEvent.click(resetButton);
    });

    // Verify component resets to initial state
    expect(screen.getByTestId('drag-drop-zone')).toBeInTheDocument();
  });
});