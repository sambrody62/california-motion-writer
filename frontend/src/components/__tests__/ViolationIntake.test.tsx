/**
 * Tests for ViolationIntake component
 */
import React from 'react';
import { render, screen, waitFor, fireEvent } from '@testing-library/react';
import '@testing-library/jest-dom';
import { BrowserRouter } from 'react-router-dom';

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

// Mock data matching actual backend response shapes

/** GET /violations/intake-questions response */
const MOCK_INTAKE_QUESTIONS = {
  questions: {
    step1: {
      step_number: 1,
      step_name: 'Violation Type',
      description: 'What type of order was violated?',
      questions: [
        {
          id: 'violationType',
          type: 'select',
          label: 'Type of Court Order Violated',
          required: true,
          options: ['Custody/Visitation', 'Child Support', 'Spousal Support', 'Property', 'Restraining Order'],
        },
        {
          id: 'urgency',
          type: 'radio',
          label: 'Is this an emergency situation?',
          required: true,
          options: ['Yes', 'No'],
        },
      ],
    },
    step2: {
      step_number: 2,
      step_name: 'Violation Details',
      description: 'Describe the violation.',
      questions: [
        {
          id: 'violationDescription',
          type: 'textarea',
          label: 'Describe the violation in detail',
          required: true,
          placeholder: 'Explain what happened...',
        },
        {
          id: 'violationDates',
          type: 'text',
          label: 'Date(s) of violation',
          required: true,
          placeholder: 'e.g., January 15, 2026',
        },
      ],
    },
  },
};

/** GET /violations/tracks response */
const MOCK_TRACKS = {
  tracks: [
    {
      id: 'emergency',
      name: 'Emergency (Ex Parte)',
      timeline: '24-48 hours',
      description: 'For situations requiring immediate court intervention.',
      proofStandard: 'Preponderance of evidence',
      requiredForms: ['FL-300', 'FL-303', 'MC-030'],
    },
    {
      id: 'regular',
      name: 'Regular RFO',
      timeline: '3-6 weeks',
      description: 'Standard enforcement for non-emergency violations.',
      proofStandard: 'Preponderance of evidence',
      requiredForms: ['FL-300', 'MC-030'],
    },
    {
      id: 'contempt',
      name: 'Contempt of Court',
      timeline: '4-8 weeks',
      description: 'Quasi-criminal proceeding; higher proof standard applies.',
      proofStandard: 'Beyond reasonable doubt',
      requiredForms: ['FL-410', 'FL-411', 'MC-030'],
    },
  ],
  courthouses: [],
};

/** POST /violations/process response */
const MOCK_PROCESS_RESULT = {
  success: true,
  track: 'regular',
  trackName: 'Regular RFO',
  timeline: '3-6 weeks',
  forms: [
    {
      id: 'FL-300',
      name: 'Request for Order',
      description: 'Main RFO form',
      fileName: 'fl300.pdf',
      required: true,
    },
    {
      id: 'MC-030',
      name: 'Declaration',
      description: 'Your declaration',
      fileName: 'mc030.pdf',
      required: true,
    },
  ],
  declaration: 'DECLARATION IN SUPPORT OF REQUEST FOR ORDER\n\nI declare...',
  courthouse: {
    name: 'San Diego Family Court',
    address: '1555 6th Ave, San Diego, CA 92101',
    phone: '(619) 450-7250',
  },
  instructions: [
    '1. Complete all required forms',
    '2. Make 3 copies of all documents',
  ],
  filingFee: '$60.00',
  serviceRequirements: {
    method: 'Mail or personal service',
    deadline: '5 days before hearing',
  },
};

const renderWithRouter = (ui: React.ReactElement) =>
  render(<BrowserRouter>{ui}</BrowserRouter>);

// Lazy import after mocks are established
let ViolationIntake: React.FC;

beforeAll(async () => {
  const mod = await import('../violation/ViolationIntake');
  ViolationIntake = mod.ViolationIntake;
});

