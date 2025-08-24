import axios from 'axios';

const API_BASE_URL = process.env.REACT_APP_API_URL || 'http://localhost:8000/api/v1';

const api = axios.create({
  baseURL: API_BASE_URL,
  headers: {
    'Content-Type': 'application/json',
  },
});

// Add auth token to requests
api.interceptors.request.use((config) => {
  const token = localStorage.getItem('token');
  if (token) {
    config.headers.Authorization = `Bearer ${token}`;
  }
  return config;
});

// Handle token expiration
api.interceptors.response.use(
  (response) => response,
  (error) => {
    if (error.response?.status === 401) {
      localStorage.removeItem('token');
      window.location.href = '/login';
    }
    return Promise.reject(error);
  }
);

// Auth endpoints
export const authAPI = {
  login: (email: string, password: string) =>
    api.post('/auth/login', { email, password }),
  
  register: (email: string, password: string) =>
    api.post('/auth/register', { email, password }),
  
  getCurrentUser: () =>
    api.get('/auth/me'),
};

// Profile endpoints
export const profileAPI = {
  getProfile: () =>
    api.get('/profile'),
  
  updateProfile: (data: any) =>
    api.put('/profile', data),
  
  createProfile: (data: any) =>
    api.post('/profile', data),
};

// Motion endpoints
export const motionAPI = {
  listMotions: () =>
    api.get('/motions'),
  
  getMotion: (id: string) =>
    api.get(`/motions/${id}`),
  
  createMotion: (data: any) =>
    api.post('/motions', data),
  
  updateMotion: (id: string, data: any) =>
    api.put(`/motions/${id}`, data),
  
  deleteMotion: (id: string) =>
    api.delete(`/motions/${id}`),
  
  saveDraft: (motionId: string, stepNumber: number, data: any) =>
    api.post(`/motions/${motionId}/draft`, {
      step_number: stepNumber,
      question_data: data,
    }),
  
  getDrafts: (motionId: string) =>
    api.get(`/motions/${motionId}/drafts`),
  
  processWithLLM: (motionId: string) =>
    api.post(`/motions/${motionId}/process`),
};

// Intake endpoints
export const intakeAPI = {
  getQuestions: (motionType: string, stepNumber: number) =>
    api.get(`/intake/questions/${motionType}/${stepNumber}`),
  
  saveAnswer: (motionId: string, stepNumber: number, answers: any) =>
    api.post(`/intake/save-answer/${motionId}/${stepNumber}`, { answers }),
  
  evaluateCondition: (condition: string, context: any) =>
    api.post('/intake/evaluate-condition', { condition, context }),
};

// Document endpoints
export const documentAPI = {
  generatePDF: (motionId: string, documentType?: string) =>
    api.post('/documents/generate-pdf', {
      motion_id: motionId,
      document_type: documentType,
    }),
  
  generatePDFSync: (motionId: string, documentType?: string) =>
    api.post('/documents/generate-pdf-sync', {
      motion_id: motionId,
      document_type: documentType,
    }, {
      responseType: 'blob',
    }),
  
  downloadDocument: (documentId: string) =>
    api.get(`/documents/${documentId}/download`, {
      responseType: 'blob',
    }),
  
  listMotionDocuments: (motionId: string) =>
    api.get(`/documents/motion/${motionId}/documents`),
};

export default api;