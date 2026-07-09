import React, { useState, useEffect } from 'react';
import { useNavigate, Link } from 'react-router-dom';
import { motionAPI, profileAPI } from '../services/api';
import { useAuth } from '../contexts/AuthContext';
import {
  PlusIcon,
  DocumentTextIcon,
  ClockIcon,
  UserIcon,
  ChatBubbleBottomCenterTextIcon,
  SparklesIcon,
  ArrowRightIcon,
  ShieldExclamationIcon,
  ScaleIcon
} from '@heroicons/react/24/outline';
import { format } from 'date-fns';

interface Motion {
  id: string;
  motion_type: string;
  case_caption: string;
  case_number: string;
  filing_date: string;
  hearing_date: string;
  hearing_time: string;
  status: string;
  created_at: string;
  updated_at: string;
}

export const Dashboard: React.FC = () => {
  const navigate = useNavigate();
  const { user, logout } = useAuth();
  const [motions, setMotions] = useState<Motion[]>([]);
  const [profile, setProfile] = useState<any>(null);
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    loadDashboardData();
  }, []);

  const loadDashboardData = async () => {
    try {
      // Load profile
      try {
        const profileResponse = await profileAPI.get();
        setProfile(profileResponse);
      } catch (profileError) {
        console.log('No profile found, user needs to set up profile');
      }

      // Load motions
      const motionsResponse = await motionAPI.list();
      setMotions(Array.isArray(motionsResponse) ? motionsResponse : []);
    } catch (error) {
      console.error('Failed to load dashboard data:', error);
    } finally {
      setLoading(false);
    }
  };

  const startNewCase = () => {
    if (!profile) {
      navigate('/profile/setup');
      return;
    }
    navigate('/case/intake');
  };

  const handleSignOut = async () => {
    try {
      await logout();
      navigate('/login');
    } catch (error) {
      console.error('Failed to sign out:', error);
    }
  };


  const getStatusBadge = (status: string) => {
    const statusColors: { [key: string]: string } = {
      'draft': 'bg-gray-100 text-gray-800',
      'in_progress': 'bg-yellow-100 text-yellow-800',
      'ready_for_review': 'bg-blue-100 text-blue-800',
      'complete': 'bg-green-100 text-green-800',
      'filed': 'bg-purple-100 text-purple-800',
    };

    return (
      <span className={`inline-flex items-center px-2.5 py-0.5 rounded-full text-xs font-medium ${statusColors[status] || 'bg-gray-100 text-gray-800'}`}>
        {status.replace('_', ' ')}
      </span>
    );
  };

  return (
    <div className="min-h-screen bg-gray-50">
      {/* Header */}
      <header className="bg-white shadow">
        <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8">
          <div className="flex justify-between items-center py-6">
            <div>
              <h1 className="text-3xl font-bold text-gray-900">
                California Motion Writer
              </h1>
              <p className="mt-1 text-sm text-gray-600">
                Welcome back, {user?.email}
              </p>
            </div>
            <div className="flex space-x-3">
              <button
                onClick={() => navigate('/profile/setup')}
                className="inline-flex items-center px-3 py-2 border border-gray-300 shadow-sm text-sm leading-4 font-medium rounded-md text-gray-700 bg-white hover:bg-gray-50 focus:outline-none focus:ring-2 focus:ring-offset-2 focus:ring-indigo-500"
              >
                <UserIcon className="h-4 w-4 mr-2" />
                Profile
              </button>
              <button
                onClick={handleSignOut}
                className="inline-flex items-center px-3 py-2 border border-transparent text-sm leading-4 font-medium rounded-md text-white bg-indigo-600 hover:bg-indigo-700 focus:outline-none focus:ring-2 focus:ring-offset-2 focus:ring-indigo-500"
              >
                Sign Out
              </button>
            </div>
          </div>
        </div>
      </header>

      <main className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 py-8">

        {/* Profile Setup Notice */}
        {!profile && (
          <div className="mb-8 bg-yellow-50 border-l-4 border-yellow-400 p-4">
            <div className="flex">
              <div className="ml-3">
                <p className="text-sm text-yellow-700">
                  <strong>Complete your profile first:</strong> Set up your profile to auto-fill form information and save time.
                  <button
                    onClick={() => navigate('/profile/setup')}
                    className="ml-2 font-medium underline hover:text-yellow-800"
                  >
                    Set up profile →
                  </button>
                </p>
              </div>
            </div>
          </div>
        )}

        {/* Main Hero Section */}
        <div className="text-center mb-12">
          <div className="flex justify-center mb-6">
            <div className="bg-indigo-100 p-4 rounded-full">
              <SparklesIcon className="h-12 w-12 text-indigo-600" />
            </div>
          </div>
          <h2 className="text-3xl font-bold text-gray-900 mb-4">
            Get Legal Help for Your Family Law Case
          </h2>
          <p className="text-xl text-gray-600 max-w-3xl mx-auto mb-8">
            Tell us about your family law situation and we'll create a personalized legal strategy,
            determine which California court forms you need, and help you fill them out correctly.
          </p>

          <button
            onClick={startNewCase}
            className="inline-flex items-center px-8 py-4 border border-transparent text-lg font-medium rounded-md text-white bg-indigo-600 hover:bg-indigo-700 focus:outline-none focus:ring-2 focus:ring-offset-2 focus:ring-indigo-500 shadow-lg hover:shadow-xl transition-all duration-300"
          >
            <ChatBubbleBottomCenterTextIcon className="h-6 w-6 mr-3" />
            Start Your Case
            <ArrowRightIcon className="h-5 w-5 ml-2" />
          </button>

          <div className="mt-6">
            <Link
              to="/emergency"
              aria-label="Need emergency protection?"
              className="inline-flex items-center text-sm text-red-600 hover:text-red-800 font-medium underline"
            >
              <ShieldExclamationIcon className="h-4 w-4 mr-1" />
              Need emergency protection?
            </Link>
          </div>
        </div>

        {/* Enforce an existing order */}
        <div className="mb-8">
          <div className="bg-white border border-gray-200 rounded-lg p-6 shadow-sm flex flex-col sm:flex-row items-start sm:items-center justify-between gap-4">
            <div className="flex items-start space-x-3">
              <ScaleIcon className="h-6 w-6 text-indigo-500 flex-shrink-0 mt-0.5" />
              <div>
                <h3 className="text-base font-semibold text-gray-900">Enforce an existing order</h3>
                <p className="text-sm text-gray-600 mt-1">
                  If the other party is not following a court order, you may have options to enforce it.
                </p>
              </div>
            </div>
            <button
              onClick={() => navigate('/violation/intake')}
              aria-label="Enforce an existing order"
              className="inline-flex items-center px-4 py-2 border border-indigo-300 shadow-sm text-sm font-medium rounded-md text-indigo-700 bg-white hover:bg-indigo-50 focus:outline-none focus:ring-2 focus:ring-offset-2 focus:ring-indigo-500 flex-shrink-0"
            >
              Get started
              <ArrowRightIcon className="h-4 w-4 ml-2" />
            </button>
          </div>
        </div>

        {/* How It Works */}
        <div className="mb-12">
          <h3 className="text-xl font-semibold text-gray-900 mb-6 text-center">How It Works</h3>
          <div className="grid grid-cols-1 md:grid-cols-3 gap-6">
            <div className="text-center">
              <div className="bg-blue-100 p-3 rounded-full w-16 h-16 mx-auto mb-4 flex items-center justify-center">
                <span className="text-2xl font-bold text-blue-600">1</span>
              </div>
              <h4 className="text-lg font-medium text-gray-900 mb-2">Explain Your Case</h4>
              <p className="text-gray-600">
                Tell us about your family law situation, what you want to achieve, and any existing orders or issues.
              </p>
            </div>

            <div className="text-center">
              <div className="bg-green-100 p-3 rounded-full w-16 h-16 mx-auto mb-4 flex items-center justify-center">
                <span className="text-2xl font-bold text-green-600">2</span>
              </div>
              <h4 className="text-lg font-medium text-gray-900 mb-2">Get Your Strategy</h4>
              <p className="text-gray-600">
                Our AI creates a personalized legal gameplan and determines exactly which California forms you need.
              </p>
            </div>

            <div className="text-center">
              <div className="bg-purple-100 p-3 rounded-full w-16 h-16 mx-auto mb-4 flex items-center justify-center">
                <span className="text-2xl font-bold text-purple-600">3</span>
              </div>
              <h4 className="text-lg font-medium text-gray-900 mb-2">File Your Forms</h4>
              <p className="text-gray-600">
                We help you fill out the forms correctly and generate ready-to-file PDFs for the court.
              </p>
            </div>
          </div>
        </div>

        {/* Recent Motions */}
        <div>
          <h2 className="text-lg font-medium text-gray-900 mb-4">Your Motions</h2>
          
          {loading ? (
            <div className="flex justify-center py-12">
              <div className="animate-spin rounded-full h-12 w-12 border-b-2 border-indigo-600"></div>
            </div>
          ) : motions.length > 0 ? (
            <div className="bg-white shadow overflow-hidden sm:rounded-md">
              <ul className="divide-y divide-gray-200">
                {motions.map((motion) => (
                  <li key={motion.id}>
                    <a
                      href="#"
                      onClick={(e) => {
                        e.preventDefault();
                        navigate(`/motion/${motion.id}`);
                      }}
                      className="block hover:bg-gray-50 px-4 py-4 sm:px-6"
                    >
                      <div className="flex items-center justify-between">
                        <div className="flex items-center">
                          <div className="flex-shrink-0">
                            <DocumentTextIcon className="h-8 w-8 text-gray-400" />
                          </div>
                          <div className="ml-4">
                            <div className="text-sm font-medium text-gray-900">
                              {motion.case_caption || `${motion.motion_type} Motion`}
                            </div>
                            <div className="text-sm text-gray-500">
                              Case #: {motion.case_number || 'Draft'}
                            </div>
                          </div>
                        </div>
                        <div className="flex items-center space-x-4">
                          {motion.hearing_date && (
                            <div className="flex items-center text-sm text-gray-500">
                              <ClockIcon className="flex-shrink-0 mr-1.5 h-4 w-4 text-gray-400" />
                              Hearing: {format(new Date(motion.hearing_date), 'MMM d, yyyy')}
                            </div>
                          )}
                          {getStatusBadge(motion.status)}
                        </div>
                      </div>
                      <div className="mt-2 text-sm text-gray-500">
                        Last updated: {format(new Date(motion.updated_at), 'MMM d, yyyy h:mm a')}
                      </div>
                    </a>
                  </li>
                ))}
              </ul>
            </div>
          ) : (
            <div className="text-center py-12 bg-white rounded-lg border-2 border-dashed border-gray-300">
              <DocumentTextIcon className="mx-auto h-12 w-12 text-gray-400" />
              <h3 className="mt-2 text-sm font-medium text-gray-900">No motions</h3>
              <p className="mt-1 text-sm text-gray-500">Get started by creating a new motion.</p>
              <div className="mt-6">
                <button
                  onClick={startNewCase}
                  className="inline-flex items-center px-4 py-2 border border-transparent shadow-sm text-sm font-medium rounded-md text-white bg-indigo-600 hover:bg-indigo-700 focus:outline-none focus:ring-2 focus:ring-offset-2 focus:ring-indigo-500"
                >
                  <ChatBubbleBottomCenterTextIcon className="-ml-1 mr-2 h-5 w-5" aria-hidden="true" />
                  Start Your Case
                </button>
              </div>
            </div>
          )}
        </div>
      </main>
    </div>
  );
};