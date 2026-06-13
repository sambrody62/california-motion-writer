/**
 * Tests for EvidenceManager component — TDD
 */
import React from 'react';
import { render, screen, fireEvent, waitFor } from '@testing-library/react';
import userEvent from '@testing-library/user-event';
import '@testing-library/jest-dom';
import { BrowserRouter } from 'react-router-dom';

const mockNavigate = jest.fn();

jest.mock('react-router-dom', () => ({
  ...jest.requireActual('react-router-dom'),
  useNavigate: () => mockNavigate,
  useParams: () => ({ motionId: 'motion-abc' }),
}));

// ── mock evidenceAPI ─────────────────────────────────────────────────────────
const mockEvidenceList = jest.fn();
const mockEvidenceCreate = jest.fn();
const mockEvidenceUpload = jest.fn();
const mockEvidenceUpdate = jest.fn();
const mockEvidenceRemove = jest.fn();

jest.mock('../../services/api', () => ({
  evidenceAPI: {
    list: (...args: any[]) => mockEvidenceList(...args),
    create: (...args: any[]) => mockEvidenceCreate(...args),
    upload: (...args: any[]) => mockEvidenceUpload(...args),
    update: (...args: any[]) => mockEvidenceUpdate(...args),
    remove: (...args: any[]) => mockEvidenceRemove(...args),
  },
}));

import { EvidenceManager } from '../evidence/EvidenceManager';

const sampleEvidence = [
  {
    id: 'ev-1',
    evidence_type: 'text' as const,
    tags: ['threat'],
    source_date: '2024-03-01',
    description: 'Text threatening custody',
    transcription: 'I will take the kids away',
    filename: null,
  },
  {
    id: 'ev-2',
    evidence_type: 'email' as const,
    tags: ['non_payment'],
    source_date: '2024-04-15',
    description: 'Missed payment email',
    transcription: null,
    filename: null,
  },
];

const renderManager = () =>
  render(
    <BrowserRouter>
      <EvidenceManager />
    </BrowserRouter>
  );

// ── 1. List renders from mocked API ─────────────────────────────────────────
describe('EvidenceManager — list', () => {
  beforeEach(() => {
    jest.clearAllMocks();
    mockEvidenceList.mockResolvedValue(sampleEvidence);
  });

  test('renders evidence list from API', async () => {
    renderManager();
    await waitFor(() => {
      expect(screen.getByText('Text threatening custody')).toBeInTheDocument();
      expect(screen.getByText('Missed payment email')).toBeInTheDocument();
    });
    expect(mockEvidenceList).toHaveBeenCalledWith('motion-abc');
  });

  test('renders empty state when no evidence', async () => {
    mockEvidenceList.mockResolvedValue([]);
    renderManager();
    await waitFor(() => {
      expect(screen.getByText(/no evidence/i)).toBeInTheDocument();
    });
  });

  test('empty state explains what makes good evidence', async () => {
    mockEvidenceList.mockResolvedValue([]);
    renderManager();
    await waitFor(() => {
      // neutral informational copy — dates, exact words
      expect(screen.getByText(/exact dates/i)).toBeInTheDocument();
      expect(screen.getByText(/exact words/i)).toBeInTheDocument();
    });
  });
});

// ── 2. Tag labels render with plain-language names ───────────────────────────
describe('EvidenceManager — tag labels', () => {
  beforeEach(() => {
    jest.clearAllMocks();
    mockEvidenceList.mockResolvedValue([]);
  });

  test('tag picker renders all six plain-language labels', async () => {
    renderManager();
    await waitFor(() => {
      expect(screen.getByRole('button', { name: /add evidence/i })).toBeInTheDocument();
    });

    // Open add form (empty state — no other Threat text on page)
    fireEvent.click(screen.getByRole('button', { name: /add evidence/i }));

    await waitFor(() => {
      expect(screen.getByLabelText(/^Threat$/i)).toBeInTheDocument();
      expect(screen.getByLabelText(/^Missed payment$/i)).toBeInTheDocument();
      expect(screen.getByLabelText(/^Custody violation$/i)).toBeInTheDocument();
      expect(screen.getByLabelText(/^Promise to follow order$/i)).toBeInTheDocument();
      expect(screen.getByLabelText(/^False claim$/i)).toBeInTheDocument();
      expect(screen.getByLabelText(/^Other$/i)).toBeInTheDocument();
    });
  });
});

