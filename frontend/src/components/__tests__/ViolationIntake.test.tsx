/**
 * Tests for the ViolationIntake wizard (steps, navigation, answer serialization).
 * The result screen is covered in ViolationIntakeResult.test.tsx; shared
 * fixtures (byte-exact live API shapes) live in
 * ../violation/__fixtures__/violationIntakeFixtures.ts.
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

const renderStepOne = async () => {
  renderWithRouter(<ViolationIntake />);
  await waitFor(() => {
    expect(screen.getByText('Order & Urgency')).toBeInTheDocument();
  });
};

const advanceTo = async (stepName: string) => {
  fireEvent.click(screen.getByRole('button', { name: /Next/i }));
  await waitFor(() => {
    expect(screen.getByText(stepName)).toBeInTheDocument();
  });
};

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
      await renderStepOne();

      expect(
        screen.getByLabelText(/What type of court order was violated/i)
      ).toBeInTheDocument();
      expect(
        screen.getByText(/Is this an emergency requiring immediate court action/i)
      ).toBeInTheDocument();
    });

    test('shows step progress indicator with all three steps', async () => {
      await renderStepOne();

      expect(screen.getByText(/Step 1 of 3/i)).toBeInTheDocument();
    });

    test('Next button is present on first step', async () => {
      await renderStepOne();

      expect(screen.getByRole('button', { name: /Next/i })).toBeInTheDocument();
    });

    test('Previous button is disabled on first step', async () => {
      await renderStepOne();

      expect(screen.getByRole('button', { name: /Previous/i })).toBeDisabled();
    });

    test('shows loading state while fetching questions', () => {
      mockGetIntakeQuestions.mockReturnValue(new Promise(() => {}));
      renderWithRouter(<ViolationIntake />);
      // Loading spinner or text should be present before data arrives
      expect(document.querySelector('.animate-spin')).toBeInTheDocument();
    });
  });

  describe('wizard navigation', () => {
    test('advances through all three steps', async () => {
      await renderStepOne();

      await advanceTo('What Happened');
      await advanceTo('Resolution & Requested Relief');

      expect(screen.getByRole('button', { name: /Submit/i })).toBeInTheDocument();
    });

    test('going back from step 2 returns to step 1', async () => {
      await renderStepOne();

      await advanceTo('What Happened');

      fireEvent.click(screen.getByRole('button', { name: /Previous/i }));

      await waitFor(() => {
        expect(screen.getByText('Order & Urgency')).toBeInTheDocument();
      });
    });
  });

  describe('form submission', () => {
    test('calls process API with collected answers on final submit', async () => {
      await renderStepOne();

      await advanceTo('What Happened');
      await advanceTo('Resolution & Requested Relief');
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

      await renderStepOne();

      await advanceTo('What Happened');
      await advanceTo('Resolution & Requested Relief');
      fireEvent.click(screen.getByRole('button', { name: /Submit/i }));

      await waitFor(() => {
        expect(
          screen.getByText(/Analyzing your answers/i)
        ).toBeInTheDocument();
      });

      resolveProcess!(MOCK_PROCESS_RESULT);
    });
  });

  describe('answer serialization', () => {
    test('checked evidence and relief checkboxes serialize to string arrays', async () => {
      await renderStepOne();

      await advanceTo('What Happened');
      fireEvent.click(screen.getByLabelText('Text messages'));
      fireEvent.click(screen.getByLabelText('Photos/Videos'));

      await advanceTo('Resolution & Requested Relief');
      fireEvent.click(screen.getByLabelText('Order makeup visitation'));
      fireEvent.click(screen.getByRole('button', { name: /Submit/i }));

      await waitFor(() => {
        expect(mockProcess).toHaveBeenCalledTimes(1);
      });

      expect(mockProcess.mock.calls[0][0]).toMatchObject({
        evidence: ['Text messages', 'Photos/Videos'],
        requestedRelief: ['Order makeup visitation'],
      });
    });

    test('urgency radio answer serializes to a boolean', async () => {
      await renderStepOne();

      fireEvent.click(screen.getByLabelText('Yes'));

      await advanceTo('What Happened');
      await advanceTo('Resolution & Requested Relief');
      fireEvent.click(screen.getByRole('button', { name: /Submit/i }));

      await waitFor(() => {
        expect(mockProcess).toHaveBeenCalledTimes(1);
      });

      expect(mockProcess.mock.calls[0][0].urgency).toBe(true);
    });
  });
});
