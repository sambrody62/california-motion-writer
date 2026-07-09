import React from 'react';
import { ArrowRightIcon } from '@heroicons/react/24/outline';

interface EnforcementTriageProps {
  onProceedRFO: () => void;
  onProceedViolation: () => void;
}

// Journey 8: shown when the case involves order violations/enforcement
export const EnforcementTriage: React.FC<EnforcementTriageProps> = ({
  onProceedRFO,
  onProceedViolation,
}) => (
  <div className="bg-amber-50 border border-amber-200 rounded-lg p-6 mb-6">
    <h2 className="text-lg font-semibold text-gray-900 mb-2">
      Your case may involve order enforcement
    </h2>
    <p className="text-sm text-gray-700 mb-4">
      Based on what you described, there may be two paths forward. Each has different requirements — choose the one that fits your situation.
    </p>
    <div className="grid grid-cols-1 sm:grid-cols-2 gap-4">
      <div className="bg-white border border-gray-200 rounded-md p-4">
        <h3 className="text-sm font-semibold text-gray-900 mb-1">Request for Order (RFO)</h3>
        <p className="text-xs text-gray-600 mb-3">
          Ask the court to modify or clarify the existing order. Typically faster and uses a preponderance-of-evidence standard.
        </p>
        <button
          onClick={onProceedRFO}
          aria-label="Proceed with Request for Order"
          className="w-full inline-flex items-center justify-center px-3 py-2 border border-indigo-300 text-xs font-medium rounded-md text-indigo-700 bg-white hover:bg-indigo-50 focus:outline-none focus:ring-2 focus:ring-offset-2 focus:ring-indigo-500"
        >
          Continue with RFO
          <ArrowRightIcon className="h-3 w-3 ml-1" />
        </button>
      </div>
      <div className="bg-white border border-gray-200 rounded-md p-4">
        <h3 className="text-sm font-semibold text-gray-900 mb-1">Contempt of Court</h3>
        <p className="text-xs text-gray-600 mb-3">
          Seek to hold the other party in contempt for willfully violating the order. Requires a higher proof standard (beyond a reasonable doubt).
        </p>
        <button
          onClick={onProceedViolation}
          aria-label="Proceed with contempt / violation enforcement"
          className="w-full inline-flex items-center justify-center px-3 py-2 border border-amber-400 text-xs font-medium rounded-md text-amber-800 bg-white hover:bg-amber-50 focus:outline-none focus:ring-2 focus:ring-offset-2 focus:ring-amber-400"
        >
          Enforce via contempt
          <ArrowRightIcon className="h-3 w-3 ml-1" />
        </button>
      </div>
    </div>
  </div>
);
