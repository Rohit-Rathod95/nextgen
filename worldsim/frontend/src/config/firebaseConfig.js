// firebaseConfig.js — Centralized Firebase initialization
import { initializeApp } from 'firebase/app';
import { getFirestore } from 'firebase/firestore';

const firebaseConfig = {
    apiKey: import.meta.env.VITE_FIREBASE_API_KEY,
    authDomain: import.meta.env.VITE_FIREBASE_AUTH_DOMAIN,
    projectId: import.meta.env.VITE_FIREBASE_PROJECT_ID,
    storageBucket: import.meta.env.VITE_FIREBASE_STORAGE_BUCKET,
    messagingSenderId: import.meta.env.VITE_FIREBASE_MESSAGING_SENDER_ID,
    appId: import.meta.env.VITE_FIREBASE_APP_ID,
};

let db = null;

try {
    if (firebaseConfig.projectId) {
        const app = initializeApp(firebaseConfig);
        db = getFirestore(app);
        console.log('[Firebase] Initialized successfully');
    }
} catch (err) {
    console.error('[Firebase] Initialization error:', err.message);
}

export { db };
