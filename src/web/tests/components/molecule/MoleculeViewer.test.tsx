import React from 'react'; // react v18.0+
import { render, screen, fireEvent, waitFor } from '@testing-library/react'; // @testing-library/react v13.0+
import { act } from '@testing-library/react'; // @testing-library/react v13.0+

import MoleculeViewer from '../../src/components/molecule/MoleculeViewer';
import { createMockMolecule, renderWithProviders, axeTest } from '../../src/utils/testHelpers';
import { createMoleculeViewer, loadMoleculeFromSmiles, exportMoleculeToSVG, exportMoleculeToPNG, DEFAULT_VIEWER_OPTIONS } from '../../src/utils/moleculeStructure';

// Mock the molecule structure utils module
jest.mock('../../src/utils/moleculeStructure', () => ({
  createMoleculeViewer: jest.fn(),
  loadMoleculeFromSmiles: jest.fn(),
  exportMoleculeToSVG: jest.fn(),
  exportMoleculeToPNG: jest.fn(),
  DEFAULT_VIEWER_OPTIONS: {}
}));

describe('MoleculeViewer', () => {
  beforeEach(() => {
    (createMoleculeViewer as jest.Mock).mockClear();
    (loadMoleculeFromSmiles as jest.Mock).mockClear();
    (exportMoleculeToSVG as jest.Mock).mockClear();
    (exportMoleculeToPNG as jest.Mock).mockClear();

    // Mock createMoleculeViewer to return a mock viewer object
    (createMoleculeViewer as jest.Mock).mockReturnValue({
      clear: jest.fn(),
      loadMolecule: jest.fn(),
      center: jest.fn(),
      repaint: jest.fn()
    });

    // Mock loadMoleculeFromSmiles to resolve successfully
    (loadMoleculeFromSmiles as jest.Mock).mockResolvedValue(true);

    // Mock export functions to return expected values
    (exportMoleculeToSVG as jest.Mock).mockReturnValue('<svg>Mock SVG</svg>');
    (exportMoleculeToPNG as jest.Mock).mockResolvedValue('data:image/png;base64,mockPngData');
  });

  afterEach(() => {
    jest.clearAllMocks();
  });

  test('renders with SMILES string', () => {
    renderWithProviders(<MoleculeViewer smiles="CC(=O)Oc1ccccc1C(=O)O" />);

    expect(createMoleculeViewer).toHaveBeenCalled();
    expect(loadMoleculeFromSmiles).toHaveBeenCalledWith(expect.anything(), "CC(=O)Oc1ccccc1C(=O)O");
    expect(screen.getByRole('figure')).toBeInTheDocument();
  });

  test('renders with molecule object', () => {
    const molecule = createMockMolecule({ smiles: "c1ccccc1" });
    renderWithProviders(<MoleculeViewer molecule={molecule} />);

    expect(createMoleculeViewer).toHaveBeenCalled();
    expect(loadMoleculeFromSmiles).toHaveBeenCalledWith(expect.anything(), "c1ccccc1");
    expect(screen.getByRole('figure')).toBeInTheDocument();
  });

  test('shows loading state while molecule is loading', async () => {
    (loadMoleculeFromSmiles as jest.Mock).mockImplementation(() => {
      return new Promise(resolve => setTimeout(() => resolve(true), 50));
    });

    renderWithProviders(<MoleculeViewer smiles="CC(=O)Oc1ccccc1C(=O)O" />);

    expect(screen.getByLabelText('Loading molecule structure')).toBeInTheDocument();

    await waitFor(() => expect(screen.queryByLabelText('Loading molecule structure')).not.toBeInTheDocument());
  });

  test('shows error state when molecule loading fails', async () => {
    (loadMoleculeFromSmiles as jest.Mock).mockRejectedValue(new Error('Failed to load'));

    renderWithProviders(<MoleculeViewer smiles="Invalid SMILES" />);

    await waitFor(() => expect(screen.getByText('Failed to load molecule structure')).toBeInTheDocument());
  });

  test('toggles between 2D and 3D views', () => {
    renderWithProviders(<MoleculeViewer smiles="CC(=O)Oc1ccccc1C(=O)O" showControls />);

    const toggleButton = screen.getByLabelText('Switch to 3D View');
    expect(toggleButton).toBeInTheDocument();

    fireEvent.click(toggleButton);
    expect(createMoleculeViewer).toHaveBeenCalledWith(expect.anything(), expect.anything(), '3D');

    const toggleButton2D = screen.getByLabelText('Switch to 2D View');
    fireEvent.click(toggleButton2D);
    expect(createMoleculeViewer).toHaveBeenCalledWith(expect.anything(), expect.anything(), '2D');
  });

  test('exports molecule as SVG', () => {
    renderWithProviders(<MoleculeViewer smiles="CC(=O)Oc1ccccc1C(=O)O" showControls />);

    const svgButton = screen.getByLabelText('Download as SVG');
    fireEvent.click(svgButton);

    expect(exportMoleculeToSVG).toHaveBeenCalled();
  });

  test('exports molecule as PNG', async () => {
    renderWithProviders(<MoleculeViewer smiles="CC(=O)Oc1ccccc1C(=O)O" showControls />);

    const pngButton = screen.getByLabelText('Download as PNG');
    fireEvent.click(pngButton);

    await waitFor(() => expect(exportMoleculeToPNG).toHaveBeenCalled());
  });

  test('calls onLoad callback when molecule loading completes', async () => {
    const onLoad = jest.fn();
    renderWithProviders(<MoleculeViewer smiles="CC(=O)Oc1ccccc1C(=O)O" onLoad={onLoad} />);

    await waitFor(() => expect(onLoad).toHaveBeenCalledWith(true));
  });

  test('calls onLoad callback with false when molecule loading fails', async () => {
    (loadMoleculeFromSmiles as jest.Mock).mockRejectedValue(new Error('Failed to load'));
    const onLoad = jest.fn();
    renderWithProviders(<MoleculeViewer smiles="Invalid SMILES" onLoad={onLoad} />);

    await waitFor(() => expect(onLoad).toHaveBeenCalledWith(false));
  });

  test('applies custom width and height', () => {
    renderWithProviders(<MoleculeViewer smiles="CC(=O)Oc1ccccc1C(=O)O" width={400} height={500} />);

    const container = screen.getByRole('figure');
    expect(container).toHaveStyle('width: 400px');
    expect(container).toHaveStyle('height: 500px');
    expect(createMoleculeViewer).toHaveBeenCalledWith(expect.anything(), expect.objectContaining({ width: 400, height: 500 }), expect.anything());
  });

  test('handles empty SMILES gracefully', () => {
    renderWithProviders(<MoleculeViewer smiles="" />);

    expect(screen.getByText('Failed to load molecule structure')).toBeInTheDocument();
    expect(loadMoleculeFromSmiles).not.toHaveBeenCalled();
  });

  test('passes accessibility tests', async () => {
    const { container } = renderWithProviders(<MoleculeViewer smiles="CC(=O)Oc1ccccc1C(=O)O" />);
    await axeTest(container);
  });
});