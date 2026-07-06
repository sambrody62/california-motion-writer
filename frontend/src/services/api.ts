import axios from 'axios';
import { evalCondition } from '../utils/conditionEval';

// REACT_APP_API_URL (build-time env: Vercel in prod, frontend/.env in dev)
// always wins; the literal fallbacks are Render (prod) and local Docker (dev).
const API_BASE_URL = process.env.REACT_APP_API_URL
  || (process.env.NODE_ENV === 'production'
    ? 'https://california-motion-api.onrender.com/api/v1'
    : 'http://127.0.0.1:8000/api/v1');

const api = axios.create({
  baseURL: API_BASE_URL,
  headers: {
    'Content-Type': 'application/json',
  },
});

// Add auth token to requests if it exists
api.interceptors.request.use((config) => {
  const token = localStorage.getItem('token');
  if (token) {
    config.headers.Authorization = `Bearer ${token}`;
  }
  return config;
});

// Auth endpoints
export const auth = {
  register: async (data: {
    email: string;
    password: string;
    full_name: string;
    phone?: string;
  }) => {
    const response = await api.post('/auth/register', data);
    return response.data;
  },

  login: async (email: string, password: string) => {
    const formData = new FormData();
    formData.append('username', email);
    formData.append('password', password);

    const response = await api.post('/auth/token', formData, {
      headers: { 'Content-Type': 'multipart/form-data' },
    });
    return response.data;
  },

  getProfile: async () => {
    const response = await api.get('/users/me');
    return response.data;
  },
};

// Chat endpoints
export const chat = {
  createSession: async () => {
    const response = await api.post('/chat/sessions', {});
    return response.data;
  },

  getSessions: async () => {
    const response = await api.get('/chat/sessions');
    return response.data;
  },

  getSession: async (sessionId: string) => {
    const response = await api.get(`/chat/sessions/${sessionId}`);
    return response.data;
  },

  sendMessage: async (sessionId: string, message: string) => {
    const response = await api.post('/chat/messages', {
      session_id: sessionId,
      content: message,
    });
    return response.data;
  },

  getMessages: async (sessionId: string) => {
    const response = await api.get(`/chat/sessions/${sessionId}/messages`);
    return response.data;
  },
};

// Profile endpoints
export const profile = {
  create: async (data: any) => {
    const response = await api.post('/profiles', data);
    return response.data;
  },

  get: async () => {
    const response = await api.get('/profiles/me');
    return response.data;
  },

  update: async (data: any) => {
    const response = await api.put('/profiles/me', data);
    return response.data;
  },
};

// Motions endpoints
export const motions = {
  create: async (data: any) => {
    const response = await api.post('/motions', data);
    return response.data;
  },

  list: async () => {
    const response = await api.get('/motions');
    return response.data;
  },

  get: async (id: string) => {
    const response = await api.get(`/motions/${id}`);
    return response.data;
  },

  update: async (id: string, data: any) => {
    const response = await api.put(`/motions/${id}`, data);
    return response.data;
  },
};

// Additional API exports for compatibility
export const motionAPI = {
  ...motions,
  list: motions.list,
  create: motions.create,
  get: motions.get,
  update: motions.update,
  listMotions: motions.list,
  createMotion: motions.create,
  getMotion: motions.get,
  getDrafts: async (motionId: string) => {
    const response = await api.get(`/motions/${motionId}`);
    return response.data.drafts as Array<{
      step_number: number;
      step_name: string;
      question_data: Record<string, unknown>;
      llm_output: string | null;
      is_complete: boolean;
    }>;
  },
  saveDraft: async (motionId: string, payload: {
    step_number: number;
    step_name: string;
    question_data: Record<string, unknown>;
    llm_input?: string;
  }) => {
    const response = await api.post(`/motions/${motionId}/drafts`, {
      step_number: payload.step_number,
      step_name: payload.step_name,
      question_data: payload.question_data,
    });
    return response.data;
  },
  processWithLLM: async (motionId: string) => {
    const response = await api.post('/llm/process-motion', { motion_id: motionId });
    return response.data;
  }
};

export const intakeAPI = {
  getQuestions: async (formType: string, stepNumber?: number) => {
    // Import form templates dynamically to avoid circular dependencies
    const { FORM_TEMPLATES } = await import('../data/formTemplates');

    const template = FORM_TEMPLATES[formType as keyof typeof FORM_TEMPLATES];
    if (!template) {
      throw new Error(`No template found for form type: ${formType}`);
    }

    const step = template.steps.find(s => s.step_number === (stepNumber || 1));
    if (!step) {
      throw new Error(`No step found for step number: ${stepNumber || 1}`);
    }

    return {
      data: {
        id: `${formType}_step_${step.step_number}`,
        step_number: step.step_number,
        step_name: step.step_name,
        description: step.description,
        questions: step.questions,
        total_steps: template.total_steps
      }
    };
  },
  saveAnswer: async (questionId: string, answer: any) => {
    return { success: true };
  },
  evaluateCondition: async (condition: string, context: any) => {
    try {
      return { data: { result: evalCondition(condition, context) } };
    } catch (error) {
      console.error('Error evaluating condition:', condition, error);
      return { data: { result: true } };
    }
  }
};

