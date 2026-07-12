import React, { useState, useEffect } from 'react';
import { useForm } from 'react-hook-form';
import { ChevronLeftIcon, ChevronRightIcon, CheckIcon } from '@heroicons/react/20/solid';
import { violationAPI, ViolationIntakePayload } from '../../services/api';
import { ViolationIntakeResult } from './ViolationIntakeResult';
import { Correction } from '../shared/CorrectionsList';
import { QuestionField, Question } from './ViolationQuestionField';

// ---------- Types ----------

interface WizardStep {
  step_number: number;
  step_name: string;
  description: string;
  questions: Question[];
}

export interface Track {
  id: string;
  name: string;
  timeline: string;
  description: string;
  proofStandard?: string;
}

export interface FilingResult {
  track: string;
  trackName: string;
  timeline: string;
  forms: any[];
  declaration: string;
  corrections?: Correction[];
  courthouse: { name: string; address: string; phone?: string };
  instructions: string[];
  filingFee: string;
}

// ---------- Helpers ----------

function parseSteps(questionsMap: Record<string, WizardStep>): WizardStep[] {
  return Object.values(questionsMap).sort(
    (a, b) => a.step_number - b.step_number
  );
}

function toArray(val: any): string[] {
  if (Array.isArray(val)) return val;
  // Checkbox groups register as `${id}.${option}`, so RHF collects them as
  // { 'Text messages': true, Emails: false, ... } — keep the checked options.
  if (val && typeof val === 'object') {
    return Object.keys(val).filter((k) => (val as any)[k]);
  }
  if (typeof val === 'string' && val) return val.split(',').map((s: string) => s.trim());
  return [];
}

function buildPayload(answers: Record<string, any>): ViolationIntakePayload {
  return {
    violationType: answers.violationType || '',
    urgency: answers.urgency === 'Yes' || answers.urgency === true,
    violationDates: toArray(answers.violationDates),
    violationDescription: answers.violationDescription || '',
    evidence: toArray(answers.evidence),
    attemptedResolution:
      answers.attemptedResolution === 'Yes' || answers.attemptedResolution === true,
    resolutionDescription: answers.resolutionDescription,
    priorViolations: answers.priorViolations === 'Yes' || answers.priorViolations === true,
    priorViolationsDescription: answers.priorViolationsDescription,
    requestedRelief: toArray(answers.requestedRelief),
  };
}

// ---------- Main component ----------

interface ViolationIntakeProps {
  onComplete?: (result: FilingResult) => void;
}

