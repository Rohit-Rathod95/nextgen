"""
conflict.py — Conflict Resolution System for WorldSim

Handles aggression between neighboring regions. Attackers need a
clear strength advantage (1.2x) to win. Conflict always costs energy
for both sides. Trust collapses across ALL observer regions when
conflict occurs — not just the combatants.

Strength = 50% energy + 50% population factor.
"""

from config.regions_config import NEIGHBOR_MAP, RESOURCES


# ---------------------------------------------------------------------------
# Constants
# ---------------------------------------------------------------------------

STRENGTH_THRESHOLD = 1.2    # Attacker must exceed defender × this
ATTACKER_WIN_FOOD_STEAL = 15
ATTACKER_WIN_WATER_STEAL = 10
ATTACKER_WIN_ENERGY_COST = 15
ATTACKER_LOSE_ENERGY_COST = 25
DEFENDER_WIN_ENERGY_COST = 15
DEFENDER_LOSE_ENERGY_COST = 10
TRUST_CASCADE_PENALTY = 10
TRUST_DEFENDER_EXTRA_PENALTY = 25
TRUST_MIN_FOR_AGGRESS = 20  # Attacker trust toward target must be < this


# ===========================================================================
# FUNCTION 1 — Calculate Strength
# ===========================================================================

def calculate_strength(region) -> float:
    """
    Calculate a region's combat strength.

    Formula:
        strength = energy × 0.5 + (population / 100) × 0.5

    Args:
        region: Region object with energy and population attributes.

    Returns:
        Strength score as a float.
    """
    energy = getattr(region, "energy", 0)
    population = getattr(region, "population", 0)
    return (energy * 0.5) + (population / 100.0 * 0.5)


# ===========================================================================
# FUNCTION 2 — Get Conflict Target
# ===========================================================================

def get_conflict_target(attacker, all_regions: list):
    """
    Find the weakest valid conflict target for the attacker.

    Valid targets must:
        1. Be a neighbor (in NEIGHBOR_MAP)
        2. Have trust < 20 from attacker's perspective
        3. Have lower health_score than attacker
        4. Not be collapsed

    Args:
        attacker:    Region object initiating aggression.
        all_regions: List of all Region objects.

    Returns:
        Weakest valid Region object, or None if no valid target.
    """
    neighbors = NEIGHBOR_MAP.get(attacker.region_id, [])
    attacker_health = getattr(attacker, "health_score", 0)
    valid = []

    for region in all_regions:
        if region.region_id == attacker.region_id:
            continue

        # Must be neighbor
        if region.region_id not in neighbors:
            continue

        # Trust must be low (hostility threshold)
        trust = attacker.trust_scores.get(region.region_id, 50)
        if trust >= TRUST_MIN_FOR_AGGRESS:
            continue

        # Target must be weaker
        target_health = getattr(region, "health_score", 100)
        if target_health >= attacker_health:
            continue

        # Target must not be collapsed
        if getattr(region, "is_collapsed", False):
            continue

        valid.append(region)

    if not valid:
        return None

    # Return weakest by health_score
    return min(valid, key=lambda r: getattr(r, "health_score", 100))


# ===========================================================================
# FUNCTION 3 — Resolve Conflict
# ===========================================================================

def resolve_conflict(attacker, defender, all_regions: list) -> str:
    """
    Resolve a conflict between attacker and defender.

    Attacker wins if their strength exceeds defender × 1.2.

    On win:
        - Attacker steals food (up to 15) and water (up to 10)
        - Attacker loses 15 energy, defender loses 10 energy

    On loss:
        - Attacker loses 25 energy, defender loses 15 energy
        - No resources stolen

    Trust cascade: ALL regions reduce trust toward attacker by 10.
    Defender gets an additional 25 trust penalty toward attacker.

    All resource values clamped to [0, 100].

    Args:
        attacker:    Region object initiating aggression.
        defender:    Region object being attacked.
        all_regions: List of all Region objects.

    Returns:
        Outcome string: "aggress_success" or "aggress_failed".
    """
    att_strength = calculate_strength(attacker)
    def_strength = calculate_strength(defender)

    if att_strength > def_strength * STRENGTH_THRESHOLD:
        # --- ATTACKER WINS ---
        stolen_food = min(ATTACKER_WIN_FOOD_STEAL, defender.food)
        stolen_water = min(ATTACKER_WIN_WATER_STEAL, defender.water)

        # Resource transfer
        attacker.food += stolen_food
        attacker.water += stolen_water
        defender.food -= stolen_food
        defender.water -= stolen_water

        # Energy cost for both
        attacker.energy -= ATTACKER_WIN_ENERGY_COST
        defender.energy -= DEFENDER_LOSE_ENERGY_COST

        outcome = "aggress_success"
    else:
        # --- ATTACKER LOSES ---
        attacker.energy -= ATTACKER_LOSE_ENERGY_COST
        defender.energy -= DEFENDER_WIN_ENERGY_COST

        outcome = "aggress_failed"

    # Clamp all resource values to [0, 100]
    for region in (attacker, defender):
        for res in RESOURCES:
            val = getattr(region, res, 0)
            setattr(region, res, max(0.0, min(100.0, val)))

    # --- TRUST CASCADE ---
    # Every region loses trust toward the attacker
    for region in all_regions:
        if region.region_id == attacker.region_id:
            continue
        current = region.trust_scores.get(attacker.region_id, 50)
        region.trust_scores[attacker.region_id] = max(
            0, current - TRUST_CASCADE_PENALTY
        )

    # Defender gets additional trust penalty
    current_def = defender.trust_scores.get(attacker.region_id, 50)
    defender.trust_scores[attacker.region_id] = max(
        0, current_def - TRUST_DEFENDER_EXTRA_PENALTY
    )

    return outcome


