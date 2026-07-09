import React from 'react';
import { ExclamationTriangleIcon } from '@heroicons/react/20/solid';

const AmberNotice: React.FC<{ children: React.ReactNode }> = ({ children }) => (
  <div className="mb-6 flex items-start gap-3 rounded-md border border-amber-300 bg-amber-50 p-4">
    <ExclamationTriangleIcon className="mt-0.5 h-5 w-5 flex-shrink-0 text-amber-500" aria-hidden="true" />
    <p className="text-sm text-amber-800">{children}</p>
  </div>
);

interface IntakeNoticesProps {
  uploadNotice: string | null;
  showUploadNotice: boolean;
  responseDeadline: string | null;
}

export const IntakeNotices: React.FC<IntakeNoticesProps> = ({
  uploadNotice,
  showUploadNotice,
  responseDeadline,
}) => (
  <>
    {uploadNotice && showUploadNotice && <AmberNotice>{uploadNotice}</AmberNotice>}

    {responseDeadline && (
      <AmberNotice>
        Responses are typically due{' '}
        <strong>9 court days after service</strong>:{' '}
        <strong>{responseDeadline}</strong>.{' '}
        Verify with your court.
      </AmberNotice>
    )}
  </>
);
