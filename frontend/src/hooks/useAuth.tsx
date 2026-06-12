import { useContext } from 'react';
import { FirebaseAuthContext } from '../contexts/FirebaseAuthContext';

export const useAuth = () => {
  const context = useContext(FirebaseAuthContext);

  if (!context) {
    throw new Error('useAuth must be used within a FirebaseAuthProvider');
  }

  // Extract token from the Firebase user
  const getToken = async () => {
    if (context.user) {
      return await context.user.getIdToken();
    }
    return null;
  };

  return {
    user: context.user,
    loading: context.loading,
    signIn: context.login,
    signUp: context.register,
    signOut: context.logout,
    token: null, // Use getToken() method for async token retrieval
    getToken
  };
};