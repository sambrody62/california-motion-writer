/**
 * Tests for GuidedIntake error surfacing (save/load failures must be visible)
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

const renderWithRouter = () => render(<BrowserRouter><GuidedIntake /></BrowserRouter>);

describe('GuidedIntake error surfacing', () => {
  beforeEach(() => {
    jest.clearAllMocks();
    mockCreate.mockResolvedValue({ id: 'motion-123' });
    mockGetDrafts.mockResolvedValue([]);
    mockSaveDraft.mockResolvedValue({ success: true });
    mockProcessWithLLM.mockResolvedValue({ success: true });
    mockGetQuestions.mockResolvedValue({ data: MOCK_STEP_DATA });
    mockEvaluateCondition.mockResolvedValue({ data: { result: true } });
    mockGetProfile.mockResolvedValue(null);
  });

  test('failed draft save shows an inline error and keeps the answers on screen', async () => {
    mockSaveDraft.mockRejectedValue(new Error('network down'));
    renderWithRouter();

    const input = await screen.findByLabelText(/Your Name/i);
    fireEvent.change(input, { target: { value: 'Jane Doe' } });
    fireEvent.click(screen.getByRole('button', { name: /next/i }));

    expect(await screen.findByText(/couldn't save this step/i)).toBeInTheDocument();
    expect((screen.getByLabelText(/Your Name/i) as HTMLInputElement).value).toBe('Jane Doe');
    expect(screen.getByText(/Step 1 of 2/i)).toBeInTheDocument();
    expect(mockNavigate).not.toHaveBeenCalled();
  });

  test('save error clears and the wizard advances once saving succeeds', async () => {
    mockSaveDraft.mockRejectedValueOnce(new Error('network down'));
    renderWithRouter();

    const input = await screen.findByLabelText(/Your Name/i);
    fireEvent.change(input, { target: { value: 'Jane Doe' } });
    fireEvent.click(screen.getByRole('button', { name: /next/i }));
    await screen.findByText(/couldn't save this step/i);

    fireEvent.click(screen.getByRole('button', { name: /next/i }));

    await waitFor(() => expect(screen.getByText(/Step 2 of 2/i)).toBeInTheDocument());
    expect(screen.queryByText(/couldn't save this step/i)).toBeNull();
  });

  test('failed step load shows an error with a working retry', async () => {
    mockGetQuestions.mockRejectedValueOnce(new Error('server error'));
    renderWithRouter();

    expect(await screen.findByText(/couldn't load this step/i)).toBeInTheDocument();

    fireEvent.click(screen.getByRole('button', { name: /try again/i }));

    await waitFor(() => expect(screen.getByLabelText(/Your Name/i)).toBeInTheDocument());
    expect(screen.queryByText(/couldn't load this step/i)).toBeNull();
  });
});
