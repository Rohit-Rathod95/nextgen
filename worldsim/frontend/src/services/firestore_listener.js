// Firestore listener — subscribes to real-time Firestore snapshots for live simulation updates.
// All normalization of backend field formats happens HERE so components always see a clean contract.
import {
    collection,
    doc,
    onSnapshot,
    query,
    orderBy,
    limit,
} from 'firebase/firestore';
import { useState, useEffect } from 'react';
import { db } from '../config/firebaseConfig';
import { REGIONS_INITIAL } from '../constants/regions_meta';

let isFirebaseReady = false;

try {
    if (db && db.app?.options?.projectId) {
        isFirebaseReady = true;
        console.log('[firestore_listener] Firebase ready');
    }
} catch (err) {
    console.warn('[firestore_listener] Firebase not ready:', err.message);
}

// ─── Normalization Helpers ────────────────────────────────────────────────────

// Capitalise first letter: "aquaria" → "Aquaria"
function capitalize(str) {
    if (!str) return str;
    return str.charAt(0).toUpperCase() + str.slice(1).toLowerCase();
}

/**
 * normalizeRegion — converts the raw Firestore region document into the
 * shape the frontend components expect.
 *
 * Backend writes:                          Frontend expects:
 *   region_id: "aquaria"          →  name: "Aquaria"
 *   strategy_weights: {trade:0.25}→  strategy_weights: {trade:0.25}  (kept nested, components updated)
 *   trust_scores: {aquaria: 50}   →  trust: {Aquaria: 0.5}  (0-100 → 0-1, keys capitalised)
 */
function normalizeRegion(raw) {
    // Capitalise the region name used as the lookup key
    const name = capitalize(raw.region_id || raw.name || '');

    // strategy_weights — backend region.py to_dict() writes FLAT fields:
    //   trade_weight, hoard_weight, invest_weight, aggress_weight
    // Rebuild nested object from either format.
    const strategy_weights = raw.strategy_weights || {
        trade: raw.trade_weight ?? 0.25,
        hoard: raw.hoard_weight ?? 0.25,
        invest: raw.invest_weight ?? 0.25,
        aggress: raw.aggress_weight ?? 0.25,
    };

    // trust — backend region.py to_dict() writes FLAT fields:
    //   trust_aquaria, trust_agrovia, trust_petrozon, trust_urbanex, trust_terranova (0-100 scale)
    // Rebuild capitalised 0-1 object from either format.
    const trust = {};
    if (raw.trust_scores) {
        // Nested trust_scores object (e.g. from mock/test data)
        Object.entries(raw.trust_scores).forEach(([k, v]) => {
            trust[capitalize(k)] = v > 1 ? v / 100 : v;
        });
    } else if (raw.trust) {
        // Already-normalised trust object — pass through, renormalize scale
        Object.entries(raw.trust).forEach(([k, v]) => {
            trust[capitalize(k)] = v > 1 ? v / 100 : v;
        });
    } else {
        // Flat trust_* fields from region.py to_dict()
        const REGION_NAMES = ['aquaria', 'agrovia', 'petrozon', 'urbanex', 'terranova'];
        REGION_NAMES.forEach((rName) => {
            const flatKey = `trust_${rName}`;
            if (raw[flatKey] !== undefined) {
                const v = raw[flatKey];
                trust[capitalize(rName)] = v > 1 ? v / 100 : v;
            }
        });
    }

    return {
        ...raw,
        name,
        strategy_weights,
        trust,
        // Population metadata
        population_trend: raw.population_trend || 'stable',
        population_history: raw.population_history || [],
        // Ensure resource fields are numbers
        water: Number(raw.water ?? 0),
        food: Number(raw.food ?? 0),
        energy: Number(raw.energy ?? 0),
        land: Number(raw.land ?? 0),
        population: Number(raw.population ?? 0),
        health_score: Number(raw.health_score ?? 0),
    };
}

/**
 * normalizeEvent — maps backend event fields to the frontend event shape.
 *
 * Backend writes:                      Frontend EventLog expects:
 *   source_region / target_region  →  regions_involved: [source, target]
 *   type                           →  type (kept as-is)
 *   description                    →  description (kept as-is)
 *   cycle                          →  cycle (kept as-is)
 */
