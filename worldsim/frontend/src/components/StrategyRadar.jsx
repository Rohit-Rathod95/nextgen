// StrategyRadar.jsx — interactive, explanatory radar & history view
import React, { useState, useEffect, useRef } from 'react';
import { Radar, Line } from 'react-chartjs-2';
import {
  Chart as ChartJS,
  RadialLinearScale,
  PointElement,
  LineElement,
  Filler,
  Tooltip,
  Legend,
  CategoryScale,
  LinearScale,
} from 'chart.js';

ChartJS.register(
  RadialLinearScale,
  PointElement,
  LineElement,
  Filler,
  Tooltip,
  Legend,
  CategoryScale,
  LinearScale
);

const STRATEGY_COLORS = {
  trade: '#22c55e',
  hoard: '#3b82f6',
  invest: '#f59e0b',
  aggress: '#ef4444',
};

const STRATEGY_INFO = {
  trade: {
    icon: '🤝',
    label: 'Trade',
    title: 'Trade Strategy',
    description:
      'This region prioritizes diplomatic resource exchange with neighbors. High trade weight means it seeks mutual benefit over self-preservation.',
    realWorld:
      'Mirrors open-economy nations — Singapore, Netherlands, UAE — that compensate for small resource bases with extensive trade networks.',
    good: 'Stable supply, trust building, alliance formation',
    risk: 'Dependent on partner goodwill. Trade rejection damages trust.',
  },
  hoard: {
    icon: '🛡️',
    label: 'Hoard',
    title: 'Hoard Strategy',
    description:
      'This region conserves resources internally, reducing consumption and refusing trade. Prioritizes self-sufficiency over cooperation.',
    realWorld:
      'Mirrors resource nationalism — North Korea, Russia post-2022, nations restricting exports during crisis periods.',
    good: 'Short-term security, independence from partners',
    risk: 'Isolation, missed trade opportunities, slower recovery after shocks.',
  },
  invest: {
    icon: '📈',
    label: 'Invest',
    title: 'Invest Strategy',
    description:
      'This region sacrifices current resources to improve future productive capacity. Land becomes more fertile. Infrastructure improves output.',
    realWorld:
      'Mirrors East Asian development model — South Korea, Japan, early China — decades of sacrificed consumption to build industrial and agricultural base.',
    good: 'Long-term growth, compounding returns, resilient resource base',
    risk: 'Vulnerable in early cycles before investments pay off.',
  },
  aggress: {
    icon: '⚔️',
    label: 'Aggress',
    title: 'Aggress Strategy',
    description:
      'This region attempts to seize resources from weaker neighbors when diplomatic options fail. High risk — requires clear strength advantage to succeed.',
    realWorld:
      'Mirrors resource-driven military conflict — Iraq invasion of Kuwait for oil, Russia-Ukraine partly driven by agricultural land and Black Sea energy resources.',
    good: 'Fast resource acquisition if successful',
    risk: 'Trust cascade — ALL regions lose faith. Failed aggression costs energy. Isolation follows.',
  },
};

const START_WEIGHT = 0.25;
const LABELS = ['trade', 'hoard', 'invest', 'aggress'];

