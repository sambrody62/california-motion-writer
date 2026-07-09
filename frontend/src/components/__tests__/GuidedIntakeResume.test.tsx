/**
 * Tests for GuidedIntake resume/edit mode (/motion/:motionId/edit/:stepNumber)
 */
import React from 'react';
import { render, screen, waitFor, fireEvent } from '@testing-library/react';
import '@testing-library/jest-dom';
import { BrowserRouter } from 'react-router-dom';
import { GuidedIntake } from '../motion/GuidedIntake';

// --- Mocks ---

const mockNavigate = jest.fn();
let mockParams: Record<string, string | undefined> = {};

jest.mock('react-router-dom', () => ({
  ...jest.requireActual('react-router-dom'),
  useNavigate: () => mockNavigate,
  useParams: () => mockParams,
  useLocation: () => ({ state: null, pathname: '/' }),
}));

jest.mock('../../services/servedMotionApi', () => ({
  servedMotionAPI: { parse: jest.fn() },
}));

jest.mock('../../types/forms', () => ({
  FORM_METADATA: {
    FL_300: { name: 'Request for Order', id: 'FL-300' },
    'FL-320': { name: 'Responsive Declaration', id: 'FL-320' },
  },
  FORM_TYPES: { FL_300: 'FL_300', FL_320: 'FL-320' },
  FormType: {},
}));

const STEP_1 = {
  step_number: 1,
  step_name: 'Case Information',
  description: 'Basic case info',
  questions: [{ id: 'party_name', type: 'text', label: 'Your Name', required: true }],
  total_steps: 2,
};

const STEP_2 = {
  step_number: 2,
  step_name: 'Orders Requested',
  description: 'What you are asking for',
  questions: [
    { id: 'relief_sought', type: 'text', label: 'What orders are you requesting?', required: true },
  ],
  total_steps: 2,
};

const SAVED_DRAFTS = [
  {
    step_number: 1,
    step_name: 'Case Information',
    question_data: { party_name: 'Saved Name' },
    llm_output: null,
    is_complete: true,
  },
  {
    step_number: 2,
    step_name: 'Orders Requested',
    question_data: { relief_sought: 'Modify custody schedule' },
    llm_output: null,
    is_complete: false,
  },
];

const mockGetProfile = jest.fn();
const mockCreate = jest.fn();
const mockGetMotion = jest.fn();
const mockSaveDraft = jest.fn();
const mockGetDrafts = jest.fn();
const mockProcessWithLLM = jest.fn();
const mockGetQuestions = jest.fn();
const mockEvaluateCondition = jest.fn();

jest.mock('../../services/api', () => ({
  profileAPI: {
    getProfile: (...args: any[]) => mockGetProfile(...args),
  },
  motionAPI: {
    create: (...args: any[]) => mockCreate(...args),
    get: (...args: any[]) => mockGetMotion(...args),
    saveDraft: (...args: any[]) => mockSaveDraft(...args),
    getDrafts: (...args: any[]) => mockGetDrafts(...args),
    processWithLLM: (...args: any[]) => mockProcessWithLLM(...args),
  },
  intakeAPI: {
    getQuestions: (...args: any[]) => mockGetQuestions(...args),
    evaluateCondition: (...args: any[]) => mockEvaluateCondition(...args),
  },
}));

const renderWithRouter = () => render(<BrowserRouter><GuidedIntake /></BrowserRouter>);

describe('GuidedIntake resume/edit mode', () => {
  beforeEach(() => {
    jest.clearAllMocks();
    mockParams = { motionId: 'motion-123', stepNumber: '2' };
    mockGetMotion.mockResolvedValue({
      id: 'motion-123',
      motion_type: 'FL_300',
      status: 'draft',
      drafts: SAVED_DRAFTS,
    });
    mockGetDrafts.mockResolvedValue(SAVED_DRAFTS);
    mockSaveDraft.mockResolvedValue({ success: true });
    mockProcessWithLLM.mockResolvedValue({ success: true });
    mockGetQuestions.mockImplementation((_formType: string, stepNumber?: number) =>
      Promise.resolve({ data: stepNumber === 2 ? STEP_2 : STEP_1 })
    );
    mockEvaluateCondition.mockResolvedValue({ data: { result: true } });
    mockGetProfile.mockResolvedValue(null);
  });

  test('loads the existing motion instead of creating a new one', async () => {
    renderWithRouter();

    await waitFor(() => expect(mockGetMotion).toHaveBeenCalledWith('motion-123'));
    await screen.findByText('Orders Requested');
    expect(mockCreate).not.toHaveBeenCalled();
  });

  test('starts at the requested step with the form type derived from the motion', async () => {
    renderWithRouter();

    await screen.findByText('Orders Requested');
    expect(mockGetQuestions).toHaveBeenCalledWith('FL_300', 2);
    expect(screen.getByText(/Step 2 of 2/i)).toBeInTheDocument();
    expect(screen.getByText(/Request for Order \(FL-300\)/i)).toBeInTheDocument();
  });

  test('hydrates saved answers for the step being edited', async () => {
    renderWithRouter();

    await waitFor(() => {
      const input = screen.getByLabelText(/What orders are you requesting/i) as HTMLInputElement;
      expect(input.value).toBe('Modify custody schedule');
    });
  });

  test('submitting saves against the existing motion id', async () => {
    renderWithRouter();

    await screen.findByText('Orders Requested');
    fireEvent.click(screen.getByRole('button', { name: /complete/i }));

    await waitFor(() =>
      expect(mockSaveDraft).toHaveBeenCalledWith(
        'motion-123',
        expect.objectContaining({ step_number: 2 })
      )
    );
  });

  test('resuming an FL-320 motion skips the served-motion upload gate', async () => {
    mockParams = { motionId: 'motion-320', stepNumber: '1' };
    mockGetMotion.mockResolvedValue({
      id: 'motion-320',
      motion_type: 'FL-320',
      status: 'draft',
      drafts: [],
    });
    mockGetDrafts.mockResolvedValue([]);
    mockGetQuestions.mockResolvedValue({ data: STEP_1 });

    renderWithRouter();

    await screen.findByText('Case Information');
    expect(screen.queryByText(/Skip — I'll type it in myself/i)).toBeNull();
  });
});
