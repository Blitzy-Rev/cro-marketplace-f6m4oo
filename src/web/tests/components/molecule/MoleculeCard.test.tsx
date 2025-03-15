import React from 'react'; // react v18.0+
import { render, screen, fireEvent, waitFor } from '@testing-library/react'; // @testing-library/react v13.4.0
import MoleculeCard from '../../src/components/molecule/MoleculeCard';
import { createMockMolecule, renderWithProviders, axeTest } from '../../src/utils/testHelpers';
import { MoleculeStatus } from '../../src/types/molecule.types';

// Mock MoleculeViewer component
jest.mock('../../src/components/molecule/MoleculeViewer', () => {
  return {
    __esModule: true,
    default: () => <div data-testid="molecule-viewer">MoleculeViewer</div>,
  };
});

// Mock formatMolecularProperty function
jest.mock('../../src/utils/propertyFormatters', () => ({
  formatMolecularProperty: jest.fn((value) => `Formatted: ${value}`),
  getPropertyDisplayName: jest.fn((name) => `Display Name: ${name}`),
}));

describe('MoleculeCard', () => {
  beforeEach(() => {
    jest.clearAllMocks();
    document.body.innerHTML = '';
  });

  afterEach(() => {
    document.body.innerHTML = '';
  });

  it('renders without crashing', () => {
    const molecule = createMockMolecule();
    renderWithProviders(<MoleculeCard molecule={molecule} />);
    expect(screen.getByText('MoleculeViewer')).toBeInTheDocument();
  });

  it('displays molecule structure using MoleculeViewer', () => {
    const molecule = createMockMolecule({ smiles: 'CCO' });
    renderWithProviders(<MoleculeCard molecule={molecule} />);
    expect(screen.getByText('MoleculeViewer')).toBeInTheDocument();
  });

  it('displays molecule properties correctly', () => {
    const molecule = createMockMolecule({
      properties: [
        { name: 'molecular_weight', value: 100 },
        { name: 'logp', value: 2.5 },
      ],
    });
    renderWithProviders(<MoleculeCard molecule={molecule} />);
    expect(screen.getByText('Display Name: molecular_weight:')).toBeInTheDocument();
    expect(screen.getByText('Formatted: 100')).toBeInTheDocument();
    expect(screen.getByText('Display Name: logp:')).toBeInTheDocument();
    expect(screen.getByText('Formatted: 2.5')).toBeInTheDocument();
  });

  it('handles selection state correctly', () => {
    const molecule = createMockMolecule();
    renderWithProviders(<MoleculeCard molecule={molecule} selected={true} showCheckbox={true} />);
    const cardElement = screen.getByRole('checkbox');
    expect(cardElement).toBeChecked();

    renderWithProviders(<MoleculeCard molecule={molecule} selected={false} showCheckbox={true} />);
    const cardElement2 = screen.getByRole('checkbox');
    expect(cardElement2).not.toBeChecked();
  });

  it('calls onSelect callback when checkbox is clicked', () => {
    const molecule = createMockMolecule();
    const onSelect = jest.fn();
    renderWithProviders(<MoleculeCard molecule={molecule} onSelect={onSelect} showCheckbox={true} />);
    const checkboxElement = screen.getByRole('checkbox');
    fireEvent.click(checkboxElement);
    expect(onSelect).toHaveBeenCalledWith(molecule, true);
  });

  it('calls onClick callback when card is clicked', () => {
    const molecule = createMockMolecule();
    const onClick = jest.fn();
    renderWithProviders(<MoleculeCard molecule={molecule} onClick={onClick} />);
    const cardElement = screen.getByRole('figure');
    fireEvent.click(cardElement);
    expect(onClick).toHaveBeenCalledWith(molecule);
  });

  it('displays status badge when showStatus is true', () => {
    const molecule = createMockMolecule({ status: MoleculeStatus.TESTING });
    renderWithProviders(<MoleculeCard molecule={molecule} showStatus={true} />);
    expect(screen.getByText('Testing')).toBeInTheDocument();

    renderWithProviders(<MoleculeCard molecule={molecule} showStatus={false} />);
    expect(screen.queryByText('Testing')).not.toBeInTheDocument();
  });

  it('displays action buttons when showActions is true', () => {
    const molecule = createMockMolecule();
    renderWithProviders(<MoleculeCard molecule={molecule} showActions={true} />);
    expect(screen.getByLabelText('add to favorites')).toBeInTheDocument();
    expect(screen.getByLabelText('view details')).toBeInTheDocument();
    expect(screen.getByLabelText('more options')).toBeInTheDocument();

    renderWithProviders(<MoleculeCard molecule={molecule} showActions={false} />);
    expect(screen.queryByLabelText('add to favorites')).not.toBeInTheDocument();
    expect(screen.queryByLabelText('view details')).not.toBeInTheDocument();
    expect(screen.queryByLabelText('more options')).not.toBeInTheDocument();
  });

  it('displays only specified properties when highlightProperties is provided', () => {
    const molecule = createMockMolecule({
      properties: [
        { name: 'molecular_weight', value: 100 },
        { name: 'logp', value: 2.5 },
        { name: 'tpsa', value: 50 },
      ],
    });
    renderWithProviders(<MoleculeCard molecule={molecule} highlightProperties={['molecular_weight', 'logp']} />);
    expect(screen.getByText('Display Name: molecular_weight:')).toBeInTheDocument();
    expect(screen.getByText('Display Name: logp:')).toBeInTheDocument();
    expect(screen.queryByText('Display Name: tpsa:')).not.toBeInTheDocument();
  });

  it('passes accessibility tests', async () => {
    const molecule = createMockMolecule();
    const { container } = renderWithProviders(<MoleculeCard molecule={molecule} />);
    await axeTest(container);
  });
});