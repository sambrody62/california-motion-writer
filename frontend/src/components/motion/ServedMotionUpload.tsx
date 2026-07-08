import React, { useState } from 'react';
import { DocumentArrowUpIcon, ExclamationTriangleIcon } from '@heroicons/react/24/outline';
import { servedMotionAPI, ServedMotionExtracted } from '../../services/servedMotionApi';

interface ServedMotionUploadProps {
  onExtracted: (extracted: ServedMotionExtracted, notice: string | null) => void;
  onSkip: () => void;
}

export const ServedMotionUpload: React.FC<ServedMotionUploadProps> = ({
  onExtracted,
  onSkip,
}) => {
  const [parsing, setParsing] = useState(false);
  const [error, setError] = useState<string | null>(null);

  const handleFile = async (event: React.ChangeEvent<HTMLInputElement>) => {
    const file = event.target.files?.[0];
    if (!file) return;
    try {
      setParsing(true);
      setError(null);
      const result = await servedMotionAPI.parse(file);
      onExtracted(result.extracted || {}, result.notice ?? null);
    } catch {
      setError(
        "We couldn't read that file. Try again, or skip and type in the details yourself."
      );
    } finally {
      setParsing(false);
      // allow re-selecting the same file after an error
      event.target.value = '';
    }
  };

  return (
    <div className="min-h-screen bg-gray-50 py-8">
      <div className="max-w-2xl mx-auto px-4 sm:px-6 lg:px-8">
        <div className="bg-white shadow rounded-lg p-8 text-center">
          <div className="flex justify-center mb-4">
            <div className="bg-indigo-100 p-3 rounded-full">
              <DocumentArrowUpIcon className="h-8 w-8 text-indigo-600" />
            </div>
          </div>
          <h1 className="text-2xl font-bold text-gray-900 mb-2">
            Do you have the motion you were served?
          </h1>
          <p className="text-gray-600 mb-6">
            Upload the Request for Order (FL-300) you received and we'll pre-fill
            your response with its details — you can review and change everything.
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
            htmlFor="served-motion-file"
            className={`inline-flex items-center px-6 py-3 border border-transparent text-base font-medium rounded-md text-white ${
              parsing ? 'bg-indigo-400 cursor-wait' : 'bg-indigo-600 hover:bg-indigo-700 cursor-pointer'
            }`}
          >
            {parsing ? 'Reading your document…' : 'Upload the motion (PDF or photo)'}
          </label>
          <input
            id="served-motion-file"
            type="file"
            accept=".pdf,image/png,image/jpeg"
            className="sr-only"
            disabled={parsing}
            onChange={handleFile}
          />

          <div className="mt-6">
            <button
              type="button"
              onClick={onSkip}
              disabled={parsing}
              className="text-sm font-medium text-indigo-600 hover:text-indigo-500 disabled:opacity-50"
            >
              Skip — I'll type it in myself
            </button>
          </div>

          <p className="mt-6 text-xs text-gray-500">
            Your file is read once to pre-fill answers and never stored.
          </p>
        </div>
      </div>
    </div>
  );
};
