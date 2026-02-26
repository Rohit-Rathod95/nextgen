// Timeline component — cycle progress bar, world state control strip, and API control buttons.
import React, { useState, useCallback } from 'react';
import { GLOBAL_CONSTANTS } from '../constants/regions_meta';

const { TOTAL_CYCLES } = GLOBAL_CONSTANTS;

// Backend API base URL
const API_BASE = 'http://localhost:8000';

const EVENT_TYPE_COLORS = {
    drought: { icon: '☀️', color: '#f59e0b' },
    flood: { icon: '🌊', color: '#38bdf8' },
    energy_crisis: { icon: '⚡', color: '#ef4444' },
    fertile_season: { icon: '🌿', color: '#4ade80' },
    solar_surge: { icon: '🌞', color: '#fbbf24' },
    None: { icon: '✅', color: '#4ade80' },
};

async function apiCall(endpoint) {
    const res = await fetch(`${API_BASE}${endpoint}`, { method: 'POST' });
    if (!res.ok) {
        const err = await res.json().catch(() => ({}));
        throw new Error(err.detail || `HTTP ${res.status}`);
    }
    return res.json();
}

export default function Timeline({ worldState, isFirebaseReady }) {
    const { current_cycle = 0, current_event = 'None', is_running = false } = worldState || {};

    const [apiError, setApiError] = useState(null);
    const [loading, setLoading] = useState(false);

    const pct = Math.min(100, (current_cycle / TOTAL_CYCLES) * 100);
    const eventCfg = EVENT_TYPE_COLORS[current_event] || { icon: '🌍', color: '#94a3b8' };
    const simDone = current_cycle >= TOTAL_CYCLES;

    const statusLabel = simDone ? 'COMPLETE' : is_running ? 'RUNNING' : 'PAUSED';
    const statusColor = simDone ? '#4ade80' : is_running ? '#38bdf8' : '#f59e0b';

    const handleApi = useCallback(async (endpoint) => {
        setLoading(true);
        setApiError(null);
        try {
            await apiCall(endpoint);
        } catch (e) {
            setApiError(e.message);
        } finally {
            setLoading(false);
        }
    }, []);

    return (
        <div className="glass rounded-xl px-4 py-3 flex flex-col gap-2">
            {/* Top bar */}
            <div className="flex items-center justify-between gap-4 flex-wrap">
                {/* Connection indicator */}
                <div className="flex items-center gap-2">
                    <div
                        className="w-2 h-2 rounded-full"
                        style={{
                            background: isFirebaseReady ? '#4ade80' : '#f59e0b',
                            boxShadow: isFirebaseReady ? '0 0 8px #4ade8066' : '0 0 8px #f59e0b66',
                        }}
                    />
                    <span className="text-xs text-slate-400 font-mono">
                        {isFirebaseReady ? 'LIVE' : 'DEMO MODE'}
                    </span>
                </div>

                {/* World title */}
                <div className="flex items-center gap-2">
                    <span className="text-lg">🌍</span>
                    <span className="text-sm font-bold tracking-widest text-slate-200">WORLDSIM</span>
                </div>

                {/* Status + cycle */}
                <div className="flex items-center gap-3">
                    {/* Current climate event badge */}
                    {current_event && current_event !== 'None' && (
                        <div
                            className="flex items-center gap-1.5 text-xs px-2 py-1 rounded"
                            style={{ background: `${eventCfg.color}20`, color: eventCfg.color }}
                        >
                            <span>{eventCfg.icon}</span>
                            <span className="font-mono">{current_event}</span>
                        </div>
                    )}

                    {/* Cycle counter */}
                    <div className="text-xs font-mono text-slate-300">
                        Cycle{' '}
                        <span className="text-white font-bold">{current_cycle}</span>
                        <span className="text-slate-500"> / {TOTAL_CYCLES}</span>
                    </div>

                    {/* Status badge */}
                    <div
                        className="text-xs font-mono px-2.5 py-1 rounded-full font-semibold flex items-center gap-1.5"
                        style={{ background: `${statusColor}20`, color: statusColor }}
                    >
                        {is_running && !simDone && (
                            <span
                                className="inline-block w-1.5 h-1.5 rounded-full"
                                style={{ background: statusColor, animation: 'pulse 1.5s ease-in-out infinite' }}
                            />
                        )}
                        {statusLabel}
                    </div>
                </div>

                {/* ─── API Control Buttons ─── */}
                <div className="flex items-center gap-2 ml-auto">
                    {!is_running && !simDone && (
                        <button
                            onClick={() => handleApi('/start')}
                            disabled={loading}
                            className="text-xs font-semibold px-3 py-1.5 rounded-lg transition-all duration-200 disabled:opacity-40"
                            style={{
                                background: 'linear-gradient(135deg, #0ea5e9, #6366f1)',
                                color: '#fff',
                                boxShadow: '0 0 12px #6366f140',
                            }}
                        >
                            {loading ? '…' : '▶ Start'}
                        </button>
                    )}
                    {is_running && (
                        <button
                            onClick={() => handleApi('/pause')}
                            disabled={loading}
                            className="text-xs font-semibold px-3 py-1.5 rounded-lg transition-all duration-200 disabled:opacity-40"
                            style={{
                                background: '#f59e0b20',
                                border: '1px solid #f59e0b50',
                                color: '#f59e0b',
                            }}
                        >
                            {loading ? '…' : '⏸ Pause'}
                        </button>
                    )}
                    {!is_running && current_cycle > 0 && !simDone && (
                        <button
                            onClick={() => handleApi('/resume')}
                            disabled={loading}
                            className="text-xs font-semibold px-3 py-1.5 rounded-lg transition-all duration-200 disabled:opacity-40"
                            style={{
                                background: '#4ade8020',
                                border: '1px solid #4ade8050',
                                color: '#4ade80',
                            }}
                        >
                            {loading ? '…' : '▶ Resume'}
                        </button>
                    )}
                    {(is_running || current_cycle > 0) && !simDone && (
                        <button
                            onClick={() => handleApi('/stop')}
                            disabled={loading}
                            className="text-xs font-semibold px-3 py-1.5 rounded-lg transition-all duration-200 disabled:opacity-40"
                            style={{
                                background: '#ef444420',
                                border: '1px solid #ef444450',
                                color: '#ef4444',
                            }}
                        >
                            {loading ? '…' : '■ Stop'}
                        </button>
                    )}
                    {simDone && (
                        <button
                            onClick={() => handleApi('/start')}
                            disabled={loading}
                            className="text-xs font-semibold px-3 py-1.5 rounded-lg transition-all duration-200 disabled:opacity-40"
                            style={{
                                background: 'linear-gradient(135deg, #4ade80, #0ea5e9)',
                                color: '#0f172a',
                            }}
                        >
                            {loading ? '…' : '🔄 Restart'}
                        </button>
                    )}
                </div>
            </div>

            {/* API error banner */}
            {apiError && (
                <div className="text-xs text-red-400 bg-red-900/20 border border-red-700/30 rounded px-3 py-1.5 flex justify-between">
                    <span>⚠ Backend error: {apiError}</span>
                    <button onClick={() => setApiError(null)} className="text-red-500 hover:text-red-300 ml-2">✕</button>
                </div>
            )}

            {/* Progress bar */}
            <div className="relative h-2 rounded-full bg-slate-800 overflow-hidden">
                <div
                    className="h-full rounded-full transition-all duration-700 ease-out"
                    style={{
                        width: `${pct}%`,
                        background: `linear-gradient(90deg, #38bdf8, #818cf8 50%, ${pct >= 80 ? '#4ade80' : '#818cf8'})`,
                        boxShadow: '0 0 10px rgba(56,189,248,0.4)',
                    }}
                />
                {[25, 50, 75].map((m) => (
                    <div
                        key={m}
                        className="absolute top-0 bottom-0 w-px bg-slate-600/60"
                        style={{ left: `${m}%` }}
                    />
                ))}
            </div>

            {/* Phase labels */}
            <div className="flex justify-between text-xs text-slate-600 font-mono">
                <span>INIT</span>
                <span>EARLY</span>
                <span>MID</span>
                <span>LATE</span>
                <span>END</span>
            </div>
        </div>
    );
}
