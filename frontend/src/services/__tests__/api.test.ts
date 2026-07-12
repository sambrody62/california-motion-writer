/**
 * Tests for API service — axios-based implementation
 */
import mockAxios from '../../__mocks__/axios';
import { auth, motionAPI, documentAPI, motions, profile } from '../api';

beforeEach(() => {
  jest.clearAllMocks();
  localStorage.clear();
});

describe('auth.login', () => {
  test('posts to /auth/token with multipart form data', async () => {
    mockAxios.post.mockResolvedValueOnce({ data: { access_token: 'tok', token_type: 'bearer' } });

    await auth.login('user@example.com', 'secret');

    expect(mockAxios.post).toHaveBeenCalledWith(
      '/auth/token',
      expect.any(FormData),
      expect.objectContaining({ headers: { 'Content-Type': 'multipart/form-data' } })
    );
  });

  test('returns response data', async () => {
    const payload = { access_token: 'tok', token_type: 'bearer' };
    mockAxios.post.mockResolvedValueOnce({ data: payload });

    const result = await auth.login('user@example.com', 'secret');
    expect(result).toEqual(payload);
  });
});

// Collection endpoints are mounted at "/" under their router prefixes, so the
// canonical paths carry a trailing slash. Without it every call takes a 307
// redirect, and redirected cross-origin POSTs can drop Authorization.
describe('collection endpoints use canonical trailing-slash paths', () => {
  test('motions.create POSTs to /motions/', async () => {
    mockAxios.post.mockResolvedValueOnce({ data: { id: 'motion-1' } });

    await motions.create({ motion_type: 'RFO' });

    expect(mockAxios.post).toHaveBeenCalledWith('/motions/', { motion_type: 'RFO' });
  });

  test('motions.list GETs /motions/', async () => {
    mockAxios.get.mockResolvedValueOnce({ data: [] });

    await motions.list();

    expect(mockAxios.get).toHaveBeenCalledWith('/motions/');
  });

  test('profile.create POSTs to /profiles/', async () => {
    mockAxios.post.mockResolvedValueOnce({ data: { id: 'profile-1' } });

    await profile.create({ county: 'San Diego' });

    expect(mockAxios.post).toHaveBeenCalledWith('/profiles/', { county: 'San Diego' });
  });
});

describe('motionAPI.getDrafts', () => {
  test('GETs /motions/:id and returns drafts array', async () => {
    const drafts = [
      { step_number: 1, step_name: 'Facts', question_data: {}, llm_output: 'text', is_complete: true },
    ];
    mockAxios.get.mockResolvedValueOnce({ data: { id: 'motion-1', drafts } });

    const result = await motionAPI.getDrafts('motion-1');

    expect(mockAxios.get).toHaveBeenCalledWith('/motions/motion-1');
    expect(result).toEqual(drafts);
  });
});

describe('motionAPI.saveDraft', () => {
  test('POSTs to /motions/:id/drafts with correct body', async () => {
    mockAxios.post.mockResolvedValueOnce({ data: { message: 'Draft saved successfully', step_number: 2, question_data: {} } });

    const payload = { step_number: 2, step_name: 'Relief', question_data: { custody: 'joint' }, llm_input: 'extra' };
    await motionAPI.saveDraft('motion-1', payload);

    expect(mockAxios.post).toHaveBeenCalledWith('/motions/motion-1/drafts', {
      step_number: 2,
      step_name: 'Relief',
      question_data: { custody: 'joint' },
    });
  });

  test('returns response data', async () => {
    const serverResponse = { message: 'Draft saved successfully', step_number: 1, question_data: {} };
    mockAxios.post.mockResolvedValueOnce({ data: serverResponse });

    const result = await motionAPI.saveDraft('motion-1', {
      step_number: 1,
      step_name: 'Facts',
      question_data: {},
    });
    expect(result).toEqual(serverResponse);
  });
});

describe('documentAPI.generatePDFSync', () => {
  test('POSTs to /documents/generate-pdf-sync with motion_id and arraybuffer responseType', async () => {
    const buffer = new ArrayBuffer(8);
    mockAxios.post.mockResolvedValueOnce({ data: buffer });

    const result = await documentAPI.generatePDFSync('motion-2');

    expect(mockAxios.post).toHaveBeenCalledWith(
      '/documents/generate-pdf-sync',
      { motion_id: 'motion-2' },
      { responseType: 'arraybuffer' }
    );
    expect(result).toBe(buffer);
  });
});
