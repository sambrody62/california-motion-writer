import React, { createContext, useContext, useState, useEffect, ReactNode } from 'react';
import { authService, User, AuthResponse } from '../services/auth/auth.service';

interface AuthContextType {
  user: User | null;
  loading: boolean;
  login: (email: string, password: string) => Promise<AuthResponse>;
  register: (email: string, password: string) => Promise<AuthResponse>;
  logout: () => Promise<void>;
}

export const AuthContext = createContext<AuthContextType | undefined>(undefined);

export const useAuth = () => {
  const context = useContext(AuthContext);
  if (!context) {
    throw new Error('useAuth must be used within an AuthProvider');
  }
  return context;
};

interface AuthProviderProps {
  children: ReactNode;
}

export const AuthProvider: React.FC<AuthProviderProps> = ({ children }) => {
  const [user, setUser] = useState<User | null>(null);
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    // Calls back synchronously with the localStorage-restored user, so hard
    // redirects (e.g. the Gmail OAuth callback) don't bounce through /login
    const unsubscribe = authService.onAuthStateChanged((user) => {
      setUser(user);
      setLoading(false);
    });

    return unsubscribe;
  }, []);

  const login = async (email: string, password: string) => {
    const result = await authService.login(email, password);
    if (result.success) {
      setUser(result.user ?? null);
    }
    return result;
  };

  const register = async (email: string, password: string) => {
    const result = await authService.register(email, password);
    if (result.success) {
      setUser(result.user ?? null);
    }
    return result;
  };

  const logout = async () => {
    await authService.logout();
    setUser(null);
  };

  return (
    <AuthContext.Provider value={{ user, loading, login, register, logout }}>
      {children}
    </AuthContext.Provider>
  );
};
