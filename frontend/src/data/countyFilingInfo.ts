/**
 * County filing information for California family court motions
 * Includes courthouse locations, filing fees, and filing requirements
 */

export interface CountyFilingInfo {
  name: string;
  courthouse: {
    name: string;
    address: string;
  };
  filingFee: {
    amount: number;
    currency: string;
    disclaimer: string;
  };
  feeWaiverForm: string;
  copiesRequired: {
    original: number;
    copies: number;
  };
  serviceDeadline: string;
}

const VERIFY_WITH_COURT_DISCLAIMER =
  'Please verify with your local court as fees may change. Call or visit the courthouse for current rates.';

const SERVICE_DEADLINE_TEXT =
  'Serve at least 16 court days before the hearing; add 5 calendar days if serving by mail.';

export const countyFilingDatabase: Record<string, CountyFilingInfo> = {
  'San Diego': {
    name: 'San Diego',
    courthouse: {
      name: 'San Diego Superior Court - Family Court Division',
      address: '1100 Union Street, San Diego, CA 92101'
    },
    filingFee: {
      amount: 60,
      currency: 'USD',
      disclaimer: VERIFY_WITH_COURT_DISCLAIMER
    },
    feeWaiverForm: 'FW-001',
    copiesRequired: {
      original: 1,
      copies: 2
    },
    serviceDeadline: SERVICE_DEADLINE_TEXT
  },
  'Los Angeles': {
    name: 'Los Angeles',
    courthouse: {
      name: 'Los Angeles Superior Court - Family Court Division',
      address: '111 North Hill Street, Los Angeles, CA 90012'
    },
    filingFee: {
      amount: 60,
      currency: 'USD',
      disclaimer: VERIFY_WITH_COURT_DISCLAIMER
    },
    feeWaiverForm: 'FW-001',
    copiesRequired: {
      original: 1,
      copies: 2
    },
    serviceDeadline: SERVICE_DEADLINE_TEXT
  },
  'Orange': {
    name: 'Orange',
    courthouse: {
      name: 'Orange County Superior Court - Family Court Division',
      address: '700 Civic Center Drive West, Santa Ana, CA 92701'
    },
    filingFee: {
      amount: 60,
      currency: 'USD',
      disclaimer: VERIFY_WITH_COURT_DISCLAIMER
    },
    feeWaiverForm: 'FW-001',
    copiesRequired: {
      original: 1,
      copies: 2
    },
    serviceDeadline: SERVICE_DEADLINE_TEXT
  },
  'Riverside': {
    name: 'Riverside',
    courthouse: {
      name: 'Riverside County Superior Court - Family Court Division',
      address: '4050 Main Street, Riverside, CA 92501'
    },
    filingFee: {
      amount: 60,
      currency: 'USD',
      disclaimer: VERIFY_WITH_COURT_DISCLAIMER
    },
    feeWaiverForm: 'FW-001',
    copiesRequired: {
      original: 1,
      copies: 2
    },
    serviceDeadline: SERVICE_DEADLINE_TEXT
  },
  'Sacramento': {
    name: 'Sacramento',
    courthouse: {
      name: 'Sacramento County Superior Court - Family Court Division',
      address: '813 6th Street, Sacramento, CA 95814'
    },
    filingFee: {
      amount: 60,
      currency: 'USD',
      disclaimer: VERIFY_WITH_COURT_DISCLAIMER
    },
    feeWaiverForm: 'FW-001',
    copiesRequired: {
      original: 1,
      copies: 2
    },
    serviceDeadline: SERVICE_DEADLINE_TEXT
  }
};

export function getCountyFilingInfo(county: string): CountyFilingInfo | null {
  return countyFilingDatabase[county] || null;
}

export function isKnownCounty(county: string): boolean {
  return county in countyFilingDatabase;
}

export const ALL_SUPPORTED_COUNTIES = Object.keys(countyFilingDatabase);