export default function StrategyRadar({ region, regionId }) {
  if (!region) return null;

  const [selectedStrategy, setSelectedStrategy] = useState(null);
  const [showHistory, setShowHistory] = useState(false);

  // current weights
  const weights = {
    trade: region?.trade_weight ?? START_WEIGHT,
    hoard: region?.hoard_weight ?? START_WEIGHT,
    invest: region?.invest_weight ?? START_WEIGHT,
    aggress: region?.aggress_weight ?? START_WEIGHT,
  };

  const changes = {};
  LABELS.forEach((s) => {
    changes[s] = weights[s] - START_WEIGHT;
  });

  const dominant = Object.entries(weights).sort(([, a], [, b]) => b - a)[0][0];

  const history = region?.history || [];
  const weightHistory = {
    trade: history.map((h) => h.trade_weight ?? START_WEIGHT),
    hoard: history.map((h) => h.hoard_weight ?? START_WEIGHT),
    invest: history.map((h) => h.invest_weight ?? START_WEIGHT),
    aggress: history.map((h) => h.aggress_weight ?? START_WEIGHT),
  };
  const cycleLabels = history.map((h) => `Y${2025 + (h.cycle || 0)}`);

  // radar dataset and options
  const radarData = {
    labels: LABELS.map((l) => STRATEGY_INFO[l].label),
    datasets: [
      {
        label: 'Current Weights',
        data: LABELS.map((l) => weights[l]),
        backgroundColor: 'rgba(99,102,241,0.2)',
        borderColor: '#6366f1',
        borderWidth: 2,
        pointBackgroundColor: LABELS.map((l) => STRATEGY_COLORS[l]),
        pointRadius: 5,
      },
    ],
  };

  const radarOptions = {
    responsive: true,
    maintainAspectRatio: false,
    scales: {
      r: {
        min: 0,
        max: 1,
        ticks: { display: false },
        grid: { color: 'rgba(255,255,255,0.1)' },
        angleLines: { color: 'rgba(255,255,255,0.1)' },
        pointLabels: { color: '#94a3b8', font: { size: 12 } },
      },
    },
    plugins: {
      legend: { display: false },
    },
  };

  const lineData = {
    labels: cycleLabels.length ? cycleLabels : ['Y2025'],
    datasets: LABELS.map((l) => ({
      label: STRATEGY_INFO[l].label,
      data: weightHistory[l].length
        ? weightHistory[l]
        : [START_WEIGHT],
      borderColor: STRATEGY_COLORS[l],
      backgroundColor: STRATEGY_COLORS[l] + '22',
      tension: 0.4,
      pointRadius: 2,
      borderWidth: 2,
    })),
  };

  const lineOptions = {
    responsive: true,
    maintainAspectRatio: false,
    scales: {
      x: {
        ticks: { color: '#64748b', maxRotation: 0, maxTicksLimit: 10 },
        grid: { color: 'rgba(255,255,255,0.05)' },
      },
      y: {
        min: 0,
        max: 1,
        ticks: { color: '#64748b' },
        grid: { color: 'rgba(255,255,255,0.05)' },
      },
    },
    plugins: {
      legend: { labels: { color: '#94a3b8' } },
    },
  };

  function handleRadarClick(event, elements) {
    if (elements.length > 0) {
      const idx = elements[0].index;
      const strat = LABELS[idx];
      setSelectedStrategy(strat === selectedStrategy ? null : strat);
    }
  }

  // compute trust average for trade performance
  const trustScores = region?.trust || {};
  const avgTrust =
    Object.values(trustScores).reduce((s, v) => s + v, 0) /
    (Object.values(trustScores).length || 1);

  return (
    <div className="w-full text-slate-100">
      {/* Part1: radar/history toggle */}
      <div className="flex justify-between items-center mb-3">
        <span className="text-sm font-semibold">Strategy Profile</span>
        <button
          className="text-xs px-2 py-1 rounded bg-slate-700 hover:bg-slate-600"
          onClick={() => setShowHistory(!showHistory)}
        >
          {showHistory ? '📊 Show Radar' : '📈 Show History'}
        </button>
      </div>

      <div className="relative h-64">
        {!showHistory ? (
          <Radar
            data={radarData}
            options={radarOptions}
            onClick={handleRadarClick}
          />
        ) : (
          <Line data={lineData} options={lineOptions} />
        )}
        {!showHistory && (
          <div className="absolute bottom-1 right-2 text-xs text-slate-500">
            Click any strategy in radar view for detailed explanation
          </div>
        )}
      </div>

      {/* Weight bars + dominant banner */}
      <div className="mt-4 space-y-2">
        {LABELS.map((s) => {
          const w = weights[s];
          const change = changes[s];
          const pct = (w * 100).toFixed(0);
          let changeLabel = '—';
          let changeColor = '#94a3b8';
          if (change > 0.02) {
            changeLabel = `▲ +${(change * 100).toFixed(0)}`;
            changeColor = '#4ade80';
          } else if (change < -0.02) {
            changeLabel = `▼ ${(change * 100).toFixed(0)}`;
            changeColor = '#ef4444';
          }
          return (
            <div
              key={s}
              className="flex items-center justify-between p-2 rounded hover:bg-slate-800 cursor-pointer transition-colors"
              onClick={() => setSelectedStrategy(s)}
            >
              <div className="flex items-center gap-2">
                <span style={{ color: STRATEGY_COLORS[s] }}>{STRATEGY_INFO[s].icon}</span>
                <span>{STRATEGY_INFO[s].label}</span>
              </div>
              <div className="flex-1 mx-3 bg-white/5 h-1 rounded overflow-hidden">
                <div
                  className="h-full"
                  style={{
                    width: `${w * 100}%`,
                    background: STRATEGY_COLORS[s],
                    transition: 'width 0.5s ease',
                  }}
                />
              </div>
              <div className="flex items-center gap-1 text-xs">
                <span>{pct}%</span>
                <span style={{ color: changeColor }}>{changeLabel}</span>
              </div>
            </div>
          );
        })}
        <div
          className="mt-2 px-3 py-1 rounded font-semibold text-sm"
          style={{
            background: STRATEGY_COLORS[dominant] + '20',
            color: STRATEGY_COLORS[dominant],
          }}
        >
          Dominant: {STRATEGY_INFO[dominant].icon} {STRATEGY_INFO[dominant].title}
        </div>
      </div>

      {/* Part2: detail card */}
      {selectedStrategy && (
        <div
          className="mt-4 p-4 rounded-lg border transition-all duration-300"
          style={{
            background: 'rgba(255,255,255,0.04)',
            borderColor: STRATEGY_COLORS[selectedStrategy] + '33',
          }}
        >
          <button
            className="absolute top-2 right-2 text-slate-400 hover:text-white"
            onClick={() => setSelectedStrategy(null)}
          >
            ✕
          </button>
          <div className="mb-3 flex items-center gap-2">
            <span style={{ fontSize: '20px' }}>
              {STRATEGY_INFO[selectedStrategy].icon}
            </span>
            <span className="text-lg font-bold">
              {STRATEGY_INFO[selectedStrategy].title}
            </span>
            <span
              className="ml-auto text-xs px-2 py-0.5 rounded"
              style={{
                background: STRATEGY_COLORS[selectedStrategy] + '20',
                color: STRATEGY_COLORS[selectedStrategy],
              }}
            >
              {(weights[selectedStrategy] * 100).toFixed(0)}% weight
            </span>
          </div>

          {/* evolution */}
          <div className="mb-3 text-sm">
            Started: 25% → Now: {(weights[selectedStrategy] * 100).toFixed(0)}%
            <span
              className="ml-2"
              style={{
                color:
                  changes[selectedStrategy] > 0
                    ? '#4ade80'
                    : changes[selectedStrategy] < 0
                    ? '#ef4444'
                    : '#94a3b8',
              }}
            >
              {changes[selectedStrategy] > 0
                ? '▲'
                : changes[selectedStrategy] < 0
                ? '▼'
                : '—'}
            </span>
          </div>
          <div className="relative mb-3 h-2 bg-white/10 rounded">
            <div
              className="absolute h-full"
              style={{
                width: '25%',
                background: '#94a3b8',
              }}
            />
            <div
              className="absolute h-full"
              style={{
                width: `${weights[selectedStrategy] * 100}%`,
                background:
                  weights[selectedStrategy] >= START_WEIGHT
                    ? '#4ade80'
                    : '#ef4444',
                transition: 'width 0.5s ease',
              }}
            />
          </div>

          <hr className="border-slate-700 my-3" />

          <div className="mb-2 text-xs font-semibold text-slate-400 uppercase">
            What This Means
          </div>
          <div className="mb-3 text-sm text-slate-300">
            {STRATEGY_INFO[selectedStrategy].description}
          </div>

          <div className="mb-2 text-xs font-semibold text-slate-400 uppercase">
            Real World Parallel 🌍
          </div>
          <div className="mb-3 italic text-sm text-slate-300">
            {STRATEGY_INFO[selectedStrategy].realWorld}
          </div>

          <div className="mb-3 grid grid-cols-2 gap-4 text-sm">
            <div>
              <div className="font-semibold">✅ Strengths</div>
              <div>{STRATEGY_INFO[selectedStrategy].good}</div>
            </div>
            <div>
              <div className="font-semibold">⚠️ Risks</div>
              <div>{STRATEGY_INFO[selectedStrategy].risk}</div>
            </div>
          </div>

          <div className="mb-2 text-xs font-semibold text-slate-400 uppercase">
            This Simulation
          </div>
          <div className="text-sm text-slate-300 space-y-1">
            {selectedStrategy === 'trade' && (
              <div>Partner trust avg: {avgTrust.toFixed(2)}</div>
            )}
            {selectedStrategy === 'aggress' && weights.aggress > 0.4 && (
              <div className="text-red-400">
                ⚠️ High aggression detected — risk of trust cascade
              </div>
            )}
            {Object.values(weights).some((w) => w > 0.6) && (
              <div className="text-green-400">
                🏆 Dominant strategy — region fully committed to this approach
              </div>
            )}
          </div>
        </div>
      )}
    </div>
  );
}

