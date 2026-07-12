import React, { useState } from 'react';
import { useParams, useNavigate } from 'react-router-dom';
import { ChatBubbleLeftRightIcon, ExclamationTriangleIcon } from '@heroicons/react/24/outline';
import { evidenceBatchAPI, BatchUploadResult } from '../../services/evidenceBatchApi';
import { BulkTranscriptReview } from './BulkTranscriptReview';

const MAX_FILES = 20;

export const BulkTextImport: React.FC = () => {
  const { motionId } = useParams<{ motionId: string }>();
  const navigate = useNavigate();

  const [uploading, setUploading] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const [result, setResult] = useState<BatchUploadResult | null>(null);

  const handleFiles = async (event: React.ChangeEvent<HTMLInputElement>) => {
    const files = Array.from(event.target.files || []);
    event.target.value = '';
    if (files.length === 0) return;
    if (files.length > MAX_FILES) {
      setError(`Too many screenshots — the maximum is ${MAX_FILES} per import.`);
      return;
    }
    try {
      setUploading(true);
      setError(null);
      setResult(await evidenceBatchAPI.batchUpload(motionId!, files));
    } catch {
      setError("We couldn't read those screenshots. Please try again.");
    } finally {
      setUploading(false);
    }
  };

  if (result) {
    return (
      <BulkTranscriptReview
        motionId={motionId!}
        result={result}
        onDone={() => navigate(`/motion/${motionId}/evidence`)}
        onStartOver={() => setResult(null)}
      />
    );
  }

  return (
    <div className="min-h-screen bg-gray-50 py-8">
      <div className="max-w-2xl mx-auto px-4 sm:px-6 lg:px-8">
        <div className="bg-white shadow rounded-lg p-8 text-center">
          <div className="flex justify-center mb-4">
            <div className="bg-primary-100 p-3 rounded-full">
              <ChatBubbleLeftRightIcon className="h-8 w-8 text-primary-600" />
            </div>
          </div>
          <h1 className="text-2xl font-bold text-gray-900 mb-2">
            Import text-message screenshots
          </h1>
          <p className="text-gray-600 mb-6">
            Select all the screenshots from one conversation — we'll read them and
            merge them into a single transcript you can review before saving.
          </p>

          {error && (
            <div className="bg-red-50 border-l-4 border-red-400 p-4 mb-6 text-left">
              <div className="flex">
                <ExclamationTriangleIcon className="h-5 w-5 text-red-400 flex-shrink-0" />
                <p className="ml-3 text-sm text-red-700">{error}</p>
              </div>
            </div>
          )}

          <label
            htmlFor="bulk-screenshots"
            className={`inline-flex items-center px-6 py-3 border border-transparent text-base font-medium rounded-md text-white ${
              uploading ? 'bg-primary-400 cursor-wait' : 'bg-primary-600 hover:bg-primary-700 cursor-pointer'
            }`}
          >
            {uploading ? 'Reading your screenshots…' : 'Choose screenshots (PNG or JPG)'}
          </label>
          <input
            id="bulk-screenshots"
            type="file"
            accept="image/png,image/jpeg"
            multiple
            className="sr-only"
            disabled={uploading}
            onChange={handleFiles}
            aria-label="Choose screenshots"
          />

          <div className="mt-6">
            <button
              type="button"
              onClick={() => navigate(`/motion/${motionId}/evidence`)}
              className="text-sm font-medium text-primary-600 hover:text-primary-500"
            >
              Back to evidence
            </button>
          </div>
          <p className="mt-6 text-xs text-gray-500">
            Up to {MAX_FILES} screenshots from one conversation per import.
          </p>
        </div>
      </div>
    </div>
  );
};
