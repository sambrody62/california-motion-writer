import React from 'react';
import { ChevronLeftIcon, ChevronRightIcon, CheckIcon } from '@heroicons/react/20/solid';
import { QuestionField, Question } from './QuestionField';

interface IntakeStepFormProps {
  visibleQuestions: Question[];
  register: any;
  errors: Record<string, unknown>;
  prefilledFields: Set<string>;
  uploadPrefilledFields: Set<string>;
  currentStep: number;
  totalSteps: number;
  onPrevious: () => void;
  onFormSubmit: (e?: React.BaseSyntheticEvent) => Promise<void>;
}

export const IntakeStepForm: React.FC<IntakeStepFormProps> = ({
  visibleQuestions,
  register,
  errors,
  prefilledFields,
  uploadPrefilledFields,
  currentStep,
  totalSteps,
  onPrevious,
  onFormSubmit,
}) => (
  <form onSubmit={onFormSubmit} className="space-y-6">
    {visibleQuestions.map((question) => (
      <div key={question.id}>
        <label
          htmlFor={question.id}
          className="block text-sm font-medium text-gray-700"
        >
          {question.label}
          {question.required && <span className="text-red-500 ml-1">*</span>}
        </label>
        <QuestionField question={question} register={register} />
        {uploadPrefilledFields.has(question.id) ? (
          <p className="mt-1 text-xs text-primary-600">
            Filled from your uploaded motion — please verify
          </p>
        ) : prefilledFields.has(question.id) ? (
          <p className="mt-1 text-xs text-primary-600">
            Filled from your profile
          </p>
        ) : null}
        {question.help_text && (
          <p className="mt-1 text-sm text-gray-500">{question.help_text}</p>
        )}
        {errors[question.id] ? (
          <p className="mt-1 text-sm text-red-600">This field is required</p>
        ) : null}
      </div>
    ))}

    {/* Navigation Buttons */}
    <div className="flex justify-between pt-6">
      <button
        type="button"
        onClick={onPrevious}
        disabled={currentStep === 1}
        className="inline-flex items-center px-4 py-2 border border-gray-300 text-sm font-medium rounded-md text-gray-700 bg-white hover:bg-gray-50 focus:outline-none focus:ring-2 focus:ring-offset-2 focus:ring-primary-500 disabled:opacity-50 disabled:cursor-not-allowed"
      >
        <ChevronLeftIcon className="mr-2 -ml-1 h-5 w-5" />
        Previous
      </button>

      <button
        type="submit"
        className="inline-flex items-center px-4 py-2 border border-transparent text-sm font-medium rounded-md text-white bg-primary-600 hover:bg-primary-700 focus:outline-none focus:ring-2 focus:ring-offset-2 focus:ring-primary-500"
      >
        {currentStep === totalSteps ? (
          <>
            Complete
            <CheckIcon className="ml-2 -mr-1 h-5 w-5" />
          </>
        ) : (
          <>
            Next
            <ChevronRightIcon className="ml-2 -mr-1 h-5 w-5" />
          </>
        )}
      </button>
    </div>
  </form>
);
