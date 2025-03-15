import React from 'react'; // react ^18.0.0
import { render, screen, waitFor, fireEvent, act } from '@testing-library/react'; // @testing-library/react ^13.0.0
import userEvent from '@testing-library/user-event'; // @testing-library/user-event ^14.0.0
import { SubmissionForm } from '../../src/components/submission/SubmissionForm';
import { renderWithProviders, createMockSubmission, createMockMolecule, createMockMoleculeArray, axeTest } from '../../src/utils/testHelpers';
import { SubmissionStatus } from '../../src/constants/submissionStatus';
import { DocumentType } from '../../src/constants/documentTypes';
import { getCROServices } from '../../src/api/croApi';
import { getMolecules } from '../../src/api/moleculeApi';
import { getSubmissionDocumentRequirements, createSubmission, updateSubmission } from '../../src/api/submissionApi';

// Mock API calls
jest.mock('../../src/api/croApi', () => ({
  getCROServices: jest.fn()
}));
jest.mock('../../src/api/moleculeApi', () => ({
  getMolecules: jest.fn()
}));
jest.mock('../../src/api/submissionApi', () => ({
  getSubmissionDocumentRequirements: jest.fn(),
  createSubmission: jest.fn(),
  updateSubmission: jest.fn()
}));
jest.mock('../../src/hooks/useToast', () => ({
  useToast: () => ({ showSuccess: jest.fn(), showError: jest.fn() })
}));