export const documentAPI = {
  generate: async (motionId: string) => {
    const response = await api.post(`/motions/${motionId}/generate-pdf`);
    return response.data;
  },
  download: async (motionId: string) => {
    const response = await api.get(`/motions/${motionId}/download`, {
      responseType: 'blob'
    });
    return response.data;
  },
  generatePDFSync: async (motionId: string): Promise<ArrayBuffer> => {
    const response = await api.post(
      '/documents/generate-pdf-sync',
      { motion_id: motionId },
      { responseType: 'arraybuffer' }
    );
    return response.data as ArrayBuffer;
  }
};

export const profileAPI = {
  ...profile,
  getProfile: profile.get,
  createProfile: profile.create,
  updateProfile: profile.update
};
export const authAPI = auth;

// Violation intake & filing endpoints
export interface ViolationIntakePayload {
  violationType: string;
  urgency: boolean;
  violationDates: string[];
  violationDescription: string;
  evidence: string[];
  attemptedResolution: boolean;
  resolutionDescription?: string;
  priorViolations: boolean;
  priorViolationsDescription?: string;
  requestedRelief: string[];
}

export const violationAPI = {
  getIntakeQuestions: async () => {
    const response = await api.get('/violations/intake-questions');
    return response.data;
  },

  getTracks: async () => {
    const response = await api.get('/violations/tracks');
    return response.data;
  },

  process: async (payload: ViolationIntakePayload) => {
    const response = await api.post('/violations/process', payload);
    return response.data;
  },

  generateDeclaration: async (payload: ViolationIntakePayload) => {
    const response = await api.post('/violations/generate-declaration', payload);
    return response.data;
  },
};

// Evidence endpoints
export const evidenceAPI = {
  list: async (motionId: string) => {
    const response = await api.get(`/motions/${motionId}/evidence`);
    return response.data;
  },

  create: async (motionId: string, payload: {
    evidence_type: 'text' | 'email' | 'photo' | 'document';
    tags: string[];
    source_date: string | null;
    description: string;
    transcription: string | null;
    user_confirmed: boolean;
  }) => {
    const response = await api.post(`/motions/${motionId}/evidence`, payload);
    return response.data;
  },

  upload: async (motionId: string, file: File, fields: {
    evidence_type: 'photo' | 'document';
    tags: string[];
    source_date: string | null;
    description: string;
    transcription: string;
    user_confirmed: boolean;
  }) => {
    const formData = new FormData();
    formData.append('file', file);
    Object.entries(fields).forEach(([key, value]) => {
      formData.append(key, Array.isArray(value) ? JSON.stringify(value) : String(value));
    });
    const response = await api.post(`/motions/${motionId}/evidence/upload`, formData, {
      headers: { 'Content-Type': 'multipart/form-data' },
    });
    return response.data;
  },

  update: async (id: string, payload: Partial<{
    evidence_type: 'text' | 'email' | 'photo' | 'document';
    tags: string[];
    source_date: string | null;
    description: string;
    transcription: string | null;
    user_confirmed: boolean;
  }>) => {
    const response = await api.put(`/evidence/${id}`, payload);
    return response.data;
  },

  remove: async (id: string) => {
    const response = await api.delete(`/evidence/${id}`);
    return response.data;
  },
};

// Gmail Evidence endpoints (GMAIL_EVIDENCE_ENABLED flag gated on the backend)
export const gmailEvidenceAPI = {
  getAuthUrl: async (): Promise<{ auth_url: string }> => {
    const response = await api.get('/gmail/auth-url');
    return response.data;
  },

  exchangeCode: async (code: string): Promise<{ access_token: string }> => {
    const response = await api.post('/gmail/exchange-code', { code });
    return response.data;
  },

  scan: async (motionId: string, accessToken: string): Promise<{
    emails: Array<{
      message_id: string;
      subject: string;
      from: string;
      date: string;
      snippet: string;
    }>;
  }> => {
    const response = await api.post(`/motions/${motionId}/gmail/scan`, { access_token: accessToken });
    return response.data;
  },

  import: async (motionId: string, accessToken: string, messageIds: string[]): Promise<{ imported: number }> => {
    const response = await api.post(`/motions/${motionId}/gmail/import`, {
      access_token: accessToken,
      message_ids: messageIds,
    });
    return response.data;
  },
};

export default api;
