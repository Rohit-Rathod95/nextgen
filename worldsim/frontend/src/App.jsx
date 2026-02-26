// Root React component — assembles all dashboard panels, map, and overlay components.
import React, { useState } from 'react';
import { useRegions, useWorldState, useEventsLog, useAnalysis, isFirebaseReady } from './services/firestore_listener';
import { GLOBAL_CONSTANTS } from './constants/regions_meta';
import Timeline from './components/Timeline';
import WorldMap from './components/WorldMap';
import RegionPanel from './components/RegionPanel';
import EventLog from './components/EventLog';
import AnalysisOverlay from './components/AnalysisOverlay';
import TradeDetailModal from './components/TradeDetailModal';

const { TOTAL_CYCLES } = GLOBAL_CONSTANTS;

export default function App() {
    const regions = useRegions();
    const worldState = useWorldState();
    const events = useEventsLog(60);
    const analysis = useAnalysis();

    const [selectedRegion, setSelectedRegion] = useState(null);
    const [showAnalysis, setShowAnalysis] = useState(false);
    const [selectedTrade, setSelectedTrade] = useState(null);

    // Auto-show analysis when simulation completes
    const simComplete = (worldState?.current_cycle ?? 0) >= TOTAL_CYCLES && !worldState?.is_running;

    // Derive active trades from recent events
    const activeTrades = events
        .filter((e) => e.type === 'trade' && e.regions_involved?.length >= 2)
        .slice(0, 6)
        .map((e) => ({
            from: e.regions_involved[0],
            to: e.regions_involved[1],
            resource: e.resource || 'water',
            volume: e.volume || 20,
        }));

    function handleSelectRegion(name) {
        setSelectedRegion((prev) => (prev === name ? null : name));
    }

    return (
        <div className="flex flex-col h-screen overflow-hidden bg-surface text-slate-100">

            {/* ═══ TIMELINE BAR ═══ */}
            <div className="shrink-0 px-4 pt-3 pb-2">
                <Timeline worldState={worldState} isFirebaseReady={isFirebaseReady} />
            </div>

            {/* ═══ MAIN 3-COLUMN GRID ═══ */}
            <div className="flex-1 grid grid-cols-[300px_1fr_280px] gap-3 px-4 pb-3 min-h-0">

                {/* ── LEFT: Region Panel ── */}
                <div className="glass rounded-xl p-4 overflow-hidden flex flex-col min-h-0">
                    <h3 className="text-sm font-semibold text-slate-200 tracking-wide mb-3 shrink-0">
                        REGION DETAIL
                    </h3>
                    <div className="flex-1 overflow-y-auto min-h-0">
                        <RegionPanel
                            region={selectedRegion ? regions[selectedRegion] : null}
                            regionName={selectedRegion}
                            onClose={() => setSelectedRegion(null)}
                        />
                    </div>
                </div>

                {/* ── CENTER: World Map ── */}
                <div className="glass rounded-xl overflow-hidden flex flex-col min-h-0">
                    <div className="flex-1 min-h-0">
                        <WorldMap
                            regions={regions}
                            selectedRegion={selectedRegion}
                            onRegionSelect={handleSelectRegion}
                            activeTrades={activeTrades}
                        />
                    </div>

                    {/* Bottom region quick-select strip */}
                    <div className="shrink-0 grid grid-cols-5 gap-0 border-t border-slate-800">
                        {Object.entries(regions).map(([name, region]) => {
                            const isSelected = selectedRegion === name;
                            return (
                                <button
                                    key={name}
                                    onClick={() => handleSelectRegion(name)}
                                    className={`py-2 text-xs font-medium transition-colors hover:bg-slate-800 ${isSelected ? 'bg-slate-800' : ''
                                        }`}
                                    style={{ color: isSelected ? '#e2e8f0' : '#64748b' }}
                                >
                                    <div className="text-center">
                                        <div className="text-base">
                                            {{ Aquaria: '💧', Agrovia: '🌾', Petrozon: '⚡', Urbanex: '🏙️', Terranova: '🌍' }[name] || '🌐'}
                                        </div>
                                        <div className="text-xs">{name}</div>
                                    </div>
                                </button>
                            );
                        })}
                    </div>
                </div>

                {/* ── RIGHT: Event Log ── */}
                <div className="glass rounded-xl p-4 overflow-hidden flex flex-col min-h-0">
                    <div className="flex-1 overflow-y-auto min-h-0">
                        <EventLog events={events} onTradeSelect={setSelectedTrade} />
                    </div>

                    {/* Analysis button */}
                    {(simComplete || analysis) && (
                        <div className="shrink-0 mt-3 pt-3 border-t border-slate-800">
                            <button
                                onClick={() => setShowAnalysis(true)}
                                className="w-full py-2 rounded-lg text-xs font-semibold transition-all"
                                style={{
                                    background: 'linear-gradient(135deg, #1d4ed820, #7c3aed20)',
                                    border: '1px solid #7c3aed50',
                                    color: '#a78bfa',
                                }}
                            >
                                📊 View Final Analysis
                            </button>
                        </div>
                    )}
                </div>
            </div>

            {/* ═══ TRADE DETAIL MODAL ═══ */}
            <TradeDetailModal
                trade={selectedTrade}
                onClose={() => setSelectedTrade(null)}
            />

            {/* ═══ ANALYSIS OVERLAY ═══ */}
            <AnalysisOverlay
                analysis={analysis}
                regions={regions}
                onClose={() => setShowAnalysis(false)}
                isVisible={showAnalysis}
            />
        </div>
    );
}
