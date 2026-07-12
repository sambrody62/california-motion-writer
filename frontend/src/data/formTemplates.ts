// Form templates and question sets for California court forms
import { FormType, FORM_TYPES } from '../types/forms';

export interface Question {
  id: string;
  type: 'text' | 'textarea' | 'select' | 'radio' | 'checkbox' | 'date' | 'time' | 'currency' | 'number';
  label: string;
  required: boolean;
  options?: string[];
  placeholder?: string;
  help_text?: string;
  condition?: string;
  validation?: {
    pattern?: string;
    min?: number;
    max?: number;
    message?: string;
  };
}

export interface FormStep {
  step_number: number;
  step_name: string;
  description: string;
  questions: Question[];
}

export interface FormTemplate {
  form_type: FormType;
  title: string;
  total_steps: number;
  steps: FormStep[];
}

// FL-300: Request for Order
const FL_300_TEMPLATE: FormTemplate = {
  form_type: FORM_TYPES.FL_300,
  title: 'Request for Order (FL-300)',
  total_steps: 6,
  steps: [
    {
      step_number: 1,
      step_name: 'Case Information',
      description: 'Provide basic information about your family law case',
      questions: [
        {
          id: 'case_number',
          type: 'text',
          label: 'Case Number',
          required: false,
          placeholder: 'FL12345678',
          help_text: 'If you already have a case number, enter it here. Leave blank if this is a new case.'
        },
        {
          id: 'court_name',
          type: 'text',
          label: 'Court Name',
          required: true,
          placeholder: 'Superior Court of California, County of San Diego',
          help_text: 'Enter the full name of the court where you are filing'
        },
        {
          id: 'county',
          type: 'select',
          label: 'County',
          required: true,
          options: [
            'Alameda', 'Alpine', 'Amador', 'Butte', 'Calaveras', 'Colusa', 'Contra Costa',
            'Del Norte', 'El Dorado', 'Fresno', 'Glenn', 'Humboldt', 'Imperial', 'Inyo',
            'Kern', 'Kings', 'Lake', 'Lassen', 'Los Angeles', 'Madera', 'Marin', 'Mariposa',
            'Mendocino', 'Merced', 'Modoc', 'Mono', 'Monterey', 'Napa', 'Nevada', 'Orange',
            'Placer', 'Plumas', 'Riverside', 'Sacramento', 'San Benito', 'San Bernardino',
            'San Diego', 'San Francisco', 'San Joaquin', 'San Luis Obispo', 'San Mateo',
            'Santa Barbara', 'Santa Clara', 'Santa Cruz', 'Shasta', 'Sierra', 'Siskiyou',
            'Solano', 'Sonoma', 'Stanislaus', 'Sutter', 'Tehama', 'Trinity', 'Tulare',
            'Tuolumne', 'Ventura', 'Yolo', 'Yuba'
          ]
        },
        {
          id: 'other_party_name',
          type: 'text',
          label: 'Other Party\'s Name',
          required: true,
          placeholder: 'First and Last Name',
          help_text: 'Enter the full legal name of the other parent or party'
        }
      ]
    },
    {
      step_number: 2,
      step_name: 'Orders Requested',
      description: 'Select the types of orders you are requesting from the court',
      questions: [
        {
          id: 'case_type',
          type: 'radio',
          label: 'What best describes your case?',
          required: true,
          options: [
            'Custody and visitation only',
            'Support only',
            'Custody, visitation, and support',
            'Other family law matter'
          ],
          help_text: 'This helps determine which questions are relevant to your situation. You choose what to request.'
        },
        {
          id: 'order_types',
          type: 'checkbox',
          label: 'What orders are you requesting?',
          required: true,
          options: [
            'Child custody and visitation (parenting time)',
            'Child support',
            'Spousal support (alimony)',
            'Property control',
            'Debt responsibility',
            'Attorney fees and costs',
            'Other'
          ],
          help_text: 'Check all that apply. You can request multiple types of orders.'
        },
        {
          id: 'other_order_description',
          type: 'textarea',
          label: 'Describe other orders requested',
          required: false,
          condition: 'order_types.Other',
          placeholder: 'Describe any other orders you are requesting...',
          help_text: 'If you selected "Other" above, please describe the specific orders you need.'
        }
      ]
    },
    {
      step_number: 3,
      step_name: 'Child Custody & Visitation',
      description: 'Provide details about child custody and visitation arrangements',
      questions: [
        {
          id: 'has_children',
          type: 'radio',
          label: 'Do you have minor children with the other party?',
          required: true,
          options: ['Yes', 'No']
        },
        {
          id: 'children_names_ages',
          type: 'textarea',
          label: 'Children\'s Names and Ages',
          required: true,
          condition: 'has_children == "Yes"',
          placeholder: 'List each child\'s full name and current age',
          help_text: 'Example: John Smith (age 8), Jane Smith (age 5)'
        },
        {
          id: 'current_custody',
          type: 'textarea',
          label: 'Current Custody Arrangement',
          required: false,
          condition: 'case_type != "Support only" && has_children == "Yes"',
          placeholder: 'Describe who the children currently live with and any existing custody orders',
          help_text: 'Include any temporary orders or informal arrangements currently in place'
        },
        {
          id: 'requested_custody',
          type: 'textarea',
          label: 'Requested Custody Arrangement',
          required: true,
          condition: 'case_type != "Support only" && has_children == "Yes"',
          placeholder: 'Describe the custody and visitation schedule you are requesting',
          help_text: 'Be specific about days, times, holidays, and vacation schedules'
        }
      ]
    },
    {
      step_number: 4,
      step_name: 'Financial Support',
      description: 'Provide information about child support and spousal support requests',
      questions: [
        {
          id: 'child_support_requested',
          type: 'radio',
          label: 'Are you requesting child support?',
          required: true,
          options: ['Yes', 'No'],
          condition: 'has_children == "Yes"'
        },
        {
          id: 'monthly_income',
          type: 'currency',
          label: 'Your Monthly Gross Income',
          required: true,
          condition: 'child_support_requested == "Yes"',
          help_text: 'Enter your total monthly income before taxes and deductions'
        },
        {
          id: 'other_party_income',
          type: 'currency',
          label: 'Other Party\'s Monthly Gross Income (if known)',
          required: false,
          condition: 'child_support_requested == "Yes"',
          help_text: 'If you know the other party\'s income, enter it here'
        },
        {
          id: 'spousal_support_requested',
          type: 'radio',
          label: 'Are you requesting spousal support?',
          required: true,
          options: ['Yes', 'No']
        },
        {
          id: 'spousal_support_amount',
          type: 'currency',
          label: 'Monthly Spousal Support Requested',
          required: true,
          condition: 'spousal_support_requested == "Yes"',
          help_text: 'Enter the monthly amount you are requesting'
        }
      ]
    },
    {
      step_number: 5,
      step_name: 'Facts Supporting Request',
      description: 'Explain the facts and circumstances that support your request',
      questions: [
        {
          id: 'facts_summary',
          type: 'textarea',
          label: 'Summary of Facts',
          required: true,
          placeholder: 'Provide a clear, factual description of the circumstances that support your request...',
          help_text: 'Include relevant dates, events, and circumstances. Be factual and avoid emotional language.'
        },
        {
          id: 'changed_circumstances',
          type: 'textarea',
          label: 'Changed Circumstances',
          required: false,
          placeholder: 'If this modifies an existing order, describe what has changed...',
          help_text: 'If you are modifying existing orders, explain what significant changes have occurred.'
        },
        {
          id: 'best_interest_children',
          type: 'textarea',
          label: 'Why This Request is in the Children\'s Best Interest',
          required: true,
          condition: 'has_children == "Yes"',
          placeholder: 'Explain how your requested orders will benefit the children...',
          help_text: 'Focus on stability, safety, education, health, and emotional well-being of the children.'
        }
      ]
    },
    {
      step_number: 6,
      step_name: 'Hearing Information',
      description: 'Provide details about the requested hearing',
      questions: [
        {
          id: 'hearing_requested',
          type: 'radio',
          label: 'Are you requesting a hearing?',
          required: true,
          options: ['Yes', 'No'],
          help_text: 'Most requests require a hearing where both parties can present their case'
        },
        {
          id: 'urgency_level',
          type: 'radio',
          label: 'How urgent is this matter?',
          required: true,
          options: ['Emergency (immediate danger)', 'Urgent (within 2 weeks)', 'Standard (normal court scheduling)'],
          help_text: 'Select the appropriate urgency level for your situation'
        },
        {
          id: 'emergency_explanation',
          type: 'textarea',
          label: 'Explain Emergency Circumstances',
          required: true,
          condition: 'urgency_level == "Emergency (immediate danger)"',
          placeholder: 'Describe the immediate danger or emergency that requires urgent court action...',
          help_text: 'Be specific about the immediate risk to you or the children'
        },
        {
          id: 'service_method',
          type: 'radio',
          label: 'How will you serve the other party?',
          required: true,
          options: ['Personal service by sheriff', 'Personal service by process server', 'Certified mail', 'Other'],
          help_text: 'You must properly serve the other party with court papers'
        }
      ]
    }
  ]
};

