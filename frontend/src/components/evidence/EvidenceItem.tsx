import React from 'react';
import { Evidence, TAG_LABELS, EvidenceTag } from './evidenceTypes';
import { TrashIcon } from '@heroicons/react/20/solid';

interface EvidenceItemProps {
  evidence: Evidence;
  onRemove: (id: string) => void;
}

export const EvidenceItem: React.FC<EvidenceItemProps> = ({ evidence, onRemove }) => (
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
                className="inline-flex items-center px-2 py-0.5 rounded text-xs font-medium bg-indigo-100 text-indigo-700"
              >
                {TAG_LABELS[tag as EvidenceTag] ?? tag}
              </span>
            ))}
          </div>
        )}
      </div>
      <button
        type="button"
        onClick={() => onRemove(evidence.id)}
        aria-label={`Remove evidence ${evidence.description}`}
        className="ml-3 text-gray-400 hover:text-red-500"
      >
        <TrashIcon className="h-4 w-4" />
      </button>
    </div>
  </div>
);
