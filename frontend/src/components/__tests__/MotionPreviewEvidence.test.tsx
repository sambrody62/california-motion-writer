/**
 * Tests for MotionPreview evidence section — TDD
 */
import React from 'react';
import { render, screen, waitFor, fireEvent } from '@testing-library/react';
import '@testing-library/jest-dom';
import { BrowserRouter } from 'react-router-dom';

const mockNavigate = jest.fn();
const mockUseLocation = jest.fn(() => ({
  state: null as any,
  pathname: '/motion/motion-abc/preview',
}));

jest.mock('react-router-dom', () => ({
  ...jest.requireActual('react-router-dom'),
  useNavigate: () => mockNavigate,
  useParams: () => ({ motionId: 'motion-abc' }),
  useLocation: () => mockUseLocation(),
}));

jest.mock('date-fns', () => ({
  format: (_date: Date, _fmt: string) => 'Jun 10, 2026',
}));

const mockGetMotion = jest.fn();
const mockGetDrafts = jest.fn();
const mockEvidenceList = jest.fn();

jest.mock('../../services/api', () => ({
  motionAPI: {
    get: (...args: any[]) => mockGetMotion(...args),
    getDrafts: (...args: any[]) => mockGetDrafts(...args),
  },
  documentAPI: {
    generatePDFSync: jest.fn().mockResolvedValue(new ArrayBuffer(8)),
  },
  evidenceAPI: {
    list: (...args: any[]) => mockEvidenceList(...args),
    create: jest.fn(),
    upload: jest.fn(),
    update: jest.fn(),
    remove: jest.fn(),
  },
}));

import { MotionPreview } from '../motion/MotionPreview';

const mockMotion = {
  id: 'motion-abc',
  motion_type: 'RFO',
  case_caption: 'Doe v. Doe',
  case_number: 'FL-2025-010',
  filing_date: '',
  hearing_date: '',
  hearing_time: '',
  status: 'complete',
};

const twoEvidence = [
  {
    id: 'ev-1',
    evidence_type: 'text',
    tags: ['threat'],
    source_date: '2024-03-01',
    description: 'Text 1',
    transcription: 'msg',
    filename: null,
  },
  {
    id: 'ev-2',
    evidence_type: 'email',
    tags: ['non_payment'],
    source_date: null,
    description: 'Email 1',
    transcription: null,
    filename: null,
  },
];

const renderPreview = () =>
  render(
    <BrowserRouter>
      <MotionPreview />
    </BrowserRouter>
  );

describe('MotionPreview — evidence section', () => {
  beforeEach(() => {
    jest.clearAllMocks();
    mockUseLocation.mockReturnValue({
      state: null,
      pathname: '/motion/motion-abc/preview',
    });
    mockGetMotion.mockResolvedValue({ data: mockMotion });
    mockGetDrafts.mockResolvedValue({ data: { drafts: [] } });
    mockEvidenceList.mockResolvedValue(twoEvidence);
  });

  test('shows evidence count section in MotionPreview', async () => {
    renderPreview();

    await waitFor(() => {
      // The evidence section is rendered as a button
      expect(
        screen.getByRole('button', { name: /evidence.*exhibits.*2/i })
      ).toBeInTheDocument();
    });
  });

  test('evidence section navigates to evidence manager on click', async () => {
    renderPreview();

    await waitFor(() => {
      const btn = screen.getByRole('button', { name: /evidence.*exhibits/i });
      expect(btn).toBeInTheDocument();
      fireEvent.click(btn);
    });

    expect(mockNavigate).toHaveBeenCalledWith(expect.stringContaining('evidence'));
  });

  test('shows confirmed evidence note near download button', async () => {
    renderPreview();

    await waitFor(() => {
      expect(
        screen.getByText(/confirmed evidence.*attached.*exhibits/i)
      ).toBeInTheDocument();
    });
  });

  test('shows zero count when no evidence', async () => {
    mockEvidenceList.mockResolvedValue([]);
    renderPreview();

    await waitFor(() => {
      expect(
        screen.getByRole('button', { name: /evidence.*exhibits.*0/i })
      ).toBeInTheDocument();
    });
  });
});
