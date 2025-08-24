import React, { useState, useEffect } from 'react';
import { useParams, useNavigate } from 'react-router-dom';
import { useForm } from 'react-hook-form';
import { motionAPI, intakeAPI } from '../../services/api';
import { ChevronLeftIcon, ChevronRightIcon, CheckIcon } from '@heroicons/react/20/solid';

interface Question {
  id: string;
  type: string;
  label: string;
  required: boolean;
  options?: string[];
  placeholder?: string;
  help_text?: string;
  condition?: string;
  validation?: any;
}

interface IntakeStep {
  step_number: number;
  step_name: string;
  description: string;
  questions: Question[];
}

export const GuidedIntake: React.FC = () => {
  const { motionType } = useParams<{ motionType: string }>();
  const navigate = useNavigate();
  const [currentStep, setCurrentStep] = useState(1);
  const [totalSteps, setTotalSteps] = useState(6);
  const [stepData, setStepData] = useState<IntakeStep | null>(null);
  const [motionId, setMotionId] = useState<string | null>(null);
  const [loading, setLoading] = useState(true);
  const [visibleQuestions, setVisibleQuestions] = useState<Question[]>([]);
  const [allAnswers, setAllAnswers] = useState<any>({});
  const { register, handleSubmit, watch, reset, formState: { errors } } = useForm();

  const watchedValues = watch();

  useEffect(() => {
    initializeMotion();
  }, [motionType]);

  useEffect(() => {
    if (motionId) {
      loadStep(currentStep);
    }
  }, [motionId, currentStep]);

  useEffect(() => {
    if (stepData) {
      evaluateConditionalQuestions();
    }
  }, [stepData, watchedValues]);

  const initializeMotion = async () => {
    try {
      const response = await motionAPI.createMotion({
        motion_type: motionType,
        status: 'draft'
      });
      setMotionId(response.data.id);
    } catch (error) {
      console.error('Failed to create motion:', error);
      navigate('/dashboard');
    }
  };

  const loadStep = async (stepNumber: number) => {
    try {
      setLoading(true);
      const response = await intakeAPI.getQuestions(motionType!, stepNumber);
      setStepData(response.data);
      
      // Load any saved answers for this step
      if (motionId) {
        const draftsResponse = await motionAPI.getDrafts(motionId);
        const savedDraft = draftsResponse.data.drafts.find(
          (d: any) => d.step_number === stepNumber
        );
        if (savedDraft) {
          reset(savedDraft.question_data);
        } else {
          reset({});
        }
      }
    } catch (error) {
      console.error('Failed to load step:', error);
    } finally {
      setLoading(false);
    }
  };

  const evaluateConditionalQuestions = async () => {
    if (!stepData) return;

    const visible: Question[] = [];
    const context = { ...allAnswers, ...watchedValues };

    for (const question of stepData.questions) {
      if (!question.condition) {
        visible.push(question);
      } else {
        try {
          const response = await intakeAPI.evaluateCondition(question.condition, context);
          if (response.data.result) {
            visible.push(question);
          }
        } catch {
          // If evaluation fails, show the question
          visible.push(question);
        }
      }
    }

    setVisibleQuestions(visible);
  };

  const onSubmit = async (data: any) => {
    try {
      // Save answers for current step
      await motionAPI.saveDraft(motionId!, currentStep, data);
      
      // Update all answers context
      setAllAnswers({ ...allAnswers, ...data });

      if (currentStep < totalSteps) {
        setCurrentStep(currentStep + 1);
      } else {
        // Process with LLM and go to preview
        await motionAPI.processWithLLM(motionId!);
        navigate(`/motion/${motionId}/preview`);
      }
    } catch (error) {
      console.error('Failed to save step:', error);
    }
  };

  const goToPreviousStep = () => {
    if (currentStep > 1) {
      setCurrentStep(currentStep - 1);
    }
  };

  const renderQuestion = (question: Question) => {
    switch (question.type) {
      case 'text':
        return (
          <input
            {...register(question.id, { required: question.required })}
            type="text"
            className="mt-1 block w-full border-gray-300 rounded-md shadow-sm focus:ring-indigo-500 focus:border-indigo-500 sm:text-sm"
            placeholder={question.placeholder}
          />
        );

      case 'textarea':
        return (
          <textarea
            {...register(question.id, { required: question.required })}
            rows={4}
            className="mt-1 block w-full border-gray-300 rounded-md shadow-sm focus:ring-indigo-500 focus:border-indigo-500 sm:text-sm"
            placeholder={question.placeholder}
          />
        );

      case 'select':
        return (
          <select
            {...register(question.id, { required: question.required })}
            className="mt-1 block w-full pl-3 pr-10 py-2 text-base border-gray-300 focus:outline-none focus:ring-indigo-500 focus:border-indigo-500 sm:text-sm rounded-md"
          >
            <option value="">Choose...</option>
            {question.options?.map(option => (
              <option key={option} value={option}>{option}</option>
            ))}
          </select>
        );

      case 'radio':
        return (
          <div className="mt-2 space-y-2">
            {question.options?.map(option => (
              <label key={option} className="inline-flex items-center mr-4">
                <input
                  {...register(question.id, { required: question.required })}
                  type="radio"
                  value={option}
                  className="form-radio h-4 w-4 text-indigo-600"
                />
                <span className="ml-2">{option}</span>
              </label>
            ))}
          </div>
        );

      case 'checkbox':
        return (
          <div className="mt-2 space-y-2">
            {question.options?.map(option => (
              <label key={option} className="flex items-center">
                <input
                  {...register(`${question.id}.${option}`)}
                  type="checkbox"
                  className="form-checkbox h-4 w-4 text-indigo-600"
                />
                <span className="ml-2">{option}</span>
              </label>
            ))}
          </div>
        );

      case 'date':
        return (
          <input
            {...register(question.id, { required: question.required })}
            type="date"
            className="mt-1 block w-full border-gray-300 rounded-md shadow-sm focus:ring-indigo-500 focus:border-indigo-500 sm:text-sm"
          />
        );

      case 'time':
        return (
          <input
            {...register(question.id, { required: question.required })}
            type="time"
            className="mt-1 block w-full border-gray-300 rounded-md shadow-sm focus:ring-indigo-500 focus:border-indigo-500 sm:text-sm"
          />
        );

      case 'currency':
        return (
          <div className="mt-1 relative rounded-md shadow-sm">
            <div className="absolute inset-y-0 left-0 pl-3 flex items-center pointer-events-none">
              <span className="text-gray-500 sm:text-sm">$</span>
            </div>
            <input
              {...register(question.id, { required: question.required })}
              type="number"
              step="0.01"
              className="pl-7 block w-full border-gray-300 rounded-md shadow-sm focus:ring-indigo-500 focus:border-indigo-500 sm:text-sm"
              placeholder="0.00"
            />
          </div>
        );

      default:
        return null;
    }
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
      <div className="max-w-3xl mx-auto px-4 sm:px-6 lg:px-8">
        {/* Progress Bar */}
        <div className="mb-8">
          <div className="flex items-center justify-between mb-2">
            <h2 className="text-lg font-medium text-gray-900">
              {motionType === 'RFO' ? 'Request for Order' : 'Response to RFO'}
            </h2>
            <span className="text-sm text-gray-500">
              Step {currentStep} of {totalSteps}
            </span>
          </div>
          <div className="w-full bg-gray-200 rounded-full h-2.5">
            <div
              className="bg-indigo-600 h-2.5 rounded-full transition-all duration-300"
              style={{ width: `${(currentStep / totalSteps) * 100}%` }}
            ></div>
          </div>
        </div>

        {/* Step Content */}
        <div className="bg-white shadow rounded-lg p-6">
          {stepData && (
            <>
              <h3 className="text-xl font-semibold text-gray-900 mb-2">
                {stepData.step_name}
              </h3>
              <p className="text-gray-600 mb-6">{stepData.description}</p>

              <form onSubmit={handleSubmit(onSubmit)} className="space-y-6">
                {visibleQuestions.map((question) => (
                  <div key={question.id}>
                    <label className="block text-sm font-medium text-gray-700">
                      {question.label}
                      {question.required && <span className="text-red-500 ml-1">*</span>}
                    </label>
                    {renderQuestion(question)}
                    {question.help_text && (
                      <p className="mt-1 text-sm text-gray-500">{question.help_text}</p>
                    )}
                    {errors[question.id] && (
                      <p className="mt-1 text-sm text-red-600">This field is required</p>
                    )}
                  </div>
                ))}

                {/* Navigation Buttons */}
                <div className="flex justify-between pt-6">
                  <button
                    type="button"
                    onClick={goToPreviousStep}
                    disabled={currentStep === 1}
                    className="inline-flex items-center px-4 py-2 border border-gray-300 text-sm font-medium rounded-md text-gray-700 bg-white hover:bg-gray-50 focus:outline-none focus:ring-2 focus:ring-offset-2 focus:ring-indigo-500 disabled:opacity-50 disabled:cursor-not-allowed"
                  >
                    <ChevronLeftIcon className="mr-2 -ml-1 h-5 w-5" />
                    Previous
                  </button>

                  <button
                    type="submit"
                    className="inline-flex items-center px-4 py-2 border border-transparent text-sm font-medium rounded-md text-white bg-indigo-600 hover:bg-indigo-700 focus:outline-none focus:ring-2 focus:ring-offset-2 focus:ring-indigo-500"
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
            </>
          )}
        </div>

        {/* Step Indicators */}
        <div className="mt-8 flex justify-center space-x-2">
          {Array.from({ length: totalSteps }).map((_, index) => (
            <button
              key={index}
              onClick={() => setCurrentStep(index + 1)}
              className={`h-2 w-2 rounded-full ${
                index + 1 === currentStep
                  ? 'bg-indigo-600'
                  : index + 1 < currentStep
                  ? 'bg-indigo-400'
                  : 'bg-gray-300'
              }`}
            />
          ))}
        </div>
      </div>
    </div>
  );
};