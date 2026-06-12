// Form type definitions and constants

export interface FormMetadata {
  id: string;
  name: string;
  description: string;
  category: FormCategory;
  complexity: 'simple' | 'moderate' | 'complex';
  estimatedTime: string;
  icon: string;
  color: string;
  disabled?: boolean;
  comingSoon?: boolean;
}

export enum FormCategory {
  MOTIONS = 'motions',
  EMERGENCY = 'emergency',
  FINANCIAL = 'financial',
  SERVICE = 'service',
  CONTEMPT = 'contempt',
  GENERAL = 'general'
}

export const FORM_TYPES = {
  // Motion Forms
  FL_300: 'FL-300',
  FL_320: 'FL-320',

  // Emergency/Ex Parte Forms
  D_046: 'D-046',
  FL_305: 'FL-305',

  // Financial Forms
  FL_150: 'FL-150',

  // Service Forms
  FL_335: 'FL-335',

  // Contempt Forms
  FL_410: 'FL-410',
  FL_411: 'FL-411',

  // General Forms
  MC_030: 'MC-030'
} as const;

export type FormType = typeof FORM_TYPES[keyof typeof FORM_TYPES];

export const FORM_METADATA: Record<FormType, FormMetadata> = {
  [FORM_TYPES.FL_300]: {
    id: 'FL-300',
    name: 'Request for Order',
    description: 'File a new request with the court for custody, support, or other orders',
    category: FormCategory.MOTIONS,
    complexity: 'moderate',
    estimatedTime: '15-20 minutes',
    icon: 'DocumentTextIcon',
    color: 'indigo'
  },

  [FORM_TYPES.FL_320]: {
    id: 'FL-320',
    name: 'Response to Request for Order',
    description: 'Respond to an existing FL-300 filed by the other party',
    category: FormCategory.MOTIONS,
    complexity: 'moderate',
    estimatedTime: '15-20 minutes',
    icon: 'DocumentTextIcon',
    color: 'green'
  },

  [FORM_TYPES.D_046]: {
    id: 'D-046',
    name: 'Ex Parte Application (San Diego)',
    description: 'Emergency application for immediate court orders (San Diego County)',
    category: FormCategory.EMERGENCY,
    complexity: 'complex',
    estimatedTime: '20-30 minutes',
    icon: 'ExclamationTriangleIcon',
    color: 'red'
  },

  [FORM_TYPES.FL_305]: {
    id: 'FL-305',
    name: 'Temporary Emergency Orders',
    description: 'Court-issued emergency orders for custody, visitation, or property',
    category: FormCategory.EMERGENCY,
    complexity: 'complex',
    estimatedTime: '25-35 minutes',
    icon: 'ShieldExclamationIcon',
    color: 'orange'
  },

  [FORM_TYPES.FL_150]: {
    id: 'FL-150',
    name: 'Income and Expense Declaration',
    description: 'Required financial disclosure for support and fee requests',
    category: FormCategory.FINANCIAL,
    complexity: 'complex',
    estimatedTime: '30-45 minutes',
    icon: 'CurrencyDollarIcon',
    color: 'emerald'
  },

  [FORM_TYPES.FL_335]: {
    id: 'FL-335',
    name: 'Proof of Service by Mail',
    description: 'Legal proof that documents were properly served by mail',
    category: FormCategory.SERVICE,
    complexity: 'simple',
    estimatedTime: '5-10 minutes',
    icon: 'EnvelopeIcon',
    color: 'blue'
  },

  [FORM_TYPES.FL_410]: {
    id: 'FL-410',
    name: 'Order to Show Cause for Contempt',
    description: 'Request court action when someone violates existing orders',
    category: FormCategory.CONTEMPT,
    complexity: 'complex',
    estimatedTime: '25-35 minutes',
    icon: 'ScaleIcon',
    color: 'purple'
  },

  [FORM_TYPES.FL_411]: {
    id: 'FL-411',
    name: 'Contempt Facts (Financial Orders)',
    description: 'Detailed facts for financial order violations (companion to FL-410)',
    category: FormCategory.CONTEMPT,
    complexity: 'moderate',
    estimatedTime: '15-25 minutes',
    icon: 'CalculatorIcon',
    color: 'violet'
  },

  [FORM_TYPES.MC_030]: {
    id: 'MC-030',
    name: 'Declaration',
    description: 'General sworn statement form for factual information',
    category: FormCategory.GENERAL,
    complexity: 'simple',
    estimatedTime: '10-15 minutes',
    icon: 'DocumentCheckIcon',
    color: 'gray'
  }
};

