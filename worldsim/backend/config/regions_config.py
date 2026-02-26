"""
regions_config.py — Single Source of Truth for WorldSim

All simulation constants, starting values, consumption rates,
neighbor maps, and region roles are defined here. Every other
module imports from this file — no magic numbers elsewhere.

Region IDs are strictly lowercase throughout.
Resource values use a 0–100 scale.
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

CRITICAL_THRESHOLD = 30       # Resource below this → flagged as critical
EMERGENCY_THRESHOLD = 20      # Resource below this → emergency hoard override
COLLAPSE_THRESHOLD = 20       # Population below this → region collapses

# ---------------------------------------------------------------------------
# Agent Defaults
# ---------------------------------------------------------------------------

INITIAL_TRUST = 50            # Starting trust between all region pairs (0–100)
INITIAL_WEIGHT = 0.25         # Starting weight for each of the 4 strategies

# ---------------------------------------------------------------------------
# Simulation Timing
# ---------------------------------------------------------------------------

CYCLE_SPEED = 1.0             # Seconds between cycles (adjustable)
TOTAL_CYCLES = 100            # Total simulation cycles per run
CLIMATE_EVENT_PROBABILITY = 0.15  # 15% chance of climate event per cycle

# ---------------------------------------------------------------------------
# Locked Starting Values (0–100 resource scale)
# ---------------------------------------------------------------------------

INITIAL_REGIONS = {
    "aquaria": {
        "water": 90,
        "food": 60,
        "energy": 30,
        "land": 70,
        "population": 500,
    },
    "agrovia": {
        "water": 50,
        "food": 95,
        "energy": 40,
        "land": 40,
        "population": 600,
    },
    "petrozon": {
        "water": 30,
        "food": 35,
        "energy": 95,
        "land": 60,
        "population": 450,
    },
    "urbanex": {
        "water": 40,
        "food": 45,
        "energy": 40,
        "land": 30,
        "population": 950,
    },
    "terranova": {
        "water": 55,
        "food": 60,
        "energy": 55,
        "land": 90,
        "population": 400,
    },
}

# ---------------------------------------------------------------------------
# Per-Region Consumption Rates (resource units consumed per cycle)
# ---------------------------------------------------------------------------

CONSUMPTION_RATES = {
    "aquaria":   {"water": 0.8, "food": 0.6, "energy": 0.4, "land": 0.1},
    "agrovia":   {"water": 0.6, "food": 0.9, "energy": 0.5, "land": 0.3},
    "petrozon":  {"water": 0.5, "food": 0.4, "energy": 1.0, "land": 0.2},
    "urbanex":   {"water": 1.0, "food": 0.9, "energy": 0.8, "land": 0.5},
    "terranova": {"water": 0.6, "food": 0.6, "energy": 0.5, "land": 0.2},
}

# ---------------------------------------------------------------------------
# Neighbor Map (which regions can trade/conflict with each other)
# ---------------------------------------------------------------------------

NEIGHBOR_MAP = {
    "aquaria":   ["agrovia", "terranova"],
    "agrovia":   ["aquaria", "petrozon", "urbanex"],
    "petrozon":  ["agrovia", "urbanex", "terranova"],
    "urbanex":   ["agrovia", "petrozon"],
    "terranova": ["aquaria", "petrozon"],
}

# ---------------------------------------------------------------------------
# Region Roles (flavor text for UI and analysis)
# ---------------------------------------------------------------------------

REGION_ROLES = {
    "aquaria":   "Water-rich",
    "agrovia":   "Agriculture-heavy",
    "petrozon":  "Energy-dominant",
    "urbanex":   "Demand-heavy",
    "terranova": "Balanced",
}
