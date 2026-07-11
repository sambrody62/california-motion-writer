import React from 'react';
import { Link } from 'react-router-dom';

const Section: React.FC<{ title: string; children: React.ReactNode }> = ({ title, children }) => (
  <section className="mb-8">
    <h2 className="text-xl font-semibold text-gray-900 mb-3">{title}</h2>
    <div className="space-y-3 text-gray-700 leading-relaxed">{children}</div>
  </section>
);

/**
 * Public terms of service. The "not legal advice" disclaimer is the core
 * unauthorized-practice-of-law (UPL) protection (PRD compliance C1/C2).
 * MUST be reviewed by a California attorney before public launch (PRD OD6).
 */
export const Terms: React.FC = () => (
  <div className="min-h-screen bg-gray-50 py-10">
    <div className="max-w-[65ch] mx-auto bg-white rounded-lg shadow-sm p-8">
      <Link to="/" className="text-primary-600 hover:text-primary-800 text-sm">&larr; Back to home</Link>
      <h1 className="text-3xl font-bold text-gray-900 mt-4 mb-2">Terms of Service</h1>
      <p className="text-sm text-gray-500 mb-8">Last updated: June 2026 · Draft pending attorney review</p>

      <div className="bg-amber-50 border border-amber-200 rounded-md p-4 mb-8">
        <p className="text-amber-900 font-medium">
          This service provides document preparation and legal information, not legal
          advice. It is not a substitute for an attorney, and using it does not create an
          attorney–client relationship.
        </p>
      </div>

      <Section title="What we do">
        <p>
          Family Court Helper helps you prepare California family court forms by
          guiding you through questions and formatting your own words into court-ready
          documents. We do not tell you what legal strategy to choose, predict how a
          court will rule, or recommend one option over another.
        </p>
      </Section>

      <Section title="What you are responsible for">
        <ul className="list-disc pl-6 space-y-1">
          <li>The accuracy of the information you provide</li>
          <li>Reviewing every generated document before you file it</li>
          <li>Meeting your court's deadlines, fees, and local filing rules</li>
          <li>Deciding whether to consult a licensed attorney about your case</li>
        </ul>
      </Section>

      <Section title="No guarantee of outcome">
        <p>
          We do not guarantee that any document will be accepted by a court or that any
          filing will achieve a particular result. Court rules, fees, and forms change;
          always verify current requirements with your court.
        </p>
      </Section>

      <Section title="Get help">
        <p>
          For legal advice, contact your county court's self-help center or the
          {' '}<a className="text-primary-600 hover:text-primary-800" href="https://selfhelp.courts.ca.gov/" target="_blank" rel="noopener noreferrer">California Courts Self-Help Guide</a>,
          or seek a licensed attorney through the California State Bar lawyer referral
          service.
        </p>
      </Section>

      <p className="text-xs text-gray-400 mt-8 border-t pt-4">
        This draft must be reviewed and finalized by a licensed California attorney before
        public launch.
      </p>
    </div>
  </div>
);

export default Terms;
