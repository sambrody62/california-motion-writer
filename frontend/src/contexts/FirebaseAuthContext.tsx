import React, { createContext, useContext, useState, useEffect, ReactNode } from 'react';
import { User } from 'firebase/auth';
import { firebaseAuthService } from '../services/firebase/auth.service';

interface FirebaseAuthContextType {
  user: User | null;
  loading: boolean;
  login: (email: string, password: string) => Promise<any>;
  register: (email: string, password: string) => Promise<any>;
  logout: () => Promise<void>;
}

const FirebaseAuthContext = createContext<FirebaseAuthContextType | undefined>(undefined);

export const useFirebaseAuth = () => {
  const context = useContext(FirebaseAuthContext);
  if (!context) {
    throw new Error('useFirebaseAuth must be used within a FirebaseAuthProvider');
  }
  return context;
};

interface FirebaseAuthProviderProps {
  children: ReactNode;
}

export const FirebaseAuthProvider: React.FC<FirebaseAuthProviderProps> = ({ children }) => {
  const [user, setUser] = useState<User | null>(null);
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    const unsubscribe = firebaseAuthService.onAuthStateChanged((user) => {
      setUser(user);
      setLoading(false);
    });

    return unsubscribe;
  }, []);

  const login = async (email: string, password: string) => {
    const result = await firebaseAuthService.login(email, password);
    if (result.success) {
      setUser(result.user!);
    }
    return result;
  };

  const register = async (email: string, password: string) => {
    const result = await firebaseAuthService.register(email, password);
    if (result.success) {
      setUser(result.user!);
    }
    return result;
  };

  const logout = async () => {
    await firebaseAuthService.logout();
    setUser(null);
  };

  return (
    <FirebaseAuthContext.Provider value={{ user, loading, login, register, logout }}>
      {children}
    </FirebaseAuthContext.Provider>
  );
};