function normalizeEvent(raw) {
    const src = capitalize(raw.source_region || '');
    const tgt = capitalize(raw.target_region || '');

    return {
        ...raw,
        regions_involved: [src, tgt].filter(Boolean),
        // resource field is not written by backend yet — default to null
        resource: raw.resource || null,
    };
}

/**
 * normalizeAnalysis — maps backend analysis fields to the frontend overlay shape.
 *
 * Backend writes:           Frontend AnalysisOverlay expects:
 *   insights               →  key_insights
 *   collapse_events        →  collapsed_regions
 *   alliance_events        →  alliance_clusters
 *   real_world_parallel    →  real_world_parallel (kept)
 *   dominant_strategy      →  dominant_strategy (kept)
 */
function normalizeAnalysis(raw) {
    return {
        ...raw,
        key_insights: raw.key_insights || raw.insights || [],
        collapsed_regions: raw.collapsed_regions || raw.collapse_events || [],
        alliance_clusters: raw.alliance_clusters || raw.alliance_events || [],
        dominant_strategy: raw.dominant_strategy || 'Unknown',
        real_world_parallel: raw.real_world_parallel || '',
    };
}

// ─── useRegions ───────────────────────────────────────────────────────────────
// Listens to `regions` collection. Documents are keyed by lowercase region_id.
// Returns an object keyed by CAPITALISED region name: { Aquaria: {...}, ... }
export function useRegions() {
    const [regions, setRegions] = useState(() => ({ ...REGIONS_INITIAL }));

    useEffect(() => {
        if (!isFirebaseReady) return;

        // Backend collection: "regions", document IDs are lowercase region names
        const col = collection(db, 'regions');
        const unsub = onSnapshot(col, (snap) => {
            const data = {};
            snap.forEach((docSnap) => {
                const raw = { ...docSnap.data(), region_id: docSnap.id };
                const norm = normalizeRegion(raw);
                // Key by capitalised name so components can do regions["Aquaria"]
                data[norm.name] = norm;
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
// Backend writes: current_cycle, is_running, current_event — already matches frontend!
export function useWorldState() {
    const [worldState, setWorldState] = useState({
        current_cycle: 0,
        current_event: 'None',
        is_running: false,
        speed: 1.0,
    });

    useEffect(() => {
        if (!isFirebaseReady) return;

        // Backend doc path: world_state/current
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
// Backend collection: "events" (NOT "events_log").
// Normalises source_region/target_region → regions_involved array.
export function useEventsLog(maxItems = 50) {
    const [events, setEvents] = useState([]);

    useEffect(() => {
        if (!isFirebaseReady) return;

        // BUG FIX: was 'events_log', backend writes to 'events'
        const q = query(
            collection(db, 'events'),
            orderBy('cycle', 'desc'),
            limit(maxItems)
        );
        const unsub = onSnapshot(q, (snap) => {
            const data = [];
            snap.forEach((docSnap) =>
                data.push(normalizeEvent({ id: docSnap.id, ...docSnap.data() }))
            );
            setEvents(data);
        }, (err) => {
            console.warn('[WorldSim] Events snapshot error:', err.message);
        });

        return () => unsub();
    }, [maxItems]);

    return events;
}

// ─── useAnalysis ──────────────────────────────────────────────────────────────
// Backend writes to: analysis/insights document.
// Normalises field names: insights→key_insights, collapse_events→collapsed_regions, etc.
export function useAnalysis() {
    const [analysis, setAnalysis] = useState(null);

    useEffect(() => {
        if (!isFirebaseReady) return;

        // Backend writes a single doc: analysis/insights
        const d = doc(db, 'analysis', 'insights');
        const unsub = onSnapshot(d, (snap) => {
            if (snap.exists()) {
                setAnalysis(normalizeAnalysis(snap.data()));
            }
        }, (err) => {
            console.warn('[WorldSim] Analysis snapshot error:', err.message);
        });

        return () => unsub();
    }, []);

    return analysis;
}

export { isFirebaseReady };
