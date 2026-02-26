// RegionPanel component — displays detailed stats and strategy weights for a selected region.
import React from 'react';
import { REGION_META, GLOBAL_CONSTANTS } from '../constants/regions_meta';
import ResourceBars from './ResourceBars';
import StrategyRadar from './StrategyRadar';

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

    // health_score is 0-100 from the backend (normalizeRegion keeps it as-is)
    const health = region.health_score ?? 0;
    const healthPct = Math.min(100, Math.max(0, health)).toFixed(1);

    // Use is_collapsed boolean from backend; fall back to population threshold
    const collapsed = region.is_collapsed || (region.population ?? 999) < GLOBAL_CONSTANTS.COLLAPSE_THRESHOLD_POPULATION;

    // Thresholds match 0-100 scale
    const healthLabel = health >= 70 ? 'HEALTHY' : health >= 40 ? 'STRESSED' : 'CRITICAL';
    const healthColor = health >= 70 ? '#4ade80' : health >= 40 ? '#f59e0b' : '#ef4444';

    // Strategy label from backend or derive from weights
    const strategyLabel = region.strategy_label || null;

    // Last action
    const lastAction = region.last_action || '—';

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
                        {healthPct}%
                    </div>
                </div>
            </div>

            {/* Population + Status Row */}
            <div className="glass rounded-xl p-3">
                <div className="grid grid-cols-2 gap-3">
                    <div>
                        <div className="text-xs text-slate-400 mb-1 font-medium">POPULATION</div>
                        <div className="text-xl font-bold font-mono" style={{ color }}>
                            {Math.round(region.population ?? 0).toLocaleString()}
                        </div>
                        {/* trend arrow and delta */}
                        {region.population_trend && (
                            <div className="text-xs mt-0.5"
                                style={{
                                    color: region.population_trend === 'growing' ? '#4ade80'
                                        : region.population_trend === 'declining' ? '#ef4444'
                                        : '#94a3b8',
                                }}>
                                {region.population_trend === 'growing' &&
                                    `↑ +${region.population_change}`}
                                {region.population_trend === 'declining' &&
                                    `↓ ${region.population_change}`}
                                {region.population_trend === 'stable' && '→ Stable'}
                            </div>
                        )}
                        <div className="text-xs text-slate-500 mt-0.5">
                            Min: {GLOBAL_CONSTANTS.COLLAPSE_THRESHOLD_POPULATION}
                        </div>
                        {/* population bar */}
                        {region.starting_population && (
                            (() => {
                                const cap = region.starting_population * 2.5;
                                const pct = Math.min(100, (region.population / cap) * 100);
                                let barColor = '#38bdf8';
                                if (region.population < region.starting_population) barColor = '#f59e0b';
                                else if (region.population > region.starting_population) barColor = '#4ade80';
                                if (pct > 90) barColor = '#ef4444';
                                return (
                                    <div className="w-full h-2 bg-slate-800 rounded mt-2">
                                        <div
                                            className="h-full rounded"
                                            style={{ width: `${pct}%`, background: barColor }}
                                        />
                                    </div>
                                );
                            })()
                        )}
                    </div>
                    <div>
                        <div className="text-xs text-slate-400 mb-1 font-medium">STRATEGY</div>
                        <div className="text-sm font-bold" style={{ color }}>
                            {strategyLabel || 'Balanced'}
                        </div>
                        <div className="text-xs text-slate-500 mt-0.5">
                            Last: {lastAction}
                        </div>
                    </div>
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
                {region.trust && Object.keys(region.trust).length > 0 ? (
                    Object.entries(region.trust).map(([neighbor, trust]) => {
                        const nMeta = REGION_META[neighbor] || {};
                        // trust is 0-1 after normalizeRegion
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
                    })
                ) : (
                    <p className="text-xs text-slate-500">Trust data loading…</p>
                )}
            </div>

            {/* Strategy Radar */}
            <div className="glass rounded-xl p-3">
                <StrategyRadar region={region} regionName={regionName} />
            </div>
        </div>
    );
}
