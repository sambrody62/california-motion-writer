/**
 * Tests for featureFlags utility
 */

describe('featureFlags — gmailEnabled', () => {
  const originalEnv = process.env;

  beforeEach(() => {
    jest.resetModules();
    process.env = { ...originalEnv };
  });

  afterEach(() => {
    process.env = originalEnv;
  });

  test('returns false when REACT_APP_GMAIL_ENABLED is not set', async () => {
    delete process.env.REACT_APP_GMAIL_ENABLED;
    const { gmailEnabled } = await import('../featureFlags');
    expect(gmailEnabled()).toBe(false);
  });

  test('returns false when REACT_APP_GMAIL_ENABLED is "false"', async () => {
    process.env.REACT_APP_GMAIL_ENABLED = 'false';
    const { gmailEnabled } = await import('../featureFlags');
    expect(gmailEnabled()).toBe(false);
  });

  test('returns false when REACT_APP_GMAIL_ENABLED is empty string', async () => {
    process.env.REACT_APP_GMAIL_ENABLED = '';
    const { gmailEnabled } = await import('../featureFlags');
    expect(gmailEnabled()).toBe(false);
  });

  test('returns true when REACT_APP_GMAIL_ENABLED is "true"', async () => {
    process.env.REACT_APP_GMAIL_ENABLED = 'true';
    const { gmailEnabled } = await import('../featureFlags');
    expect(gmailEnabled()).toBe(true);
  });

  test('returns false for any value other than "true"', async () => {
    process.env.REACT_APP_GMAIL_ENABLED = '1';
    const { gmailEnabled } = await import('../featureFlags');
    expect(gmailEnabled()).toBe(false);
  });
});
