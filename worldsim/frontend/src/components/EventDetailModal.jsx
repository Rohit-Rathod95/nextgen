// EventDetailModal.jsx — Universal event detail popup for WorldSim.
// Handles climate, conflict, and collapse events with rich contextual info.
import React, { useEffect } from 'react';

// ─── Animation Styles ─────────────────────────────────────────────────────

const animationStyles = `
@keyframes modalFadeIn {
  from {
    opacity: 0;
    transform: scale(0.92) translateY(-10px);
  }
  to {
    opacity: 1;
    transform: scale(1) translateY(0);
  }
}

.event-detail-modal-box {
  animation: modalFadeIn 0.2s ease-out;
  scrollbar-width: thin;
  scrollbar-color: rgba(99, 102, 241, 0.3) transparent;
}

.event-detail-modal-box::-webkit-scrollbar {
  width: 6px;
}

.event-detail-modal-box::-webkit-scrollbar-track {
  background: transparent;
}

.event-detail-modal-box::-webkit-scrollbar-thumb {
  background: rgba(99, 102, 241, 0.3);
  border-radius: 3px;
}

.event-detail-modal-box::-webkit-scrollbar-thumb:hover {
  background: rgba(99, 102, 241, 0.5);
}
`;

if (typeof document !== 'undefined') {
    const styleEl = document.createElement('style');
    styleEl.textContent = animationStyles;
    document.head.appendChild(styleEl);
}

// ─── Constants ─────────────────────────────────────────────────────────────

const REAL_WORLD_LABELS = {
    aquaria: 'Aquaria (Brazil)',
    agrovia: 'Agrovia (India)',
    petrozon: 'Petrozon (Gulf States)',
    urbanex: 'Urbanex (China)',
    terranova: 'Terranova (Africa)',
};

const REGION_COLORS = {
    aquaria: '#3b82f6',
    agrovia: '#22c55e',
    petrozon: '#f97316',
    urbanex: '#ef4444',
    terranova: '#a855f7',
};

const RESOURCE_ICONS = {
    water: '💧',
    food: '🌾',
    energy: '⚡',
    land: '🏔️',
};

const getLabel = (id) =>
    REAL_WORLD_LABELS[id?.toLowerCase()] || id || 'Unknown';

const getColor = (id) =>
    REGION_COLORS[id?.toLowerCase()] || '#6366f1';

const displayYear = (cycle) =>
    2025 + (cycle || 0);

// ─── Shared card / pill helpers ────────────────────────────────────────────

function GlobeCard({ title, children }) {
    return (
        <div style={{
            background: 'rgba(255,255,255,0.04)',
            border: '1px solid rgba(255,255,255,0.08)',
            borderRadius: 10,
            padding: 12,
            marginTop: 12,
        }}>
            <p className="text-xs font-semibold text-slate-400 mb-2">{title}</p>
            <div className="text-xs text-slate-300 leading-relaxed">{children}</div>
        </div>
    );
}

function RegionPill({ id, label }) {
    const color = getColor(id);
    return (
        <span className="inline-flex items-center gap-1.5 px-2.5 py-1 rounded-full text-xs font-semibold"
            style={{ background: `${color}20`, color }}>
            <span className="w-2 h-2 rounded-full inline-block" style={{ background: color }} />
            {label || getLabel(id)}
        </span>
    );
}

function SectionTitle({ children }) {
    return (
        <p className="text-xs font-semibold text-slate-400 uppercase tracking-wider mb-2 mt-4">
            {children}
        </p>
    );
}

// ─── CLIMATE EVENT ─────────────────────────────────────────────────────────

const CLIMATE_CONFIG = {
    drought: { emoji: '🌵', title: 'Severe Drought', positive: false },
    flood: { emoji: '🌊', title: 'Catastrophic Flood', positive: false },
    energy_crisis: { emoji: '⚡', title: 'Energy Crisis', positive: false },
    fertile_season: { emoji: '🌱', title: 'Fertile Season Boom', positive: true },
    solar_surge: { emoji: '☀️', title: 'Solar Energy Surge', positive: true },
};