export const FORMS_BY_CATEGORY = {
  [FormCategory.MOTIONS]: [FORM_TYPES.FL_300, FORM_TYPES.FL_320],
  [FormCategory.EMERGENCY]: [FORM_TYPES.D_046, FORM_TYPES.FL_305],
  [FormCategory.FINANCIAL]: [FORM_TYPES.FL_150],
  [FormCategory.SERVICE]: [FORM_TYPES.FL_335],
  [FormCategory.CONTEMPT]: [FORM_TYPES.FL_410, FORM_TYPES.FL_411],
  [FormCategory.GENERAL]: [FORM_TYPES.MC_030]
};

export const CATEGORY_METADATA = {
  [FormCategory.MOTIONS]: {
    name: 'Court Motions',
    description: 'Request new orders or respond to existing requests',
    icon: 'DocumentTextIcon',
    color: 'indigo'
  },
  [FormCategory.EMERGENCY]: {
    name: 'Emergency Orders',
    description: 'Urgent requests requiring immediate court attention',
    icon: 'ExclamationTriangleIcon',
    color: 'red'
  },
  [FormCategory.FINANCIAL]: {
    name: 'Financial Disclosure',
    description: 'Income and expense documentation for support matters',
    icon: 'CurrencyDollarIcon',
    color: 'green'
  },
  [FormCategory.SERVICE]: {
    name: 'Service of Process',
    description: 'Legal proof of document delivery',
    icon: 'EnvelopeIcon',
    color: 'blue'
  },
  [FormCategory.CONTEMPT]: {
    name: 'Contempt Actions',
    description: 'Enforcement when court orders are violated',
    icon: 'ScaleIcon',
    color: 'purple'
  },
  [FormCategory.GENERAL]: {
    name: 'General Forms',
    description: 'Supporting documents and declarations',
    icon: 'DocumentCheckIcon',
    color: 'gray'
  }
};

// Form validation and requirements
export interface FormRequirement {
  formType: FormType;
  requiredForms: FormType[];
  recommendedForms: FormType[];
  prerequisites: string[];
  warningMessage?: string;
}

export const FORM_REQUIREMENTS: Record<FormType, FormRequirement> = {
  [FORM_TYPES.FL_300]: {
    formType: FORM_TYPES.FL_300,
    requiredForms: [],
    recommendedForms: [FORM_TYPES.FL_150, FORM_TYPES.MC_030],
    prerequisites: ['Complete profile setup'],
    warningMessage: 'FL-150 Income Declaration may be required for support requests'
  },

  [FORM_TYPES.FL_320]: {
    formType: FORM_TYPES.FL_320,
    requiredForms: [],
    recommendedForms: [FORM_TYPES.FL_150, FORM_TYPES.MC_030],
    prerequisites: ['Must have received FL-300 from other party'],
    warningMessage: 'You must respond within 30 days of being served'
  },

  [FORM_TYPES.D_046]: {
    formType: FORM_TYPES.D_046,
    requiredForms: [FORM_TYPES.MC_030],
    recommendedForms: [],
    prerequisites: ['Emergency situation exists', 'San Diego County case'],
    warningMessage: 'Only for true emergencies - false emergencies may result in sanctions'
  },

  [FORM_TYPES.FL_305]: {
    formType: FORM_TYPES.FL_305,
    requiredForms: [],
    recommendedForms: [FORM_TYPES.MC_030],
    prerequisites: ['Court-issued form - filed by judge'],
    warningMessage: 'This form is typically completed by the court, not parties'
  },

  [FORM_TYPES.FL_150]: {
    formType: FORM_TYPES.FL_150,
    requiredForms: [],
    recommendedForms: [],
    prerequisites: ['Gather financial documents', 'Pay stubs', 'Tax returns'],
    warningMessage: 'Requires detailed financial information under penalty of perjury'
  },

  [FORM_TYPES.FL_335]: {
    formType: FORM_TYPES.FL_335,
    requiredForms: [],
    recommendedForms: [],
    prerequisites: ['Documents must have been mailed'],
    warningMessage: 'Cannot be used for restraining orders - personal service required'
  },

  [FORM_TYPES.FL_410]: {
    formType: FORM_TYPES.FL_410,
    requiredForms: [FORM_TYPES.FL_411],
    recommendedForms: [FORM_TYPES.FL_150],
    prerequisites: ['Existing court order was violated', 'Documentation of violation'],
    warningMessage: 'Contempt actions are serious - may result in jail time for violator'
  },

  [FORM_TYPES.FL_411]: {
    formType: FORM_TYPES.FL_411,
    requiredForms: [],
    recommendedForms: [],
    prerequisites: ['Must accompany FL-410', 'Financial order violations only'],
    warningMessage: 'Requires detailed tracking of missed payments'
  },

  [FORM_TYPES.MC_030]: {
    formType: FORM_TYPES.MC_030,
    requiredForms: [],
    recommendedForms: [],
    prerequisites: ['Factual information to declare'],
    warningMessage: 'Information provided under penalty of perjury'
  }
};