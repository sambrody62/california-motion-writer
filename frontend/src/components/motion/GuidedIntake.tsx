import React, { useState, useEffect, useRef } from 'react';
import { useParams, useNavigate, useLocation } from 'react-router-dom';
import { useForm } from 'react-hook-form';
import { motionAPI, intakeAPI, profileAPI } from '../../services/api';
import { ChevronLeftIcon, ChevronRightIcon, CheckIcon, ExclamationTriangleIcon } from '@heroicons/react/20/solid';
import { FORM_METADATA, FormType, FORM_TYPES } from '../../types/forms';
import { addCourtDays, formatCourtDeadline } from '../../utils/courtDays';
import { QuestionField, Question } from './QuestionField';
import { ServedMotionUpload } from './ServedMotionUpload';
import { ServedMotionExtracted } from '../../services/servedMotionApi';

interface IntakeStep {
  step_number: number;
  step_name: string;
  description: string;
  questions: Question[];
  total_steps?: number;
}

// Fields that can be auto-filled from user profile
const PROFILE_FIELD_MAP: Record<string, string> = {
  party_name: 'party_name',
  other_party_name: 'other_party_name',
  case_number: 'case_number',
  county: 'county',
  children_info: 'children_info',
};

// Wizard fields the served-motion upload may pre-fill. date_served is
// deliberately absent — it's when the user was served, not in the document,
// and the response deadline depends on the user entering it themselves.
const SERVED_MOTION_FIELDS = [
  'case_number',
  'petitioner_name',
  'hearing_date',
  'hearing_time',
  'other_party_requests',
] as const;

interface GuidedIntakeProps {
  onComplete?: (motionId: string) => void;
}

