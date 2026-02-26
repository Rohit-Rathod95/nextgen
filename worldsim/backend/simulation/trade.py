"""
trade.py - Inter-Region Trade System for WorldSim

All regions can trade with all other regions (global trade model).
Trust threshold lowered to 30 to allow trades from cycle 1.
Urbanex uses manufacturing_power instead of resource surplus.
Adjacent pairs transfer 15 units; distant pairs 8 units after cycle 30.
"""

from config.regions_config import (
    NEIGHBOR_MAP, RESOURCES,
    SURPLUS_THRESHOLD, DEFICIT_THRESHOLD,
    TRADE_TRUST_MINIMUM, RECEIVER_HAS_THRESHOLD,
    ADJACENT_PAIRS,
)

# ---------------------------------------------------------------------------
# Trade constants
# ---------------------------------------------------------------------------

TRADE_AMOUNT_ADJACENT = 15    # Units transferred for adjacent/close regions
TRADE_AMOUNT_DISTANT = 8      # Units transferred for distant regions after cycle 30
TRUST_GAIN_ON_SUCCESS = 5
TRUST_LOSS_ON_REJECT = 5      # Lowered from 8 to avoid trust death spirals


# ===========================================================================
# FUNCTION 1 - Find Surplus Resource
# ===========================================================================

def find_surplus_resource(region) -> str | None:
    """
    Return the resource name with the highest value above SURPLUS_THRESHOLD.
    Returns None if no resource is in surplus.
    """
    best = None
    best_val = SURPLUS_THRESHOLD

    for resource in RESOURCES:
        val = getattr(region, resource, 0)
        if val > best_val:
            best = resource
            best_val = val

    return best


# ===========================================================================
# FUNCTION 2 - Find Deficit Resource
# ===========================================================================

def find_deficit_resource(region) -> str | None:
    """
    Return the resource name with the lowest value below DEFICIT_THRESHOLD.
    Returns None if no resource is in deficit.
    """
    worst = None
    worst_val = DEFICIT_THRESHOLD

    for resource in RESOURCES:
        val = getattr(region, resource, 0)
        if val < worst_val:
            worst = resource
            worst_val = val

    return worst


# ===========================================================================
# FUNCTION 3 - Get Valid Trade Partners
# ===========================================================================

def get_valid_trade_partners(sender, all_regions: list) -> list:
    """
    Return all valid trade partners for the sender.

    A valid partner must:
      1. Be in NEIGHBOR_MAP for sender (now all-to-all)
      2. Have trust score >= TRADE_TRUST_MINIMUM (30) from sender
      3. Have trade_open == True
      4. Not be collapsed
    Partners sorted by trust score descending.
    """
    neighbors = NEIGHBOR_MAP.get(sender.region_id, [])
    valid = []

    for region in all_regions:
        if region.region_id == sender.region_id:
            continue
        if region.region_id not in neighbors:
            continue
        trust = sender.trust_scores.get(region.region_id, 0)
        if trust < TRADE_TRUST_MINIMUM:
            continue
        if not getattr(region, "trade_open", True):
            continue
        if getattr(region, "is_collapsed", False):
            continue
        valid.append(region)

    # Sort by trust so highest-trust partners are tried first
    valid.sort(
        key=lambda r: sender.trust_scores.get(r.region_id, 0),
        reverse=True
    )
    return valid


# ===========================================================================
# FUNCTION 4 - Propose Trade (rewritten)
# ===========================================================================

