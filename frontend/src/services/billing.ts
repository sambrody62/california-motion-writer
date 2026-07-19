import api from './api';

export interface BillingStatus {
  status: string | null;
  is_entitled: boolean;
  current_period_end: string | null;
  cancel_at_period_end: boolean;
}

export const billingAPI = {
  getStatus: async (): Promise<BillingStatus> => {
    const response = await api.get('/billing/status');
    return response.data;
  },

  createCheckoutSession: async (returnTo?: string): Promise<{ url: string }> => {
    const response = await api.post('/billing/checkout-session', {
      return_to: returnTo ?? null,
    });
    return response.data;
  },

  createPortalSession: async (): Promise<{ url: string }> => {
    const response = await api.post('/billing/portal-session');
    return response.data;
  },

  verifySession: async (sessionId: string): Promise<BillingStatus> => {
    const response = await api.post('/billing/verify-session', {
      session_id: sessionId,
    });
    return response.data;
  },
};

// 402 from a gated endpoint means "show the paywall", not "show an error".
// Works for arraybuffer responses too — status survives any responseType.
export const isPaywallError = (error: any): boolean => error?.response?.status === 402;
