import React, { useState } from 'react';
import { gmailEvidenceAPI } from '../../services/api';

interface GmailConnectProps {
  motionId: string;
  accessToken: string;
}

export const GmailConnect: React.FC<GmailConnectProps> = ({ motionId, accessToken }) => {
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);

  const handleConnect = async () => {
    setLoading(true);
    setError(null);
    try {
      const { auth_url } = await gmailEvidenceAPI.getAuthUrl();
      window.location.href = auth_url;
    } catch (err) {
      setError('Could not start Gmail authorization. Please try again.');
      setLoading(false);
    }
  };

  return (
    <div className="mt-2">
      {error && (
        <p role="alert" className="text-sm text-red-600 mb-2">
          {error}
        </p>
      )}
      <button
        type="button"
        onClick={handleConnect}
        disabled={loading}
        className="inline-flex items-center gap-2 px-3 py-2 text-sm font-medium text-indigo-700 bg-indigo-50 border border-indigo-200 rounded-md hover:bg-indigo-100 disabled:opacity-50 disabled:cursor-not-allowed"
        aria-label="Connect Gmail to find evidence"
      >
        {loading ? 'Connecting…' : 'Connect Gmail to find evidence'}
      </button>
    </div>
  );
};
