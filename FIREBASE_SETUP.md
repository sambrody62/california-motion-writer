# Firebase Setup Guide for California Motion Writer

## 🔥 Quick Setup Steps

### 1. Create Firebase Project

1. Go to [Firebase Console](https://console.firebase.google.com/)
2. Click "Create a project"
3. Name it: `california-motion-writer`
4. Disable Google Analytics (for now)
5. Click "Create project"

### 2. Enable Services

In Firebase Console:

#### Enable Authentication
1. Click "Authentication" in left sidebar
2. Click "Get started"
3. Enable "Email/Password" provider
4. Click "Save"

#### Enable Firestore
1. Click "Firestore Database" in left sidebar
2. Click "Create database"
3. Choose "Start in test mode" (we'll secure it later)
4. Select location: `us-central1`
5. Click "Enable"

#### Enable Storage (Optional, for PDFs)
1. Click "Storage" in left sidebar
2. Click "Get started"
3. Start in test mode
4. Select same location: `us-central1`

### 3. Get Your Configuration

1. In Firebase Console, click the gear ⚙️ > "Project settings"
2. Scroll down to "Your apps"
3. Click "</>" (Web) icon
4. Register app with nickname: "Motion Writer Web"
5. Copy the configuration object

### 4. Update Your .env.local

Replace the values in `frontend/.env.local` with your actual Firebase config:

```env
REACT_APP_FIREBASE_API_KEY=AIzaSy...your-actual-key
REACT_APP_FIREBASE_AUTH_DOMAIN=california-motion-writer.firebaseapp.com
REACT_APP_FIREBASE_PROJECT_ID=california-motion-writer
REACT_APP_FIREBASE_STORAGE_BUCKET=california-motion-writer.appspot.com
REACT_APP_FIREBASE_MESSAGING_SENDER_ID=123456789
REACT_APP_FIREBASE_APP_ID=1:123456789:web:abcdef
```

### 5. Deploy Firestore Rules

```bash
firebase deploy --only firestore:rules
```

### 6. Test Locally

```bash
# Start Firebase emulators (optional, for local testing)
firebase emulators:start

# Or just run the React app
cd frontend
npm start
```

## 📁 What We've Set Up

### Collections Structure:
```
Firestore Database
├── users/
│   └── {userId}/
│       ├── email
│       ├── created_at
│       └── uid
├── profiles/
│   └── {userId}/
│       ├── party_name
│       ├── case_number
│       ├── county
│       └── ...
├── motions/
│   └── {motionId}/
│       ├── user_id
│       ├── motion_type
│       ├── status
│       └── drafts/ (subcollection)
│           └── {stepNumber}/
│               ├── question_data
│               └── llm_output
└── documents/
    └── {documentId}/
        ├── motion_id
        ├── filename
        └── url
```

### Security Rules:
- Users can only access their own data
- Authentication required for all operations
- Proper read/write permissions per collection

## 🚀 Next Steps

### To Use Firebase in Your React App:

1. **Update App.tsx** to use FirebaseAuthProvider:
```tsx
import { FirebaseAuthProvider } from './contexts/FirebaseAuthContext';

function App() {
  return (
    <FirebaseAuthProvider>
      {/* Your app */}
    </FirebaseAuthProvider>
  );
}
```

2. **Use Firebase services** in components:
```tsx
import { firestoreService } from '../services/firebase/firestore.service';

// Create a motion
const result = await firestoreService.createMotion(userId, {
  motion_type: 'RFO',
  case_number: 'FL-2024-001'
});
```

## 🎯 Benefits Over Cloud SQL:

1. **No Schema Management**: Just add fields as needed
2. **Real-time Updates**: Built-in, no polling needed
3. **Offline Support**: Works offline, syncs when online
4. **Authentication**: Built-in, no JWT management
5. **Scaling**: Automatic, no server management
6. **Cost**: Pay only for what you use

## 💰 Pricing (Free Tier):

- **Firestore**: 1GB storage, 50K reads/day, 20K writes/day
- **Authentication**: Unlimited users
- **Storage**: 5GB storage, 1GB/day bandwidth
- **Hosting**: 10GB hosting, 360MB/day bandwidth

This is MORE than enough for MVP and early users!

## 🔗 Deployment:

When ready to deploy:

```bash
# Build React app
cd frontend
npm run build

# Deploy to Firebase Hosting
firebase deploy --only hosting

# Your app will be live at:
# https://california-motion-writer.web.app
```

## 📝 Migration from SQL:

The existing SQL models map to Firestore like this:

- `users` table → `users` collection
- `profiles` table → `profiles` collection  
- `motions` table → `motions` collection
- `motion_drafts` table → `drafts` subcollection
- `documents` table → `documents` collection

No JOINs needed - Firestore handles relationships via document IDs!