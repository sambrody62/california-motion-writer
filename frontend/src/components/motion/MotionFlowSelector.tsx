import React from 'react';
import { useNavigate, useParams } from 'react-router-dom';
import { ChatBubbleBottomCenterTextIcon, DocumentTextIcon, ArrowLeftIcon } from '@heroicons/react/24/outline';

export const MotionFlowSelector: React.FC = () => {
  const navigate = useNavigate();
  const { motionType } = useParams<{ motionType: string }>();

  const getMotionTitle = () => {
    switch (motionType) {
      case 'RFO':
        return 'Request for Order';
      case 'response':
        return 'Response to Request for Order';
      case 'ex-parte':
        return 'Ex Parte Motion';
      default:
        return 'Motion';
    }
  };

  const handleChatFlow = () => {
    // Navigate to chat interface with motion context
    navigate(`/chat/${motionType}`);
  };

  const handleFormsFlow = () => {
    // Navigate to traditional guided forms
    navigate(`/motion/guided/${motionType}`);
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
        <div className="text-center mb-12">
          <h1 className="text-3xl font-bold text-gray-900 mb-3">
            {getMotionTitle()}
          </h1>
          <p className="text-lg text-gray-600">
            How would you like to create your motion?
          </p>
        </div>

        {/* Option Cards */}
        <div className="grid md:grid-cols-2 gap-8">
          {/* Chat Option */}
          <button
            onClick={handleChatFlow}
            className="group relative bg-white rounded-2xl shadow-lg hover:shadow-xl transition-all duration-300 p-8 text-left border-2 border-transparent hover:border-indigo-500"
          >
            {/* Recommended badge */}
            <div className="absolute -top-3 left-6 bg-green-500 text-white text-xs font-semibold px-3 py-1 rounded-full">
              Recommended for first-timers
            </div>

            <div className="flex flex-col items-center text-center">
              <div className="bg-indigo-100 p-4 rounded-full mb-4 group-hover:bg-indigo-200 transition-colors">
                <ChatBubbleBottomCenterTextIcon className="h-12 w-12 text-indigo-600" />
              </div>

              <h2 className="text-xl font-semibold text-gray-900 mb-3">
                💬 Chat with Assistant
              </h2>

              <p className="text-gray-600 mb-4">
                Tell me about your situation in your own words. I'll help you understand what you need and create a plan together.
              </p>

              <ul className="text-left text-sm text-gray-500 space-y-2 w-full">
                <li className="flex items-start">
                  <span className="text-green-500 mr-2">✓</span>
                  <span>Conversational and easy</span>
                </li>
                <li className="flex items-start">
                  <span className="text-green-500 mr-2">✓</span>
                  <span>Get legal guidance as you go</span>
                </li>
                <li className="flex items-start">
                  <span className="text-green-500 mr-2">✓</span>
                  <span>AI helps organize your thoughts</span>
                </li>
                <li className="flex items-start">
                  <span className="text-green-500 mr-2">✓</span>
                  <span>Perfect if you're not sure what you need</span>
                </li>
              </ul>

              <div className="mt-6 text-indigo-600 font-medium group-hover:text-indigo-700">
                Start conversation →
              </div>
            </div>
          </button>

          {/* Forms Option */}
          <button
            onClick={handleFormsFlow}
            className="group relative bg-white rounded-2xl shadow-lg hover:shadow-xl transition-all duration-300 p-8 text-left border-2 border-transparent hover:border-blue-500"
          >
            {/* Faster badge */}
            <div className="absolute -top-3 left-6 bg-blue-500 text-white text-xs font-semibold px-3 py-1 rounded-full">
              Faster if you know what you need
            </div>

            <div className="flex flex-col items-center text-center">
              <div className="bg-blue-100 p-4 rounded-full mb-4 group-hover:bg-blue-200 transition-colors">
                <DocumentTextIcon className="h-12 w-12 text-blue-600" />
              </div>

              <h2 className="text-xl font-semibold text-gray-900 mb-3">
                📝 Guided Forms
              </h2>

              <p className="text-gray-600 mb-4">
                Fill out step-by-step forms with all the required information. Direct and efficient if you know what you're asking for.
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
                  <span>Faster for experienced users</span>
                </li>
                <li className="flex items-start">
                  <span className="text-green-500 mr-2">✓</span>
                  <span>Skip straight to the forms</span>
                </li>
              </ul>

              <div className="mt-6 text-blue-600 font-medium group-hover:text-blue-700">
                Go to forms →
              </div>
            </div>
          </button>
        </div>

        {/* Help text */}
        <div className="mt-12 text-center">
          <p className="text-sm text-gray-500">
            Not sure which to choose? The chat assistant is recommended if this is your first time filing a motion.
          </p>
          <p className="text-sm text-gray-500 mt-2">
            You can always switch between methods or get help at any time.
          </p>
        </div>
      </div>
    </div>
  );
};