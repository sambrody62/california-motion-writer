import React, { useState, useEffect, useRef } from 'react';
import { useNavigate, useLocation } from 'react-router-dom';
import { useForm } from 'react-hook-form';
import { motionAPI, intakeAPI } from '../../services/api';
import { FORM_METADATA, FormType, FORM_TYPES } from '../../types/forms';
import { addCourtDays, formatCourtDeadline } from '../../utils/courtDays';
import { Question } from './QuestionField';
import { ServedMotionUpload } from './ServedMotionUpload';
import { ServedMotionExtracted } from '../../services/servedMotionApi';
import { useMotionInit } from './useMotionInit';
import { useIntakePrefill } from './useIntakePrefill';
import { IntakeProgressBar, IntakeStepDots } from './IntakeProgress';
import { IntakeStepForm } from './IntakeStepForm';
import { IntakeNotices } from './IntakeNotices';

interface IntakeStep {
  step_number: number;
  step_name: string;
  description: string;
  questions: Question[];
  total_steps?: number;
}

interface GuidedIntakeProps {
  onComplete?: (motionId: string) => void;
}

export const GuidedIntake: React.FC<GuidedIntakeProps> = ({ onComplete }) => {
  const navigate = useNavigate();
  const location = useLocation();
  const locationState = location.state as any;

  const { motionId, currentFormType, initialStep, resumeAnswers, isResume } = useMotionInit();

  const isResponseForm =
    currentFormType === FORM_TYPES.FL_320 ||
    currentFormType === 'FL-320' ||
    currentFormType === 'Response';

  const [currentStep, setCurrentStep] = useState(initialStep);
  const [totalSteps, setTotalSteps] = useState(6);
  const [stepData, setStepData] = useState<IntakeStep | null>(null);
  const [loading, setLoading] = useState(true);
  const [processingLLM, setProcessingLLM] = useState(false);
  const [visibleQuestions, setVisibleQuestions] = useState<Question[]>([]);
  const [allAnswers, setAllAnswers] = useState<any>({});
  const [responseDeadline, setResponseDeadline] = useState<string | null>(null);
  // FL-320: skippable "upload the motion you were served" gate before step 1.
  // Resume skips it — the served motion was already handled on first entry.
  const [showUploadGate, setShowUploadGate] = useState(isResponseForm && !isResume);
  // Track last visible question IDs to avoid infinite update loops from evaluateConditionalQuestions
  const visibleQuestionIdsRef = useRef<string>('');

  const { register, handleSubmit, watch, reset, setValue, getValues, formState: { errors } } = useForm();
  const watchedValues = watch();

  const {
    prefilledFields,
    uploadNotice,
    uploadPrefilledFields,
    acceptUploadExtracted,
  } = useIntakePrefill({ stepData, getValues, setValue });

  const getFormTitle = () => {
    if (!currentFormType) return 'Form';
    if (currentFormType === 'RFO') return 'Request for Order (FL-300)';
    if (currentFormType === 'Response') return 'Response to RFO (FL-320)';
    const formMetadata = FORM_METADATA[currentFormType as FormType];
    return formMetadata ? `${formMetadata.name} (${formMetadata.id})` : currentFormType;
  };

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

  const handleUploadExtracted = (
    extracted: ServedMotionExtracted,
    notice: string | null
  ) => {
    acceptUploadExtracted(extracted, notice);
    setShowUploadGate(false);
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
    const context = { ...resumeAnswers, ...allAnswers, ...watchedValues };

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
        <IntakeProgressBar title={getFormTitle()} currentStep={currentStep} totalSteps={totalSteps} />

        {/* Step Content */}
        <div className="bg-white shadow rounded-lg p-6">
          {stepData && (
            <>
              <h3 className="text-xl font-semibold text-gray-900 mb-2">
                {stepData.step_name}
              </h3>
              <p className="text-gray-600 mb-6">{stepData.description}</p>

              <IntakeNotices
                uploadNotice={uploadNotice}
                showUploadNotice={currentStep === 1}
                responseDeadline={responseDeadline}
              />

              <IntakeStepForm
                visibleQuestions={visibleQuestions}
                register={register}
                errors={errors}
                prefilledFields={prefilledFields}
                uploadPrefilledFields={uploadPrefilledFields}
                currentStep={currentStep}
                totalSteps={totalSteps}
                onPrevious={goToPreviousStep}
                onFormSubmit={handleSubmit(onSubmit)}
              />
            </>
          )}
        </div>

        <IntakeStepDots
          currentStep={currentStep}
          totalSteps={totalSteps}
          onStepSelect={setCurrentStep}
        />
      </div>
    </div>
  );
};
