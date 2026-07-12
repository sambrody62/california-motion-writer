import React, { useState } from 'react';
import {
  CheckCircleIcon,
  ExclamationTriangleIcon,
  InformationCircleIcon,
} from '@heroicons/react/20/solid';

/** One fact-gate correction, as returned unwrapped by the backend on
 *  GET /motions/{id} (fact_check.corrections) and POST /violations/process
 *  (corrections). */
export interface Correction {
  type: string;
  severity: 'corrected' | 'needs_review' | 'info';
  section: string;
  original: string;
  replacement: string | null;
  message: string;
}

const COLLAPSE_AT = 5;

const SEVERITY_ICONS = {
  corrected: { Icon: CheckCircleIcon, label: 'Corrected', color: 'text-success-600' },
  needs_review: { Icon: ExclamationTriangleIcon, label: 'Needs review', color: 'text-amber-500' },
  info: { Icon: InformationCircleIcon, label: 'Info', color: 'text-primary-500' },
} as const;

interface CorrectionsListProps {
  corrections: Correction[];
}

/**
 * Amber "review before filing" banner listing fact-gate corrections.
 * Shared by MotionPreview (motion fact_check) and ViolationIntakeResult
 * (process response corrections).
 */
export const CorrectionsList: React.FC<CorrectionsListProps> = ({ corrections }) => {
  const [showAll, setShowAll] = useState(false);

  if (corrections.length === 0) return null;

  const visible = showAll ? corrections : corrections.slice(0, COLLAPSE_AT);

  return (
    <div className="bg-amber-50 border-l-4 border-amber-400 p-4 mb-6">
      <div className="flex">
        <div className="flex-shrink-0">
          <ExclamationTriangleIcon className="h-5 w-5 text-amber-500" aria-hidden="true" />
        </div>
        <div className="ml-3">
          <p className="text-sm font-medium text-amber-800">
            We corrected or flagged {corrections.length}{' '}
            {corrections.length === 1 ? 'detail' : 'details'} in your draft — review each one
            before filing
          </p>
          <ul className="mt-2 space-y-1.5">
            {visible.map((item, idx) => {
              const { Icon, label, color } =
                SEVERITY_ICONS[item.severity] ?? SEVERITY_ICONS.info;
              return (
                <li key={idx} className="flex items-start text-sm text-amber-700">
                  <Icon
                    className={`h-4 w-4 mt-0.5 mr-1.5 flex-shrink-0 ${color}`}
                    role="img"
                    aria-label={label}
                    aria-hidden={false}
                  />
                  <span>{item.message}</span>
                </li>
              );
            })}
          </ul>
          {!showAll && corrections.length > COLLAPSE_AT && (
            <button
              type="button"
              onClick={() => setShowAll(true)}
              className="mt-2 text-sm font-medium text-amber-800 underline hover:text-amber-700"
            >
              Show all ({corrections.length})
            </button>
          )}
        </div>
      </div>
    </div>
  );
};