describe('SubmissionForm', () => {
  beforeEach(() => {
    (getCROServices as jest.Mock).mockClear();
    (getMolecules as jest.Mock).mockClear();
    (getSubmissionDocumentRequirements as jest.Mock).mockClear();
    (createSubmission as jest.Mock).mockClear();
    (updateSubmission as jest.Mock).mockClear();

    (getCROServices as jest.Mock).mockResolvedValue({ items: [{ id: 'cro1', name: 'CRO 1' }] });
    (getMolecules as jest.Mock).mockResolvedValue({ items: createMockMoleculeArray(5) });
    (getSubmissionDocumentRequirements as jest.Mock).mockResolvedValue({
      required_documents: [
        { type: DocumentType.MATERIAL_TRANSFER_AGREEMENT, description: 'MTA', exists: false },
        { type: DocumentType.NON_DISCLOSURE_AGREEMENT, description: 'NDA', exists: false },
        { type: DocumentType.EXPERIMENT_SPECIFICATION, description: 'Experiment Spec', exists: false }
      ],
      optional_documents: [],
      existing_documents: []
    });
  });

  it('renders the form in create mode', async () => {
    (getCROServices as jest.Mock).mockResolvedValue({ items: [{ id: 'cro1', name: 'CRO 1' }] });

    renderWithProviders(<SubmissionForm />);

    expect(screen.getByText('Create Submission')).toBeInTheDocument();
    expect(screen.getByText('Step 1: CRO Service Selection')).toBeInTheDocument();
    expect(screen.getByLabelText('Submission Name')).toBeInTheDocument();
    expect(screen.getByLabelText('CRO Service')).toBeInTheDocument();
  });

  it('renders the form in edit mode with initial data', async () => {
    const initialData = createMockSubmission({ name: 'Test Submission', cro_service_id: 'cro1' });
    (getCROServices as jest.Mock).mockResolvedValue({ items: [{ id: 'cro1', name: 'CRO 1' }] });
    (getMolecules as jest.Mock).mockResolvedValue({ items: createMockMoleculeArray(5) });
    (getSubmissionDocumentRequirements as jest.Mock).mockResolvedValue({
      required_documents: [],
      optional_documents: [],
      existing_documents: []
    });

    renderWithProviders(<SubmissionForm initialData={initialData} submissionId="sub1" />);

    expect(screen.getByText('Edit Submission')).toBeInTheDocument();
    expect((screen.getByLabelText('Submission Name') as HTMLInputElement).value).toBe('Test Submission');
  });

  it('validates required fields', async () => {
    renderWithProviders(<SubmissionForm />);

    const nextButton = screen.getByRole('button', { name: 'Next' });
    await act(async () => {
      fireEvent.click(nextButton);
    });

    expect(screen.getByText('Submission name is required')).toBeInTheDocument();
    expect(screen.getByText('CRO service is required')).toBeInTheDocument();

    const nameInput = screen.getByLabelText('Submission Name');
    const croSelect = screen.getByLabelText('CRO Service');

    await act(async () => {
      fireEvent.change(nameInput, { target: { value: 'Test Submission' } });
      fireEvent.change(croSelect, { target: { value: 'cro1' } });
    });

    expect(() => screen.getByText('Submission name is required')).toThrow();
    expect(() => screen.getByText('CRO service is required')).toThrow();
  });

  it('navigates between steps correctly', async () => {
    renderWithProviders(<SubmissionForm />);

    const nameInput = screen.getByLabelText('Submission Name');
    const croSelect = screen.getByLabelText('CRO Service');
    const nextButton = screen.getByRole('button', { name: 'Next' });
    const backButton = screen.getByRole('button', { name: 'Back' });

    await act(async () => {
      fireEvent.change(nameInput, { target: { value: 'Test Submission' } });
      fireEvent.change(croSelect, { target: { value: 'cro1' } });
      fireEvent.click(nextButton);
    });

    expect(screen.getByText('Step 2: Molecule Selection')).toBeInTheDocument();

    await act(async () => {
      fireEvent.click(backButton);
    });

    expect(screen.getByText('Step 1: CRO Service Selection')).toBeInTheDocument();
  });

  it('handles CRO service selection correctly', async () => {
    (getCROServices as jest.Mock).mockResolvedValue({ items: [{ id: 'cro1', name: 'CRO 1' }, { id: 'cro2', name: 'CRO 2' }] });

    renderWithProviders(<SubmissionForm />);

    const croSelect = screen.getByLabelText('CRO Service');
    await act(async () => {
      fireEvent.mouseDown(croSelect);
    });

    const cro1Option = screen.getByRole('option', { name: 'CRO 1' });
    await act(async () => {
      fireEvent.click(cro1Option);
    });

    expect((croSelect as HTMLSelectElement).value).toBe('cro1');
  });

  it('handles molecule selection correctly', async () => {
    (getMolecules as jest.Mock).mockResolvedValue({ items: createMockMoleculeArray(5) });

    renderWithProviders(<SubmissionForm />);

    const nameInput = screen.getByLabelText('Submission Name');
    const croSelect = screen.getByLabelText('CRO Service');
    const nextButton = screen.getByRole('button', { name: 'Next' });

    await act(async () => {
      fireEvent.change(nameInput, { target: { value: 'Test Submission' } });
      fireEvent.change(croSelect, { target: { value: 'cro1' } });
      fireEvent.click(nextButton);
    });

    expect(screen.getByText('Step 2: Molecule Selection')).toBeInTheDocument();

    const moleculeCheckboxes = await screen.findAllByRole('checkbox');
    await act(async () => {
      fireEvent.click(moleculeCheckboxes[1]);
      fireEvent.click(moleculeCheckboxes[2]);
    });

    expect(screen.getByText('Step 2: Molecule Selection')).toBeInTheDocument();
  });

  it('handles document requirements correctly', async () => {
    (getSubmissionDocumentRequirements as jest.Mock).mockResolvedValue({
      required_documents: [
        { type: DocumentType.MATERIAL_TRANSFER_AGREEMENT, description: 'MTA', exists: false },
        { type: DocumentType.NON_DISCLOSURE_AGREEMENT, description: 'NDA', exists: false },
        { type: DocumentType.EXPERIMENT_SPECIFICATION, description: 'Experiment Spec', exists: false }
      ],
      optional_documents: [],
      existing_documents: []
    });

    renderWithProviders(<SubmissionForm submissionId="sub1" />);

    const nameInput = screen.getByLabelText('Submission Name');
    const croSelect = screen.getByLabelText('CRO Service');
    const nextButton = screen.getByRole('button', { name: 'Next' });

    await act(async () => {
      fireEvent.change(nameInput, { target: { value: 'Test Submission' } });
      fireEvent.change(croSelect, { target: { value: 'cro1' } });
      fireEvent.click(nextButton);
    });

    expect(screen.getByText('Step 2: Molecule Selection')).toBeInTheDocument();
    await act(async () => {
      fireEvent.click(nextButton);
    });

    expect(screen.getByText('Step 3: Document Management')).toBeInTheDocument();
    expect(screen.getByText('MTA')).toBeInTheDocument();
    expect(screen.getByText('NDA')).toBeInTheDocument();
    expect(screen.getByText('Experiment Spec')).toBeInTheDocument();
  });

  it('submits the form correctly', async () => {
    (createSubmission as jest.Mock).mockResolvedValue(createMockSubmission({ id: 'new-submission' }));

    renderWithProviders(<SubmissionForm />);

    const nameInput = screen.getByLabelText('Submission Name');
    const croSelect = screen.getByLabelText('CRO Service');
    const nextButton = screen.getByRole('button', { name: 'Next' });
    const submitButton = screen.getByRole('button', { name: 'Submit' });

    await act(async () => {
      fireEvent.change(nameInput, { target: { value: 'Test Submission' } });
      fireEvent.change(croSelect, { target: { value: 'cro1' } });
      fireEvent.click(nextButton);
    });

    await act(async () => {
      fireEvent.click(nextButton);
    });

    await act(async () => {
      fireEvent.click(submitButton);
    });

    expect(createSubmission).toHaveBeenCalled();
  });

  it('saves form as draft correctly', async () => {
    (createSubmission as jest.Mock).mockResolvedValue(createMockSubmission({ id: 'new-submission' }));

    renderWithProviders(<SubmissionForm />);

    const nameInput = screen.getByLabelText('Submission Name');
    const croSelect = screen.getByLabelText('CRO Service');
    const saveDraftButton = screen.getByRole('button', { name: 'Save Draft' });

    await act(async () => {
      fireEvent.change(nameInput, { target: { value: 'Test Submission' } });
      fireEvent.change(croSelect, { target: { value: 'cro1' } });
      fireEvent.click(saveDraftButton);
    });

    expect(createSubmission).toHaveBeenCalled();
  });

  it('handles cancellation correctly', async () => {
    const onCancel = jest.fn();
    renderWithProviders(<SubmissionForm onCancel={onCancel} />);

    const cancelButton = screen.getByRole('button', { name: 'Back' });
    await act(async () => {
      fireEvent.click(cancelButton);
    });

    expect(onCancel).toHaveBeenCalled();
  });

  it('meets accessibility requirements', async () => {
    const { container } = renderWithProviders(<SubmissionForm />);
    await axeTest(container);
  });

  it('handles API errors correctly', async () => {
    (getCROServices as jest.Mock).mockRejectedValue(new Error('API Error'));

    renderWithProviders(<SubmissionForm />);

    await waitFor(() => {
      expect(screen.getByText('Failed to load CRO services: API Error')).toBeInTheDocument();
    });
  });
});