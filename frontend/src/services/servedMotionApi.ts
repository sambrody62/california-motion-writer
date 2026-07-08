import api from './api';

export interface ServedMotionExtracted {
  case_number?: string;
  petitioner_name?: string;
  hearing_date?: string;
  hearing_time?: string;
  other_party_requests?: string;
  children?: Array<{ name?: string; age?: number | null }>;
}

export interface ServedMotionParseResult {
  success: boolean;
  extracted: ServedMotionExtracted;
  notice: string | null;
}

export const servedMotionAPI = {
  // Returns the unwrapped response body (see lessons.md — helpers never
  // return the axios response itself)
  parse: async (file: File): Promise<ServedMotionParseResult> => {
    const formData = new FormData();
    formData.append('file', file);
    const response = await api.post('/llm/parse-served-motion', formData, {
      headers: { 'Content-Type': 'multipart/form-data' },
    });
    return response.data;
  },
};
