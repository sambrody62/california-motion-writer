import React from 'react';
import { useNavigate, useParams } from 'react-router-dom';
import { DocumentTextIcon, ArrowLeftIcon, ExclamationTriangleIcon } from '@heroicons/react/24/outline';
import { FORM_METADATA, FORM_REQUIREMENTS, FormType } from '../../types/forms';

export const FormFlowSelector: React.FC = () => {
  const navigate = useNavigate();
  const { formType } = useParams<{ formType: string }>();

  const formMetadata = FORM_METADATA[formType as FormType];
  const formRequirements = FORM_REQUIREMENTS[formType as FormType];

  if (!formMetadata) {
    return (
      <div className="min-h-screen bg-gray-50 py-12">
        <div className="max-w-4xl mx-auto px-4 sm:px-6 lg:px-8 text-center">
          <h1 className="text-3xl font-bold text-gray-900 mb-3">Form Not Found</h1>
          <p className="text-lg text-gray-600 mb-6">The requested form type could not be found.</p>
          <button
            onClick={() => navigate('/dashboard')}
            className="inline-flex items-center text-sm text-indigo-600 hover:text-indigo-900"
          >
            <ArrowLeftIcon className="h-4 w-4 mr-1" />
            Back to Dashboard
          </button>
        </div>
      </div>
    );
  }

  const handleFormsFlow = () => {
    navigate(`/form/guided/${formType}`);
  };

  const getFormTypeDescription = () => {
    switch (formMetadata.category) {
      case 'emergency':
        return 'This is an emergency form requiring immediate court attention.';
      case 'financial':
        return 'This form requires detailed financial information.';
      case 'contempt':
        return 'This form is used to enforce existing court orders.';
      case 'service':
        return 'This form proves legal documents were properly served.';
      default:
        return 'Choose how you\'d like to complete this form.';
    }
  };

  return (
    <div className="min-h-screen bg-gray-50 py-12">
      <div className="max-w-4xl mx-auto px-4 sm:px-6 lg:px-8">
        {/* Back button */}
        <button
          onClick={() => navigate('/dashboard')}
          className="mb-6 inline-flex items-center text-sm text-gray-600 hover:text-gray-900"
        >
          <ArrowLeftIcon className="h-4 w-4 mr-1" />
          Back to Dashboard
        </button>

        {/* Header */}
        <div className="text-center mb-8">
          <h1 className="text-3xl font-bold text-gray-900 mb-3">
            {formMetadata.name} ({formMetadata.id})
          </h1>
          <p className="text-lg text-gray-600 mb-4">
            {formMetadata.description}
          </p>
          <p className="text-sm text-gray-500">
            {getFormTypeDescription()}
          </p>
        </div>

        {/* Requirements and Warnings */}
        {(formRequirements.prerequisites.length > 0 || formRequirements.warningMessage) && (
          <div className="mb-8 bg-yellow-50 border-l-4 border-yellow-400 p-4">
            <div className="flex">
              <div className="flex-shrink-0">
                <ExclamationTriangleIcon className="h-5 w-5 text-yellow-400" />
              </div>
              <div className="ml-3">
                <h3 className="text-sm font-medium text-yellow-800">Before You Start</h3>
                <div className="mt-2 text-sm text-yellow-700">
                  {formRequirements.prerequisites.length > 0 && (
                    <div className="mb-2">
                      <p className="font-medium">Prerequisites:</p>
                      <ul className="list-disc list-inside">
                        {formRequirements.prerequisites.map((prereq, index) => (
                          <li key={index}>{prereq}</li>
                        ))}
                      </ul>
                    </div>
                  )}
                  {formRequirements.warningMessage && (
                    <p className="font-medium text-yellow-800">{formRequirements.warningMessage}</p>
                  )}
                </div>
              </div>
            </div>
          </div>
        )}

        {/* Form complexity and time estimate */}
        <div className="text-center mb-8">
          <div className="inline-flex items-center space-x-4 bg-white rounded-lg px-6 py-3 shadow-sm">
            <span className={`inline-flex items-center px-3 py-1 rounded-full text-xs font-medium ${
              formMetadata.complexity === 'simple' ? 'bg-green-100 text-green-800' :
              formMetadata.complexity === 'moderate' ? 'bg-yellow-100 text-yellow-800' :
              'bg-red-100 text-red-800'
            }`}>
              {formMetadata.complexity} form
            </span>
            <span className="text-sm text-gray-600">
              Estimated time: {formMetadata.estimatedTime}
            </span>
          </div>
        </div>

        {/* Option Card */}
        <div className="max-w-md mx-auto">
          {/* Forms Option */}
          <button
            onClick={handleFormsFlow}
            className="group relative w-full bg-white rounded-2xl shadow-lg hover:shadow-xl transition-all duration-300 p-8 text-left border-2 border-transparent hover:border-blue-500"
          >
            <div className="absolute -top-3 left-6 bg-blue-500 text-white text-xs font-semibold px-3 py-1 rounded-full">
              Step-by-step guidance
            </div>

            <div className="flex flex-col items-center text-center">
              <div className="bg-blue-100 p-4 rounded-full mb-4 group-hover:bg-blue-200 transition-colors">
                <DocumentTextIcon className="h-12 w-12 text-blue-600" />
              </div>

              <h2 className="text-xl font-semibold text-gray-900 mb-3">
                📝 Guided Forms
              </h2>

              <p className="text-gray-600 mb-4">
                Fill out the form step-by-step with clear instructions and field explanations.
              </p>

              <ul className="text-left text-sm text-gray-500 space-y-2 w-full">
                <li className="flex items-start">
                  <span className="text-green-500 mr-2">✓</span>
                  <span>Structured step-by-step process</span>
                </li>
                <li className="flex items-start">
                  <span className="text-green-500 mr-2">✓</span>
                  <span>See all required fields upfront</span>
                </li>
                <li className="flex items-start">
                  <span className="text-green-500 mr-2">✓</span>
                  <span>Auto-fill from your profile</span>
                </li>
                <li className="flex items-start">
                  <span className="text-green-500 mr-2">✓</span>
                  <span>Direct and efficient</span>
                </li>
              </ul>

              <div className="mt-6 text-blue-600 font-medium group-hover:text-blue-700">
                Go to forms →
              </div>
            </div>
          </button>
        </div>

        {/* Required/Recommended Forms */}
        {(formRequirements.requiredForms.length > 0 || formRequirements.recommendedForms.length > 0) && (
          <div className="mt-12 bg-blue-50 border-l-4 border-blue-400 p-6">
            <h3 className="text-lg font-medium text-blue-900 mb-4">Related Forms</h3>

            {formRequirements.requiredForms.length > 0 && (
              <div className="mb-4">
                <h4 className="text-sm font-medium text-blue-800 mb-2">Required Forms:</h4>
                <ul className="text-sm text-blue-700 space-y-1">
                  {formRequirements.requiredForms.map((reqForm) => (
                    <li key={reqForm} className="flex items-center">
                      <span className="mr-2">•</span>
                      <span>{FORM_METADATA[reqForm]?.name} ({reqForm})</span>
                    </li>
                  ))}
                </ul>
              </div>
            )}

            {formRequirements.recommendedForms.length > 0 && (
              <div>
                <h4 className="text-sm font-medium text-blue-800 mb-2">Recommended Forms:</h4>
                <ul className="text-sm text-blue-700 space-y-1">
                  {formRequirements.recommendedForms.map((recForm) => (
                    <li key={recForm} className="flex items-center">
                      <span className="mr-2">•</span>
                      <span>{FORM_METADATA[recForm]?.name} ({recForm})</span>
                    </li>
                  ))}
                </ul>
              </div>
            )}
          </div>
        )}

        {/* Help text */}
        <div className="mt-12 text-center">
          <p className="text-sm text-gray-500">
            Each step has clear instructions, and your answers are saved as you move between steps.
          </p>
        </div>
      </div>
    </div>
  );
};