const CLIMATE_CONTEXT = {
    drought:
        'Mirrors accelerating drought patterns driven by climate change. Similar to the 2011 East Africa drought affecting 13 million people and triggering a regional food crisis.',
    flood:
        'Mirrors the 2022 Pakistan floods that submerged one third of the country and destroyed 45% of crop output, requiring emergency food imports.',
    energy_crisis:
        'Mirrors the 2022 European energy crisis when supply disruption forced emergency rationing and accelerated renewable energy investment.',
    fertile_season:
        'Mirrors La Niña weather patterns bringing above-average rainfall and exceptional harvests to agricultural regions globally.',
    solar_surge:
        'Mirrors the global solar adoption boom — nations investing in renewables gaining energy independence from volatile fossil fuel markets.',
};

function ClimateBody({ event }) {
    const outcomeKey = event.outcome || event.climate_type || 'drought';
    const cfg = CLIMATE_CONFIG[outcomeKey] || CLIMATE_CONFIG.drought;
    const regionId = (event.regions_involved?.[0] || event.source_region || event.affected_region || '').toLowerCase();
    const context = CLIMATE_CONTEXT[outcomeKey] || 'A significant climate event has occurred.';
    const isNegative = !cfg.positive;

    // Extract resource changes from event data
    const resourceChanges = [];
    if (event.sender_before && event.sender_after) {
        ['water', 'food', 'energy', 'land'].forEach((res) => {
            const before = event.sender_before[res];
            const after = event.sender_after[res];
            if (before !== undefined && after !== undefined) {
                resourceChanges.push({ resource: res, before, after });
            }
        });
    }

    // Calculate severity
    let maxChange = 0;
    resourceChanges.forEach(({ before, after }) => {
        maxChange = Math.max(maxChange, Math.abs(after - before));
    });

    let severityLabel = '🟢 Minor Impact';
    let severityBg = 'rgba(74,222,128,0.12)';
    let severityBorder = 'rgba(74,222,128,0.3)';
    let severityColor = '#4ade80';

    if (maxChange > 30) {
        severityLabel = '🔴 Severe Impact';
        severityBg = 'rgba(239,68,68,0.12)';
        severityBorder = 'rgba(239,68,68,0.3)';
        severityColor = '#f87171';
    } else if (maxChange >= 15) {
        severityLabel = '🟡 Moderate Impact';
        severityBg = 'rgba(234,179,8,0.12)';
        severityBorder = 'rgba(234,179,8,0.3)';
        severityColor = '#facc15';
    }

    return (
        <>
            {/* What Happened */}
            <div className="text-center py-4">
                <div style={{ fontSize: 48 }}>{cfg.emoji}</div>
                <p className="text-white font-bold text-lg mt-2">{cfg.title}</p>
                {regionId && (
                    <div className="mt-2 flex justify-center">
                        <RegionPill id={regionId} />
                    </div>
                )}
            </div>

            {/* Resource Impact */}
            {resourceChanges.length > 0 && (
                <>
                    <SectionTitle>Resource Impact</SectionTitle>
                    {resourceChanges.map(({ resource, before, after }) => {
                        const change = after - before;
                        const changeText = change > 0 ? `+${change.toFixed(1)}` : `${change.toFixed(1)}`;
                        const changeColor = change > 0 ? '#22c55e' : '#ef4444';
                        return (
                            <div key={resource} className="text-xs text-slate-300 py-1.5 flex justify-between items-center">
                                <span>
                                    <span className="mr-1.5">{RESOURCE_ICONS[resource] || '•'}</span>
                                    {resource.charAt(0).toUpperCase() + resource.slice(1)}
                                </span>
                                <span className="font-mono text-slate-500">
                                    {before.toFixed(1)} → {after.toFixed(1)}
                                </span>
                                <span className="font-mono font-semibold ml-2" style={{ color: changeColor }}>
                                    {changeText}
                                </span>
                            </div>
                        );
                    })}

                    {/* Severity Badge */}
                    <div className="rounded-lg px-3 py-2 text-xs font-semibold text-center mt-3"
                        style={{ background: severityBg, border: `1px solid ${severityBorder}`, color: severityColor }}>
                        {severityLabel}
                    </div>
                </>
            )}

            {/* Real World Context */}
            <GlobeCard title="🌐 Real World Parallel">
                {context}
            </GlobeCard>

            {/* Strategic Impact */}
            <SectionTitle>Strategic Impact</SectionTitle>
            <div className="rounded-lg px-3 py-2 text-xs text-slate-300 leading-relaxed"
                style={{ background: 'rgba(255,255,255,0.04)', border: '1px solid rgba(255,255,255,0.08)' }}>
                {isNegative
                    ? <>
                        ⚠️ This shock will push <strong style={{ color: getColor(regionId) }}>{getLabel(regionId)}</strong> toward
                        emergency hoarding and desperate trade seeking. Expect increased aggression weight if resources cannot be recovered.
                    </>
                    : <>
                        ✅ This windfall gives <strong style={{ color: getColor(regionId) }}>{getLabel(regionId)}</strong> a
                        surplus advantage. Expect increased trade willingness and strengthened diplomatic position with resource-poor neighbors.
                    </>
                }
            </div>
        </>
    );
}

