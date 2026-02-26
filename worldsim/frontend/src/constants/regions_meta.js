// Regions metadata — static display properties + locked initial values

export const GLOBAL_CONSTANTS = {
    TOTAL_CYCLES: 20,
    CLIMATE_PROBABILITY: 0.15,
    TRADE_THRESHOLD: 60,       // matches backend surplus threshold (>60)
    DEFICIT_THRESHOLD: 40,     // matches backend deficit threshold (<40)
    COLLAPSE_THRESHOLD_POPULATION: 150,
    MAX_RESOURCE: 100,         // backend uses 0-100 scale
    MIN_RESOURCE: 0,
};

// Initial locked state — matches backend regions_config.py exactly (0-100 scale)
export const REGIONS_INITIAL = {
    Aquaria: {
        name: 'Aquaria',
        water: 90, food: 60, energy: 30, land: 70,
        population: 500,
        strategy_weights: { trade: 0.25, hoard: 0.25, invest: 0.25, aggress: 0.25 },
        health_score: 75,
        trust: { Agrovia: 0.5, Petrozon: 0.5, Urbanex: 0.5, Terranova: 0.5 },
    },
    Agrovia: {
        name: 'Agrovia',
        water: 50, food: 95, energy: 40, land: 40,
        population: 600,
        strategy_weights: { trade: 0.25, hoard: 0.25, invest: 0.25, aggress: 0.25 },
        health_score: 75,
        trust: { Aquaria: 0.5, Petrozon: 0.5, Urbanex: 0.5, Terranova: 0.5 },
    },
    Petrozon: {
        name: 'Petrozon',
        water: 30, food: 35, energy: 95, land: 60,
        population: 450,
        strategy_weights: { trade: 0.25, hoard: 0.25, invest: 0.25, aggress: 0.25 },
        health_score: 70,
        trust: { Aquaria: 0.5, Agrovia: 0.5, Urbanex: 0.5, Terranova: 0.5 },
    },
    Urbanex: {
        name: 'Urbanex',
        water: 40, food: 45, energy: 40, land: 30,
        population: 950,
        strategy_weights: { trade: 0.25, hoard: 0.25, invest: 0.25, aggress: 0.25 },
        health_score: 60,
        trust: { Aquaria: 0.5, Agrovia: 0.5, Petrozon: 0.5, Terranova: 0.5 },
    },
    Terranova: {
        name: 'Terranova',
        water: 55, food: 60, energy: 55, land: 90,
        population: 400,
        strategy_weights: { trade: 0.25, hoard: 0.25, invest: 0.25, aggress: 0.25 },
        health_score: 78,
        trust: { Aquaria: 0.5, Agrovia: 0.5, Petrozon: 0.5, Urbanex: 0.5 },
    },
};


// Visual metadata per region
export const REGION_META = {
    Aquaria: {
        color: '#38bdf8',
        glowClass: 'glow-aquaria',
        icon: '💧',
        dominant: 'Water',
        // SVG canvas position (cx, cy) on a 600x380 map
        cx: 110, cy: 130,
    },
    Agrovia: {
        color: '#4ade80',
        glowClass: 'glow-agrovia',
        icon: '🌾',
        dominant: 'Food',
        cx: 320, cy: 90,
    },
    Petrozon: {
        color: '#f59e0b',
        glowClass: 'glow-petrozon',
        icon: '⚡',
        dominant: 'Energy',
        cx: 490, cy: 170,
    },
    Urbanex: {
        color: '#c084fc',
        glowClass: 'glow-urbanex',
        icon: '🏙️',
        dominant: 'Population',
        cx: 200, cy: 280,
    },
    Terranova: {
        color: '#f87171',
        glowClass: 'glow-terranova',
        icon: '🌍',
        dominant: 'Land',
        cx: 400, cy: 290,
    },
};

export const REGION_NAMES = Object.keys(REGIONS_INITIAL);
