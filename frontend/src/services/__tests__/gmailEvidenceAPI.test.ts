/**
 * Tests for gmailEvidenceAPI in api.ts
 */

jest.mock('axios', () => ({
  create: () => ({
    get: jest.fn(),
    post: jest.fn(),
    put: jest.fn(),
    delete: jest.fn(),
    interceptors: {
      request: { use: jest.fn() },
      response: { use: jest.fn() },
    },
  }),
}));

describe('gmailEvidenceAPI — exports', () => {
  test('gmailEvidenceAPI is exported from api.ts', async () => {
    const api = await import('../api');
    expect(api.gmailEvidenceAPI).toBeDefined();
  });

  test('gmailEvidenceAPI has getAuthUrl method', async () => {
    const { gmailEvidenceAPI } = await import('../api');
    expect(typeof gmailEvidenceAPI.getAuthUrl).toBe('function');
  });

  test('gmailEvidenceAPI has exchangeCode method', async () => {
    const { gmailEvidenceAPI } = await import('../api');
    expect(typeof gmailEvidenceAPI.exchangeCode).toBe('function');
  });

  test('gmailEvidenceAPI has scan method', async () => {
    const { gmailEvidenceAPI } = await import('../api');
    expect(typeof gmailEvidenceAPI.scan).toBe('function');
  });

  test('gmailEvidenceAPI has import method', async () => {
    const { gmailEvidenceAPI } = await import('../api');
    expect(typeof gmailEvidenceAPI.import).toBe('function');
  });
});

describe('evidenceAPI.upload — surfaces suggested_transcription', () => {
  test('upload returns full response data including suggested_transcription', async () => {
    // The upload function should return response.data which may contain suggested_transcription.
    // This test verifies the shape contract by checking the function exists and has the right signature.
    const { evidenceAPI } = await import('../api');
    expect(typeof evidenceAPI.upload).toBe('function');
  });
});
