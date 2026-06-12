import React, { useState, useEffect } from 'react';
import { useLocation, useNavigate } from 'react-router-dom';
import {
  DocumentTextIcon,
  CheckCircleIcon,
  ArrowRightIcon,
  ArrowLeftIcon,
  ClipboardDocumentListIcon
} from '@heroicons/react/24/outline';
import { FORM_METADATA, FormType } from '../../types/forms';

interface LocationState {
  gameplan: {
    analysis: string;
    legalStrategy: string;
    recommendedForms: FormType[];
    timeline: string;
    keyConsiderations: string[];
    nextSteps: string[];
  };
  caseDescription: string;
  sessionId: string;
}

interface FormExecutionProps {
  onComplete?: (completedFormIndex: number) => void;
}

export const FormExecution: React.FC<FormExecutionProps> = ({ onComplete }) => {
  const location = useLocation();
  const navigate = useNavigate();
  const [currentFormIndex, setCurrentFormIndex] = useState(0);
  const [completedForms, setCompletedForms] = useState<Set<number>>(new Set());

  const state = location.state as LocationState;

  useEffect(() => {
    if (!state?.gameplan) {
      navigate('/case/intake');
      return;
    }
  }, []);

  // Handle returning from GuidedIntake with a completion signal
  useEffect(() => {
    const returnState = location.state as any;
    if (returnState?.completedFormIndex !== undefined) {
      markFormComplete(returnState.completedFormIndex);
      if (onComplete) {
        onComplete(returnState.completedFormIndex);
      }
    }
  }, [location.state]);

  if (!state?.gameplan) {
    return null;
  }

  const { gameplan } = state;
  const forms = gameplan.recommendedForms;
  const currentForm = forms[currentFormIndex];
  const currentFormMeta = FORM_METADATA[currentForm];

  const startForm = (formType: FormType) => {
    navigate(`/form/guided/${formType}`, {
      state: {
        gameplan,
        caseDescription: state.caseDescription,
        sessionId: state.sessionId,
        fromFormExecution: true,
        formExecutionFormIndex: currentFormIndex,
      },
    });
  };

  const markFormComplete = (formIndex: number) => {
    setCompletedForms(prev => new Set(Array.from(prev).concat(formIndex)));
  };

  const goToNextForm = () => {
    if (currentFormIndex < forms.length - 1) {
      setCurrentFormIndex(currentFormIndex + 1);
    }
  };

  const goToPreviousForm = () => {
    if (currentFormIndex > 0) {
      setCurrentFormIndex(currentFormIndex - 1);
    }
  };

  const allFormsCompleted = completedForms.size === forms.length;

  return (
    <div className="min-h-screen bg-gray-50 py-8">
      <div className="max-w-4xl mx-auto px-4 sm:px-6 lg:px-8">

        {/* Header */}
        <div className="text-center mb-8">
          <div className="flex justify-center mb-4">
            <div className="bg-indigo-100 p-3 rounded-full">
              <ClipboardDocumentListIcon className="h-8 w-8 text-indigo-600" />
            </div>
          </div>
          <h1 className="text-3xl font-bold text-gray-900 mb-3">
            Fill Out Your Court Forms
          </h1>
          <p className="text-lg text-gray-600">
            Complete each form based on your legal strategy
          </p>
        </div>

        {/* Progress Overview */}
        <div className="bg-white shadow rounded-lg p-6 mb-8">
          <h2 className="text-xl font-semibold text-gray-900 mb-4">Progress Overview</h2>
          <div className="grid grid-cols-1 gap-4 sm:grid-cols-2 lg:grid-cols-3">
            {forms.map((formType, index) => {
              const formMeta = FORM_METADATA[formType];
              const isCompleted = completedForms.has(index);
              const isCurrent = index === currentFormIndex;

              return (
                <div
                  key={formType}
                  className={`border rounded-lg p-4 ${
                    isCurrent
                      ? 'border-indigo-500 bg-indigo-50'
                      : isCompleted
                      ? 'border-green-500 bg-green-50'
                      : 'border-gray-200 bg-white'
                  }`}
                >
                  <div className="flex items-center justify-between">
                    <div className="flex items-center">
                      <div className={`flex-shrink-0 h-8 w-8 rounded-full flex items-center justify-center ${
                        isCompleted
                          ? 'bg-green-600 text-white'
                          : isCurrent
                          ? 'bg-indigo-600 text-white'
                          : 'bg-gray-300 text-gray-600'
                      }`}>
                        {isCompleted ? (
                          <CheckCircleIcon className="h-5 w-5" />
                        ) : (
                          <span className="text-sm font-medium">{index + 1}</span>
                        )}
                      </div>
                      <div className="ml-3">
                        <h3 className="text-sm font-medium text-gray-900">
                          {formMeta.name}
                        </h3>
                        <p className="text-xs text-gray-500">{formMeta.id}</p>
                      </div>
                    </div>
                    {isCompleted && (
                      <CheckCircleIcon className="h-5 w-5 text-green-600" />
                    )}
                  </div>
                </div>
              );
            })}
          </div>
        </div>

        {!allFormsCompleted ? (
          <>
            {/* Current Form */}
            <div className="bg-white shadow rounded-lg p-6 mb-6">
              <div className="flex items-center justify-between mb-6">
                <div>
                  <h2 className="text-2xl font-semibold text-gray-900">
                    {currentFormMeta.name} ({currentFormMeta.id})
                  </h2>
                  <p className="text-gray-600 mt-1">{currentFormMeta.description}</p>
                </div>
                <div className="flex items-center space-x-2">
                  <span className={`inline-flex items-center px-3 py-1 rounded-full text-sm font-medium ${
                    currentFormMeta.complexity === 'simple' ? 'bg-green-100 text-green-800' :
                    currentFormMeta.complexity === 'moderate' ? 'bg-yellow-100 text-yellow-800' :
                    'bg-red-100 text-red-800'
                  }`}>
                    {currentFormMeta.complexity}
                  </span>
                  <span className="text-sm text-gray-500">
                    ~{currentFormMeta.estimatedTime}
                  </span>
                </div>
              </div>

              {/* Form Context from Gameplan */}
              <div className="bg-blue-50 border-l-4 border-blue-400 p-4 mb-6">
                <h3 className="text-sm font-medium text-blue-800 mb-2">
                  Why you need this form:
                </h3>
                <p className="text-sm text-blue-700">
                  Based on your case analysis, this form is needed to implement your legal strategy.
                  The information you provided will be used to pre-populate relevant fields.
                </p>
              </div>

              {/* Action Buttons */}
              <div className="flex justify-center">
                <button
                  onClick={() => startForm(currentForm)}
                  className="inline-flex items-center px-6 py-3 border border-transparent text-base font-medium rounded-md text-white bg-indigo-600 hover:bg-indigo-700 focus:outline-none focus:ring-2 focus:ring-offset-2 focus:ring-indigo-500"
                >
                  <DocumentTextIcon className="h-5 w-5 mr-2" />
                  Fill Out Form
                  <ArrowRightIcon className="h-5 w-5 ml-2" />
                </button>
              </div>
            </div>

            {/* Navigation */}
            <div className="flex justify-between">
              <button
                onClick={goToPreviousForm}
                disabled={currentFormIndex === 0}
                className="inline-flex items-center px-4 py-2 border border-gray-300 text-sm font-medium rounded-md text-gray-700 bg-white hover:bg-gray-50 focus:outline-none focus:ring-2 focus:ring-offset-2 focus:ring-indigo-500 disabled:opacity-50 disabled:cursor-not-allowed"
              >
                <ArrowLeftIcon className="h-4 w-4 mr-2" />
                Previous Form
              </button>

              <div className="text-center">
                <span className="text-sm text-gray-500">
                  Form {currentFormIndex + 1} of {forms.length}
                </span>
              </div>

              <button
                onClick={goToNextForm}
                disabled={currentFormIndex === forms.length - 1}
                className="inline-flex items-center px-4 py-2 border border-gray-300 text-sm font-medium rounded-md text-gray-700 bg-white hover:bg-gray-50 focus:outline-none focus:ring-2 focus:ring-offset-2 focus:ring-indigo-500 disabled:opacity-50 disabled:cursor-not-allowed"
              >
                Next Form
                <ArrowRightIcon className="h-4 w-4 ml-2" />
              </button>
            </div>
          </>
        ) : (
          /* All Forms Completed */
          <div className="bg-white shadow rounded-lg p-8 text-center">
            <div className="flex justify-center mb-6">
              <div className="bg-green-100 p-4 rounded-full">
                <CheckCircleIcon className="h-12 w-12 text-green-600" />
              </div>
            </div>
            <h2 className="text-2xl font-semibold text-gray-900 mb-4">
              All Forms Completed!
            </h2>
            <p className="text-lg text-gray-600 mb-8">
              You have successfully completed all the required forms for your case.
              Your documents are ready for review and filing.
            </p>
            <div className="space-y-4">
              <button
                onClick={() => navigate('/dashboard')}
                className="inline-flex items-center px-6 py-3 border border-transparent text-base font-medium rounded-md text-white bg-green-600 hover:bg-green-700 focus:outline-none focus:ring-2 focus:ring-offset-2 focus:ring-green-500"
              >
                View Your Documents
                <ArrowRightIcon className="h-5 w-5 ml-2" />
              </button>
            </div>
          </div>
        )}

        {/* Strategy Reminder */}
        <div className="mt-8 bg-gray-100 rounded-lg p-6">
          <h3 className="text-lg font-medium text-gray-900 mb-3">
            Remember Your Strategy
          </h3>
          <p className="text-gray-700 mb-4">{gameplan.legalStrategy}</p>
          <div className="text-sm text-gray-600">
            <strong>Timeline:</strong> {gameplan.timeline}
          </div>
        </div>
      </div>
    </div>
  );
};