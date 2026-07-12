import React, { useState, useEffect } from 'react';
import { useParams, useNavigate } from 'react-router-dom';
import { evidenceAPI } from '../../services/api';
import { Evidence } from './evidenceTypes';
import { EvidenceEmptyState } from './EvidenceEmptyState';
import { EvidenceForm } from './EvidenceForm';
import { EvidenceItem } from './EvidenceItem';
import { PlusIcon, ArrowLeftIcon } from '@heroicons/react/20/solid';

export const EvidenceManager: React.FC = () => {
  const { motionId } = useParams<{ motionId: string }>();
  const navigate = useNavigate();

  const [items, setItems] = useState<Evidence[]>([]);
  const [loading, setLoading] = useState(true);
  const [showForm, setShowForm] = useState(false);
  const [deleteError, setDeleteError] = useState<string | null>(null);
  const [saveError, setSaveError] = useState<string | null>(null);

  useEffect(() => {
    loadEvidence();
  }, [motionId]);

  const loadEvidence = async () => {
    try {
      setLoading(true);
      const data = await evidenceAPI.list(motionId!);
      setItems(Array.isArray(data) ? data : []);
    } catch {
      setItems([]);
    } finally {
      setLoading(false);
    }
  };

  const handleSave = async (payload: any) => {
    try {
      setSaveError(null);
      const { file, ...fields } = payload;
      if (file) {
        await evidenceAPI.upload(motionId!, file, fields);
      } else {
        await evidenceAPI.create(motionId!, fields);
      }
      setShowForm(false);
      await loadEvidence();
    } catch {
      setSaveError('Upload failed — your evidence was not saved. Please try again.');
    }
  };

  const handleRemove = async (id: string) => {
    try {
      setDeleteError(null);
      await evidenceAPI.remove(id);
      setItems((prev) => prev.filter((e) => e.id !== id));
    } catch {
      setDeleteError("We couldn't delete this item — check your connection and try again.");
    }
  };

  if (loading) {
    return (
      <div className="min-h-screen flex items-center justify-center">
        <div className="animate-spin rounded-full h-10 w-10 border-b-2 border-primary-600" />
      </div>
    );
  }

  return (
    <div className="min-h-screen bg-gray-50 py-8">
      <div className="max-w-3xl mx-auto px-4 sm:px-6 lg:px-8">
        {/* Header */}
        <div className="flex items-center justify-between mb-6">
          <div className="flex items-center gap-3">
            <button
              type="button"
              onClick={() => navigate(`/motion/${motionId}/preview`)}
              className="text-gray-500 hover:text-gray-700"
              aria-label="Back to motion"
            >
              <ArrowLeftIcon className="h-5 w-5" />
            </button>
            <h1 className="text-xl font-bold text-gray-900">
              Evidence &amp; Exhibits
            </h1>
          </div>
          <div className="flex items-center gap-2">
            <button
              type="button"
              onClick={() => navigate(`/motion/${motionId}/evidence/bulk-import`)}
              className="inline-flex items-center gap-1.5 px-4 py-2 text-sm font-medium text-primary-700 bg-primary-50 rounded-md hover:bg-primary-100"
              aria-label="Import text screenshots"
            >
              Import text screenshots
            </button>
            <button
              type="button"
              onClick={() => setShowForm(true)}
              className="inline-flex items-center gap-1.5 px-4 py-2 text-sm font-medium text-white bg-primary-600 rounded-md hover:bg-primary-700"
              aria-label="Add evidence"
            >
              <PlusIcon className="h-4 w-4" />
              Add evidence
            </button>
          </div>
        </div>

        {/* Add form */}
        {showForm && (
          <div className="mb-6">
            {saveError && (
              <div className="mb-4 bg-red-50 border-l-4 border-red-400 p-4">
                <p className="text-sm text-red-700">{saveError}</p>
              </div>
            )}
            <EvidenceForm
              motionId={motionId!}
              onSave={handleSave}
              onCancel={() => setShowForm(false)}
            />
          </div>
        )}

        {deleteError && (
          <div className="mb-4 bg-red-50 border-l-4 border-red-400 p-4">
            <p className="text-sm text-red-700">{deleteError}</p>
          </div>
        )}

        {/* List or empty state */}
        {items.length === 0 ? (
          <EvidenceEmptyState />
        ) : (
          <div className="space-y-3">
            {items.map((ev) => (
              <EvidenceItem key={ev.id} evidence={ev} onRemove={handleRemove} />
            ))}
          </div>
        )}
      </div>
    </div>
  );
};
