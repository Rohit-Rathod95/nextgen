// Region ID -> display label with real-world mapping
const REAL_WORLD_LABELS = {
    aquaria: 'Aquaria (Brazil)',
    agrovia: 'Agrovia (India)',
    petrozon: 'Petrozon (Gulf States)',
    urbanex: 'Urbanex (China)',
    terranova: 'Terranova (Africa)',
};

const getLabel = (regionId) =>
    REAL_WORLD_LABELS[regionId?.toLowerCase()] || regionId;

function InsightCard({ text, index }) {
    const colors = ['#38bdf8', '#4ade80', '#f59e0b', '#c084fc', '#f87171', '#34d399'];
    const c = colors[index % colors.length];
    return (
        <div
            className="rounded-lg p-3 border text-sm text-slate-300 leading-relaxed"
            style={{ background: `${c}08`, borderColor: `${c}30` }}
        >
            <span className="font-mono text-xs mr-2" style={{ color: c }}>
                #{index + 1}
            </span>
            {text}
        </div>
    );
}

function CollapseCard({ region, index }) {
    const colors = ['#ef4444', '#f97316', '#f59e0b', '#ec4899', '#a78bfa'];
    const c = colors[index % colors.length];

    const name = typeof region === 'string'
        ? region
        : (region.region_id || region.region || 'Unknown');
    const cause = typeof region === 'object' ? region.cause : null;
    const cycle = typeof region === 'object' ? region.collapse_cycle : null;

    return (
        <div
            className="rounded-lg p-3 border"
            style={{ background: '#ef444408', borderColor: '#ef444430' }}
        >
            <div className="flex items-center gap-2 flex-wrap">
                <span className="text-sm px-2 py-0.5 rounded font-mono bg-red-900/30 text-red-400">
                    💀 {getLabel(name)}
                </span>
                {cycle && (
                    <span className="text-xs text-slate-500 font-mono">cycle {cycle}</span>
                )}
            </div>
            {cause && (
                <p className="text-xs text-slate-400 mt-1.5">{cause}</p>
            )}
        </div>
    );
}

function ClusterBadge({ cluster, index }) {
    const colors = ['#38bdf8', '#4ade80', '#f59e0b', '#c084fc', '#f87171'];
    const c = colors[index % colors.length];

    // cluster may be an array of region IDs or { regions: [...], formed_at, duration }
    let members = [];
    let formedAt = null;
    let duration = null;

    if (Array.isArray(cluster)) {
        members = cluster;
    } else if (typeof cluster === 'object' && cluster !== null) {
        members = cluster.regions || cluster.partners || [];
        formedAt = cluster.formed_at;
        duration = cluster.duration;
    } else {
        members = [];
    }

    // Display as "Petrozon + Urbanex" with full labels
    const displayName = members
        .filter(r => r)
        .map(r => getLabel(r))
        .join(' + ');

    return (
        <div
            className="p-3 rounded-lg border flex flex-col gap-1.5"
            style={{ background: `${c}10`, borderColor: `${c}25` }}
        >
            <div className="flex flex-wrap items-center gap-2">
                <span
                    className="text-sm font-semibold"
                    style={{ color: c }}
                >
                    🤝 {displayName}
                </span>
            </div>
            {(formedAt != null || duration != null) && (
                <div className="text-xs text-slate-400 font-mono">
                    {formedAt != null && `formed cycle ${formedAt}`}
                    {formedAt != null && duration != null && ' · '}
                    {duration != null && `${duration} cycles`}
                </div>
            )}
        </div>
    );
}


