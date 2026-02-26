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
TOTAL_CYCLES = 20  # shortened demo to 20 cycles (1 cycle = 1 year)
CLIMATE_EVENT_PROBABILITY = 0.50   # 50% chance per region per cycle (very frequent climate drama)

# ---------------------------------------------------------------------------
# Population Dynamics (in region.py, not here — kept for cross-module ref)
# ---------------------------------------------------------------------------

POPULATION_GROWTH_RATE       = 0.05   # +5% per year when thriving
POPULATION_DECLINE_RATE      = 0.08   # -8% when under stress
POPULATION_COLLAPSE_RATE     = 0.20   # -20% rapid collapse
POPULATION_MIN               = 50
THRIVING_THRESHOLD           = 55    # easier to trigger growth
STRESS_THRESHOLD             = 35    # stress kicks in earlier
COLLAPSE_RESOURCE_THRESHOLD  = 18    # slightly higher collapse trigger

# ---------------------------------------------------------------------------
# Starting Values — tuned so every region has a clear surplus + deficit
# ---------------------------------------------------------------------------

INITIAL_REGIONS = {
    "aquaria": {
        "water": 70,
        "food": 40,
        "energy": 20,
        "land": 55,
        "population": 500,
    },
    "agrovia": {
        "water": 35,
        "food": 75,
        "energy": 30,
        "land": 30,
        "population": 600,
    },
    "petrozon": {
        "water": 20,
        "food": 25,
        "energy": 80,
        "land": 45,
        "population": 450,
    },
    "urbanex": {
        "water": 30,
        "food": 35,
        "energy": 30,
        "land": 20,
        "population": 950,
    },
    "terranova": {
        "water": 45,
        "food": 50,
        "energy": 45,
        "land": 75,
        "population": 400,
    },
}

# ---------------------------------------------------------------------------
# Consumption Rates (units per 1000 population per cycle)
# Raised to create real scarcity pressure and trade incentive
# ---------------------------------------------------------------------------

CONSUMPTION_RATES = {
    "aquaria": {
        "water": 2.5,
        "food": 1.8,
        "energy": 1.2,
        "land": 0.5,
    },
    "agrovia": {
        "water": 2.0,
        "food": 3.0,
        "energy": 1.5,
        "land": 1.0,
    },
    "petrozon": {
        "water": 1.8,
        "food": 1.5,
        "energy": 3.5,
        "land": 0.8,
    },
    "urbanex": {
        "water": 3.5,
        "food": 3.5,
        "energy": 3.0,
        "land": 2.0,
    },
    "terranova": {
        "water": 1.5,
        "food": 2.0,
        "energy": 1.5,
        "land": 0.8,
    },
}

# ---------------------------------------------------------------------------
# Special Abilities - unique passive per region (applied after consume)
# ---------------------------------------------------------------------------

SPECIAL_ABILITIES = {
    "aquaria": {
        "ability": "water_regeneration",
        "resource": "water",
        "regen_rate": 5.0,
    },
    "agrovia": {
        "ability": "food_regeneration",
        "resource": "food",
        "regen_rate": 6.0,
        "land_threshold": 25,
    },
    "petrozon": {
        "ability": "energy_regeneration",
        "resource": "energy",
        "regen_rate": 5.0,
    },
    "urbanex": {
        "ability": "manufacturing_power",
        "initial_value": 85,
        "trade_trust_bonus": 15,
        "trade_amount_bonus": 5,
        "regen_rate": 2.0,
    },
    "terranova": {
        "ability": "land_development",
        "invest_multiplier": 2.5,
        "regen_rate": 3.0,
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
    "trade_success": {
        "trade": 0.15,
        "aggress": -0.05
    },
    "trade_rejected": {
        "trade": -0.12,
        "hoard": 0.10
    },
    "hoard_success": {
        "hoard": 0.14,
        "invest": -0.05
    },
    "hoard_hurt": {
        "hoard": -0.14,
        "trade": 0.08
    },
    "invest_payoff": {
        "invest": 0.15,
        "hoard": -0.04
    },
    "aggress_success": {
        "aggress": 0.15,
        "trade": -0.08
    },
    "aggress_failed": {
        "aggress": -0.18,
        "hoard": 0.10
    },
    "emergency_hoard": {
        "hoard": 0.20,
        "aggress": 0.05,
        "invest": -0.12,
        "trade": -0.13
    }
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