// FL-320: Response to Request for Order (3-screen flow)
const FL_320_TEMPLATE: FormTemplate = {
  form_type: FORM_TYPES.FL_320,
  title: 'Response to Request for Order (FL-320)',
  total_steps: 3,
  steps: [
    {
      step_number: 1,
      step_name: 'Case Information & Service',
      description: 'Confirm the case information from the Request for Order you received',
      questions: [
        {
          id: 'case_number',
          type: 'text',
          label: 'Case Number',
          required: true,
          placeholder: 'FL12345678',
          help_text: 'Enter the case number from the Request for Order you received'
        },
        {
          id: 'petitioner_name',
          type: 'text',
          label: 'Petitioner\'s Name',
          required: true,
          help_text: 'The person who filed the original Request for Order'
        },
        {
          id: 'hearing_date',
          type: 'date',
          label: 'Scheduled Hearing Date',
          required: true,
          help_text: 'Enter the hearing date from the Request for Order'
        },
        {
          id: 'hearing_time',
          type: 'time',
          label: 'Scheduled Hearing Time',
          required: true,
          help_text: 'Enter the hearing time from the Request for Order'
        },
        {
          id: 'date_served',
          type: 'date',
          label: 'Date You Were Served',
          required: true,
          help_text: 'The date you personally received or were served with the Request for Order'
        }
      ]
    },
    {
      step_number: 2,
      step_name: 'Response to Requests',
      description: 'Describe what the other party requested and your position on each item',
      questions: [
        {
          id: 'other_party_requests',
          type: 'textarea',
          label: 'What did the other party request?',
          required: true,
          placeholder: 'Summarize the orders the other party is asking the court to make...',
          help_text: 'You can find this information in the Request for Order (FL-300) you received'
        },
        {
          id: 'agree_with_requests',
          type: 'radio',
          label: 'Do you agree with what the other party is requesting?',
          required: true,
          options: ['Yes, I agree', 'No, I disagree', 'I partially agree']
        },
        {
          id: 'disagreement_details',
          type: 'textarea',
          label: 'What do you disagree with?',
          required: true,
          condition: 'agree_with_requests == "No, I disagree" || agree_with_requests == "I partially agree"',
          placeholder: 'Describe specifically what you disagree with and why...',
          help_text: 'Be factual and specific. Include dates and relevant circumstances.'
        }
      ]
    },
    {
      step_number: 3,
      step_name: 'Your Requests & Additional Information',
      description: 'State what you would like the court to order and provide any additional information',
      questions: [
        {
          id: 'your_requested_orders',
          type: 'textarea',
          label: 'What orders would you like the court to make instead?',
          required: false,
          placeholder: 'Describe the specific orders you are asking the court to make...',
          help_text: 'If you agree with everything, you may leave this blank. Be specific about dates, amounts, and schedules.'
        },
        {
          id: 'supporting_facts',
          type: 'textarea',
          label: 'Additional facts supporting your position',
          required: false,
          placeholder: 'Include any other relevant facts, dates, or circumstances the court should know...',
          help_text: 'Focus on factual information. Avoid emotional language.'
        },
        {
          id: 'requests_attorney_fees',
          type: 'radio',
          label: 'Are you requesting that the other party pay your attorney fees or costs?',
          required: true,
          options: ['Yes', 'No'],
          help_text: 'The court may award fees based on each party\'s financial circumstances'
        }
      ]
    }
  ]
};

