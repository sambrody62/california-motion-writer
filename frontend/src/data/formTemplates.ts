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
          condition: 'has_children == "Yes"',
          placeholder: 'Describe who the children currently live with and any existing custody orders',
          help_text: 'Include any temporary orders or informal arrangements currently in place'
        },
        {
          id: 'requested_custody',
          type: 'textarea',
          label: 'Requested Custody Arrangement',
          required: true,
          condition: 'has_children == "Yes"',
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

// FL-320: Response to Request for Order
const FL_320_TEMPLATE: FormTemplate = {
  form_type: FORM_TYPES.FL_320,
  title: 'Response to Request for Order (FL-320)',
  total_steps: 4,
  steps: [
    {
      step_number: 1,
      step_name: 'Case Information',
      description: 'Confirm the case information from the original request',
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
        }
      ]
    },
    {
      step_number: 2,
      step_name: 'Response to Requests',
      description: 'Respond to each request made by the other party',
      questions: [
        {
          id: 'agree_child_custody',
          type: 'radio',
          label: 'Do you agree with the requested child custody arrangement?',
          required: true,
          options: ['Agree', 'Disagree', 'Not applicable'],
          help_text: 'Select your position on the custody request'
        },
        {
          id: 'custody_counterproposal',
          type: 'textarea',
          label: 'Your Custody Proposal',
          required: true,
          condition: 'agree_child_custody == "Disagree"',
          placeholder: 'Describe the custody arrangement you believe is appropriate...',
          help_text: 'Provide specific details about your proposed custody and visitation schedule'
        },
        {
          id: 'agree_child_support',
          type: 'radio',
          label: 'Do you agree with the requested child support?',
          required: true,
          options: ['Agree', 'Disagree', 'Not applicable'],
          help_text: 'Select your position on the child support request'
        },
        {
          id: 'support_counterproposal',
          type: 'currency',
          label: 'Your Proposed Child Support Amount',
          required: true,
          condition: 'agree_child_support == "Disagree"',
          help_text: 'Enter the monthly child support amount you believe is appropriate'
        },
        {
          id: 'agree_spousal_support',
          type: 'radio',
          label: 'Do you agree with the requested spousal support?',
          required: true,
          options: ['Agree', 'Disagree', 'Not applicable'],
          help_text: 'Select your position on the spousal support request'
        }
      ]
    },
    {
      step_number: 3,
      step_name: 'Your Counter-Requests',
      description: 'Make any additional requests you want the court to consider',
      questions: [
        {
          id: 'has_counter_requests',
          type: 'radio',
          label: 'Do you have additional requests for the court?',
          required: true,
          options: ['Yes', 'No'],
          help_text: 'Do you want to ask the court for orders beyond responding to the original request?'
        },
        {
          id: 'counter_request_types',
          type: 'checkbox',
          label: 'What additional orders are you requesting?',
          required: true,
          condition: 'has_counter_requests == "Yes"',
          options: [
            'Different child custody arrangement',
            'Different child support amount',
            'Spousal support',
            'Attorney fees and costs',
            'Property orders',
            'Other'
          ]
        },
        {
          id: 'counter_request_details',
          type: 'textarea',
          label: 'Details of Your Additional Requests',
          required: true,
          condition: 'has_counter_requests == "Yes"',
          placeholder: 'Describe the specific orders you are requesting...',
          help_text: 'Be specific about what you want the court to order'
        }
      ]
    },
    {
      step_number: 4,
      step_name: 'Supporting Facts',
      description: 'Provide facts that support your response and any counter-requests',
      questions: [
        {
          id: 'response_facts',
          type: 'textarea',
          label: 'Facts Supporting Your Response',
          required: true,
          placeholder: 'Explain the factual basis for your agreement or disagreement with the original requests...',
          help_text: 'Provide clear, factual information that supports your position'
        },
        {
          id: 'best_interest_response',
          type: 'textarea',
          label: 'Why Your Position is in the Children\'s Best Interest',
          required: true,
          placeholder: 'Explain how your proposed arrangements will benefit the children...',
          help_text: 'Focus on the children\'s safety, stability, and well-being'
        },
        {
          id: 'financial_information',
          type: 'textarea',
          label: 'Financial Information',
          required: false,
          placeholder: 'Provide any relevant financial information...',
          help_text: 'Include income, expenses, or other financial details relevant to support requests'
        }
      ]
    }
  ]
};

