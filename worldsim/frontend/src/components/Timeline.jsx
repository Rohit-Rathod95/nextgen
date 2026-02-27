// Timeline component — cycle progress bar, world state control strip, and API control buttons.
import React, { useState, useEffect, useCallback } from 'react';
import { GLOBAL_CONSTANTS } from '../constants/regions_meta';

const { TOTAL_CYCLES } = GLOBAL_CONSTANTS;

// Backend API functions
import {
  startSimulation,
  pauseSimulation,
  resumeSimulation,
  stopSimulation,
  setSpeed,
  getState,
  checkHealth,
} from '../services/api';

const EVENT_TYPE_COLORS = {
    drought: { icon: '☀️', color: '#f59e0b' },
    flood: { icon: '🌊', color: '#38bdf8' },
    energy_crisis: { icon: '⚡', color: '#ef4444' },
    fertile_season: { icon: '🌿', color: '#4ade80' },
    solar_surge: { icon: '🌞', color: '#fbbf24' },
    None: { icon: '✅', color: '#4ade80' },
};


export default function Timeline({ worldState, isFirebaseReady }) {
    const { current_cycle = 0, current_event = 'None', is_running = false } = worldState || {};

    // Local running state — pre-set optimistically & overridden by Firestore truth
    const [isRunning, setIsRunning] = useState(is_running);
    const [isLoading, setIsLoading] = useState(false);
    const [apiError, setApiError] = useState(null);

    // Keep local isRunning in sync with Firestore is_running (source of truth)
    useEffect(() => {
        setIsRunning(is_running);
    }, [is_running]);

    // Auto-dismiss error banner after 4 seconds
    useEffect(() => {
        if (!apiError) return;
        const t = setTimeout(() => setApiError(null), 4000);
        return () => clearTimeout(t);
    }, [apiError]);

    const pct = Math.min(100, (current_cycle / TOTAL_CYCLES) * 100);
    const eventCfg = EVENT_TYPE_COLORS[current_event] || { icon: '🌍', color: '#94a3b8' };
    const simDone = current_cycle >= TOTAL_CYCLES;

    const START_YEAR = 2025;
    const displayYear = START_YEAR + current_cycle;

    const statusLabel = simDone ? 'COMPLETE' : isRunning ? 'RUNNING' : 'PAUSED';
    const statusColor = simDone ? '#4ade80' : isRunning ? '#38bdf8' : '#f59e0b';

    // Cyan -> Amber -> Red transition
    const ringColor = pct < 40 ? '#0ea5e9' : pct < 75 ? '#f59e0b' : '#ef4444';

    // ── Start ──────────────────────────────────────────────────────────────────
    const handleStart = async () => {
        const result = await startSimulation();
        if (result.error) {
            console.error('Could not start:', result.error);
        }
    };

    // ── Pause ──────────────────────────────────────────────────────────────────
    const handlePause = async () => {
        const result = await pauseSimulation();
        if (result.error) {
            console.error('Could not pause:', result.error);
        }
    };

    // ── Resume ─────────────────────────────────────────────────────────────────
    const handleResume = async () => {
        const result = await resumeSimulation();
        if (result.error) {
            console.error('Could not resume:', result.error);
        }
    };

    // ── Stop ───────────────────────────────────────────────────────────────────
    const handleStop = async () => {
        const result = await stopSimulation();
        if (result.error) {
            console.error('Could not stop:', result.error);
        }
    };


    // ── Restart (after simDone) ────────────────────────────────────────────────
    const handleRestart = useCallback(async () => {
        if (isLoading) return;
        setIsLoading(true);
        setApiError(null);
        setIsRunning(true);
        try {
            await apiCall('/start');
        } catch (e) {
            setApiError(e.message);
            setIsRunning(false);
        } finally {
            setIsLoading(false);
        }
    }, [isLoading]);

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

                {/* World title & Cycle Ring */}
                <div className="flex items-center gap-4">
                    <div className="flex items-center gap-2">
                        <span className="text-lg">🌍</span>
                        <span className="text-sm font-bold tracking-widest text-slate-200">WORLDSIM</span>
                    </div>

                    {/* Circular Progress Ring */}
                    <div className="relative flex items-center justify-center w-9 h-9">
                        <svg className="w-9 h-9 -rotate-90 transform" viewBox="0 0 36 36">
                            <circle
                                cx="18"
                                cy="18"
                                r="15"
                                fill="none"
                                className="stroke-slate-800"
                                strokeWidth="2.5"
                            />
                            <circle
                                cx="18"
                                cy="18"
                                r="15"
                                fill="none"
                                stroke={ringColor}
                                strokeWidth="2.5"
                                strokeDasharray={94.248}
                                strokeDashoffset={94.248 - (pct / 100) * 94.248}
                                strokeLinecap="round"
                                className="transition-all duration-700 ease-in-out"
                            />
                        </svg>
                        <div className="absolute flex items-center justify-center mt-0.5">
                            <span className="text-[10px] font-bold font-mono tracking-tighter" style={{ color: ringColor }}>
                                {Math.floor(pct)}
                            </span>
                        </div>
                    </div>
                </div>

                {/* Cycle / Year display */}
                <div className="flex items-center gap-3">
                    <span className="text-xs font-mono text-slate-200">
                        📅 Year {displayYear} 
                        (Cycle {current_cycle} of {TOTAL_CYCLES})
                    </span>
                </div>
                {/* Status + Event */}
                <div className="flex items-center gap-3">
                    {current_event && current_event !== 'None' && (
                        <div
                            className="flex items-center gap-1.5 text-xs px-2 py-1 rounded"
                            style={{ background: `${eventCfg.color}20`, color: eventCfg.color }}
                        >
                            <span>{eventCfg.icon}</span>
                            <span className="font-mono">{current_event}</span>
                        </div>
                    )}

                    <div
                        className="text-xs font-mono px-2.5 py-1 rounded-full font-semibold flex items-center gap-1.5"
                        style={{ background: `${statusColor}20`, color: statusColor }}
                    >
                        {isRunning && !simDone && (
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

                    {/* START — only when not running, not done */}
                    {!isRunning && !simDone && (
                        <button
                            onClick={handleStart}
                            disabled={isLoading}
                            className="text-xs font-semibold px-3 py-1.5 rounded-lg transition-all duration-200 disabled:opacity-40 disabled:cursor-not-allowed"
                            style={{
                                background: 'linear-gradient(135deg, #0ea5e9, #6366f1)',
                                color: '#fff',
                                boxShadow: '0 0 12px #6366f140',
                            }}
                        >
                            {isLoading ? '⏳ STARTING…' : '▶ Start'}
                        </button>
                    )}

                    {/* PAUSE — only when running */}
                    {isRunning && !simDone && (
                        <button
                            onClick={handlePause}
                            disabled={isLoading}
                            className="text-xs font-semibold px-3 py-1.5 rounded-lg transition-all duration-200 disabled:opacity-40 disabled:cursor-not-allowed"
                            style={{
                                background: '#f59e0b20',
                                border: '1px solid #f59e0b50',
                                color: '#f59e0b',
                            }}
                        >
                            {isLoading ? '⏳ PAUSING…' : '⏸ Pause'}
                        </button>
                    )}

                    {/* RESUME — when paused mid-sim */}
                    {!isRunning && current_cycle > 0 && !simDone && (
                        <button
                            onClick={handleResume}
                            disabled={isLoading}
                            className="text-xs font-semibold px-3 py-1.5 rounded-lg transition-all duration-200 disabled:opacity-40 disabled:cursor-not-allowed"
                            style={{
                                background: '#4ade8020',
                                border: '1px solid #4ade8050',
                                color: '#4ade80',
                            }}
                        >
                            {isLoading ? '⏳ RESUMING…' : '▶ Resume'}
                        </button>
                    )}

                    {/* STOP — when running or mid-sim */}
                    {(isRunning || current_cycle > 0) && !simDone && (
                        <button
                            onClick={handleStop}
                            disabled={isLoading}
                            className="text-xs font-semibold px-3 py-1.5 rounded-lg transition-all duration-200 disabled:opacity-40 disabled:cursor-not-allowed"
                            style={{
                                background: '#ef444420',
                                border: '1px solid #ef444450',
                                color: '#ef4444',
                            }}
                        >
                            {isLoading ? '⏳ STOPPING…' : '■ Stop'}
                        </button>
                    )}

                    {/* RESTART — sim complete */}
                    {simDone && (
                        <button
                            onClick={handleRestart}
                            disabled={isLoading}
                            className="text-xs font-semibold px-3 py-1.5 rounded-lg transition-all duration-200 disabled:opacity-40 disabled:cursor-not-allowed"
                            style={{
                                background: 'linear-gradient(135deg, #4ade80, #0ea5e9)',
                                color: '#0f172a',
                            }}
                        >
                            {isLoading ? '⏳ STARTING…' : '🔄 Restart'}
                        </button>
                    )}
                </div>
            </div>

            {/* API error banner — auto-dismisses after 4s */}
            {apiError && (
                <div className="text-xs text-red-400 bg-red-900/20 border border-red-700/30 rounded px-3 py-1.5 flex justify-between items-center">
                    <span>⚠ Backend error: {apiError}</span>
                    <button
                        onClick={() => setApiError(null)}
                        className="text-red-500 hover:text-red-300 ml-2 leading-none"
                    >✕</button>
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
