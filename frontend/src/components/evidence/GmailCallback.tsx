import React, { useEffect, useState } from 'react';
import { useNavigate, useSearchParams } from 'react-router-dom';
import { gmailEvidenceAPI } from '../../services/api';
import { TAG_LABELS } from './evidenceTypes';

interface EmailCandidate {
  message_id: string;
  subject: string;
  from: string;
  date: string;
  snippet: string;
  relevance_score?: number;
  relevance_reason?: string;
  suggested_tags?: string[];
}

const byRelevance = (a: EmailCandidate, b: EmailCandidate) =>
  (b.relevance_score ?? -1) - (a.relevance_score ?? -1);

export const GmailCallback: React.FC = () => {
  const [searchParams] = useSearchParams();
  const navigate = useNavigate();

  const [accessToken, setAccessToken] = useState<string | null>(null);
  const [motionId, setMotionId] = useState<string | null>(null);
  const [emails, setEmails] = useState<EmailCandidate[]>([]);
  const [rankingNotice, setRankingNotice] = useState<string | null>(null);
  const [selected, setSelected] = useState<Set<string>>(new Set());
  const [tagsByMessage, setTagsByMessage] = useState<Record<string, string[]>>({});
  const [status, setStatus] = useState<'loading' | 'selecting' | 'importing' | 'done' | 'error'>('loading');
  const [errorMsg, setErrorMsg] = useState('');

  useEffect(() => {
    const code = searchParams.get('code');
    const state = searchParams.get('state'); // motionId passed as state

    if (!code) {
      setStatus('error');
      setErrorMsg('No authorization code received.');
      return;
    }

    const run = async () => {
      try {
        const { access_token } = await gmailEvidenceAPI.exchangeCode(code);
        setAccessToken(access_token);
        setMotionId(state);

        const { emails: candidates, ranking_notice } = await gmailEvidenceAPI.scan(state ?? '', access_token);
        setEmails([...candidates].sort(byRelevance));
        setRankingNotice(ranking_notice);
        const seededTags: Record<string, string[]> = {};
        candidates.forEach((c) => {
          if (c.suggested_tags?.length) seededTags[c.message_id] = c.suggested_tags;
        });
        setTagsByMessage(seededTags);
        setStatus('selecting');
      } catch (err) {
        setStatus('error');
        setErrorMsg('Failed to connect Gmail. Please try again.');
      }
    };

    run();
  }, [searchParams]);

  const toggleSelect = (id: string) => {
    setSelected(prev => {
      const next = new Set(prev);
      if (next.has(id)) {
        next.delete(id);
      } else {
        next.add(id);
      }
      return next;
    });
  };

  const removeTag = (messageId: string, tag: string) => {
    setTagsByMessage(prev => ({
      ...prev,
      [messageId]: (prev[messageId] || []).filter(t => t !== tag),
    }));
  };

  const handleImport = async () => {
    if (!motionId || !accessToken || selected.size === 0) return;
    setStatus('importing');
    try {
      const ids = Array.from(selected);
      const tags: Record<string, string[]> = {};
      ids.forEach((id) => {
        if (id in tagsByMessage) tags[id] = tagsByMessage[id];
      });
      await gmailEvidenceAPI.import(motionId, accessToken, ids, tags);
      navigate(`/motion/${motionId}/evidence`);
    } catch (err) {
      setStatus('error');
      setErrorMsg('Import failed. Please try again.');
    }
  };

  if (status === 'loading') {
    return (
      <div className="min-h-screen bg-gray-50 flex items-center justify-center">
        <p className="text-gray-600">Connecting to Gmail…</p>
      </div>
    );
  }

  if (status === 'error') {
    return (
      <div className="min-h-screen bg-gray-50 flex items-center justify-center">
        <p role="alert" className="text-red-600">{errorMsg}</p>
      </div>
    );
  }

  return (
    <div className="min-h-screen bg-gray-50 py-10">
      <div className="max-w-2xl mx-auto bg-white rounded-lg shadow-sm p-6">
        <h1 className="text-xl font-semibold text-gray-900 mb-2">Select emails to import as evidence</h1>
        <p className="text-sm text-amber-700 bg-amber-50 border border-amber-200 rounded-md p-3 mb-3">
          Imported emails are saved as unconfirmed — review and confirm each before it becomes an exhibit.
        </p>
        {rankingNotice && (
          <p className="text-sm text-gray-700 bg-gray-100 border border-gray-200 rounded-md p-3 mb-3">
            {rankingNotice}
          </p>
        )}

        {emails.length === 0 ? (
          <p className="text-gray-500 text-sm">No relevant emails found.</p>
        ) : (
          <ul className="space-y-3 mb-6">
            {emails.map(email => (
              <li key={email.message_id} className="flex items-start gap-3 p-3 border border-gray-200 rounded-md">
                <input
                  type="checkbox"
                  id={`email-${email.message_id}`}
                  checked={selected.has(email.message_id)}
                  onChange={() => toggleSelect(email.message_id)}
                  className="mt-0.5 rounded border-gray-300 text-indigo-600"
                  aria-label={email.subject}
                />
                <div className="flex-1">
                  <label htmlFor={`email-${email.message_id}`} className="block cursor-pointer">
                    <p className="text-sm font-medium text-gray-900">
                      {email.subject}
                      {typeof email.relevance_score === 'number' && (
                        <span className="ml-2 inline-flex items-center rounded-full bg-indigo-100 px-2 py-0.5 text-xs font-medium text-indigo-700">
                          {Math.round(email.relevance_score * 100)}% match
                        </span>
                      )}
                    </p>
                    <p className="text-xs text-gray-500">{email.from} · {email.date}</p>
                    <p className="text-xs text-gray-600 mt-0.5">{email.snippet}</p>
                    {email.relevance_reason && (
                      <p className="text-xs text-indigo-600 mt-0.5">{email.relevance_reason}</p>
                    )}
                  </label>
                  {(tagsByMessage[email.message_id] || []).length > 0 && (
                    <div className="mt-1.5 flex flex-wrap gap-1.5">
                      {tagsByMessage[email.message_id].map(tag => (
                        <button
                          key={tag}
                          type="button"
                          onClick={() => removeTag(email.message_id, tag)}
                          aria-label={`remove tag ${TAG_LABELS[tag as keyof typeof TAG_LABELS] ?? tag}`}
                          className="inline-flex items-center gap-1 rounded-full bg-gray-100 px-2 py-0.5 text-xs text-gray-700 hover:bg-gray-200"
                          title="Click to remove this tag"
                        >
                          {TAG_LABELS[tag as keyof typeof TAG_LABELS] ?? tag}
                          <span aria-hidden="true">×</span>
                        </button>
                      ))}
                    </div>
                  )}
                </div>
              </li>
            ))}
          </ul>
        )}

        <div className="flex justify-end gap-3">
          <button
            type="button"
            onClick={() => navigate(-1)}
            className="px-4 py-2 text-sm font-medium text-gray-700 bg-white border border-gray-300 rounded-md hover:bg-gray-50"
          >
            Cancel
          </button>
          <button
            type="button"
            onClick={handleImport}
            disabled={selected.size === 0 || status === 'importing'}
            className="px-4 py-2 text-sm font-medium text-white bg-indigo-600 rounded-md hover:bg-indigo-700 disabled:opacity-50 disabled:cursor-not-allowed"
            aria-label="Import selected emails"
          >
            {status === 'importing' ? 'Importing…' : 'Import selected'}
          </button>
        </div>
      </div>
    </div>
  );
};
