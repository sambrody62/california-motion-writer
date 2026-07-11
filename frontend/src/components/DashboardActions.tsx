import React from 'react';
import { useNavigate } from 'react-router-dom';
import {
  ScaleIcon,
  InboxArrowDownIcon,
  DocumentPlusIcon,
  ArrowRightIcon,
} from '@heroicons/react/24/outline';

interface ActionCard {
  icon: React.ComponentType<React.SVGProps<SVGSVGElement>>;
  title: string;
  description: string;
  ariaLabel: string;
  route: string;
}

// Copy stays document-preparation phrasing only — never "legal help",
// "strategy", or "advice" (UPL guardrail)
const ACTIONS: ActionCard[] = [
  {
    icon: ScaleIcon,
    title: 'Enforce an existing order',
    description:
      'If the other party is not following a court order, you may have options to enforce it.',
    ariaLabel: 'Enforce an existing order',
    route: '/violation/intake',
  },
  {
    icon: InboxArrowDownIcon,
    title: 'Respond to a motion you were served',
    description:
      'Prepare a Response to Request for Order (FL-320) using the papers you received.',
    ariaLabel: 'Respond to a motion you were served',
    route: '/motion/guided/FL-320',
  },
  {
    icon: DocumentPlusIcon,
    title: 'Request a court order (FL-300)',
    description:
      'Prepare a Request for Order (FL-300) for custody, visitation, or support matters.',
    ariaLabel: 'Request a court order',
    route: '/form/guided/FL-300',
  },
];

// Direct entry points for the three document flows. Before this, FL-320 was
// reachable only by typing the URL and there was no direct FL-300 start (L17)
export const DashboardActions: React.FC = () => {
  const navigate = useNavigate();

  return (
    <div className="mb-8 grid grid-cols-1 md:grid-cols-3 gap-4">
      {ACTIONS.map((action) => (
        <div
          key={action.route}
          className="bg-white border border-gray-200 rounded-lg p-6 shadow-sm flex flex-col justify-between gap-4"
        >
          <div className="flex items-start space-x-3">
            <action.icon className="h-6 w-6 text-primary-500 flex-shrink-0 mt-0.5" />
            <div>
              <h3 className="text-base font-semibold text-gray-900">{action.title}</h3>
              <p className="text-sm text-gray-600 mt-1">{action.description}</p>
            </div>
          </div>
          <button
            onClick={() => navigate(action.route)}
            aria-label={action.ariaLabel}
            className="inline-flex items-center self-start px-4 py-2 border border-primary-300 shadow-sm text-sm font-medium rounded-md text-primary-700 bg-white hover:bg-primary-50 focus:outline-none focus:ring-2 focus:ring-offset-2 focus:ring-primary-500"
          >
            Get started
            <ArrowRightIcon className="h-4 w-4 ml-2" />
          </button>
        </div>
      ))}
    </div>
  );
};
