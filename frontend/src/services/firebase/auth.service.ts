import { localAuthService } from '../auth/local-auth.service';
import {
  createUserWithEmailAndPassword,
  signInWithEmailAndPassword,
  signOut,
  onAuthStateChanged,
  User
} from 'firebase/auth';
import { auth, db } from '../../config/firebase';
import { doc, setDoc, getDoc } from 'firebase/firestore';

// Conditional logic for Firebase vs Local auth
const USE_LOCAL_AUTH = process.env.REACT_APP_USE_LOCAL_AUTH === 'true' ||
                       process.env.NODE_ENV === 'development';

export class FirebaseAuthService {
  // Register new user
  async register(email: string, password: string) {
    // Use local auth for development
    if (USE_LOCAL_AUTH) {
      const result = await localAuthService.register(email, password);
      if (result.success) {
        return { success: true, user: localAuthService.createMockFirebaseUser() };
      }
      return result;
    }

    // Original Firebase implementation
    try {
      const userCredential = await createUserWithEmailAndPassword(auth, email, password);
      const user = userCredential.user;
      
      // Create user document in Firestore
      await setDoc(doc(db, 'users', user.uid), {
        email: user.email,
        created_at: new Date().toISOString(),
        uid: user.uid
      });
      
      return { success: true, user };
    } catch (error: any) {
      return { success: false, error: error.message };
    }
  }

  // Login user
  async login(email: string, password: string) {
    // Use local auth for development
    if (USE_LOCAL_AUTH) {
      const result = await localAuthService.login(email, password);
      if (result.success) {
        return { success: true, user: localAuthService.createMockFirebaseUser() };
      }
      return result;
    }

    // Original Firebase implementation
    try {
      const userCredential = await signInWithEmailAndPassword(auth, email, password);
      return { success: true, user: userCredential.user };
    } catch (error: any) {
      return { success: false, error: error.message };
    }
  }

  // Logout user
  async logout() {
    // Use local auth for development
    if (USE_LOCAL_AUTH) {
      return await localAuthService.logout();
    }

    // Original Firebase implementation
    try {
      await signOut(auth);
      return { success: true };
    } catch (error: any) {
      return { success: false, error: error.message };
    }
  }

  // Get current user
  getCurrentUser(): User | null {
    // Use local auth for development
    if (USE_LOCAL_AUTH) {
      const mockUser = localAuthService.createMockFirebaseUser();
      return mockUser as User;
    }

    // Original Firebase implementation
    return auth.currentUser;
  }

  // Listen to auth state changes
  onAuthStateChanged(callback: (user: User | null) => void) {
    // Use local auth for development
    if (USE_LOCAL_AUTH) {
      return localAuthService.onAuthStateChanged((user) => {
        callback(user ? localAuthService.createMockFirebaseUser() as User : null);
      });
    }

    // Original Firebase implementation
    return onAuthStateChanged(auth, callback);
  }

  // Get user data from Firestore
  async getUserData(uid: string) {
    // Use local auth for development
    if (USE_LOCAL_AUTH) {
      return await localAuthService.getUserData();
    }

    // Original Firebase implementation
    try {
      const userDoc = await getDoc(doc(db, 'users', uid));
      if (userDoc.exists()) {
        return { success: true, data: userDoc.data() };
      } else {
        return { success: false, error: 'User not found' };
      }
    } catch (error: any) {
      return { success: false, error: error.message };
    }
  }
}

export const firebaseAuthService = new FirebaseAuthService();