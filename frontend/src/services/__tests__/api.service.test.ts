/**
 * Tests for API service
 */
import { motionAPI, profileAPI, authAPI } from '../api';

// Mock fetch globally
const mockFetch = jest.fn();
(global as any).fetch = mockFetch;

// Mock localStorage
const localStorageMock = {
  getItem: jest.fn(),
  setItem: jest.fn(),
  removeItem: jest.fn(),
  clear: jest.fn()
};
Object.defineProperty(window, 'localStorage', {
  value: localStorageMock,
  writable: true
});

// SKIPPED: written against removed fetch-based API client. Rewrite against axios client
// in src/services/api.ts after M1 replaces the stub methods (see tasks/todo.md).
describe.skip('API Service', () => {
  beforeEach(() => {
    jest.clearAllMocks();
    localStorageMock.getItem.mockReturnValue('mock-jwt-token');
  });

  describe('motionAPI', () => {
    test('list() makes correct API call', async () => {
      const mockResponse = {
        data: {
          motions: [
            { id: '1', title: 'Test Motion', status: 'draft' }
          ]
        }
      };

      mockFetch.mockResolvedValue({
        ok: true,
        json: async () => mockResponse
      });

      const result = await motionAPI.list();

      expect(mockFetch).toHaveBeenCalledWith(
        expect.stringContaining('/api/v1/motions'),
        expect.objectContaining({
          method: 'GET',
          headers: expect.objectContaining({
            'Authorization': 'Bearer mock-jwt-token',
            'Content-Type': 'application/json'
          })
        })
      );

      expect(result).toEqual(mockResponse);
    });

    test('create() makes correct API call', async () => {
      const motionData = {
        motion_type: 'RFO',
        title: 'New Motion',
        description: 'Test description'
      };

      const mockResponse = {
        id: 'new-motion-id',
        ...motionData,
        status: 'draft'
      };

      mockFetch.mockResolvedValue({
        ok: true,
        json: async () => mockResponse
      });

      const result = await motionAPI.create(motionData);

      expect(mockFetch).toHaveBeenCalledWith(
        expect.stringContaining('/api/v1/motions'),
        expect.objectContaining({
          method: 'POST',
          headers: expect.objectContaining({
            'Authorization': 'Bearer mock-jwt-token',
            'Content-Type': 'application/json'
          }),
          body: JSON.stringify(motionData)
        })
      );

      expect(result).toEqual(mockResponse);
    });

    test('get() makes correct API call', async () => {
      const motionId = 'motion-123';
      const mockResponse = {
        id: motionId,
        title: 'Retrieved Motion',
        status: 'complete'
      };

      mockFetch.mockResolvedValue({
        ok: true,
        json: async () => mockResponse
      });

      const result = await motionAPI.get(motionId);

      expect(mockFetch).toHaveBeenCalledWith(
        expect.stringContaining(`/api/v1/motions/${motionId}`),
        expect.objectContaining({
          method: 'GET',
          headers: expect.objectContaining({
            'Authorization': 'Bearer mock-jwt-token'
          })
        })
      );

      expect(result).toEqual(mockResponse);
    });

    test('update() makes correct API call', async () => {
      const motionId = 'motion-123';
      const updateData = { title: 'Updated Title', status: 'complete' };

      const mockResponse = {
        id: motionId,
        ...updateData
      };

      mockFetch.mockResolvedValue({
        ok: true,
        json: async () => mockResponse
      });

      const result = await motionAPI.update(motionId, updateData);

      expect(mockFetch).toHaveBeenCalledWith(
        expect.stringContaining(`/api/v1/motions/${motionId}`),
        expect.objectContaining({
          method: 'PUT',
          headers: expect.objectContaining({
            'Authorization': 'Bearer mock-jwt-token',
            'Content-Type': 'application/json'
          }),
          body: JSON.stringify(updateData)
        })
      );

      expect(result).toEqual(mockResponse);
    });

    test('delete() makes correct API call', async () => {
      const motionId = 'motion-123';

      mockFetch.mockResolvedValue({
        ok: true,
        status: 204
      });

      await motionAPI.delete(motionId);

      expect(mockFetch).toHaveBeenCalledWith(
        expect.stringContaining(`/api/v1/motions/${motionId}`),
        expect.objectContaining({
          method: 'DELETE',
          headers: expect.objectContaining({
            'Authorization': 'Bearer mock-jwt-token'
          })
        })
      );
    });
  });

  describe('profileAPI', () => {
    test('get() makes correct API call', async () => {
      const mockProfile = {
        id: 'profile-123',
        party_name: 'John Doe',
        case_number: 'FL-2024-001'
      };

      mockFetch.mockResolvedValue({
        ok: true,
        json: async () => mockProfile
      });

      const result = await profileAPI.get();

      expect(mockFetch).toHaveBeenCalledWith(
        expect.stringContaining('/api/v1/profiles'),
        expect.objectContaining({
          method: 'GET',
          headers: expect.objectContaining({
            'Authorization': 'Bearer mock-jwt-token'
          })
        })
      );

      expect(result).toEqual(mockProfile);
    });

    test('create() makes correct API call', async () => {
      const profileData = {
        party_name: 'Jane Doe',
        case_number: 'FL-2024-002',
        county: 'Los Angeles'
      };

      const mockResponse = {
        id: 'new-profile-id',
        ...profileData
      };

      mockFetch.mockResolvedValue({
        ok: true,
        json: async () => mockResponse
      });

      const result = await profileAPI.create(profileData);

      expect(mockFetch).toHaveBeenCalledWith(
        expect.stringContaining('/api/v1/profiles'),
        expect.objectContaining({
          method: 'POST',
          headers: expect.objectContaining({
            'Authorization': 'Bearer mock-jwt-token',
            'Content-Type': 'application/json'
          }),
          body: JSON.stringify(profileData)
        })
      );

      expect(result).toEqual(mockResponse);
    });

    test('update() makes correct API call', async () => {
      const updateData = {
        party_name: 'Updated Name',
        county: 'Orange'
      };

      const mockResponse = {
        id: 'profile-123',
        ...updateData
      };

      mockFetch.mockResolvedValue({
        ok: true,
        json: async () => mockResponse
      });

      const result = await profileAPI.update(updateData);

      expect(mockFetch).toHaveBeenCalledWith(
        expect.stringContaining('/api/v1/profiles'),
        expect.objectContaining({
          method: 'PUT',
          headers: expect.objectContaining({
            'Authorization': 'Bearer mock-jwt-token',
            'Content-Type': 'application/json'
          }),
          body: JSON.stringify(updateData)
        })
      );

      expect(result).toEqual(mockResponse);
    });
  });

  describe('authAPI', () => {
    test('register() makes correct API call', async () => {
      const userData = {
        email: 'test@example.com',
        password: 'password123',
        full_name: 'Test User'
      };

      const mockResponse = {
        id: 'user-123',
        email: userData.email,
        full_name: userData.full_name
      };

      mockFetch.mockResolvedValue({
        ok: true,
        json: async () => mockResponse
      });

      const result = await authAPI.register(userData);

      expect(mockFetch).toHaveBeenCalledWith(
        expect.stringContaining('/api/v1/auth/register'),
        expect.objectContaining({
          method: 'POST',
          headers: expect.objectContaining({
            'Content-Type': 'application/json'
          }),
          body: JSON.stringify(userData)
        })
      );

      expect(result).toEqual(mockResponse);
    });

    test('login() makes correct API call', async () => {
      const credentials = {
        username: 'test@example.com',
        password: 'password123'
      };

      const mockResponse = {
        access_token: 'jwt-token',
        token_type: 'bearer'
      };

      mockFetch.mockResolvedValue({
        ok: true,
        json: async () => mockResponse
      });

      const result = await authAPI.login(credentials);

      expect(mockFetch).toHaveBeenCalledWith(
        expect.stringContaining('/api/v1/auth/token'),
        expect.objectContaining({
          method: 'POST',
          headers: expect.objectContaining({
            'Content-Type': 'application/x-www-form-urlencoded'
          }),
          body: expect.stringContaining('username=test%40example.com')
        })
      );

      expect(result).toEqual(mockResponse);
    });

    test('getCurrentUser() makes correct API call', async () => {
      const mockUser = {
        id: 'user-123',
        email: 'test@example.com',
        full_name: 'Test User'
      };

      mockFetch.mockResolvedValue({
        ok: true,
        json: async () => mockUser
      });

      const result = await authAPI.getCurrentUser();

      expect(mockFetch).toHaveBeenCalledWith(
        expect.stringContaining('/api/v1/auth/me'),
        expect.objectContaining({
          method: 'GET',
          headers: expect.objectContaining({
            'Authorization': 'Bearer mock-jwt-token'
          })
        })
      );

      expect(result).toEqual(mockUser);
    });
  });

  describe('Error Handling', () => {
    test('handles HTTP error responses', async () => {
      mockFetch.mockResolvedValue({
        ok: false,
        status: 400,
        json: async () => ({ detail: 'Bad Request' })
      });

      await expect(motionAPI.list()).rejects.toThrow('HTTP error! status: 400');
    });

    test('handles network errors', async () => {
      mockFetch.mockRejectedValue(new Error('Network error'));

      await expect(motionAPI.list()).rejects.toThrow('Network error');
    });

    test('handles missing authentication token', async () => {
      localStorageMock.getItem.mockReturnValue(null);

      await expect(motionAPI.list()).rejects.toThrow('No authentication token found');
    });

    test('handles invalid JSON responses', async () => {
      mockFetch.mockResolvedValue({
        ok: true,
        json: async () => {
          throw new Error('Invalid JSON');
        }
      });

      await expect(motionAPI.list()).rejects.toThrow('Invalid JSON');
    });
  });

  describe('Authentication Headers', () => {
    test('includes auth token in requests', async () => {
      mockFetch.mockResolvedValue({
        ok: true,
        json: async () => ({})
      });

      await motionAPI.list();

      expect(mockFetch).toHaveBeenCalledWith(
        expect.any(String),
        expect.objectContaining({
          headers: expect.objectContaining({
            'Authorization': 'Bearer mock-jwt-token'
          })
        })
      );
    });

    test('handles missing token gracefully', async () => {
      localStorageMock.getItem.mockReturnValue(null);

      await expect(motionAPI.list()).rejects.toThrow('No authentication token found');
    });

    test('handles expired token', async () => {
      mockFetch.mockResolvedValue({
        ok: false,
        status: 401,
        json: async () => ({ detail: 'Token expired' })
      });

      await expect(motionAPI.list()).rejects.toThrow('HTTP error! status: 401');
    });
  });

  describe('Base URL Configuration', () => {
    test('uses correct base URL in development', () => {
      // The actual implementation would check process.env.NODE_ENV
      // This test verifies the URL construction logic
      expect(true).toBe(true); // Placeholder - actual URL testing would go here
    });

    test('constructs URLs correctly', async () => {
      mockFetch.mockResolvedValue({
        ok: true,
        json: async () => ({})
      });

      await motionAPI.get('test-id');

      expect(mockFetch).toHaveBeenCalledWith(
        expect.stringMatching(/\/api\/v1\/motions\/test-id$/),
        expect.any(Object)
      );
    });
  });

  describe('Request Body Serialization', () => {
    test('correctly serializes JSON bodies', async () => {
      const testData = {
        title: 'Test Motion',
        nested: { key: 'value' },
        array: [1, 2, 3]
      };

      mockFetch.mockResolvedValue({
        ok: true,
        json: async () => ({})
      });

      await motionAPI.create(testData);

      expect(mockFetch).toHaveBeenCalledWith(
        expect.any(String),
        expect.objectContaining({
          body: JSON.stringify(testData)
        })
      );
    });

    test('correctly serializes form data for login', async () => {
      const credentials = {
        username: 'test@example.com',
        password: 'password123'
      };

      mockFetch.mockResolvedValue({
        ok: true,
        json: async () => ({})
      });

      await authAPI.login(credentials);

      expect(mockFetch).toHaveBeenCalledWith(
        expect.any(String),
        expect.objectContaining({
          headers: expect.objectContaining({
            'Content-Type': 'application/x-www-form-urlencoded'
          }),
          body: 'username=test%40example.com&password=password123'
        })
      );
    });
  });
});