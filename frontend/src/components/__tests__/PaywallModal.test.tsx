/**
 * Tests for PaywallModal component
 */
import React from 'react';
import { render, screen, fireEvent, waitFor } from '@testing-library/react';
import '@testing-library/jest-dom';
import { PaywallModal } from '../billing/PaywallModal';

const mockCreateCheckoutSession = jest.fn();

jest.mock('../../services/billing', () => ({
  billingAPI: {
    createCheckoutSession: (...args: any[]) => mockCreateCheckoutSession(...args),
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

test('renders offer copy when open', () => {
  render(<PaywallModal isOpen onClose={jest.fn()} returnTo="/dashboard" />);

  expect(screen.getByText(/\$300/)).toBeInTheDocument();
  expect(screen.getByText(/60-day money-back guarantee/i)).toBeInTheDocument();
  expect(screen.getByText(/guided session/i)).toBeInTheDocument();
});

test('renders nothing when closed', () => {
  const { container } = render(
    <PaywallModal isOpen={false} onClose={jest.fn()} returnTo="/dashboard" />
  );
  expect(container).toBeEmptyDOMElement();
});

test('subscribe requests checkout session with returnTo and redirects', async () => {
  mockCreateCheckoutSession.mockResolvedValueOnce({ url: 'https://checkout.stripe.com/x' });

  render(<PaywallModal isOpen onClose={jest.fn()} returnTo="/motion/1/preview" />);
  fireEvent.click(screen.getByRole('button', { name: /subscribe/i }));

  await waitFor(() => {
    expect(mockCreateCheckoutSession).toHaveBeenCalledWith('/motion/1/preview');
    expect(assignMock).toHaveBeenCalledWith('https://checkout.stripe.com/x');
  });
});

test('shows error when checkout session fails', async () => {
  mockCreateCheckoutSession.mockRejectedValueOnce(new Error('network'));

  render(<PaywallModal isOpen onClose={jest.fn()} returnTo="/dashboard" />);
  fireEvent.click(screen.getByRole('button', { name: /subscribe/i }));

  expect(await screen.findByText(/couldn't start checkout/i)).toBeInTheDocument();
  expect(assignMock).not.toHaveBeenCalled();
});

test('close button calls onClose', () => {
  const onClose = jest.fn();
  render(<PaywallModal isOpen onClose={onClose} returnTo="/dashboard" />);

  fireEvent.click(screen.getByRole('button', { name: /not now/i }));
  expect(onClose).toHaveBeenCalled();
});
