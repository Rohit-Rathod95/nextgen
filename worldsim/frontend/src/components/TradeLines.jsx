// TradeLines component — animated arcs showing active trade routes and conflicts between regions.
import React, { useMemo } from 'react';
import { REGION_META } from '../constants/regions_meta';

function curvedPath(x1, y1, x2, y2) {
    const mx = (x1 + x2) / 2;
    const my = (y1 + y2) / 2 - 50;
    return `M ${x1} ${y1} Q ${mx} ${my} ${x2} ${y2}`;
}

export default function TradeLines({ lastEvents }) {
    const lines = useMemo(() => {
        if (!lastEvents || lastEvents.length === 0) return [];
        const result = [];
        // Only show events from the last 3 cycles
        const recentEvents = lastEvents.slice(0, 10);
        recentEvents.forEach((ev) => {
            if (!ev.regions_involved || ev.regions_involved.length < 2) return;
            const [a, b] = ev.regions_involved;
            const metaA = REGION_META[a];
            const metaB = REGION_META[b];
            if (!metaA || !metaB) return;
            result.push({
                key: `${ev.id || Math.random()}`,
                x1: metaA.cx, y1: metaA.cy,
                x2: metaB.cx, y2: metaB.cy,
                type: ev.type,
            });
        });
        return result;
    }, [lastEvents]);

    return (
        <>
            <defs>
                <marker id="arrow-trade" markerWidth="6" markerHeight="6" refX="3" refY="3" orient="auto">
                    <path d="M0,0 L0,6 L6,3 Z" fill="#38bdf8" />
                </marker>
                <marker id="arrow-conflict" markerWidth="6" markerHeight="6" refX="3" refY="3" orient="auto">
                    <path d="M0,0 L0,6 L6,3 Z" fill="#ef4444" />
                </marker>
                {/* Animated dash */}
                <style>{`
          @keyframes dashMove {
            to { stroke-dashoffset: -24; }
          }
          .trade-line { animation: dashMove 1s linear infinite; }
          .conflict-line { animation: dashMove 0.6s linear infinite; }
        `}</style>
            </defs>

            {lines.map((l) => {
                const isTrade = l.type === 'trade';
                const isConflict = l.type === 'conflict';
                const color = isTrade ? '#38bdf8' : isConflict ? '#ef4444' : '#94a3b8';
                const cls = isTrade ? 'trade-line' : isConflict ? 'conflict-line' : '';
                const marker = isTrade ? 'url(#arrow-trade)' : isConflict ? 'url(#arrow-conflict)' : undefined;

                return (
                    <path
                        key={l.key}
                        d={curvedPath(l.x1, l.y1, l.x2, l.y2)}
                        fill="none"
                        stroke={color}
                        strokeWidth={isTrade ? 2 : 2.5}
                        strokeDasharray={isTrade ? '8 6' : '4 4'}
                        opacity="0.75"
                        markerEnd={marker}
                        className={cls}
                    />
                );
            })}
        </>
    );
}
