import React from 'react'; // react v18.0+
import { renderWithProviders, axeTest } from '../../../../src/utils/testHelpers';
import { screen, fireEvent, waitFor } from '@testing-library/react'; // @testing-library/react v13.0+
import { act } from 'react-dom/test-utils'; // react-dom/test-utils v18.0+
import DragDropZone from '../../../../src/components/common/DragDropZone';
import { vi, Mock } from 'vitest';

// Mock callback function for file acceptance
const onFilesAccepted: Mock<any[], void> = vi.fn();

// Helper function to create mock File objects for testing
const createMockFile = (name: string, size: number, type: string): File => {
  const blob = new Blob([''], { type });
  blob['name'] = name;
  blob['size'] = size;
  return blob as File;
};

// Helper function to create mock drag events
const createDragEvent = (files: File[]): React.DragEvent<HTMLDivElement> => {
  return {
    preventDefault: () => {},
    stopPropagation: () => {},
    dataTransfer: {
      files: files as any,
      items: files.map(file => ({
        kind: 'file',
        type: file.type,
        getAsFile: () => file,
      })) as any,
    } as DataTransfer,
    target: {}
  } as React.DragEvent<HTMLDivElement>;
};

describe('DragDropZone', () => {
  beforeEach(() => {
    onFilesAccepted.mockClear();
  });

  afterEach(() => {
    vi.clearAllMocks();
  });

  it('renders correctly', async () => {
    const { container } = renderWithProviders(
      <DragDropZone onFilesAccepted={onFilesAccepted} />
    );

    expect(screen.getByText('Drag and drop your file here')).toBeInTheDocument();
    expect(screen.getByText('or')).toBeInTheDocument();
    expect(screen.getByRole('button', { name: 'Browse' })).toBeInTheDocument();
    expect(container.querySelector('svg')).toBeInTheDocument();
  });

  it('renders with custom children', async () => {
    renderWithProviders(
      <DragDropZone onFilesAccepted={onFilesAccepted}>
        <div>Custom Content</div>
      </DragDropZone>
    );

    expect(screen.getByText('Custom Content')).toBeInTheDocument();
    expect(screen.queryByText('Drag and drop your file here')).not.toBeInTheDocument();
  });

  it('handles file selection via browse button', async () => {
    const mockFile = createMockFile('test.csv', 1024, 'text/csv');
    const { container } = renderWithProviders(
      <DragDropZone onFilesAccepted={onFilesAccepted} />
    );

    const fileInput = container.querySelector('input[type="file"]') as HTMLInputElement;
    expect(fileInput).toBeInTheDocument();

    // Simulate file selection
    await act(async () => {
      fireEvent.change(fileInput, { target: { files: [mockFile] } });
    });

    await waitFor(() => {
      expect(onFilesAccepted).toHaveBeenCalledWith([mockFile]);
    });
  });

  it('handles drag and drop events', async () => {
    const mockFile = createMockFile('test.csv', 1024, 'text/csv');
    const dragEvent = createDragEvent([mockFile]);

    const { container } = renderWithProviders(
      <DragDropZone onFilesAccepted={onFilesAccepted} />
    );

    const dropZone = container.querySelector('div') as HTMLDivElement;
    expect(dropZone).toBeInTheDocument();

    // Simulate dragEnter event
    await act(async () => {
      fireEvent.dragEnter(dropZone, dragEvent);
    });

    // Simulate dragLeave event
    await act(async () => {
      fireEvent.dragLeave(dropZone, dragEvent);
    });

    // Simulate drop event
    await act(async () => {
      fireEvent.drop(dropZone, dragEvent);
    });

    await waitFor(() => {
      expect(onFilesAccepted).toHaveBeenCalledWith([mockFile]);
    });
  });

  it('validates file type', async () => {
    const validFile = createMockFile('test.csv', 1024, 'text/csv');
    const invalidFile = createMockFile('test.txt', 1024, 'text/plain');

    const { container } = renderWithProviders(
      <DragDropZone onFilesAccepted={onFilesAccepted} acceptedFileTypes={['.csv']} />
    );

    const dropZone = container.querySelector('div') as HTMLDivElement;
    expect(dropZone).toBeInTheDocument();

    // Simulate drop with invalid file type
    await act(async () => {
      fireEvent.drop(dropZone, createDragEvent([invalidFile]));
    });

    expect(screen.getByText('File type not supported. Accepted types: .csv')).toBeInTheDocument();
    expect(onFilesAccepted).not.toHaveBeenCalled();

    // Simulate drop with valid file type
    await act(async () => {
      fireEvent.drop(dropZone, createDragEvent([validFile]));
    });

    await waitFor(() => {
      expect(onFilesAccepted).toHaveBeenCalledWith([validFile]);
    });
  });

  it('validates file size', async () => {
    const validFile = createMockFile('test.csv', 1024, 'text/csv');
    const oversizedFile = createMockFile('test.csv', 2048 * 1024, 'text/csv'); // 2MB

    const { container } = renderWithProviders(
      <DragDropZone onFilesAccepted={onFilesAccepted} maxFileSizeMB={1} />
    );

    const dropZone = container.querySelector('div') as HTMLDivElement;
    expect(dropZone).toBeInTheDocument();

    // Simulate drop with oversized file
    await act(async () => {
      fireEvent.drop(dropZone, createDragEvent([oversizedFile]));
    });

    expect(screen.getByText('File size exceeds the maximum limit of 1 MB')).toBeInTheDocument();
    expect(onFilesAccepted).not.toHaveBeenCalled();

    // Simulate drop with valid size file
    await act(async () => {
      fireEvent.drop(dropZone, createDragEvent([validFile]));
    });

    await waitFor(() => {
      expect(onFilesAccepted).toHaveBeenCalledWith([validFile]);
    });
  });

  it('validates multiple file selection', async () => {
    const file1 = createMockFile('test1.csv', 1024, 'text/csv');
    const file2 = createMockFile('test2.csv', 1024, 'text/csv');
    const files = [file1, file2];

    // Test with multiple=false
    const { container: containerSingle } = renderWithProviders(
      <DragDropZone onFilesAccepted={onFilesAccepted} multiple={false} />
    );

    const dropZoneSingle = containerSingle.querySelector('div') as HTMLDivElement;
    expect(dropZoneSingle).toBeInTheDocument();

    await act(async () => {
      fireEvent.drop(dropZoneSingle, createDragEvent(files));
    });

    expect(screen.getByText('Only one file can be uploaded at a time')).toBeInTheDocument();
    expect(onFilesAccepted).not.toHaveBeenCalled();

    // Test with multiple=true
    const { container: containerMultiple } = renderWithProviders(
      <DragDropZone onFilesAccepted={onFilesAccepted} multiple={true} />
    );

    const dropZoneMultiple = containerMultiple.querySelector('div') as HTMLDivElement;
    expect(dropZoneMultiple).toBeInTheDocument();

    await act(async () => {
      fireEvent.drop(dropZoneMultiple, createDragEvent(files));
    });

    await waitFor(() => {
      expect(onFilesAccepted).toHaveBeenCalledWith(files);
    });
  });

  it('shows loading state', async () => {
    const { container } = renderWithProviders(
      <DragDropZone onFilesAccepted={onFilesAccepted} loading={true} />
    );

    expect(container.querySelector('.MuiCircularProgress-root')).toBeInTheDocument();
    expect(screen.queryByRole('button', { name: 'Browse' })).toBeDisabled();
  });

  it('clears error message on new file drop', async () => {
    const validFile = createMockFile('test.csv', 1024, 'text/csv');
    const invalidFile = createMockFile('test.txt', 1024, 'text/plain');

    const { container } = renderWithProviders(
      <DragDropZone onFilesAccepted={onFilesAccepted} acceptedFileTypes={['.csv']} />
    );

    const dropZone = container.querySelector('div') as HTMLDivElement;
    expect(dropZone).toBeInTheDocument();

    // Simulate drop with invalid file type
    await act(async () => {
      fireEvent.drop(dropZone, createDragEvent([invalidFile]));
    });

    expect(screen.getByText('File type not supported. Accepted types: .csv')).toBeInTheDocument();

    // Simulate drop with valid file type
    await act(async () => {
      fireEvent.drop(dropZone, createDragEvent([validFile]));
    });

    await waitFor(() => {
      expect(onFilesAccepted).toHaveBeenCalledWith([validFile]);
    });
  });

  it('passes accessibility tests', async () => {
    const { container } = renderWithProviders(
      <DragDropZone onFilesAccepted={onFilesAccepted} />
    );

    await axeTest(container);
  });
});