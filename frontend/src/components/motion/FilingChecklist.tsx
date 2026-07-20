/**
 * FilingChecklist Component
 * Displays county-specific filing requirements and checklist
 */
import React, { useState } from 'react';
import { getCountyFilingInfo, isKnownCounty } from '../../data/countyFilingInfo';
import { CheckIcon } from '@heroicons/react/20/solid';

interface FilingChecklistProps {
  county: string;
  motionType: string;
}

export const FilingChecklist: React.FC<FilingChecklistProps> = ({ county, motionType }) => {
  const countyInfo = getCountyFilingInfo(county);
  const isKnown = isKnownCounty(county);
  const [checkedItems, setCheckedItems] = useState<Set<number>>(new Set());

  const toggleItem = (index: number) => {
    const newChecked = new Set(checkedItems);
    if (newChecked.has(index)) {
      newChecked.delete(index);
    } else {
      newChecked.add(index);
    }
    setCheckedItems(newChecked);
  };

  if (!isKnown) {
    return (
      <div className="bg-white shadow rounded-lg p-6 mb-6">
        <h2 className="text-xl font-bold text-gray-900 mb-4">Generic Filing Checklist</h2>
        <div className="bg-amber-50 border-l-4 border-amber-400 p-4 mb-4">
          <p className="text-sm text-amber-700">
            This is a generic filing checklist. Please verify the specific requirements with your local court.
            Visit the <a
              href="https://selfhelp.courts.ca.gov"
              target="_blank"
              rel="noopener noreferrer"
              className="font-semibold text-amber-800 hover:text-amber-900 underline"
            >
              California Court self-help center
            </a> for county-specific information.
          </p>
        </div>

        <div className="space-y-3">
          <div className="flex items-start">
            <input
              type="checkbox"
              id="generic-print"
              className="mt-1 h-4 w-4 text-primary-600 focus:ring-primary-500 border-gray-300 rounded cursor-pointer"
              checked={checkedItems.has(0)}
              onChange={() => toggleItem(0)}
            />
            <label htmlFor="generic-print" className="ml-3 text-sm text-gray-700 cursor-pointer">
              Print copies of your motion (original + 2 copies)
            </label>
          </div>

          <div className="flex items-start">
            <input
              type="checkbox"
              id="generic-sign"
              className="mt-1 h-4 w-4 text-primary-600 focus:ring-primary-500 border-gray-300 rounded cursor-pointer"
              checked={checkedItems.has(1)}
              onChange={() => toggleItem(1)}
            />
            <label htmlFor="generic-sign" className="ml-3 text-sm text-gray-700 cursor-pointer">
              Sign and date the original and all copies
            </label>
          </div>

          <div className="flex items-start">
            <input
              type="checkbox"
              id="generic-fee"
              className="mt-1 h-4 w-4 text-primary-600 focus:ring-primary-500 border-gray-300 rounded cursor-pointer"
              checked={checkedItems.has(2)}
              onChange={() => toggleItem(2)}
            />
            <label htmlFor="generic-fee" className="ml-3 text-sm text-gray-700 cursor-pointer">
              Determine filing fee or apply for fee waiver (Form FW-001)
            </label>
          </div>

          <div className="flex items-start">
            <input
              type="checkbox"
              id="generic-address"
              className="mt-1 h-4 w-4 text-primary-600 focus:ring-primary-500 border-gray-300 rounded cursor-pointer"
              checked={checkedItems.has(3)}
              onChange={() => toggleItem(3)}
            />
            <label htmlFor="generic-address" className="ml-3 text-sm text-gray-700 cursor-pointer">
              Locate your courthouse address and filing clerk hours
            </label>
          </div>

          <div className="flex items-start">
            <input
              type="checkbox"
              id="generic-serve"
              className="mt-1 h-4 w-4 text-primary-600 focus:ring-primary-500 border-gray-300 rounded cursor-pointer"
              checked={checkedItems.has(4)}
              onChange={() => toggleItem(4)}
            />
            <label htmlFor="generic-serve" className="ml-3 text-sm text-gray-700 cursor-pointer">
              Serve a copy on the other party (at least 16 court days before hearing)
            </label>
          </div>

          <div className="flex items-start">
            <input
              type="checkbox"
              id="generic-proof"
              className="mt-1 h-4 w-4 text-primary-600 focus:ring-primary-500 border-gray-300 rounded cursor-pointer"
              checked={checkedItems.has(5)}
              onChange={() => toggleItem(5)}
            />
            <label htmlFor="generic-proof" className="ml-3 text-sm text-gray-700 cursor-pointer">
              File proof of service (Form FL-335) with the court
            </label>
          </div>

          <div className="flex items-start">
            <input
              type="checkbox"
              id="generic-local-rules"
              className="mt-1 h-4 w-4 text-primary-600 focus:ring-primary-500 border-gray-300 rounded cursor-pointer"
              checked={checkedItems.has(6)}
              onChange={() => toggleItem(6)}
            />
            <label htmlFor="generic-local-rules" className="ml-3 text-sm text-gray-700 cursor-pointer">
              Review your county's local rules for family law — local rules may require additional local forms, cover sheets, or specific hearing scheduling steps
            </label>
          </div>
        </div>
      </div>
    );
  }

  return (
    <div className="bg-white shadow rounded-lg p-6 mb-6">
      <h2 className="text-xl font-bold text-gray-900 mb-4">
        {county} County Filing Checklist
      </h2>

      {/* Courthouse Information */}
      <div className="mb-6 p-4 bg-gray-50 rounded border border-gray-200">
        <h3 className="text-sm font-semibold text-gray-900 mb-2">Courthouse Information</h3>
        <p className="text-sm font-medium text-gray-900">{countyInfo!.courthouse.name}</p>
        <p className="text-sm text-gray-600 mt-1">{countyInfo!.courthouse.address}</p>
        {countyInfo!.additionalCourthouses && countyInfo!.additionalCourthouses.length > 0 && (
          <div className="mt-3">
            <p className="text-xs font-semibold text-gray-700 mb-1">Other family law locations in this county:</p>
            <ul className="space-y-1">
              {countyInfo!.additionalCourthouses.map((court) => (
                <li key={court.name} className="text-xs text-gray-600">
                  {court.name} — {court.address}
                </li>
              ))}
            </ul>
            <p className="text-xs text-gray-500 mt-1">
              Confirm which courthouse serves your case before filing.
            </p>
          </div>
        )}
      </div>

      {/* Local Rules & Resources */}
      <div className="mb-6 p-4 bg-amber-50 rounded border border-amber-200">
        <h3 className="text-sm font-semibold text-gray-900 mb-2">Local Rules &amp; Resources</h3>
        <p className="text-sm text-gray-700 mb-2">{countyInfo!.localRules.note}</p>
        <p className="text-sm text-gray-700 mb-2">{countyInfo!.eFiling.note}</p>
        <p className="text-sm">
          <a
            href={countyInfo!.localRules.url || countyInfo!.courtWebsite}
            target="_blank"
            rel="noopener noreferrer"
            className="font-semibold text-primary-700 hover:text-primary-900 underline"
          >
            {county} County court website
          </a>
        </p>
        {!countyInfo!.verification.verified && (
          <p className="text-xs text-amber-700 mt-2">
            County details shown here have not been verified against the court's current local
            rules. Always confirm requirements with the court before filing.
          </p>
        )}
      </div>

      {/* Filing Requirements */}
      <div className="mb-6 p-4 bg-primary-50 rounded border border-primary-200">
        <h3 className="text-sm font-semibold text-gray-900 mb-3">Filing Requirements</h3>
        <div className="space-y-2 text-sm text-gray-700">
          <p>
            <span className="font-medium">Filing Fee:</span> ${countyInfo!.filingFee.amount}
            <br />
            <span className="text-xs text-gray-600">{countyInfo!.filingFee.disclaimer}</span>
          </p>
          <p>
            <span className="font-medium">Fee Waiver:</span> Form {countyInfo!.feeWaiverForm} (if you cannot afford the fee)
          </p>
          <p>
            <span className="font-medium">Copies Required:</span> {countyInfo!.copiesRequired.original} original + {countyInfo!.copiesRequired.copies} copies
          </p>
          <p>
            <span className="font-medium">Service Deadline:</span>{' '}
            <span className="text-gray-600">{countyInfo!.serviceDeadline}</span>
          </p>
        </div>
      </div>

      {/* Filing Checklist */}
      <div className="space-y-3">
        <h3 className="text-sm font-semibold text-gray-900 mb-3">Filing Checklist</h3>

        <div className="flex items-start">
          <input
            type="checkbox"
            id="check-print"
            className="mt-1 h-4 w-4 text-primary-600 focus:ring-primary-500 border-gray-300 rounded cursor-pointer"
            checked={checkedItems.has(0)}
            onChange={() => toggleItem(0)}
          />
          <label htmlFor="check-print" className="ml-3 text-sm text-gray-700 cursor-pointer">
            Print {countyInfo!.copiesRequired.original} original + {countyInfo!.copiesRequired.copies} copies on white 8.5" x 11" paper
          </label>
        </div>

        <div className="flex items-start">
          <input
            type="checkbox"
            id="check-sign"
            className="mt-1 h-4 w-4 text-primary-600 focus:ring-primary-500 border-gray-300 rounded cursor-pointer"
            checked={checkedItems.has(1)}
            onChange={() => toggleItem(1)}
          />
          <label htmlFor="check-sign" className="ml-3 text-sm text-gray-700 cursor-pointer">
            Sign and date the original and all copies in blue or black ink
          </label>
        </div>

        <div className="flex items-start">
          <input
            type="checkbox"
            id="check-fee"
            className="mt-1 h-4 w-4 text-primary-600 focus:ring-primary-500 border-gray-300 rounded cursor-pointer"
            checked={checkedItems.has(2)}
            onChange={() => toggleItem(2)}
          />
          <label htmlFor="check-fee" className="ml-3 text-sm text-gray-700 cursor-pointer">
            Prepare filing fee (${countyInfo!.filingFee.amount}) or Form {countyInfo!.feeWaiverForm} for fee waiver
          </label>
        </div>

        <div className="flex items-start">
          <input
            type="checkbox"
            id="check-address"
            className="mt-1 h-4 w-4 text-primary-600 focus:ring-primary-500 border-gray-300 rounded cursor-pointer"
            checked={checkedItems.has(3)}
            onChange={() => toggleItem(3)}
          />
          <label htmlFor="check-address" className="ml-3 text-sm text-gray-700 cursor-pointer">
            Verify courthouse address and clerk hours before filing
          </label>
        </div>

        <div className="flex items-start">
          <input
            type="checkbox"
            id="check-serve"
            className="mt-1 h-4 w-4 text-primary-600 focus:ring-primary-500 border-gray-300 rounded cursor-pointer"
            checked={checkedItems.has(4)}
            onChange={() => toggleItem(4)}
          />
          <label htmlFor="check-serve" className="ml-3 text-sm text-gray-700 cursor-pointer">
            Serve the other party (at least 16 court days before hearing; 21 days if serving by mail)
          </label>
        </div>

        <div className="flex items-start">
          <input
            type="checkbox"
            id="check-proof"
            className="mt-1 h-4 w-4 text-primary-600 focus:ring-primary-500 border-gray-300 rounded cursor-pointer"
            checked={checkedItems.has(5)}
            onChange={() => toggleItem(5)}
          />
          <label htmlFor="check-proof" className="ml-3 text-sm text-gray-700 cursor-pointer">
            File proof of service (Form FL-335) with the court within 5 days of filing
          </label>
        </div>

        <div className="flex items-start">
          <input
            type="checkbox"
            id="check-local-rules"
            className="mt-1 h-4 w-4 text-primary-600 focus:ring-primary-500 border-gray-300 rounded cursor-pointer"
            checked={checkedItems.has(6)}
            onChange={() => toggleItem(6)}
          />
          <label htmlFor="check-local-rules" className="ml-3 text-sm text-gray-700 cursor-pointer">
            Review the {county} County local rules for family law (see Local Rules &amp; Resources above)
          </label>
        </div>
      </div>

      {/* Footer Note */}
      <div className="mt-6 pt-4 border-t border-gray-200">
        <p className="text-xs text-gray-500">
          This is general information only. Please consult the specific rules and procedures for {county} County Superior Court Family Court Division.
        </p>
      </div>
    </div>
  );
};
