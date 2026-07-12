import { FORM_METADATA, FormType } from '../../types/forms';
import { Question } from './QuestionField';

export interface IntakeStep {
  step_number: number;
  step_name: string;
  description: string;
  questions: Question[];
  total_steps?: number;
}

export const getFormTitle = (currentFormType: string | undefined): string => {
  if (!currentFormType) return 'Form';
  if (currentFormType === 'RFO') return 'Request for Order (FL-300)';
  if (currentFormType === 'Response') return 'Response to RFO (FL-320)';
  const formMetadata = FORM_METADATA[currentFormType as FormType];
  return formMetadata ? `${formMetadata.name} (${formMetadata.id})` : currentFormType;
};