// FL-150: Income and Expense Declaration (3-screen flow)
const FL_150_TEMPLATE: FormTemplate = {
  form_type: FORM_TYPES.FL_150,
  title: 'Income and Expense Declaration (FL-150)',
  total_steps: 3,
  steps: [
    {
      step_number: 1,
      step_name: 'Income Source',
      description: 'Provide information about your primary income source and any other income',
      questions: [
        {
          id: 'income_source',
          type: 'radio',
          label: 'Primary income source',
          required: true,
          options: [
            'W-2 employee',
            'Self-employed',
            'Fixed income (pension/SSI/disability)',
            'Other'
          ],
          help_text: 'Select the category that best describes your main source of income'
        },
        {
          id: 'gross_monthly_income',
          type: 'currency',
          label: 'Gross Monthly Income',
          required: true,
          condition: 'income_source == "W-2 employee"',
          help_text: 'Your total monthly income before taxes and deductions (from pay stubs)'
        },
        {
          id: 'last_year_net_income',
          type: 'currency',
          label: 'Last Year Net Income (self-employment)',
          required: true,
          condition: 'income_source == "Self-employed"',
          help_text: 'Your net profit from self-employment or business last calendar year (from Schedule C or tax return)'
        },
        {
          id: 'fixed_monthly_income',
          type: 'currency',
          label: 'Monthly Fixed Income Amount',
          required: true,
          condition: 'income_source == "Fixed income (pension/SSI/disability)"',
          help_text: 'Total monthly amount received from pension, SSI, disability, or other fixed source'
        },
        {
          id: 'other_income_description',
          type: 'text',
          label: 'Describe your income source',
          required: true,
          condition: 'income_source == "Other"',
          placeholder: 'e.g., rental income, freelance, investments...',
          help_text: 'Describe where your income comes from'
        },
        {
          id: 'other_income_amount',
          type: 'currency',
          label: 'Monthly Income Amount',
          required: true,
          condition: 'income_source == "Other"',
          help_text: 'Average monthly amount from the income source described above'
        },
        {
          id: 'additional_income',
          type: 'currency',
          label: 'Other monthly income (rental, investments, unemployment, etc.)',
          required: false,
          help_text: 'Any other regular monthly income not included above. Enter 0 if none.'
        },
        {
          id: 'additional_income_description',
          type: 'text',
          label: 'Describe other monthly income',
          required: false,
          condition: 'additional_income > 0',
          placeholder: 'Describe the source of this additional income'
        }
      ]
    },
    {
      step_number: 2,
      step_name: 'Monthly Expenses',
      description: 'List your average monthly expenses and indicate whether you support other children',
      questions: [
        {
          id: 'housing_payment',
          type: 'currency',
          label: 'Housing Payment (rent/mortgage)',
          required: true,
          help_text: 'Monthly rent or mortgage payment'
        },
        {
          id: 'utilities',
          type: 'currency',
          label: 'Utilities',
          required: true,
          help_text: 'Gas, electric, water, trash, internet, etc.'
        },
        {
          id: 'food_household',
          type: 'currency',
          label: 'Food and Household Supplies',
          required: true,
          help_text: 'Groceries and household items'
        },
        {
          id: 'transportation',
          type: 'currency',
          label: 'Transportation',
          required: true,
          help_text: 'Car payment, gas, maintenance, public transit'
        },
        {
          id: 'health_insurance',
          type: 'currency',
          label: 'Health Insurance',
          required: false,
          help_text: 'Monthly health insurance premiums (your share)'
        },
        {
          id: 'childcare',
          type: 'currency',
          label: 'Childcare',
          required: false,
          help_text: 'Daycare, babysitting, after-school care for children in this case'
        },
        {
          id: 'other_monthly_expenses',
          type: 'currency',
          label: 'Other monthly expenses',
          required: false,
          help_text: 'Any other significant monthly expenses not listed above'
        },
        {
          id: 'supports_other_children',
          type: 'radio',
          label: 'Do you support other children not in this case?',
          required: true,
          options: ['Yes', 'No'],
          help_text: 'Children from another relationship who are not part of this court case'
        },
        {
          id: 'other_children_count',
          type: 'number',
          label: 'Number of other children you support',
          required: true,
          condition: 'supports_other_children == "Yes"',
          validation: { min: 1, message: 'Enter a number greater than 0' }
        },
        {
          id: 'other_children_support_amount',
          type: 'currency',
          label: 'Monthly support amount for other children (total)',
          required: true,
          condition: 'supports_other_children == "Yes"',
          help_text: 'Total monthly amount you pay to support all other children not in this case'
        }
      ]
    },
    {
      step_number: 3,
      step_name: 'Assets',
      description: 'Provide information about your assets',
      questions: [
        {
          id: 'has_assets',
          type: 'radio',
          label: 'Do you have significant assets (bank accounts, property, retirement accounts, etc.)?',
          required: true,
          options: ['Yes', 'No'],
          help_text: 'Assets include cash, real estate, vehicles, investments, and retirement accounts'
        },
        {
          id: 'assets_description',
          type: 'textarea',
          label: 'Describe your assets and estimated values',
          required: true,
          condition: 'has_assets == "Yes"',
          placeholder: 'Example: Checking account ~$2,000; 2018 Honda Civic ~$12,000; 401k ~$45,000...',
          help_text: 'List each significant asset and its approximate current value. Approximate values are acceptable.'
        },
        {
          id: 'has_significant_debts',
          type: 'radio',
          label: 'Do you have significant debts (mortgage, loans, credit cards, etc.)?',
          required: true,
          options: ['Yes', 'No']
        },
        {
          id: 'debts_description',
          type: 'textarea',
          label: 'Describe your debts and amounts owed',
          required: true,
          condition: 'has_significant_debts == "Yes"',
          placeholder: 'Example: Mortgage balance ~$280,000; Car loan ~$8,000; Credit cards ~$3,500...',
          help_text: 'List each significant debt and the approximate balance remaining'
        }
      ]
    }
  ]
};