def propose_trade(sender, receiver, cycle: int = 0) -> str:
    """
    Propose a trade between sender and receiver.

    Standard trade: sender offers their surplus, gets their deficit.
    Urbanex manufacturing trade: offers manufacturing capacity, gets resources.

    Transfer amounts:
      - Adjacent pair:         TRADE_AMOUNT_ADJACENT (15 units)
      - Distant pair cycle<30: TRADE_AMOUNT_ADJACENT (15 units)
      - Distant pair cycle>=30: TRADE_AMOUNT_DISTANT (8 units — distance penalty)

    Args:
        sender:   Region proposing the trade.
        receiver: Region receiving the proposal.
        cycle:    Current simulation cycle (for distance penalty).

    Returns:
        Outcome string.
    """
    wanted = find_deficit_resource(sender)

    # ── Urbanex manufacturing path ─────────────────────────────────────────
    manufacturing_trade = False
    if sender.region_id == "urbanex":
        mfg_power = getattr(sender, "manufacturing_power", 0)
        if mfg_power > 20:
            # China leverages manufacturing capacity to acquire needed resources
            # Lower trust requirement, higher transfer (more attractive partner)
            trust_required = max(20, TRADE_TRUST_MINIMUM - 10)
            transfer_amount = 20
            manufacturing_trade = True
            # If no deficit, still skip
            if wanted is None:
                return "trade_skipped_no_deficit"
        else:
            return "trade_skipped_no_capacity"
    else:
        # ── Standard path ──────────────────────────────────────────────────
        if wanted is None:
            return "trade_skipped_no_deficit"

        offered = find_surplus_resource(sender)
        if offered is None:
            return "trade_skipped_no_surplus"

        trust_required = TRADE_TRUST_MINIMUM

        # Distance-adjusted transfer amount
        pair = frozenset([sender.region_id, receiver.region_id])
        if pair in ADJACENT_PAIRS or cycle < 30:
            transfer_amount = TRADE_AMOUNT_ADJACENT
        else:
            transfer_amount = TRADE_AMOUNT_DISTANT  # long-distance penalty after cycle 30

    # ── Trust check ────────────────────────────────────────────────────────
    receiver_trust = receiver.trust_scores.get(sender.region_id, 50)
    if receiver_trust < trust_required:
        sender.trust_scores[receiver.region_id] = max(
            0, sender.trust_scores.get(receiver.region_id, 50) - TRUST_LOSS_ON_REJECT
        )
        return "trade_rejected_low_trust"

    # ── Receiver stock check ───────────────────────────────────────────────
    receiver_resource_value = getattr(receiver, wanted, 0)
    if receiver_resource_value < RECEIVER_HAS_THRESHOLD:
        return "trade_rejected_no_surplus"

    # ── Execute trade ──────────────────────────────────────────────────────
    if manufacturing_trade:
        # Urbanex gives manufacturing capacity, receives the resource it needs
        setattr(receiver, wanted,
                getattr(receiver, wanted) - transfer_amount)
        setattr(sender, wanted,
                getattr(sender, wanted) + transfer_amount)
        sender.manufacturing_power = max(
            0, sender.manufacturing_power - 2
        )
    else:
        # Normal bilateral resource swap
        setattr(sender,   wanted,  getattr(sender,   wanted)  + transfer_amount)
        setattr(receiver, wanted,  getattr(receiver, wanted)  - transfer_amount)
        setattr(sender,   offered, getattr(sender,   offered) - transfer_amount)
        setattr(receiver, offered, getattr(receiver, offered) + transfer_amount)

    # ── Clamp all values to [0, 100] ──────────────────────────────────────
    for region in [sender, receiver]:
        for res in RESOURCES:
            setattr(region, res,
                    max(0.0, min(100.0, getattr(region, res))))

    # ── Update mutual trust ────────────────────────────────────────────────
    sender.trust_scores[receiver.region_id] = min(
        100, sender.trust_scores.get(receiver.region_id, 50) + TRUST_GAIN_ON_SUCCESS
    )
    receiver.trust_scores[sender.region_id] = min(
        100, receiver.trust_scores.get(sender.region_id, 50) + TRUST_GAIN_ON_SUCCESS
    )

    return "trade_success"


# ===========================================================================
# FUNCTION 5 - Run Trade Phase (rewritten)
# ===========================================================================