describe('ViolationIntake', () => {
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

  describe('wizard rendering', () => {
    test('renders first step questions from mocked API', async () => {
      renderWithRouter(<ViolationIntake />);

      await waitFor(() => {
        expect(screen.getByText('Violation Type')).toBeInTheDocument();
      });

      expect(
        screen.getByLabelText(/Type of Court Order Violated/i)
      ).toBeInTheDocument();
      expect(
        screen.getByText(/Is this an emergency situation/i)
      ).toBeInTheDocument();
    });

    test('shows step progress indicator', async () => {
      renderWithRouter(<ViolationIntake />);

      await waitFor(() => {
        expect(screen.getByText(/Step 1/i)).toBeInTheDocument();
      });
    });

    test('Next button is present on first step', async () => {
      renderWithRouter(<ViolationIntake />);

      await waitFor(() => {
        expect(screen.getByRole('button', { name: /Next/i })).toBeInTheDocument();
      });
    });

    test('Previous button is disabled on first step', async () => {
      renderWithRouter(<ViolationIntake />);

      await waitFor(() => {
        expect(screen.getByRole('button', { name: /Previous/i })).toBeDisabled();
      });
    });

    test('shows loading state while fetching questions', () => {
      mockGetIntakeQuestions.mockReturnValue(new Promise(() => {}));
      renderWithRouter(<ViolationIntake />);
      // Loading spinner or text should be present before data arrives
      expect(document.querySelector('.animate-spin')).toBeInTheDocument();
    });
  });

  describe('wizard navigation', () => {
    test('advances to step 2 when Next is clicked on step 1', async () => {
      renderWithRouter(<ViolationIntake />);

      await waitFor(() => {
        expect(screen.getByRole('button', { name: /Next/i })).toBeInTheDocument();
      });

      fireEvent.click(screen.getByRole('button', { name: /Next/i }));

      await waitFor(() => {
        expect(screen.getByText('Violation Details')).toBeInTheDocument();
      });
    });

    test('going back from step 2 returns to step 1', async () => {
      renderWithRouter(<ViolationIntake />);

      await waitFor(() => {
        expect(screen.getByRole('button', { name: /Next/i })).toBeInTheDocument();
      });

      fireEvent.click(screen.getByRole('button', { name: /Next/i }));

      await waitFor(() => {
        expect(screen.getByText('Violation Details')).toBeInTheDocument();
      });

      fireEvent.click(screen.getByRole('button', { name: /Previous/i }));

      await waitFor(() => {
        expect(screen.getByText('Violation Type')).toBeInTheDocument();
      });
    });
  });

  describe('form submission', () => {
    test('calls process API with collected answers on final submit', async () => {
      renderWithRouter(<ViolationIntake />);

      // Step 1 — advance
      await waitFor(() => {
        expect(screen.getByRole('button', { name: /Next/i })).toBeInTheDocument();
      });
      fireEvent.click(screen.getByRole('button', { name: /Next/i }));

      // Step 2 — submit
      await waitFor(() => {
        expect(screen.getByRole('button', { name: /Submit/i })).toBeInTheDocument();
      });
      fireEvent.click(screen.getByRole('button', { name: /Submit/i }));

      await waitFor(() => {
        expect(mockProcess).toHaveBeenCalledTimes(1);
      });

      const callArg = mockProcess.mock.calls[0][0];
      expect(callArg).toMatchObject({
        violationDates: expect.any(Array),
        requestedRelief: expect.any(Array),
      });
    });

    test('shows processing state while API call is in flight', async () => {
      let resolveProcess: (v: any) => void;
      mockProcess.mockReturnValue(
        new Promise((resolve) => {
          resolveProcess = resolve;
        })
      );

      renderWithRouter(<ViolationIntake />);

      await waitFor(() => {
        expect(screen.getByRole('button', { name: /Next/i })).toBeInTheDocument();
      });
      fireEvent.click(screen.getByRole('button', { name: /Next/i }));

      await waitFor(() => {
        expect(screen.getByRole('button', { name: /Submit/i })).toBeInTheDocument();
      });
      fireEvent.click(screen.getByRole('button', { name: /Submit/i }));

      await waitFor(() => {
        expect(
          screen.getByText(/Analyzing your answers/i)
        ).toBeInTheDocument();
      });

      resolveProcess!(MOCK_PROCESS_RESULT);
    });
  });

  describe('result screen', () => {
    const advanceToResult = async () => {
      renderWithRouter(<ViolationIntake />);

      await waitFor(() => {
        expect(screen.getByRole('button', { name: /Next/i })).toBeInTheDocument();
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
  });
});
