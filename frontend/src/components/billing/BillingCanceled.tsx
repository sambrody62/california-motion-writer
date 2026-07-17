import React from 'react';
import { Link } from 'react-router-dom';

export const BillingCanceled: React.FC = () => (
  <div className="min-h-screen bg-gray-50 flex items-center justify-center p-4">
    <div className="bg-white rounded-lg shadow max-w-md w-full p-8 text-center">
      <h2 className="text-xl font-semibold text-gray-900">Checkout canceled</h2>
      <p className="mt-2 text-sm text-gray-600">
        Nothing was charged. Your answers and drafts are still saved — you can subscribe
        whenever you're ready.
      </p>
      <Link
        to="/dashboard"
        className="mt-4 inline-block w-full px-4 py-2 rounded-md text-white bg-primary-600 hover:bg-primary-700 font-medium"
      >
        Back to dashboard
      </Link>
    </div>
  </div>
);
