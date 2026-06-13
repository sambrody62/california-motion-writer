import React from 'react';

export const EvidenceEmptyState: React.FC = () => (
  <div className="text-center py-12 px-4">
    <p className="text-lg font-medium text-gray-700 mb-2">No evidence added yet</p>
    <p className="text-sm text-gray-500 max-w-md mx-auto">
      Good evidence includes: exact dates, the exact words used, and who sent or said them.
      Screenshots, emails, and text messages work best when they show the date, the sender,
      and the complete message.
    </p>
  </div>
);
