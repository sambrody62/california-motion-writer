/**
 * County filing information for California family court motions.
 *
 * This file is the canonical dataset for county-specific filing rules:
 * courthouse locations, filing fees, copy/service requirements, and pointers
 * to each county's local rules. See docs/COUNTY_RULES.md for the schema,
 * the verification workflow, and how to add a new county.
 *
 * IMPORTANT: entries with `verification.verified === false` contain
 * best-effort data that has NOT been confirmed against the court's current
 * local rules. The UI must always present unverified details with a
 * "confirm with the court" disclaimer — never as authoritative.
 */

export interface Courthouse {
  name: string;
  address: string;
}

export interface CountyFilingInfo {
  name: string;
  courthouse: Courthouse;
  /** Additional family law courthouse locations, when the county has more than one. */
  additionalCourthouses?: Courthouse[];
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
  /** Official Superior Court website for the county. */
  courtWebsite: string;
  /**
   * Where to find the county's local rules. Local rules govern things the
   * statewide Judicial Council forms don't: local cover sheets, department
   * assignment, hearing reservation procedures, and mandatory local forms.
   */
  localRules: {
    /** Direct link if known and stable; omit rather than guess. */
    url?: string;
    note: string;
  };
  eFiling: {
    note: string;
  };
  verification: {
    verified: boolean;
    /** ISO date of last human review against the court's published rules. */
    lastReviewed?: string;
  };
}

const VERIFY_WITH_COURT_DISCLAIMER =
  'Please verify with your local court as fees may change. Call or visit the courthouse for current rates.';

const SERVICE_DEADLINE_TEXT =
  'Serve at least 16 court days before the hearing; add 5 calendar days if serving by mail.';

const LOCAL_RULES_NOTE =
  "Check the court website's Local Rules section for family law requirements before filing — local rules cover mandatory local forms, department assignment, and hearing scheduling procedures.";

const EFILING_CHECK_NOTE =
  'E-filing may be available or required in this county. Check the court website for current e-filing requirements for family law before filing on paper.';

export const countyFilingDatabase: Record<string, CountyFilingInfo> = {
  'San Diego': {
    name: 'San Diego',
    courthouse: {
      name: 'San Diego Superior Court - Family Court Division (Central Division)',
      address: '1100 Union Street, San Diego, CA 92101'
    },
    additionalCourthouses: [
      { name: 'East County Division', address: '250 E. Main St., El Cajon, CA 92020' },
      { name: 'North County Division', address: '325 S. Melrose Dr., Vista, CA 92081' },
      { name: 'South County Division', address: '500 3rd Ave., Chula Vista, CA 91910' }
    ],
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
    serviceDeadline: SERVICE_DEADLINE_TEXT,
    courtWebsite: 'https://www.sdcourt.ca.gov',
    localRules: {
      note: LOCAL_RULES_NOTE
    },
    eFiling: {
      note: EFILING_CHECK_NOTE
    },
    verification: {
      verified: false
    }
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
    serviceDeadline: SERVICE_DEADLINE_TEXT,
    courtWebsite: 'https://www.lacourt.org',
    localRules: {
      note:
        LOCAL_RULES_NOTE +
        ' Los Angeles County has multiple family law courthouses — confirm which courthouse serves your case before filing.'
    },
    eFiling: {
      note: EFILING_CHECK_NOTE
    },
    verification: {
      verified: false
    }
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
    serviceDeadline: SERVICE_DEADLINE_TEXT,
    courtWebsite: 'https://www.occourts.org',
    localRules: {
      note: LOCAL_RULES_NOTE
    },
    eFiling: {
      note: EFILING_CHECK_NOTE
    },
    verification: {
      verified: false
    }
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
    serviceDeadline: SERVICE_DEADLINE_TEXT,
    courtWebsite: 'https://www.riverside.courts.ca.gov',
    localRules: {
      note: LOCAL_RULES_NOTE
    },
    eFiling: {
      note: EFILING_CHECK_NOTE
    },
    verification: {
      verified: false
    }
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
    serviceDeadline: SERVICE_DEADLINE_TEXT,
    courtWebsite: 'https://www.saccourt.ca.gov',
    localRules: {
      note: LOCAL_RULES_NOTE
    },
    eFiling: {
      note: EFILING_CHECK_NOTE
    },
    verification: {
      verified: false
    }
  }
};

export function getCountyFilingInfo(county: string): CountyFilingInfo | null {
  return countyFilingDatabase[county] || null;
}

export function isKnownCounty(county: string): boolean {
  return county in countyFilingDatabase;
}

export const ALL_SUPPORTED_COUNTIES = Object.keys(countyFilingDatabase);
