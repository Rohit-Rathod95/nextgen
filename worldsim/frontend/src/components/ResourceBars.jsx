// ResourceBars component — animated bar charts showing water, food, energy, and land levels per region.
import React from 'react';
import { GLOBAL_CONSTANTS } from '../constants/regions_meta';

const RESOURCES = [
    { key: 'water', label: 'Water', icon: '💧', color: '#38bdf8', track: '#0c4a6e' },
    { key: 'food', label: 'Food', icon: '🌾', color: '#4ade80', track: '#14532d' },
    { key: 'energy', label: 'Energy', icon: '⚡', color: '#f59e0b', track: '#451a03' },
    { key: 'land', label: 'Land', icon: '🌍', color: '#f87171', track: '#450a0a' },
];

const { MAX_RESOURCE, TRADE_THRESHOLD, DEFICIT_THRESHOLD } = GLOBAL_CONSTANTS;

function ResourceBar({ label, icon, color, track, value }) {
    const pct = Math.max(0, Math.min(100, (value / MAX_RESOURCE) * 100));
    const deficitPct = (DEFICIT_THRESHOLD / MAX_RESOURCE) * 100;
    const surplusPct = (TRADE_THRESHOLD / MAX_RESOURCE) * 100;

    const isDeficit = value < DEFICIT_THRESHOLD;
    const isSurplus = value > TRADE_THRESHOLD;
    const barColor = isDeficit ? '#ef4444' : isSurplus ? color : '#94a3b8';

    return (
        <div className="mb-3">
            <div className="flex justify-between items-center mb-1">
                <span className="text-xs font-medium flex items-center gap-1" style={{ color }}>
                    <span>{icon}</span>
                    <span>{label}</span>
                </span>
                <div className="flex items-center gap-2">
                    {isDeficit && (
                        <span className="text-xs px-1.5 py-0.5 rounded bg-red-900/40 text-red-400 font-mono">
                            DEFICIT
                        </span>
                    )}
                    {isSurplus && (
                        <span className="text-xs px-1.5 py-0.5 rounded font-mono" style={{ background: `${color}20`, color }}>
                            SURPLUS
                        </span>
                    )}
                    <span className="text-xs font-mono text-slate-300">
                        {Math.round(value)}
                    </span>
                </div>
            </div>
            <div className="relative h-3 rounded-full overflow-hidden" style={{ background: track }}>
                {/* Deficit threshold marker */}
                <div
                    className="absolute top-0 bottom-0 w-px bg-red-500/50 z-10"
                    style={{ left: `${deficitPct}%` }}
                />
                {/* Surplus threshold marker */}
                <div
                    className="absolute top-0 bottom-0 w-px bg-green-500/50 z-10"
                    style={{ left: `${surplusPct}%` }}
                />
                {/* Bar fill */}
                <div
                    className="h-full rounded-full bar-fill"
                    style={{
                        width: `${pct}%`,
                        background: `linear-gradient(90deg, ${barColor}99, ${barColor})`,
                        boxShadow: pct > 0 ? `0 0 8px ${barColor}66` : 'none',
                    }}
                />
            </div>
            <div className="flex justify-between text-xs text-slate-600 mt-0.5">
                <span className="font-mono">0</span>
                <span className="font-mono text-red-500/70">▲{DEFICIT_THRESHOLD}</span>
                <span className="font-mono text-green-500/70">▲{TRADE_THRESHOLD}</span>
                <span className="font-mono">{MAX_RESOURCE}</span>
            </div>
        </div>
    );
}

export default function ResourceBars({ region }) {
    if (!region) return null;
    return (
        <div>
            {RESOURCES.map((r) => {
                const { key, ...props } = r;
                return (
                    <ResourceBar key={key} {...props} value={region[key] ?? 0} />
                );
            })}
        </div>
    );
}
