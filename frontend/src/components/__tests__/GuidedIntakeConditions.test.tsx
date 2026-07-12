/**
 * Cross-step conditional questions: an answer saved on an earlier step must
 * still satisfy a later step's condition. Since 871cafa the draft reset fires
 * while the previous step's fields are still mounted, so they re-register
 * blank values that shadow the accumulated answers when the condition context
 * is built. Caught by real-LLM browser verification (FL-300 step 4).
 *
 * Unlike the other intake suites, evaluateCondition here calls through to the
 * REAL evaluator — an always-true stub cannot catch this bug.
 */
import React from 'react';
import { render, screen, waitFor, fireEvent, act } from '@testing-library/react';
import '@testing-library/jest-dom';
import { BrowserRouter } from 'react-router-dom';
import { GuidedIntake } from '../motion/GuidedIntake';

const { evalCondition } = jest.requireActual('../../utils/conditionEval');

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

const STEP_1_CHILDREN = {
  step_number: 1,
  step_name: 'About Your Children',
  description: 'Tell us about your children',
  questions: [
    {
      id: 'has_children',
      type: 'radio',
      label: 'Do you and the other party have children together?',
      required: true,
      options: ['Yes', 'No'],
    },
  ],
  total_steps: 2,
};

const STEP_2_ORDERS = {
  step_number: 2,
  step_name: 'Orders Requested',
  description: 'What orders are you asking for?',
  questions: [
    {
      id: 'orders_summary',
      type: 'text',
      label: 'Summarize the orders you want',
      required: true,
    },
    {
      id: 'child_support_request',
      type: 'textarea',
      label: 'Are you requesting child support?',
      required: false,
      condition: 'has_children == "Yes"',
    },
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

// Answer step 1 and advance. The step-2 draft load is deferred past the
// loading-spinner commit — as under real network latency — so step 1's radio
// unmounts before reset() and re-registers blank afterwards (the live repro).
const answerStep1AndAdvance = async (answer: 'Yes' | 'No') => {
  const step2Drafts = deferred<any[]>();
  mockGetDrafts
    .mockResolvedValueOnce([])
    .mockImplementation(() => step2Drafts.promise);

  renderWithRouter();
  fireEvent.click(await screen.findByRole('radio', { name: answer }));
  fireEvent.click(screen.getByRole('button', { name: /next/i }));

  await waitFor(() => expect(mockGetDrafts).toHaveBeenCalledTimes(2));
  // Flush the loading-spinner render (step-1 fields unmount), then let the
  // draft load land — reset() now fires with the answer only in allAnswers
  await act(async () => {});
  await act(async () => {
    step2Drafts.resolve([
      {
        step_number: 1,
        step_name: 'About Your Children',
        question_data: { has_children: answer },
      },
    ]);
  });

  await screen.findByText('Orders Requested');
  await screen.findByLabelText(/Summarize the orders/i);
  // Let any trailing condition re-evaluation settle
  await act(async () => {});
};

describe('GuidedIntake cross-step conditional questions', () => {
  beforeEach(() => {
    jest.clearAllMocks();
    mockParams = { motionType: 'FL_300' };
    mockCreate.mockResolvedValue({ id: 'motion-123' });
    mockGetProfile.mockResolvedValue(null);
    mockSaveDraft.mockResolvedValue({ success: true });
    mockProcessWithLLM.mockResolvedValue({ success: true });
    mockGetQuestions.mockImplementation((_formType: string, step?: number) =>
      Promise.resolve({ data: step === 2 ? STEP_2_ORDERS : STEP_1_CHILDREN })
    );
    // Wire the mock through the real evaluator — a stub that always returns
    // true is exactly the test gap that let this regression ship
    mockEvaluateCondition.mockImplementation(
      (condition: string, context: Record<string, any>) =>
        Promise.resolve({ data: { result: evalCondition(condition, context) } })
    );
  });

  test('answering Yes on step 1 shows the conditional question on step 2', async () => {
    await answerStep1AndAdvance('Yes');

    expect(
      await screen.findByLabelText(/Are you requesting child support/i)
    ).toBeInTheDocument();
  });

  test('answering No on step 1 keeps the conditional question hidden on step 2', async () => {
    await answerStep1AndAdvance('No');

    expect(
      screen.queryByLabelText(/Are you requesting child support/i)
    ).not.toBeInTheDocument();
  });
});
