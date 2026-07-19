/**
 * MotionPreview paywall: a 402 from PDF generation opens the paywall modal
 * instead of the generic error; other failures keep the generic error.
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
const mockGeneratePDFSync = jest.fn();
const mockGetProfile = jest.fn();
const mockCreateCheckoutSession = jest.fn();

jest.mock('../../services/api', () => ({
  motionAPI: {
    get: (...args: any[]) => mockGetMotion(...args),
    getDrafts: (...args: any[]) => mockGetDrafts(...args),
  },
  documentAPI: {
    generatePDFSync: (...args: any[]) => mockGeneratePDFSync(...args),
  },
  profileAPI: {
    get: (...args: any[]) => mockGetProfile(...args),
  },
}));

jest.mock('../../services/billing', () => ({
  billingAPI: {
    createCheckoutSession: (...args: any[]) => mockCreateCheckoutSession(...args),
  },
  isPaywallError: (error: any) => error?.response?.status === 402,
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

const mockDrafts = [
  {
    id: 'draft-1',
    step_number: 1,
    step_name: 'Case Information',
    question_data: { party_name: 'Jane' },
    llm_output: 'Petitioner Jane respectfully requests...',
    created_at: '2024-01-01T00:00:00Z',
  },
];

const assignMock = jest.fn();
const originalLocation = window.location;

beforeAll(() => {
  delete (window as any).location;
  (window as any).location = { ...originalLocation, assign: assignMock };
});

afterAll(() => {
  (window as any).location = originalLocation;
});

const clickDownload = async () => {
  await waitFor(() => {
    expect(screen.getAllByRole('button', { name: /Download PDF/i }).length).toBeGreaterThan(0);
  });
  fireEvent.click(screen.getAllByRole('button', { name: /Download PDF/i })[0]);
};

describe('MotionPreview paywall', () => {
  beforeEach(() => {
    jest.clearAllMocks();
    mockGetMotion.mockResolvedValue(mockMotion);
    mockGetDrafts.mockResolvedValue(mockDrafts);
    mockGetProfile.mockRejectedValue(new Error('No profile'));
  });

  test('402 opens the paywall modal instead of the generic error', async () => {
    mockGeneratePDFSync.mockRejectedValue({ response: { status: 402 } });

    render(<BrowserRouter><MotionPreview /></BrowserRouter>);
    await clickDownload();

    expect(await screen.findByText(/60-day money-back guarantee/i)).toBeInTheDocument();
    expect(screen.queryByText(/PDF generation failed/i)).toBeNull();
  });

  test('subscribe from the preview paywall returns to the preview page', async () => {
    mockGeneratePDFSync.mockRejectedValue({ response: { status: 402 } });
    mockCreateCheckoutSession.mockResolvedValue({ url: 'https://checkout.stripe.com/x' });

    render(<BrowserRouter><MotionPreview /></BrowserRouter>);
    await clickDownload();

    fireEvent.click(await screen.findByRole('button', { name: /subscribe/i }));

    await waitFor(() => {
      expect(mockCreateCheckoutSession).toHaveBeenCalledWith('/motion/motion-123/preview');
    });
  });

  test('non-402 failures keep the generic error without the modal', async () => {
    mockGeneratePDFSync.mockRejectedValue(new Error('boom'));

    render(<BrowserRouter><MotionPreview /></BrowserRouter>);
    await clickDownload();

    expect(await screen.findByText(/PDF generation failed/i)).toBeInTheDocument();
    expect(screen.queryByText(/60-day money-back guarantee/i)).toBeNull();
  });
});
