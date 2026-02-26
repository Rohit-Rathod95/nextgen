"""
regions_config.py

Global constants and initial region values for the simulation.
"""

TOTAL_CYCLES = 100
CLIMATE_PROBABILITY = 0.15
DEFICIT_THRESHOLD = 40
SURPLUS_THRESHOLD = 80
COLLAPSE_THRESHOLD_POPULATION = 150
MAX_RESOURCE = 200.0
MIN_RESOURCE = 0.0
CONSUMPTION_RATE = 0.002

INITIAL_REGIONS = {
    "Aquaria": {
        "water": 180.0,
        "food": 120.0,
        "energy": 90.0,
        "land": 100.0,
        "population": 500.0,
    },
    "Agrovia": {
        "water": 120.0,
        "food": 180.0,
        "energy": 80.0,
        "land": 150.0,
        "population": 600.0,
    },
    "Petrozon": {
        "water": 60.0,
        "food": 80.0,
        "energy": 180.0,
        "land": 120.0,
        "population": 450.0,
    },
    "Urbanex": {
        "water": 100.0,
        "food": 100.0,
        "energy": 140.0,
        "land": 180.0,
        "population": 800.0,
    },
    "Terranova": {
        "water": 140.0,
        "food": 150.0,
        "energy": 120.0,
        "land": 200.0,
        "population": 550.0,
    }
}
