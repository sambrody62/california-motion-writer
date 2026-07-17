/**
 * GuidedIntake paywall: a 402 from LLM processing opens the paywall modal and
 * stops navigation; other errors keep the existing llmFailed fallback.
 */
import React from 'react';
import { render, screen, waitFor, fireEvent } from '@testing-library/react';
import '@testing-library/jest-dom';
import { BrowserRouter } from 'react-router-dom';
import { GuidedIntake } from '../motion/GuidedIntake';

const mockNavigate = jest.fn();

jest.mock('react-router-dom', () => ({
  ...jest.requireActual('react-router-dom'),
  useNavigate: () => mockNavigate,
  useParams: () => ({ motionType: 'FL_300', formType: undefined }),
  useLocation: () => ({ state: null, pathname: '/' }),
}));

jest.mock('../../services/servedMotionApi', () => ({
  servedMotionAPI: { parse: jest.fn() },
}));

jest.mock('../../types/forms', () => ({
  FORM_METADATA: { FL_300: { name: 'Request for Order', id: 'FL-300' } },
  FORM_TYPES: { FL_300: 'FL_300' },
  FormType: {},
}));

const MOCK_STEP_DATA = {
  step_number: 1,
  step_name: 'Case Information',
  description: 'Basic case info',
  questions: [{ id: 'party_name', type: 'text', label: 'Your Name', required: true }],
  total_steps: 1,
};

const mockGetProfile = jest.fn();
const mockCreate = jest.fn();
const mockSaveDraft = jest.fn();
const mockGetDrafts = jest.fn();
const mockProcessWithLLM = jest.fn();
const mockGetQuestions = jest.fn();
const mockEvaluateCondition = jest.fn();
const mockCreateCheckoutSession = jest.fn();

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

jest.mock('../../services/billing', () => ({
  billingAPI: {
    createCheckoutSession: (...args: any[]) => mockCreateCheckoutSession(...args),
  },
  isPaywallError: (error: any) => error?.response?.status === 402,
}));

const assignMock = jest.fn();
const originalLocation = window.location;

beforeAll(() => {
  delete (window as any).location;
  (window as any).location = { ...originalLocation, assign: assignMock };
});

afterAll(() => {
  (window as any).location = originalLocation;
});

const renderWithRouter = () => render(<BrowserRouter><GuidedIntake /></BrowserRouter>);

const submitFinalStep = async () => {
  const input = await screen.findByLabelText(/Your Name/i);
  fireEvent.change(input, { target: { value: 'Jane Doe' } });
  fireEvent.click(screen.getByRole('button', { name: /complete/i }));
};

describe('GuidedIntake paywall', () => {
  beforeEach(() => {
    jest.clearAllMocks();
    mockCreate.mockResolvedValue({ id: 'motion-123' });
    mockGetDrafts.mockResolvedValue([]);
    mockSaveDraft.mockResolvedValue({ success: true });
    mockGetQuestions.mockResolvedValue({ data: MOCK_STEP_DATA });
    mockEvaluateCondition.mockResolvedValue({ data: { result: true } });
    mockGetProfile.mockResolvedValue(null);
  });

  test('402 opens the paywall modal and does not navigate', async () => {
    mockProcessWithLLM.mockRejectedValue({ response: { status: 402 } });
    renderWithRouter();
    await submitFinalStep();

    expect(await screen.findByText(/60-day money-back guarantee/i)).toBeInTheDocument();
    expect(mockNavigate).not.toHaveBeenCalled();
  });

  test('subscribe from the intake paywall returns to the final step', async () => {
    mockProcessWithLLM.mockRejectedValue({ response: { status: 402 } });
    mockCreateCheckoutSession.mockResolvedValue({ url: 'https://checkout.stripe.com/x' });
    renderWithRouter();
    await submitFinalStep();

    fireEvent.click(await screen.findByRole('button', { name: /subscribe/i }));

    await waitFor(() => {
      expect(mockCreateCheckoutSession).toHaveBeenCalledWith('/motion/motion-123/edit/1');
    });
  });

  test('non-402 errors keep the llmFailed fallback to preview', async () => {
    mockProcessWithLLM.mockRejectedValue(new Error('llm exploded'));
    renderWithRouter();
    await submitFinalStep();

    await waitFor(() => {
      expect(mockNavigate).toHaveBeenCalledWith('/motion/motion-123/preview', {
        state: { llmFailed: true },
      });
    });
    expect(screen.queryByText(/60-day money-back guarantee/i)).toBeNull();
  });
});
