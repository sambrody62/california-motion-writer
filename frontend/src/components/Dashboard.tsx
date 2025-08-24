import React, { useState, useEffect } from 'react';
import { useNavigate } from 'react-router-dom';
import { motionAPI } from '../services/api';
import { useFirebaseAuth } from '../contexts/FirebaseAuthContext';
import { PlusIcon, DocumentTextIcon, ClockIcon } from '@heroicons/react/20/solid';
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
  const { user, logout } = useFirebaseAuth();
  const [motions, setMotions] = useState<Motion[]>([]);
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    loadMotions();
  }, []);

  const loadMotions = async () => {
    try {
      const response = await motionAPI.listMotions();
      setMotions(response.data.motions || []);
    } catch (error) {
      console.error('Failed to load motions:', error);
    } finally {
      setLoading(false);
    }
  };

  const startNewMotion = (motionType: string) => {
    navigate(`/motion/new/${motionType}`);
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
                className="inline-flex items-center px-4 py-2 border border-gray-300 rounded-md shadow-sm text-sm font-medium text-gray-700 bg-white hover:bg-gray-50"
              >
                Profile
              </button>
              <button
                onClick={logout}
                className="inline-flex items-center px-4 py-2 border border-gray-300 rounded-md shadow-sm text-sm font-medium text-gray-700 bg-white hover:bg-gray-50"
              >
                Sign Out
              </button>
            </div>
          </div>
        </div>
      </header>

      <main className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 py-8">
        {/* New Motion Section */}
        <div className="mb-8">
          <h2 className="text-lg font-medium text-gray-900 mb-4">Start a New Motion</h2>
          <div className="grid grid-cols-1 gap-4 sm:grid-cols-2 lg:grid-cols-3">
            <button
              onClick={() => startNewMotion('RFO')}
              className="relative rounded-lg border border-gray-300 bg-white px-6 py-4 shadow-sm flex items-center space-x-3 hover:border-gray-400 focus-within:ring-2 focus-within:ring-offset-2 focus-within:ring-indigo-500"
            >
              <div className="flex-shrink-0">
                <DocumentTextIcon className="h-10 w-10 text-indigo-600" />
              </div>
              <div className="flex-1 min-w-0">
                <span className="absolute inset-0" aria-hidden="true" />
                <p className="text-sm font-medium text-gray-900">Request for Order (FL-300)</p>
                <p className="text-sm text-gray-500">File a new request with the court</p>
              </div>
            </button>

            <button
              onClick={() => startNewMotion('Response')}
              className="relative rounded-lg border border-gray-300 bg-white px-6 py-4 shadow-sm flex items-center space-x-3 hover:border-gray-400 focus-within:ring-2 focus-within:ring-offset-2 focus-within:ring-indigo-500"
            >
              <div className="flex-shrink-0">
                <DocumentTextIcon className="h-10 w-10 text-green-600" />
              </div>
              <div className="flex-1 min-w-0">
                <span className="absolute inset-0" aria-hidden="true" />
                <p className="text-sm font-medium text-gray-900">Response to RFO (FL-320)</p>
                <p className="text-sm text-gray-500">Respond to a filed motion</p>
              </div>
            </button>

            <button
              disabled
              className="relative rounded-lg border border-gray-300 bg-gray-50 px-6 py-4 shadow-sm flex items-center space-x-3 opacity-50 cursor-not-allowed"
            >
              <div className="flex-shrink-0">
                <DocumentTextIcon className="h-10 w-10 text-gray-400" />
              </div>
              <div className="flex-1 min-w-0">
                <p className="text-sm font-medium text-gray-900">More Forms</p>
                <p className="text-sm text-gray-500">Coming soon</p>
              </div>
            </button>
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
                  onClick={() => startNewMotion('RFO')}
                  className="inline-flex items-center px-4 py-2 border border-transparent shadow-sm text-sm font-medium rounded-md text-white bg-indigo-600 hover:bg-indigo-700 focus:outline-none focus:ring-2 focus:ring-offset-2 focus:ring-indigo-500"
                >
                  <PlusIcon className="-ml-1 mr-2 h-5 w-5" aria-hidden="true" />
                  New Request for Order
                </button>
              </div>
            </div>
          )}
        </div>
      </main>
    </div>
  );
};