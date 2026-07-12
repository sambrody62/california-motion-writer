/**
 * Tests for the fact-check corrections banner on MotionPreview.
 * The banner surfaces GET /motions/{id} `fact_check.corrections` so users
 * review every corrected/flagged detail before filing (real-LLM findings
 * L1–L4). Split from MotionPreview.test.tsx to respect the 300-line limit.
 */
import React from 'react';
import { render, screen, waitFor, fireEvent } from '@testing-library/react';
import '@testing-library/jest-dom';
import { BrowserRouter } from 'react-router-dom';
import { MotionPreview } from '../motion/MotionPreview';

const mockNavigate = jest.fn();

jest.mock('react-router-dom', () => ({
  ...jest.requireActual('react-router-dom'),
  useNavigate: () => mockNavigate,
  useParams: () => ({ motionId: 'motion-123' }),
  useLocation: () => ({ state: null, pathname: '/motion/motion-123/preview' }),
}));

jest.mock('date-fns', () => ({
  format: (_date: Date, _fmt: string) => 'Jun 10, 2026',
}));

const mockGetMotion = jest.fn();
const mockGetDrafts = jest.fn();

jest.mock('../../services/api', () => ({
  motionAPI: {
    get: (...args: any[]) => mockGetMotion(...args),
    getDrafts: (...args: any[]) => mockGetDrafts(...args),
  },
  documentAPI: {
    generatePDFSync: jest.fn(),
  },
  profileAPI: {
    get: jest.fn().mockRejectedValue(new Error('No profile')),
  },
}));

const mockMotion = {
  id: 'motion-123',
  motion_type: 'RFO',
  case_caption: 'Smith v. Smith',
  case_number: 'FL-2024-001',
  filing_date: '',
  hearing_date: '',
  hearing_time: '',
  status: 'complete',
};

// Unwrapped GET /motions/{id} fact_check shape (severity per correction type)
const correction = (severity: string, message: string) => ({
  type: severity === 'corrected' ? 'party_role' : severity === 'info' ? 'placeholder_filled' : 'upl_flag',
  severity,
  section: 'Case Information',
  original: 'X',
  replacement: severity === 'needs_review' ? null : 'Y',
  message,
});

const threeCorrections = [
  correction('corrected', 'We changed the declarant from Respondent to Petitioner.'),
  correction('needs_review', 'We removed a citation to Local Rule 5.5.2 — verify any legal authority yourself.'),
  correction('info', 'We filled in your full legal name from your profile.'),
];

const renderPreview = () => render(<BrowserRouter><MotionPreview /></BrowserRouter>);

const loadWithFactCheck = (factCheck: any) => {
  mockGetMotion.mockResolvedValue({ ...mockMotion, fact_check: factCheck });
};

describe('MotionPreview fact-check banner', () => {
  beforeEach(() => {
    jest.clearAllMocks();
    mockGetDrafts.mockResolvedValue([]);
  });

  test('renders the heading with the correction count and each message', async () => {
    loadWithFactCheck({ version: 1, corrections: threeCorrections });

    renderPreview();

    await waitFor(() => {
      expect(
        screen.getByText(/We corrected or flagged 3 details in your draft — review each one before filing/i)
      ).toBeInTheDocument();
    });
    expect(screen.getByText(/changed the declarant from Respondent to Petitioner/i)).toBeInTheDocument();
    expect(screen.getByText(/removed a citation to Local Rule 5\.5\.2/i)).toBeInTheDocument();
    expect(screen.getByText(/filled in your full legal name from your profile/i)).toBeInTheDocument();
  });

  test('needs_review entries get a warning icon distinct from corrected and info', async () => {
    loadWithFactCheck({ version: 1, corrections: threeCorrections });

    renderPreview();

    await waitFor(() => {
      expect(screen.getByRole('img', { name: 'Needs review' })).toBeInTheDocument();
    });
    expect(screen.getByRole('img', { name: 'Corrected' })).toBeInTheDocument();
    expect(screen.getByRole('img', { name: 'Info' })).toBeInTheDocument();
  });

  test('banner is absent when fact_check is null', async () => {
    loadWithFactCheck(null);

    renderPreview();

    await waitFor(() => {
      expect(screen.getByText('Smith v. Smith')).toBeInTheDocument();
    });
    expect(screen.queryByText(/We corrected or flagged/i)).not.toBeInTheDocument();
  });

  test('banner is absent when the motion has no fact_check field', async () => {
    mockGetMotion.mockResolvedValue(mockMotion);

    renderPreview();

    await waitFor(() => {
      expect(screen.getByText('Smith v. Smith')).toBeInTheDocument();
    });
    expect(screen.queryByText(/We corrected or flagged/i)).not.toBeInTheDocument();
  });

  test('banner is absent when corrections is an empty list', async () => {
    loadWithFactCheck({ version: 1, corrections: [] });

    renderPreview();

    await waitFor(() => {
      expect(screen.getByText('Smith v. Smith')).toBeInTheDocument();
    });
    expect(screen.queryByText(/We corrected or flagged/i)).not.toBeInTheDocument();
  });

  test('collapses past 5 entries behind a Show all toggle', async () => {
    const seven = Array.from({ length: 7 }, (_, i) =>
      correction('corrected', `Correction message number ${i + 1}.`)
    );
    loadWithFactCheck({ version: 1, corrections: seven });

    renderPreview();

    await waitFor(() => {
      expect(screen.getByText(/We corrected or flagged 7 details/i)).toBeInTheDocument();
    });
    // Only the first 5 are visible before expanding
    expect(screen.getByText('Correction message number 5.')).toBeInTheDocument();
    expect(screen.queryByText('Correction message number 6.')).not.toBeInTheDocument();
    expect(screen.queryByText('Correction message number 7.')).not.toBeInTheDocument();

    fireEvent.click(screen.getByRole('button', { name: /Show all/i }));

    expect(screen.getByText('Correction message number 6.')).toBeInTheDocument();
    expect(screen.getByText('Correction message number 7.')).toBeInTheDocument();
  });

  test('no Show all toggle at 5 or fewer entries', async () => {
    loadWithFactCheck({ version: 1, corrections: threeCorrections });

    renderPreview();

    await waitFor(() => {
      expect(screen.getByText(/We corrected or flagged 3 details/i)).toBeInTheDocument();
    });
    expect(screen.queryByRole('button', { name: /Show all/i })).not.toBeInTheDocument();
  });
});
