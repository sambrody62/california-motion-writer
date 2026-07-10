import React, { useState, useEffect } from 'react';
import { useLocation, useNavigate } from 'react-router-dom';
import { useForm } from 'react-hook-form';
import {
  SparklesIcon,
  CheckCircleIcon,
  ArrowRightIcon,
  PencilIcon,
  ExclamationTriangleIcon
} from '@heroicons/react/24/outline';
import { chat } from '../../services/api';
import {
  GameplanData,
  parseLLMResponse,
  extractResponseText,
  detectsEnforcementIntent,
} from '../../utils/gameplanParser';
import { GameplanSections } from './GameplanSections';
import { EnforcementTriage } from './EnforcementTriage';

interface LocationState {
  caseDescription: string;
  existingGameplan?: string;
}

export const GameplanCreation: React.FC = () => {
  const location = useLocation();
  const navigate = useNavigate();
  const [loading, setLoading] = useState(true);
  const [gameplan, setGameplan] = useState<GameplanData | null>(null);
  const [isFallback, setIsFallback] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const [sessionId, setSessionId] = useState<string | null>(null);
  const [showEnforcementTriage, setShowEnforcementTriage] = useState(false);

  const { register, handleSubmit, watch, setValue } = useForm({
    defaultValues: {
      customization: ''
    }
  });

  const customization = watch('customization');
  const state = location.state as LocationState;

  useEffect(() => {
    if (!state?.caseDescription) {
      navigate('/case/intake');
      return;
    }
    createGameplan();
  }, []);

  const createGameplan = async () => {
    try {
      setLoading(true);
      setError(null);

      // Create a chat session for gameplan creation
      const sessionResponse = await chat.createSession();
      const newSessionId = sessionResponse.session_id;
      setSessionId(newSessionId);

      // Prepare the prompt for LLM
      const prompt = state.existingGameplan
        ? `I have a California family law case. Here's my situation: ${state.caseDescription}

I already have this gameplan: ${state.existingGameplan}

Please review my existing gameplan and help me determine:
1. Analysis of my legal situation
2. Refined legal strategy
3. Which specific California court forms I need to file (choose from: FL-300, FL-320, D-046, FL-305, FL-150, FL-335, FL-410, FL-411, MC-030)
4. Recommended timeline
5. Key legal considerations I should know
6. Next steps to take

Please provide a structured response focusing on practical action steps.`
        : `I have a California family law case. Here's my situation: ${state.caseDescription}

Please help me create a comprehensive legal gameplan including:
1. Analysis of my legal situation and rights
2. Recommended legal strategy
3. Which specific California court forms I need to file (choose from: FL-300, FL-320, D-046, FL-305, FL-150, FL-335, FL-410, FL-411, MC-030)
4. Recommended timeline for filing
5. Key legal considerations and potential challenges
6. Step-by-step next actions

Please provide specific, actionable guidance for my California family law case.`;

      // Send message to get gameplan
      const messageResponse = await chat.sendMessage(newSessionId, prompt);
      const responseText = extractResponseText(messageResponse);

      // Parse the LLM response into structured data
      const parsed = parseLLMResponse(responseText);
      setGameplan(parsed.data);
      setIsFallback(parsed.isFallback);

      // Check whether the case description or response mentions violations/enforcement
      const combinedText = `${state.caseDescription} ${responseText}`;
      setShowEnforcementTriage(detectsEnforcementIntent(combinedText));

    } catch (error) {
      console.error('Error creating gameplan:', error);
      setError('Failed to create gameplan. Please try again.');
    } finally {
      setLoading(false);
    }
  };

  const refineGameplan = async (data: { customization: string }) => {
    if (!sessionId || !data.customization.trim()) return;

    try {
      setLoading(true);
      const refinePrompt = `Based on our previous discussion, please refine the gameplan with this additional input: ${data.customization}

Please provide an updated structured response with any necessary changes to the strategy, forms, or timeline.`;

      const messageResponse = await chat.sendMessage(sessionId, refinePrompt);
      const responseText = extractResponseText(messageResponse);

      const parsed = parseLLMResponse(responseText);
      setGameplan(parsed.data);
      setIsFallback(parsed.isFallback);
      setValue('customization', '');

      const combinedText = `${state.caseDescription} ${data.customization} ${responseText}`;
      setShowEnforcementTriage(detectsEnforcementIntent(combinedText));
    } catch (error) {
      console.error('Error refining gameplan:', error);
      setError('Failed to refine gameplan. Please try again.');
    } finally {
      setLoading(false);
    }
  };

  const proceedToForms = () => {
    if (!gameplan) return;

    // Navigate to form filling with the gameplan and recommended forms
    navigate('/case/forms', {
      state: {
        gameplan,
        caseDescription: state.caseDescription,
        sessionId
      }
    });
  };

  if (loading) {
    return (
      <div className="min-h-screen bg-gray-50 flex items-center justify-center">
        <div className="text-center">
          <div className="animate-spin rounded-full h-12 w-12 border-b-2 border-primary-600 mx-auto mb-4"></div>
          <h3 className="text-lg font-medium text-gray-900 mb-2">Preparing Your Action Plan</h3>
          <p className="text-gray-600">Analyzing your case and determining the best approach...</p>
        </div>
      </div>
    );
  }

  if (error) {
    return (
      <div className="min-h-screen bg-gray-50 py-8">
        <div className="max-w-4xl mx-auto px-4 sm:px-6 lg:px-8">
          <div className="bg-red-50 border-l-4 border-red-400 p-4">
            <div className="flex">
              <div className="flex-shrink-0">
                <ExclamationTriangleIcon className="h-5 w-5 text-red-400" />
              </div>
              <div className="ml-3">
                <h3 className="text-sm font-medium text-red-800">Error Creating Gameplan</h3>
                <p className="text-sm text-red-700 mt-1">{error}</p>
                <div className="mt-4">
                  <button
                    onClick={() => navigate('/case/intake')}
                    className="text-sm font-medium text-red-800 hover:text-red-900 underline"
                  >
                    Start over
                  </button>
                </div>
              </div>
            </div>
          </div>
        </div>
      </div>
    );
  }

  return (
    <div className="min-h-screen bg-gray-50 py-8">
      <div className="max-w-4xl mx-auto px-4 sm:px-6 lg:px-8">

        {/* Header — honest about whether the plan is personalized */}
        <div className="text-center mb-8">
          {isFallback ? (
            <>
              <div className="flex justify-center mb-4">
                <div className="bg-amber-100 p-3 rounded-full">
                  <ExclamationTriangleIcon className="h-8 w-8 text-amber-600" />
                </div>
              </div>
              <h1 className="text-3xl font-bold text-gray-900 mb-3">
                We couldn't generate a personalized plan
              </h1>
              <p className="text-lg text-gray-600">
                Here's a general checklist to get you started — these steps are not tailored to your case.
              </p>
            </>
          ) : (
            <>
              <div className="flex justify-center mb-4">
                <div className="bg-green-100 p-3 rounded-full">
                  <CheckCircleIcon className="h-8 w-8 text-green-600" />
                </div>
              </div>
              <h1 className="text-3xl font-bold text-gray-900 mb-3">
                Your Action Plan
              </h1>
              <p className="text-lg text-gray-600">
                Here's your personalized action plan based on your case details
              </p>
            </>
          )}
        </div>

        {gameplan && (
          <>
            <GameplanSections gameplan={gameplan} />

            {/* Refinement Section */}
            <div className="bg-white shadow rounded-lg p-6 mb-6">
              <h2 className="text-xl font-semibold text-gray-900 mb-4">
                Want to refine this plan?
              </h2>
              <form onSubmit={handleSubmit(refineGameplan)} className="space-y-4">
                <div>
                  <label htmlFor="customization" className="block text-sm font-medium text-gray-700 mb-2">
                    Ask for adjustments or provide additional details
                  </label>
                  <textarea
                    {...register('customization')}
                    id="customization"
                    rows={3}
                    className="block w-full border-gray-300 rounded-md shadow-sm focus:ring-primary-500 focus:border-primary-500 sm:text-sm"
                    placeholder="e.g., I also need help with emergency custody, or I have a restraining order that affects this case..."
                  />
                </div>
                <button
                  type="submit"
                  disabled={!customization?.trim() || loading}
                  className="inline-flex items-center px-4 py-2 border border-gray-300 shadow-sm text-sm font-medium rounded-md text-gray-700 bg-white hover:bg-gray-50 focus:outline-none focus:ring-2 focus:ring-offset-2 focus:ring-primary-500 disabled:opacity-50 disabled:cursor-not-allowed"
                >
                  <PencilIcon className="h-4 w-4 mr-2" />
                  Refine Plan
                </button>
              </form>
            </div>

            {showEnforcementTriage && (
              <EnforcementTriage
                onProceedRFO={proceedToForms}
                onProceedViolation={() => navigate('/violation/intake')}
              />
            )}

            {/* Proceed Button */}
            <div className="text-center">
              <button
                onClick={proceedToForms}
                className="inline-flex items-center px-8 py-4 border border-transparent text-lg font-medium rounded-md text-white bg-primary-600 hover:bg-primary-700 focus:outline-none focus:ring-2 focus:ring-offset-2 focus:ring-primary-500 shadow-lg hover:shadow-xl transition-all duration-300"
              >
                <SparklesIcon className="h-6 w-6 mr-3" />
                Start Filling Forms
                <ArrowRightIcon className="h-5 w-5 ml-2" />
              </button>
            </div>
          </>
        )}
      </div>
    </div>
  );
};
