import React, { useState, useEffect } from 'react';
import { useParams, useNavigate, useLocation } from 'react-router-dom';
import { motionAPI, documentAPI, evidenceAPI } from '../../services/api';
import { DocumentTextIcon, ArrowDownTrayIcon, PencilIcon, CheckCircleIcon, ExclamationTriangleIcon } from '@heroicons/react/20/solid';
import { format } from 'date-fns';

interface MotionDraft {
  id: string;
  step_number: number;
  step_name: string;
  question_data: any;
  llm_output: string;
  created_at: string;
}

interface Motion {
  id: string;
  motion_type: string;
  case_caption: string;
  case_number: string;
  filing_date: string;
  hearing_date: string;
  hearing_time: string;
  status: string;
}

interface LocationState {
  llmFailed?: boolean;
}

export const MotionPreview: React.FC = () => {
  const { motionId } = useParams<{ motionId: string }>();
  const navigate = useNavigate();
  const location = useLocation();
  const locationState = location.state as LocationState | null;

  const [motion, setMotion] = useState<Motion | null>(null);
  const [drafts, setDrafts] = useState<MotionDraft[]>([]);
  const [evidenceCount, setEvidenceCount] = useState(0);
  const [loading, setLoading] = useState(true);
  const [generating, setGenerating] = useState(false);
  const [pdfError, setPdfError] = useState<string | null>(null);

  const llmFailed = locationState?.llmFailed === true;

  useEffect(() => {
    loadMotionData();
  }, [motionId]);

  const loadMotionData = async () => {
    try {
      setLoading(true);
      const [motionResponse, draftsResponse] = await Promise.all([
        motionAPI.get(motionId!),
        (motionAPI as any).getDrafts(motionId!),
      ]);
      setMotion(motionResponse.data);
      setDrafts(draftsResponse.data.drafts || []);
      // Load evidence count — non-blocking, never prevents PDF generation
      try {
        const evidenceItems = await evidenceAPI.list(motionId!);
        setEvidenceCount(Array.isArray(evidenceItems) ? evidenceItems.length : 0);
      } catch {
        setEvidenceCount(0);
      }
    } catch (error) {
      console.error('Failed to load motion:', error);
      navigate('/dashboard');
    } finally {
      setLoading(false);
    }
  };

  const generatePDF = async () => {
    try {
      setGenerating(true);
      setPdfError(null);

      const response = await (documentAPI as any).generatePDFSync(motionId!);
      const blob = new Blob([response.data], { type: 'application/pdf' });
      const url = window.URL.createObjectURL(blob);

      const filename = `${motion?.motion_type || 'motion'}-${motion?.case_number || 'draft'}.pdf`;

      const link = document.createElement('a');
      link.href = url;
      link.download = filename;
      document.body.appendChild(link);
      link.click();
      document.body.removeChild(link);
      window.URL.revokeObjectURL(url);
    } catch (error) {
      console.error('Failed to generate PDF:', error);
      setPdfError(
        'PDF generation failed. Your draft is saved on our servers — try again or come back later.'
      );
    } finally {
      setGenerating(false);
    }
  };

  const editSection = (stepNumber: number) => {
    navigate(`/motion/${motionId}/edit/${stepNumber}`);
  };

  if (loading) {
    return (
      <div className="min-h-screen flex items-center justify-center">
        <div className="animate-spin rounded-full h-12 w-12 border-b-2 border-indigo-600"></div>
      </div>
    );
  }

  return (
    <div className="min-h-screen bg-gray-50 py-8">
      <div className="max-w-5xl mx-auto px-4 sm:px-6 lg:px-8">
        {/* Header */}
        <div className="bg-white shadow rounded-lg p-6 mb-6">
          <div className="flex justify-between items-start">
            <div>
              <h1 className="text-2xl font-bold text-gray-900">
                {motion?.case_caption || `${motion?.motion_type} Motion`}
              </h1>
              <p className="mt-1 text-sm text-gray-600">
                Case Number: {motion?.case_number || 'Draft'}
              </p>
              {motion?.hearing_date && (
                <p className="mt-1 text-sm text-gray-600">
                  Hearing: {format(new Date(motion.hearing_date), 'MMMM d, yyyy')} at {motion.hearing_time}
                </p>
              )}
            </div>
            <div className="flex space-x-3">
              <button
                onClick={() => navigate(`/motion/${motionId}/edit/1`)}
                className="inline-flex items-center px-4 py-2 border border-gray-300 rounded-md shadow-sm text-sm font-medium text-gray-700 bg-white hover:bg-gray-50"
              >
                <PencilIcon className="-ml-1 mr-2 h-5 w-5 text-gray-500" />
                Edit
              </button>
              <button
                onClick={generatePDF}
                disabled={generating}
                className="inline-flex items-center px-4 py-2 border border-transparent rounded-md shadow-sm text-sm font-medium text-white bg-indigo-600 hover:bg-indigo-700 disabled:opacity-50"
              >
                <ArrowDownTrayIcon className="-ml-1 mr-2 h-5 w-5" />
                {generating ? 'Generating...' : 'Download PDF'}
              </button>
            </div>
          </div>
        </div>

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
                onClick={generatePDF}
                disabled={generating}
                className="ml-4 text-sm font-medium text-red-700 underline hover:text-red-600 disabled:opacity-50"
              >
                Try Again
              </button>
            </div>
          </div>
        )}

        {/* Status Banner */}
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

        {/* Evidence & Exhibits section */}
        <div className="bg-white shadow rounded-lg p-5 mb-6">
          <button
            type="button"
            onClick={() => navigate(`/motion/${motionId}/evidence`)}
            aria-label={`Evidence & exhibits (${evidenceCount})`}
            className="w-full flex items-center justify-between group text-left"
          >
            <span className="text-base font-medium text-indigo-600 group-hover:text-indigo-500">
              Evidence &amp; exhibits ({evidenceCount})
            </span>
            <span className="text-sm text-gray-400 group-hover:text-gray-600">Manage →</span>
          </button>
        </div>

        {/* Motion Sections */}
        <div className="space-y-6">
          {drafts.map((draft) => (
            <div key={draft.id} className="bg-white shadow rounded-lg">
              <div className="px-6 py-4 border-b border-gray-200">
                <div className="flex justify-between items-center">
                  <h3 className="text-lg font-medium text-gray-900">
                    {draft.step_name}
                  </h3>
                  <button
                    onClick={() => editSection(draft.step_number)}
                    className="text-sm text-indigo-600 hover:text-indigo-500"
                  >
                    Edit
                  </button>
                </div>
              </div>
              <div className="px-6 py-4">
                {draft.llm_output ? (
                  <div className="prose max-w-none">
                    <div className="whitespace-pre-wrap text-gray-700">
                      {draft.llm_output}
                    </div>
                  </div>
                ) : (
                  <div className="space-y-3">
                    <div className="text-sm font-medium text-gray-500">Original Answers:</div>
                    {Object.entries(draft.question_data).map(([key, value]) => (
                      <div key={key} className="flex justify-between py-2 border-b border-gray-100">
                        <span className="text-sm font-medium text-gray-600">
                          {key.replace(/_/g, ' ').replace(/\b\w/g, l => l.toUpperCase())}:
                        </span>
                        <span className="text-sm text-gray-900">
                          {typeof value === 'object' ? JSON.stringify(value) : String(value)}
                        </span>
                      </div>
                    ))}
                  </div>
                )}
              </div>
            </div>
          ))}
        </div>

        {/* Confirmed evidence note */}
        <p className="mt-6 text-sm text-gray-500 text-center">
          Confirmed evidence is attached as lettered exhibits in your PDF packet.
        </p>

        {/* Action Buttons */}
        <div className="mt-4 flex justify-between">
          <button
            onClick={() => navigate('/dashboard')}
            className="inline-flex items-center px-4 py-2 border border-gray-300 rounded-md shadow-sm text-sm font-medium text-gray-700 bg-white hover:bg-gray-50"
          >
            Back to Dashboard
          </button>
          <div className="space-x-3">
            <button
              onClick={() => navigate(`/motion/${motionId}/edit/1`)}
              className="inline-flex items-center px-4 py-2 border border-gray-300 rounded-md shadow-sm text-sm font-medium text-gray-700 bg-white hover:bg-gray-50"
            >
              Make Changes
            </button>
            <button
              onClick={generatePDF}
              disabled={generating}
              className="inline-flex items-center px-4 py-2 border border-transparent rounded-md shadow-sm text-sm font-medium text-white bg-indigo-600 hover:bg-indigo-700 disabled:opacity-50"
            >
              <DocumentTextIcon className="-ml-1 mr-2 h-5 w-5" />
              {generating ? 'Generating PDF...' : 'Generate Final PDF'}
            </button>
          </div>
        </div>

        {/* Instructions */}
        <div className="mt-8 bg-blue-50 border-l-4 border-blue-400 p-4">
          <div className="flex">
            <div className="ml-3">
              <h3 className="text-sm font-medium text-blue-800">Next Steps</h3>
              <div className="mt-2 text-sm text-blue-700">
                <ol className="list-decimal list-inside space-y-1">
                  <li>Review all sections carefully for accuracy</li>
                  <li>Download the PDF and review the formatted document</li>
                  <li>Print the document on white 8.5" x 11" paper</li>
                  <li>Sign and date where indicated</li>
                  <li>File with the court clerk and serve on the other party</li>
                </ol>
              </div>
            </div>
          </div>
        </div>
      </div>
    </div>
  );
};
