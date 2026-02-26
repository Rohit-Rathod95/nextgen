import React, { useMemo, useState, useCallback } from 'react';
import { ComposableMap, Geographies, Geography, Marker } from 'react-simple-maps';
import { GLOBAL_CONSTANTS } from '../constants/regions_meta';
import TradeLines from './TradeLines';

const GEO_URL = 'https://cdn.jsdelivr.net/npm/world-atlas@2/countries-110m.json';

// ─── Territory Definitions (numeric ISO 3166-1 IDs used by world-atlas geo.id) ──
const REGION_TERRITORIES = {
    Aquaria: {
        color: '#00cfff', glow: 'rgba(0,207,255,0.5)', bg: 'rgba(0,207,255,0.12)',
        // MAR MRT SEN GMB GNB GIN SLE LBR CIV GHA TGO BEN NGA
        ids: new Set([504, 478, 686, 270, 624, 324, 694, 430, 384, 288, 768, 204, 566]),
    },
    Agrovia: {
        color: '#00ff88', glow: 'rgba(0,255,136,0.5)', bg: 'rgba(0,255,136,0.12)',
        // IND BGD LKA NPL BTN PAK MMR THA KHM VNM LAO MYS IDN PHL
        ids: new Set([356, 50, 144, 524, 64, 586, 104, 764, 116, 704, 418, 458, 360, 608]),
    },
    Petrozon: {
        color: '#ff9500', glow: 'rgba(255,149,0,0.5)', bg: 'rgba(255,149,0,0.12)',
        // SAU IRQ IRN KWT ARE QAT OMN YEM BHR JOR SYR TUR
        ids: new Set([682, 368, 364, 414, 784, 634, 512, 887, 48, 400, 760, 792]),
    },
    Urbanex: {
        color: '#cc44ff', glow: 'rgba(204,68,255,0.5)', bg: 'rgba(204,68,255,0.12)',
        // CHN KOR JPN MNG PRK KAZ UZB KGZ TJK TKM
        ids: new Set([156, 410, 392, 496, 408, 398, 860, 417, 762, 795]),
    },
    Terranova: {
        color: '#ffdd00', glow: 'rgba(255,221,0,0.5)', bg: 'rgba(255,221,0,0.12)',
        // BRA BOL PRY URY ARG CHL PER COL VEN ECU GUY SUR
        ids: new Set([76, 68, 600, 858, 32, 152, 604, 170, 862, 218, 328, 740]),
    },
};

const REGION_ICONS = {
    Aquaria: '💧', Agrovia: '🌾', Petrozon: '⚡', Urbanex: '🏙️', Terranova: '🌍',
};

// ─── Region Pin Config ───────────────────────────────────────────────────────
const REGION_CONFIG = {
    Aquaria: { coordinates: [-20.0, -35.0], dominant: 'Water Dominant', labelDx: 0, labelDy: 32, anchor: 'middle' },
    Agrovia: { coordinates: [78.0, 20.0], dominant: 'Food Dominant', labelDx: 0, labelDy: -32, anchor: 'middle' },
    Petrozon: { coordinates: [45.0, 28.0], dominant: 'Energy Dominant', labelDx: 0, labelDy: 32, anchor: 'middle' },
    Urbanex: { coordinates: [118.0, 32.0], dominant: 'Population Heavy', labelDx: 26, labelDy: 0, anchor: 'start' },
    Terranova: { coordinates: [-52.0, -15.0], dominant: 'Land Rich', labelDx: 0, labelDy: 32, anchor: 'middle' },
};

const RESOURCE_COLORS = { water: '#00cfff', food: '#00ff88', energy: '#ff9500', land: '#ffdd00' };
const { MAX_RESOURCE } = GLOBAL_CONSTANTS;
const STATUS_COLORS = { healthy: '#4ade80', stressed: '#f59e0b', critical: '#ef4444' };

function getHealth(region) {
    if (!region) return 0.5;
    const avg = ['water', 'food', 'energy', 'land'].reduce((s, k) => s + (region[k] ?? 0), 0) / 4;
    return avg / MAX_RESOURCE;
}
function getStatus(h) { return h >= 0.45 ? 'healthy' : h >= 0.20 ? 'stressed' : 'critical'; }

// ─── Territory pulse CSS keyframe (injected once) ────────────────────────────
const PULSE_STYLE = `
  @keyframes territoryPulse {
    0%,100% { fill-opacity: 0.27; }
    50%      { fill-opacity: 0.48; }
  }
`;