// ── 3. Create posts correct shape ────────────────────────────────────────────
describe('EvidenceManager — create text evidence', () => {
  beforeEach(() => {
    jest.clearAllMocks();
    mockEvidenceList.mockResolvedValue([]);
    mockEvidenceCreate.mockResolvedValue({
      id: 'ev-new',
      evidence_type: 'text',
      tags: ['threat'],
      source_date: '2024-05-01',
      description: 'Threatening message',
      transcription: 'You will regret this',
      filename: null,
    });
  });

  test('create posts correct shape to API', async () => {
    const user = userEvent.setup();
    renderManager();

    await waitFor(() => {
      expect(screen.getByRole('button', { name: /add evidence/i })).toBeInTheDocument();
    });

    fireEvent.click(screen.getByRole('button', { name: /add evidence/i }));

    await waitFor(() => {
      expect(screen.getByLabelText(/^Threat$/i)).toBeInTheDocument();
    });

    // Fill description
    await user.type(screen.getByRole('textbox', { name: /description/i }), 'Threatening message');

    // Fill paste text
    await user.type(screen.getByRole('textbox', { name: /message text/i }), 'You will regret this');

    // Fill date
    const dateInput = screen.getByLabelText(/date of message/i);
    fireEvent.change(dateInput, { target: { value: '2024-05-01' } });

    // Pick tag
    fireEvent.click(screen.getByLabelText(/^Threat$/i));

    // Confirm accuracy
    fireEvent.click(screen.getByRole('checkbox', { name: /confirmed accurate/i }));

    // Submit
    fireEvent.click(screen.getByRole('button', { name: /save evidence/i }));

    await waitFor(() => {
      expect(mockEvidenceCreate).toHaveBeenCalledWith(
        'motion-abc',
        expect.objectContaining({
          evidence_type: expect.any(String),
          tags: expect.arrayContaining(['threat']),
          description: 'Threatening message',
          transcription: 'You will regret this',
          source_date: '2024-05-01',
          user_confirmed: true,
        })
      );
    });
  });
});

// ── 4. Upload requires transcription before submit enabled ───────────────────
describe('EvidenceManager — upload path', () => {
  beforeEach(() => {
    jest.clearAllMocks();
    mockEvidenceList.mockResolvedValue([]);
    mockEvidenceUpload.mockResolvedValue({
      id: 'ev-upload',
      evidence_type: 'photo',
      tags: [],
      source_date: null,
      description: '',
      transcription: 'photo text',
      filename: 'screenshot.png',
    });
  });

  test('upload submit is disabled until transcription is filled', async () => {
    const user = userEvent.setup();
    renderManager();

    await waitFor(() => {
      expect(screen.getByRole('button', { name: /add evidence/i })).toBeInTheDocument();
    });

    fireEvent.click(screen.getByRole('button', { name: /add evidence/i }));

    // Switch to upload path
    fireEvent.click(screen.getByRole('radio', { name: /upload/i }));

    await waitFor(() => {
      expect(screen.getByRole('button', { name: /save evidence/i })).toBeDisabled();
    });

    // Type transcription
    await user.type(
      screen.getByRole('textbox', { name: /type what the message says/i }),
      'some transcribed text'
    );

    await waitFor(() => {
      expect(screen.getByRole('button', { name: /save evidence/i })).not.toBeDisabled();
    });
  });

  test('shows required transcription label explaining purpose', async () => {
    renderManager();

    await waitFor(() => {
      expect(screen.getByRole('button', { name: /add evidence/i })).toBeInTheDocument();
    });

    fireEvent.click(screen.getByRole('button', { name: /add evidence/i }));
    fireEvent.click(screen.getByRole('radio', { name: /upload/i }));

    await waitFor(() => {
      expect(
        screen.getByText(/you must confirm the text before it can be used/i)
      ).toBeInTheDocument();
    });
  });
});
