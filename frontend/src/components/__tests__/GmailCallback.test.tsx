/**
 * Tests for GmailCallback component
 */
import React from 'react';
import { render, screen, fireEvent, waitFor } from '@testing-library/react';
import '@testing-library/jest-dom';

// ── router mock ───────────────────────────────────────────────────────────────
const mockNavigate = jest.fn();
jest.mock('react-router-dom', () => ({
  ...jest.requireActual('react-router-dom'),
  useNavigate: () => mockNavigate,
  useSearchParams: () => [new URLSearchParams('?code=auth-code-123&state=m1'), jest.fn()],
}));

// ── api mock ──────────────────────────────────────────────────────────────────
const mockExchangeCode = jest.fn();
const mockScan = jest.fn();
const mockImport = jest.fn();

jest.mock('../../services/api', () => ({
  gmailEvidenceAPI: {
    getAuthUrl: jest.fn(),
    exchangeCode: (...args: any[]) => mockExchangeCode(...args),
    scan: (...args: any[]) => mockScan(...args),
    import: (...args: any[]) => mockImport(...args),
  },
}));

import { GmailCallback } from '../evidence/GmailCallback';

const sampleEmails = [
  { message_id: 'msg-1', subject: 'Kids pickup tomorrow', from: 'other@example.com', date: '2024-03-01', snippet: 'I will not be there...' },
  { message_id: 'msg-2', subject: 'Payment overdue', from: 'other@example.com', date: '2024-04-15', snippet: 'I refuse to pay...' },
];

describe('GmailCallback', () => {
  beforeEach(() => {
    jest.clearAllMocks();
    mockExchangeCode.mockResolvedValue({ access_token: 'tok-123' });
    mockScan.mockResolvedValue({ emails: sampleEmails });
  });

  test('exchanges code and shows candidate email list', async () => {
    render(<GmailCallback />);

    await waitFor(() => {
      expect(mockExchangeCode).toHaveBeenCalledWith('auth-code-123');
    });

    await waitFor(() => {
      expect(screen.getByText('Kids pickup tomorrow')).toBeInTheDocument();
      expect(screen.getByText('Payment overdue')).toBeInTheDocument();
    });
  });

  test('shows unconfirmed disclaimer', async () => {
    render(<GmailCallback />);

    await waitFor(() => {
      expect(
        screen.getByText(/imported emails are saved as unconfirmed/i)
      ).toBeInTheDocument();
    });
  });

  test('import button calls import API with selected message IDs', async () => {
    mockImport.mockResolvedValue({ imported: 1 });
    render(<GmailCallback />);

    await waitFor(() => {
      expect(screen.getByText('Kids pickup tomorrow')).toBeInTheDocument();
    });

    // Select the first email checkbox
    const checkboxes = screen.getAllByRole('checkbox');
    fireEvent.click(checkboxes[0]);

    fireEvent.click(screen.getByRole('button', { name: /import selected/i }));

    await waitFor(() => {
      expect(mockImport).toHaveBeenCalledWith(
        'm1',
        'tok-123',
        expect.arrayContaining(['msg-1'])
      );
    });
  });

  test('navigates back after import', async () => {
    mockImport.mockResolvedValue({ imported: 1 });
    render(<GmailCallback />);

    await waitFor(() => {
      expect(screen.getByText('Kids pickup tomorrow')).toBeInTheDocument();
    });

    const checkboxes = screen.getAllByRole('checkbox');
    fireEvent.click(checkboxes[0]);

    fireEvent.click(screen.getByRole('button', { name: /import selected/i }));

    await waitFor(() => {
      expect(mockNavigate).toHaveBeenCalled();
    });
  });
});
