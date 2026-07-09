import React, { useState } from 'react';
import { useNavigate } from 'react-router-dom';
import { useForm } from 'react-hook-form';
import {
  ChatBubbleBottomCenterTextIcon,
  DocumentDuplicateIcon,
  SparklesIcon,
  ArrowRightIcon,
  ClipboardDocumentIcon
} from '@heroicons/react/24/outline';

interface CaseIntakeForm {
  caseDescription: string;
  existingGameplan?: string;
  hasExistingGameplan: boolean;
}

export const CaseIntake: React.FC = () => {
  const navigate = useNavigate();
  const [isLoading, setIsLoading] = useState(false);
  const { register, handleSubmit, watch, setValue, formState: { errors } } = useForm<CaseIntakeForm>({
    defaultValues: {
      hasExistingGameplan: false
    }
  });

  // Radio values arrive from react-hook-form as the strings "true"/"false";
  // passing those straight to checked= makes "false" truthy
  const hasExistingGameplan = String(watch('hasExistingGameplan')) === 'true';

  const setHasExistingGameplan = (value: boolean) => {
    setValue('hasExistingGameplan', value);
  };

  const onSubmit = async (data: CaseIntakeForm) => {
    setIsLoading(true);
    try {
      // Navigate to gameplan creation with the case data
      navigate('/case/gameplan', {
        state: {
          caseDescription: data.caseDescription,
          existingGameplan: data.existingGameplan
        }
      });
    } catch (error) {
      console.error('Error processing case intake:', error);
    } finally {
      setIsLoading(false);
    }
  };

  return (
    <div className="min-h-screen bg-gray-50 py-8">
      <div className="max-w-4xl mx-auto px-4 sm:px-6 lg:px-8">

        {/* Header */}
        <div className="text-center mb-8">
          <div className="flex justify-center mb-4">
            <div className="bg-indigo-100 p-3 rounded-full">
              <ChatBubbleBottomCenterTextIcon className="h-8 w-8 text-indigo-600" />
            </div>
          </div>
          <h1 className="text-3xl font-bold text-gray-900 mb-3">
            Tell Us About Your Case
          </h1>
          <p className="text-lg text-gray-600 max-w-2xl mx-auto">
            Explain your family law situation and we'll help create an action plan and determine which court forms you need to file.
          </p>
        </div>

        {/* Main Form */}
        <div className="bg-white shadow-lg rounded-lg p-8">
          <form onSubmit={handleSubmit(onSubmit)} className="space-y-8">

            {/* Gameplan Option Toggle */}
            <div className="border-b border-gray-200 pb-6">
              <div className="grid grid-cols-1 gap-4 sm:grid-cols-2">
                <label className="relative">
                  <input
                    {...register('hasExistingGameplan')}
                    type="radio"
                    value="false"
                    checked={!hasExistingGameplan}
                    onChange={() => setHasExistingGameplan(false)}
                    className="sr-only"
                  />
                  <div
                    onClick={() => setHasExistingGameplan(false)}
                    className={`cursor-pointer rounded-lg border-2 p-4 ${
                    !hasExistingGameplan
                      ? 'border-indigo-500 bg-indigo-50'
                      : 'border-gray-300 bg-white hover:border-gray-400'
                  }`}>
                    <div className="flex items-center">
                      <SparklesIcon className="h-6 w-6 text-indigo-600 mr-3" />
                      <div>
                        <h3 className="text-sm font-medium text-gray-900">
                          I need help creating a plan
                        </h3>
                        <p className="text-sm text-gray-500">
                          Tell us your situation and we'll create an action plan
                        </p>
                      </div>
                    </div>
                  </div>
                </label>

                <label className="relative">
                  <input
                    {...register('hasExistingGameplan')}
                    type="radio"
                    value="true"
                    checked={hasExistingGameplan}
                    onChange={() => setHasExistingGameplan(true)}
                    className="sr-only"
                  />
                  <div
                    onClick={() => setHasExistingGameplan(true)}
                    className={`cursor-pointer rounded-lg border-2 p-4 ${
                    hasExistingGameplan
                      ? 'border-indigo-500 bg-indigo-50'
                      : 'border-gray-300 bg-white hover:border-gray-400'
                  }`}>
                    <div className="flex items-center">
                      <ClipboardDocumentIcon className="h-6 w-6 text-indigo-600 mr-3" />
                      <div>
                        <h3 className="text-sm font-medium text-gray-900">
                          I have an existing gameplan
                        </h3>
                        <p className="text-sm text-gray-500">
                          Paste your strategy and we'll determine the forms
                        </p>
                      </div>
                    </div>
                  </div>
                </label>
              </div>
            </div>

            {/* Case Description */}
            <div>
              <label htmlFor="caseDescription" className="block text-lg font-medium text-gray-900 mb-3">
                {hasExistingGameplan ? 'Describe your situation briefly' : 'Tell us about your family law case'}
              </label>

              {!hasExistingGameplan && (
                <div className="mb-4 bg-blue-50 border-l-4 border-blue-400 p-4">
                  <p className="text-sm text-blue-700 font-medium mb-2">
                    To create the best action plan, please answer these questions:
                  </p>
                  <ul className="text-sm text-blue-600 space-y-2 list-none">
                    <li>📍 <strong>Your current status:</strong> Are you married, separated, or divorced?</li>
                    <li>🎯 <strong>What you need help with:</strong> Custody change? Child/spousal support? Restraining order? Division of property?</li>
                    <li>👶 <strong>Children (if any):</strong> How many children, their ages, and who they currently live with?</li>
                    <li>⚠️ <strong>Urgent issues:</strong> Any safety concerns, violations of existing orders, or upcoming court dates?</li>
                    <li>📄 <strong>Existing orders:</strong> Do you have any current court orders or agreements in place?</li>
                    <li>📅 <strong>Timeline:</strong> When did you separate? Any important deadlines?</li>
                    <li>📍 <strong>Location:</strong> Which California county is your case in?</li>
                  </ul>
                  <div className="mt-3 p-3 bg-white rounded border border-blue-200">
                    <p className="text-xs text-blue-700 font-medium mb-1">Example response:</p>
                    <p className="text-xs text-blue-600 italic">
                      "I separated from my spouse 6 months ago after 10 years of marriage. We have two children (ages 8 and 12)
                      who currently live with me. My ex has them every other weekend but often cancels last minute. I want to
                      formalize a custody arrangement with me as primary custodian and get child support. My ex is self-employed
                      and claims to have no income but drives a new car. There's no court order yet. We're in San Diego County.
                      I'm worried because my ex mentioned taking the kids out of state."
                    </p>
                  </div>
                </div>
              )}

              <div className="mt-1">
                <textarea
                  {...register('caseDescription', {
                    required: 'Please describe your case situation',
                    minLength: { value: 50, message: 'Please provide at least 50 characters' }
                  })}
                  id="caseDescription"
                  rows={hasExistingGameplan ? 4 : 10}
                  className="block w-full border-gray-300 rounded-md shadow-sm focus:ring-indigo-500 focus:border-indigo-500 sm:text-sm"
                  placeholder={hasExistingGameplan
                    ? "Briefly describe your family law situation..."
                    : "Start here: 'I am [married/separated/divorced]. I need help with [custody/support/property/restraining order]. Here's my situation...'"
                  }
                />
              </div>
              {errors.caseDescription && (
                <p className="mt-2 text-sm text-red-600">{errors.caseDescription.message}</p>
              )}
              <p className="mt-2 text-sm text-gray-500">
                {hasExistingGameplan
                  ? 'Provide a brief overview since you already have a gameplan'
                  : '💡 Tip: Include specific details about your situation. The more information you provide, the more accurate your action plan will be.'
                }
              </p>
            </div>

            {/* Existing Gameplan */}
            {hasExistingGameplan && (
              <div>
                <label htmlFor="existingGameplan" className="block text-lg font-medium text-gray-900 mb-3">
                  Your existing gameplan
                </label>
                <div className="mt-1">
                  <textarea
                    {...register('existingGameplan', {
                      required: hasExistingGameplan ? 'Please paste your existing gameplan' : false
                    })}
                    id="existingGameplan"
                    rows={6}
                    className="block w-full border-gray-300 rounded-md shadow-sm focus:ring-indigo-500 focus:border-indigo-500 sm:text-sm"
                    placeholder="Paste your existing legal strategy or gameplan here. Include what forms you think you need, what you want to achieve, timeline, etc."
                  />
                </div>
                {errors.existingGameplan && (
                  <p className="mt-2 text-sm text-red-600">{errors.existingGameplan.message}</p>
                )}
                <p className="mt-2 text-sm text-gray-500">
                  We'll review your gameplan and help determine the correct California court forms to implement it
                </p>
              </div>
            )}

            {/* Helpful Examples */}
            {!hasExistingGameplan && (
              <div className="bg-blue-50 border-l-4 border-blue-400 p-4">
                <div className="flex">
                  <div className="flex-shrink-0">
                    <DocumentDuplicateIcon className="h-5 w-5 text-blue-400" />
                  </div>
                  <div className="ml-3">
                    <h3 className="text-sm font-medium text-blue-800">
                      Example situations we can help with:
                    </h3>
                    <div className="mt-2 text-sm text-blue-700">
                      <ul className="list-disc list-inside space-y-1">
                        <li>Requesting or modifying child custody and visitation schedules</li>
                        <li>Seeking child or spousal support modifications</li>
                        <li>Enforcing existing court orders (contempt actions)</li>
                        <li>Emergency requests for protection or temporary orders</li>
                        <li>Property and debt division issues</li>
                        <li>Proving service of legal documents</li>
                      </ul>
                    </div>
                  </div>
                </div>
              </div>
            )}

            {/* Submit Button */}
            <div className="flex justify-end">
              <button
                type="submit"
                disabled={isLoading}
                className="inline-flex items-center px-6 py-3 border border-transparent text-base font-medium rounded-md text-white bg-indigo-600 hover:bg-indigo-700 focus:outline-none focus:ring-2 focus:ring-offset-2 focus:ring-indigo-500 disabled:opacity-50 disabled:cursor-not-allowed"
              >
                {isLoading ? (
                  <>
                    <div className="animate-spin rounded-full h-5 w-5 border-b-2 border-white mr-2"></div>
                    Processing...
                  </>
                ) : (
                  <>
                    {hasExistingGameplan ? 'Review Gameplan' : 'Create Legal Strategy'}
                    <ArrowRightIcon className="ml-2 h-5 w-5" />
                  </>
                )}
              </button>
            </div>
          </form>
        </div>

        {/* Additional Help */}
        <div className="mt-8 text-center">
          <p className="text-sm text-gray-500">
            This information helps us create a personalized legal strategy for your California family law case.
          </p>
          <p className="text-sm text-gray-500 mt-1">
            All information is confidential and secure.
          </p>
        </div>
      </div>
    </div>
  );
};