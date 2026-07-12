import React from 'react';
import { CheckCircleIcon, ExclamationTriangleIcon } from '@heroicons/react/20/solid';
import { CorrectionsList, Correction } from '../shared/CorrectionsList';

export interface FactCheck {
  version: number;
  corrections: Correction[];
}

interface MotionPreviewBannersProps {
  llmFailed: boolean;
  hasLLMContent: boolean;
  pdfError: string | null;
  generating: boolean;
  onRetryPDF: () => void;
  factCheck?: FactCheck | null;
}

export const MotionPreviewBanners: React.FC<MotionPreviewBannersProps> = ({
  llmFailed,
  hasLLMContent,
  pdfError,
  generating,
  onRetryPDF,
  factCheck,
}) => (
  <>
    {/* Fact-check corrections — review every corrected/flagged detail before filing */}
    {factCheck?.corrections && factCheck.corrections.length > 0 && (
      <CorrectionsList corrections={factCheck.corrections} />
    )}

    {/* LLM failure notice — non-blocking */}
    {llmFailed && (
      <div className="bg-yellow-50 border-l-4 border-yellow-400 p-4 mb-6">
        <div className="flex">
          <div className="flex-shrink-0">
            <ExclamationTriangleIcon className="h-5 w-5 text-yellow-400" aria-hidden="true" />
          </div>
          <div className="ml-3">
            <p className="text-sm text-yellow-700">
              We couldn't polish your wording — your own words are legally valid.
            </p>
          </div>
        </div>
      </div>
    )}

    {/* PDF error state */}
    {pdfError && (
      <div className="bg-red-50 border-l-4 border-red-400 p-4 mb-6">
        <div className="flex items-start">
          <div className="flex-shrink-0">
            <ExclamationTriangleIcon className="h-5 w-5 text-red-400" aria-hidden="true" />
          </div>
          <div className="ml-3 flex-1">
            <p className="text-sm text-red-700">{pdfError}</p>
          </div>
          <button
            onClick={onRetryPDF}
            disabled={generating}
            className="ml-4 text-sm font-medium text-red-700 underline hover:text-red-600 disabled:opacity-50"
          >
            Try Again
          </button>
        </div>
      </div>
    )}

    {/* Status Banner — only claim a rewrite when LLM output actually exists */}
    {hasLLMContent && !llmFailed && (
      <div className="bg-green-50 border-l-4 border-green-400 p-4 mb-6">
        <div className="flex">
          <div className="flex-shrink-0">
            <CheckCircleIcon className="h-5 w-5 text-green-400" aria-hidden="true" />
          </div>
          <div className="ml-3">
            <p className="text-sm text-green-700">
              Your motion has been processed and is ready for review. The content has been rewritten in proper legal format.
            </p>
          </div>
        </div>
      </div>
    )}
  </>
);
