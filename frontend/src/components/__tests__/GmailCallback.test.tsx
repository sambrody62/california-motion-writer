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
  { message_id: 'msg-1', subject: 'Kids pickup tomorrow', from: 'other@example.com', date: '2024-03-01', snippet: 'I will not be there...',
    relevance_score: 0.4, relevance_reason: 'Mentions a pickup', suggested_tags: ['custody_violation'] },
  { message_id: 'msg-2', subject: 'Payment overdue', from: 'other@example.com', date: '2024-04-15', snippet: 'I refuse to pay...',
    relevance_score: 0.9, relevance_reason: 'Refusal to pay support', suggested_tags: ['non_payment'] },
];

describe('GmailCallback', () => {
  beforeEach(() => {
    jest.clearAllMocks();
    mockExchangeCode.mockResolvedValue({ access_token: 'tok-123' });
    mockScan.mockResolvedValue({ emails: sampleEmails, ranking_notice: null });
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

    // Select a specific email (the list is sorted by relevance)
    fireEvent.click(screen.getByLabelText('Kids pickup tomorrow'));

    fireEvent.click(screen.getByRole('button', { name: /import selected/i }));

    await waitFor(() => {
      expect(mockImport).toHaveBeenCalledWith(
        'm1',
        'tok-123',
        expect.arrayContaining(['msg-1']),
        expect.any(Object)
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


describe('GmailCallback — relevance ranking', () => {
  beforeEach(() => {
    jest.clearAllMocks();
    mockExchangeCode.mockResolvedValue({ access_token: 'tok-123' });
    mockScan.mockResolvedValue({ emails: sampleEmails, ranking_notice: null });
  });

  test('sorts emails by relevance score, highest first', async () => {
    render(<GmailCallback />);
    await waitFor(() => {
      expect(screen.getByText('Payment overdue')).toBeInTheDocument();
    });
    const items = screen.getAllByRole('listitem');
    expect(items[0]).toHaveTextContent('Payment overdue');
    expect(items[1]).toHaveTextContent('Kids pickup tomorrow');
  });

  test('shows the relevance reason and suggested tag chips', async () => {
    render(<GmailCallback />);
    await waitFor(() => {
      expect(screen.getByText(/Refusal to pay support/i)).toBeInTheDocument();
      expect(screen.getByText(/Missed payment/i)).toBeInTheDocument();
    });
  });

  test('shows ranking notice banner when ranking is unavailable', async () => {
    mockScan.mockResolvedValue({
      emails: sampleEmails.map(({ relevance_score, relevance_reason, suggested_tags, ...e }) => e),
      ranking_notice: 'Relevance ranking is not available right now.',
    });
    render(<GmailCallback />);
    await waitFor(() => {
      expect(
        screen.getByText(/Relevance ranking is not available/i)
      ).toBeInTheDocument();
    });
  });

  test('import sends suggested tags for selected messages', async () => {
    mockImport.mockResolvedValue([]);
    render(<GmailCallback />);
    await waitFor(() => {
      expect(screen.getByText('Payment overdue')).toBeInTheDocument();
    });

    fireEvent.click(screen.getByLabelText('Payment overdue'));
    fireEvent.click(screen.getByRole('button', { name: /import selected/i }));

    await waitFor(() => {
      expect(mockImport).toHaveBeenCalledWith(
        'm1',
        'tok-123',
        ['msg-2'],
        { 'msg-2': ['non_payment'] }
      );
    });
  });

  test('clicking a suggested tag chip removes it from the import tags', async () => {
    mockImport.mockResolvedValue([]);
    render(<GmailCallback />);
    await waitFor(() => {
      expect(screen.getByText('Payment overdue')).toBeInTheDocument();
    });

    fireEvent.click(screen.getByLabelText('Payment overdue'));
    fireEvent.click(screen.getByRole('button', { name: /remove tag Missed payment/i }));
    fireEvent.click(screen.getByRole('button', { name: /import selected/i }));

    await waitFor(() => {
      expect(mockImport).toHaveBeenCalledWith('m1', 'tok-123', ['msg-2'], { 'msg-2': [] });
    });
  });
});
