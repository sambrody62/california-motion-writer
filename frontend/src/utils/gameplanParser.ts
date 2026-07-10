import { FormType } from '../types/forms';

export interface GameplanData {
  analysis: string;
  legalStrategy: string;
  recommendedForms: FormType[];
  timeline: string;
  keyConsiderations: string[];
  nextSteps: string[];
}

export interface ParsedGameplan {
  data: GameplanData;
  // True when nothing case-specific could be extracted — the caller must
  // present the generic checklist honestly, not as a personalized plan
  isFallback: boolean;
}

const FORM_CODES = ['FL-300', 'FL-320', 'D-046', 'FL-305', 'FL-150', 'FL-335', 'FL-410', 'FL-411', 'MC-030'];

const GENERIC_FALLBACK: Omit<GameplanData, 'recommendedForms'> = {
  analysis: "We couldn't analyze your specific situation — the checklist below is general guidance.",
  legalStrategy:
    'Review the California courts self-help resources for your case type, and consider speaking with your county family law facilitator (a free service).',
  timeline: 'File as soon as your forms are complete — hearing dates depend on your court.',
  keyConsiderations: [
    'Court forms must be complete and accurate before filing',
    'Keep copies of everything you file and receive',
  ],
  nextSteps: [
    'Consult with a legal professional or your county family law facilitator',
    'Gather required documentation',
    'File forms within any applicable deadline',
  ],
};

export const extractResponseText = (messageResponse: any): string => {
  if (typeof messageResponse === 'string') return messageResponse;
  // Real POST /chat/messages shape: {response: {message: {content}}}
  if (typeof messageResponse?.response?.message?.content === 'string') {
    return messageResponse.response.message.content;
  }
  if (messageResponse?.response) {
    return typeof messageResponse.response === 'string'
      ? messageResponse.response
      : messageResponse.response.response || JSON.stringify(messageResponse.response);
  }
  if (messageResponse?.data) {
    return typeof messageResponse.data === 'string'
      ? messageResponse.data
      : messageResponse.data.response || JSON.stringify(messageResponse.data);
  }
  return JSON.stringify(messageResponse);
};

export const parseLLMResponse = (response: string): ParsedGameplan => {
  const recommendedForms = FORM_CODES.filter((code) =>
    response.toUpperCase().includes(code)
  ) as FormType[];
  const formsDetected = recommendedForms.length > 0;
  if (!formsDetected) {
    recommendedForms.push('FL-300' as FormType);
  }

  const analysis = extractSection(response, ['analysis', 'situation', 'case analysis']);
  const legalStrategy = extractSection(response, ['strategy', 'legal strategy', 'approach']);
  const timeline = extractSection(response, ['timeline', 'timeframe', 'schedule']);
  const keyConsiderations = extractListItems(response, ['considerations', 'challenges', 'important']);
  const nextSteps = extractListItems(response, ['next steps', 'actions', 'steps']);

  const isFallback =
    !analysis && !legalStrategy && keyConsiderations.length === 0 && nextSteps.length === 0;

  return {
    isFallback,
    data: {
      analysis: analysis || GENERIC_FALLBACK.analysis,
      legalStrategy: legalStrategy || GENERIC_FALLBACK.legalStrategy,
      recommendedForms,
      timeline: timeline || GENERIC_FALLBACK.timeline,
      keyConsiderations:
        keyConsiderations.length > 0 ? keyConsiderations : GENERIC_FALLBACK.keyConsiderations,
      nextSteps: nextSteps.length > 0 ? nextSteps : GENERIC_FALLBACK.nextSteps,
    },
  };
};

const extractSection = (text: string, keywords: string[]): string | null => {
  const lines = text.split('\n');
  for (let i = 0; i < lines.length; i++) {
    const line = lines[i].toLowerCase();
    if (keywords.some((keyword) => line.includes(keyword))) {
      // Look for content in next few lines
      for (let j = i + 1; j < Math.min(i + 5, lines.length); j++) {
        const nextLine = lines[j].trim();
        if (nextLine && !nextLine.match(/^\d+\./) && nextLine.length > 20) {
          return nextLine;
        }
      }
    }
  }
  return null;
};

const extractListItems = (text: string, keywords: string[]): string[] => {
  const items: string[] = [];
  const lines = text.split('\n');

  for (let i = 0; i < lines.length; i++) {
    const line = lines[i].toLowerCase();
    if (keywords.some((keyword) => line.includes(keyword))) {
      // Look for list items in next lines
      for (let j = i + 1; j < Math.min(i + 10, lines.length); j++) {
        const nextLine = lines[j].trim();
        if (nextLine.match(/^[-*•]\s/) || nextLine.match(/^\d+\.\s/)) {
          items.push(nextLine.replace(/^[-*•]\s/, '').replace(/^\d+\.\s/, ''));
        }
      }
      break;
    }
  }

  return items;
};

export const detectsEnforcementIntent = (text: string): boolean => {
  const lower = text.toLowerCase();
  const keywords = ['violation', 'violat', 'enforce', 'contempt', 'not following', 'disobeying', 'not comply', 'non-compliance'];
  return keywords.some((kw) => lower.includes(kw));
};
