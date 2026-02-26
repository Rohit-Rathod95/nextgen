// EventLog component — scrollable feed of simulation events (trades, conflicts, climate disasters).
import React, { useRef, useEffect } from 'react';

const TYPE_CONFIG = {
    climate: { icon: '🌪', color: '#f97316', bg: 'bg-orange-900/20', border: 'border-orange-700/30', label: 'CLIMATE' },
    trade: { icon: '🤝', color: '#38bdf8', bg: 'bg-sky-900/20', border: 'border-sky-700/30', label: 'TRADE' },
    conflict: { icon: '⚔️', color: '#ef4444', bg: 'bg-red-900/20', border: 'border-red-700/30', label: 'CONFLICT' },
};

function EventItem({ event, isNew }) {
    const cfg = TYPE_CONFIG[event.type] || {
        icon: '📋', color: '#94a3b8', bg: 'bg-slate-800/50', border: 'border-slate-700/30', label: 'EVENT',
    };

    return (
        <div
            className={`rounded-lg p-2.5 border ${cfg.bg} ${cfg.border} ${isNew ? 'event-enter' : ''} mb-2`}
        >
            <div className="flex items-start gap-2">
                <span className="text-base mt-0.5">{cfg.icon}</span>
                <div className="flex-1 min-w-0">
                    <div className="flex justify-between items-center gap-2 flex-wrap">
                        <span
                            className="text-xs font-mono font-semibold px-1.5 py-0.5 rounded"
                            style={{ background: `${cfg.color}20`, color: cfg.color }}
                        >
                            {cfg.label}
                        </span>
                        <span className="text-xs font-mono text-slate-500">
                            Cycle {event.cycle ?? '?'}
                        </span>
                    </div>
                    <p className="text-xs text-slate-300 mt-1 leading-relaxed">{event.description}</p>
                    {event.regions_involved && event.regions_involved.length > 0 && (
                        <div className="flex gap-1 mt-1 flex-wrap">
                            {event.regions_involved.map((r) => (
                                <span key={r} className="text-xs px-1.5 py-0.5 rounded bg-slate-700/50 text-slate-400">
                                    {r}
                                </span>
                            ))}
                        </div>
                    )}
                </div>
            </div>
        </div>
    );
}

export default function EventLog({ events }) {
    const bottomRef = useRef(null);
    const prevLen = useRef(0);

    // Scroll to top when new events arrive (newest at top since ordered desc)
    useEffect(() => {
        prevLen.current = events.length;
    }, [events]);

    const hasEvents = events && events.length > 0;

    return (
        <div className="flex flex-col h-full">
            <div className="flex justify-between items-center mb-3">
                <h3 className="text-sm font-semibold text-slate-200 tracking-wide">EVENT LOG</h3>
                {hasEvents && (
                    <span className="text-xs px-2 py-0.5 rounded-full bg-slate-700 text-slate-400 font-mono">
                        {events.length}
                    </span>
                )}
            </div>

            <div className="flex-1 overflow-y-auto">
                {!hasEvents ? (
                    <div className="flex flex-col items-center justify-center h-full text-slate-500 gap-3">
                        <span className="text-3xl">📋</span>
                        <p className="text-xs text-center">No events yet — simulation has not started</p>
                    </div>
                ) : (
                    events.map((ev, idx) => (
                        <EventItem key={ev.id || idx} event={ev} isNew={idx === 0} />
                    ))
                )}
                <div ref={bottomRef} />
            </div>
        </div>
    );
}
