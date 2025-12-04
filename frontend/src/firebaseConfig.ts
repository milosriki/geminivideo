import { FirebaseApp, initializeApp } from 'firebase/app';
import { Auth, getAuth } from 'firebase/auth';
import { Firestore, getFirestore } from 'firebase/firestore';
import { FirebaseStorage, getStorage } from 'firebase/storage';
import { Functions, getFunctions } from 'firebase/functions';
import { getAnalytics, isSupported } from 'firebase/analytics';
import { getPerformance } from 'firebase/performance';

// Validate required environment variables
const requiredEnvVars = [
  'VITE_FIREBASE_API_KEY',
  'VITE_FIREBASE_AUTH_DOMAIN',
  'VITE_FIREBASE_PROJECT_ID',
  'VITE_FIREBASE_STORAGE_BUCKET',
  'VITE_FIREBASE_MESSAGING_SENDER_ID',
  'VITE_FIREBASE_APP_ID'
] as const;

for (const varName of requiredEnvVars) {
  if (!import.meta.env[varName]) {
    throw new Error(
      `❌ Missing required environment variable: ${varName}\n` +
      `Please set all Firebase config variables in your .env file.\n` +
      `See .env.example for required variables.`
    );
  }
}

// Your web app's Firebase configuration
// SECURITY: All values must come from environment variables - no hardcoded fallbacks
const firebaseConfig = {
  apiKey: import.meta.env.VITE_FIREBASE_API_KEY as string,
  authDomain: import.meta.env.VITE_FIREBASE_AUTH_DOMAIN as string,
  projectId: import.meta.env.VITE_FIREBASE_PROJECT_ID as string,
  storageBucket: import.meta.env.VITE_FIREBASE_STORAGE_BUCKET as string,
  messagingSenderId: import.meta.env.VITE_FIREBASE_MESSAGING_SENDER_ID as string,
  appId: import.meta.env.VITE_FIREBASE_APP_ID as string,
  measurementId: import.meta.env.VITE_FIREBASE_MEASUREMENT_ID as string // Optional
};

// Initialize Firebase
let app: FirebaseApp;
let auth: Auth;
let db: Firestore;
let storage: FirebaseStorage;
let functions: Functions;

try {
  app = initializeApp(firebaseConfig);

  // Initialize Firebase services
  auth = getAuth(app);
  db = getFirestore(app);
  storage = getStorage(app);
  functions = getFunctions(app);

  // Initialize Performance Monitoring
  if (typeof window !== 'undefined') {
    const perf = getPerformance(app);
  }


} catch (error) {
  console.warn('⚠️ Firebase initialization failed:', error);
}

export { auth, db, storage, functions };

// Initialize Analytics only if supported
let analytics = null;
if (typeof window !== 'undefined') {
  isSupported().then(yes => {
    if (yes) {
      analytics = getAnalytics(app);
    }
  }).catch(() => {

  });
}
export { analytics };

// Log Firebase initialization for testing


export default app!;
