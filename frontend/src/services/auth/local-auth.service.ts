// Local authentication service for development
// This connects to the backend API for authentication

const API_BASE = process.env.REACT_APP_API_URL || 'http://127.0.0.1:8000/api/v1';

interface User {
  id: string;
  email: string;
  full_name?: string;
  created_at: string;
}

interface AuthResponse {
  success: boolean;
  user?: User;
  token?: string;
  error?: string;
}

export class LocalAuthService {
  private currentUser: User | null = null;
  private token: string | null = null;
  private listeners: Array<(user: User | null) => void> = [];

  constructor() {
    // Check for stored token on initialization
    this.token = localStorage.getItem('token');
    const userStr = localStorage.getItem('user');
    if (userStr) {
      try {
        this.currentUser = JSON.parse(userStr);
      } catch (e) {
        console.error('Failed to parse stored user:', e);
      }
    }
  }

  // Register new user using backend API
  async register(email: string, password: string): Promise<AuthResponse> {
    try {
      const response = await fetch(`${API_BASE}/auth/register`, {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
        },
        body: JSON.stringify({
          email,
          password,
          full_name: email.split('@')[0], // Default name from email
          phone: ''
        }),
      });

      if (!response.ok) {
        const error = await response.json();
        return { success: false, error: error.detail || 'Registration failed' };
      }

      const data = await response.json();
      this.token = data.access_token;

      // After getting token, fetch user data
      if (this.token) {
        localStorage.setItem('token', this.token);

        // Fetch user data using the token
        const userResponse = await fetch(`${API_BASE}/users/me`, {
          headers: {
            'Authorization': `Bearer ${this.token}`
          }
        });

        if (userResponse.ok) {
          this.currentUser = await userResponse.json();
        } else {
          // Create a minimal user object from email
          this.currentUser = {
            id: 'local-user',
            email: email,
            full_name: email.split('@')[0],
            created_at: new Date().toISOString()
          };
        }
        localStorage.setItem('user', JSON.stringify(this.currentUser));
      }

      // Notify listeners
      this.notifyListeners();

      return { success: true, user: this.currentUser || undefined, token: this.token || undefined };
    } catch (error: any) {
      console.error('Registration error:', error);
      return { success: false, error: error.message || 'Network error' };
    }
  }

  // Login user using backend API
  async login(email: string, password: string): Promise<AuthResponse> {
    try {
      // Use FormData for OAuth2 compatible login
      const formData = new FormData();
      formData.append('username', email);
      formData.append('password', password);

      const response = await fetch(`${API_BASE}/auth/token`, {
        method: 'POST',
        body: formData,
      });

      if (!response.ok) {
        const error = await response.json();
        return { success: false, error: error.detail || 'Login failed' };
      }

      const data = await response.json();
      this.token = data.access_token;

      // After getting token, fetch user data
      if (this.token) {
        localStorage.setItem('token', this.token);

        // Fetch user data using the token
        const userResponse = await fetch(`${API_BASE}/users/me`, {
          headers: {
            'Authorization': `Bearer ${this.token}`
          }
        });

        if (userResponse.ok) {
          this.currentUser = await userResponse.json();
          localStorage.setItem('user', JSON.stringify(this.currentUser));
        } else {
          // Create a minimal user object from email
          this.currentUser = {
            id: 'local-user',
            email: email,
            full_name: email.split('@')[0],
            created_at: new Date().toISOString()
          };
          localStorage.setItem('user', JSON.stringify(this.currentUser));
        }
      }

      // Notify listeners
      this.notifyListeners();

      return { success: true, user: this.currentUser || undefined, token: this.token || undefined };
    } catch (error: any) {
      console.error('Login error:', error);
      return { success: false, error: error.message || 'Network error' };
    }
  }

  // Logout user
  async logout(): Promise<{ success: boolean; error?: string }> {
    try {
      // Clear local storage
      localStorage.removeItem('token');
      localStorage.removeItem('user');

      this.currentUser = null;
      this.token = null;

      // Notify listeners
      this.notifyListeners();

      return { success: true };
    } catch (error: any) {
      return { success: false, error: error.message };
    }
  }

  // Get current user
  getCurrentUser(): User | null {
    return this.currentUser;
  }

  // Get current token
  getToken(): string | null {
    return this.token;
  }

  // Listen to auth state changes
  onAuthStateChanged(callback: (user: User | null) => void): () => void {
    this.listeners.push(callback);
    // Call immediately with current state
    callback(this.currentUser);

    // Return unsubscribe function
    return () => {
      this.listeners = this.listeners.filter(l => l !== callback);
    };
  }

  // Notify all listeners of auth state change
  private notifyListeners() {
    this.listeners.forEach(listener => listener(this.currentUser));
  }

  // Check if user is authenticated
  isAuthenticated(): boolean {
    return this.currentUser !== null && this.token !== null;
  }

  // Get user data from backend
  async getUserData(): Promise<any> {
    if (!this.token) {
      return { success: false, error: 'Not authenticated' };
    }

    try {
      const response = await fetch(`${API_BASE}/users/me`, {
        headers: {
          'Authorization': `Bearer ${this.token}`
        }
      });

      if (!response.ok) {
        return { success: false, error: 'Failed to get user data' };
      }

      const data = await response.json();
      return { success: true, data };
    } catch (error: any) {
      return { success: false, error: error.message };
    }
  }

  // Create a mock Firebase User object for compatibility
  createMockFirebaseUser(): any {
    if (!this.currentUser) return null;

    return {
      uid: this.currentUser.id,
      email: this.currentUser.email,
      displayName: this.currentUser.full_name || this.currentUser.email,
      photoURL: null,
      emailVerified: true,
      isAnonymous: false,
      metadata: {
        creationTime: this.currentUser.created_at,
        lastSignInTime: new Date().toISOString()
      },
      providerData: [],
      refreshToken: '',
      tenantId: null,
      delete: async () => {},
      getIdToken: async () => this.token || '',
      getIdTokenResult: async () => ({
        token: this.token || '',
        authTime: new Date().toISOString(),
        issuedAtTime: new Date().toISOString(),
        expirationTime: new Date(Date.now() + 3600000).toISOString(),
        signInProvider: 'password',
        claims: {},
        signInSecondFactor: null
      }),
      reload: async () => {},
      toJSON: () => ({
        uid: this.currentUser?.id,
        email: this.currentUser?.email,
        displayName: this.currentUser?.full_name
      })
    };
  }
}

export const localAuthService = new LocalAuthService();