export const ViolationIntake: React.FC<ViolationIntakeProps> = ({ onComplete }) => {
  const [steps, setSteps] = useState<WizardStep[]>([]);
  const [allTracks, setAllTracks] = useState<Track[]>([]);
  const [currentStep, setCurrentStep] = useState(0);
  const [allAnswers, setAllAnswers] = useState<Record<string, any>>({});
  const [loading, setLoading] = useState(true);
  const [processing, setProcessing] = useState(false);
  const [result, setResult] = useState<FilingResult | null>(null);

  const { register, getValues, reset, formState: { errors } } = useForm();

  useEffect(() => {
    const fetchData = async () => {
      try {
        const [questionsData, tracksData] = await Promise.all([
          violationAPI.getIntakeQuestions(),
          violationAPI.getTracks(),
        ]);
        setSteps(parseSteps(questionsData.questions));
        setAllTracks(tracksData.tracks || []);
      } catch (err) {
        console.error('Failed to load violation intake data:', err);
      } finally {
        setLoading(false);
      }
    };
    fetchData();
  }, []);

  useEffect(() => {
    reset({});
  }, [currentStep, reset]);

  const totalSteps = steps.length;
  const isLastStep = currentStep === totalSteps - 1;
  const stepData = steps[currentStep] ?? null;

  const handleNext = () => {
    const data = getValues();
    setAllAnswers((prev) => ({ ...prev, ...data }));
    setCurrentStep((s) => s + 1);
  };

  const handleSubmitFinal = async () => {
    const data = getValues();
    const merged = { ...allAnswers, ...data };
    setAllAnswers(merged);
    setProcessing(true);
    try {
      const payload = buildPayload(merged);
      const filingResult = await violationAPI.process(payload);
      setResult(filingResult);
      if (onComplete) onComplete(filingResult);
    } catch (err) {
      console.error('Failed to process violation filing:', err);
    } finally {
      setProcessing(false);
    }
  };

  if (loading) {
    return (
      <div className="min-h-screen flex items-center justify-center">
        <div className="animate-spin rounded-full h-12 w-12 border-b-2 border-primary-600" />
      </div>
    );
  }

  if (processing) {
    return (
      <div className="min-h-screen flex items-center justify-center">
        <div className="text-center">
          <div className="animate-spin rounded-full h-12 w-12 border-b-2 border-primary-600 mx-auto mb-4" />
          <p className="text-gray-700 text-lg">Analyzing your answers…</p>
        </div>
      </div>
    );
  }

  if (result) {
    return (
      <div className="min-h-screen bg-gray-50 py-8">
        <div className="max-w-3xl mx-auto px-4 sm:px-6 lg:px-8">
          <ViolationIntakeResult result={result} allTracks={allTracks} />
        </div>
      </div>
    );
  }

  return (
    <div className="min-h-screen bg-gray-50 py-8">
      <div className="max-w-3xl mx-auto px-4 sm:px-6 lg:px-8">
        <div className="mb-8">
          <div className="flex items-center justify-between mb-2">
            <h2 className="text-lg font-medium text-gray-900">
              Enforcement / Violation Filing
            </h2>
            <span className="text-sm text-gray-500">
              Step {currentStep + 1} of {totalSteps}
            </span>
          </div>
          <div className="w-full bg-gray-200 rounded-full h-2.5">
            <div
              className="bg-primary-600 h-2.5 rounded-full transition-all duration-300"
              style={{ width: `${((currentStep + 1) / totalSteps) * 100}%` }}
            />
          </div>
        </div>

        <div className="bg-white shadow rounded-lg p-6">
          {stepData && (
            <>
              <h3 className="text-xl font-semibold text-gray-900 mb-2">
                {stepData.step_name}
              </h3>
              <p className="text-gray-600 mb-6">{stepData.description}</p>

              <div className="space-y-6">
                {stepData.questions.map((question) => (
                  <div key={question.id}>
                    <label
                      htmlFor={question.id}
                      className="block text-sm font-medium text-gray-700"
                    >
                      {question.label}
                      {question.required && <span className="text-red-500 ml-1">*</span>}
                    </label>
                    <QuestionField question={question} register={register} errors={errors} />
                    {question.help_text && (
                      <p className="mt-1 text-sm text-gray-500">{question.help_text}</p>
                    )}
                  </div>
                ))}

                <div className="flex justify-between pt-6">
                  <button
                    type="button"
                    onClick={() => currentStep > 0 && setCurrentStep((s) => s - 1)}
                    disabled={currentStep === 0}
                    className="inline-flex items-center px-4 py-2 border border-gray-300 text-sm font-medium rounded-md text-gray-700 bg-white hover:bg-gray-50 focus:outline-none focus:ring-2 focus:ring-offset-2 focus:ring-primary-500 disabled:opacity-50 disabled:cursor-not-allowed"
                  >
                    <ChevronLeftIcon className="mr-2 -ml-1 h-5 w-5" />
                    Previous
                  </button>

                  {isLastStep ? (
                    <button
                      type="button"
                      onClick={handleSubmitFinal}
                      className="inline-flex items-center px-4 py-2 border border-transparent text-sm font-medium rounded-md text-white bg-primary-600 hover:bg-primary-700 focus:outline-none focus:ring-2 focus:ring-offset-2 focus:ring-primary-500"
                    >
                      Submit <CheckIcon className="ml-2 -mr-1 h-5 w-5" />
                    </button>
                  ) : (
                    <button
                      type="button"
                      onClick={handleNext}
                      className="inline-flex items-center px-4 py-2 border border-transparent text-sm font-medium rounded-md text-white bg-primary-600 hover:bg-primary-700 focus:outline-none focus:ring-2 focus:ring-offset-2 focus:ring-primary-500"
                    >
                      Next <ChevronRightIcon className="ml-2 -mr-1 h-5 w-5" />
                    </button>
                  )}
                </div>
              </div>
            </>
          )}
        </div>

        <div className="mt-8 flex justify-center space-x-2">
          {steps.map((_, idx) => (
            <span
              key={idx}
              className={`h-2 w-2 rounded-full ${
                idx === currentStep ? 'bg-primary-600' : idx < currentStep ? 'bg-primary-400' : 'bg-gray-300'
              }`}
            />
          ))}
        </div>
      </div>
    </div>
  );
};

export default ViolationIntake;
