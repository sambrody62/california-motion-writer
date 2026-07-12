/**
 * Tests for GuidedIntake prefill ordering: profile autofill and served-motion
 * prefill must apply AFTER the draft reset instead of racing it, and stale
 * "Filled from your profile" badges must clear on steps with nothing to fill.
 * Regressions for real-LLM browser findings L9 and L12.
 */
import React from 'react';
import { render, screen, waitFor, fireEvent, act } from '@testing-library/react';
import '@testing-library/jest-dom';
import { BrowserRouter } from 'react-router-dom';
import { GuidedIntake } from '../motion/GuidedIntake';

const mockNavigate = jest.fn();
let mockParams: Record<string, string | undefined> = {};

jest.mock('react-router-dom', () => ({
  ...jest.requireActual('react-router-dom'),
  useNavigate: () => mockNavigate,
  useParams: () => mockParams,
  useLocation: () => ({ state: null, pathname: '/' }),
}));

const mockParseServedMotion = jest.fn();

jest.mock('../../services/servedMotionApi', () => ({
  servedMotionAPI: { parse: (...args: any[]) => mockParseServedMotion(...args) },
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

const STEP_2_OTHER_PARTY = {
  step_number: 2,
  step_name: 'Response Details',
  description: 'Respond to the other party',
  questions: [
    {
      id: 'other_party_requests',
      type: 'textarea',
      label: 'What is the other party asking for?',
      required: true,
    },
  ],
  total_steps: 2,
};

// Same question id as step 1 — the stale-badge case: the profile filled it on
// step 1, but on step 2 a saved draft owns the value, so no badge belongs here.
const STEP_2_REVISITS_NAME = {
  step_number: 2,
  step_name: 'Confirm Details',
  description: 'Confirm your details',
  questions: [
    { id: 'party_name', type: 'text', label: 'Your Name', required: true },
  ],
  total_steps: 2,
};

const mockGetProfile = jest.fn();
const mockCreate = jest.fn();
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
    saveDraft: (...args: any[]) => mockSaveDraft(...args),
    getDrafts: (...args: any[]) => mockGetDrafts(...args),
    processWithLLM: (...args: any[]) => mockProcessWithLLM(...args),
  },
  intakeAPI: {
    getQuestions: (...args: any[]) => mockGetQuestions(...args),
    evaluateCondition: (...args: any[]) => mockEvaluateCondition(...args),
  },
}));

function deferred<T>() {
  let resolve!: (value: T) => void;
  const promise = new Promise<T>((r) => {
    resolve = r;
  });
  return { promise, resolve };
}

const renderWithRouter = () => render(<BrowserRouter><GuidedIntake /></BrowserRouter>);

describe('GuidedIntake prefill ordering', () => {
  beforeEach(() => {
    jest.clearAllMocks();
    mockParams = { motionType: 'FL_300' };
    mockCreate.mockResolvedValue({ id: 'motion-123' });
    mockGetDrafts.mockResolvedValue([]);
    mockSaveDraft.mockResolvedValue({ success: true });
    mockProcessWithLLM.mockResolvedValue({ success: true });
    mockGetQuestions.mockResolvedValue({ data: STEP_1 });
    mockEvaluateCondition.mockResolvedValue({ data: { result: true } });
    mockGetProfile.mockResolvedValue(null);
  });

  test('profile autofill survives a slow draft load', async () => {
    mockGetProfile.mockResolvedValue({ party_name: 'Maria Delgado' });
    const draftLoad = deferred<any[]>();
    mockGetDrafts.mockImplementation(() => draftLoad.promise);

    renderWithRouter();

    await waitFor(() => expect(mockGetDrafts).toHaveBeenCalled());
    // Give the prefill effect the window the live race had (L12), then
    // let the draft load finish — the autofilled value must survive it.
    await act(async () => {});
    await act(async () => {
      draftLoad.resolve([]);
    });

    const input = await screen.findByLabelText(/Your Name/i);
    expect((input as HTMLInputElement).value).toBe('Maria Delgado');
    expect(screen.getByText(/Filled from your profile/i)).toBeInTheDocument();
  });

  test('served-motion prefill survives the step reset', async () => {
    mockParams = { motionType: 'FL-320' };
    mockGetQuestions.mockImplementation((_formType: string, step?: number) =>
      Promise.resolve({ data: step === 2 ? STEP_2_OTHER_PARTY : STEP_1 })
    );
    mockParseServedMotion.mockResolvedValue({
      success: true,
      extracted: {
        other_party_requests: 'Sole legal custody and a new visitation schedule.',
      },
      notice: null,
    });
    // Step-1 drafts resolve immediately; step-2 drafts are held open so the
    // prefill effect fires while the draft load is still in flight (the L9 race)
    const step2Drafts = deferred<any[]>();
    mockGetDrafts
      .mockResolvedValueOnce([])
      .mockImplementation(() => step2Drafts.promise);

    renderWithRouter();

    const fileInput = await screen.findByLabelText(/Upload the motion/i);
    fireEvent.change(fileInput, {
      target: { files: [new File(['pdf'], 'served.pdf', { type: 'application/pdf' })] },
    });

    const nameInput = await screen.findByLabelText(/Your Name/i);
    fireEvent.change(nameInput, { target: { value: 'Rosa Martinez' } });
    fireEvent.click(screen.getByRole('button', { name: /next/i }));

    await waitFor(() => expect(mockGetDrafts).toHaveBeenCalledTimes(2));
    await act(async () => {});
    await act(async () => {
      step2Drafts.resolve([]);
    });

    const textarea = await screen.findByLabelText(/What is the other party asking/i);
    expect((textarea as HTMLTextAreaElement).value).toBe(
      'Sole legal custody and a new visitation schedule.'
    );
    expect(screen.getByText(/Filled from your uploaded motion/i)).toBeInTheDocument();
  });

  test('profile badge clears on a step whose fields were not autofilled', async () => {
    mockGetProfile.mockResolvedValue({ party_name: 'Maria Delgado' });
    mockGetQuestions.mockImplementation((_formType: string, step?: number) =>
      Promise.resolve({ data: step === 2 ? STEP_2_REVISITS_NAME : STEP_1 })
    );
    // Step 2 already has a user-typed draft — nothing left to autofill there
    mockGetDrafts.mockResolvedValue([
      {
        step_number: 2,
        step_name: 'Confirm Details',
        question_data: { party_name: 'Typed Name' },
      },
    ]);

    renderWithRouter();

    const input = await screen.findByLabelText(/Your Name/i);
    await waitFor(() => expect((input as HTMLInputElement).value).toBe('Maria Delgado'));
    expect(screen.getByText(/Filled from your profile/i)).toBeInTheDocument();

    fireEvent.click(screen.getByRole('button', { name: /next/i }));

    await screen.findByText('Confirm Details');
    const step2Input = screen.getByLabelText(/Your Name/i);
    await waitFor(() => expect((step2Input as HTMLInputElement).value).toBe('Typed Name'));
    expect(screen.queryByText(/Filled from your profile/i)).not.toBeInTheDocument();
  });
});