// Add templates for other forms with simplified versions for now
const OTHER_FORM_TEMPLATES: FormTemplate[] = [
  {
    form_type: FORM_TYPES.D_046,
    title: 'Ex Parte Application (D-046)',
    total_steps: 3,
    steps: [
      {
        step_number: 1,
        step_name: 'Emergency Circumstances',
        description: 'Describe the emergency situation requiring immediate court action',
        questions: [
          {
            id: 'emergency_nature',
            type: 'textarea',
            label: 'Nature of Emergency',
            required: true,
            placeholder: 'Describe the specific emergency circumstances...',
            help_text: 'Be specific about the immediate danger or urgent situation'
          },
          {
            id: 'immediate_harm',
            type: 'textarea',
            label: 'Immediate Harm if Relief Not Granted',
            required: true,
            placeholder: 'Explain what harm will occur if the court does not act immediately...',
            help_text: 'Focus on irreparable harm that would occur if you wait for a regular hearing'
          }
        ]
      },
      {
        step_number: 2,
        step_name: 'Relief Requested',
        description: 'Specify the emergency orders you are requesting',
        questions: [
          {
            id: 'emergency_orders',
            type: 'textarea',
            label: 'Emergency Orders Requested',
            required: true,
            placeholder: 'List the specific orders you need from the court...',
            help_text: 'Be specific about the temporary orders needed to address the emergency'
          }
        ]
      },
      {
        step_number: 3,
        step_name: 'Supporting Declaration',
        description: 'Provide facts supporting your emergency request',
        questions: [
          {
            id: 'supporting_facts',
            type: 'textarea',
            label: 'Supporting Facts',
            required: true,
            placeholder: 'Provide detailed facts supporting your emergency request...',
            help_text: 'Include dates, times, witnesses, and specific incidents'
          }
        ]
      }
    ]
  },
  {
    form_type: FORM_TYPES.FL_335,
    title: 'Proof of Service by Mail (FL-335)',
    total_steps: 2,
    steps: [
      {
        step_number: 1,
        step_name: 'Service Information',
        description: 'Provide details about how documents were served by mail',
        questions: [
          {
            id: 'documents_served',
            type: 'textarea',
            label: 'Documents Served',
            required: true,
            placeholder: 'List all documents that were served...',
            help_text: 'List each document by name and form number'
          },
          {
            id: 'person_served',
            type: 'text',
            label: 'Person Served',
            required: true,
            placeholder: 'Full name of person served',
            help_text: 'Enter the full legal name of the person who was served'
          },
          {
            id: 'service_address',
            type: 'textarea',
            label: 'Address Where Served',
            required: true,
            placeholder: 'Complete mailing address...',
            help_text: 'Enter the complete address where documents were mailed'
          }
        ]
      },
      {
        step_number: 2,
        step_name: 'Service Details',
        description: 'Confirm the details of service by mail',
        questions: [
          {
            id: 'service_date',
            type: 'date',
            label: 'Date of Service',
            required: true,
            help_text: 'Date when documents were placed in the mail'
          },
          {
            id: 'service_method',
            type: 'radio',
            label: 'Method of Service',
            required: true,
            options: ['Certified mail', 'First-class mail'],
            help_text: 'How were the documents mailed?'
          }
        ]
      }
    ]
  }
];

