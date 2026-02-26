// StrategyRadar component — Chart.js radar chart visualizing trade, hoard, invest, aggress weights.
import React from 'react';
import {
    Chart as ChartJS,
    RadialLinearScale,
    PointElement,
    LineElement,
    Filler,
    Tooltip,
} from 'chart.js';
import { Radar } from 'react-chartjs-2';
import { REGION_META } from '../constants/regions_meta';

ChartJS.register(RadialLinearScale, PointElement, LineElement, Filler, Tooltip);

const LABELS = ['Trade', 'Hoard', 'Invest', 'Aggress'];

export default function StrategyRadar({ region, regionName }) {
    if (!region) return null;

    const meta = REGION_META[regionName] || {};
    const color = meta.color || '#38bdf8';

    const values = [
        region.trade_weight ?? 0.25,
        region.hoard_weight ?? 0.25,
        region.invest_weight ?? 0.25,
        region.aggress_weight ?? 0.25,
    ];

    const data = {
        labels: LABELS,
        datasets: [
            {
                data: values,
                backgroundColor: `${color}25`,
                borderColor: color,
                borderWidth: 2,
                pointBackgroundColor: color,
                pointBorderColor: '#1e293b',
                pointRadius: 4,
                pointHoverRadius: 6,
            },
        ],
    };

    const options = {
        responsive: true,
        maintainAspectRatio: true,
        scales: {
            r: {
                min: 0,
                max: 1,
                ticks: {
                    display: false,
                    stepSize: 0.25,
                },
                grid: {
                    color: 'rgba(71,85,105,0.4)',
                    circular: true,
                },
                angleLines: {
                    color: 'rgba(71,85,105,0.4)',
                },
                pointLabels: {
                    color: '#94a3b8',
                    font: {
                        family: 'Inter, sans-serif',
                        size: 11,
                        weight: '500',
                    },
                },
            },
        },
        plugins: {
            tooltip: {
                callbacks: {
                    label: (ctx) => ` ${(ctx.raw * 100).toFixed(1)}%`,
                },
                backgroundColor: '#1e293b',
                borderColor: '#334155',
                borderWidth: 1,
                titleColor: '#e2e8f0',
                bodyColor: '#94a3b8',
            },
            legend: { display: false },
        },
    };

    // Dominant strategy label
    const maxIdx = values.indexOf(Math.max(...values));
    const dominant = LABELS[maxIdx];

    return (
        <div>
            <div className="flex justify-between items-center mb-2">
                <span className="text-xs font-medium text-slate-400">STRATEGY WEIGHTS</span>
                <span
                    className="text-xs font-mono px-2 py-0.5 rounded"
                    style={{ background: `${color}20`, color }}
                >
                    ▲ {dominant}
                </span>
            </div>
            <Radar data={data} options={options} />
            {/* Legend row */}
            <div className="grid grid-cols-2 gap-1 mt-2">
                {LABELS.map((lbl, i) => (
                    <div key={lbl} className="flex justify-between text-xs">
                        <span className="text-slate-500">{lbl}</span>
                        <span className="font-mono" style={{ color }}>
                            {(values[i] * 100).toFixed(1)}%
                        </span>
                    </div>
                ))}
            </div>
        </div>
    );
}
