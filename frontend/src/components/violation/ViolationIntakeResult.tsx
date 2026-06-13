import React, { useState } from 'react';
import { CheckCircleIcon, ClipboardDocumentIcon } from '@heroicons/react/20/solid';

interface Form {
  id: string;
  name: string;
  description: string;
  fileName: string;
  required: boolean;
}

interface Track {
  id: string;
  name: string;
  timeline: string;
  description: string;
  proofStandard?: string;
}

interface Courthouse {
  name: string;
  address: string;
  phone?: string;
}

interface ViolationFilingResult {
  track: string;
  trackName: string;
  timeline: string;
  forms: Form[];
  declaration: string;
  courthouse: Courthouse;
  instructions: string[];
  filingFee: string;
}

interface ViolationIntakeResultProps {
  result: ViolationFilingResult;
  allTracks: Track[];
}

const TRACK_DESCRIPTIONS: Record<string, string> = {
  emergency: 'Available when there is an immediate safety concern or ongoing harm. Heard within 24-48 hours. The moving party must show irreparable harm if relief is delayed.',
  regular: 'Standard enforcement track. A hearing is typically scheduled 3-6 weeks out. Proof standard is preponderance of the evidence.',
  contempt: 'A quasi-criminal proceeding. A higher proof standard applies (beyond reasonable doubt). The other party may face fines or jail if found in contempt.',
};

export const ViolationIntakeResult: React.FC<ViolationIntakeResultProps> = ({
  result,
  allTracks,
}) => {
  const [copied, setCopied] = useState(false);

  const handleCopy = async () => {
    try {
      await navigator.clipboard.writeText(result.declaration);
      setCopied(true);
      setTimeout(() => setCopied(false), 2000);
    } catch {
      // clipboard unavailable — silently fail
    }
  };

  return (
    <div className="space-y-8">
      {/* Determined track — neutral framing */}
      <div className="bg-white shadow rounded-lg p-6">
        <h2 className="text-xl font-semibold text-gray-900 mb-2">Filing Track</h2>
        <p className="text-gray-600 mb-4">
          Based on your answers, this matches the{' '}
          <span className="font-medium text-indigo-700">{result.trackName}</span> track (
          {result.timeline}).
        </p>
        <p className="text-sm text-gray-500">
          Review all tracks below to understand your options. You decide which path to take.
        </p>
      </div>

      {/* All tracks comparison */}
      <div className="bg-white shadow rounded-lg p-6">
        <h2 className="text-xl font-semibold text-gray-900 mb-4">All Filing Tracks</h2>
        <div className="space-y-4">
          {allTracks.map((track) => (
            <div
              key={track.id}
              className={`rounded-lg border p-4 ${
                track.id === result.track
                  ? 'border-indigo-500 bg-indigo-50'
                  : 'border-gray-200'
              }`}
            >
              <div className="flex items-center justify-between mb-1">
                <h3 className="font-medium text-gray-900">{track.name}</h3>
                <span className="text-sm text-gray-500">{track.timeline}</span>
              </div>
              <p className="text-sm text-gray-600">
                {TRACK_DESCRIPTIONS[track.id] || track.description}
              </p>
              {track.id === result.track && (
                <span className="mt-2 inline-flex items-center text-xs text-indigo-700 font-medium">
                  <CheckCircleIcon className="h-4 w-4 mr-1" />
                  Matches your answers
                </span>
              )}
            </div>
          ))}
        </div>
      </div>

      {/* Required forms */}
      <div className="bg-white shadow rounded-lg p-6">
        <h2 className="text-xl font-semibold text-gray-900 mb-4">Required Forms</h2>
        <ul className="divide-y divide-gray-100">
          {result.forms.map((form) => (
            <li key={form.id} className="py-3 flex items-start">
              <span className="inline-block w-20 text-xs font-mono text-gray-500 pt-0.5">
                {form.id}
              </span>
              <div>
                <p className="text-sm font-medium text-gray-900">{form.name}</p>
                <p className="text-xs text-gray-500">{form.description}</p>
              </div>
              {form.required && (
                <span className="ml-auto text-xs text-red-600 font-medium">Required</span>
              )}
            </li>
          ))}
        </ul>
      </div>

      {/* Courthouse */}
      <div className="bg-white shadow rounded-lg p-6">
        <h2 className="text-xl font-semibold text-gray-900 mb-2">Courthouse</h2>
        <p className="font-medium text-gray-900">{result.courthouse.name}</p>
        {result.courthouse.address && (
          <p className="text-sm text-gray-600 mt-1">{result.courthouse.address}</p>
        )}
        {result.courthouse.phone && (
          <p className="text-sm text-gray-600">{result.courthouse.phone}</p>
        )}
        <p className="mt-3 text-xs text-gray-500">
          Filing fee: {result.filingFee} (fee waivers available — ask the clerk for Form FW-001)
        </p>
      </div>

      {/* Declaration */}
      <div className="bg-white shadow rounded-lg p-6">
        <div className="flex items-center justify-between mb-4">
          <h2 className="text-xl font-semibold text-gray-900">Declaration Draft</h2>
          <button
            type="button"
            onClick={handleCopy}
            className="inline-flex items-center px-3 py-1.5 border border-gray-300 text-sm font-medium rounded-md text-gray-700 bg-white hover:bg-gray-50 focus:outline-none focus:ring-2 focus:ring-offset-2 focus:ring-indigo-500"
          >
            <ClipboardDocumentIcon className="h-4 w-4 mr-1.5" />
            {copied ? 'Copied!' : 'Copy Declaration'}
          </button>
        </div>
        <pre className="whitespace-pre-wrap text-sm text-gray-700 bg-gray-50 rounded p-4 border border-gray-200 max-h-96 overflow-y-auto">
          {result.declaration}
        </pre>
        <p className="mt-3 text-xs text-gray-500">
          This is a draft. Review it carefully and adjust the facts to match your situation
          before filing.
        </p>
      </div>
    </div>
  );
};
