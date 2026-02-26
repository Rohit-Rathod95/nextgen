// Timeline component — cycle progress bar and world state control strip.
import React from 'react';
import { GLOBAL_CONSTANTS } from '../constants/regions_meta';

const { TOTAL_CYCLES } = GLOBAL_CONSTANTS;

const EVENT_TYPE_COLORS = {
    Drought: { icon: '☀️', color: '#f59e0b' },
    Flood: { icon: '🌊', color: '#38bdf8' },
    'Energy Crisis': { icon: '⚡', color: '#ef4444' },
    None: { icon: '✅', color: '#4ade80' },
};

export default function Timeline({ worldState, isFirebaseReady }) {
    const { current_cycle = 0, current_event = 'None', is_running = false } = worldState || {};

    const pct = Math.min(100, (current_cycle / TOTAL_CYCLES) * 100);
    const eventCfg = EVENT_TYPE_COLORS[current_event] || { icon: '🌍', color: '#94a3b8' };

    const statusLabel = current_cycle >= TOTAL_CYCLES
        ? 'COMPLETE'
        : is_running
            ? 'RUNNING'
            : 'PAUSED';

    const statusColor = current_cycle >= TOTAL_CYCLES
        ? '#4ade80'
        : is_running
            ? '#38bdf8'
            : '#f59e0b';

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
                    {/* Current climate event */}
                    {current_event !== 'None' && (
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
                        {is_running && current_cycle < TOTAL_CYCLES && (
                            <span
                                className="inline-block w-1.5 h-1.5 rounded-full"
                                style={{ background: statusColor, animation: 'pulse 1.5s ease-in-out infinite' }}
                            />
                        )}
                        {statusLabel}
                    </div>
                </div>
            </div>

            {/* Progress bar */}
            <div className="relative h-2 rounded-full bg-slate-800 overflow-hidden">
                {/* Gradient fill */}
                <div
                    className="h-full rounded-full transition-all duration-700 ease-out"
                    style={{
                        width: `${pct}%`,
                        background: `linear-gradient(90deg, #38bdf8, #818cf8 50%, ${pct >= 80 ? '#4ade80' : '#818cf8'})`,
                        boxShadow: '0 0 10px rgba(56,189,248,0.4)',
                    }}
                />
                {/* Milestone markers */}
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
