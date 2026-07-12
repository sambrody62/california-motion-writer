import React from 'react';
import { Link } from 'react-router-dom';

export const LegalFooter: React.FC = () => (
  <footer className="bg-white border-t border-gray-200 py-6 mt-auto">
    <div className="max-w-5xl mx-auto px-4 sm:px-6 lg:px-8 text-center">
      <p className="text-xs text-gray-500 mb-2">
        Family Court Helper is a document-preparation tool. It does not provide legal
        advice, and using it does not create an attorney–client relationship.
      </p>
      <div className="space-x-4 text-xs">
        <Link to="/terms" className="text-primary-600 hover:text-primary-500">
          Terms of Service
        </Link>
        <Link to="/privacy" className="text-primary-600 hover:text-primary-500">
          Privacy Policy
        </Link>
      </div>
    </div>
  </footer>
);
