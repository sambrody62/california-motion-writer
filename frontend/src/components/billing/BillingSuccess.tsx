import React, { useEffect, useState } from 'react';
import { useNavigate, useSearchParams } from 'react-router-dom';
import { billingAPI } from '../../services/billing';

const MAX_POLLS = 5;

interface BillingSuccessProps {
  pollIntervalMs?: number;
}

export const BillingSuccess: React.FC<BillingSuccessProps> = ({ pollIntervalMs = 2000 }) => {
  const navigate = useNavigate();
  const [searchParams] = useSearchParams();
  const [phase, setPhase] = useState<'activating' | 'active' | 'error'>('activating');

  const sessionId = searchParams.get('session_id');
  const returnTo = searchParams.get('return_to') || '/dashboard';
  const schedulingUrl = process.env.REACT_APP_SCHEDULING_URL;

  useEffect(() => {
    let cancelled = false;

    const activate = async () => {
      // Primary: server-side session verification beats the webhook race
      if (sessionId) {
        try {
          const status = await billingAPI.verifySession(sessionId);
          if (status.is_entitled) {
            if (!cancelled) setPhase('active');
            return;
          }
        } catch {
          // fall through to polling
        }
      }
      // Fallback: the webhook may land a moment later
      for (let attempt = 0; attempt < MAX_POLLS; attempt++) {
        await new Promise((resolve) => setTimeout(resolve, pollIntervalMs));
        if (cancelled) return;
        try {
          const status = await billingAPI.getStatus();
          if (status.is_entitled) {
            setPhase('active');
            return;
          }
        } catch {
          // keep polling
        }
      }
      if (!cancelled) setPhase('error');
    };

    activate();
    return () => {
      cancelled = true;
    };
  }, [sessionId, pollIntervalMs]);

  return (
    <div className="min-h-screen bg-gray-50 flex items-center justify-center p-4">
      <div className="bg-white rounded-lg shadow max-w-md w-full p-8 text-center">
        {phase === 'activating' && (
          <>
            <div className="animate-spin rounded-full h-12 w-12 border-b-2 border-primary-600 mx-auto mb-4"></div>
            <p className="text-gray-700 text-lg">Activating your subscription…</p>
          </>
        )}
        {phase === 'active' && (
          <>
            <h2 className="text-2xl font-semibold text-gray-900">You're subscribed!</h2>
            <p className="mt-2 text-sm text-gray-600">
              Motion drafting and PDF export are now unlocked. Remember: you're covered by our
              60-day money-back guarantee.
            </p>
            {schedulingUrl && (
              <a
                href={schedulingUrl}
                target="_blank"
                rel="noopener noreferrer"
                className="mt-4 inline-block w-full px-4 py-2 rounded-md text-primary-700 bg-white border border-primary-300 hover:bg-primary-50 font-medium"
              >
                Schedule your 1-on-1 session
              </a>
            )}
            <button
              onClick={() => navigate(returnTo)}
              className="mt-3 w-full px-4 py-2 rounded-md text-white bg-primary-600 hover:bg-primary-700 font-medium"
            >
              Continue
            </button>
          </>
        )}
        {phase === 'error' && (
          <>
            <h2 className="text-xl font-semibold text-gray-900">
              Activation is taking longer than expected
            </h2>
            <p className="mt-2 text-sm text-gray-600">
              Your payment went through, but we haven't received confirmation yet. Wait a moment
              and refresh this page — if it persists, contact support and we'll sort it out.
            </p>
            <button
              onClick={() => navigate('/dashboard')}
              className="mt-4 w-full px-4 py-2 rounded-md text-gray-700 bg-white border border-gray-300 hover:bg-gray-50 font-medium"
            >
              Back to dashboard
            </button>
          </>
        )}
      </div>
    </div>
  );
};