export default function AnalysisOverlay({ analysis, onClose }) {
    if (!analysis) return null;

    const {
        dominant_strategy = 'Unknown',
        collapsed_regions = [],
        alliance_clusters = [],
        key_insights = [],
        real_world_parallel = '',
        simulation_summary = '',
    } = analysis;

    return (
        <div
            className="fixed inset-0 z-50 flex items-center justify-center p-6"
            style={{ background: 'rgba(0,0,0,0.75)', backdropFilter: 'blur(8px)' }}
        >
            <div
                className="w-full max-w-2xl max-h-[85vh] overflow-y-auto rounded-2xl border border-slate-700 shadow-2xl"
                style={{ background: '#0f172a' }}
            >
                {/* Header */}
                <div className="sticky top-0 z-10 flex items-center justify-between p-5 border-b border-slate-800"
                    style={{ background: '#0f172a' }}
                >
                    <div className="flex items-center gap-3">
                        <div className="w-10 h-10 rounded-xl bg-green-900/30 border border-green-700/30 flex items-center justify-center text-xl">
                            📊
                        </div>
                        <div>
                            <h2 className="text-base font-bold text-white">Simulation Complete</h2>
                            <p className="text-xs text-slate-400">Final analysis & strategic insights</p>
                        </div>
                    </div>
                    <button
                        onClick={onClose}
                        className="w-8 h-8 rounded-lg bg-slate-800 hover:bg-slate-700 flex items-center justify-center text-slate-400 hover:text-white transition-colors"
                    >
                        ✕
                    </button>
                </div>

                <div className="p-5 flex flex-col gap-5">
                    {/* Summary cards */}
                    <div className="grid grid-cols-2 gap-3">
                        <div className="glass rounded-xl p-4">
                            <div className="text-xs text-slate-400 mb-1">DOMINANT STRATEGY</div>
                            <div className="text-lg font-bold text-green-400">{dominant_strategy}</div>
                        </div>
                        <div className="glass rounded-xl p-4">
                            <div className="text-xs text-slate-400 mb-1">COLLAPSED REGIONS</div>
                            <div className="text-lg font-bold text-red-400">
                                {collapsed_regions.length === 0 ? 'None 🏆' : `${collapsed_regions.length} ⚠️`}
                            </div>
                        </div>
                    </div>

                    {/* Simulation summary */}
                    {simulation_summary && (
                        <div className="glass rounded-xl p-4">
                            <div className="text-xs text-slate-400 mb-2 font-medium">SIMULATION SUMMARY</div>
                            <p className="text-sm text-slate-300 leading-relaxed">{simulation_summary}</p>
                        </div>
                    )}

                    {/* Real world parallel */}
                    {real_world_parallel && (
                        <div className="glass rounded-xl p-4 border border-indigo-800/30">
                            <div className="text-xs text-indigo-400 mb-2 font-medium">🌐 REAL WORLD PARALLEL</div>
                            <p className="text-sm text-slate-300 leading-relaxed">{real_world_parallel}</p>
                        </div>
                    )}

                    {/* Collapsed regions */}
                    {collapsed_regions.length > 0 && (
                        <div>
                            <div className="text-xs text-slate-400 font-medium mb-2">COLLAPSED REGIONS</div>
                            <div className="flex flex-col gap-2">
                                {collapsed_regions.map((r, i) => (
                                    <CollapseCard key={i} region={r} index={i} />
                                ))}
                            </div>
                        </div>
                    )}

                    {/* Alliance clusters */}
                    {alliance_clusters.length > 0 && (
                        <div>
                            <div className="text-xs text-slate-400 font-medium mb-2">ALLIANCE CLUSTERS</div>
                            <div className="flex flex-col gap-2">
                                {alliance_clusters.map((cluster, i) => (
                                    <ClusterBadge key={i} cluster={cluster} index={i} />
                                ))}
                            </div>
                        </div>
                    )}

                    {/* Key insights */}
                    {key_insights.length > 0 && (
                        <div>
                            <div className="text-xs text-slate-400 font-medium mb-2">KEY INSIGHTS</div>
                            <div className="flex flex-col gap-2">
                                {key_insights.map((insight, i) => (
                                    <InsightCard key={i} text={insight} index={i} />
                                ))}
                            </div>
                        </div>
                    )}

                    <button
                        onClick={onClose}
                        className="w-full py-3 rounded-xl font-semibold text-sm text-white transition-all duration-200"
                        style={{
                            background: 'linear-gradient(135deg, #1d4ed8, #7c3aed)',
                            boxShadow: '0 0 20px rgba(124,58,237,0.3)',
                        }}
                    >
                        Back to Dashboard
                    </button>
                </div>
            </div>
        </div>
    );
}
