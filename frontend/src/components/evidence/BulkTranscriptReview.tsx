import React, { useState } from 'react';
import { ExclamationTriangleIcon } from '@heroicons/react/24/outline';
import { evidenceAPI } from '../../services/api';
import { BatchUploadResult } from '../../services/evidenceBatchApi';
import { TagPicker } from './TagPicker';
import { EvidenceTag } from './evidenceTypes';

interface BulkTranscriptReviewProps {
  motionId: string;
  result: BatchUploadResult;
  onDone: () => void;
  onStartOver: () => void;
}

export const BulkTranscriptReview: React.FC<BulkTranscriptReviewProps> = ({
  motionId,
  result,
  onDone,
  onStartOver,
}) => {
  const [transcription, setTranscription] = useState(result.merged_transcript);
  const [sourceDate, setSourceDate] = useState(result.suggested_source_date || '');
  const [tags, setTags] = useState<EvidenceTag[]>([]);
  const [confirmed, setConfirmed] = useState(false);
  const [saving, setSaving] = useState(false);
  const [error, setError] = useState<string | null>(null);

  const failedFiles = result.per_file.filter((f) => !f.ok);
  const okCount = result.per_file.length - failedFiles.length;

  const handleSave = async () => {
    try {
      setSaving(true);
      setError(null);
      await evidenceAPI.create(motionId, {
        evidence_type: 'text',
        tags,
        source_date: sourceDate || null,
        description: `Text message conversation (${okCount} screenshots)`,
        transcription,
        user_confirmed: true,
      });
      onDone();
    } catch {
      setError("We couldn't save this evidence. Please try again.");
      setSaving(false);
    }
  };

  return (
    <div className="min-h-screen bg-gray-50 py-8">
      <div className="max-w-3xl mx-auto px-4 sm:px-6 lg:px-8">
        <div className="bg-white shadow rounded-lg p-6 space-y-5">
          <h1 className="text-xl font-bold text-gray-900">Review the conversation</h1>

          {result.notice && (
            <div className="flex items-start gap-3 rounded-md border border-amber-300 bg-amber-50 p-4">
              <ExclamationTriangleIcon className="mt-0.5 h-5 w-5 flex-shrink-0 text-amber-500" />
              <p className="text-sm text-amber-800">{result.notice}</p>
            </div>
          )}

          {failedFiles.length > 0 && (
            <p className="text-sm text-gray-600">
              Couldn't read: {failedFiles.map((f) => f.filename).join(', ')}
            </p>
          )}

          {error && <p className="text-sm text-red-600">{error}</p>}

          <div>
            <label htmlFor="bulk-transcript" className="block text-sm font-medium text-gray-700">
              Transcript — check the order and wording, and fix anything that's wrong
            </label>
            <textarea
              id="bulk-transcript"
              rows={14}
              value={transcription}
              onChange={(e) => setTranscription(e.target.value)}
              className="mt-1 block w-full border-gray-300 rounded-md shadow-sm focus:ring-indigo-500 focus:border-indigo-500 sm:text-sm font-mono"
            />
          </div>

          <div>
            <label htmlFor="bulk-source-date" className="block text-sm font-medium text-gray-700">
              Conversation date (first message)
            </label>
            <input
              id="bulk-source-date"
              type="date"
              value={sourceDate}
              onChange={(e) => setSourceDate(e.target.value)}
              className="mt-1 block border-gray-300 rounded-md shadow-sm focus:ring-indigo-500 focus:border-indigo-500 sm:text-sm"
            />
          </div>

          <TagPicker selected={tags} onChange={setTags} />

          <label className="flex items-start gap-2">
            <input
              type="checkbox"
              checked={confirmed}
              onChange={(e) => setConfirmed(e.target.checked)}
              aria-label="I reviewed this transcript and it is accurate"
              className="mt-1 rounded border-gray-300 text-indigo-600 focus:ring-indigo-500"
            />
            <span className="text-sm text-gray-700">
              I reviewed this transcript and it is accurate. Only confirmed items are
              included as exhibits in your PDF packet.
            </span>
          </label>

          <div className="flex justify-between pt-2">
            <button
              type="button"
              onClick={onStartOver}
              className="inline-flex items-center px-4 py-2 border border-gray-300 text-sm font-medium rounded-md text-gray-700 bg-white hover:bg-gray-50"
            >
              Start over
            </button>
            <button
              type="button"
              onClick={handleSave}
              disabled={!confirmed || !transcription.trim() || saving}
              className="inline-flex items-center px-4 py-2 border border-transparent text-sm font-medium rounded-md text-white bg-indigo-600 hover:bg-indigo-700 disabled:opacity-50"
            >
              {saving ? 'Saving…' : 'Save to case'}
            </button>
          </div>
        </div>
      </div>
    </div>
  );
};
