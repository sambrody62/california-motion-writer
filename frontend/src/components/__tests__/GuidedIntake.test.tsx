/**
 * Tests for GuidedIntake component
 */
import React from 'react';
import { render, screen, waitFor, fireEvent } from '@testing-library/react';
import '@testing-library/jest-dom';
import { BrowserRouter } from 'react-router-dom';
import { GuidedIntake } from '../motion/GuidedIntake';

// --- Mocks ---

const mockNavigate = jest.fn();
const mockUseLocation = jest.fn(() => ({ state: null, pathname: '/' }));

jest.mock('react-router-dom', () => ({
  ...jest.requireActual('react-router-dom'),
  useNavigate: () => mockNavigate,
  useParams: () => ({ motionType: 'FL_300', formType: undefined }),
  useLocation: () => mockUseLocation(),
}));

jest.mock('../../types/forms', () => ({
  FORM_METADATA: { FL_300: { name: 'Request for Order', id: 'FL-300' } },
  FORM_TYPES: { FL_300: 'FL_300' },
  FormType: {},
}));

const MOCK_STEP_DATA = {
  id: 'FL_300_step_1',
  step_number: 1,
  step_name: 'Case Information',
  description: 'Basic case info',
  questions: [
    { id: 'party_name', type: 'text', label: 'Your Name', required: true },
    { id: 'other_party_name', type: 'text', label: 'Other Party Name', required: false },
    { id: 'case_number', type: 'text', label: 'Case Number', required: false },
  ],
  total_steps: 1,
};

// Module-level mock functions — safe against jest.clearAllMocks()
const mockGetProfile = jest.fn();
const mockCreate = jest.fn();
const mockSaveDraft = jest.fn();
const mockGetDrafts = jest.fn();
const mockProcessWithLLM = jest.fn();
const mockGetQuestions = jest.fn();
const mockSaveAnswer = jest.fn();
const mockEvaluateCondition = jest.fn();

jest.mock('../../services/api', () => ({
  profileAPI: {
    getProfile: (...args: any[]) => mockGetProfile(...args),
  },
  motionAPI: {
    create: (...args: any[]) => mockCreate(...args),
    saveDraft: (...args: any[]) => mockSaveDraft(...args),
    getDrafts: (...args: any[]) => mockGetDrafts(...args),
    processWithLLM: (...args: any[]) => mockProcessWithLLM(...args),
  },
  intakeAPI: {
    getQuestions: (...args: any[]) => mockGetQuestions(...args),
    saveAnswer: (...args: any[]) => mockSaveAnswer(...args),
    evaluateCondition: (...args: any[]) => mockEvaluateCondition(...args),
  },
}));

const renderWithRouter = (ui: React.ReactElement) =>
  render(<BrowserRouter>{ui}</BrowserRouter>);

