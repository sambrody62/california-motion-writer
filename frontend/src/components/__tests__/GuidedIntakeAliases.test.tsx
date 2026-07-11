/**
 * Tests for the response/rfo route aliases (/motion/new/response,
 * /motion/new/rfo). Regression for real-LLM browser finding L16: 'response'
 * created a motion with a type no form template can render, leaving the
 * wizard in a perpetual "We couldn't load this step" state.
 */
import React from 'react';
import { render, screen, waitFor } from '@testing-library/react';
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

jest.mock('../../services/servedMotionApi', () => ({
  servedMotionAPI: { parse: jest.fn() },
}));

jest.mock('../../types/forms', () => ({
  FORM_METADATA: {
    'FL-300': { name: 'Request for Order', id: 'FL-300' },
    'FL-320': { name: 'Responsive Declaration', id: 'FL-320' },
  },
  FORM_TYPES: { FL_300: 'FL-300', FL_320: 'FL-320' },
  FormType: {},
}));

const STEP_1 = {
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

describe('GuidedIntake route aliases', () => {
  beforeEach(() => {
    jest.clearAllMocks();
    mockCreate.mockResolvedValue({ id: 'motion-123' });
    mockGetDrafts.mockResolvedValue([]);
    mockSaveDraft.mockResolvedValue({ success: true });
    mockProcessWithLLM.mockResolvedValue({ success: true });
    mockGetQuestions.mockResolvedValue({ data: STEP_1 });
    mockEvaluateCondition.mockResolvedValue({ data: { result: true } });
    mockGetProfile.mockResolvedValue(null);
  });

  test("param 'response' maps to FL-320: upload gate renders and the motion is created as FL-320", async () => {
    mockParams = { motionType: 'response' };

    renderWithRouter();

    expect(await screen.findByText(/motion you were served/i)).toBeInTheDocument();
    await waitFor(() =>
      expect(mockCreate).toHaveBeenCalledWith(
        expect.objectContaining({ motion_type: 'FL-320' })
      )
    );
  });

  test("param 'RFO' maps to FL-300: motion created and template looked up as FL-300", async () => {
    mockParams = { motionType: 'RFO' };

    renderWithRouter();

    await screen.findByLabelText(/Your Name/i);
    expect(mockCreate).toHaveBeenCalledWith(
      expect.objectContaining({ motion_type: 'FL-300' })
    );
    expect(mockGetQuestions).toHaveBeenCalledWith('FL-300', 1);
  });
});
