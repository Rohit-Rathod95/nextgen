// AnalysisOverlay.jsx — Complete post-simulation analysis dashboard with chat
import React, { useState, useEffect, useRef } from 'react';
import { db } from '../config/firebaseConfig';
import { collection, getDocs, query, orderBy } from 'firebase/firestore';
import { Line } from 'react-chartjs-2';
import {
    Chart as ChartJS,
    CategoryScale,
    LinearScale,
    PointElement,
    LineElement,
    Title,
    Tooltip,
    Legend,
} from 'chart.js';

ChartJS.register(
    CategoryScale,
    LinearScale,
    PointElement,
    LineElement,
    Title,
    Tooltip,
    Legend
);

// ─────────────────────────────────────────────────────────────────────────────
// CONSTANTS
// ─────────────────────────────────────────────────────────────────────────────

const REAL_WORLD_LABELS = {
    aquaria: 'Aquaria (Brazil)',
    agrovia: 'Agrovia (India)',
    petrozon: 'Petrozon (Gulf States)',
    urbanex: 'Urbanex (China)',
    terranova: 'Terranova (Africa)',
};

const SHORT_LABELS = {
    aquaria: 'Brazil',
    agrovia: 'India',
    petrozon: 'Gulf States',
    urbanex: 'China',
    terranova: 'Africa',
};

const REGION_COLORS = {
    aquaria: '#3b82f6',
    agrovia: '#22c55e',
    petrozon: '#f97316',
    urbanex: '#ef4444',
    terranova: '#a855f7',
};

const REGIONS = ['aquaria', 'agrovia', 'petrozon', 'urbanex', 'terranova'];

const STRATEGY_COLORS = {
    Trader: '#22c55e',
    Hoarder: '#3b82f6',
    Aggressor: '#ef4444',
    Investor: '#f59e0b',
    Mixed: '#a855f7',
};

// ─────────────────────────────────────────────────────────────────────────────
// MAIN COMPONENT
// ─────────────────────────────────────────────────────────────────────────────