def run_trade_phase(regions_list: list, cycle: int = 0) -> list:
    """
    Run the trade phase for one simulation cycle.

    A region participates if:
      - Its last_action is "trade", OR
      - It has any resource below DEFICIT_THRESHOLD (survival pressure)

    Each region tries partners in descending trust order.
    One successful trade per region per cycle (break after first success).
    Rejected attempts are still logged.

    Args:
        regions_list: All Region objects.
        cycle:        Current cycle number (for distance penalty).

    Returns:
        List of trade event dicts.
    """
    trade_events = []

    for region in regions_list:
        if region.is_collapsed:
            continue

        # Participate if chose trade OR has a resource deficit (survival pressure)
        has_deficit = any(
            getattr(region, res, 100) < DEFICIT_THRESHOLD
            for res in RESOURCES
        )
        should_trade = (
            getattr(region, "last_action", "none") == "trade"
            or has_deficit
        )
        if not should_trade:
            continue

        # Need something specific to trade for
        wanted = find_deficit_resource(region)
        if wanted is None and region.region_id != "urbanex":
            continue

        partners = get_valid_trade_partners(region, regions_list)
        if not partners:
            continue

        traded = False
        for partner in partners:
            outcome = propose_trade(region, partner, cycle)

            if outcome == "trade_success":
                wanted_res = find_deficit_resource(region) or "resources"
                trade_events.append({
                    "type": "trade",
                    "source_region": region.region_id,
                    "target_region": partner.region_id,
                    "outcome": "trade_success",
                    "description": (
                        f"{region.region_id.capitalize()} traded with "
                        f"{partner.region_id.capitalize()} "
                        f"({'manufacturing' if region.region_id == 'urbanex' else wanted_res})"
                    ),
                })
                traded = True
                break  # One successful trade per region per cycle

            elif "rejected" in outcome:
                trade_events.append({
                    "type": "trade",
                    "source_region": region.region_id,
                    "target_region": partner.region_id,
                    "outcome": outcome,
                    "description": (
                        f"Trade rejected: {region.region_id.capitalize()} "
                        f"-> {partner.region_id.capitalize()} ({outcome})"
                    ),
                })
                # Keep trying next partner on rejection

        # If region action was "trade" but couldn't find a partner, log skip
        if not traded and getattr(region, "last_action", "none") == "trade":
            trade_events.append({
                "type": "trade",
                "source_region": region.region_id,
                "target_region": "none",
                "outcome": "trade_skipped",
                "description": f"{region.region_id.capitalize()} could not find a valid trade partner",
            })

    return trade_events


# ===========================================================================
# Test Cases
# ===========================================================================

