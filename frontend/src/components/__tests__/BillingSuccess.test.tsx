/**
 * BillingSuccess: verifies the checkout session, polls status until entitled,
 * then offers the guided-session link and Continue back into the app.
 * BillingCanceled: reassures nothing was charged.
 */
import React from 'react';
import { render, screen, fireEvent, waitFor } from '@testing-library/react';
import '@testing-library/jest-dom';
import { BrowserRouter } from 'react-router-dom';
import { BillingSuccess } from '../billing/BillingSuccess';
import { BillingCanceled } from '../billing/BillingCanceled';

const mockNavigate = jest.fn();
let mockSearchParams = new URLSearchParams('session_id=cs_1&return_to=/motion/1/preview');

jest.mock('react-router-dom', () => ({
  ...jest.requireActual('react-router-dom'),
  useNavigate: () => mockNavigate,
  useSearchParams: () => [mockSearchParams, jest.fn()],
}));

const mockVerifySession = jest.fn();
const mockGetStatus = jest.fn();

jest.mock('../../services/billing', () => ({
  billingAPI: {
    verifySession: (...args: any[]) => mockVerifySession(...args),
    getStatus: (...args: any[]) => mockGetStatus(...args),
  },
}));

const renderSuccess = () =>
  render(<BrowserRouter><BillingSuccess pollIntervalMs={1} /></BrowserRouter>);

describe('BillingSuccess', () => {
  beforeEach(() => {
    jest.clearAllMocks();
    mockSearchParams = new URLSearchParams('session_id=cs_1&return_to=/motion/1/preview');
    process.env.REACT_APP_SCHEDULING_URL = 'https://calendar.app/sam';
  });

  test('verify-session success activates immediately without polling', async () => {
    mockVerifySession.mockResolvedValue({ status: 'active', is_entitled: true });

    renderSuccess();

    expect(await screen.findByText(/subscribed/i)).toBeInTheDocument();
    expect(mockVerifySession).toHaveBeenCalledWith('cs_1');
    expect(mockGetStatus).not.toHaveBeenCalled();
    expect(screen.getByRole('link', { name: /schedule/i })).toHaveAttribute(
      'href',
      'https://calendar.app/sam'
    );
  });

  test('falls back to polling status until entitled', async () => {
    mockVerifySession.mockRejectedValue(new Error('stripe hiccup'));
    mockGetStatus
      .mockResolvedValueOnce({ status: 'incomplete', is_entitled: false })
      .mockResolvedValueOnce({ status: 'active', is_entitled: true });

    renderSuccess();

    expect(await screen.findByText(/subscribed/i)).toBeInTheDocument();
    expect(mockGetStatus).toHaveBeenCalledTimes(2);
  });

  test('shows an error state when activation never confirms', async () => {
    mockVerifySession.mockRejectedValue(new Error('stripe hiccup'));
    mockGetStatus.mockResolvedValue({ status: 'incomplete', is_entitled: false });

    renderSuccess();

    expect(await screen.findByText(/taking longer than expected/i)).toBeInTheDocument();
  });

  test('continue navigates to return_to', async () => {
    mockVerifySession.mockResolvedValue({ status: 'active', is_entitled: true });

    renderSuccess();
    fireEvent.click(await screen.findByRole('button', { name: /continue/i }));

    expect(mockNavigate).toHaveBeenCalledWith('/motion/1/preview');
  });
});

describe('BillingCanceled', () => {
  test('states nothing was charged with a way back', () => {
    render(<BrowserRouter><BillingCanceled /></BrowserRouter>);

    expect(screen.getByText(/nothing was charged/i)).toBeInTheDocument();
    expect(screen.getByRole('link', { name: /back to dashboard/i })).toBeInTheDocument();
  });
});
