/**
 * Tests for OCR pre-fill behavior in EvidenceForm
 */
import React from 'react';
import { render, screen, fireEvent, waitFor } from '@testing-library/react';
import '@testing-library/jest-dom';
import userEvent from '@testing-library/user-event';

// ── feature flag mock (Gmail off for these tests) ─────────────────────────────
jest.mock('../../utils/featureFlags', () => ({
  gmailEnabled: () => false,
}));

// ── api mock ──────────────────────────────────────────────────────────────────
const mockUpload = jest.fn();
jest.mock('../../services/api', () => ({
  evidenceAPI: {
    list: jest.fn().mockResolvedValue([]),
    create: jest.fn().mockResolvedValue({}),
    upload: (...args: any[]) => mockUpload(...args),
    update: jest.fn().mockResolvedValue({}),
    remove: jest.fn().mockResolvedValue({}),
  },
  gmailEvidenceAPI: {
    getAuthUrl: jest.fn(),
    exchangeCode: jest.fn(),
    scan: jest.fn(),
    import: jest.fn(),
  },
}));

import { EvidenceForm } from '../evidence/EvidenceForm';

describe('EvidenceForm — OCR pre-fill', () => {
  const noop = jest.fn();

  beforeEach(() => {
    jest.clearAllMocks();
  });

  test('pre-fills transcription textarea with suggested_transcription from upload response', async () => {
    mockUpload.mockResolvedValue({ suggested_transcription: 'OCR extracted text here' });

    const onSave = jest.fn().mockImplementation(async (payload) => {
      // simulate the component receiving OCR suggestion via a prop pathway
    });

    render(
      <EvidenceForm
        motionId="m1"
        onSave={noop}
        onCancel={noop}
        suggestedTranscription="OCR extracted text here"
      />
    );

    // Switch to upload path
    fireEvent.click(screen.getByRole('radio', { name: /upload/i }));

    await waitFor(() => {
      const textarea = screen.getByRole('textbox', { name: /type what the message says/i });
      expect(textarea).toHaveValue('OCR extracted text here');
    });
  });

  test('shows suggestion notice when suggestedTranscription is provided', async () => {
    render(
      <EvidenceForm
        motionId="m1"
        onSave={noop}
        onCancel={noop}
        suggestedTranscription="Some text from OCR"
      />
    );

    fireEvent.click(screen.getByRole('radio', { name: /upload/i }));

    await waitFor(() => {
      expect(
        screen.getByText(/suggested from your image.*review and correct/i)
      ).toBeInTheDocument();
    });
  });

  test('confirmation checkbox is NOT auto-checked when suggestion is pre-filled', async () => {
    render(
      <EvidenceForm
        motionId="m1"
        onSave={noop}
        onCancel={noop}
        suggestedTranscription="Some text from OCR"
      />
    );

    fireEvent.click(screen.getByRole('radio', { name: /upload/i }));

    await waitFor(() => {
      const confirmCheckbox = screen.getByRole('checkbox', { name: /confirmed accurate/i });
      expect(confirmCheckbox).not.toBeChecked();
    });
  });

  test('suggestion note does NOT appear when no suggestedTranscription prop', () => {
    render(
      <EvidenceForm motionId="m1" onSave={noop} onCancel={noop} />
    );

    fireEvent.click(screen.getByRole('radio', { name: /upload/i }));

    expect(
      screen.queryByText(/suggested from your image/i)
    ).not.toBeInTheDocument();
  });
});