// FL-150: Income and Expense Declaration
const FL_150_TEMPLATE: FormTemplate = {
  form_type: FORM_TYPES.FL_150,
  title: 'Income and Expense Declaration (FL-150)',
  total_steps: 5,
  steps: [
    {
      step_number: 1,
      step_name: 'Employment and Income',
      description: 'Provide detailed information about your employment and income sources',
      questions: [
        {
          id: 'employer_name',
          type: 'text',
          label: 'Employer Name',
          required: true,
          placeholder: 'ABC Company Inc.'
        },
        {
          id: 'employer_address',
          type: 'textarea',
          label: 'Employer Address',
          required: true,
          placeholder: '123 Main St, City, State 12345'
        },
        {
          id: 'job_title',
          type: 'text',
          label: 'Job Title/Position',
          required: true,
          placeholder: 'Software Engineer'
        },
        {
          id: 'employment_start_date',
          type: 'date',
          label: 'Employment Start Date',
          required: true
        },
        {
          id: 'gross_monthly_salary',
          type: 'currency',
          label: 'Gross Monthly Salary',
          required: true,
          help_text: 'Before taxes and deductions'
        },
        {
          id: 'overtime_income',
          type: 'currency',
          label: 'Average Monthly Overtime',
          required: false,
          help_text: 'Average overtime pay per month'
        },
        {
          id: 'bonus_income',
          type: 'currency',
          label: 'Annual Bonus (divided by 12)',
          required: false,
          help_text: 'If you receive annual bonuses, divide by 12 for monthly amount'
        }
      ]
    },
    {
      step_number: 2,
      step_name: 'Other Income Sources',
      description: 'List all other sources of income',
      questions: [
        {
          id: 'self_employment_income',
          type: 'currency',
          label: 'Self-Employment Income',
          required: false,
          help_text: 'Monthly net income from self-employment or business'
        },
        {
          id: 'rental_income',
          type: 'currency',
          label: 'Rental Property Income',
          required: false,
          help_text: 'Monthly net income from rental properties'
        },
        {
          id: 'investment_income',
          type: 'currency',
          label: 'Investment Income',
          required: false,
          help_text: 'Monthly income from investments, dividends, interest'
        },
        {
          id: 'unemployment_benefits',
          type: 'currency',
          label: 'Unemployment Benefits',
          required: false,
          help_text: 'Monthly unemployment compensation'
        },
        {
          id: 'social_security',
          type: 'currency',
          label: 'Social Security Benefits',
          required: false,
          help_text: 'Monthly Social Security payments'
        },
        {
          id: 'other_income',
          type: 'currency',
          label: 'Other Income',
          required: false,
          help_text: 'Any other regular monthly income'
        },
        {
          id: 'other_income_description',
          type: 'text',
          label: 'Describe Other Income',
          required: false,
          condition: 'other_income > 0',
          placeholder: 'Describe the source of other income'
        }
      ]
    },
    {
      step_number: 3,
      step_name: 'Monthly Expenses',
      description: 'List your average monthly living expenses',
      questions: [
        {
          id: 'housing_payment',
          type: 'currency',
          label: 'Housing Payment (rent/mortgage)',
          required: true,
          help_text: 'Monthly rent or mortgage payment'
        },
        {
          id: 'property_taxes',
          type: 'currency',
          label: 'Property Taxes',
          required: false,
          help_text: 'Monthly property tax payment'
        },
        {
          id: 'homeowners_insurance',
          type: 'currency',
          label: 'Homeowner\'s/Renter\'s Insurance',
          required: false,
          help_text: 'Monthly insurance payment'
        },
        {
          id: 'utilities',
          type: 'currency',
          label: 'Utilities',
          required: true,
          help_text: 'Gas, electric, water, trash, etc.'
        },
        {
          id: 'food_household',
          type: 'currency',
          label: 'Food and Household Supplies',
          required: true,
          help_text: 'Groceries and household items'
        },
        {
          id: 'childcare',
          type: 'currency',
          label: 'Childcare',
          required: false,
          help_text: 'Daycare, babysitting, after-school care'
        },
        {
          id: 'health_insurance',
          type: 'currency',
          label: 'Health Insurance',
          required: false,
          help_text: 'Monthly health insurance premiums'
        },
        {
          id: 'transportation',
          type: 'currency',
          label: 'Transportation',
          required: true,
          help_text: 'Car payment, gas, maintenance, public transit'
        }
      ]
    },
    {
      step_number: 4,
      step_name: 'Assets and Debts',
      description: 'List your major assets and debts',
      questions: [
        {
          id: 'checking_savings',
          type: 'currency',
          label: 'Cash in Checking/Savings',
          required: true,
          help_text: 'Total cash in all bank accounts'
        },
        {
          id: 'home_value',
          type: 'currency',
          label: 'Home Fair Market Value',
          required: false,
          help_text: 'Current fair market value of your home'
        },
        {
          id: 'mortgage_balance',
          type: 'currency',
          label: 'Mortgage Balance',
          required: false,
          help_text: 'Current balance owed on mortgage'
        },
        {
          id: 'vehicle_value',
          type: 'currency',
          label: 'Vehicle Value',
          required: false,
          help_text: 'Fair market value of vehicles owned'
        },
        {
          id: 'vehicle_loans',
          type: 'currency',
          label: 'Vehicle Loan Balance',
          required: false,
          help_text: 'Amount owed on vehicle loans'
        },
        {
          id: 'credit_card_debt',
          type: 'currency',
          label: 'Credit Card Debt',
          required: false,
          help_text: 'Total balance on all credit cards'
        },
        {
          id: 'retirement_accounts',
          type: 'currency',
          label: 'Retirement Accounts',
          required: false,
          help_text: '401k, IRA, pension values'
        }
      ]
    },
    {
      step_number: 5,
      step_name: 'Additional Information',
      description: 'Provide any additional relevant financial information',
      questions: [
        {
          id: 'income_change_expected',
          type: 'radio',
          label: 'Do you expect your income to change?',
          required: true,
          options: ['Yes', 'No']
        },
        {
          id: 'income_change_details',
          type: 'textarea',
          label: 'Explain Expected Income Change',
          required: true,
          condition: 'income_change_expected == "Yes"',
          placeholder: 'Describe the expected change and when it will occur...',
          help_text: 'Include details about promotions, job loss, retirement, etc.'
        },
        {
          id: 'hardship_circumstances',
          type: 'textarea',
          label: 'Unusual Circumstances',
          required: false,
          placeholder: 'Describe any unusual financial circumstances...',
          help_text: 'Medical expenses, special needs, etc.'
        },
        {
          id: 'attachment_needed',
          type: 'radio',
          label: 'Are you attaching additional documentation?',
          required: true,
          options: ['Yes', 'No'],
          help_text: 'Pay stubs, tax returns, bank statements, etc.'
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