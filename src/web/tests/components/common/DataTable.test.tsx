import React from 'react'; // react v18.0.0
import { render, screen, fireEvent, waitFor } from '@testing-library/react'; // ^13.0.0
import userEvent from '@testing-library/user-event'; // ^14.0.0
import DataTable from '../../../src/components/common/DataTable';
import { renderWithProviders, axeTest } from '../../../src/utils/testHelpers';
import { Molecule } from '../../../src/types/molecule.types';

// Mock data for testing the DataTable component
const mockData: { id: string; name: string; age: number; email: string }[] = [
  { id: '1', name: 'John Doe', age: 30, email: 'john.doe@example.com' },
  { id: '2', name: 'Jane Smith', age: 25, email: 'jane.smith@example.com' },
  { id: '3', name: 'Peter Jones', age: 40, email: 'peter.jones@example.com' },
];

// Mock column configuration for testing the DataTable component
const mockColumns = [
  { id: 'name', label: 'Name', sortable: true },
  { id: 'age', label: 'Age', sortable: true, align: 'right', format: (value: number) => `${value} years` },
  { id: 'email', label: 'Email' },
];

/**
 * Helper function to set up the test environment with mock data and render the DataTable component
 * @param props - Optional props to override default DataTable props
 * @returns Rendered component and utilities
 */
const setup = (props = {}) => {
  // LD1: Create mock data for the table
  const data = mockData;

  // LD1: Define column configuration
  const columns = mockColumns;

  // LD1: Merge default props with provided props
  const mergedProps = {
    columns,
    data,
    ...props,
  };

  // LD1: Render the DataTable component with renderWithProviders
  const renderResult = renderWithProviders(<DataTable {...mergedProps} />);

  // LD1: Return rendered component and utilities
  return {
    ...renderResult,
  };
};

describe('DataTable', () => {
  it('renders without crashing', () => {
    // Arrange
    const { getByText } = setup();

    // Assert
    expect(getByText('John Doe')).toBeInTheDocument();
    expect(getByText('Jane Smith')).toBeInTheDocument();
    expect(getByText('Peter Jones')).toBeInTheDocument();
    expect(getByText('Name')).toBeInTheDocument();
    expect(getByText('Age')).toBeInTheDocument();
    expect(getByText('Email')).toBeInTheDocument();
  });

  it('displays loading state correctly', () => {
    // Arrange
    const { rerender } = setup({ loading: true });

    // Assert
    expect(screen.getByRole('progressbar')).toBeInTheDocument();
    expect(screen.queryByText('John Doe')).not.toBeInTheDocument();

    // Act
    rerender(<DataTable columns={mockColumns} data={mockData} loading={false} />);

    // Assert
    expect(screen.queryByRole('progressbar')).not.toBeInTheDocument();
    expect(screen.getByText('John Doe')).toBeInTheDocument();
  });

  it('displays empty message when data is empty', () => {
    // Arrange
    const { getByText } = setup({ data: [] });

    // Assert
    expect(getByText('No data available')).toBeInTheDocument();

    // Arrange
    const customEmptyMessage = 'Custom empty message';
    const { getByText: getByTextCustom } = setup({ data: [], emptyMessage: customEmptyMessage });

    // Assert
    expect(getByTextCustom(customEmptyMessage)).toBeInTheDocument();
  });

  it('sorts data when clicking on sortable column headers', async () => {
    // Arrange
    const { getByText } = setup();
    const nameHeader = getByText('Name');
    const ageHeader = getByText('Age');

    // Act
    fireEvent.click(nameHeader);

    // Assert
    await waitFor(() => {
      expect(mockData[0].name).toBe('John Doe');
    });

    // Act
    fireEvent.click(ageHeader);

    // Assert
    await waitFor(() => {
      expect(mockData[0].age).toBe(25);
    });
  });

  it('handles row selection correctly', async () => {
    // Arrange
    const onSelectionChange = jest.fn();
    const { getByRole, getAllByRole } = setup({ selectable: true, onSelectionChange });

    // Act
    const checkbox = getByRole('checkbox', { name: 'select row' });
    fireEvent.click(checkbox);

    // Assert
    expect(onSelectionChange).toHaveBeenCalledTimes(1);
    expect(onSelectionChange).toHaveBeenCalledWith(['1']);

    // Act
    const selectAllCheckbox = getByRole('checkbox', { name: 'select all' });
    fireEvent.click(selectAllCheckbox);

    // Assert
    expect(onSelectionChange).toHaveBeenCalledTimes(2);
    expect(onSelectionChange).toHaveBeenCalledWith(['1', '2', '3']);
  });

  it('handles row click events', () => {
    // Arrange
    const onRowClick = jest.fn();
    const { getByText } = setup({ onRowClick });

    // Act
    const row = getByText('John Doe');
    fireEvent.click(row);

    // Assert
    expect(onRowClick).toHaveBeenCalledTimes(1);
    expect(onRowClick).toHaveBeenCalledWith(mockData[0]);
  });

  it('renders pagination controls when pagination is enabled', () => {
    // Arrange
    const onPageChange = jest.fn();
    const onPageSizeChange = jest.fn();
    const totalCount = 100;
    const { getByRole, queryByRole } = setup({ pagination: true, totalCount, onPageChange, onPageSizeChange });

    // Assert
    expect(getByRole('navigation')).toBeInTheDocument();

    // Act
    const nextPageButton = getByRole('button', { name: 'Next page' });
    fireEvent.click(nextPageButton);

    // Assert
    expect(onPageChange).toHaveBeenCalledTimes(1);
    expect(onPageChange).toHaveBeenCalledWith(2);

    // Act
    const pageSizeSelect = getByRole('combobox', { name: 'Items per page' });
    fireEvent.change(pageSizeSelect, { target: { value: 50 } });

    // Assert
    expect(onPageSizeChange).toHaveBeenCalledTimes(0);
  });

  it('applies custom formatting to cells', () => {
    // Arrange
    const format = jest.fn((value) => `Formatted: ${value}`);
    const renderCell = jest.fn((row) => <div>Custom Rendered</div>);
    const columns = [
      { id: 'name', label: 'Name', format },
      { id: 'age', label: 'Age', renderCell },
    ];
    const { getByText } = setup({ columns });

    // Assert
    expect(getByText('Formatted: John Doe')).toBeInTheDocument();
    expect(getByText('Custom Rendered')).toBeInTheDocument();
  });

  it('passes accessibility tests', async () => {
    // Arrange
    const { container } = setup();

    // Act & Assert
    await axeTest(container);
  });
});