# ===========================================================================
# FUNCTION 4 — Run Conflict Phase
# ===========================================================================

def run_conflict_phase(regions_list: list) -> list:
    """
    Run the conflict phase for one cycle. Each region whose
    last_action is "aggress" attempts to attack the weakest
    valid neighbor.

    Args:
        regions_list: List of all Region objects.

    Returns:
        List of conflict event log dicts.
    """
    conflict_events = []

    for region in regions_list:
        if getattr(region, "last_action", "none") != "aggress":
            continue

        target = get_conflict_target(region, regions_list)
        if target is None:
            continue

        outcome = resolve_conflict(region, target, regions_list)

        # Build description
        att_name = region.region_id.capitalize()
        def_name = target.region_id.capitalize()

        if outcome == "aggress_success":
            desc = (
                f"{att_name} attacked {def_name} and seized food "
                f"and water resources. All regions lost trust in "
                f"{att_name}."
            )
        else:
            desc = (
                f"{att_name} attacked {def_name} but was repelled. "
                f"Both sides suffered heavy energy losses. "
                f"Global trust in {att_name} collapsed."
            )

        conflict_events.append({
            "type": "conflict",
            "source_region": region.region_id,
            "target_region": target.region_id,
            "outcome": outcome,
            "description": desc,
        })

    return conflict_events


# ===========================================================================
# Test Cases
# ===========================================================================

