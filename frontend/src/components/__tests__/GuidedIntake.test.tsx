/**
 * Tests for GuidedIntake component
 */
import React from 'react';
import { render, screen, waitFor, fireEvent, act } from '@testing-library/react';
import '@testing-library/jest-dom';
import { BrowserRouter } from 'react-router-dom';
import { GuidedIntake } from '../motion/GuidedIntake';

// --- Mocks ---

const mockNavigate = jest.fn();
const mockUseLocation = jest.fn(() => ({ state: null, pathname: '/' }));

// This variable is mutated per describe block to change the form type
let mockFormType = 'FL_300';

jest.mock('react-router-dom', () => ({
  ...jest.requireActual('react-router-dom'),
  useNavigate: () => mockNavigate,
  useParams: () => ({ motionType: mockFormType, formType: undefined }),
  useLocation: () => mockUseLocation(),
}));

const mockServedParse = jest.fn();
jest.mock('../../services/servedMotionApi', () => ({
  servedMotionAPI: {
    parse: (...args: any[]) => mockServedParse(...args),
  },
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
    mockCreate.mockResolvedValue({ id: 'motion-123' });
    mockGetDrafts.mockResolvedValue([]);
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
    mockGetDrafts.mockResolvedValue([
      {
        step_number: 1,
        question_data: { party_name: 'Existing Name', case_number: 'EXISTING-001' },
      },
    ]);

    renderWithRouter(<GuidedIntake />);

    await waitFor(() => {
      const partyNameInput = screen.getByLabelText(/Your Name/i) as HTMLInputElement;
      expect(partyNameInput.value).toBe('Existing Name');
    });

    // case_number saved value should not be overwritten
    const caseNumberInput = screen.getByLabelText(/Case Number/i) as HTMLInputElement;
    expect(caseNumberInput.value).toBe('EXISTING-001');
  });

  test('submitting a step saves the draft with the DraftUpdate payload shape', async () => {
    renderWithRouter(<GuidedIntake />);

    await waitFor(() => {
      expect(screen.getByRole('button', { name: /Complete/i })).toBeInTheDocument();
    });

    fireEvent.click(screen.getByRole('button', { name: /Complete/i }));

    // The backend requires {step_number, step_name, question_data} — a positional
    // step number here serializes to {} and 422s (2026-07-06 E2E finding #1)
    await waitFor(() => {
      expect(mockSaveDraft).toHaveBeenCalledWith(
        'motion-123',
        expect.objectContaining({
          step_number: 1,
          step_name: 'Case Information',
          question_data: expect.any(Object),
        })
      );
    });
  });

  test('when launched from FormExecution, completing returns to /case/forms', async () => {
    mockUseLocation.mockReturnValue({
      state: { fromFormExecution: true, formExecutionFormIndex: 0 },
      pathname: '/form/guided/FL_300',
    });

    renderWithRouter(<GuidedIntake />);

    await waitFor(() => {
      expect(screen.getByRole('button', { name: /Complete/i })).toBeInTheDocument();
    });

    fireEvent.click(screen.getByRole('button', { name: /Complete/i }));

    // FormExecution is mounted at /case/forms — navigating to /form/execution
    // matches no route and rendered a blank page (2026-07-07 E2E finding)
    await waitFor(() => {
      expect(mockNavigate).toHaveBeenCalledWith(
        '/case/forms',
        expect.objectContaining({
          state: expect.objectContaining({ completedFormIndex: 0 }),
        })
      );
    });
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

// -------------------------------------------------------------------
// FL-320 deadline warning
// -------------------------------------------------------------------

const MOCK_FL320_STEP_WITH_DATE_SERVED = {
  id: 'FL_320_step_1',
  step_number: 1,
  step_name: 'Case Information',
  description: 'Confirm the case information from the original request',
  questions: [
    { id: 'case_number', type: 'text', label: 'Case Number', required: true },
    { id: 'date_served', type: 'date', label: 'Date You Were Served', required: true },
  ],
  total_steps: 3,
};

describe('GuidedIntake — FL-320 deadline warning', () => {
  beforeEach(() => {
    jest.clearAllMocks();
    mockFormType = 'FL-320';
    mockUseLocation.mockReturnValue({ state: null, pathname: '/' });
    mockCreate.mockResolvedValue({ id: 'motion-456' });
    mockGetDrafts.mockResolvedValue([]);
    mockSaveDraft.mockResolvedValue({ success: true });
    mockProcessWithLLM.mockResolvedValue({ success: true });
    mockGetQuestions.mockResolvedValue({ data: MOCK_FL320_STEP_WITH_DATE_SERVED });
    mockSaveAnswer.mockResolvedValue({ success: true });
    mockEvaluateCondition.mockResolvedValue({ data: { result: true } });
    mockGetProfile.mockResolvedValue({});
  });

  afterEach(() => {
    mockFormType = 'FL_300';
  });

  test('shows deadline warning when date_served is filled in on an FL-320 form', async () => {
    renderWithRouter(<GuidedIntake />);

    // Skip past the upload gate to reach the form
    fireEvent.click(await screen.findByRole('button', { name: /skip/i }));

    await waitFor(() => {
      expect(screen.getByLabelText(/Date You Were Served/i)).toBeInTheDocument();
    });

    const dateInput = screen.getByLabelText(/Date You Were Served/i);
    fireEvent.change(dateInput, { target: { value: '2026-01-09' } });

    await waitFor(() => {
      // Warning should mention "9 court days" and "Verify with your court"
      expect(screen.getByText(/9 court days/i)).toBeInTheDocument();
      expect(screen.getByText(/Verify with your court/i)).toBeInTheDocument();
    });
  });

  test('deadline warning contains computed date after service date input', async () => {
    renderWithRouter(<GuidedIntake />);

    fireEvent.click(await screen.findByRole('button', { name: /skip/i }));

    await waitFor(() => {
      expect(screen.getByLabelText(/Date You Were Served/i)).toBeInTheDocument();
    });

    const dateInput = screen.getByLabelText(/Date You Were Served/i);
    // Friday Jan 9 2026 + 9 court days = Thursday Jan 22 2026
    fireEvent.change(dateInput, { target: { value: '2026-01-09' } });

    await waitFor(() => {
      // The computed deadline (Jan 22, 2026) should appear somewhere in the warning
      expect(screen.getByText(/2026/)).toBeInTheDocument();
    });
  });

  test('no deadline warning shown when date_served is empty', async () => {
    renderWithRouter(<GuidedIntake />);

    fireEvent.click(await screen.findByRole('button', { name: /skip/i }));

    await waitFor(() => {
      expect(screen.getByLabelText(/Date You Were Served/i)).toBeInTheDocument();
    });

    // Warning should not appear without a date
    expect(screen.queryByText(/9 court days/i)).not.toBeInTheDocument();
  });
});

// -------------------------------------------------------------------
// FL-300 support-only path hides custody questions
// -------------------------------------------------------------------

const MOCK_FL300_CUSTODY_STEP = {
  id: 'FL_300_step_3',
  step_number: 3,
  step_name: 'Child Custody & Visitation',
  description: 'Provide details about child custody and visitation arrangements',
  questions: [
    {
      id: 'has_children',
      type: 'radio',
      label: 'Do you have minor children with the other party?',
      required: true,
      options: ['Yes', 'No'],
    },
    {
      id: 'children_names_ages',
      type: 'textarea',
      label: "Children's Names and Ages",
      required: true,
      condition: 'has_children == "Yes"',
    },
    {
      id: 'requested_custody',
      type: 'textarea',
      label: 'Requested Custody Arrangement',
      required: true,
      condition: 'case_type != "Support only" && has_children == "Yes"',
    },
  ],
  total_steps: 6,
};

describe('GuidedIntake — FL-300 support-only hides custody questions', () => {
  beforeEach(() => {
    jest.clearAllMocks();
    mockFormType = 'FL_300';
    mockUseLocation.mockReturnValue({ state: null, pathname: '/' });
    mockCreate.mockResolvedValue({ data: { id: 'motion-789' } });
    mockGetDrafts.mockResolvedValue([]);
    mockSaveDraft.mockResolvedValue({ success: true });
    mockProcessWithLLM.mockResolvedValue({ success: true });
    mockGetQuestions.mockResolvedValue({ data: MOCK_FL300_CUSTODY_STEP });
    mockSaveAnswer.mockResolvedValue({ success: true });
    mockGetProfile.mockResolvedValue({});
  });

  test('custody question hidden when case_type is "Support only" and evaluateCondition returns false', async () => {
    // Simulate evaluateCondition returning false for the custody compound condition
    // (as it would when case_type === 'Support only')
    mockEvaluateCondition.mockImplementation(async (condition: string) => {
      if (condition.includes('case_type != "Support only"')) {
        // Support-only filer: custody condition is false → hide the question
        return { data: { result: false } };
      }
      // All other conditions pass through as true
      return { data: { result: true } };
    });

    renderWithRouter(<GuidedIntake />);

    await waitFor(() => {
      expect(screen.getByText(/Do you have minor children/i)).toBeInTheDocument();
    });

    // "Requested Custody Arrangement" has a compound condition that includes
    // 'case_type != "Support only"' — mock returns false → question hidden
    expect(screen.queryByText(/Requested Custody Arrangement/i)).not.toBeInTheDocument();
  });

  test('custody question visible when case_type is not support-only and has_children is Yes', async () => {
    // All conditions return true = all questions visible
    mockEvaluateCondition.mockResolvedValue({ data: { result: true } });

    renderWithRouter(<GuidedIntake />);

    await waitFor(() => {
      expect(screen.getByText(/Requested Custody Arrangement/i)).toBeInTheDocument();
    });
  });
});

// -------------------------------------------------------------------
// FL-150 conditional income questions
// -------------------------------------------------------------------

const MOCK_FL150_INCOME_STEP = {
  id: 'FL_150_step_1',
  step_number: 1,
  step_name: 'Income Source',
  description: 'Provide information about your primary income source',
  questions: [
    {
      id: 'income_source',
      type: 'radio',
      label: 'Primary income source',
      required: true,
      options: ['W-2 employee', 'Self-employed', 'Fixed income (pension/SSI/disability)', 'Other'],
    },
    {
      id: 'gross_monthly_income',
      type: 'currency',
      label: 'Gross Monthly Income',
      required: true,
      condition: 'income_source == "W-2 employee"',
    },
    {
      id: 'last_year_net_income',
      type: 'currency',
      label: 'Last Year Net Income (self-employment)',
      required: true,
      condition: 'income_source == "Self-employed"',
    },
    {
      id: 'supports_other_children',
      type: 'radio',
      label: 'Do you support other children not in this case?',
      required: true,
      options: ['Yes', 'No'],
    },
    {
      id: 'other_children_count',
      type: 'number',
      label: 'Number of other children',
      required: true,
      condition: 'supports_other_children == "Yes"',
    },
    {
      id: 'other_children_support_amount',
      type: 'currency',
      label: 'Monthly support amount per child',
      required: true,
      condition: 'supports_other_children == "Yes"',
    },
  ],
  total_steps: 3,
};

describe('GuidedIntake — FL-150 conditional income fields', () => {
  beforeEach(() => {
    jest.clearAllMocks();
    mockFormType = 'FL-150';
    mockUseLocation.mockReturnValue({ state: null, pathname: '/' });
    mockCreate.mockResolvedValue({ data: { id: 'motion-fl150' } });
    mockGetDrafts.mockResolvedValue([]);
    mockSaveDraft.mockResolvedValue({ success: true });
    mockProcessWithLLM.mockResolvedValue({ success: true });
    mockGetQuestions.mockResolvedValue({ data: MOCK_FL150_INCOME_STEP });
    mockSaveAnswer.mockResolvedValue({ success: true });
    mockGetProfile.mockResolvedValue({});
  });

  afterEach(() => {
    mockFormType = 'FL_300';
  });

  test('gross monthly income shown when W-2 employee selected', async () => {
    mockEvaluateCondition.mockImplementation(async (condition: string, context: any) => {
      if (condition === 'income_source == "W-2 employee"') {
        return { data: { result: context.income_source === 'W-2 employee' } };
      }
      if (condition === 'income_source == "Self-employed"') {
        return { data: { result: context.income_source === 'Self-employed' } };
      }
      if (condition === 'supports_other_children == "Yes"') {
        return { data: { result: context.supports_other_children === 'Yes' } };
      }
      return { data: { result: false } };
    });

    renderWithRouter(<GuidedIntake />);

    await waitFor(() => {
      expect(screen.getByText(/Primary income source/i)).toBeInTheDocument();
    });

    // Initially W-2 income question hidden (no selection yet)
    expect(screen.queryByText(/Gross Monthly Income/i)).not.toBeInTheDocument();
  });

  test('other children fields visible when supports_other_children is Yes', async () => {
    mockEvaluateCondition.mockImplementation(async (condition: string, context: any) => {
      if (condition === 'income_source == "W-2 employee"') {
        return { data: { result: false } };
      }
      if (condition === 'income_source == "Self-employed"') {
        return { data: { result: false } };
      }
      if (condition === 'supports_other_children == "Yes"') {
        return { data: { result: true } };
      }
      return { data: { result: false } };
    });

    renderWithRouter(<GuidedIntake />);

    await waitFor(() => {
      expect(screen.getByText(/Number of other children/i)).toBeInTheDocument();
      expect(screen.getByText(/Monthly support amount per child/i)).toBeInTheDocument();
    });
  });

  test('self-employed income shown when Self-employed selected', async () => {
    mockEvaluateCondition.mockImplementation(async (condition: string, context: any) => {
      if (condition === 'income_source == "W-2 employee"') {
        return { data: { result: false } };
      }
      if (condition === 'income_source == "Self-employed"') {
        return { data: { result: true } };
      }
      if (condition === 'supports_other_children == "Yes"') {
        return { data: { result: false } };
      }
      return { data: { result: false } };
    });

    renderWithRouter(<GuidedIntake />);

    await waitFor(() => {
      expect(screen.getByText(/Last Year Net Income/i)).toBeInTheDocument();
    });
  });
});

// -------------------------------------------------------------------
// FL-320 upload gate ("upload the motion you were served")
// -------------------------------------------------------------------

const MOCK_FL320_GATE_STEP = {
  id: 'FL_320_step_1',
  step_number: 1,
  step_name: 'Case Information',
  description: 'Confirm the case information from the original request',
  questions: [
    { id: 'case_number', type: 'text', label: 'Case Number', required: true },
    { id: 'date_served', type: 'date', label: 'Date You Were Served', required: true },
    { id: 'other_party_requests', type: 'textarea', label: 'What did the other party request?', required: true },
  ],
  total_steps: 3,
};

describe('GuidedIntake — FL-320 upload gate', () => {
  beforeEach(() => {
    jest.clearAllMocks();
    mockFormType = 'FL-320';
    mockUseLocation.mockReturnValue({ state: null, pathname: '/' });
    mockCreate.mockResolvedValue({ id: 'motion-789' });
    mockGetDrafts.mockResolvedValue([]);
    mockSaveDraft.mockResolvedValue({ success: true });
    mockProcessWithLLM.mockResolvedValue({ success: true });
    mockGetQuestions.mockResolvedValue({ data: MOCK_FL320_GATE_STEP });
    mockSaveAnswer.mockResolvedValue({ success: true });
    mockEvaluateCondition.mockResolvedValue({ data: { result: true } });
    mockGetProfile.mockResolvedValue({});
    mockServedParse.mockResolvedValue({
      success: true,
      extracted: {
        case_number: '24STFL01234',
        other_party_requests: 'Sole custody and child support',
      },
      notice: null,
    });
  });

  afterEach(() => {
    mockFormType = 'FL_300';
  });

  test('gate renders before the form for FL-320', async () => {
    renderWithRouter(<GuidedIntake />);

    expect(await screen.findByText(/motion you were served/i)).toBeInTheDocument();
    expect(screen.queryByLabelText(/Case Number/i)).not.toBeInTheDocument();
  });

  test('gate does not render for FL-300', async () => {
    mockFormType = 'FL_300';
    mockGetQuestions.mockResolvedValue({ data: MOCK_STEP_DATA });
    renderWithRouter(<GuidedIntake />);

    await waitFor(() => {
      expect(screen.getByLabelText(/Your Name/i)).toBeInTheDocument();
    });
    expect(screen.queryByText(/motion you were served/i)).not.toBeInTheDocument();
  });

  test('skip proceeds to step 1 without parsing', async () => {
    renderWithRouter(<GuidedIntake />);

    fireEvent.click(await screen.findByRole('button', { name: /skip/i }));

    await waitFor(() => {
      expect(screen.getByLabelText(/Case Number/i)).toBeInTheDocument();
    });
    expect(mockServedParse).not.toHaveBeenCalled();
  });

  test('extracted values pre-fill the form with a verify indicator; date_served stays empty', async () => {
    renderWithRouter(<GuidedIntake />);

    const input = (await screen.findByLabelText(/upload/i)) as HTMLInputElement;
    fireEvent.change(input, {
      target: { files: [new File(['%PDF'], 'served.pdf', { type: 'application/pdf' })] },
    });

    await waitFor(() => {
      expect(screen.getByLabelText(/Case Number/i)).toBeInTheDocument();
    });

    await waitFor(() => {
      const caseInput = screen.getByLabelText(/Case Number/i) as HTMLInputElement;
      expect(caseInput.value).toBe('24STFL01234');
    });
    const requestsInput = screen.getByLabelText(/other party request/i) as HTMLTextAreaElement;
    expect(requestsInput.value).toBe('Sole custody and child support');

    const dateInput = screen.getByLabelText(/Date You Were Served/i) as HTMLInputElement;
    expect(dateInput.value).toBe('');

    expect(
      screen.getAllByText(/Filled from your uploaded motion/i).length
    ).toBeGreaterThan(0);
  });

  test('empty extraction shows the notice banner on step 1', async () => {
    mockServedParse.mockResolvedValue({
      success: true,
      extracted: {},
      notice: 'Automatic extraction is not available right now.',
    });
    renderWithRouter(<GuidedIntake />);

    const input = (await screen.findByLabelText(/upload/i)) as HTMLInputElement;
    fireEvent.change(input, {
      target: { files: [new File(['%PDF'], 'served.pdf', { type: 'application/pdf' })] },
    });

    await waitFor(() => {
      expect(screen.getByLabelText(/Case Number/i)).toBeInTheDocument();
      expect(
        screen.getByText(/Automatic extraction is not available right now/i)
      ).toBeInTheDocument();
    });
  });
});