describe('GuidedIntake', () => {
  beforeEach(() => {
    jest.clearAllMocks();
    mockUseLocation.mockReturnValue({ state: null, pathname: '/' });
    mockCreate.mockResolvedValue({ data: { id: 'motion-123' } });
    mockGetDrafts.mockResolvedValue({ data: { drafts: [] } });
    mockSaveDraft.mockResolvedValue({ success: true });
    mockProcessWithLLM.mockResolvedValue({ success: true });
    mockGetQuestions.mockResolvedValue({ data: MOCK_STEP_DATA });
    mockSaveAnswer.mockResolvedValue({ success: true });
    mockEvaluateCondition.mockResolvedValue({ data: { result: true } });
    mockGetProfile.mockResolvedValue({
      party_name: 'Jane Doe',
      other_party_name: 'John Doe',
      case_number: 'FL-2024-999',
      county: 'San Diego',
      children_info: 'Two children, ages 5 and 8',
    });
  });

  test('autofill populates fields from profile when fields are empty', async () => {
    renderWithRouter(<GuidedIntake />);

    // Wait for form questions to render
    await waitFor(() => {
      expect(screen.getByLabelText(/Your Name/i)).toBeInTheDocument();
    });

    // Profile fields should be pre-populated
    await waitFor(() => {
      const partyNameInput = screen.getByLabelText(/Your Name/i) as HTMLInputElement;
      expect(partyNameInput.value).toBe('Jane Doe');
    });

    const otherPartyInput = screen.getByLabelText(/Other Party Name/i) as HTMLInputElement;
    expect(otherPartyInput.value).toBe('John Doe');

    const caseNumberInput = screen.getByLabelText(/Case Number/i) as HTMLInputElement;
    expect(caseNumberInput.value).toBe('FL-2024-999');
  });

  test('shows "Filled from your profile" indicator on autofilled fields', async () => {
    renderWithRouter(<GuidedIntake />);

    await waitFor(() => {
      expect(screen.getAllByText(/Filled from your profile/i).length).toBeGreaterThan(0);
    });
  });

  test('does not autofill fields that already have saved values', async () => {
    mockGetDrafts.mockResolvedValue({
      data: {
        drafts: [
          {
            step_number: 1,
            question_data: { party_name: 'Existing Name', case_number: 'EXISTING-001' },
          },
        ],
      },
    });

    renderWithRouter(<GuidedIntake />);

    await waitFor(() => {
      const partyNameInput = screen.getByLabelText(/Your Name/i) as HTMLInputElement;
      expect(partyNameInput.value).toBe('Existing Name');
    });

    // case_number saved value should not be overwritten
    const caseNumberInput = screen.getByLabelText(/Case Number/i) as HTMLInputElement;
    expect(caseNumberInput.value).toBe('EXISTING-001');
  });

  test('LLM failure path still navigates to preview with user words', async () => {
    mockProcessWithLLM.mockRejectedValue(new Error('LLM unavailable'));

    renderWithRouter(<GuidedIntake />);

    // Wait for form to load and show "Complete" on the single-step form
    await waitFor(() => {
      expect(screen.getByRole('button', { name: /Complete/i })).toBeInTheDocument();
    });

    fireEvent.click(screen.getByRole('button', { name: /Complete/i }));

    // After LLM failure, should navigate to preview anyway with llmFailed=true
    await waitFor(() => {
      expect(mockNavigate).toHaveBeenCalledWith(
        expect.stringContaining('/preview'),
        expect.objectContaining({ state: expect.objectContaining({ llmFailed: true }) })
      );
    });
  });

  test('shows LLM processing text during processing phase', async () => {
    // Delay processWithLLM so we can observe the loading state
    let resolveLLM: () => void;
    mockProcessWithLLM.mockReturnValue(
      new Promise<void>((resolve) => { resolveLLM = resolve; })
    );

    renderWithRouter(<GuidedIntake />);

    await waitFor(() => {
      expect(screen.getByRole('button', { name: /Complete/i })).toBeInTheDocument();
    });

    fireEvent.click(screen.getByRole('button', { name: /Complete/i }));

    await waitFor(() => {
      expect(
        screen.getByText(/Reviewing your answers and drafting court language/i)
      ).toBeInTheDocument();
    });

    // Resolve so we don't leave pending promises
    resolveLLM!();
  });

  test('completion callback fires when intake finishes successfully', async () => {
    const onComplete = jest.fn();

    renderWithRouter(<GuidedIntake onComplete={onComplete} />);

    await waitFor(() => {
      expect(screen.getByRole('button', { name: /Complete/i })).toBeInTheDocument();
    });

    fireEvent.click(screen.getByRole('button', { name: /Complete/i }));

    await waitFor(() => {
      expect(onComplete).toHaveBeenCalledWith('motion-123');
    });
  });

  test('completion callback fires even when LLM fails', async () => {
    mockProcessWithLLM.mockRejectedValue(new Error('LLM unavailable'));
    const onComplete = jest.fn();

    renderWithRouter(<GuidedIntake onComplete={onComplete} />);

    await waitFor(() => {
      expect(screen.getByRole('button', { name: /Complete/i })).toBeInTheDocument();
    });

    fireEvent.click(screen.getByRole('button', { name: /Complete/i }));

    await waitFor(() => {
      expect(onComplete).toHaveBeenCalledWith('motion-123');
    });
  });
});
