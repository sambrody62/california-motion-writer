import { 
  collection, 
  doc, 
  setDoc, 
  getDoc, 
  getDocs,
  addDoc,
  updateDoc,
  deleteDoc,
  query,
  where,
  orderBy,
  limit,
  Timestamp
} from 'firebase/firestore';
import { db } from '../../config/firebase';

export class FirestoreService {
  // Profile operations
  async createProfile(userId: string, profileData: any) {
    try {
      await setDoc(doc(db, 'profiles', userId), {
        ...profileData,
        user_id: userId,
        created_at: Timestamp.now(),
        updated_at: Timestamp.now()
      });
      return { success: true };
    } catch (error: any) {
      return { success: false, error: error.message };
    }
  }

  async getProfile(userId: string) {
    try {
      const profileDoc = await getDoc(doc(db, 'profiles', userId));
      if (profileDoc.exists()) {
        return { success: true, data: profileDoc.data() };
      }
      return { success: false, error: 'Profile not found' };
    } catch (error: any) {
      return { success: false, error: error.message };
    }
  }

  async updateProfile(userId: string, updates: any) {
    try {
      await updateDoc(doc(db, 'profiles', userId), {
        ...updates,
        updated_at: Timestamp.now()
      });
      return { success: true };
    } catch (error: any) {
      return { success: false, error: error.message };
    }
  }

  // Motion operations
  async createMotion(userId: string, motionData: any) {
    try {
      const docRef = await addDoc(collection(db, 'motions'), {
        ...motionData,
        user_id: userId,
        status: 'draft',
        created_at: Timestamp.now(),
        updated_at: Timestamp.now()
      });
      return { success: true, id: docRef.id };
    } catch (error: any) {
      return { success: false, error: error.message };
    }
  }

  async getMotion(motionId: string) {
    try {
      const motionDoc = await getDoc(doc(db, 'motions', motionId));
      if (motionDoc.exists()) {
        return { success: true, data: { id: motionDoc.id, ...motionDoc.data() } };
      }
      return { success: false, error: 'Motion not found' };
    } catch (error: any) {
      return { success: false, error: error.message };
    }
  }

  async getUserMotions(userId: string) {
    try {
      const q = query(
        collection(db, 'motions'),
        where('user_id', '==', userId),
        orderBy('created_at', 'desc')
      );
      const querySnapshot = await getDocs(q);
      const motions = querySnapshot.docs.map(doc => ({
        id: doc.id,
        ...doc.data()
      }));
      return { success: true, data: motions };
    } catch (error: any) {
      return { success: false, error: error.message };
    }
  }

  async updateMotion(motionId: string, updates: any) {
    try {
      await updateDoc(doc(db, 'motions', motionId), {
        ...updates,
        updated_at: Timestamp.now()
      });
      return { success: true };
    } catch (error: any) {
      return { success: false, error: error.message };
    }
  }

  async deleteMotion(motionId: string) {
    try {
      await deleteDoc(doc(db, 'motions', motionId));
      return { success: true };
    } catch (error: any) {
      return { success: false, error: error.message };
    }
  }

  // Draft operations (subcollection under motions)
  async saveDraft(motionId: string, stepNumber: number, draftData: any) {
    try {
      const draftId = `step_${stepNumber}`;
      await setDoc(
        doc(db, 'motions', motionId, 'drafts', draftId),
        {
          ...draftData,
          step_number: stepNumber,
          saved_at: Timestamp.now()
        }
      );
      return { success: true };
    } catch (error: any) {
      return { success: false, error: error.message };
    }
  }

  async getDrafts(motionId: string) {
    try {
      const draftsSnapshot = await getDocs(
        collection(db, 'motions', motionId, 'drafts')
      );
      const drafts = draftsSnapshot.docs.map(doc => ({
        id: doc.id,
        ...doc.data()
      }));
      return { success: true, data: drafts };
    } catch (error: any) {
      return { success: false, error: error.message };
    }
  }

  // Document operations
  async saveDocument(motionId: string, documentData: any) {
    try {
      const docRef = await addDoc(collection(db, 'documents'), {
        ...documentData,
        motion_id: motionId,
        created_at: Timestamp.now()
      });
      return { success: true, id: docRef.id };
    } catch (error: any) {
      return { success: false, error: error.message };
    }
  }

  async getMotionDocuments(motionId: string) {
    try {
      const q = query(
        collection(db, 'documents'),
        where('motion_id', '==', motionId),
        orderBy('created_at', 'desc')
      );
      const querySnapshot = await getDocs(q);
      const documents = querySnapshot.docs.map(doc => ({
        id: doc.id,
        ...doc.data()
      }));
      return { success: true, data: documents };
    } catch (error: any) {
      return { success: false, error: error.message };
    }
  }
}

export const firestoreService = new FirestoreService();