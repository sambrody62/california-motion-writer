/**
 * Tests for GmailConnect component and EvidenceForm Gmail integration
 */
import React from 'react';
import { render, screen, fireEvent, waitFor } from '@testing-library/react';
import '@testing-library/jest-dom';

// ── feature flag mock ─────────────────────────────────────────────────────────
const mockGmailEnabled = jest.fn();
jest.mock('../../utils/featureFlags', () => ({
  gmailEnabled: () => mockGmailEnabled(),
}));

// ── api mock ──────────────────────────────────────────────────────────────────
const mockGetAuthUrl = jest.fn();
jest.mock('../../services/api', () => ({
  evidenceAPI: {
    list: jest.fn().mockResolvedValue([]),
    create: jest.fn().mockResolvedValue({}),
    upload: jest.fn().mockResolvedValue({}),
    update: jest.fn().mockResolvedValue({}),
    remove: jest.fn().mockResolvedValue({}),
  },
  gmailEvidenceAPI: {
    getAuthUrl: () => mockGetAuthUrl(),
    exchangeCode: jest.fn(),
    scan: jest.fn(),
    import: jest.fn(),
  },
}));

import { GmailConnect } from '../evidence/GmailConnect';
import { EvidenceForm } from '../evidence/EvidenceForm';

// ── GmailConnect ──────────────────────────────────────────────────────────────
describe('GmailConnect', () => {
  const originalLocation = window.location;

  beforeEach(() => {
    jest.clearAllMocks();
    // jsdom does not fully support window.location assignment — patch href setter
    delete (window as any).location;
    (window as any).location = { href: '' };
  });

  afterEach(() => {
    (window as any).location = originalLocation;
  });

  test('renders connect button', () => {
    render(<GmailConnect motionId="m1" accessToken="tok" />);
    expect(
      screen.getByRole('button', { name: /connect gmail/i })
    ).toBeInTheDocument();
  });

  test('clicking the button fetches the auth URL and redirects', async () => {
    mockGetAuthUrl.mockResolvedValue({ auth_url: 'https://accounts.google.com/o/oauth2/auth?foo=bar' });

    render(<GmailConnect motionId="m1" accessToken="tok" />);
    fireEvent.click(screen.getByRole('button', { name: /connect gmail/i }));

    await waitFor(() => {
      expect(mockGetAuthUrl).toHaveBeenCalledTimes(1);
      expect(window.location.href).toBe('https://accounts.google.com/o/oauth2/auth?foo=bar');
    });
  });

  test('shows error message when getAuthUrl fails', async () => {
    mockGetAuthUrl.mockRejectedValue(new Error('Network error'));

    render(<GmailConnect motionId="m1" accessToken="tok" />);
    fireEvent.click(screen.getByRole('button', { name: /connect gmail/i }));

    await waitFor(() => {
      expect(screen.getByRole('alert')).toBeInTheDocument();
    });
  });
});

// ── EvidenceForm — Gmail button visibility ────────────────────────────────────
describe('EvidenceForm — Gmail button visibility', () => {
  const noop = jest.fn();

  test('renders "Connect Gmail" button when gmailEnabled is true', () => {
    mockGmailEnabled.mockReturnValue(true);
    render(
      <EvidenceForm motionId="m1" onSave={noop} onCancel={noop} />
    );
    expect(
      screen.getByRole('button', { name: /connect gmail/i })
    ).toBeInTheDocument();
  });

  test('does NOT render "Connect Gmail" button when gmailEnabled is false', () => {
    mockGmailEnabled.mockReturnValue(false);
    render(
      <EvidenceForm motionId="m1" onSave={noop} onCancel={noop} />
    );
    expect(
      screen.queryByRole('button', { name: /connect gmail/i })
    ).not.toBeInTheDocument();
  });
});
