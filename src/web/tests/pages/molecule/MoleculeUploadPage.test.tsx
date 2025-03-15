import React from 'react'; // react v18.0.0
import { screen, fireEvent, waitFor, act } from '@testing-library/react'; // @testing-library/react v13.0.0
import { renderWithProviders, createMockCSVData } from '../../../../src/utils/testHelpers';
import MoleculeUploadPage from '../../../../src/pages/molecule/MoleculeUploadPage';
import { ROUTES } from '../../../../src/constants/routes';
import { axeTest } from '../../../../src/utils/testHelpers';

// Mock the useNavigate hook
import { useNavigate } from 'react-router-dom'; // react-router-dom v6.0.0
jest.mock('react-router-dom', () => ({
  ...jest.requireActual('react-router-dom'),
  useNavigate: jest.fn(),
}));

// Mock the MoleculeUploader component
jest.mock('../../../../src/components/molecule/MoleculeUploader', () => {
  return {
    __esModule: true,
    default: jest.fn(({ onUploadComplete }) => (
      <div data-testid="molecule-uploader">
        MoleculeUploader
        <button onClick={() => onUploadComplete({
          total_rows: 10,
          processed_rows: 8,
          failed_rows: 2,
          duplicate_rows: 1,
          created_molecules: 7,
          status: 'completed'
        })}>Complete Upload</button>
      </div>
    )),
  };
});

describe('MoleculeUploadPage', () => {
  const mockNavigate = jest.fn();

  beforeEach(() => {
    (useNavigate as jest.Mock).mockReturnValue(mockNavigate);
  });

  afterEach(() => {
    jest.clearAllMocks();
  });

  it('renders the upload page correctly', () => {
    renderWithProviders(<MoleculeUploadPage />);
    expect(screen.getByText('Upload Molecules')).toBeInTheDocument();
    expect(screen.getByText('Upload a CSV file containing molecular data to add molecules to the system.')).toBeInTheDocument();
    expect(screen.getByText('MoleculeUploader')).toBeInTheDocument();
  });

  it('displays breadcrumbs navigation', () => {
    renderWithProviders(<MoleculeUploadPage />);
    expect(screen.getByText('Dashboard')).toBeInTheDocument();
    expect(screen.getByText('Upload')).toBeInTheDocument();
  });

  it('navigates to molecules page on upload complete', async () => {
    renderWithProviders(<MoleculeUploadPage />);
    const completeButton = screen.getByText('Complete Upload');
    fireEvent.click(completeButton);
    expect(mockNavigate).toHaveBeenCalledWith(ROUTES.MOLECULES.LIST);
  });

  it('passes accessibility tests', async () => {
    const { container } = renderWithProviders(<MoleculeUploadPage />);
    await axeTest(container);
  });
});