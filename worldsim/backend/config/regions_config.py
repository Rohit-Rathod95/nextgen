"""
regions_config.py - Single Source of Truth for WorldSim

All simulation constants, starting values, consumption rates,
neighbor maps, and region roles defined here. No magic numbers elsewhere.

Region IDs: strictly lowercase. Resources: 0-100 scale.
"""

# ---------------------------------------------------------------------------
# Region & Resource Lists
# ---------------------------------------------------------------------------

REGIONS  = ["aquaria", "agrovia", "petrozon", "urbanex", "terranova"]
RESOURCES = ["water", "food", "energy", "land"]
ACTIONS   = ["trade", "hoard", "invest", "aggress"]

# ---------------------------------------------------------------------------
# Thresholds
# ---------------------------------------------------------------------------

CRITICAL_THRESHOLD  = 30    # Resource below this -> flagged critical
EMERGENCY_THRESHOLD = 15    # Resource below this -> emergency override
COLLAPSE_THRESHOLD  = 15    # Health below this -> collapse check
COLLAPSE_POPULATION = 100   # Population below this -> collapse eligible

SURPLUS_THRESHOLD   = 55    # Resource above this -> tradeable surplus
DEFICIT_THRESHOLD   = 45    # Resource below this -> region needs it

TRADE_TRUST_MINIMUM = 20    # Min trust to propose trade (global trade model)  # lowered to encourage early alliances

# ---------------------------------------------------------------------------
# Agent Defaults
# ---------------------------------------------------------------------------

INITIAL_TRUST  = 50    # Starting trust between all region pairs (0-100)
INITIAL_WEIGHT = 0.25  # Starting weight for each of 4 strategies

# ---------------------------------------------------------------------------
# Simulation Timing
# ---------------------------------------------------------------------------

CYCLE_SPEED = 1.0
TOTAL_CYCLES = 100
CLIMATE_EVENT_PROBABILITY = 0.30   # 30% chance per cycle (higher to force more climate events)

# ---------------------------------------------------------------------------
# Population Dynamics (in region.py, not here — kept for cross-module ref)
# ---------------------------------------------------------------------------

POPULATION_GROWTH_RATE       = 0.02
POPULATION_DECLINE_RATE      = 0.03
POPULATION_COLLAPSE_RATE     = 0.10
POPULATION_MIN               = 50
THRIVING_THRESHOLD           = 60    # avg resources > this -> grow
STRESS_THRESHOLD             = 30    # avg resources < this -> decline
COLLAPSE_RESOURCE_THRESHOLD  = 15    # avg resources < this -> collapse rate

# ---------------------------------------------------------------------------
# Starting Values — tuned so every region has a clear surplus + deficit
# ---------------------------------------------------------------------------

INITIAL_REGIONS = {
    "aquaria": {
        # Brazil: water-rich, energy-poor -> strong pull towards Petrozon trade
        "water": 80, "food": 50, "energy": 25, "land": 60,
        "population": 500,
    },
    "agrovia": {
        # India: food-rich, land-hungry, energy deficit
        "water": 40, "food": 85, "energy": 35, "land": 35,
        "population": 600,
    },
    "petrozon": {
        # Gulf States: energy-rich, water/food critical -> must trade or collapse
        "water": 25, "food": 30, "energy": 85, "land": 50,
        "population": 450,
    },
    "urbanex": {
        # China: high pop, moderate resources, manufacturing leverage
        "water": 35, "food": 40, "energy": 35, "land": 25,
        "population": 950,
    },
    "terranova": {
        # Africa: land-rich, developing, balanced but plenty of room to grow
        "water": 50, "food": 55, "energy": 50, "land": 80,
        "population": 400,
    },
}

# ---------------------------------------------------------------------------
# Consumption Rates (units per 1000 population per cycle)
# Raised to create real scarcity pressure and trade incentive
# ---------------------------------------------------------------------------

CONSUMPTION_RATES = {
    "aquaria":   {"water": 1.4, "food": 1.0, "energy": 0.7, "land": 0.2},
    "agrovia":   {"water": 1.1, "food": 1.6, "energy": 0.8, "land": 0.5},
    "petrozon":  {"water": 0.9, "food": 0.8, "energy": 1.8, "land": 0.3},
    "urbanex":   {"water": 1.8, "food": 1.7, "energy": 1.5, "land": 0.9},
    "terranova": {"water": 0.9, "food": 1.0, "energy": 0.8, "land": 0.3},
}

