import React, { useState } from 'react';
import { billingAPI } from '../../services/billing';

interface PaywallModalProps {
  isOpen: boolean;
  onClose: () => void;
  returnTo: string;
}

export const PaywallModal: React.FC<PaywallModalProps> = ({ isOpen, onClose, returnTo }) => {
  const [redirecting, setRedirecting] = useState(false);
  const [error, setError] = useState('');

  if (!isOpen) return null;

  const subscribe = async () => {
    setError('');
    setRedirecting(true);
    try {
      const { url } = await billingAPI.createCheckoutSession(returnTo);
      window.location.assign(url);
    } catch {
      setError("We couldn't start checkout. Please try again.");
      setRedirecting(false);
    }
  };

  return (
    <div className="fixed inset-0 z-50 flex items-center justify-center bg-gray-900 bg-opacity-50 p-4">
      <div className="bg-white rounded-lg shadow-xl max-w-md w-full p-6">
        <h2 className="text-xl font-semibold text-gray-900">
          Unlock motion drafting &amp; PDF export
        </h2>
        <p className="mt-2 text-3xl font-bold text-gray-900">$499</p>
        <p className="text-sm text-gray-600">
          One-time to get started, then $99/month while you need us.
        </p>
        <ul className="mt-4 space-y-2 text-sm text-gray-700">
          <li>✓ AI-drafted, court-ready motions and PDF export</li>
          <li>✓ 60-day money-back guarantee — no questions asked</li>
          <li>✓ Includes a 1-on-1 guided session to walk through the process together</li>
          <li>✓ Intake, gameplan, and evidence tools stay free</li>
          <li>✓ Cancel anytime</li>
        </ul>
        {error && <p className="mt-3 text-sm text-red-600">{error}</p>}
        <div className="mt-6 flex flex-col gap-2">
          <button
            onClick={subscribe}
            disabled={redirecting}
            className="w-full px-4 py-2 rounded-md text-white bg-primary-600 hover:bg-primary-700 font-medium disabled:opacity-50"
          >
            {redirecting ? 'Opening secure checkout…' : 'Subscribe'}
          </button>
          <button
            onClick={onClose}
            className="w-full px-4 py-2 rounded-md text-gray-700 bg-white border border-gray-300 hover:bg-gray-50 font-medium"
          >
            Not now
          </button>
        </div>
        <p className="mt-3 text-xs text-gray-500">
          Secure payment by Stripe. You'll be redirected to complete your purchase.
        </p>
      </div>
    </div>
  );
};