if __name__ == "__main__":

    PASS = "[PASS]"
    FAIL = "[FAIL]"

    # Mock Region class for testing (includes manufacturing_power)
    class MockRegion:
        def __init__(self, region_id, water, food, energy, land,
                     population=500, mfg=0):
            self.region_id = region_id
            self.water = float(water)
            self.food = float(food)
            self.energy = float(energy)
            self.land = float(land)
            self.population = float(population)
            self.trade_open = True
            self.is_collapsed = False
            self.last_action = "trade"
            self.manufacturing_power = float(mfg)
            self.trust_scores = {
                r: 50 for r in
                ["aquaria", "agrovia", "petrozon", "urbanex", "terranova"]
                if r != region_id
            }

    # ===================================================================
    # TEST 1 — Surplus and Deficit Detection
    # ===================================================================
    print("=" * 60)
    print("  TEST 1 - Surplus and Deficit Detection")
    print("=" * 60)

    aq = MockRegion("aquaria", water=80, food=50, energy=25, land=60)
    surplus = find_surplus_resource(aq)
    deficit = find_deficit_resource(aq)
    print(f"  Aquaria surplus: {surplus} (expected: water)")
    print(f"  Aquaria deficit: {deficit} (expected: energy)")
    print(f"  Surplus correct? {PASS if surplus == 'water' else FAIL}")
    print(f"  Deficit correct? {PASS if deficit == 'energy' else FAIL}")
    print()

    # ===================================================================
    # TEST 2 — All regions are now valid partners
    # ===================================================================
    print("=" * 60)
    print("  TEST 2 - All Regions Are Valid Partners (global trade)")
    print("=" * 60)

    all_regions = [
        MockRegion("aquaria",   80, 50, 25, 60),
        MockRegion("agrovia",   40, 85, 35, 35),
        MockRegion("petrozon",  25, 30, 85, 50),
        MockRegion("urbanex",   35, 40, 35, 25, mfg=85),
        MockRegion("terranova", 50, 55, 50, 80),
    ]

    partners = get_valid_trade_partners(all_regions[0], all_regions)
    partner_ids = [p.region_id for p in partners]
    print(f"  Aquaria valid partners: {partner_ids}")
    # All 4 other regions should be valid (global trade, trust=50 > 30)
    all_valid = len(partner_ids) == 4
    print(f"  All 4 others reachable? {PASS if all_valid else FAIL}")
    print()

    # ===================================================================
    # TEST 3 — Successful Trade: Aquaria <-> Petrozon
    # ===================================================================
    print("=" * 60)
    print("  TEST 3 - Successful Trade: Aquaria gets energy from Petrozon")
    print("=" * 60)

    aq = MockRegion("aquaria",  water=80, food=50, energy=25, land=60)
    pt = MockRegion("petrozon", water=25, food=30, energy=85, land=50)

    print(f"  Before: Aquaria E={aq.energy:.0f}  Petrozon E={pt.energy:.0f}")
    outcome = propose_trade(aq, pt, cycle=0)
    print(f"  Outcome: {outcome}")
    print(f"  After:  Aquaria E={aq.energy:.0f}  Petrozon E={pt.energy:.0f}")
    print(f"  Success? {PASS if outcome == 'trade_success' else FAIL}")
    print(f"  Aquaria energy increased? {PASS if aq.energy > 25 else FAIL}")
    print()

    # ===================================================================
    # TEST 4 — Urbanex Manufacturing Trade
    # ===================================================================
    print("=" * 60)
    print("  TEST 4 - Urbanex Manufacturing Trade")
    print("=" * 60)

    ux = MockRegion("urbanex",  water=35, food=40, energy=35, land=25, mfg=85)
    ag = MockRegion("agrovia",  water=40, food=85, energy=35, land=35)

    print(f"  Before: Urbanex E={ux.energy:.0f} mfg={ux.manufacturing_power:.0f}  Agrovia F={ag.food:.0f}")
    outcome4 = propose_trade(ux, ag, cycle=0)
    print(f"  Outcome: {outcome4}")
    print(f"  After:  Urbanex E={ux.energy:.0f} mfg={ux.manufacturing_power:.0f}  Agrovia F={ag.food:.0f}")
    print(f"  Success? {PASS if outcome4 == 'trade_success' else FAIL}")
    print(f"  Urbanex mfg_power decreased? {PASS if ux.manufacturing_power < 85 else FAIL}")
    print()

    # ===================================================================
    # TEST 5 — Full Trade Phase fires 3+ trades
    # ===================================================================
    print("=" * 60)
    print("  TEST 5 - Full Trade Phase (expect 3+ successful trades)")
    print("=" * 60)

    all_r = [
        MockRegion("aquaria",   80, 50, 25, 60),
        MockRegion("agrovia",   40, 85, 35, 35),
        MockRegion("petrozon",  25, 30, 85, 50),
        MockRegion("urbanex",   35, 40, 35, 25, mfg=85),
        MockRegion("terranova", 50, 55, 50, 80),
    ]

    events = run_trade_phase(all_r, cycle=1)
    successes = [e for e in events if e["outcome"] == "trade_success"]
    print(f"  Total events: {len(events)}")
    print(f"  Successful trades: {len(successes)}")
    for ev in events:
        print(f"    {ev['source_region']} -> {ev['target_region']}: {ev['outcome']}")
    print(f"  >= 3 successful trades? {PASS if len(successes) >= 3 else FAIL}")
    print()

    # ===================================================================
    # TEST 6 — Low trust blocks trade
    # ===================================================================
    print("=" * 60)
    print("  TEST 6 - Low Trust Blocks Trade (trust < 30)")
    print("=" * 60)

    sender = MockRegion("petrozon", 25, 30, 85, 50)
    receiver = MockRegion("urbanex", 35, 40, 35, 25)
    sender.trust_scores["urbanex"] = 15   # below minimum

    outcome6 = propose_trade(sender, receiver, cycle=0)
    print(f"  Trust: {sender.trust_scores['urbanex']}")
    print(f"  Outcome: {outcome6}")
    print(f"  Blocked? {PASS if 'rejected' in outcome6 or 'skipped' in outcome6 else FAIL}")
    print()

    # ===================================================================
    print("=" * 60)
    print("  All trade tests complete")
    print("=" * 60)
