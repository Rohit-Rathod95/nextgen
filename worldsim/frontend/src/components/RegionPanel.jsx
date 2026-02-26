// RegionPanel component — displays detailed stats and strategy weights for a selected region.
import React from 'react';
import { REGION_META, GLOBAL_CONSTANTS } from '../constants/regions_meta';
import ResourceBars from './ResourceBars';
import StrategyRadar from './StrategyRadar';

function StatRow({ label, value, unit = '', color }) {
    return (
        <div className="flex justify-between items-center py-1 border-b border-slate-800">
            <span className="text-xs text-slate-400">{label}</span>
            <span className="text-xs font-mono font-medium" style={{ color: color || '#e2e8f0' }}>
                {typeof value === 'number' ? value.toFixed(1) : value}{unit}
            </span>
        </div>
    );
}

export default function RegionPanel({ region, regionName, onClose }) {
    if (!region || !regionName) {
        return (
            <div className="flex flex-col items-center justify-center h-full text-slate-500 p-6 text-center gap-3">
                <span className="text-4xl">🌐</span>
                <p className="text-sm font-medium">Select a region on the map</p>
                <p className="text-xs opacity-60">Click any hex node to view detailed stats</p>
            </div>
        );
    }

    const meta = REGION_META[regionName] || {};
    const color = meta.color || '#38bdf8';
    const health = region.health_score ?? 0;
    const collapsed = (region.population ?? 999) < GLOBAL_CONSTANTS.COLLAPSE_THRESHOLD_POPULATION;

    const healthLabel = health >= 0.7 ? 'HEALTHY' : health >= 0.4 ? 'STRESSED' : 'CRITICAL';
    const healthColor = health >= 0.7 ? '#4ade80' : health >= 0.4 ? '#f59e0b' : '#ef4444';

    return (
        <div className="flex flex-col gap-4 h-full overflow-y-auto pr-1">
            {/* Header */}
            <div
                className="rounded-xl p-4 flex items-center gap-3"
                style={{ background: `${color}12`, border: `1px solid ${color}33` }}
            >
                <span className="text-3xl">{meta.icon || '🌍'}</span>
                <div className="flex-1 min-w-0">
                    <div className="flex items-center gap-2 flex-wrap">
                        <h2 className="text-base font-bold tracking-wide" style={{ color }}>
                            {regionName}
                        </h2>
                        {collapsed && (
                            <span className="text-xs px-2 py-0.5 rounded bg-red-900/50 text-red-400 font-mono">
                                COLLAPSED
                            </span>
                        )}
                    </div>
                    <p className="text-xs text-slate-400 mt-0.5">{meta.dominant}-dominant region</p>
                </div>
                <div className="text-right">
                    <div
                        className="text-xs font-mono px-2 py-1 rounded"
                        style={{ background: `${healthColor}20`, color: healthColor }}
                    >
                        {healthLabel}
                    </div>
                    <div className="text-xs font-mono mt-1" style={{ color: healthColor }}>
                        {(health * 100).toFixed(1)}%
                    </div>
                </div>
            </div>

            {/* Population */}
            <div className="glass rounded-xl p-3">
                <div className="text-xs text-slate-400 mb-2 font-medium">POPULATION</div>
                <div className="text-2xl font-bold font-mono" style={{ color }}>
                    {Math.round(region.population ?? 0).toLocaleString()}
                </div>
                <div className="text-xs text-slate-500 mt-1">
                    Collapse threshold: {GLOBAL_CONSTANTS.COLLAPSE_THRESHOLD_POPULATION}
                </div>
            </div>

            {/* Resource Bars */}
            <div className="glass rounded-xl p-3">
                <div className="text-xs text-slate-400 mb-3 font-medium">RESOURCES</div>
                <ResourceBars region={region} />
            </div>

            {/* Trust Scores */}
            <div className="glass rounded-xl p-3">
                <div className="text-xs text-slate-400 mb-2 font-medium">TRUST SCORES</div>
                {region.trust && Object.entries(region.trust).map(([neighbor, trust]) => {
                    const nMeta = REGION_META[neighbor] || {};
                    const trustPct = (trust * 100).toFixed(0);
                    const trustColor = trust >= 0.6 ? '#4ade80' : trust >= 0.4 ? '#f59e0b' : '#ef4444';
                    return (
                        <div key={neighbor} className="mb-2">
                            <div className="flex justify-between text-xs mb-1">
                                <span className="text-slate-400" style={{ color: nMeta.color }}>
                                    {nMeta.icon} {neighbor}
                                </span>
                                <span className="font-mono" style={{ color: trustColor }}>{trustPct}%</span>
                            </div>
                            <div className="h-1.5 rounded-full bg-slate-800">
                                <div
                                    className="h-full rounded-full transition-all duration-500"
                                    style={{ width: `${trustPct}%`, background: trustColor }}
                                />
                            </div>
                        </div>
                    );
                })}
            </div>

            {/* Strategy Radar */}
            <div className="glass rounded-xl p-3">
                <StrategyRadar region={region} regionName={regionName} />
            </div>
        </div>
    );
}