export const GuidedIntake: React.FC<GuidedIntakeProps> = ({ onComplete }) => {
  const { motionType, formType } = useParams<{ motionType?: string; formType?: string }>();
  const navigate = useNavigate();
  const location = useLocation();
  const locationState = location.state as any;

  const currentFormType = formType || motionType;

  const isResponseForm =
    currentFormType === FORM_TYPES.FL_320 ||
    currentFormType === 'FL-320' ||
    currentFormType === 'Response';

  const [currentStep, setCurrentStep] = useState(1);
  const [totalSteps, setTotalSteps] = useState(6);
  const [stepData, setStepData] = useState<IntakeStep | null>(null);
  const [motionId, setMotionId] = useState<string | null>(null);
  const [loading, setLoading] = useState(true);
  const [processingLLM, setProcessingLLM] = useState(false);
  const [visibleQuestions, setVisibleQuestions] = useState<Question[]>([]);
  const [allAnswers, setAllAnswers] = useState<any>({});
  const [profile, setProfile] = useState<any>(null);
  const [prefilledFields, setPrefilledFields] = useState<Set<string>>(new Set());
  const [responseDeadline, setResponseDeadline] = useState<string | null>(null);
  // FL-320: skippable "upload the motion you were served" gate before step 1
  const [showUploadGate, setShowUploadGate] = useState(isResponseForm);
  const [uploadPrefill, setUploadPrefill] = useState<ServedMotionExtracted | null>(null);
  const [uploadNotice, setUploadNotice] = useState<string | null>(null);
  const [uploadPrefilledFields, setUploadPrefilledFields] = useState<Set<string>>(new Set());
  // Track last visible question IDs to avoid infinite update loops from evaluateConditionalQuestions
  const visibleQuestionIdsRef = useRef<string>('');

  const { register, handleSubmit, watch, reset, setValue, getValues, formState: { errors } } = useForm();
  const watchedValues = watch();

  const getFormTitle = () => {
    if (!currentFormType) return 'Form';
    if (currentFormType === 'RFO') return 'Request for Order (FL-300)';
    if (currentFormType === 'Response') return 'Response to RFO (FL-320)';
    const formMetadata = FORM_METADATA[currentFormType as FormType];
    return formMetadata ? `${formMetadata.name} (${formMetadata.id})` : currentFormType;
  };

  useEffect(() => {
    loadProfile();
    initializeMotion();
  }, [currentFormType]);

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

  // Apply profile autofill whenever profile and stepData are both loaded
  useEffect(() => {
    if (profile && stepData) {
      applyProfileAutofill();
    }
  }, [profile, stepData]);

  // Apply served-motion prefill whenever a step loads (upload wins over profile)
  useEffect(() => {
    if (uploadPrefill && stepData) {
      applyUploadPrefill();
    }
  }, [uploadPrefill, stepData]);

  // FL-320: compute response deadline whenever date_served changes
  useEffect(() => {
    if (!isResponseForm) return;

    const dateServed: string = watchedValues.date_served;
    if (!dateServed) {
      setResponseDeadline(null);
      return;
    }

    // Parse as local date to avoid UTC shift
    const [year, month, day] = dateServed.split('-').map(Number);
    const served = new Date(year, month - 1, day);
    const deadline = addCourtDays(served, 9);
    setResponseDeadline(formatCourtDeadline(deadline));
  }, [watchedValues.date_served, currentFormType]);

  const loadProfile = async () => {
    try {
      const data = await profileAPI.getProfile();
      setProfile(data);
    } catch {
      // No profile — autofill skipped silently
    }
  };

  const applyProfileAutofill = () => {
    if (!profile || !stepData) return;
    const newPrefilled = new Set<string>();

    stepData.questions.forEach((question) => {
      // Upload prefill owns these fields — the served motion is the better source
      if (uploadPrefill && question.id in uploadPrefill) return;
      const profileKey = PROFILE_FIELD_MAP[question.id];
      if (!profileKey) return;
      const profileValue = profile[profileKey];
      if (!profileValue) return;

      // Only fill if the field is currently empty
      const currentValue = getValues(question.id);
      if (!currentValue) {
        setValue(question.id, profileValue, { shouldValidate: false });
        newPrefilled.add(question.id);
      }
    });

    if (newPrefilled.size > 0) {
      setPrefilledFields(newPrefilled);
    }
  };

  const applyUploadPrefill = () => {
    if (!uploadPrefill || !stepData) return;
    const newPrefilled = new Set(uploadPrefilledFields);

    stepData.questions.forEach((question) => {
      const value = uploadPrefill[question.id as keyof ServedMotionExtracted];
      if (typeof value !== 'string' || !value) return;
      if (!getValues(question.id)) {
        setValue(question.id, value, { shouldValidate: false });
        newPrefilled.add(question.id);
      }
    });

    if (newPrefilled.size !== uploadPrefilledFields.size) {
      setUploadPrefilledFields(newPrefilled);
    }
  };

  const handleUploadExtracted = (
    extracted: ServedMotionExtracted,
    notice: string | null
  ) => {
    const allowed: ServedMotionExtracted = {};
    SERVED_MOTION_FIELDS.forEach((key) => {
      const value = extracted[key];
      if (typeof value === 'string' && value) {
        allowed[key] = value;
      }
    });
    setUploadPrefill(Object.keys(allowed).length > 0 ? allowed : null);
    setUploadNotice(notice);
    setShowUploadGate(false);
  };

  const initializeMotion = async () => {
    try {
      const response = await motionAPI.create({
        motion_type: currentFormType,
        status: 'draft',
      });
      const id = response?.data?.id || response?.id;
      setMotionId(id);
    } catch (error) {
      console.error('Failed to create motion:', error);
      navigate('/dashboard');
    }
  };

  const loadStep = async (stepNumber: number) => {
    try {
      setLoading(true);
      const response = await intakeAPI.getQuestions(currentFormType!, stepNumber);
      setStepData(response.data);

      if (response.data.total_steps) {
        setTotalSteps(response.data.total_steps);
      }

      if (motionId) {
        const drafts = await motionAPI.getDrafts(motionId);
        const savedDraft = (drafts || []).find(
          (d) => d.step_number === stepNumber
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
          const response = await (intakeAPI as any).evaluateCondition(question.condition, context);
          if (response.data.result) {
            visible.push(question);
          }
        } catch {
          visible.push(question);
        }
      }
    }

    // Only update state if visible question set actually changed (prevents render loops)
    const newIds = visible.map(q => q.id).join(',');
    if (newIds !== visibleQuestionIdsRef.current) {
      visibleQuestionIdsRef.current = newIds;
      setVisibleQuestions(visible);
    }
  };

  const onSubmit = async (data: any) => {
    try {
      await motionAPI.saveDraft(motionId!, {
        step_number: currentStep,
        step_name: stepData?.step_name || `step_${currentStep}`,
        question_data: data,
      });
      setAllAnswers({ ...allAnswers, ...data });

      if (currentStep < totalSteps) {
        setCurrentStep(currentStep + 1);
        return;
      }

      // Final step — process with LLM
      setProcessingLLM(true);
      let llmFailed = false;

      try {
        await motionAPI.processWithLLM(motionId!);
      } catch (llmError) {
        console.error('LLM processing failed, proceeding with user words:', llmError);
        llmFailed = true;
      } finally {
        setProcessingLLM(false);
      }

      if (onComplete) {
        onComplete(motionId!);
      }

      // If launched from FormExecution, navigate back to signal completion.
      // FormExecution is mounted at /case/forms — there is no /form/execution route.
      if (locationState?.fromFormExecution) {
        navigate('/case/forms', {
          state: {
            ...locationState,
            completedFormIndex: locationState.formExecutionFormIndex,
          },
        });
        return;
      }

      navigate(`/motion/${motionId}/preview`, {
        state: { llmFailed },
      });
    } catch (error) {
      console.error('Failed to save step:', error);
    }
  };

  const goToPreviousStep = () => {
    if (currentStep > 1) {
      setCurrentStep(currentStep - 1);
    }
  };

  // FL-320 gate: offer the served-motion upload before anything else renders
  if (showUploadGate) {
    return (
      <ServedMotionUpload
        onExtracted={handleUploadExtracted}
        onSkip={() => setShowUploadGate(false)}
      />
    );
  }

  // Show LLM processing screen — never a blank screen during this phase
  if (processingLLM) {
    return (
      <div className="min-h-screen flex items-center justify-center">
        <div className="text-center">
          <div className="animate-spin rounded-full h-12 w-12 border-b-2 border-indigo-600 mx-auto mb-4"></div>
          <p className="text-gray-700 text-lg">
            Reviewing your answers and drafting court language…
          </p>
        </div>
      </div>
    );
  }

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
              {getFormTitle()}
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

              {uploadNotice && currentStep === 1 && (
                <div className="mb-6 flex items-start gap-3 rounded-md border border-amber-300 bg-amber-50 p-4">
                  <ExclamationTriangleIcon className="mt-0.5 h-5 w-5 flex-shrink-0 text-amber-500" aria-hidden="true" />
                  <p className="text-sm text-amber-800">{uploadNotice}</p>
                </div>
              )}

              {responseDeadline && (
                <div className="mb-6 flex items-start gap-3 rounded-md border border-amber-300 bg-amber-50 p-4">
                  <ExclamationTriangleIcon className="mt-0.5 h-5 w-5 flex-shrink-0 text-amber-500" aria-hidden="true" />
                  <p className="text-sm text-amber-800">
                    Responses are typically due{' '}
                    <strong>9 court days after service</strong>:{' '}
                    <strong>{responseDeadline}</strong>.{' '}
                    Verify with your court.
                  </p>
                </div>
              )}

              <form onSubmit={handleSubmit(onSubmit)} className="space-y-6">
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
                      <p className="mt-1 text-xs text-indigo-600">
                        Filled from your uploaded motion — please verify
                      </p>
                    ) : prefilledFields.has(question.id) ? (
                      <p className="mt-1 text-xs text-indigo-600">
                        Filled from your profile
                      </p>
                    ) : null}
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