// ─── Main Component ──────────────────────────────────────────────────────────
export default function WorldMap({ regions, activeTrades, onRegionSelect, selectedRegion }) {
    const [hoveredRegion, setHoveredRegion] = useState(null);
    const [mousePos, setMousePos] = useState({ x: 0, y: 0 });

    const tradesArray = useMemo(() => (activeTrades || []).slice(0, 8), [activeTrades]);
    const activeTradeCount = tradesArray.length;
    const anySelected = !!selectedRegion;

    // O(1) country→region lookup keyed on numeric geo.id
    const countryToRegion = useMemo(() => {
        const map = new Map();
        Object.entries(REGION_TERRITORIES).forEach(([regionId, data]) => {
            data.ids.forEach((numId) => map.set(String(numId), { regionId, ...data }));
        });
        return map;
    }, []);

    const handlePinClick = useCallback((name, e) => {
        e.stopPropagation();
        onRegionSelect(selectedRegion === name ? null : name);
    }, [selectedRegion, onRegionSelect]);

    const handleMapClick = useCallback(() => {
        if (anySelected) onRegionSelect(null);
    }, [anySelected, onRegionSelect]);

    function handleMouseMove(e) {
        const rect = e.currentTarget.getBoundingClientRect();
        setMousePos({ x: e.clientX - rect.left, y: e.clientY - rect.top });
    }

    return (
        <div style={{
            width: '100%', height: '100%', display: 'flex', flexDirection: 'column',
            background: '#060d1a', borderRadius: 12, overflow: 'hidden',
            border: '1px solid rgba(0,207,255,0.15)',
            boxShadow: 'inset 0 0 60px rgba(6,13,26,0.8)',
        }}>
            <style>{PULSE_STYLE}</style>

            {/* ── Header ─────────────────────────────────────────────────────── */}
            <div style={{
                display: 'flex', justifyContent: 'space-between', alignItems: 'center',
                padding: '8px 16px', background: 'rgba(6,13,26,0.9)',
                borderBottom: '1px solid rgba(30,64,96,0.5)', flexShrink: 0,
                fontFamily: 'Inter, sans-serif',
            }}>
                <span style={{ fontSize: 10, color: '#4a7fa5', letterSpacing: 1.2, fontWeight: 600 }}>
                    WORLD MAP  •  5 REGIONS
                </span>
                {activeTradeCount > 0 ? (
                    <span style={{ fontSize: 10, fontFamily: 'monospace', color: '#00ff88', letterSpacing: 1, display: 'flex', alignItems: 'center', gap: 5 }}>
                        <span style={{ display: 'inline-block', width: 7, height: 7, borderRadius: '50%', background: '#00ff88', boxShadow: '0 0 8px #00ff88', animation: 'pulse 1.5s ease-in-out infinite' }} />
                        {activeTradeCount} ACTIVE TRADE{activeTradeCount !== 1 ? 'S' : ''}
                    </span>
                ) : (
                    <span style={{ fontSize: 10, fontFamily: 'monospace', color: '#ff2244', letterSpacing: 1 }}>✗ NO ACTIVE TRADES</span>
                )}
            </div>

            {/* ── Map Canvas ──────────────────────────────────────────────────── */}
            <div
                style={{ flex: 1, position: 'relative', overflow: 'hidden', minHeight: 0 }}
                onClick={handleMapClick}
                onMouseMove={handleMouseMove}
            >
                {/* Vignette */}
                <div style={{ position: 'absolute', inset: 0, zIndex: 10, pointerEvents: 'none', boxShadow: 'inset 0 0 80px rgba(6,13,26,0.75)' }} />

                {/* Hover tooltip */}
                {hoveredRegion && (
                    <div style={{
                        position: 'absolute',
                        left: mousePos.x + 14,
                        top: mousePos.y - 36,
                        zIndex: 50,
                        pointerEvents: 'none',
                        background: 'rgba(6,13,26,0.92)',
                        border: `1px solid ${REGION_TERRITORIES[hoveredRegion]?.color}55`,
                        borderRadius: 8,
                        padding: '5px 10px',
                        display: 'flex', alignItems: 'center', gap: 6,
                        backdropFilter: 'blur(10px)',
                        boxShadow: `0 4px 16px ${REGION_TERRITORIES[hoveredRegion]?.color}30`,
                    }}>
                        <span style={{ fontSize: 13 }}>{REGION_ICONS[hoveredRegion]}</span>
                        <span style={{ fontFamily: 'JetBrains Mono, monospace', fontSize: 10, color: REGION_TERRITORIES[hoveredRegion]?.color, fontWeight: 700, letterSpacing: 1 }}>
                            {hoveredRegion.toUpperCase()}
                        </span>
                        <span style={{ fontSize: 9, color: '#4a7fa5', fontFamily: 'monospace' }}>· click to select</span>
                    </div>
                )}

                <ComposableMap
                    projection="geoMercator"
                    projectionConfig={{ center: [10, 10], scale: 155 }}
                    style={{ width: '100%', height: '100%', display: 'block' }}
                >
                    <defs>
                        {/* Per-region glow filters */}
                        {Object.entries(REGION_TERRITORIES).map(([regionId]) => (
                            <filter key={regionId} id={`glow-${regionId}`} x="-20%" y="-20%" width="140%" height="140%">
                                <feGaussianBlur stdDeviation="3" result="coloredBlur" />
                                <feMerge>
                                    <feMergeNode in="coloredBlur" />
                                    <feMergeNode in="SourceGraphic" />
                                </feMerge>
                            </filter>
                        ))}
                        {/* Strong glow for selected territory */}
                        <filter id="glow-selected" x="-30%" y="-30%" width="160%" height="160%">
                            <feGaussianBlur stdDeviation="5" result="coloredBlur" />
                            <feMerge>
                                <feMergeNode in="coloredBlur" />
                                <feMergeNode in="coloredBlur" />
                                <feMergeNode in="SourceGraphic" />
                            </feMerge>
                        </filter>
                        {/* Pin glow filters */}
                        <filter id="pinGlow" x="-80%" y="-80%" width="260%" height="260%">
                            <feGaussianBlur stdDeviation="2.5" result="blur" />
                            <feMerge><feMergeNode in="blur" /><feMergeNode in="SourceGraphic" /></feMerge>
                        </filter>
                        <filter id="pinGlowSelected" x="-80%" y="-80%" width="260%" height="260%">
                            <feGaussianBlur stdDeviation="4" result="blur" />
                            <feMerge><feMergeNode in="blur" /><feMergeNode in="SourceGraphic" /></feMerge>
                        </filter>
                        <radialGradient id="oceanGrad" cx="50%" cy="50%" r="70%">
                            <stop offset="0%" stopColor="#071428" />
                            <stop offset="100%" stopColor="#060d1a" />
                        </radialGradient>
                    </defs>

                    {/* Ocean */}
                    <rect x="-10000" y="-10000" width="20000" height="20000" fill="url(#oceanGrad)" />

                    <Geographies geography={GEO_URL}>
                        {({ geographies }) =>
                            geographies.map((geo) => {
                                // world-atlas encodes country as numeric ISO in geo.id
                                const numId = String(geo.id);
                                const match = countryToRegion.get(numId);

                                if (!match) {
                                    return (
                                        <Geography key={geo.rsmKey} geography={geo}
                                            fill={anySelected ? '#08141f' : '#0f2235'}
                                            stroke="#1e4060"
                                            strokeWidth={0.3}
                                            style={{ default: { outline: 'none' }, hover: { outline: 'none' }, pressed: { outline: 'none' } }}
                                        />
                                    );
                                }

                                const { color, regionId } = match;
                                const isThisSelected = selectedRegion === regionId;
                                const isDimmed = anySelected && !isThisSelected;
                                const isHov = hoveredRegion === regionId;

                                // Fill opacity: selected=55%, normal=30%, dimmed=10%, hovered=45%
                                const fillAlpha = isThisSelected ? 'cc'
                                    : isDimmed ? '1a'
                                        : isHov ? '73'
                                            : '4d';  // hex: cc=80% 1a=10% 73=45% 4d=30%

                                const strokeAlpha = isThisSelected ? 'cc' : isDimmed ? '40' : 'cc';
                                const strokeW = isThisSelected ? 1.2 : isDimmed ? 0.3 : 0.5;

                                return (
                                    <Geography
                                        key={geo.rsmKey}
                                        geography={geo}
                                        fill={`${color}${fillAlpha}`}
                                        stroke={`${color}${strokeAlpha}`}
                                        strokeWidth={strokeW}
                                        onClick={(e) => {
                                            e.stopPropagation();
                                            onRegionSelect(selectedRegion === regionId ? null : regionId);
                                        }}
                                        onMouseEnter={() => setHoveredRegion(regionId)}
                                        onMouseLeave={() => setHoveredRegion(null)}
                                        style={{
                                            default: { outline: 'none', cursor: 'pointer' },
                                            hover: { outline: 'none', cursor: 'pointer', fill: `${color}73` },
                                            pressed: { outline: 'none' },
                                        }}
                                    />
                                );
                            })
                        }
                    </Geographies>

                    {/* ── Animated Trade Arcs ─────────────────────────────────────── */}
                    <TradeLines lastEvents={activeTrades} />

                    {/* ── Region Pins ─────────────────────────────────────────────── */}
                    {Object.entries(REGION_CONFIG).map(([name, cfg]) => {
                        const rc = REGION_TERRITORIES[name];
                        const region = regions?.[name];
                        const health = getHealth(region);
                        const status = getStatus(health);
                        const dotColor = STATUS_COLORS[status];
                        const isSelected = selectedRegion === name;
                        const pinOpacity = anySelected ? (isSelected ? 1 : 0.42) : 1;
                        const pop = region?.population ?? 0;

                        const bodyR = isSelected ? 26 : 20;
                        const strokeW = isSelected ? 3.5 : 2.5;
                        const bodyFill = isSelected ? `${rc.color}59` : rc.bg;

                        return (
                            <Marker key={name} coordinates={cfg.coordinates}>
                                <g
                                    onClick={(e) => handlePinClick(name, e)}
                                    style={{ cursor: 'pointer', opacity: pinOpacity, transition: 'opacity 0.3s ease' }}
                                    filter={isSelected ? 'url(#pinGlowSelected)' : 'url(#pinGlow)'}
                                >
                                    {/* Scale wrapper */}
                                    <g transform={isSelected ? 'scale(1.25)' : 'scale(1)'}
                                        style={{ transformOrigin: '0 0', transition: 'transform 0.3s cubic-bezier(0.34,1.56,0.64,1)' }}>

                                        {/* Outer pulse ring */}
                                        <circle r={bodyR + 6} fill="none" stroke={rc.color} strokeWidth={1.2} opacity={0}>
                                            <animate attributeName="r" from={bodyR} to={bodyR + 14} dur="2.5s" repeatCount="indefinite" />
                                            <animate attributeName="opacity" from={0.55} to={0} dur="2.5s" repeatCount="indefinite" />
                                        </circle>

                                        {/* Critical fast pulse */}
                                        {status === 'critical' && (
                                            <circle r={bodyR + 6} fill="none" stroke="#ef4444" strokeWidth={2} opacity={0}>
                                                <animate attributeName="r" from={bodyR - 2} to={bodyR + 10} dur="0.85s" repeatCount="indefinite" />
                                                <animate attributeName="opacity" from={0.8} to={0} dur="0.85s" repeatCount="indefinite" />
                                            </circle>
                                        )}

                                        {/* Selected: dashed rotating white ring */}
                                        {isSelected && (
                                            <circle r={34} fill="none" stroke="white" strokeWidth={1.2} strokeDasharray="7 4" opacity={0.35}>
                                                <animateTransform attributeName="transform" type="rotate" from="0 0 0" to="360 0 0" dur="4s" repeatCount="indefinite" />
                                            </circle>
                                        )}

                                        {/* Pin body */}
                                        <circle r={bodyR} fill={bodyFill} stroke={rc.color} strokeWidth={strokeW}
                                            style={{ filter: `drop-shadow(0 0 ${isSelected ? '20px' : '8px'} ${rc.glow})` }}
                                        />

                                        {/* Teardrop tail */}
                                        <polygon points={`0,${bodyR} -5,${bodyR + 9} 5,${bodyR + 9}`}
                                            fill={rc.color} opacity={isSelected ? 0.95 : 0.75} />

                                        {/* Icon */}
                                        <text textAnchor="middle" dominantBaseline="central" y={0}
                                            style={{ fontSize: 16, userSelect: 'none', pointerEvents: 'none' }}>
                                            {REGION_ICONS[name]}
                                        </text>

                                        {/* Status dot */}
                                        <circle cx={isSelected ? 18 : 14} cy={isSelected ? -18 : -14}
                                            r={isSelected ? 6 : 5} fill={dotColor} stroke="#060d1a" strokeWidth={1.5}
                                            style={{ filter: `drop-shadow(0 0 5px ${dotColor})` }}
                                        />

                                        {/* Trade orbit dots */}
                                        {tradesArray
                                            .filter((t) => t.from === name || t.to === name)
                                            .slice(0, 4)
                                            .map((t, idx, arr) => {
                                                const angle = (idx / Math.max(arr.length, 1)) * Math.PI * 2;
                                                const dc = RESOURCE_COLORS[t.resource] || '#94a3b8';
                                                const orbitR = bodyR + 8;
                                                return (
                                                    <circle key={`orbit-${idx}`}
                                                        cx={Math.cos(angle) * orbitR} cy={Math.sin(angle) * orbitR}
                                                        r={3} fill={dc} opacity={0.9}
                                                        style={{ filter: `drop-shadow(0 0 4px ${dc})` }}
                                                    />
                                                );
                                            })}
                                    </g>

                                    {/* Labels (outside scale) */}
                                    {isSelected ? (
                                        <g>
                                            <rect x={cfg.labelDx - 34} y={cfg.labelDy - 11} width={68} height={16} rx={4}
                                                fill={`${rc.color}40`} stroke={rc.color} strokeWidth={0.8} />
                                            <text dx={cfg.labelDx} dy={cfg.labelDy} textAnchor={cfg.anchor}
                                                style={{ fontFamily: 'JetBrains Mono, monospace', fontSize: 12, fill: '#ffffff', fontWeight: 700, letterSpacing: 1.5, textShadow: `0 0 10px ${rc.color}`, pointerEvents: 'none', userSelect: 'none' }}>
                                                {name.toUpperCase()}
                                            </text>
                                        </g>
                                    ) : (
                                        <text dx={cfg.labelDx} dy={cfg.labelDy} textAnchor={cfg.anchor}
                                            style={{ fontFamily: 'JetBrains Mono, monospace', fontSize: 10, fill: rc.color, fontWeight: 700, letterSpacing: 1.5, textShadow: `0 0 10px ${rc.color}, 0 0 4px #060d1a`, pointerEvents: 'none', userSelect: 'none' }}>
                                            {name.toUpperCase()}
                                        </text>
                                    )}

                                    {/* Population */}
                                    <text dx={cfg.labelDx} dy={cfg.labelDy + 15} textAnchor={cfg.anchor}
                                        style={{ fontFamily: 'monospace', fontSize: 8.5, fill: isSelected ? '#ffffff' : 'rgba(255,255,255,0.55)', textShadow: '0 0 6px #060d1a', pointerEvents: 'none', userSelect: 'none' }}>
                                        {`👥 ${Math.round(pop)}`}
                                    </text>
                                </g>
                            </Marker>
                        );
                    })}
                </ComposableMap>
            </div>

            {/* ── Legend Bar ──────────────────────────────────────────────────── */}
            <div style={{
                display: 'flex', alignItems: 'center', padding: '7px 16px',
                background: 'rgba(6,13,26,0.9)', borderTop: '1px solid rgba(30,64,96,0.4)',
                flexShrink: 0, gap: 14, flexWrap: 'wrap',
            }}>
                {/* Region territory swatches */}
                {Object.entries(REGION_TERRITORIES).map(([name, rc]) => (
                    <div key={name}
                        onClick={() => onRegionSelect(selectedRegion === name ? null : name)}
                        style={{ display: 'flex', alignItems: 'center', gap: 5, cursor: 'pointer' }}>
                        <div style={{
                            width: 10, height: 10, borderRadius: 2,
                            background: `${rc.color}66`,
                            border: `1px solid ${rc.color}`,
                            boxShadow: selectedRegion === name ? `0 0 10px ${rc.color}` : `0 0 4px ${rc.color}50`,
                            transition: 'box-shadow 0.2s ease',
                        }} />
                        <span style={{
                            fontSize: 9, letterSpacing: 1, fontFamily: 'JetBrains Mono, monospace',
                            color: selectedRegion === name ? rc.color : '#4a7fa5',
                            fontWeight: selectedRegion === name ? 700 : 400,
                            transition: 'color 0.2s ease',
                        }}>
                            {name.toUpperCase()}
                        </span>
                    </div>
                ))}

                <span style={{ marginLeft: 'auto', fontSize: 9, color: '#2a3448', fontFamily: 'monospace', whiteSpace: 'nowrap' }}>
                    Click territory or pin to select region
                </span>
            </div>
        </div>
    );
}
