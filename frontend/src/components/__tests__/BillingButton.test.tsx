/**
 * BillingButton: Dashboard entry point — Subscribe when unsubscribed,
 * Manage billing (portal) when entitled.
 */
import React from 'react';
import { render, screen, fireEvent, waitFor } from '@testing-library/react';
import '@testing-library/jest-dom';
import { BillingButton } from '../billing/BillingButton';

const mockGetStatus = jest.fn();
const mockCreateCheckoutSession = jest.fn();
const mockCreatePortalSession = jest.fn();

jest.mock('../../services/billing', () => ({
  billingAPI: {
    getStatus: (...args: any[]) => mockGetStatus(...args),
    createCheckoutSession: (...args: any[]) => mockCreateCheckoutSession(...args),
    createPortalSession: (...args: any[]) => mockCreatePortalSession(...args),
  },
}));

const assignMock = jest.fn();
const originalLocation = window.location;

beforeAll(() => {
  delete (window as any).location;
  (window as any).location = { ...originalLocation, assign: assignMock };
});

afterAll(() => {
  (window as any).location = originalLocation;
});

beforeEach(() => {
  jest.clearAllMocks();
});

test('shows Subscribe and starts checkout when not entitled', async () => {
  mockGetStatus.mockResolvedValue({ status: null, is_entitled: false });
  mockCreateCheckoutSession.mockResolvedValue({ url: 'https://checkout.stripe.com/x' });

  render(<BillingButton />);
  fireEvent.click(await screen.findByRole('button', { name: /subscribe/i }));

  await waitFor(() => {
    expect(mockCreateCheckoutSession).toHaveBeenCalledWith('/dashboard');
    expect(assignMock).toHaveBeenCalledWith('https://checkout.stripe.com/x');
  });
});

test('shows Manage billing and opens the portal when entitled', async () => {
  mockGetStatus.mockResolvedValue({ status: 'active', is_entitled: true });
  mockCreatePortalSession.mockResolvedValue({ url: 'https://billing.stripe.com/x' });

  render(<BillingButton />);
  fireEvent.click(await screen.findByRole('button', { name: /manage billing/i }));

  await waitFor(() => {
    expect(assignMock).toHaveBeenCalledWith('https://billing.stripe.com/x');
  });
});

test('renders nothing while status is unknown', async () => {
  mockGetStatus.mockRejectedValue(new Error('network'));

  const { container } = render(<BillingButton />);

  await waitFor(() => {
    expect(mockGetStatus).toHaveBeenCalled();
  });
  expect(container).toBeEmptyDOMElement();
});
