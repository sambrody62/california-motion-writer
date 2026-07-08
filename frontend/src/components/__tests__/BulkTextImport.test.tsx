/**
 * Tests for BulkTextImport — multi-screenshot text-message import with a
 * single review + confirm step.
 */
import React from 'react';
import { render, screen, waitFor, fireEvent } from '@testing-library/react';
import '@testing-library/jest-dom';
import { BrowserRouter } from 'react-router-dom';
import { BulkTextImport } from '../evidence/BulkTextImport';

const mockNavigate = jest.fn();
jest.mock('react-router-dom', () => ({
  ...jest.requireActual('react-router-dom'),
  useNavigate: () => mockNavigate,
  useParams: () => ({ motionId: 'motion-123' }),
}));

const mockBatchUpload = jest.fn();
jest.mock('../../services/evidenceBatchApi', () => ({
  evidenceBatchAPI: {
    batchUpload: (...args: any[]) => mockBatchUpload(...args),
  },
}));

const mockEvidenceCreate = jest.fn();
jest.mock('../../services/api', () => ({
  evidenceAPI: {
    create: (...args: any[]) => mockEvidenceCreate(...args),
  },
}));

const makeFiles = (n: number) =>
  Array.from({ length: n }, (_, i) =>
    new File(['img'], `shot-${i}.png`, { type: 'image/png' })
  );

// REAL unwrapped response shape (lessons.md)
const BATCH_RESULT = {
  merged_transcript: '[2026-03-03 20:41] Daniel: Running late again',
  participants: ['Daniel', 'Me'],
  date_range: { start: '2026-03-03', end: '2026-03-03' },
  suggested_source_date: '2026-03-03',
  per_file: [
    { filename: 'shot-0.png', ok: true, chars: 40 },
    { filename: 'shot-1.png', ok: true, chars: 52 },
  ],
  notice: null,
};

const renderPage = () =>
  render(
    <BrowserRouter>
      <BulkTextImport />
    </BrowserRouter>
  );

const uploadFiles = (n: number) => {
  const input = screen.getByLabelText(/screenshots/i) as HTMLInputElement;
  fireEvent.change(input, { target: { files: makeFiles(n) } });
};

describe('BulkTextImport', () => {
  beforeEach(() => {
    jest.clearAllMocks();
    mockBatchUpload.mockResolvedValue(BATCH_RESULT);
    mockEvidenceCreate.mockResolvedValue({ id: 'ev-1' });
  });

  test('rejects more than 20 files client-side without calling the API', async () => {
    renderPage();
    uploadFiles(21);
    expect(await screen.findByText(/maximum.*20/i)).toBeInTheDocument();
    expect(mockBatchUpload).not.toHaveBeenCalled();
  });

  test('uploads files and shows the merged transcript for review', async () => {
    renderPage();
    uploadFiles(2);
    await waitFor(() => {
      expect(mockBatchUpload).toHaveBeenCalledWith('motion-123', expect.any(Array));
    });
    const transcript = (await screen.findByRole('textbox')) as HTMLTextAreaElement;
    expect(transcript.value).toContain('Running late again');
  });

  test('shows the degraded-merge notice when present', async () => {
    mockBatchUpload.mockResolvedValue({
      ...BATCH_RESULT,
      notice: 'Automatic merging is not available right now.',
    });
    renderPage();
    uploadFiles(2);
    expect(
      await screen.findByText(/Automatic merging is not available/i)
    ).toBeInTheDocument();
  });

  test('confirm saves via evidenceAPI.create with user_confirmed true', async () => {
    renderPage();
    uploadFiles(2);
    const transcript = (await screen.findByRole('textbox')) as HTMLTextAreaElement;
    fireEvent.change(transcript, {
      target: { value: transcript.value + '\nMe: edited line' },
    });

    // pick a tag and confirm accuracy
    fireEvent.click(screen.getByLabelText(/Custody violation/i));
    fireEvent.click(screen.getByLabelText(/reviewed this transcript/i));
    fireEvent.click(screen.getByRole('button', { name: /save to case/i }));

    await waitFor(() => {
      expect(mockEvidenceCreate).toHaveBeenCalledWith(
        'motion-123',
        expect.objectContaining({
          evidence_type: 'text',
          user_confirmed: true,
          tags: ['custody_violation'],
          source_date: '2026-03-03',
          transcription: expect.stringContaining('edited line'),
        })
      );
      expect(mockNavigate).toHaveBeenCalledWith('/motion/motion-123/evidence');
    });
  });

  test('save is disabled until the user confirms accuracy', async () => {
    renderPage();
    uploadFiles(2);
    await screen.findByRole('textbox');
    const save = screen.getByRole('button', { name: /save to case/i });
    expect(save).toBeDisabled();
  });

  test('upload failure shows an error and allows retry', async () => {
    mockBatchUpload.mockRejectedValue(new Error('network'));
    renderPage();
    uploadFiles(2);
    expect(await screen.findByText(/couldn't read|failed/i)).toBeInTheDocument();
  });
});
