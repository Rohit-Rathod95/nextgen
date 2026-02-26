"""
climate.py — Climate Event Engine for WorldSim

Generates random environmental events each cycle that impact
regional resources. Events fire with a configurable probability
(default 15%) and affect 1-2 randomly chosen regions.

Negative severity = positive event (resource increases).
Positive severity = negative event (resource decreases).
"""

import random
from config.regions_config import CLIMATE_EVENT_PROBABILITY


# ---------------------------------------------------------------------------
# Event Definitions
# ---------------------------------------------------------------------------

EVENTS = [
    {
        "type": "drought",
        "targets": ["water"],
        "severity": 0.45,  # harsher drought
        "description": "Severe drought depletes water reserves",
    },
    {
        "type": "flood",
        "targets": ["food"],
        "severity": 0.20,
        "description": "Flooding destroys food supplies",
    },
    {
        "type": "energy_crisis",
        "targets": ["energy"],
        "severity": 0.40,  # stronger impact
        "description": "Energy infrastructure failure",
    },
    {
        "type": "fertile_season",
        "targets": ["food", "land"],
        "severity": -0.15,
        "description": "Exceptional growing season boosts food",
    },
    {
        "type": "solar_surge",
        "targets": ["energy"],
        "severity": -0.20,
        "description": "Abundant solar energy production",
    },
]


# ===========================================================================
# Functions
# ===========================================================================

def should_fire_event() -> bool:
    """
    Roll the dice — returns True if a climate event should fire
    this cycle based on CLIMATE_EVENT_PROBABILITY (default 15%).

    Returns:
        True if event fires, False otherwise.
    """
    return random.random() < CLIMATE_EVENT_PROBABILITY


def get_random_event() -> dict:
    """
    Pick a random climate event from the event pool.

    Returns:
        Event dict with type, targets, severity, and description.
    """
    return random.choice(EVENTS)


def apply_event(region, event: dict) -> dict:
    """
    Apply a climate event to a region, modifying target resources.

    For positive severity (bad events): resource decreases.
    For negative severity (good events): resource increases.

    All resources are clamped to [0, 100] after modification.

    Args:
        region: Region object with resource attributes.
        event:  Event dict from EVENTS list.

    Returns:
        Event log dict for recording in Firestore.
    """
    for target in event["targets"]:
        current = getattr(region, target, 0)
        change = current * event["severity"]
        new_value = current - change
        # Clamp to [0, 100]
        new_value = max(0.0, min(100.0, new_value))
        setattr(region, target, new_value)

    return {
        "type": event["type"],
        "affected_region": region.region_id,
        "description": event["description"],
        "severity": event["severity"],
    }


def run_climate_phase(regions_list: list) -> list:
    """
    Run the climate phase for one cycle. Randomly selects 1-2 regions
    and rolls for a climate event on each.

    Args:
        regions_list: List of Region objects.

    Returns:
        List of event log dicts for events that fired.
    """
    if not regions_list:
        return []

    events_fired = []

    # Pick 1 or 2 random regions
    count = random.randint(1, min(2, len(regions_list)))
    targets = random.sample(regions_list, count)

    for region in targets:
        if should_fire_event():
            event = get_random_event()
            log = apply_event(region, event)
            events_fired.append(log)

    return events_fired


# ===========================================================================
# Test Cases
# ===========================================================================

if __name__ == "__main__":

    PASS = "[PASS]"
    FAIL = "[FAIL]"

    # Simple mock region for testing
    class MockRegion:
        def __init__(self, region_id, water, food, energy, land):
            self.region_id = region_id
            self.water = float(water)
            self.food = float(food)
            self.energy = float(energy)
            self.land = float(land)

    # ===================================================================
    # TEST 1 — Drought on Aquaria
    # ===================================================================
    print("=" * 60)
    print("  TEST 1 - Drought Applied to Aquaria")
    print("=" * 60)

    r = MockRegion("aquaria", water=90, food=60, energy=30, land=70)
    drought = EVENTS[0]  # drought

    print(f"  Before: water={r.water:.1f}")
    log = apply_event(r, drought)
    expected = 90 - (90 * 0.30)  # 63.0
    print(f"  After:  water={r.water:.1f} (expected {expected:.1f})")
    print(f"  Match?  {PASS if abs(r.water - expected) < 0.01 else FAIL}")
    print(f"  Log:    {log}")
    print()

    # ===================================================================
    # TEST 2 — Flood on Agrovia
    # ===================================================================
    print("=" * 60)
    print("  TEST 2 - Flood Applied to Agrovia")
    print("=" * 60)

    r2 = MockRegion("agrovia", water=50, food=95, energy=40, land=40)
    flood = EVENTS[1]  # flood

    print(f"  Before: food={r2.food:.1f}")
    log2 = apply_event(r2, flood)
    expected2 = 95 - (95 * 0.20)  # 76.0
    print(f"  After:  food={r2.food:.1f} (expected {expected2:.1f})")
    print(f"  Match?  {PASS if abs(r2.food - expected2) < 0.01 else FAIL}")
    print()

    # ===================================================================
    # TEST 3 — Fertile Season (positive event)
    # ===================================================================
    print("=" * 60)
    print("  TEST 3 - Fertile Season (Positive Event)")
    print("=" * 60)

    r3 = MockRegion("terranova", water=55, food=60, energy=55, land=90)
    fertile = EVENTS[3]  # fertile_season, severity=-0.15

    print(f"  Before: food={r3.food:.1f}, land={r3.land:.1f}")
    log3 = apply_event(r3, fertile)
    # severity=-0.15 → change = 60 * -0.15 = -9.0 → new = 60 - (-9) = 69
    print(f"  After:  food={r3.food:.1f}, land={r3.land:.1f}")
    food_increased = r3.food > 60
    print(f"  Food increased? {PASS if food_increased else FAIL}")
    print()

    # ===================================================================
    # TEST 4 — Clamping at 100
    # ===================================================================
    print("=" * 60)
    print("  TEST 4 - Clamping at 100 Maximum")
    print("=" * 60)

    r4 = MockRegion("petrozon", water=30, food=35, energy=95, land=60)
    solar = EVENTS[4]  # solar_surge, severity=-0.20

    print(f"  Before: energy={r4.energy:.1f}")
    apply_event(r4, solar)
    # 95 - (95 * -0.20) = 95 + 19 = 114 → clamped to 100
    print(f"  After:  energy={r4.energy:.1f} (clamped to 100)")
    print(f"  Clamped? {PASS if r4.energy == 100.0 else FAIL}")
    print()

    # ===================================================================
    # TEST 5 — run_climate_phase
    # ===================================================================
    print("=" * 60)
    print("  TEST 5 - run_climate_phase (10 runs)")
    print("=" * 60)

    regions = [
        MockRegion("aquaria", 90, 60, 30, 70),
        MockRegion("agrovia", 50, 95, 40, 40),
        MockRegion("petrozon", 30, 35, 95, 60),
        MockRegion("urbanex", 40, 45, 40, 30),
        MockRegion("terranova", 55, 60, 55, 90),
    ]

    total_events = 0
    for run in range(10):
        events = run_climate_phase(regions)
        total_events += len(events)

    print(f"  Events over 10 runs: {total_events}")
    print(f"  Some fired? {PASS if total_events > 0 else FAIL}")
    print()

    # ===================================================================
    print("=" * 60)
    print("  All climate tests complete")
    print("=" * 60)