export default function AnalysisOverlay({
    analysis,
    regions,
    onClose,
    isVisible,
}) {
    if (!isVisible) return null;

    const [cycleLogs, setCycleLogs] = useState([]);
    const [chartData, setChartData] = useState(null);
    const [messages, setMessages] = useState([
        {
            role: 'analyst',
            text: 'Hello! I am the WorldSim Analyst. I have analyzed the complete 20-year simulation. Ask me anything about what happened, or click one of the suggested questions below. 📊',
        },
    ]);
    const [input, setInput] = useState('');
    const messagesEndRef = useRef(null);

    // Fetch cycle logs for chart
    useEffect(() => {
        async function fetchCycleLogs() {
            try {
                const q = query(
                    collection(db, 'cycle_logs'),
                    orderBy('cycle')
                );
                const snap = await getDocs(q);
                const logs = snap.docs.map((d) => d.data());
                setCycleLogs(logs);
            } catch (err) {
                console.warn('[AnalysisOverlay] Cycle logs fetch error:', err.message);
            }
        }
        if (isVisible) fetchCycleLogs();
    }, [isVisible]);

    // Build chart data from cycle logs
    useEffect(() => {
        if (cycleLogs.length === 0) return;

        const chartDataByRegion = {};
        REGIONS.forEach((region) => {
            chartDataByRegion[region] = [];
        });

        cycleLogs.forEach((log) => {
            const snapshot = log.regions_snapshot || {};
            REGIONS.forEach((region) => {
                const health = snapshot[region]?.health_score || 0;
                chartDataByRegion[region].push(health);
            });
        });

        const labels = Array.from(
            { length: Math.min(20, cycleLogs.length) },
            (_, i) => `Year ${2025 + i + 1}`
        );

        const newChartData = {
            labels,
            datasets: REGIONS.map((region) => ({
                label: REAL_WORLD_LABELS[region],
                data: chartDataByRegion[region],
                borderColor: REGION_COLORS[region],
                backgroundColor: REGION_COLORS[region] + '22',
                tension: 0.4,
                pointRadius: 3,
                borderWidth: 2,
            })),
        };

        setChartData(newChartData);
    }, [cycleLogs]);

    // Auto-scroll chat to bottom
    useEffect(() => {
        messagesEndRef.current?.scrollIntoView({ behavior: 'smooth' });
    }, [messages]);

    // ─────────────────────────────────────────────────────────────────────────
    // HELPER FUNCTIONS
    // ─────────────────────────────────────────────────────────────────────────

    const getWinner = () => {
        if (!regions) return null;
        const entries = Object.entries(regions).filter(
            ([_, r]) => !r?.is_collapsed
        );
        if (entries.length === 0) return null;
        const sorted = entries.sort(([_, a], [__, b]) =>
            (b?.health_score || 0) - (a?.health_score || 0)
        );
        return sorted[0]?.[0] || null;
    };

    const getFirstCollapsed = () => {
        return (
            analysis?.collapsed_regions?.[0]?.region ||
            analysis?.collapsed_regions?.[0]?.region_id ||
            null
        );
    };

    const getRegionAlliances = (regionId) => {
        return (analysis?.alliance_clusters || []).filter((a) =>
            a?.regions?.includes(regionId)
        );
    };

    const getYearSummary = (cycle) => {
        const log = cycleLogs?.find((l) => l.cycle === cycle);
        if (!log) return 'Data unavailable';

        const events = log?.events_fired || [];
        if (events.length === 0) return 'Quiet year — normal consumption';

        const climateEvents = events.filter((e) => e?.type === 'climate');
        const tradeEvents = events.filter(
            (e) => e?.type === 'trade' && e?.outcome === 'trade_success'
        );
        const conflictEvents = events.filter((e) => e?.type === 'conflict');

        let summary = '';
        if (climateEvents.length > 0)
            summary += `⚡ ${climateEvents.length} climate event(s). `;
        if (tradeEvents.length > 0)
            summary += `🤝 ${tradeEvents.length} trade(s). `;
        if (conflictEvents.length > 0) summary += `⚔️ Conflict! `;
        return summary || 'Normal resource cycle.';
    };

    // ─────────────────────────────────────────────────────────────────────────
    // ANSWER GENERATION
    // ─────────────────────────────────────────────────────────────────────────

    const generateWinnerAnswer = (winner) => {
        if (!winner) return 'All regions performed well — no clear winner.';

        const r = regions?.[winner];
        const wLabel = REAL_WORLD_LABELS[winner];
        const alliances = getRegionAlliances(winner);

        return `🏆 ${wLabel} emerged strongest by Year 2045 with a health score of ${(
            r?.health_score || 0
        ).toFixed(1)}.

Key factors behind their success:

• Natural advantage: Their special ability provided resource regeneration each year, maintaining surplus even during climate stress.

• Diplomatic strength: Formed ${alliances.length} stable alliance(s), creating mutual resource support.

• Adaptive strategy: Evolved toward "${r?.strategy_label || 'Balanced'}" approach.

• Population: ${r?.population || 0} people by Year 2045.`;
    };

    const generateCollapseAnswer = (loser) => {
        if (!loser)
            return 'No regions collapsed — all 5 survived the full 20 years.';

        const collapse = analysis?.collapsed_regions?.find(
            (c) => c?.region === loser || c?.region_id === loser
        );

        return `💀 ${REAL_WORLD_LABELS[loser] || loser} collapsed in Year ${
            2025 + (collapse?.collapse_cycle || 15)
        }.

Root cause: ${
            collapse?.description ||
            'Resource exhaustion across multiple categories.'
        }

What went wrong:
• High consumption rates depleted resources faster
• Trade partnerships failed or were rejected
• Population pressure exceeded recovery capacity
• Climate events accelerated decline at critical moments`;
    };

    const generateAllianceAnswer = () => {
        const clusters = analysis?.alliance_clusters;
        if (!clusters?.length)
            return 'No stable alliances formed. All regions operated independently.';

        let answer = '🤝 Alliance Analysis:\n\n';
        clusters.forEach((a) => {
            const r1 = REAL_WORLD_LABELS[a?.regions?.[0]] || 'Unknown';
            const r2 = REAL_WORLD_LABELS[a?.regions?.[1]] || 'Unknown';
            answer += `${r1} + ${r2}\n`;
            answer += `Formed: Year ${2025 + (a?.formed_at || 0)}\n`;
            answer += `Duration: ${a?.duration || 0} years\n\n`;
        });
        return answer;
    };

    const generateTimelineAnswer = () => {
        let timeline = '📅 Year by Year Breakdown:\n\n';
        Array.from({ length: 20 }, (_, i) => i + 1).forEach((y) => {
            timeline += `Year ${2025 + y}: ${getYearSummary(y)}\n`;
        });
        return timeline;
    };

    const generateClimateAnswer = () => {
        return `🌍 Climate Impact Analysis:

Climate events fired throughout the simulation with three major effects:

1. Immediate resource shock — affected regions lost 30-45% of target resource in a single year.

2. Accelerated cooperation — regions facing climate stress sought trade partnerships.

3. Strategy shifts — severe climate events pushed agents toward emergency hoarding.

Real world mirror: The IPCC projects increasing climate volatility through 2045 — exactly our simulation window.`;
    };

    const generateStrategyAnswer = () => {
        const dominant = analysis?.dominant_strategy || 'Mixed';
        return `📊 Strategy Analysis:

Dominant strategy: ${dominant}

How strategies evolved across 20 years:

🤝 Trader: Regions with natural surpluses discovered cooperation paid off consistently.

🛡️ Hoarder: Resource-poor regions under climate stress retreated inward for safety.

⚔️ Aggressor: Desperate regions attempted conflict when trade failed.

📈 Investor: Patient regions improved land productivity with strong late-game position.

Winner strategy "${dominant}" emerged because it best matched the resource distribution.`;
    };

    const generateTurningPointAnswer = () => {
        return `⚡ Biggest Turning Points:

Year 3-5: Initial trade networks established. Early partnerships gained compounding advantages.

Year 8-12: Climate shocks tested alliances. Partnerships that survived became permanent.

Year 15+: Resource depletion pressure peaked. Networks made the difference in survival.

The single biggest turning point was likely the first major climate event — it forced immediate adaptation and revealed which regions were truly resilient.`;
    };

    const generateAnswer = (question) => {
        const q = question.toLowerCase();
        const winner = getWinner();
        const loser = getFirstCollapsed();

        if (
            q.includes('why') &&
            (q.includes('win') ||
                q.includes('winner') ||
                q.includes('best') ||
                q.includes('succeed'))
        ) {
            return generateWinnerAnswer(winner);
        }

        if (
            q.includes('collapse') ||
            q.includes('fall') ||
            (q.includes('why') && loser)
        ) {
            return generateCollapseAnswer(loser);
        }

        if (q.includes('alliance') || q.includes('cooperat')) {
            return generateAllianceAnswer();
        }

        if (
            q.includes('climate') ||
            q.includes('weather') ||
            q.includes('event') ||
            q.includes('disaster')
        ) {
            return generateClimateAnswer();
        }

        if (q.includes('real world') || q.includes('reality')) {
            return `${analysis?.real_world_parallel || 'This simulation reflects modern geopolitical resource competition.'}\n\nSimulation window: 2025-2045.`;
        }

        if (
            q.includes('year') ||
            q.includes('breakdown') ||
            q.includes('timeline')
        ) {
            return generateTimelineAnswer();
        }

        if (q.includes('strategy') || q.includes('approach')) {
            return generateStrategyAnswer();
        }

        if (q.includes('turning point') || q.includes('biggest')) {
            return generateTurningPointAnswer();
        }

        return `Based on the simulation data: ${analysis?.simulation_summary || 'The simulation revealed complex geopolitical dynamics over 20 years.'}`;
    };

    // ─────────────────────────────────────────────────────────────────────────
    // CHAT HANDLERS
    // ─────────────────────────────────────────────────────────────────────────

    const addMessage = (role, text) => {
        setMessages((prev) => [...prev, { role, text }]);
    };

    const handleChipClick = (question) => {
        addMessage('user', question);
        setTimeout(() => {
            const answer = generateAnswer(question);
            addMessage('analyst', answer);
        }, 300);
    };

    const handleSend = () => {
        if (!input.trim()) return;
        addMessage('user', input);
        const answer = generateAnswer(input);
        setTimeout(() => {
            addMessage('analyst', answer);
        }, 300);
        setInput('');
    };

    // ─────────────────────────────────────────────────────────────────────────
    // DATA HELPERS
    // ─────────────────────────────────────────────────────────────────────────

    const survivors = Object.values(regions || {}).filter(
        (r) => !r?.is_collapsed
    ).length;
    const collapsed = Object.values(regions || {}).filter(
        (r) => r?.is_collapsed
    ).length;
    const alliances = analysis?.alliance_clusters?.length || 0;
    const climateCount = cycleLogs.reduce(
        (sum, log) =>
            sum +
            (log?.events_fired?.filter((e) => e?.type === 'climate')?.length ||
                0),
        0
    );

    const winner = getWinner();
    const dominantStrategy = analysis?.dominant_strategy || 'Mixed';
    const strategyColor = STRATEGY_COLORS[dominantStrategy] || '#a855f7';

    // Sort regions by health for standings table
    const standings = Object.entries(regions || {})
        .map(([key, region]) => ({
            ...region,
            key,
        }))
        .sort((a, b) => (b?.health_score || 0) - (a?.health_score || 0));

    // Pentagon layout for alliance network
    const getPentagonPoint = (index) => {
        const cx = 200;
        const cy = 150;
        const r = 110;
        const angle = (index * (2 * Math.PI)) / 5 - Math.PI / 2;
        return {
            x: cx + r * Math.cos(angle),
            y: cy + r * Math.sin(angle),
        };
    };

    const regionPoints = {};
    REGIONS.forEach((region, i) => {
        regionPoints[region] = getPentagonPoint(i);
    });

    // Suggested questions for chatbot
    const suggestedQuestions = [
        '📈 Which strategy worked best?',
        '🌍 What does this reveal about the real world?',
        '⚡ What was the biggest turning point?',
        '📅 Year by year breakdown',
        '💧 How did climate events affect outcomes?',
    ];

    if (collapsed > 0) {
        suggestedQuestions.push(`💀 Why did ${REAL_WORLD_LABELS[getFirstCollapsed()]} collapse?`);
    }

    if (winner) {
        suggestedQuestions.push(`🏆 Why did ${REAL_WORLD_LABELS[winner]} win?`);
    }

    if (alliances > 0) {
        suggestedQuestions.push('🤝 Why did alliances form?');
    }

    // ─────────────────────────────────────────────────────────────────────────
    // RENDER
    // ─────────────────────────────────────────────────────────────────────────

    return (
        <div
            style={{
                position: 'fixed',
                inset: 0,
                background: 'rgba(0,0,0,0.85)',
                backdropFilter: 'blur(6px)',
                zIndex: 9999,
                display: 'flex',
                alignItems: 'center',
                justifyContent: 'center',
                padding: '20px',
            }}
        >
            {/* Modal Box */}
            <div
                style={{
                    width: '95vw',
                    maxWidth: '1100px',
                    height: '92vh',
                    overflowY: 'auto',
                    background: '#0a0f1e',
                    border: '1px solid rgba(99, 102, 241, 0.4)',
                    borderRadius: '20px',
                    boxShadow:
                        '0 30px 80px rgba(0,0,0,0.9), 0 0 40px rgba(99,102,241,0.2)',
                    display: 'flex',
                    flexDirection: 'column',
                    animation: 'fadeInScale 300ms ease-out',
                }}
            >
                {/* STICKY HEADER */}
                <div
                    style={{
                        position: 'sticky',
                        top: 0,
                        background: '#0a0f1e',
                        zIndex: 10,
                        padding: '20px 28px 16px',
                        borderBottom: '1px solid rgba(255,255,255,0.06)',
                        display: 'flex',
                        justifyContent: 'space-between',
                        alignItems: 'center',
                    }}
                >
                    <div>
                        <div
                            style={{
                                fontSize: '22px',
                                fontWeight: 'bold',
                                color: 'white',
                                marginBottom: '4px',
                            }}
                        >
                            🌍 WorldSim — Final Analysis Report
                        </div>
                        <div
                            style={{
                                fontSize: '12px',
                                color: '#94a3b8',
                            }}
                        >
                            Simulation Complete • 20 Years (2025 → 2045)
                        </div>
                    </div>

                    <div
                        style={{
                            display: 'flex',
                            alignItems: 'center',
                            gap: '16px',
                        }}
                    >
                        {/* Dominant Strategy Badge */}
                        <div
                            style={{
                                background: strategyColor + '20',
                                border: `1px solid ${strategyColor}`,
                                borderRadius: '8px',
                                padding: '6px 12px',
                                fontSize: '12px',
                                color: strategyColor,
                                fontWeight: 'bold',
                            }}
                        >
                            {dominantStrategy}
                        </div>

                        {/* Close Button */}
                        <button
                            onClick={onClose}
                            style={{
                                background: 'rgba(239, 68, 68, 0.2)',
                                border: '1px solid rgba(239, 68, 68, 0.4)',
                                color: '#ef4444',
                                borderRadius: '6px',
                                padding: '6px 10px',
                                cursor: 'pointer',
                                fontSize: '16px',
                                fontWeight: 'bold',
                                transition: 'all 200ms',
                            }}
                            onMouseEnter={(e) => {
                                e.target.style.background = 'rgba(239, 68, 68, 0.3)';
                            }}
                            onMouseLeave={(e) => {
                                e.target.style.background = 'rgba(239, 68, 68, 0.2)';
                            }}
                        >
                            ✕
                        </button>
                    </div>
                </div>

                {/* SCROLLABLE CONTENT */}
                <div
                    style={{
                        flex: 1,
                        overflowY: 'auto',
                        padding: '24px 28px',
                        display: 'flex',
                        flexDirection: 'column',
                        gap: '32px',
                    }}
                >
                    {/* SECTION A — Summary Cards */}
                    <div>
                        <div
                            style={{
                                display: 'grid',
                                gridTemplateColumns:
                                    'repeat(auto-fit, minmax(220px, 1fr))',
                                gap: '16px',
                            }}
                        >
                            {/* Card 1: Survivors */}
                            <div
                                style={{
                                    background: 'rgba(255,255,255,0.04)',
                                    border: survivors === 5 ? '2px solid #22c55e' : '1px solid rgba(255,255,255,0.08)',
                                    borderRadius: '12px',
                                    padding: '16px 20px',
                                    textAlign: 'center',
                                }}
                            >
                                <div
                                    style={{
                                        fontSize: '32px',
                                        fontWeight: 'bold',
                                        color: '#4ade80',
                                        marginBottom: '8px',
                                    }}
                                >
                                    🏆 {survivors}
                                </div>
                                <div
                                    style={{
                                        fontSize: '14px',
                                        fontWeight: 'bold',
                                        color: 'white',
                                        marginBottom: '4px',
                                    }}
                                >
                                    Regions Survived
                                </div>
                                <div
                                    style={{
                                        fontSize: '12px',
                                        color: '#94a3b8',
                                    }}
                                >
                                    out of 5 total
                                </div>
                            </div>

                            {/* Card 2: Collapsed */}
                            <div
                                style={{
                                    background: 'rgba(255,255,255,0.04)',
                                    border: collapsed > 0 ? '2px solid #ef4444' : '1px solid rgba(255,255,255,0.08)',
                                    borderRadius: '12px',
                                    padding: '16px 20px',
                                    textAlign: 'center',
                                }}
                            >
                                <div
                                    style={{
                                        fontSize: '32px',
                                        fontWeight: 'bold',
                                        color: collapsed > 0 ? '#ef4444' : '#4ade80',
                                        marginBottom: '8px',
                                    }}
                                >
                                    💀 {collapsed === 0 ? 'None 🎉' : collapsed}
                                </div>
                                <div
                                    style={{
                                        fontSize: '14px',
                                        fontWeight: 'bold',
                                        color: 'white',
                                    }}
                                >
                                    Regions Collapsed
                                </div>
                            </div>

                            {/* Card 3: Alliances */}
                            <div
                                style={{
                                    background: 'rgba(255,255,255,0.04)',
                                    border: '1px solid rgba(255,255,255,0.08)',
                                    borderRadius: '12px',
                                    padding: '16px 20px',
                                    textAlign: 'center',
                                }}
                            >
                                <div
                                    style={{
                                        fontSize: '32px',
                                        fontWeight: 'bold',
                                        color: '#22c55e',
                                        marginBottom: '8px',
                                    }}
                                >
                                    🤝 {alliances}
                                </div>
                                <div
                                    style={{
                                        fontSize: '14px',
                                        fontWeight: 'bold',
                                        color: 'white',
                                        marginBottom: '4px',
                                    }}
                                >
                                    Stable Alliances
                                </div>
                                <div
                                    style={{
                                        fontSize: '12px',
                                        color: '#94a3b8',
                                    }}
                                >
                                    formed during simulation
                                </div>
                            </div>

                            {/* Card 4: Climate Events */}
                            <div
                                style={{
                                    background: 'rgba(255,255,255,0.04)',
                                    border: '1px solid rgba(255,255,255,0.08)',
                                    borderRadius: '12px',
                                    padding: '16px 20px',
                                    textAlign: 'center',
                                }}
                            >
                                <div
                                    style={{
                                        fontSize: '32px',
                                        fontWeight: 'bold',
                                        color: '#f97316',
                                        marginBottom: '8px',
                                    }}
                                >
                                    ⚡ {climateCount}
                                </div>
                                <div
                                    style={{
                                        fontSize: '14px',
                                        fontWeight: 'bold',
                                        color: 'white',
                                    }}
                                >
                                    Climate Shocks
                                </div>
                                <div
                                    style={{
                                        fontSize: '12px',
                                        color: '#94a3b8',
                                    }}
                                >
                                    across 20 years
                                </div>
                            </div>
                        </div>
                    </div>

                    {/* SECTION B — Final Standings Table */}
                    <div>
                        <div
                            style={{
                                fontSize: '18px',
                                fontWeight: 'bold',
                                color: 'white',
                                marginBottom: '16px',
                            }}
                        >
                            📊 Final Standings — Year 2045
                        </div>

                        <div
                            style={{
                                overflowX: 'auto',
                                background: 'rgba(255,255,255,0.02)',
                                borderRadius: '12px',
                                border: '1px solid rgba(255,255,255,0.08)',
                            }}
                        >
                            <table
                                style={{
                                    width: '100%',
                                    borderCollapse: 'collapse',
                                    fontSize: '13px',
                                }}
                            >
                                <thead>
                                    <tr style={{ borderBottom: '1px solid rgba(255,255,255,0.1)' }}>
                                        <th style={{ padding: '12px 16px', textAlign: 'left', color: '#94a3b8', fontWeight: '600' }}>
                                            Rank
                                        </th>
                                        <th style={{ padding: '12px 16px', textAlign: 'left', color: '#94a3b8', fontWeight: '600' }}>
                                            Region
                                        </th>
                                        <th style={{ padding: '12px 16px', textAlign: 'center', color: '#94a3b8', fontWeight: '600' }}>
                                            Health
                                        </th>
                                        <th style={{ padding: '12px 16px', textAlign: 'center', color: '#94a3b8', fontWeight: '600' }}>
                                            Population
                                        </th>
                                        <th style={{ padding: '12px 16px', textAlign: 'left', color: '#94a3b8', fontWeight: '600' }}>
                                            Strategy
                                        </th>
                                        <th style={{ padding: '12px 16px', textAlign: 'center', color: '#94a3b8', fontWeight: '600' }}>
                                            Status
                                        </th>
                                    </tr>
                                </thead>
                                <tbody>
                                    {standings.map((region, idx) => {
                                        const medals = ['🥇', '🥈', '🥉'];
                                        const rank = medals[idx] || String(idx + 1);
                                        const regionName = REAL_WORLD_LABELS[region.key];
                                        const regionColor = REGION_COLORS[region.key];
                                        const healthColor =
                                            region.health_score >= 60
                                                ? '#4ade80'
                                                : region.health_score >= 30
                                                    ? '#f59e0b'
                                                    : '#ef4444';

                                        const popChange = region.population - (region.starting_population || 0);
                                        const popChangeColor = popChange >= 0 ? '#4ade80' : '#ef4444';

                                        return (
                                            <tr
                                                key={region.key}
                                                style={{
                                                    borderBottom: '1px solid rgba(255,255,255,0.06)',
                                                    borderLeft:
                                                        idx === 0
                                                            ? `4px solid #f59e0b`
                                                            : '4px solid transparent',
                                                    background: idx === 0 ? 'rgba(249, 115, 22, 0.05)' : 'transparent',
                                                }}
                                            >
                                                <td
                                                    style={{
                                                        padding: '12px 16px',
                                                        fontSize: '16px',
                                                        fontWeight: 'bold',
                                                    }}
                                                >
                                                    {rank}
                                                </td>
                                                <td style={{ padding: '12px 16px' }}>
                                                    <div style={{ display: 'flex', alignItems: 'center', gap: '8px' }}>
                                                        <div
                                                            style={{
                                                                width: '12px',
                                                                height: '12px',
                                                                borderRadius: '50%',
                                                                background: regionColor,
                                                            }}
                                                        />
                                                        <span style={{ color: 'white', fontWeight: '500' }}>
                                                            {regionName}
                                                        </span>
                                                    </div>
                                                </td>
                                                <td style={{ padding: '12px 16px', textAlign: 'center' }}>
                                                    <div
                                                        style={{
                                                            height: '4px',
                                                            background: 'rgba(255,255,255,0.1)',
                                                            borderRadius: '2px',
                                                            overflow: 'hidden',
                                                            marginBottom: '4px',
                                                        }}
                                                    >
                                                        <div
                                                            style={{
                                                                height: '100%',
                                                                width: `${Math.min(100, region.health_score)}%`,
                                                                background: healthColor,
                                                            }}
                                                        />
                                                    </div>
                                                    <span style={{ color: healthColor, fontSize: '11px', fontWeight: 'bold' }}>
                                                        {region.health_score.toFixed(1)}
                                                    </span>
                                                </td>
                                                <td style={{ padding: '12px 16px', textAlign: 'center', color: 'white' }}>
                                                    {region.population}
                                                    <span style={{ color: popChangeColor, marginLeft: '6px', fontSize: '11px' }}>
                                                        {popChange >= 0 ? '+' : ''}{popChange}
                                                    </span>
                                                </td>
                                                <td style={{ padding: '12px 16px' }}>
                                                    <div
                                                        style={{
                                                            background: STRATEGY_COLORS[region.strategy_label] + '20',
                                                            border: `1px solid ${STRATEGY_COLORS[region.strategy_label] || '#a855f7'}`,
                                                            borderRadius: '6px',
                                                            padding: '4px 8px',
                                                            fontSize: '11px',
                                                            color: STRATEGY_COLORS[region.strategy_label] || '#a855f7',
                                                            fontWeight: 'bold',
                                                            display: 'inline-block',
                                                        }}
                                                    >
                                                        {region.strategy_label || 'Balanced'}
                                                    </div>
                                                </td>
                                                <td style={{ padding: '12px 16px', textAlign: 'center' }}>
                                                    <span
                                                        style={{
                                                            color: region.is_collapsed ? '#ef4444' : '#4ade80',
                                                        }}
                                                    >
                                                        {region.is_collapsed ? '💀 Collapsed' : '✓ Survived'}
                                                    </span>
                                                </td>
                                            </tr>
                                        );
                                    })}
                                </tbody>
                            </table>
                        </div>
                    </div>

                    {/* SECTION C — Health Timeline Chart */}
                    <div>
                        <div
                            style={{
                                fontSize: '18px',
                                fontWeight: 'bold',
                                color: 'white',
                                marginBottom: '16px',
                            }}
                        >
                            📈 Health Score Over 20 Years
                        </div>

                        {chartData ? (
                            <div
                                style={{
                                    height: '280px',
                                    background: 'rgba(255,255,255,0.02)',
                                    borderRadius: '12px',
                                    border: '1px solid rgba(255,255,255,0.08)',
                                    padding: '16px',
                                }}
                            >
                                <Line
                                    data={chartData}
                                    options={{
                                        responsive: true,
                                        maintainAspectRatio: false,
                                        plugins: {
                                            legend: {
                                                position: 'bottom',
                                                labels: {
                                                    color: '#94a3b8',
                                                    usePointStyle: true,
                                                    padding: 16,
                                                },
                                            },
                                        },
                                        scales: {
                                            x: {
                                                ticks: { color: '#64748b', maxRotation: 45 },
                                                grid: { color: 'rgba(255,255,255,0.04)' },
                                            },
                                            y: {
                                                min: 0,
                                                max: 100,
                                                ticks: { color: '#64748b' },
                                                grid: { color: 'rgba(255,255,255,0.04)' },
                                            },
                                        },
                                    }}
                                />
                            </div>
                        ) : (
                            <div style={{ color: '#94a3b8', textAlign: 'center', padding: '32px' }}>
                                Loading chart data...
                            </div>
                        )}
                    </div>

                    {/* SECTION D — Alliance Network SVG */}
                    <div>
                        <div
                            style={{
                                fontSize: '18px',
                                fontWeight: 'bold',
                                color: 'white',
                                marginBottom: '16px',
                            }}
                        >
                            🤝 Alliance Network
                        </div>

                        <div
                            style={{
                                background: 'rgba(255,255,255,0.02)',
                                borderRadius: '12px',
                                border: '1px solid rgba(255,255,255,0.08)',
                                padding: '16px',
                            }}
                        >
                            <svg
                                viewBox="0 0 400 300"
                                style={{
                                    width: '100%',
                                    height: '300px',
                                }}
                            >
                                {/* Alliance Lines */}
                                {(analysis?.alliance_clusters || []).map((alliance, idx) => {
                                    const r1 = alliance.regions?.[0];
                                    const r2 = alliance.regions?.[1];
                                    if (!r1 || !r2) return null;

                                    const p1 = regionPoints[r1];
                                    const p2 = regionPoints[r2];
                                    if (!p1 || !p2) return null;

                                    const isEnded = !alliance.held_until_end;

                                    return (
                                        <g key={`alliance-${idx}`}>
                                            <line
                                                x1={p1.x}
                                                y1={p1.y}
                                                x2={p2.x}
                                                y2={p2.y}
                                                stroke="#22c55e"
                                                strokeWidth={alliance.duration > 10 ? 3 : 1.5}
                                                strokeDasharray={isEnded ? '5,5' : 'none'}
                                                opacity={0.7}
                                            />
                                            <text
                                                x={(p1.x + p2.x) / 2}
                                                y={(p1.y + p2.y) / 2}
                                                fill="#22c55e"
                                                fontSize="8"
                                                textAnchor="middle"
                                                dominantBaseline="middle"
                                            >
                                                {alliance.duration}y
                                            </text>
                                        </g>
                                    );
                                })}

                                {/* Region Circles and Labels */}
                                {REGIONS.map((region, idx) => {
                                    const point = regionPoints[region];
                                    if (!point) return null;

                                    return (
                                        <g key={`region-${region}`}>
                                            <circle
                                                cx={point.x}
                                                cy={point.y}
                                                r={30}
                                                fill={REGION_COLORS[region] + '33'}
                                                stroke={REGION_COLORS[region]}
                                                strokeWidth={2}
                                            />
                                            <text
                                                x={point.x}
                                                y={point.y - 6}
                                                textAnchor="middle"
                                                dominantBaseline="middle"
                                                fill="white"
                                                fontSize="9"
                                                fontWeight="bold"
                                            >
                                                {region.charAt(0).toUpperCase() + region.slice(1)}
                                            </text>
                                            <text
                                                x={point.x}
                                                y={point.y + 10}
                                                textAnchor="middle"
                                                dominantBaseline="middle"
                                                fill="#94a3b8"
                                                fontSize="7"
                                            >
                                                {SHORT_LABELS[region]}
                                            </text>
                                        </g>
                                    );
                                })}
                            </svg>

                            {/* Legend */}
                            <div
                                style={{
                                    display: 'flex',
                                    gap: '24px',
                                    marginTop: '16px',
                                    justifyContent: 'center',
                                    fontSize: '12px',
                                    flexWrap: 'wrap',
                                }}
                            >
                                <div style={{ display: 'flex', alignItems: 'center', gap: '8px' }}>
                                    <div
                                        style={{
                                            height: '2px',
                                            width: '20px',
                                            background: '#22c55e',
                                            borderRadius: '2px',
                                        }}
                                    />
                                    <span style={{ color: '#94a3b8' }}>Stable Alliance</span>
                                </div>
                                <div style={{ display: 'flex', alignItems: 'center', gap: '8px' }}>
                                    <div
                                        style={{
                                            height: '2px',
                                            width: '20px',
                                            background: '#22c55e',
                                            borderRadius: '2px',
                                            backgroundImage: 'linear-gradient(90deg, #22c55e 5px, transparent 5px)',
                                            backgroundSize: '10px 100%',
                                        }}
                                    />
                                    <span style={{ color: '#94a3b8' }}>Ended Alliance</span>
                                </div>
                            </div>
                        </div>
                    </div>

                    {/* SECTION E — Region Deep Dive Cards */}
                    <div>
                        <div
                            style={{
                                fontSize: '18px',
                                fontWeight: 'bold',
                                color: 'white',
                                marginBottom: '16px',
                            }}
                        >
                            🔍 Region Analysis
                        </div>

                        <div
                            style={{
                                display: 'flex',
                                overflowX: 'auto',
                                gap: '16px',
                                paddingBottom: '8px',
                            }}
                        >
                            {REGIONS.map((region) => {
                                const regionData = regions?.[region];
                                if (!regionData) return null;

                                const healthColor =
                                    regionData.health_score >= 60
                                        ? '#4ade80'
                                        : regionData.health_score >= 30
                                            ? '#f59e0b'
                                            : '#ef4444';

                                const startPop = regionData.starting_population || 0;
                                const endPop = regionData.population || 0;
                                const popChange = endPop - startPop;
                                const popChangePercent = startPop > 0 ? ((popChange / startPop) * 100).toFixed(1) : 0;
                                const popColor = popChange >= 0 ? '#4ade80' : '#ef4444';

                                const resources = {
                                    water: regionData.water || 0,
                                    food: regionData.food || 0,
                                    energy: regionData.energy || 0,
                                    land: regionData.land || 0,
                                };

                                const resourceColors = {
                                    water: '#3b82f6',
                                    food: '#22c55e',
                                    energy: '#f97316',
                                    land: '#f59e0b',
                                };

                                return (
                                    <div
                                        key={region}
                                        style={{
                                            minWidth: '220px',
                                            background: 'rgba(255,255,255,0.04)',
                                            border: `2px solid ${REGION_COLORS[region]}`,
                                            borderRadius: '14px',
                                            padding: '16px',
                                            display: 'flex',
                                            flexDirection: 'column',
                                            gap: '12px',
                                        }}
                                    >
                                        {/* Header */}
                                        <div>
                                            <div style={{ display: 'flex', alignItems: 'center', gap: '8px', marginBottom: '4px' }}>
                                                <div
                                                    style={{
                                                        width: '12px',
                                                        height: '12px',
                                                        borderRadius: '50%',
                                                        background: REGION_COLORS[region],
                                                    }}
                                                />
                                                <div
                                                    style={{
                                                        fontWeight: 'bold',
                                                        color: 'white',
                                                    }}
                                                >
                                                    {REAL_WORLD_LABELS[region]}
                                                </div>
                                            </div>
                                        </div>

                                        {/* Health Bar */}
                                        <div>
                                            <div
                                                style={{
                                                    fontSize: '11px',
                                                    color: '#94a3b8',
                                                    marginBottom: '4px',
                                                }}
                                            >
                                                Health
                                            </div>
                                            <div
                                                style={{
                                                    height: '4px',
                                                    background: 'rgba(255,255,255,0.1)',
                                                    borderRadius: '2px',
                                                    overflow: 'hidden',
                                                }}
                                            >
                                                <div
                                                    style={{
                                                        height: '100%',
                                                        width: `${Math.min(100, regionData.health_score)}%`,
                                                        background: healthColor,
                                                    }}
                                                />
                                            </div>
                                            <div
                                                style={{
                                                    fontSize: '11px',
                                                    color: healthColor,
                                                    marginTop: '4px',
                                                    fontWeight: 'bold',
                                                }}
                                            >
                                                {regionData.health_score.toFixed(1)}
                                            </div>
                                        </div>

                                        {/* Resources */}
                                        <div style={{ display: 'flex', flexDirection: 'column', gap: '6px' }}>
                                            {Object.entries(resources).map(([res, val]) => (
                                                <div key={res}>
                                                    <div
                                                        style={{
                                                            fontSize: '10px',
                                                            color: '#94a3b8',
                                                            marginBottom: '2px',
                                                            display: 'flex',
                                                            justifyContent: 'space-between',
                                                        }}
                                                    >
                                                        <span>{res.charAt(0).toUpperCase() + res.slice(1)}</span>
                                                        <span>{val.toFixed(0)}</span>
                                                    </div>
                                                    <div
                                                        style={{
                                                            height: '2px',
                                                            background: 'rgba(255,255,255,0.1)',
                                                            borderRadius: '1px',
                                                            overflow: 'hidden',
                                                        }}
                                                    >
                                                        <div
                                                            style={{
                                                                height: '100%',
                                                                width: `${Math.min(100, val)}%`,
                                                                background: resourceColors[res],
                                                            }}
                                                        />
                                                    </div>
                                                </div>
                                            ))}
                                        </div>

                                        {/* Population */}
                                        <div
                                            style={{
                                                fontSize: '12px',
                                                color: '#e2e8f0',
                                                fontFamily: 'monospace',
                                            }}
                                        >
                                            👥 {startPop.toLocaleString()} → {endPop.toLocaleString()}
                                        </div>
                                        <div
                                            style={{
                                                fontSize: '11px',
                                                color: popColor,
                                                fontWeight: 'bold',
                                            }}
                                        >
                                            {popChange >= 0 ? '+' : ''}{popChangePercent}%
                                        </div>

                                        {/* Strategy */}
                                        <div>
                                            <div
                                                style={{
                                                    fontSize: '10px',
                                                    color: '#94a3b8',
                                                    marginBottom: '4px',
                                                }}
                                            >
                                                Strategy
                                            </div>
                                            <div
                                                style={{
                                                    background: STRATEGY_COLORS[regionData.strategy_label] + '20',
                                                    border: `1px solid ${STRATEGY_COLORS[regionData.strategy_label] || '#a855f7'}`,
                                                    borderRadius: '6px',
                                                    padding: '4px 8px',
                                                    fontSize: '11px',
                                                    color: STRATEGY_COLORS[regionData.strategy_label] || '#a855f7',
                                                    fontWeight: 'bold',
                                                    textAlign: 'center',
                                                }}
                                            >
                                                {regionData.strategy_label || 'Balanced'}
                                            </div>
                                        </div>
                                    </div>
                                );
                            })}
                        </div>
                    </div>

                    {/* SECTION F — Key Insights */}
                    <div>
                        <div
                            style={{
                                fontSize: '18px',
                                fontWeight: 'bold',
                                color: 'white',
                                marginBottom: '16px',
                            }}
                        >
                            🧠 Key Insights
                        </div>

                        <div
                            style={{
                                display: 'grid',
                                gridTemplateColumns: 'repeat(auto-fit, minmax(300px, 1fr))',
                                gap: '12px',
                            }}
                        >
                            {(analysis?.key_insights || []).map((insight, idx) => (
                                <div
                                    key={idx}
                                    style={{
                                        background: 'rgba(99, 102, 241, 0.08)',
                                        border: '1px solid rgba(99, 102, 241, 0.2)',
                                        borderRadius: '10px',
                                        padding: '14px',
                                    }}
                                >
                                    <div
                                        style={{
                                            display: 'inline-block',
                                            background: 'rgba(99, 102, 241, 0.3)',
                                            borderRadius: '50%',
                                            width: '24px',
                                            height: '24px',
                                            lineHeight: '24px',
                                            textAlign: 'center',
                                            color: '#6366f1',
                                            fontWeight: 'bold',
                                            fontSize: '12px',
                                            marginBottom: '8px',
                                        }}
                                    >
                                        {idx + 1}
                                    </div>
                                    <div
                                        style={{
                                            color: '#e2e8f0',
                                            fontSize: '13px',
                                            lineHeight: '1.5',
                                        }}
                                    >
                                        {insight}
                                    </div>
                                </div>
                            ))}
                        </div>
                    </div>

                    {/* SECTION G — Real World Parallel */}
                    <div
                        style={{
                            background: 'rgba(16, 185, 129, 0.08)',
                            border: '1px solid rgba(16, 185, 129, 0.2)',
                            borderRadius: '12px',
                            padding: '20px',
                        }}
                    >
                        <div
                            style={{
                                fontSize: '16px',
                                fontWeight: 'bold',
                                color: '#10b981',
                                marginBottom: '12px',
                            }}
                        >
                            🌐 Real World Parallel
                        </div>
                        <div
                            style={{
                                color: '#e2e8f0',
                                fontSize: '14px',
                                lineHeight: '1.6',
                            }}
                        >
                            {analysis?.real_world_parallel ||
                                'This simulation reflects modern geopolitical dynamics around resource scarcity and international cooperation.'}
                        </div>
                    </div>

                    {/* SECTION H — Chatbot */}
                    <div>
                        <div>
                            <div
                                style={{
                                    fontSize: '18px',
                                    fontWeight: 'bold',
                                    color: 'white',
                                    marginBottom: '4px',
                                }}
                            >
                                💬 Ask WorldSim Analyst
                            </div>
                            <div
                                style={{
                                    fontSize: '12px',
                                    color: '#94a3b8',
                                    marginBottom: '16px',
                                }}
                            >
                                Ask questions about the simulation
                            </div>
                        </div>

                        <div
                            style={{
                                background: 'rgba(255,255,255,0.03)',
                                border: '1px solid rgba(255,255,255,0.08)',
                                borderRadius: '14px',
                                overflow: 'hidden',
                                display: 'flex',
                                flexDirection: 'column',
                            }}
                        >
                            {/* Messages Area */}
                            <div
                                style={{
                                    height: '250px',
                                    overflowY: 'auto',
                                    padding: '16px',
                                    display: 'flex',
                                    flexDirection: 'column',
                                    gap: '10px',
                                }}
                            >
                                {messages.map((msg, idx) => (
                                    <div
                                        key={idx}
                                        style={{
                                            display: 'flex',
                                            justifyContent:
                                                msg.role === 'user'
                                                    ? 'flex-end'
                                                    : 'flex-start',
                                        }}
                                    >
                                        <div
                                            style={{
                                                maxWidth: '80%',
                                                background:
                                                    msg.role === 'analyst'
                                                        ? 'rgba(99, 102, 241, 0.2)'
                                                        : 'rgba(255,255,255,0.08)',
                                                border:
                                                    msg.role === 'analyst'
                                                        ? '1px solid rgba(99, 102, 241, 0.3)'
                                                        : '1px solid rgba(255,255,255,0.1)',
                                                borderRadius:
                                                    msg.role === 'analyst'
                                                        ? '12px 12px 12px 2px'
                                                        : '12px 12px 2px 12px',
                                                padding: '10px 14px',
                                                color:
                                                    msg.role === 'user'
                                                        ? '#e2e8f0'
                                                        : 'white',
                                                fontSize: '13px',
                                                lineHeight: '1.4',
                                                whiteSpace: 'pre-wrap',
                                                wordBreak: 'break-word',
                                            }}
                                        >
                                            {msg.text}
                                        </div>
                                    </div>
                                ))}
                                <div ref={messagesEndRef} />
                            </div>

                            {/* Question Chips */}
                            <div
                                style={{
                                    display: 'flex',
                                    flexWrap: 'wrap',
                                    gap: '8px',
                                    padding: '12px 16px',
                                    borderTop: '1px solid rgba(255,255,255,0.06)',
                                    maxHeight: '120px',
                                    overflowY: 'auto',
                                }}
                            >
                                {suggestedQuestions.slice(0, 5).map((question, idx) => (
                                    <button
                                        key={idx}
                                        onClick={() => handleChipClick(question)}
                                        style={{
                                            background: 'rgba(99, 102, 241, 0.15)',
                                            border: '1px solid rgba(99, 102, 241, 0.3)',
                                            borderRadius: '20px',
                                            padding: '6px 14px',
                                            fontSize: '12px',
                                            color: '#a5b4fc',
                                            cursor: 'pointer',
                                            transition: 'all 200ms',
                                            whiteSpace: 'nowrap',
                                        }}
                                        onMouseEnter={(e) => {
                                            e.target.style.background = 'rgba(99, 102, 241, 0.3)';
                                        }}
                                        onMouseLeave={(e) => {
                                            e.target.style.background =
                                                'rgba(99, 102, 241, 0.15)';
                                        }}
                                    >
                                        {question}
                                    </button>
                                ))}
                            </div>

                            {/* Input Row */}
                            <div
                                style={{
                                    display: 'flex',
                                    padding: '12px 16px',
                                    gap: '8px',
                                    borderTop: '1px solid rgba(255,255,255,0.06)',
                                }}
                            >
                                <input
                                    type="text"
                                    value={input}
                                    onChange={(e) => setInput(e.target.value)}
                                    onKeyDown={(e) => {
                                        if (e.key === 'Enter') handleSend();
                                    }}
                                    placeholder="Ask about the simulation..."
                                    style={{
                                        flex: 1,
                                        background: 'rgba(255,255,255,0.06)',
                                        border: '1px solid rgba(255,255,255,0.12)',
                                        borderRadius: '8px',
                                        padding: '8px 12px',
                                        color: 'white',
                                        fontSize: '12px',
                                        outline: 'none',
                                    }}
                                />
                                <button
                                    onClick={handleSend}
                                    style={{
                                        background: 'rgba(99, 102, 241, 0.6)',
                                        border: 'none',
                                        borderRadius: '8px',
                                        padding: '8px 16px',
                                        color: 'white',
                                        fontWeight: 'bold',
                                        fontSize: '12px',
                                        cursor: 'pointer',
                                        transition: 'all 200ms',
                                    }}
                                    onMouseEnter={(e) => {
                                        e.target.style.background = 'rgba(99, 102, 241, 0.8)';
                                    }}
                                    onMouseLeave={(e) => {
                                        e.target.style.background = 'rgba(99, 102, 241, 0.6)';
                                    }}
                                >
                                    Send
                                </button>
                            </div>
                        </div>
                    </div>
                </div>
            </div>

            <style>
                {`
                    @keyframes fadeInScale {
                        from {
                            opacity: 0;
                            transform: scale(0.95);
                        }
                        to {
                            opacity: 1;
                            transform: scale(1);
                        }
                    }
                `}
            </style>
        </div>
    );
}
