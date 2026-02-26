// WorldMap component — renders the SVG interactive map of all 5 regions with health-score coloring.
import React, { useMemo } from 'react';
import { REGION_META, GLOBAL_CONSTANTS } from '../constants/regions_meta';
import TradeLines from './TradeLines';

const MAP_W = 600;
const MAP_H = 380;

// Interpolate color from green→yellow→red based on health 0..1
function healthColor(h) {
    if (h >= 0.6) {
        // green to yellow
        const t = (h - 0.6) / 0.4;
        const r = Math.round(74 + (234 - 74) * (1 - t));
        const g = Math.round(222);
        const b = Math.round(128 * t);
        return `rgb(${r},${g},${b})`;
    }
    if (h >= 0.3) {
        // yellow to orange
        const t = (h - 0.3) / 0.3;
        return `rgb(${Math.round(234 + (253 - 234) * (1 - t))},${Math.round(179 + (222 - 179) * t)},20)`;
    }
    // orange to red
    const t = h / 0.3;
    return `rgb(${Math.round(239)},${Math.round(68 + 111 * t)},${Math.round(68 - 48 * t)})`;
}

// Hexagon path around a center point
function hexPath(cx, cy, r) {
    const pts = [];
    for (let i = 0; i < 6; i++) {
        const a = (Math.PI / 180) * (60 * i - 30);
        pts.push(`${cx + r * Math.cos(a)},${cy + r * Math.sin(a)}`);
    }
    return `M ${pts.join(' L ')} Z`;
}

