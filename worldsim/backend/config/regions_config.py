"""
regions_config.py — Single Source of Truth for WorldSim

All simulation constants, starting values, consumption rates,
neighbor maps, and region roles are defined here. Every other
module imports from this file — no magic numbers elsewhere.

Region IDs are strictly lowercase throughout.
Resource values use a 0-100 scale.
"""

# ---------------------------------------------------------------------------
# Region & Resource Definitions
# ---------------------------------------------------------------------------

REGIONS = ["aquaria", "agrovia", "petrozon", "urbanex", "terranova"]

RESOURCES = ["water", "food", "energy", "land"]

ACTIONS = ["trade", "hoard", "invest", "aggress"]

# ---------------------------------------------------------------------------
# Thresholds
# ---------------------------------------------------------------------------

CRITICAL_THRESHOLD = 30       # Resource below this -> flagged as critical
EMERGENCY_THRESHOLD = 15      # Resource below this -> emergency hoard override (lowered from 20)
COLLAPSE_THRESHOLD = 20       # Health below this -> region collapses
SURPLUS_THRESHOLD = 55        # Resource above this -> tradeable surplus (lowered from 60)
DEFICIT_THRESHOLD = 45        # Resource below this -> region needs this resource (raised from 40)
TRADE_TRUST_MINIMUM = 30      # Minimum trust to propose trade (lowered from 40)
RECEIVER_HAS_THRESHOLD = 35   # Receiver must have > this to give resource in trade

# ---------------------------------------------------------------------------
# Agent Defaults
# ---------------------------------------------------------------------------

INITIAL_TRUST = 50            # Starting trust between all region pairs (0-100)
INITIAL_WEIGHT = 0.25         # Starting weight for each of the 4 strategies

# ---------------------------------------------------------------------------
# Simulation Timing
# ---------------------------------------------------------------------------

CYCLE_SPEED = 1.0             # Seconds between cycles (adjustable)
TOTAL_CYCLES = 100            # Total simulation cycles per run
CLIMATE_EVENT_PROBABILITY = 0.15  # 15% chance of climate event per cycle

# ---------------------------------------------------------------------------
# Locked Starting Values (0-100 resource scale)
# Tuned so every region has at least one clear need and one clear surplus,
# ensuring trade pressure exists from cycle 1.
# ---------------------------------------------------------------------------

INITIAL_REGIONS = {
    "aquaria": {
        # Amazon basin: water rich, energy poor -> needs energy from Petrozon
        "water": 80, "food": 50, "energy": 25, "land": 60,
        "population": 500,
    },
    "agrovia": {
        # South Asia: food rich, water moderate, energy poor
        "water": 40, "food": 85, "energy": 35, "land": 35,
        "population": 600,
    },
    "petrozon": {
        # Middle East: energy rich, water/food very poor -> strong trade motivation
        "water": 25, "food": 30, "energy": 85, "land": 50,
        "population": 450,
    },
    "urbanex": {
        # China: high population, moderate resources, manufacturing leverage
        "water": 35, "food": 40, "energy": 35, "land": 25,
        "population": 950,
    },
    "terranova": {
        # Brazil interior: balanced, large land for investment
        "water": 50, "food": 55, "energy": 50, "land": 80,
        "population": 400,
    },
}

# ---------------------------------------------------------------------------
# Per-Region Consumption Rates (resource units consumed per cycle at pop=1000)
# ---------------------------------------------------------------------------

CONSUMPTION_RATES = {
    "aquaria":   {"water": 0.8, "food": 0.6, "energy": 0.4, "land": 0.1},
    "agrovia":   {"water": 0.6, "food": 0.9, "energy": 0.5, "land": 0.3},
    "petrozon":  {"water": 0.5, "food": 0.4, "energy": 1.0, "land": 0.2},
    "urbanex":   {"water": 1.0, "food": 0.9, "energy": 0.8, "land": 0.5},
    "terranova": {"water": 0.6, "food": 0.6, "energy": 0.5, "land": 0.2},
}

# ---------------------------------------------------------------------------
# Neighbor Map — global trade (all-to-all mirrors modern global trade).
# Distance penalty: after cycle 30, non-adjacent trades transfer fewer units.
# ---------------------------------------------------------------------------

NEIGHBOR_MAP = {
    "aquaria":   ["agrovia", "petrozon", "urbanex", "terranova"],
    "agrovia":   ["aquaria", "petrozon", "urbanex", "terranova"],
    "petrozon":  ["aquaria", "agrovia",  "urbanex", "terranova"],
    "urbanex":   ["aquaria", "agrovia",  "petrozon", "terranova"],
    "terranova": ["aquaria", "agrovia",  "petrozon", "urbanex"],
}

# Adjacent pairs (shorter distance, full transfer amount)
ADJACENT_PAIRS = {
    frozenset(["aquaria",   "agrovia"]),
    frozenset(["aquaria",   "terranova"]),
    frozenset(["agrovia",   "petrozon"]),
    frozenset(["agrovia",   "urbanex"]),
    frozenset(["petrozon",  "urbanex"]),
    frozenset(["petrozon",  "terranova"]),
}

# ---------------------------------------------------------------------------
# Special Abilities — each region has a unique passive or active edge
# ---------------------------------------------------------------------------

SPECIAL_ABILITIES = {
    "aquaria": {
        # Amazon basin: rivers and rainfall replenish water naturally
        "ability": "water_regeneration",
        "resource": "water",
        "regen_rate": 2.0,
        "description": "Amazon basin natural water cycle",
    },
    "agrovia": {
        # Monsoon agriculture: food regenerates if enough land is cultivated
        "ability": "food_regeneration",
        "resource": "food",
        "regen_rate": 3.0,
        "land_threshold": 30,
        "description": "Monsoon agricultural cycle",
    },
    "petrozon": {
        # Vast oil reserves: energy base-level regeneration from extraction
        "ability": "energy_regeneration",
        "resource": "energy",
        "regen_rate": 1.5,
        "description": "Vast oil reserve base",
    },
    "urbanex": {
        # Manufacturing economy: offer manufactured goods instead of raw resources
        "ability": "manufacturing_power",
        "initial_value": 85,
        "trade_trust_bonus": -10,      # lower trust required to trade
        "trade_amount_bonus": 5,       # extra units gained per trade
        "invest_improvement": 3,       # bonus resource gain per invest cycle
        "description": "Manufacturing export economy",
    },
    "terranova": {
        # Undeveloped land: investment yields higher returns than other regions
        "ability": "land_development",
        "invest_multiplier": 1.8,
        "description": "Undeveloped land potential",
    },
}

# ---------------------------------------------------------------------------
# Region Roles (flavor text for UI and analysis)
# ---------------------------------------------------------------------------

REGION_ROLES = {
    "aquaria":   "Water-rich / Amazon Basin",
    "agrovia":   "Agriculture-heavy / South Asia",
    "petrozon":  "Energy-dominant / Middle East",
    "urbanex":   "Manufacturing / East Asia",
    "terranova": "Balanced / South America",
}
