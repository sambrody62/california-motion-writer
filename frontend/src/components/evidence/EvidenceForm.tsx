import React, { useState, useEffect } from 'react';
import { TagPicker } from './TagPicker';
import { Evidence, EvidenceTag, EvidenceType } from './evidenceTypes';
import { gmailEnabled } from '../../utils/featureFlags';
import { GmailConnect } from './GmailConnect';

type InputPath = 'paste' | 'upload';

interface EvidenceFormProps {
  motionId: string;
  onSave: (payload: Omit<Evidence, 'id' | 'filename'> & {
    user_confirmed: boolean;
    file?: File;
  }) => Promise<void>;
  onCancel: () => void;
  /** OCR suggestion from a prior upload response. Pre-fills transcription textarea. */
  suggestedTranscription?: string;
}

export const EvidenceForm: React.FC<EvidenceFormProps> = ({
  onSave,
  onCancel,
  motionId,
  suggestedTranscription,
}) => {
  const [path, setPath] = useState<InputPath>('paste');
  const [evidenceType, setEvidenceType] = useState<EvidenceType>('text');
  const [description, setDescription] = useState('');
  const [messageText, setMessageText] = useState('');
  const [transcription, setTranscription] = useState('');
  const [sourceDate, setSourceDate] = useState('');
  const [tags, setTags] = useState<EvidenceTag[]>([]);
  const [confirmed, setConfirmed] = useState(false);
  const [file, setFile] = useState<File | null>(null);
  const [saving, setSaving] = useState(false);

  // Pre-fill transcription when a suggestion arrives (OCR result from backend)
  useEffect(() => {
    if (suggestedTranscription) {
      setTranscription(suggestedTranscription);
    }
  }, [suggestedTranscription]);

  const uploadSubmitEnabled = path === 'upload' && transcription.trim().length > 0;
  const pasteSubmitEnabled = path === 'paste';
  const submitEnabled = path === 'upload' ? uploadSubmitEnabled : pasteSubmitEnabled;

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    if (!submitEnabled) return;
    setSaving(true);
    try {
      await onSave({
        evidence_type: path === 'upload' ? (evidenceType as 'photo' | 'document') : evidenceType,
        tags,
        source_date: sourceDate || null,
        description,
        transcription: path === 'paste' ? messageText || null : transcription,
        user_confirmed: confirmed,
        ...(file ? { file } : {}),
      });
    } finally {
      setSaving(false);
    }
  };

  return (
    <form onSubmit={handleSubmit} className="space-y-5 bg-white border border-gray-200 rounded-lg p-6">
      {/* Path selector */}
      <div className="flex gap-6">
        <label className="flex items-center gap-2 cursor-pointer">
          <input
            type="radio"
            name="evidencePath"
            value="paste"
            checked={path === 'paste'}
            onChange={() => setPath('paste')}
            aria-label="Paste or type text"
          />
          <span className="text-sm font-medium text-gray-700">Paste / type text</span>
        </label>
        <label className="flex items-center gap-2 cursor-pointer">
          <input
            type="radio"
            name="evidencePath"
            value="upload"
            checked={path === 'upload'}
            onChange={() => setPath('upload')}
            aria-label="Upload file"
          />
          <span className="text-sm font-medium text-gray-700">Upload screenshot or PDF</span>
        </label>
      </div>

      {/* Evidence type */}
      <div>
        <label htmlFor="evidenceType" className="block text-sm font-medium text-gray-700 mb-1">
          Type
        </label>
        <select
          id="evidenceType"
          value={evidenceType}
          onChange={(e) => setEvidenceType(e.target.value as EvidenceType)}
          className="block w-full rounded-md border-gray-300 shadow-sm focus:border-indigo-500 focus:ring-indigo-500 text-sm"
        >
          <option value="text">Text message</option>
          <option value="email">Email</option>
          <option value="photo">Photo / screenshot</option>
          <option value="document">Document</option>
        </select>
      </div>

      {/* Description */}
      <div>
        <label htmlFor="description" className="block text-sm font-medium text-gray-700 mb-1">
          Description
        </label>
        <input
          id="description"
          type="text"
          value={description}
          onChange={(e) => setDescription(e.target.value)}
          placeholder="Brief description of this evidence"
          className="block w-full rounded-md border-gray-300 shadow-sm focus:border-indigo-500 focus:ring-indigo-500 text-sm"
          aria-label="Description"
        />
      </div>

      {/* Paste path: message text */}
      {path === 'paste' && (
        <div>
          <label htmlFor="messageText" className="block text-sm font-medium text-gray-700 mb-1">
            Message text
          </label>
          <textarea
            id="messageText"
            value={messageText}
            onChange={(e) => setMessageText(e.target.value)}
            rows={4}
            placeholder="Paste or type the exact message content here"
            className="block w-full rounded-md border-gray-300 shadow-sm focus:border-indigo-500 focus:ring-indigo-500 text-sm"
            aria-label="Message text"
          />
        </div>
      )}

      {/* Upload path: file input + required transcription */}
      {path === 'upload' && (
        <>
          <div>
            <label htmlFor="fileInput" className="block text-sm font-medium text-gray-700 mb-1">
              File
            </label>
            <input
              id="fileInput"
              type="file"
              accept="image/*,.pdf"
              onChange={(e) => setFile(e.target.files?.[0] ?? null)}
              className="block w-full text-sm text-gray-500"
            />
          </div>
          <div>
            <label htmlFor="transcription" className="block text-sm font-medium text-gray-700 mb-1">
              Type what the message says
              <span className="ml-1 text-red-500">*</span>
            </label>
            <p className="text-xs text-gray-500 mb-2">
              You must confirm the text before it can be used as an exhibit.
            </p>
            {suggestedTranscription && (
              <p className="text-xs text-amber-700 bg-amber-50 border border-amber-200 rounded-md px-3 py-2 mb-2">
                Suggested from your image — review and correct before confirming.
              </p>
            )}
            <textarea
              id="transcription"
              value={transcription}
              onChange={(e) => setTranscription(e.target.value)}
              rows={4}
              placeholder="Type out the exact text shown in the file"
              className="block w-full rounded-md border-gray-300 shadow-sm focus:border-indigo-500 focus:ring-indigo-500 text-sm"
              aria-label="Type what the message says"
            />
          </div>
        </>
      )}

      {/* Date */}
      <div>
        <label htmlFor="sourceDate" className="block text-sm font-medium text-gray-700 mb-1">
          Date of message / event
        </label>
        <input
          id="sourceDate"
          type="date"
          value={sourceDate}
          onChange={(e) => setSourceDate(e.target.value)}
          className="block rounded-md border-gray-300 shadow-sm focus:border-indigo-500 focus:ring-indigo-500 text-sm"
          aria-label="Date"
        />
      </div>

      {/* Tags */}
      <TagPicker selected={tags} onChange={setTags} />

      {/* Gmail import (feature flag gated) */}
      {gmailEnabled() && (
        <div>
          <p className="text-sm text-gray-600 mb-1">Import from Gmail</p>
          <GmailConnect motionId={motionId} accessToken="" />
        </div>
      )}

      {/* Confirmed accurate */}
      <label className="flex items-start gap-3 cursor-pointer">
        <input
          type="checkbox"
          checked={confirmed}
          onChange={(e) => setConfirmed(e.target.checked)}
          aria-label="Confirmed accurate"
          className="mt-0.5 rounded border-gray-300 text-indigo-600 focus:ring-indigo-500"
        />
        <span className="text-sm text-gray-700">
          <span className="font-medium">Confirmed accurate</span> — Only confirmed items are
          included as exhibits in your PDF packet.
        </span>
      </label>

      {/* Actions */}
      <div className="flex justify-end gap-3 pt-2">
        <button
          type="button"
          onClick={onCancel}
          className="px-4 py-2 text-sm font-medium text-gray-700 bg-white border border-gray-300 rounded-md hover:bg-gray-50"
        >
          Cancel
        </button>
        <button
          type="submit"
          disabled={!submitEnabled || saving}
          className="px-4 py-2 text-sm font-medium text-white bg-indigo-600 rounded-md hover:bg-indigo-700 disabled:opacity-50 disabled:cursor-not-allowed"
          aria-label="Save evidence"
        >
          {saving ? 'Saving…' : 'Save evidence'}
        </button>
      </div>
    </form>
  );
};