// ─── CONFLICT EVENT ────────────────────────────────────────────────────────

function ConflictBody({ event }) {
    const attackerId = (event.source_region || event.regions_involved?.[0] || '').toLowerCase();
    const defenderId = (event.target_region || event.regions_involved?.[1] || '').toLowerCase();
    const isSuccess = (event.outcome || '').includes('success');
    const aggressSuccess = event.aggress_success || isSuccess;

    const attackerLabel = attackerId ? attackerId.charAt(0).toUpperCase() + attackerId.slice(1) : '?';
    const defenderLabel = defenderId ? defenderId.charAt(0).toUpperCase() + defenderId.slice(1) : '?';

    return (
        <>
            {/* Participants */}
            <SectionTitle>Participants</SectionTitle>
            <div className="grid grid-cols-[1fr_auto_1fr] items-center gap-2 mt-1">
                {/* Attacker */}
                <div className="text-center rounded-xl p-3"
                    style={{ background: 'rgba(255,255,255,0.05)', border: `1px solid ${getColor(attackerId)}30` }}>
                    <div className="w-3 h-3 rounded-full mx-auto mb-1" style={{ background: getColor(attackerId) }} />
                    <p className="text-sm font-bold text-white">{attackerLabel}</p>
                    <p className="text-xs text-slate-400">{getLabel(attackerId)}</p>
                    <span className="mt-1 inline-block text-xs px-1.5 py-0.5 rounded"
                        style={{ background: 'rgba(239,68,68,0.15)', color: '#f87171' }}>ATTACKER</span>
                </div>

                <div className="text-xl">⚔️</div>

                {/* Defender */}
                <div className="text-center rounded-xl p-3"
                    style={{ background: 'rgba(255,255,255,0.05)', border: `1px solid ${getColor(defenderId)}30` }}>
                    <div className="w-3 h-3 rounded-full mx-auto mb-1" style={{ background: getColor(defenderId) }} />
                    <p className="text-sm font-bold text-white">{defenderLabel}</p>
                    <p className="text-xs text-slate-400">{getLabel(defenderId)}</p>
                    <span className="mt-1 inline-block text-xs px-1.5 py-0.5 rounded"
                        style={{ background: 'rgba(99,102,241,0.15)', color: '#818cf8' }}>DEFENDER</span>
                </div>
            </div>

            {/* Outcome Banner */}
            <SectionTitle>Battle Outcome</SectionTitle>
            <div className="grid grid-cols-2 rounded-xl overflow-hidden text-xs font-bold text-center">
                <div className="py-3"
                    style={isSuccess
                        ? { background: 'rgba(74,222,128,0.15)', color: '#4ade80' }
                        : { background: 'rgba(239,68,68,0.15)', color: '#f87171' }}>
                    {isSuccess ? `⚔️ ${attackerLabel} WON` : `⚔️ ${attackerLabel} FAILED`}
                </div>
                <div className="py-3"
                    style={isSuccess
                        ? { background: 'rgba(239,68,68,0.15)', color: '#f87171' }
                        : { background: 'rgba(74,222,128,0.15)', color: '#4ade80' }}>
                    {isSuccess ? `🛡️ ${defenderLabel} DEFEATED` : `🛡️ ${defenderLabel} HELD`}
                </div>
            </div>

            {/* Resources Seized */}
            {aggressSuccess && (
                <>
                    <SectionTitle>Resources Seized</SectionTitle>
                    <div className="grid grid-cols-2 gap-3">
                        <div className="rounded-lg p-3 text-xs"
                            style={{ background: 'rgba(74,222,128,0.08)', border: '1px solid rgba(74,222,128,0.2)' }}>
                            <p className="font-semibold text-green-400 mb-1">{attackerLabel} GAINED</p>
                            <p className="text-green-300">+15 🌾 Food</p>
                            <p className="text-green-300">+10 💧 Water</p>
                            <p className="text-red-400 mt-1">-15 ⚡ Energy (battle cost)</p>
                        </div>
                        <div className="rounded-lg p-3 text-xs"
                            style={{ background: 'rgba(239,68,68,0.08)', border: '1px solid rgba(239,68,68,0.2)' }}>
                            <p className="font-semibold text-red-400 mb-1">{defenderLabel} LOST</p>
                            <p className="text-red-300">-15 🌾 Food</p>
                            <p className="text-red-300">-10 💧 Water</p>
                            <p className="text-red-400 mt-1">-10 ⚡ Energy (battle cost)</p>
                        </div>
                    </div>
                </>
            )}

            {/* Trust Cascade */}
            <SectionTitle>🌐 Global Trust Impact</SectionTitle>
            <div className="rounded-lg px-3 py-3 text-xs text-slate-300 leading-relaxed"
                style={{ background: 'rgba(239,68,68,0.08)', border: '1px solid rgba(239,68,68,0.2)' }}>
                <p>All regions lost trust in <strong style={{ color: getColor(attackerId) }}>{getLabel(attackerId)}</strong> by 10 points.
                    The world watched — and remembers.</p>
                <p className="text-slate-500 mt-2">Trust damage makes future trade harder for {attackerLabel} and may trigger coordinated isolation.</p>
            </div>

            {/* Why It Happened */}
            <SectionTitle>Why Conflict Occurred</SectionTitle>
            <ul className="text-xs text-slate-300 leading-relaxed space-y-1">
                <li>• <strong style={{ color: getColor(attackerId) }}>{getLabel(attackerId)}</strong> resources were critically low</li>
                <li>• Trust with <strong style={{ color: getColor(defenderId) }}>{getLabel(defenderId)}</strong> fell below 20</li>
                <li>• Aggression became the dominant strategy weight</li>
                <li>• <strong style={{ color: getColor(defenderId) }}>{getLabel(defenderId)}</strong> was identified as the weakest available target</li>
            </ul>
        </>
    );
}

