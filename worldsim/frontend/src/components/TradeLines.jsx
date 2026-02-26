import React from 'react';
import { useActiveTrades } from '../services/firestore_listener';

// Renders all active trade relationships as animated SVG arcs.  A "strong"
// relationship (>=3 successful trades in the last 3 cycles) appears as a thick
// solid green line with a moving dot and optional count badge.  Weaker pairs
// are thin dashed light-green lines.
//
// regionPositions must map lowercase region IDs to {x,y} pixel positions on
// the same SVG canvas. TradeLines does not compute any projections itself.

const TradeLines = ({ regionPositions }) => {
    const activeTrades = useActiveTrades();

    if (!activeTrades || activeTrades.length === 0) {
        return null;
    }

    return (
        <g className="trade-lines">
            {activeTrades.map((trade, index) => {
                const srcPos = regionPositions[trade.source];
                const tgtPos = regionPositions[trade.target];
                if (!srcPos || !tgtPos) return null;

                const key = `${trade.source}__${trade.target}__${index}`;
                const isStrong = trade.count >= 3;

                const midX = (srcPos.x + tgtPos.x) / 2;
                const midY = (srcPos.y + tgtPos.y) / 2;
                const dx = tgtPos.x - srcPos.x;
                const dy = tgtPos.y - srcPos.y;
                const curvature = isStrong ? 0.25 : 0.15;
                const cpX = midX - dy * curvature;
                const cpY = midY + dx * curvature;

                const pathD = `M ${srcPos.x} ${srcPos.y} Q ${cpX} ${cpY} ${tgtPos.x} ${tgtPos.y}`;
                const strokeColor = isStrong ? '#22c55e' : '#86efac';
                const strokeWidth = isStrong ? 2.5 : 1.5;
                const strokeOpacity = isStrong ? 0.85 : 0.55;
                const dashArray = isStrong ? 'none' : '4,3';

                return (
                    <g key={key}>
                        <path
                            d={pathD}
                            fill="none"
                            stroke={strokeColor}
                            strokeWidth={strokeWidth}
                            strokeOpacity={strokeOpacity}
                            strokeDasharray={dashArray}
                        />

                        <circle r="3" fill={strokeColor} opacity="0.9">
                            <animateMotion
                                dur={`${1.5 + index * 0.2}s`}
                                repeatCount="indefinite"
                                path={pathD}
                            />
                        </circle>

                        <text
                            x={cpX}
                            y={cpY - 6}
                            fill="#86efac"
                            fontSize="8"
                            textAnchor="middle"
                            opacity="0.7"
                        >
                            {trade.count > 1 ? `×${trade.count}` : ''}
                        </text>
                    </g>
                );
            })}
        </g>
    );
};

export default TradeLines;
