import React from 'react';
import { Link } from 'react-router-dom';

const Section: React.FC<{ title: string; children: React.ReactNode }> = ({ title, children }) => (
  <section className="mb-8">
    <h2 className="text-xl font-semibold text-gray-900 mb-3">{title}</h2>
    <div className="space-y-3 text-gray-700 leading-relaxed">{children}</div>
  </section>
);

/**
 * Public privacy policy. Required at a stable URL for Google OAuth verification
 * (gmail.readonly is a restricted scope). Content reflects the commitments in
 * PRD_COMPLETE.md (Data Privacy & Retention). MUST be reviewed by a California
 * attorney before public launch (PRD open decision OD6).
 */
export const PrivacyPolicy: React.FC = () => (
  <div className="min-h-screen bg-gray-50 py-10">
    <div className="max-w-[65ch] mx-auto bg-white rounded-lg shadow-sm p-8">
      <Link to="/" className="text-primary-600 hover:text-primary-800 text-sm">&larr; Back to home</Link>
      <h1 className="text-3xl font-bold text-gray-900 mt-4 mb-2">Privacy Policy</h1>
      <p className="text-sm text-gray-500 mb-8">Last updated: June 2026 · Draft pending attorney review</p>

      <Section title="What this service is">
        <p>
          Family Court Helper helps self-represented litigants prepare California
          family court documents. It provides document preparation and legal information
          only — not legal advice, and it is not a law firm.
        </p>
      </Section>

      <Section title="Information we collect">
        <p>We collect only what you provide to prepare your documents:</p>
        <ul className="list-disc pl-6 space-y-1">
          <li>Account information (email, name, phone)</li>
          <li>Case and party details you enter into your profile and intake answers</li>
          <li>Evidence you choose to add (typed text, transcriptions, uploaded files)</li>
          <li>If you connect Gmail, only emails you explicitly select for import</li>
        </ul>
      </Section>

      <Section title="How we use your information">
        <p>
          Your information is used solely to generate your court documents and operate
          your account. <strong>We never use your content — documents, intake answers,
          chat transcripts, or evidence — to train AI models.</strong> When AI assists
          with drafting, it processes your text under no-data-retention terms.
        </p>
      </Section>

      <Section title="Gmail access (if you connect it)">
        <p>
          Connecting Gmail is optional. We request read-only access and use it strictly
          to find emails relevant to your case so you can select them as evidence. We do
          not read, store, or transmit any email you do not explicitly select to import.
          Imported emails are saved as unconfirmed evidence and are never included in a
          filing until you review and confirm them. You can disconnect Gmail at any time.
          Our use of information received from Google APIs adheres to the
          {' '}<a className="text-primary-600 hover:text-primary-800" href="https://developers.google.com/terms/api-services-user-data-policy" target="_blank" rel="noopener noreferrer">Google API Services User Data Policy</a>,
          including the Limited Use requirements.
        </p>
      </Section>

      <Section title="How long we keep it &amp; your right to delete">
        <p>
          Active accounts retain data while the account is active. Inactive accounts are
          deleted after 24 months, with an email warning first. You can delete your
          account at any time; deletion removes your motions, drafts, chat history, and
          evidence (including uploaded files) within 30 days.
        </p>
      </Section>

      <Section title="Security">
        <p>
          Data is encrypted in transit (TLS) and at rest. Uploaded evidence is stored in
          non-public storage accessible only through your authenticated account.
        </p>
      </Section>

      <Section title="Legal demands from third parties">
        <p>
          The other party in your dispute may attempt to subpoena your data. We require a
          valid court order before responding, will notify you beforehand unless legally
          barred, and produce only the minimum required.
        </p>
      </Section>

      <Section title="We do not sell your data">
        <p>We never sell or share your personal information. (CCPA "Do Not Sell.")</p>
      </Section>

      <Section title="Contact">
        <p>Questions about this policy: sambrody34@gmail.com</p>
      </Section>

      <p className="text-xs text-gray-400 mt-8 border-t pt-4">
        This draft reflects our intended practices and must be reviewed and finalized by
        a licensed California attorney before public launch.
      </p>
    </div>
  </div>
);

export default PrivacyPolicy;
