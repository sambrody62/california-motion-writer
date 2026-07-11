/**
 * Tests for the ViolationIntake result screen (track determination display,
 * forms list, courthouse routing, declaration copy). Wizard behaviour is
 * covered in ViolationIntake.test.tsx.
 */
import React from 'react';
import { render, screen, waitFor, fireEvent } from '@testing-library/react';
import '@testing-library/jest-dom';
import { BrowserRouter } from 'react-router-dom';
import {
  MOCK_INTAKE_QUESTIONS,
  MOCK_TRACKS,
  MOCK_PROCESS_RESULT,
} from '../violation/__fixtures__/violationIntakeFixtures';

// --- Mocks ---

const mockNavigate = jest.fn();

jest.mock('react-router-dom', () => ({
  ...jest.requireActual('react-router-dom'),
  useNavigate: () => mockNavigate,
}));

// Module-level mock functions — safe against jest.clearAllMocks()
const mockGetIntakeQuestions = jest.fn();
const mockGetTracks = jest.fn();
const mockProcess = jest.fn();
const mockGenerateDeclaration = jest.fn();

jest.mock('../../services/api', () => ({
  violationAPI: {
    getIntakeQuestions: (...args: any[]) => mockGetIntakeQuestions(...args),
    getTracks: (...args: any[]) => mockGetTracks(...args),
    process: (...args: any[]) => mockProcess(...args),
    generateDeclaration: (...args: any[]) => mockGenerateDeclaration(...args),
  },
}));

const renderWithRouter = (ui: React.ReactElement) =>
  render(<BrowserRouter>{ui}</BrowserRouter>);

// Lazy import after mocks are established
let ViolationIntake: React.FC;

beforeAll(async () => {
  const mod = await import('../violation/ViolationIntake');
  ViolationIntake = mod.ViolationIntake;
});

const advanceToResult = async () => {
  renderWithRouter(<ViolationIntake />);

  await waitFor(() => {
    expect(screen.getByText('Order & Urgency')).toBeInTheDocument();
  });
  fireEvent.click(screen.getByRole('button', { name: /Next/i }));

  await waitFor(() => {
    expect(screen.getByText('What Happened')).toBeInTheDocument();
  });
  fireEvent.click(screen.getByRole('button', { name: /Next/i }));

  await waitFor(() => {
    expect(screen.getByRole('button', { name: /Submit/i })).toBeInTheDocument();
  });
  fireEvent.click(screen.getByRole('button', { name: /Submit/i }));

  // Wait for the result screen — use a unique element only present there
  await waitFor(() => {
    expect(screen.getByText(/Based on your answers, this matches the/i)).toBeInTheDocument();
  });
};

describe('ViolationIntake result screen', () => {
  beforeEach(() => {
    jest.clearAllMocks();
    mockGetIntakeQuestions.mockResolvedValue(MOCK_INTAKE_QUESTIONS);
    mockGetTracks.mockResolvedValue(MOCK_TRACKS);
    mockProcess.mockResolvedValue(MOCK_PROCESS_RESULT);
    mockGenerateDeclaration.mockResolvedValue({
      success: true,
      declaration: 'Enhanced declaration text...',
    });
  });

  test('result screen shows determined track name', async () => {
    await advanceToResult();
    // Track name appears multiple times in the result screen
    expect(screen.getAllByText(/Regular RFO/i).length).toBeGreaterThan(0);
  });

  test('result screen uses neutral informational language, not directive', async () => {
    await advanceToResult();
    // Must contain neutral framing
    expect(
      screen.getByText(/Based on your answers, this matches the/i)
    ).toBeInTheDocument();
    // Must NOT contain directive language
    expect(screen.queryByText(/you should file/i)).not.toBeInTheDocument();
  });

  test('result screen shows all three tracks for comparison', async () => {
    await advanceToResult();
    expect(screen.getByText(/Emergency \(Ex Parte\)/i)).toBeInTheDocument();
    expect(screen.getAllByText(/Regular RFO/i).length).toBeGreaterThan(0);
    expect(screen.getByText(/Contempt of Court/i)).toBeInTheDocument();
  });

  test('result screen lists required forms', async () => {
    await advanceToResult();
    // Form names may appear in multiple places (forms list + declaration text)
    expect(screen.getAllByText(/Request for Order/i).length).toBeGreaterThan(0);
    expect(screen.getAllByText(/Declaration/i).length).toBeGreaterThan(0);
  });

  test('result screen shows courthouse routing', async () => {
    await advanceToResult();
    expect(screen.getByText(/San Diego Family Court/i)).toBeInTheDocument();
  });

  test('result screen shows declaration text', async () => {
    await advanceToResult();
    expect(
      screen.getByText(/DECLARATION IN SUPPORT OF REQUEST FOR ORDER/i)
    ).toBeInTheDocument();
  });

  test('copy button is present for declaration', async () => {
    await advanceToResult();
    expect(
      screen.getByRole('button', { name: /Copy Declaration/i })
    ).toBeInTheDocument();
  });

  test('copy button calls clipboard API', async () => {
    const writeText = jest.fn().mockResolvedValue(undefined);
    Object.defineProperty(navigator, 'clipboard', {
      value: { writeText },
      configurable: true,
    });

    await advanceToResult();
    fireEvent.click(screen.getByRole('button', { name: /Copy Declaration/i }));

    await waitFor(() => {
      expect(writeText).toHaveBeenCalledWith(
        expect.stringContaining('DECLARATION IN SUPPORT')
      );
    });
  });

  // POST /violations/process responses gain a top-level `corrections` list
  // (fact gate, real-LLM findings L4/L7). Same unwrapped correction shape as
  // motions' fact_check.corrections.
  const MOCK_CORRECTIONS = [
    {
      type: 'date',
      severity: 'corrected',
      section: 'Declaration',
      original: 'June 22',
      replacement: null,
      message: 'We removed a June 22 date you did not enter.',
    },
    {
      type: 'quantifier_flag',
      severity: 'needs_review',
      section: 'Declaration',
      original: 'multiple occasions',
      replacement: null,
      message: 'The draft says "multiple" call attempts — confirm this matches what happened.',
    },
  ];

  test('renders corrections above the declaration when the process response includes them', async () => {
    mockProcess.mockResolvedValue({ ...MOCK_PROCESS_RESULT, corrections: MOCK_CORRECTIONS });

    await advanceToResult();

    expect(screen.getByText(/We corrected or flagged 2 details/i)).toBeInTheDocument();
    expect(screen.getByText(/We removed a June 22 date you did not enter/i)).toBeInTheDocument();
    expect(
      screen.getByText(/confirm this matches what happened/i)
    ).toBeInTheDocument();

    // The corrections banner precedes the declaration draft in the document
    const banner = screen.getByText(/We corrected or flagged 2 details/i);
    const declarationHeading = screen.getByRole('heading', { name: /Declaration Draft/i });
    expect(
      banner.compareDocumentPosition(declarationHeading) & Node.DOCUMENT_POSITION_FOLLOWING
    ).toBeTruthy();
  });

  test('no corrections banner when the response has an empty corrections list', async () => {
    mockProcess.mockResolvedValue({ ...MOCK_PROCESS_RESULT, corrections: [] });

    await advanceToResult();

    expect(screen.queryByText(/We corrected or flagged/i)).not.toBeInTheDocument();
  });

  test('no corrections banner when the response has no corrections field', async () => {
    await advanceToResult();

    expect(screen.queryByText(/We corrected or flagged/i)).not.toBeInTheDocument();
  });
});