// ─── COLLAPSE EVENT ────────────────────────────────────────────────────────

const COLLAPSE_CAUSES = {
    water_depletion:
        'Critical water shortage over multiple years depleted reserves below survival threshold. Without water, food production failed and population began rapid decline.',
    food_depletion:
        'Food supply failed to meet growing population demand. High consumption rates combined with failed trade partnerships left no recovery path.',
    sustained_decline:
        'Consistent multi-year resource decline with no successful trade recovery. Each failed trade attempt damaged trust, further isolating the region from potential aid.',
    overpopulation_pressure:
        'Population growth outpaced all resource production and trade capacity. The demographic pressure was unsustainable given available resources.',
};

function CollapseBody({ event }) {
    const regionId = (event.source_region || event.affected_region || event.regions_involved?.[0] || '').toLowerCase();
    const causeKey = event.outcome || 'sustained_decline';
    const causeText = COLLAPSE_CAUSES[causeKey] ||
        'Multiple resources hit critical levels simultaneously, triggering cascade failure across all systems.';

    // Extract final state from event
    const finalPopulation = event.population || 0;
    const healthScore = event.health_score || 0;

    return (
        <>
            {/* Banner */}
            <div className="rounded-xl p-4 text-center mt-2" style={{
                background: 'rgba(239,68,68,0.15)',
                border: '1px solid rgba(239,68,68,0.3)',
            }}>
                <p className="text-lg font-black text-red-400">💀 {getLabel(regionId).toUpperCase()} HAS FALLEN</p>
                <p className="text-xs text-slate-400 mt-1">Year {displayYear(event.cycle)} — This region can no longer sustain its population</p>
            </div>

            {/* Final State */}
            <SectionTitle>Final State at Collapse</SectionTitle>
            <div className="grid grid-cols-2 gap-3">
                <div className="rounded-lg p-3 text-xs text-center"
                    style={{ background: 'rgba(255,255,255,0.04)', border: '1px solid rgba(255,255,255,0.08)' }}>
                    <p className="text-slate-400 mb-1">Population</p>
                    <p className="text-white font-bold text-sm">{finalPopulation || 'N/A'}</p>
                </div>
                <div className="rounded-lg p-3 text-xs text-center"
                    style={{ background: 'rgba(255,255,255,0.04)', border: '1px solid rgba(255,255,255,0.08)' }}>
                    <p className="text-slate-400 mb-1">Health Score</p>
                    <p className="text-white font-bold text-sm">{healthScore || 'N/A'}</p>
                </div>
            </div>

            {/* Root Cause */}
            <SectionTitle>Why Did This Happen?</SectionTitle>
            <div className="rounded-lg px-3 py-3 text-xs text-slate-300 leading-relaxed"
                style={{ background: 'rgba(239,68,68,0.06)', border: '1px solid rgba(239,68,68,0.15)' }}>
                {causeText}
            </div>

            {/* Real World Parallel */}
            <GlobeCard title="🌐 Real World Parallel">
                This collapse mirrors real-world state failure patterns — where resource exhaustion removes the economic foundation of governance,
                triggering population displacement and regional instability.
            </GlobeCard>
        </>
    );
}

