import React from 'react';
import { Link } from 'react-router-dom';
import { PhoneIcon, ExclamationTriangleIcon, DocumentTextIcon, HomeIcon } from '@heroicons/react/24/outline';

const handleQuickExit = () => {
  window.location.replace('https://www.google.com');
};

const ResourceCard: React.FC<{ title: string; children: React.ReactNode }> = ({ title, children }) => (
  <div className="bg-white border border-gray-200 rounded-lg p-6 shadow-sm">
    <h2 className="text-lg font-semibold text-gray-900 mb-4">{title}</h2>
    {children}
  </div>
);

export const EmergencyHelp: React.FC = () => {
  return (
    <div className="min-h-screen bg-gray-50">
      {/* Quick exit button - fixed top-right */}
      <button
        onClick={handleQuickExit}
        aria-label="Quick exit"
        className="fixed top-4 right-4 z-50 bg-red-600 text-white px-4 py-2 rounded-md font-medium shadow-lg hover:bg-red-700 focus:outline-none focus:ring-2 focus:ring-red-500 focus:ring-offset-2"
      >
        Quick Exit
      </button>

      {/* 911 Banner */}
      <div
        role="alert"
        className="bg-red-600 text-white text-center py-4 px-4 font-semibold text-lg"
      >
        If you are in danger right now, call 911.
      </div>

      <main className="max-w-3xl mx-auto px-4 py-8 space-y-6">
        <div className="text-center mb-4">
          <h1 className="text-3xl font-bold text-gray-900 mb-2">Emergency Legal Help</h1>
          <p className="text-gray-600">
            California courts offer same-day emergency orders in certain situations. See your options below.
          </p>
        </div>

        {/* Option 1: DVRO */}
        <ResourceCard title="Domestic Violence Restraining Order (DVRO)">
          <div className="flex items-start space-x-3 mb-4">
            <ExclamationTriangleIcon className="h-5 w-5 text-red-500 flex-shrink-0 mt-0.5" />
            <p className="text-gray-700">
              A DVRO can order someone to stay away from you, your home, your workplace, and your children.
              Filing is <strong>free</strong>. Courts can issue a temporary order the same day you file, before a hearing.
            </p>
          </div>
          <p className="text-sm text-gray-600 mb-4">
            <strong>Forms used:</strong> DV-100 series. File before your county&apos;s ex parte cutoff (typically morning).
          </p>
          <div className="space-y-2">
            <a
              href="https://selfhelp.courts.ca.gov/DV-restraining-order"
              target="_blank"
              rel="noopener noreferrer"
              className="inline-flex items-center text-primary-600 hover:text-primary-800 underline text-sm font-medium"
            >
              <DocumentTextIcon className="h-4 w-4 mr-1" />
              California Courts Self-Help: Domestic Violence Restraining Order
            </a>
            <br />
            <a
              href="https://www.courts.ca.gov/1032.htm"
              target="_blank"
              rel="noopener noreferrer"
              className="inline-flex items-center text-primary-600 hover:text-primary-800 underline text-sm font-medium"
            >
              <DocumentTextIcon className="h-4 w-4 mr-1" />
              DV-100 and related court forms
            </a>
          </div>
          <p className="text-xs text-gray-500 mt-3">
            Note: This tool does not generate DVRO forms. Use the links above and your county self-help center for assistance.
          </p>
        </ResourceCard>

        {/* Option 2: Emergency custody orders */}
        <ResourceCard title="Emergency (Ex Parte) Custody Order">
          <div className="flex items-start space-x-3 mb-4">
            <DocumentTextIcon className="h-5 w-5 text-primary-500 flex-shrink-0 mt-0.5" />
            <p className="text-gray-700">
              If your child is in immediate danger, you can ask a judge for an emergency custody order without
              advance notice to the other parent. You must show an immediate risk of harm.
            </p>
          </div>
          <p className="text-sm text-gray-600 mb-4">
            <strong>Forms used:</strong> FL-300 (Request for Order) + FL-303 (Declaration Re Notice). File before your
            county&apos;s ex parte cutoff.
          </p>
          <a
            href="https://selfhelp.courts.ca.gov/child-custody"
            target="_blank"
            rel="noopener noreferrer"
            className="inline-flex items-center text-primary-600 hover:text-primary-800 underline text-sm font-medium"
          >
            <DocumentTextIcon className="h-4 w-4 mr-1" />
            California Courts Self-Help: Child Custody
          </a>
        </ResourceCard>

        {/* Resources */}
        <ResourceCard title="Support Resources">
          <ul className="space-y-4">
            <li className="flex items-start space-x-3">
              <PhoneIcon className="h-5 w-5 text-green-600 flex-shrink-0 mt-0.5" />
              <div>
                <p className="font-medium text-gray-900">National Domestic Violence Hotline</p>
                <p className="text-gray-700">
                  Call <a href="tel:18007997233" className="font-semibold text-primary-600 hover:underline">1-800-799-7233</a>{' '}
                  (24/7, free, confidential) or text <strong>START</strong> to <strong>88788</strong>
                </p>
              </div>
            </li>
            <li className="flex items-start space-x-3">
              <HomeIcon className="h-5 w-5 text-primary-600 flex-shrink-0 mt-0.5" />
              <div>
                <p className="font-medium text-gray-900">Find a local shelter</p>
                <a
                  href="https://www.domesticshelters.org/"
                  target="_blank"
                  rel="noopener noreferrer"
                  className="text-primary-600 hover:underline text-sm"
                >
                  domesticshelters.org — search by zip code
                </a>
              </div>
            </li>
          </ul>
        </ResourceCard>

        <div className="text-center pt-2">
          <Link to="/dashboard" className="text-sm text-gray-500 hover:text-gray-700 underline">
            Return to dashboard
          </Link>
        </div>
      </main>
    </div>
  );
};
