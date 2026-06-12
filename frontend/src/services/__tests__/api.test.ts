import { auth, motions, profile } from '../api';

// Mock fetch globally
global.fetch = jest.fn();

// SKIPPED: written against removed fetch-based API client. Rewrite against axios client
// in src/services/api.ts after M1 replaces the stub methods (see tasks/todo.md).
describe.skip('API Service Tests', () => {
  beforeEach(() => {
    // Clear all mocks before each test
    jest.clearAllMocks();
    // Clear localStorage
    localStorage.clear();
  });

  describe('Authentication API', () => {
    test('register sends correct request', async () => {
      const mockResponse = {
        user: { id: '123', email: 'test@example.com' },
        access_token: 'mock-token'
      };

      (global.fetch as jest.Mock).mockResolvedValueOnce({
        ok: true,
        json: async () => ({ data: mockResponse })
      });

      const userData = {
        email: 'test@example.com',
        password: 'password123',
        full_name: 'Test User',
        phone: '555-1234'
      };

      await auth.register(userData);

      expect(global.fetch).toHaveBeenCalledWith(
        expect.stringContaining('/auth/register'),
        expect.objectContaining({
          method: 'POST',
          headers: expect.objectContaining({
            'Content-Type': 'application/json'
          }),
          body: JSON.stringify(userData)
        })
      );
    });

    test('login sends form data', async () => {
      const mockResponse = {
        access_token: 'mock-token',
        token_type: 'bearer',
        user: { id: '123', email: 'test@example.com' }
      };

      (global.fetch as jest.Mock).mockResolvedValueOnce({
        ok: true,
        json: async () => ({ data: mockResponse })
      });

      await auth.login('test@example.com', 'password123');

      expect(global.fetch).toHaveBeenCalledWith(
        expect.stringContaining('/auth/login'),
        expect.objectContaining({
          method: 'POST',
          headers: expect.objectContaining({
            'Content-Type': 'multipart/form-data'
          })
        })
      );
    });

    test('getProfile includes auth header', async () => {
      localStorage.setItem('token', 'test-token');

      (global.fetch as jest.Mock).mockResolvedValueOnce({
        ok: true,
        json: async () => ({ data: { id: '123', email: 'test@example.com' } })
      });

      await auth.getProfile();

      expect(global.fetch).toHaveBeenCalledWith(
        expect.stringContaining('/users/me'),
        expect.objectContaining({
          headers: expect.objectContaining({
            'Authorization': 'Bearer test-token'
          })
        })
      );
    });
  });

  describe('Motions API', () => {
    beforeEach(() => {
      localStorage.setItem('token', 'test-token');
    });

    test('create motion sends correct data', async () => {
      const mockMotion = {
        id: '456',
        motion_type: 'RFO',
        title: 'Test Motion'
      };

      (global.fetch as jest.Mock).mockResolvedValueOnce({
        ok: true,
        json: async () => ({ data: mockMotion })
      });

      const motionData = {
        motion_type: 'RFO',
        title: 'Test Motion',
        description: 'Test description'
      };

      await motions.create(motionData);

      expect(global.fetch).toHaveBeenCalledWith(
        expect.stringContaining('/motions'),
        expect.objectContaining({
          method: 'POST',
          headers: expect.objectContaining({
            'Authorization': 'Bearer test-token',
            'Content-Type': 'application/json'
          }),
          body: JSON.stringify(motionData)
        })
      );
    });

    test('list motions fetches all user motions', async () => {
      const mockMotions = [
        { id: '1', title: 'Motion 1' },
        { id: '2', title: 'Motion 2' }
      ];

      (global.fetch as jest.Mock).mockResolvedValueOnce({
        ok: true,
        json: async () => ({ data: mockMotions })
      });

      const result = await motions.list();

      expect(global.fetch).toHaveBeenCalledWith(
        expect.stringContaining('/motions'),
        expect.objectContaining({
          method: 'GET',
          headers: expect.objectContaining({
            'Authorization': 'Bearer test-token'
          })
        })
      );

      expect(result.data).toEqual(mockMotions);
    });

    test('get motion by id', async () => {
      const mockMotion = { id: '123', title: 'Test Motion' };

      (global.fetch as jest.Mock).mockResolvedValueOnce({
        ok: true,
        json: async () => ({ data: mockMotion })
      });

      await motions.get('123');

      expect(global.fetch).toHaveBeenCalledWith(
        expect.stringContaining('/motions/123'),
        expect.anything()
      );
    });

    test('update motion sends PUT request', async () => {
      const updateData = { title: 'Updated Title' };

      (global.fetch as jest.Mock).mockResolvedValueOnce({
        ok: true,
        json: async () => ({ data: { id: '123', ...updateData } })
      });

      await motions.update('123', updateData);

      expect(global.fetch).toHaveBeenCalledWith(
        expect.stringContaining('/motions/123'),
        expect.objectContaining({
          method: 'PUT',
          body: JSON.stringify(updateData)
        })
      );
    });
  });

  describe('Profile API', () => {
    beforeEach(() => {
      localStorage.setItem('token', 'test-token');
    });

    test('create profile', async () => {
      const profileData = {
        case_number: 'FL-2024-001',
        county: 'Los Angeles',
        party_name: 'Test User'
      };

      (global.fetch as jest.Mock).mockResolvedValueOnce({
        ok: true,
        json: async () => ({ data: { id: '789', ...profileData } })
      });

      await profile.create(profileData);

      expect(global.fetch).toHaveBeenCalledWith(
        expect.stringContaining('/profiles'),
        expect.objectContaining({
          method: 'POST',
          body: JSON.stringify(profileData)
        })
      );
    });

    test('get profile', async () => {
      const mockProfile = {
        id: '789',
        case_number: 'FL-2024-001',
        county: 'Los Angeles'
      };

      (global.fetch as jest.Mock).mockResolvedValueOnce({
        ok: true,
        json: async () => ({ data: mockProfile })
      });

      const result = await profile.get();

      expect(global.fetch).toHaveBeenCalledWith(
        expect.stringContaining('/profiles/me'),
        expect.objectContaining({
          headers: expect.objectContaining({
            'Authorization': 'Bearer test-token'
          })
        })
      );

      expect(result.data).toEqual(mockProfile);
    });

    test('update profile', async () => {
      const updateData = { case_number: 'FL-2024-002' };

      (global.fetch as jest.Mock).mockResolvedValueOnce({
        ok: true,
        json: async () => ({ data: { id: '789', ...updateData } })
      });

      await profile.update(updateData);

      expect(global.fetch).toHaveBeenCalledWith(
        expect.stringContaining('/profiles/me'),
        expect.objectContaining({
          method: 'PUT',
          body: JSON.stringify(updateData)
        })
      );
    });
  });

  describe('Error Handling', () => {
    test('handles network errors', async () => {
      (global.fetch as jest.Mock).mockRejectedValueOnce(new Error('Network error'));

      await expect(auth.getProfile()).rejects.toThrow('Network error');
    });

    test('handles 401 unauthorized', async () => {
      (global.fetch as jest.Mock).mockResolvedValueOnce({
        ok: false,
        status: 401,
        json: async () => ({ detail: 'Unauthorized' })
      });

      try {
        await auth.getProfile();
        fail('Should have thrown an error');
      } catch (error: any) {
        expect(error.message).toContain('Unauthorized');
      }
    });

    test('handles 404 not found', async () => {
      (global.fetch as jest.Mock).mockResolvedValueOnce({
        ok: false,
        status: 404,
        json: async () => ({ detail: 'Not found' })
      });

      try {
        await motions.get('nonexistent');
        fail('Should have thrown an error');
      } catch (error: any) {
        expect(error.message).toContain('Not found');
      }
    });
  });

  describe('Token Management', () => {
    test('adds token to requests when available', async () => {
      localStorage.setItem('token', 'auth-token-123');

      (global.fetch as jest.Mock).mockResolvedValueOnce({
        ok: true,
        json: async () => ({ data: [] })
      });

      await motions.list();

      expect(global.fetch).toHaveBeenCalledWith(
        expect.any(String),
        expect.objectContaining({
          headers: expect.objectContaining({
            'Authorization': 'Bearer auth-token-123'
          })
        })
      );
    });

    test('does not add token header when not available', async () => {
      localStorage.removeItem('token');

      (global.fetch as jest.Mock).mockResolvedValueOnce({
        ok: true,
        json: async () => ({ data: {} })
      });

      await auth.register({
        email: 'test@example.com',
        password: 'pass123',
        full_name: 'Test',
        phone: '555-1234'
      });

      const callHeaders = (global.fetch as jest.Mock).mock.calls[0][1].headers;
      expect(callHeaders.Authorization).toBeUndefined();
    });
  });
});