// Firestore listener — subscribes to real-time Firestore snapshots for live simulation updates.
import { initializeApp } from 'firebase/app';
import {
    getFirestore,
    collection,
    doc,
    onSnapshot,
    query,
    orderBy,
    limit,
} from 'firebase/firestore';
import { useState, useEffect } from 'react';
import { REGIONS_INITIAL } from '../constants/regions_meta';

// Firebase config — populated from environment variables (see .env.template)
const firebaseConfig = {
    apiKey: import.meta.env.VITE_FIREBASE_API_KEY,
    authDomain: import.meta.env.VITE_FIREBASE_AUTH_DOMAIN,
    projectId: import.meta.env.VITE_FIREBASE_PROJECT_ID,
    storageBucket: import.meta.env.VITE_FIREBASE_STORAGE_BUCKET,
    messagingSenderId: import.meta.env.VITE_FIREBASE_MESSAGING_SENDER_ID,
    appId: import.meta.env.VITE_FIREBASE_APP_ID,
};

let app, db;
let isFirebaseReady = false;

try {
    if (firebaseConfig.projectId) {
        app = initializeApp(firebaseConfig);
        db = getFirestore(app);
        isFirebaseReady = true;
    }
} catch (e) {
    console.warn('[WorldSim] Firebase not configured — running in demo mode with initial values.');
}

// ─── useRegions ───────────────────────────────────────────────────────────────
// Returns live region data keyed by name. Falls back to REGIONS_INITIAL if
// Firestore is not configured.
export function useRegions() {
    const [regions, setRegions] = useState(() => ({ ...REGIONS_INITIAL }));

    useEffect(() => {
        if (!isFirebaseReady) return;

        const col = collection(db, 'regions');
        const unsub = onSnapshot(col, (snap) => {
            const data = {};
            snap.forEach((docSnap) => {
                const d = docSnap.data();
                data[d.name] = d;
            });
            if (Object.keys(data).length > 0) setRegions(data);
        }, (err) => {
            console.warn('[WorldSim] Regions snapshot error:', err.message);
        });

        return () => unsub();
    }, []);

    return regions;
}

// ─── useWorldState ────────────────────────────────────────────────────────────
export function useWorldState() {
    const [worldState, setWorldState] = useState({
        current_cycle: 0,
        current_event: 'None',
        is_running: false,
    });

    useEffect(() => {
        if (!isFirebaseReady) return;

        const d = doc(db, 'world_state', 'current');
        const unsub = onSnapshot(d, (snap) => {
            if (snap.exists()) setWorldState(snap.data());
        }, (err) => {
            console.warn('[WorldSim] WorldState snapshot error:', err.message);
        });

        return () => unsub();
    }, []);

    return worldState;
}

// ─── useEventsLog ─────────────────────────────────────────────────────────────
export function useEventsLog(maxItems = 50) {
    const [events, setEvents] = useState([]);

    useEffect(() => {
        if (!isFirebaseReady) return;

        const q = query(
            collection(db, 'events_log'),
            orderBy('cycle', 'desc'),
            limit(maxItems)
        );
        const unsub = onSnapshot(q, (snap) => {
            const data = [];
            snap.forEach((docSnap) => data.push({ id: docSnap.id, ...docSnap.data() }));
            setEvents(data);
        }, (err) => {
            console.warn('[WorldSim] EventsLog snapshot error:', err.message);
        });

        return () => unsub();
    }, [maxItems]);

    return events;
}

// ─── useAnalysis ──────────────────────────────────────────────────────────────
export function useAnalysis() {
    const [analysis, setAnalysis] = useState(null);

    useEffect(() => {
        if (!isFirebaseReady) return;

        const col = collection(db, 'analysis');
        const unsub = onSnapshot(col, (snap) => {
            if (!snap.empty) {
                setAnalysis(snap.docs[0].data());
            }
        }, (err) => {
            console.warn('[WorldSim] Analysis snapshot error:', err.message);
        });

        return () => unsub();
    }, []);

    return analysis;
}

export { isFirebaseReady };