# ---------------------------------------------------------------------------
# Special Abilities - unique passive per region (applied after consume)
# ---------------------------------------------------------------------------

SPECIAL_ABILITIES = {
    "aquaria": {
        # Amazon basin: continuous water cycle replenishment
        "ability": "water_regeneration",
        "resource": "water",
        "regen_rate": 3.0,
        "description": "Amazon basin natural water cycle",
    },
    "agrovia": {
        # Monsoon agriculture: food regenerates if enough land cultivated
        "ability": "food_regeneration",
        "resource": "food",
        "regen_rate": 3.0,
        "land_threshold": 25,
        "description": "Monsoon agricultural cycle",
    },
    "petrozon": {
        # Vast oil reserves: passive energy extraction each cycle
        "ability": "energy_regeneration",
        "resource": "energy",
        "regen_rate": 2.5,
        "description": "Vast oil reserve base",
    },
    "urbanex": {
        # China's manufacturing economy: trade without resource surplus
        "ability": "manufacturing_power",
        "initial_value": 85,
        "regen_rate": 1.0,          # manufacturing rebuilds 1/cycle when not trading
        "trade_trust_bonus": 15,
        "trade_amount_bonus": 5,
        "invest_improvement": 3,
        "description": "Manufacturing export economy",
    },
    "terranova": {
        # Undeveloped land: invest yields multiplied returns
        "ability": "land_development",
        "invest_multiplier": 2.0,
        "regen_rate": 1.5,          # passive land improvement from development
        "description": "Undeveloped land potential",
    },
}

# ---------------------------------------------------------------------------
# Neighbor Map — all-to-all (global trade, mirrors modern reality)
# ---------------------------------------------------------------------------

NEIGHBOR_MAP = {
    "aquaria":   ["agrovia", "petrozon", "urbanex", "terranova"],
    "agrovia":   ["aquaria", "petrozon", "urbanex", "terranova"],
    "petrozon":  ["aquaria", "agrovia",  "urbanex", "terranova"],
    "urbanex":   ["aquaria", "agrovia",  "petrozon", "terranova"],
    "terranova": ["aquaria", "agrovia",  "petrozon", "urbanex"],
}

# ---------------------------------------------------------------------------
# Adjacent pairs - shorter supply chains, full transfer amount
# ---------------------------------------------------------------------------

ADJACENT_PAIRS = {
    frozenset(["aquaria",   "agrovia"]),
    frozenset(["aquaria",   "terranova"]),
    frozenset(["agrovia",   "petrozon"]),
    frozenset(["agrovia",   "urbanex"]),
    frozenset(["petrozon",  "urbanex"]),
    frozenset(["petrozon",  "terranova"]),
}

# ---------------------------------------------------------------------------
# Agent weight update rules (used in agent.py)
# ---------------------------------------------------------------------------

WEIGHT_UPDATE_RULES = {
    "trade_success":        {"trade":  0.08, "aggress": -0.03},
    "trade_rejected":       {"trade": -0.06, "hoard":   0.05},
    "hoard_success":        {"hoard":  0.07, "invest":  -0.03},
    "hoard_hurt":           {"hoard": -0.07, "trade":   0.04},
    "invest_payoff":        {"invest": 0.08, "hoard":  -0.02},
    "aggress_success":      {"aggress": 0.08, "trade":  -0.05},
    "aggress_failed":       {"aggress": -0.10, "hoard":  0.05},
    "emergency_hoard":      {"hoard":  0.12, "aggress": 0.03,
                             "invest": -0.08, "trade":  -0.07},
}

# ---------------------------------------------------------------------------
# Region Roles (flavor text)
# ---------------------------------------------------------------------------

REGION_ROLES = {
    "aquaria":   "Water-rich / Amazon Basin (Brazil)",
    "agrovia":   "Agriculture-heavy / South Asia (India)",
    "petrozon":  "Energy-dominant / Gulf States",
    "urbanex":   "Manufacturing superpower / East Asia (China)",
    "terranova": "Balanced / Developing Africa",
}