export default function WorldMap({ regions, selectedRegion, onSelectRegion, lastEvents }) {
    const eventRegion = useMemo(() => {
        if (!lastEvents || lastEvents.length === 0) return null;
        const latest = lastEvents[0];
        if (latest.type === 'climate' && latest.regions_involved?.length > 0) {
            return latest.regions_involved[0];
        }
        return null;
    }, [lastEvents]);

    return (
        <div className="relative w-full h-full flex items-center justify-center">
            <svg
                viewBox={`0 0 ${MAP_W} ${MAP_H}`}
                className="w-full h-full"
                style={{ maxHeight: '100%' }}
            >
                {/* Background grid */}
                <defs>
                    <pattern id="grid" width="30" height="30" patternUnits="userSpaceOnUse">
                        <path d="M 30 0 L 0 0 0 30" fill="none" stroke="rgba(51,65,85,0.3)" strokeWidth="0.5" />
                    </pattern>
                    <radialGradient id="bgGrad" cx="50%" cy="50%" r="70%">
                        <stop offset="0%" stopColor="#1e293b" />
                        <stop offset="100%" stopColor="#0f172a" />
                    </radialGradient>
                    <filter id="glow">
                        <feGaussianBlur stdDeviation="3" result="coloredBlur" />
                        <feMerge>
                            <feMergeNode in="coloredBlur" />
                            <feMergeNode in="SourceGraphic" />
                        </feMerge>
                    </filter>
                </defs>

                <rect width={MAP_W} height={MAP_H} fill="url(#bgGrad)" rx="12" />
                <rect width={MAP_W} height={MAP_H} fill="url(#grid)" rx="12" />

                {/* Connection lines (faint background) */}
                {Object.entries(REGION_META).map(([nameA, metaA]) =>
                    Object.entries(REGION_META).map(([nameB, metaB]) => {
                        if (nameA >= nameB) return null;
                        return (
                            <line
                                key={`${nameA}-${nameB}-bg`}
                                x1={metaA.cx} y1={metaA.cy}
                                x2={metaB.cx} y2={metaB.cy}
                                stroke="rgba(51,65,85,0.25)"
                                strokeWidth="1"
                                strokeDasharray="4 6"
                            />
                        );
                    })
                )}

                {/* Trade / conflict animated lines */}
                <TradeLines lastEvents={lastEvents} />

                {/* Region nodes */}
                {Object.entries(regions).map(([name, region]) => {
                    const meta = REGION_META[name];
                    if (!meta) return null;
                    const health = region.health_score ?? 0.5;
                    const hc = healthColor(health);
                    const isSelected = selectedRegion === name;
                    const isClimate = eventRegion === name;
                    const collapsed = (region.population ?? 999) < GLOBAL_CONSTANTS.COLLAPSE_THRESHOLD_POPULATION;
                    const R = 36;

                    return (
                        <g
                            key={name}
                            onClick={() => onSelectRegion(name)}
                            style={{ cursor: 'pointer' }}
                        >
                            {/* Climate pulse ring */}
                            {isClimate && (
                                <circle
                                    cx={meta.cx} cy={meta.cy} r={R + 4}
                                    fill="none"
                                    stroke="#f97316"
                                    strokeWidth="2"
                                    className="ping-ring"
                                    opacity="0.8"
                                />
                            )}

                            {/* Selection ring */}
                            {isSelected && (
                                <circle
                                    cx={meta.cx} cy={meta.cy} r={R + 8}
                                    fill="none"
                                    stroke={meta.color}
                                    strokeWidth="2"
                                    strokeDasharray="6 3"
                                    opacity="0.9"
                                />
                            )}

                            {/* Hex background */}
                            <path
                                d={hexPath(meta.cx, meta.cy, R)}
                                fill={collapsed ? '#1e293b' : `${meta.color}18`}
                                stroke={isSelected ? meta.color : `${meta.color}66`}
                                strokeWidth={isSelected ? 2.5 : 1.5}
                                filter="url(#glow)"
                            />

                            {/* Inner hex with health color */}
                            <path
                                d={hexPath(meta.cx, meta.cy, R * 0.65)}
                                fill={collapsed ? '#ef444433' : `${hc}33`}
                                stroke={collapsed ? '#ef4444' : hc}
                                strokeWidth="1.5"
                            />

                            {/* Icon */}
                            <text
                                x={meta.cx} y={meta.cy - 4}
                                textAnchor="middle"
                                dominantBaseline="middle"
                                fontSize="18"
                            >
                                {collapsed ? '💀' : meta.icon}
                            </text>

                            {/* Region name */}
                            <text
                                x={meta.cx} y={meta.cy + R + 14}
                                textAnchor="middle"
                                fontSize="11"
                                fontWeight="600"
                                fontFamily="Inter, sans-serif"
                                fill={meta.color}
                                letterSpacing="0.5"
                            >
                                {name.toUpperCase()}
                            </text>

                            {/* Population badge */}
                            <g>
                                <rect
                                    x={meta.cx - 22} y={meta.cy + R + 23}
                                    width="44" height="14"
                                    rx="7"
                                    fill={collapsed ? '#ef444422' : '#1e293b'}
                                    stroke={collapsed ? '#ef4444' : '#475569'}
                                    strokeWidth="0.5"
                                />
                                <text
                                    x={meta.cx} y={meta.cy + R + 32}
                                    textAnchor="middle"
                                    fontSize="9"
                                    fontFamily="JetBrains Mono, monospace"
                                    fill={collapsed ? '#ef4444' : '#94a3b8'}
                                >
                                    {`👥 ${Math.round(region.population ?? 0)}`}
                                </text>
                            </g>

                            {/* Health bar */}
                            <rect
                                x={meta.cx - 22} y={meta.cy + R + 40}
                                width="44" height="4"
                                rx="2"
                                fill="#1e293b"
                            />
                            <rect
                                x={meta.cx - 22} y={meta.cy + R + 40}
                                width={`${Math.max(0, Math.min(1, health)) * 44}`}
                                height="4"
                                rx="2"
                                fill={hc}
                            />
                        </g>
                    );
                })}

                {/* Title */}
                <text x="12" y="22" fontSize="11" fill="#475569" fontFamily="Inter, sans-serif" fontWeight="500">
                    WORLD MAP  •  {Object.keys(regions).length} REGIONS
                </text>
            </svg>
        </div>
    );
}
