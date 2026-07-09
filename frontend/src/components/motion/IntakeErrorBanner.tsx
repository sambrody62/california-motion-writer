import React from 'react';

interface IntakeErrorBannerProps {
  message: string;
  onRetry?: () => void;
}

export const IntakeErrorBanner: React.FC<IntakeErrorBannerProps> = ({ message, onRetry }) => (
  <div className="mb-6 bg-red-50 border-l-4 border-red-400 p-4">
    <div className="flex items-center justify-between gap-4">
      <p className="text-sm text-red-800">{message}</p>
      {onRetry && (
        <button
          type="button"
          onClick={onRetry}
          className="flex-shrink-0 px-3 py-1.5 border border-red-300 text-sm font-medium rounded-md text-red-700 bg-white hover:bg-red-50"
        >
          Try again
        </button>
      )}
    </div>
  </div>
);