if __name__ == "__main__":

    PASS = "[PASS]"
    FAIL = "[FAIL]"

    class MockRegion:
        def __init__(self, rid, w, f, e, l, pop=500, health=50):
            self.region_id = rid
            self.water = float(w)
            self.food = float(f)
            self.energy = float(e)
            self.land = float(l)
            self.population = float(pop)
            self.health_score = float(health)
            self.trade_open = True
            self.is_collapsed = False
            self.last_action = "none"
            self.trust_scores = {
                r: 50 for r in
                ["aquaria", "agrovia", "petrozon", "urbanex", "terranova"]
                if r != rid
            }

    # ===================================================================
    # TEST 1 — Strength Calculation
    # ===================================================================
    print("=" * 60)
    print("  TEST 1 - Strength Calculation")
    print("=" * 60)

    r = MockRegion("urbanex", 40, 45, 80, 30, pop=950, health=60)
    s = calculate_strength(r)
    expected = (80 * 0.5) + (950 / 100 * 0.5)  # 40 + 4.75 = 44.75
    print(f"  Urbanex strength: {s:.2f} (expected {expected:.2f})")
    print(f"  Match? {PASS if abs(s - expected) < 0.01 else FAIL}")
    print()

    # ===================================================================
    # TEST 2 — Urbanex Attacks Weakened Terranova
    # ===================================================================
    print("=" * 60)
    print("  TEST 2 - Urbanex Attacks Terranova (attacker wins)")
    print("=" * 60)

    # Set up: Urbanex strong, Terranova weakened
    # Urbanex neighbors: agrovia, petrozon (from NEIGHBOR_MAP)
    # Terranova neighbors: aquaria, petrozon
    # Urbanex and Terranova are NOT neighbors in the config!
    # So let's use Petrozon attacking Terranova instead
    # Petrozon neighbors: agrovia, urbanex, terranova

    attacker = MockRegion("petrozon", 30, 35, 95, 60, pop=600, health=65)
    defender = MockRegion("terranova", 20, 25, 15, 30, pop=200, health=25)
    # Set low trust so attack is valid
    attacker.trust_scores["terranova"] = 10
    attacker.last_action = "aggress"

    all_r = [
        MockRegion("aquaria", 90, 60, 30, 70, health=70),
        MockRegion("agrovia", 50, 95, 40, 40, health=65),
        attacker,
        MockRegion("urbanex", 40, 45, 40, 30, health=45),
        defender,
    ]

    att_s = calculate_strength(attacker)
    def_s = calculate_strength(defender)
    print(f"  Petrozon strength: {att_s:.2f}")
    print(f"  Terranova strength: {def_s:.2f}")
    print(f"  Threshold (def * 1.2): {def_s * 1.2:.2f}")
    print(f"  Attacker wins? {att_s > def_s * 1.2}")

    print(f"  Before: Petrozon food={attacker.food} water={attacker.water} "
          f"energy={attacker.energy}")
    print(f"  Before: Terranova food={defender.food} water={defender.water} "
          f"energy={defender.energy}")

    outcome = resolve_conflict(attacker, defender, all_r)
    print(f"  Outcome: {outcome}")
    print(f"  After: Petrozon food={attacker.food} water={attacker.water} "
          f"energy={attacker.energy}")
    print(f"  After: Terranova food={defender.food} water={defender.water} "
          f"energy={defender.energy}")
    print(f"  Won? {PASS if outcome == 'aggress_success' else FAIL}")
    print()

    # ===================================================================
    # TEST 3 — Trust Cascade
    # ===================================================================
    print("=" * 60)
    print("  TEST 3 - Trust Cascade After Conflict")
    print("=" * 60)

    # Check trust of ALL regions toward petrozon
    for r in all_r:
        if r.region_id == "petrozon":
            continue
        trust = r.trust_scores.get("petrozon", 50)
        dropped = trust < 50
        label = PASS if dropped else FAIL
        print(f"  {r.region_id} trust toward petrozon: "
              f"{trust} (dropped? {label})")

    # Defender (terranova) should have extra penalty
    def_trust = defender.trust_scores.get("petrozon", 50)
    extra_drop = def_trust < 30  # cascade (-10) + extra (-25) = -35
    print(f"  Terranova extra penalty? {PASS if extra_drop else FAIL} "
          f"(trust={def_trust})")
    print()

    # ===================================================================
    # TEST 4 — Failed Attack (weak attacker)
    # ===================================================================
    print("=" * 60)
    print("  TEST 4 - Failed Attack (weak attacker)")
    print("=" * 60)

    weak_att = MockRegion("agrovia", 50, 95, 20, 40, pop=300, health=40)
    strong_def = MockRegion("aquaria", 90, 60, 80, 70, pop=500, health=70)
    weak_att.trust_scores["aquaria"] = 5

    all_r2 = [weak_att, strong_def,
              MockRegion("petrozon", 30, 35, 95, 60, health=65),
              MockRegion("urbanex", 40, 45, 40, 30, health=45),
              MockRegion("terranova", 55, 60, 55, 90, health=60)]

    att_s2 = calculate_strength(weak_att)
    def_s2 = calculate_strength(strong_def)
    print(f"  Agrovia strength: {att_s2:.2f}")
    print(f"  Aquaria strength: {def_s2:.2f}")
    print(f"  Before: Agrovia energy={weak_att.energy}")

    outcome2 = resolve_conflict(weak_att, strong_def, all_r2)
    print(f"  Outcome: {outcome2}")
    print(f"  After: Agrovia energy={weak_att.energy}")
    print(f"  Failed? {PASS if outcome2 == 'aggress_failed' else FAIL}")
    print(f"  Agrovia energy dropped 25? "
          f"{PASS if weak_att.energy == 0 else FAIL} "
          f"(20-25=0, clamped)")
    print()

    # ===================================================================
    # TEST 5 — run_conflict_phase
    # ===================================================================
    print("=" * 60)
    print("  TEST 5 - Full Conflict Phase")
    print("=" * 60)

    phase_regions = [
        MockRegion("aquaria", 90, 60, 30, 70, health=70),
        MockRegion("agrovia", 50, 95, 40, 40, health=65),
        MockRegion("petrozon", 30, 35, 95, 60, pop=600, health=65),
        MockRegion("urbanex", 40, 45, 40, 30, health=45),
        MockRegion("terranova", 20, 25, 15, 30, pop=200, health=25),
    ]
    # Petrozon wants to aggress, low trust toward terranova
    phase_regions[2].last_action = "aggress"
    phase_regions[2].trust_scores["terranova"] = 10

    events = run_conflict_phase(phase_regions)
    print(f"  Conflict events: {len(events)}")
    for ev in events:
        print(f"    {ev['source_region']} -> {ev['target_region']}: "
              f"{ev['outcome']}")
        print(f"    {ev['description']}")
    print(f"  Events generated? {PASS if len(events) > 0 else FAIL}")
    print()

    print("=" * 60)
    print("  All conflict tests complete")
    print("=" * 60)