// ─── HEADER ────────────────────────────────────────────────────────────────

const HEADER_CONFIG = {
    climate: { badge: '🌍 CLIMATE EVENT', bg: 'rgba(59,130,246,0.15)', border: 'rgba(59,130,246,0.4)', color: '#60a5fa' },
    conflict: { badge: '⚔️ CONFLICT EVENT', bg: 'rgba(239,68,68,0.15)', border: 'rgba(239,68,68,0.4)', color: '#f87171' },
    collapse: { badge: '💀 COLLAPSE EVENT', bg: 'rgba(107,114,128,0.15)', border: 'rgba(107,114,128,0.4)', color: '#9ca3af' },
};

export default function EventDetailModal({ event, onClose }) {
    // Escape key handler
    useEffect(() => {
        if (!event) return;
        const handler = (e) => {
            if (e.key === 'Escape') onClose();
        };
        window.addEventListener('keydown', handler);
        return () => window.removeEventListener('keydown', handler);
    }, [event, onClose]);

    // Lock body scroll
    useEffect(() => {
        if (!event) return;
        document.body.style.overflow = 'hidden';
        return () => {
            document.body.style.overflow = 'unset';
        };
    }, [event]);

    if (!event) return null;

    const hCfg = HEADER_CONFIG[event.type] || HEADER_CONFIG.climate;

    return (
        <div
            onClick={onClose}
            style={{
                position: 'fixed',
                inset: 0,
                background: 'rgba(0,0,0,0.75)',
                backdropFilter: 'blur(4px)',
                zIndex: 9999,
                display: 'flex',
                alignItems: 'center',
                justifyContent: 'center',
            }}
        >
            <div
                className="event-detail-modal-box"
                onClick={(e) => e.stopPropagation()}
                style={{
                    position: 'relative',
                    maxWidth: 480,
                    width: '90vw',
                    maxHeight: '85vh',
                    overflowY: 'auto',
                    background: '#0f172a',
                    border: '1px solid rgba(99,102,241,0.3)',
                    borderRadius: 16,
                    boxShadow: '0 25px 50px rgba(0,0,0,0.8)',
                    padding: 28,
                }}
            >
                {/* Header */}
                <div className="flex items-start justify-between gap-3 mb-4">
                    <div>
                        <span className="text-xs font-bold px-2 py-1 rounded-full"
                            style={{ background: hCfg.bg, border: `1px solid ${hCfg.border}`, color: hCfg.color }}>
                            {hCfg.badge}
                        </span>
                        <p className="text-white font-bold text-lg mt-2">
                            Year {displayYear(event.cycle)}
                        </p>
                    </div>
                    <button
                        onClick={onClose}
                        className="shrink-0 flex items-center justify-center text-slate-400 hover:text-white transition-colors"
                        style={{
                            width: 32,
                            height: 32,
                            borderRadius: '50%',
                            background: 'rgba(255,255,255,0.1)',
                        }}
                        aria-label="Close"
                    >
                        ✕
                    </button>
                </div>

                {/* Divider */}
                <div style={{ height: 1, background: 'rgba(255,255,255,0.08)', marginBottom: 16 }} />

                {/* Body — per type */}
                {event.type === 'climate' && <ClimateBody event={event} />}
                {event.type === 'conflict' && <ConflictBody event={event} />}
                {event.type === 'collapse' && <CollapseBody event={event} />}

                {/* Fallback for unknown types */}
                {!['climate', 'conflict', 'collapse'].includes(event.type) && (
                    <div className="py-4">
                        <p className="text-slate-300 text-sm">{event.description || 'No additional details available.'}</p>
                    </div>
                )}

                {/* Footer */}
                <p className="text-center text-xs text-slate-600 mt-6">
                    WorldSim · Year {displayYear(event.cycle)} · Click outside or press Esc to close
                </p>
            </div>
        </div>
    );
}
