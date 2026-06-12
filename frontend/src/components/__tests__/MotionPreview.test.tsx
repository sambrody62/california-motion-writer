/**
 * Tests for MotionPreview component
 */
import React from 'react';
import { render, screen, waitFor, fireEvent } from '@testing-library/react';
import '@testing-library/jest-dom';
import { BrowserRouter } from 'react-router-dom';
import { MotionPreview } from '../motion/MotionPreview';

const mockNavigate = jest.fn();
const mockUseLocation = jest.fn(() => ({ state: null as any, pathname: '/motion/motion-123/preview' }));

jest.mock('react-router-dom', () => ({
  ...jest.requireActual('react-router-dom'),
  useNavigate: () => mockNavigate,
  useParams: () => ({ motionId: 'motion-123' }),
  useLocation: () => mockUseLocation(),
}));

jest.mock('date-fns', () => ({
  format: (_date: Date, _fmt: string) => 'Jun 10, 2026',
}));

const mockGetMotion = jest.fn();
const mockGetDrafts = jest.fn();
const mockGeneratePDFSync = jest.fn();

jest.mock('../../services/api', () => ({
  motionAPI: {
    get: (...args: any[]) => mockGetMotion(...args),
    getDrafts: (...args: any[]) => mockGetDrafts(...args),
  },
  documentAPI: {
    generatePDFSync: (...args: any[]) => mockGeneratePDFSync(...args),
  },
}));

const createObjectURLMock = jest.fn(() => 'blob:mock-url');
const revokeObjectURLMock = jest.fn();

beforeAll(() => {
  global.URL.createObjectURL = createObjectURLMock;
  global.URL.revokeObjectURL = revokeObjectURLMock;
});

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

const renderWithRouter = (ui: React.ReactElement) =>
  render(<BrowserRouter>{ui}</BrowserRouter>);

describe('MotionPreview', () => {
  beforeEach(() => {
    jest.clearAllMocks();
    mockUseLocation.mockReturnValue({ state: null, pathname: '/motion/motion-123/preview' });
    mockGetMotion.mockResolvedValue({ data: mockMotion });
    mockGetDrafts.mockResolvedValue({ data: { drafts: mockDrafts } });
    mockGeneratePDFSync.mockResolvedValue({ data: new ArrayBuffer(100) });
  });

  test('renders motion preview with case info', async () => {
    renderWithRouter(<MotionPreview />);

    await waitFor(() => {
      expect(screen.getByText('Smith v. Smith')).toBeInTheDocument();
      expect(screen.getByText(/FL-2024-001/)).toBeInTheDocument();
    });
  });

  test('download button triggers blob download with correct filename', async () => {
    // Track anchor elements created after rendering
    const createdAnchors: HTMLAnchorElement[] = [];
    const origCreate = document.createElement.bind(document);

    // Temporarily track `a` elements created without preventing real DOM ops
    const createSpy = jest
      .spyOn(document, 'createElement')
      .mockImplementation((tagName: string, ...args: any[]) => {
        const el = origCreate(tagName, ...args);
        if (tagName === 'a') {
          jest.spyOn(el as HTMLAnchorElement, 'click').mockImplementation(() => {});
          createdAnchors.push(el as HTMLAnchorElement);
        }
        return el;
      });

    renderWithRouter(<MotionPreview />);

    await waitFor(() => {
      expect(screen.getAllByRole('button', { name: /Download PDF/i }).length).toBeGreaterThan(0);
    });

    const downloadBtn = screen.getAllByRole('button', { name: /Download PDF/i })[0];
    fireEvent.click(downloadBtn);

    await waitFor(() => {
      expect(mockGeneratePDFSync).toHaveBeenCalledWith('motion-123');
      expect(createObjectURLMock).toHaveBeenCalled();
      expect(createdAnchors.length).toBeGreaterThan(0);
    });

    // Verify filename: {motion_type}-{case_number}.pdf
    const anchor = createdAnchors[0];
    expect(anchor.download).toBe('RFO-FL-2024-001.pdf');

    createSpy.mockRestore();
  });

  test('shows error state with retry button and saved-draft message on PDF failure', async () => {
    mockGeneratePDFSync.mockRejectedValue(new Error('PDF generation failed'));

    renderWithRouter(<MotionPreview />);

    await waitFor(() => {
      expect(screen.getByText('Smith v. Smith')).toBeInTheDocument();
    });

    fireEvent.click(screen.getAllByRole('button', { name: /Download PDF/i })[0]);

    await waitFor(() => {
      // Error message mentions the draft is saved server-side
      expect(screen.getByText(/saved|server/i)).toBeInTheDocument();
    });

    // Retry button must appear
    expect(screen.getByRole('button', { name: /Try Again/i })).toBeInTheDocument();
  });

  test('shows LLM failure notice when navigated with llmFailed state', async () => {
    mockUseLocation.mockReturnValue({
      state: { llmFailed: true },
      pathname: '/motion/motion-123/preview',
    });

    renderWithRouter(<MotionPreview />);

    await waitFor(() => {
      expect(
        screen.getByText(/couldn't polish your wording|own words are legally valid/i)
      ).toBeInTheDocument();
    });
  });

  test('does not show LLM failure notice when no llmFailed state', async () => {
    renderWithRouter(<MotionPreview />);

    await waitFor(() => {
      expect(screen.getByText('Smith v. Smith')).toBeInTheDocument();
    });

    expect(
      screen.queryByText(/couldn't polish your wording/i)
    ).not.toBeInTheDocument();
  });
});
