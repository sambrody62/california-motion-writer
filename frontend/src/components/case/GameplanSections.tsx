import React from 'react';
import { DocumentTextIcon } from '@heroicons/react/24/outline';
import { FORM_METADATA } from '../../types/forms';
import { GameplanData } from '../../utils/gameplanParser';

export const GameplanSections: React.FC<{ gameplan: GameplanData }> = ({ gameplan }) => (
  <>
    {/* Case Analysis */}
    <div className="bg-white shadow rounded-lg p-6 mb-6">
      <h2 className="text-xl font-semibold text-gray-900 mb-4">Case Analysis</h2>
      <p className="text-gray-700">{gameplan.analysis}</p>
    </div>

    {/* Recommended Strategy */}
    <div className="bg-white shadow rounded-lg p-6 mb-6">
      <h2 className="text-xl font-semibold text-gray-900 mb-4">Recommended Strategy</h2>
      <p className="text-gray-700">{gameplan.legalStrategy}</p>
    </div>

    {/* Recommended Forms */}
    <div className="bg-white shadow rounded-lg p-6 mb-6">
      <h2 className="text-xl font-semibold text-gray-900 mb-4">Required Court Forms</h2>
      <div className="grid grid-cols-1 gap-4 sm:grid-cols-2">
        {gameplan.recommendedForms.map((formType) => {
          const formMeta = FORM_METADATA[formType];
          return (
            <div key={formType} className="border border-gray-200 rounded-lg p-4">
              <div className="flex items-center">
                <DocumentTextIcon className="h-5 w-5 text-indigo-600 mr-3" />
                <div>
                  <h3 className="text-sm font-medium text-gray-900">
                    {formMeta.name} ({formMeta.id})
                  </h3>
                  <p className="text-sm text-gray-500">{formMeta.description}</p>
                </div>
              </div>
            </div>
          );
        })}
      </div>
    </div>

    {/* Timeline and Considerations */}
    <div className="grid grid-cols-1 lg:grid-cols-2 gap-6 mb-6">
      <div className="bg-white shadow rounded-lg p-6">
        <h2 className="text-xl font-semibold text-gray-900 mb-4">Timeline</h2>
        <p className="text-gray-700">{gameplan.timeline}</p>
      </div>

      <div className="bg-white shadow rounded-lg p-6">
        <h2 className="text-xl font-semibold text-gray-900 mb-4">Key Considerations</h2>
        <ul className="space-y-2">
          {gameplan.keyConsiderations.map((consideration, index) => (
            <li key={index} className="flex items-start">
              <span className="flex-shrink-0 h-2 w-2 bg-indigo-600 rounded-full mt-2 mr-3"></span>
              <span className="text-gray-700">{consideration}</span>
            </li>
          ))}
        </ul>
      </div>
    </div>

    {/* Next Steps */}
    <div className="bg-white shadow rounded-lg p-6 mb-6">
      <h2 className="text-xl font-semibold text-gray-900 mb-4">Next Steps</h2>
      <ol className="space-y-3">
        {gameplan.nextSteps.map((step, index) => (
          <li key={index} className="flex">
            <span className="flex-shrink-0 bg-indigo-600 text-white text-sm font-medium rounded-full h-6 w-6 flex items-center justify-center mr-3">
              {index + 1}
            </span>
            <span className="text-gray-700">{step}</span>
          </li>
        ))}
      </ol>
    </div>
  </>
);
