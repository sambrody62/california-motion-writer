import React from 'react';

interface MotionPreviewDeclarationProps {
  text: string;
}

/**
 * Renders a motion's generated declaration text. Violation motions store
 * their declaration on motion.generated_text and have no drafts, so this
 * is the only reviewable content before filing (real-LLM finding L14).
 */
export const MotionPreviewDeclaration: React.FC<MotionPreviewDeclarationProps> = ({ text }) => (
  <div className="bg-white shadow rounded-lg">
    <div className="px-6 py-4 border-b border-gray-200">
      <h3 className="text-lg font-medium text-gray-900">Declaration</h3>
    </div>
    <div className="px-6 py-4">
      <div className="prose max-w-none">
        <div className="whitespace-pre-wrap text-gray-700">{text}</div>
      </div>
    </div>
  </div>
);
