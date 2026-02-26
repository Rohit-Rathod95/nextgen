// Regions metadata — static display properties + locked initial values

export const GLOBAL_CONSTANTS = {
    TOTAL_CYCLES: 100,
    CLIMATE_PROBABILITY: 0.15,
    TRADE_THRESHOLD: 80,
    DEFICIT_THRESHOLD: 40,
    COLLAPSE_THRESHOLD_POPULATION: 150,
    MAX_RESOURCE: 200,
    MIN_RESOURCE: 0,
};

// Initial locked state (design spec values)
export const REGIONS_INITIAL = {
    Aquaria: {
        name: 'Aquaria',
        water: 120, food: 70, energy: 50, land: 80,
        population: 500,
        trade_weight: 0.25, hoard_weight: 0.25, invest_weight: 0.25, aggress_weight: 0.25,
        health_score: 0.75,
        trust: { Agrovia: 0.5, Petrozon: 0.5, Urbanex: 0.5, Terranova: 0.5 },
    },
    Agrovia: {
        name: 'Agrovia',
        water: 70, food: 130, energy: 60, land: 60,
        population: 450,
        trade_weight: 0.25, hoard_weight: 0.25, invest_weight: 0.25, aggress_weight: 0.25,
        health_score: 0.75,
        trust: { Aquaria: 0.5, Petrozon: 0.5, Urbanex: 0.5, Terranova: 0.5 },
    },
    Petrozon: {
        name: 'Petrozon',
        water: 60, food: 60, energy: 140, land: 50,
        population: 480,
        trade_weight: 0.25, hoard_weight: 0.25, invest_weight: 0.25, aggress_weight: 0.25,
        health_score: 0.70,
        trust: { Aquaria: 0.5, Agrovia: 0.5, Urbanex: 0.5, Terranova: 0.5 },
    },
    Urbanex: {
        name: 'Urbanex',
        water: 60, food: 60, energy: 60, land: 50,
        population: 700,
        trade_weight: 0.25, hoard_weight: 0.25, invest_weight: 0.25, aggress_weight: 0.25,
        health_score: 0.60,
        trust: { Aquaria: 0.5, Agrovia: 0.5, Petrozon: 0.5, Terranova: 0.5 },
    },
    Terranova: {
        name: 'Terranova',
        water: 80, food: 80, energy: 70, land: 120,
        population: 520,
        trade_weight: 0.25, hoard_weight: 0.25, invest_weight: 0.25, aggress_weight: 0.25,
        health_score: 0.78,
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