// Export all form templates
export const FORM_TEMPLATES: Record<FormType, FormTemplate> = {
  [FORM_TYPES.FL_300]: FL_300_TEMPLATE,
  [FORM_TYPES.FL_320]: FL_320_TEMPLATE,
  [FORM_TYPES.FL_150]: FL_150_TEMPLATE,
  [FORM_TYPES.D_046]: OTHER_FORM_TEMPLATES[0],
  [FORM_TYPES.FL_305]: {
    form_type: FORM_TYPES.FL_305,
    title: 'Temporary Emergency Orders (FL-305)',
    total_steps: 1,
    steps: [
      {
        step_number: 1,
        step_name: 'Court Use Only',
        description: 'This form is typically completed by the court, not parties',
        questions: [
          {
            id: 'court_note',
            type: 'text',
            label: 'Note',
            required: false,
            placeholder: 'This form is usually filled out by the judge',
            help_text: 'FL-305 is typically completed by the court as part of emergency proceedings'
          }
        ]
      }
    ]
  },
  [FORM_TYPES.FL_335]: OTHER_FORM_TEMPLATES[1],
  [FORM_TYPES.FL_410]: {
    form_type: FORM_TYPES.FL_410,
    title: 'Order to Show Cause for Contempt (FL-410)',
    total_steps: 3,
    steps: [
      {
        step_number: 1,
        step_name: 'Violation Details',
        description: 'Describe how court orders were violated',
        questions: [
          {
            id: 'order_violated',
            type: 'textarea',
            label: 'Court Order Violated',
            required: true,
            placeholder: 'Describe the specific court order that was violated...',
            help_text: 'Include the date and details of the original order'
          },
          {
            id: 'violation_description',
            type: 'textarea',
            label: 'How Order Was Violated',
            required: true,
            placeholder: 'Describe specifically how the order was violated...',
            help_text: 'Include dates, times, and specific actions or failures to act'
          }
        ]
      },
      {
        step_number: 2,
        step_name: 'Documentation',
        description: 'Provide evidence of the violation',
        questions: [
          {
            id: 'evidence_available',
            type: 'checkbox',
            label: 'Evidence Available',
            required: true,
            options: ['Written communications', 'Witness statements', 'Financial records', 'Photos/videos', 'Other'],
            help_text: 'Check all types of evidence you have'
          }
        ]
      },
      {
        step_number: 3,
        step_name: 'Relief Sought',
        description: 'What do you want the court to do?',
        questions: [
          {
            id: 'contempt_remedy',
            type: 'textarea',
            label: 'Remedy Requested',
            required: true,
            placeholder: 'What do you want the court to order as punishment or remedy...',
            help_text: 'This could include fines, jail time, or other enforcement measures'
          }
        ]
      }
    ]
  },
  [FORM_TYPES.FL_411]: {
    form_type: FORM_TYPES.FL_411,
    title: 'Contempt Facts (Financial Orders) (FL-411)',
    total_steps: 2,
    steps: [
      {
        step_number: 1,
        step_name: 'Payment History',
        description: 'Document missed or late payments',
        questions: [
          {
            id: 'payment_amount_ordered',
            type: 'currency',
            label: 'Monthly Payment Amount Ordered',
            required: true,
            help_text: 'Enter the monthly amount the court ordered'
          },
          {
            id: 'payments_missed',
            type: 'textarea',
            label: 'Missed Payments',
            required: true,
            placeholder: 'List dates and amounts of missed payments...',
            help_text: 'Be specific about each missed payment with dates and amounts'
          }
        ]
      },
      {
        step_number: 2,
        step_name: 'Total Owed',
        description: 'Calculate the total amount in arrears',
        questions: [
          {
            id: 'total_arrears',
            type: 'currency',
            label: 'Total Amount Owed',
            required: true,
            help_text: 'Total unpaid support including interest and penalties'
          }
        ]
      }
    ]
  },
  [FORM_TYPES.MC_030]: {
    form_type: FORM_TYPES.MC_030,
    title: 'Declaration (MC-030)',
    total_steps: 1,
    steps: [
      {
        step_number: 1,
        step_name: 'Declaration Statement',
        description: 'Provide your sworn statement of facts',
        questions: [
          {
            id: 'declaration_facts',
            type: 'textarea',
            label: 'Declaration of Facts',
            required: true,
            placeholder: 'State the facts you are declaring under penalty of perjury...',
            help_text: 'This is a sworn statement. Only include facts you know to be true.'
          },
          {
            id: 'personal_knowledge',
            type: 'radio',
            label: 'Is this declaration based on your personal knowledge?',
            required: true,
            options: ['Yes', 'No'],
            help_text: 'Personal knowledge means you directly witnessed or experienced these facts'
          }
        ]
      }
    ]
  }
};

export default FORM_TEMPLATES;