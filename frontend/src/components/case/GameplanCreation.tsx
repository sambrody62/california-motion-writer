import React, { useState, useEffect } from 'react';
import { useLocation, useNavigate } from 'react-router-dom';
import { useForm } from 'react-hook-form';
import {
  SparklesIcon,
  CheckCircleIcon,
  DocumentTextIcon,
  ArrowRightIcon,
  PencilIcon,
  ExclamationTriangleIcon
} from '@heroicons/react/24/outline';
import { FORM_METADATA, FormType } from '../../types/forms';
import { chat } from '../../services/api';

interface LocationState {
  caseDescription: string;
  existingGameplan?: string;
}

interface GameplanData {
  analysis: string;
  legalStrategy: string;
  recommendedForms: FormType[];
  timeline: string;
  keyConsiderations: string[];
  nextSteps: string[];
}

export const GameplanCreation: React.FC = () => {
  const location = useLocation();
  const navigate = useNavigate();
  const [loading, setLoading] = useState(true);
  const [gameplan, setGameplan] = useState<GameplanData | null>(null);
  const [error, setError] = useState<string | null>(null);
  const [sessionId, setSessionId] = useState<string | null>(null);

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

      // Extract response text from the response structure
      let responseText = '';
      if (typeof messageResponse === 'string') {
        responseText = messageResponse;
      } else if (messageResponse.response) {
        responseText = typeof messageResponse.response === 'string'
          ? messageResponse.response
          : messageResponse.response.response || JSON.stringify(messageResponse.response);
      } else if (messageResponse.data) {
        responseText = typeof messageResponse.data === 'string'
          ? messageResponse.data
          : messageResponse.data.response || JSON.stringify(messageResponse.data);
      } else {
        responseText = JSON.stringify(messageResponse);
      }

      // Parse the LLM response into structured data
      const parsedGameplan = parseLLMResponse(responseText);
      setGameplan(parsedGameplan);

    } catch (error) {
      console.error('Error creating gameplan:', error);
      setError('Failed to create gameplan. Please try again.');
    } finally {
      setLoading(false);
    }
  };

  const parseLLMResponse = (response: string): GameplanData => {
    // Parse the LLM response to extract structured information
    // This is a simplified parser - in production you'd want more robust parsing

    const lines = response.split('\n').filter(line => line.trim());

    // Extract recommended forms by looking for form codes
    const formCodes = ['FL-300', 'FL-320', 'D-046', 'FL-305', 'FL-150', 'FL-335', 'FL-410', 'FL-411', 'MC-030'];
    const recommendedForms: FormType[] = [];

    formCodes.forEach(code => {
      if (response.toUpperCase().includes(code)) {
        recommendedForms.push(code as FormType);
      }
    });

    // If no forms detected, default to FL-300 (Request for Order)
    if (recommendedForms.length === 0) {
      recommendedForms.push('FL-300');
    }

    return {
      analysis: extractSection(response, ['analysis', 'situation', 'case analysis']) || 'Legal situation analysis',
      legalStrategy: extractSection(response, ['strategy', 'legal strategy', 'approach']) || 'Legal strategy recommendation',
      recommendedForms,
      timeline: extractSection(response, ['timeline', 'timeframe', 'schedule']) || 'Recommended filing timeline',
      keyConsiderations: extractListItems(response, ['considerations', 'challenges', 'important']),
      nextSteps: extractListItems(response, ['next steps', 'actions', 'steps'])
    };
  };

  const extractSection = (text: string, keywords: string[]): string | null => {
    const lines = text.split('\n');
    for (let i = 0; i < lines.length; i++) {
      const line = lines[i].toLowerCase();
      if (keywords.some(keyword => line.includes(keyword))) {
        // Look for content in next few lines
        for (let j = i + 1; j < Math.min(i + 5, lines.length); j++) {
          const nextLine = lines[j].trim();
          if (nextLine && !nextLine.match(/^\d+\./) && nextLine.length > 20) {
            return nextLine;
          }
        }
      }
    }
    return null;
  };

  const extractListItems = (text: string, keywords: string[]): string[] => {
    const items: string[] = [];
    const lines = text.split('\n');

    for (let i = 0; i < lines.length; i++) {
      const line = lines[i].toLowerCase();
      if (keywords.some(keyword => line.includes(keyword))) {
        // Look for list items in next lines
        for (let j = i + 1; j < Math.min(i + 10, lines.length); j++) {
          const nextLine = lines[j].trim();
          if (nextLine.match(/^[-*•]\s/) || nextLine.match(/^\d+\.\s/)) {
            items.push(nextLine.replace(/^[-*•]\s/, '').replace(/^\d+\.\s/, ''));
          }
        }
        break;
      }
    }

    return items.length > 0 ? items : ['Consult with legal professional', 'Gather required documentation', 'File forms within deadline'];
  };

  const refineGameplan = async (data: { customization: string }) => {
    if (!sessionId || !data.customization.trim()) return;

    try {
      setLoading(true);
      const refinePrompt = `Based on our previous discussion, please refine the gameplan with this additional input: ${data.customization}

Please provide an updated structured response with any necessary changes to the strategy, forms, or timeline.`;

      const messageResponse = await chat.sendMessage(sessionId, refinePrompt);

      // Extract response text from the response structure
      let responseText = '';
      if (typeof messageResponse === 'string') {
        responseText = messageResponse;
      } else if (messageResponse.response) {
        responseText = typeof messageResponse.response === 'string'
          ? messageResponse.response
          : messageResponse.response.response || JSON.stringify(messageResponse.response);
      } else if (messageResponse.data) {
        responseText = typeof messageResponse.data === 'string'
          ? messageResponse.data
          : messageResponse.data.response || JSON.stringify(messageResponse.data);
      } else {
        responseText = JSON.stringify(messageResponse);
      }

      const refinedGameplan = parseLLMResponse(responseText);
      setGameplan(refinedGameplan);
      setValue('customization', '');
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
          <div className="animate-spin rounded-full h-12 w-12 border-b-2 border-indigo-600 mx-auto mb-4"></div>
          <h3 className="text-lg font-medium text-gray-900 mb-2">Creating Your Legal Strategy</h3>
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

        {/* Header */}
        <div className="text-center mb-8">
          <div className="flex justify-center mb-4">
            <div className="bg-green-100 p-3 rounded-full">
              <CheckCircleIcon className="h-8 w-8 text-green-600" />
            </div>
          </div>
          <h1 className="text-3xl font-bold text-gray-900 mb-3">
            Your Legal Strategy
          </h1>
          <p className="text-lg text-gray-600">
            Here's your personalized gameplan based on your case details
          </p>
        </div>

        {gameplan && (
          <>
            {/* Case Analysis */}
            <div className="bg-white shadow rounded-lg p-6 mb-6">
              <h2 className="text-xl font-semibold text-gray-900 mb-4">Case Analysis</h2>
              <p className="text-gray-700">{gameplan.analysis}</p>
            </div>

            {/* Legal Strategy */}
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

            {/* Refinement Section */}
            <div className="bg-white shadow rounded-lg p-6 mb-6">
              <h2 className="text-xl font-semibold text-gray-900 mb-4">
                Want to refine this strategy?
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
                    className="block w-full border-gray-300 rounded-md shadow-sm focus:ring-indigo-500 focus:border-indigo-500 sm:text-sm"
                    placeholder="e.g., I also need help with emergency custody, or I have a restraining order that affects this case..."
                  />
                </div>
                <button
                  type="submit"
                  disabled={!customization?.trim() || loading}
                  className="inline-flex items-center px-4 py-2 border border-gray-300 shadow-sm text-sm font-medium rounded-md text-gray-700 bg-white hover:bg-gray-50 focus:outline-none focus:ring-2 focus:ring-offset-2 focus:ring-indigo-500 disabled:opacity-50 disabled:cursor-not-allowed"
                >
                  <PencilIcon className="h-4 w-4 mr-2" />
                  Refine Strategy
                </button>
              </form>
            </div>

            {/* Proceed Button */}
            <div className="text-center">
              <button
                onClick={proceedToForms}
                className="inline-flex items-center px-8 py-4 border border-transparent text-lg font-medium rounded-md text-white bg-indigo-600 hover:bg-indigo-700 focus:outline-none focus:ring-2 focus:ring-offset-2 focus:ring-indigo-500 shadow-lg hover:shadow-xl transition-all duration-300"
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