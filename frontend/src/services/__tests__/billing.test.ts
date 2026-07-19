/**
 * Tests for billing service
 */
import mockAxios from '../../__mocks__/axios';
import { billingAPI, isPaywallError } from '../billing';

beforeEach(() => {
  jest.clearAllMocks();
});

describe('billingAPI', () => {
  test('getStatus GETs /billing/status', async () => {
    const payload = { status: 'active', is_entitled: true };
    mockAxios.get.mockResolvedValueOnce({ data: payload });

    const result = await billingAPI.getStatus();

    expect(mockAxios.get).toHaveBeenCalledWith('/billing/status');
    expect(result).toEqual(payload);
  });

  test('createCheckoutSession POSTs return_to', async () => {
    mockAxios.post.mockResolvedValueOnce({ data: { url: 'https://checkout.stripe.com/x' } });

    const result = await billingAPI.createCheckoutSession('/motion/1/preview');

    expect(mockAxios.post).toHaveBeenCalledWith('/billing/checkout-session', {
      return_to: '/motion/1/preview',
    });
    expect(result.url).toBe('https://checkout.stripe.com/x');
  });

  test('createCheckoutSession without returnTo sends null', async () => {
    mockAxios.post.mockResolvedValueOnce({ data: { url: 'u' } });

    await billingAPI.createCheckoutSession();

    expect(mockAxios.post).toHaveBeenCalledWith('/billing/checkout-session', {
      return_to: null,
    });
  });

  test('createPortalSession POSTs /billing/portal-session', async () => {
    mockAxios.post.mockResolvedValueOnce({ data: { url: 'https://billing.stripe.com/x' } });

    const result = await billingAPI.createPortalSession();

    expect(mockAxios.post).toHaveBeenCalledWith('/billing/portal-session');
    expect(result.url).toBe('https://billing.stripe.com/x');
  });

  test('verifySession POSTs session_id', async () => {
    mockAxios.post.mockResolvedValueOnce({ data: { status: 'active', is_entitled: true } });

    const result = await billingAPI.verifySession('cs_123');

    expect(mockAxios.post).toHaveBeenCalledWith('/billing/verify-session', {
      session_id: 'cs_123',
    });
    expect(result.is_entitled).toBe(true);
  });
});

describe('isPaywallError', () => {
  test('true for 402 responses', () => {
    expect(isPaywallError({ response: { status: 402 } })).toBe(true);
  });

  test('false for other statuses and shapes', () => {
    expect(isPaywallError({ response: { status: 500 } })).toBe(false);
    expect(isPaywallError({})).toBe(false);
    expect(isPaywallError(undefined)).toBe(false);
    expect(isPaywallError(new Error('network'))).toBe(false);
  });
});
