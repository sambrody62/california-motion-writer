/**
 * Tests for ServedMotionUpload — the skippable "upload the motion you were
 * served" gate shown before step 1 of the FL-320 response wizard.
 */
import React from 'react';
import { render, screen, waitFor, fireEvent } from '@testing-library/react';
import '@testing-library/jest-dom';
import { ServedMotionUpload } from '../motion/ServedMotionUpload';

const mockParse = jest.fn();

jest.mock('../../services/servedMotionApi', () => ({
  servedMotionAPI: {
    parse: (...args: any[]) => mockParse(...args),
  },
}));

const makeFile = (name = 'served-motion.pdf') =>
  new File(['%PDF-1.4 fake'], name, { type: 'application/pdf' });

describe('ServedMotionUpload', () => {
  const onExtracted = jest.fn();
  const onSkip = jest.fn();

  beforeEach(() => {
    jest.clearAllMocks();
    // REAL unwrapped response shape (lessons.md): {success, extracted, notice}
    mockParse.mockResolvedValue({
      success: true,
      extracted: {
        case_number: '24STFL01234',
        other_party_requests: 'Sole custody and child support',
      },
      notice: null,
    });
  });

  const renderUpload = () =>
    render(<ServedMotionUpload onExtracted={onExtracted} onSkip={onSkip} />);

  test('renders upload prompt, skip option, and privacy note', () => {
    renderUpload();
    expect(screen.getByText(/motion you were served/i)).toBeInTheDocument();
    expect(
      screen.getByRole('button', { name: /skip/i })
    ).toBeInTheDocument();
    expect(screen.getByText(/never stored/i)).toBeInTheDocument();
  });

  test('skip calls onSkip without parsing', () => {
    renderUpload();
    fireEvent.click(screen.getByRole('button', { name: /skip/i }));
    expect(onSkip).toHaveBeenCalled();
    expect(mockParse).not.toHaveBeenCalled();
  });

  test('uploading a file parses it and reports extracted facts', async () => {
    renderUpload();
    const input = screen.getByLabelText(/upload/i) as HTMLInputElement;
    fireEvent.change(input, { target: { files: [makeFile()] } });

    await waitFor(() => {
      expect(mockParse).toHaveBeenCalledWith(expect.any(File));
      expect(onExtracted).toHaveBeenCalledWith(
        expect.objectContaining({ case_number: '24STFL01234' }),
        null
      );
    });
  });

  test('empty extraction still proceeds, passing the notice through', async () => {
    mockParse.mockResolvedValue({
      success: true,
      extracted: {},
      notice: 'Automatic extraction is not available right now.',
    });
    renderUpload();
    const input = screen.getByLabelText(/upload/i) as HTMLInputElement;
    fireEvent.change(input, { target: { files: [makeFile()] } });

    await waitFor(() => {
      expect(onExtracted).toHaveBeenCalledWith(
        {},
        'Automatic extraction is not available right now.'
      );
    });
  });

  test('parse failure shows an error and lets the user retry or skip', async () => {
    mockParse.mockRejectedValue(new Error('network down'));
    renderUpload();
    const input = screen.getByLabelText(/upload/i) as HTMLInputElement;
    fireEvent.change(input, { target: { files: [makeFile()] } });

    await waitFor(() => {
      expect(screen.getByText(/couldn't read|could not read|failed/i)).toBeInTheDocument();
    });
    expect(onExtracted).not.toHaveBeenCalled();
    // skip still available as the escape hatch
    expect(screen.getByRole('button', { name: /skip/i })).toBeInTheDocument();
  });
});
