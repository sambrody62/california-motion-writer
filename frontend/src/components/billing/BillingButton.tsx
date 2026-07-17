import React, { useEffect, useState } from 'react';
import { billingAPI, BillingStatus } from '../../services/billing';

export const BillingButton: React.FC = () => {
  const [status, setStatus] = useState<BillingStatus | null>(null);

  useEffect(() => {
    (async () => {
      try {
        setStatus(await billingAPI.getStatus());
      } catch {
        // Billing unreachable — render nothing rather than a broken button
      }
    })();
  }, []);

  const openPortal = async () => {
    try {
      const { url } = await billingAPI.createPortalSession();
      window.location.assign(url);
    } catch {
      // Portal unavailable; leave the dashboard as-is
    }
  };

  const openCheckout = async () => {
    try {
      const { url } = await billingAPI.createCheckoutSession('/dashboard');
      window.location.assign(url);
    } catch {
      // Checkout unavailable; leave the dashboard as-is
    }
  };

  if (!status) return null;

  return status.is_entitled ? (
    <button
      onClick={openPortal}
      className="inline-flex items-center px-3 py-2 border border-gray-300 shadow-sm text-sm leading-4 font-medium rounded-md text-gray-700 bg-white hover:bg-gray-50 focus:outline-none focus:ring-2 focus:ring-offset-2 focus:ring-primary-500"
    >
      Manage billing
    </button>
  ) : (
    <button
      onClick={openCheckout}
      className="inline-flex items-center px-3 py-2 border border-transparent text-sm leading-4 font-medium rounded-md text-white bg-green-600 hover:bg-green-700 focus:outline-none focus:ring-2 focus:ring-offset-2 focus:ring-green-500"
    >
      Subscribe
    </button>
  );
};
