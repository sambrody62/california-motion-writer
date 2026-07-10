import React, { useState } from 'react';
import { Evidence, TAG_LABELS, EvidenceTag } from './evidenceTypes';
import { TrashIcon } from '@heroicons/react/20/solid';

interface EvidenceItemProps {
  evidence: Evidence;
  onRemove: (id: string) => void;
}

export const EvidenceItem: React.FC<EvidenceItemProps> = ({ evidence, onRemove }) => {
  const [confirming, setConfirming] = useState(false);

  return (
    <div className="bg-white border border-gray-200 rounded-lg p-4">
      <div className="flex justify-between items-start">
        <div className="flex-1 min-w-0">
          <p className="text-sm font-medium text-gray-900 truncate">{evidence.description}</p>
          <p className="text-xs text-gray-500 mt-0.5">
            {evidence.evidence_type}
            {evidence.source_date ? ` · ${evidence.source_date}` : ''}
            {evidence.filename ? ` · ${evidence.filename}` : ''}
          </p>
          {evidence.tags.length > 0 && (
            <div className="flex flex-wrap gap-1 mt-2">
              {evidence.tags.map((tag) => (
                <span
                  key={tag}
                  className="inline-flex items-center px-2 py-0.5 rounded text-xs font-medium bg-primary-100 text-primary-700"
                >
                  {TAG_LABELS[tag as EvidenceTag] ?? tag}
                </span>
              ))}
            </div>
          )}
        </div>
        {confirming ? (
          <div className="ml-3 flex items-center gap-2">
            <button
              type="button"
              onClick={() => {
                setConfirming(false);
                onRemove(evidence.id);
              }}
              className="px-2 py-1 text-xs font-medium rounded-md text-white bg-red-600 hover:bg-red-700"
            >
              Confirm delete
            </button>
            <button
              type="button"
              onClick={() => setConfirming(false)}
              className="px-2 py-1 text-xs font-medium rounded-md text-gray-700 border border-gray-300 bg-white hover:bg-gray-50"
            >
              Cancel
            </button>
          </div>
        ) : (
          <button
            type="button"
            onClick={() => setConfirming(true)}
            aria-label={`Remove evidence ${evidence.description}`}
            className="ml-3 text-gray-400 hover:text-red-500"
          >
            <TrashIcon className="h-4 w-4" />
          </button>
        )}
      </div>
    </div>
  );
};
