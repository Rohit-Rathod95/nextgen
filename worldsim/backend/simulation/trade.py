"""
trade.py - Inter-Region Trade System for WorldSim

All regions can trade globally (all-to-all).
Trust minimum: 25 (low threshold for global-trade realism).
Urbanex uses manufacturing_power instead of resource surplus.
Any region with a deficit participates regardless of chosen action (survival pressure).
"""

from config.regions_config import (
    NEIGHBOR_MAP, SURPLUS_THRESHOLD, DEFICIT_THRESHOLD,
    TRADE_TRUST_MINIMUM, REGIONS,
)

RESOURCES = ["water", "food", "energy", "land"]

# Trade transfer sizes
TRADE_AMOUNT   = 15    # Standard bilateral trade
URBANEX_AMOUNT = 18    # Manufacturing trade (higher value goods)

TRUST_GAIN = 5
TRUST_LOSS = 5


# ===========================================================================
# FUNCTION 1 — Find Surplus Resource
# ===========================================================================

def find_surplus_resource(region) -> str | None:
    """Return the resource in highest surplus (above SURPLUS_THRESHOLD), or None."""
    surpluses = {
        r: getattr(region, r, 0)
        for r in RESOURCES
        if getattr(region, r, 0) > SURPLUS_THRESHOLD
    }
    return max(surpluses, key=surpluses.get) if surpluses else None


# ===========================================================================
# FUNCTION 2 — Find Deficit Resource
# ===========================================================================

def find_deficit_resource(region) -> str | None:
    """Return the resource in lowest deficit (below DEFICIT_THRESHOLD), or None."""
    deficits = {
        r: getattr(region, r, 0)
        for r in RESOURCES
        if getattr(region, r, 0) < DEFICIT_THRESHOLD
    }
    return min(deficits, key=deficits.get) if deficits else None


# ===========================================================================
# FUNCTION 3 — Get Valid Partners
# ===========================================================================

def get_valid_partners(sender, all_regions: list) -> list:
    """
    Return valid trade partners sorted by trust (highest first).

    Partner criteria:
        - In NEIGHBOR_MAP for sender (now all-to-all)
        - Trust from sender >= TRADE_TRUST_MINIMUM (25)
        - Not collapsed
        - Not the sender itself
    """
    neighbors = NEIGHBOR_MAP.get(sender.region_id, [])
    valid = [
        r for r in all_regions
        if r.region_id != sender.region_id
        and r.region_id in neighbors
        and not r.is_collapsed
        and sender.trust_scores.get(r.region_id, 50) >= TRADE_TRUST_MINIMUM
    ]
    valid.sort(
        key=lambda r: sender.trust_scores.get(r.region_id, 50),
        reverse=True
    )
    return valid


# ===========================================================================
# FUNCTION 4 — Propose Trade
# ===========================================================================

def propose_trade(sender, receiver) -> str:
    """
    Propose a trade between sender and receiver.

    Standard trade: sender offers surplus, gets deficit resource.
    Urbanex manufacturing: offers manufacturing capacity, receives needed resource.

    Returns outcome string.
    """
    wanted = find_deficit_resource(sender)

    # ── Urbanex manufacturing path ──────────────────────────────────────────
    is_urbanex = sender.region_id == "urbanex"
    if is_urbanex:
        mfg = getattr(sender, "manufacturing_power", 0)
        if mfg < 10:
            return "trade_skipped_no_capacity"
        if wanted is None:
            return "trade_skipped_no_deficit"
        trust_required = max(15, TRADE_TRUST_MINIMUM - 15)   # lower bar
        transfer       = URBANEX_AMOUNT
    else:
        # ── Standard path ────────────────────────────────────────────────────
        if wanted is None:
            return "trade_skipped_no_deficit"
        offered = find_surplus_resource(sender)
        if offered is None:
            return "trade_skipped_no_surplus"
        trust_required = TRADE_TRUST_MINIMUM
        transfer       = TRADE_AMOUNT

    # ── Trust check ──────────────────────────────────────────────────────────
    receiver_trust = receiver.trust_scores.get(sender.region_id, 50)
    if receiver_trust < trust_required:
        # allow a small "first contact" trade if trust in low yet >= 15
        if receiver_trust >= 15 and not is_urbanex:
            # attempt a reduced transfer to build trust
            transfer = 8  # smaller transfer amount
            # continue execution below (skip penalty)
        else:
            # penalize sender trust for low-trust rejection
            sender.trust_scores[receiver.region_id] = max(
                0, sender.trust_scores.get(receiver.region_id, 50) - TRUST_LOSS
            )
            return "trade_rejected_low_trust"

    # ── Receiver stock check ─────────────────────────────────────────────────
    receiver_has = getattr(receiver, wanted, 0)
    if receiver_has < 30:
        return "trade_rejected_no_surplus"

    actual = min(transfer, receiver_has - 15)
    if actual <= 0:
        return "trade_rejected_no_surplus"

    # ── Execute trade ────────────────────────────────────────────────────────
    if is_urbanex:
        # Urbanex exports manufacturing value, imports needed resource
        setattr(receiver, wanted, getattr(receiver, wanted) - actual)
        setattr(sender,   wanted, getattr(sender,   wanted) + actual)
        sender.manufacturing_power = max(0.0, sender.manufacturing_power - 3.0)
    else:
        # Bilateral resource swap
        setattr(sender,   wanted,  getattr(sender,   wanted)  + actual)
        setattr(receiver, wanted,  getattr(receiver, wanted)  - actual)
        give = min(actual, getattr(sender, offered) - 10)
        if give > 0:
            setattr(sender,   offered, getattr(sender,   offered) - give)
            setattr(receiver, offered, getattr(receiver, offered) + give)

    # ── Clamp ────────────────────────────────────────────────────────────────
    for reg in [sender, receiver]:
        for res in RESOURCES:
            setattr(reg, res, max(0.0, min(100.0, getattr(reg, res))))

    # ── Trust update ─────────────────────────────────────────────────────────
    sender.trust_scores[receiver.region_id] = min(
        100, sender.trust_scores.get(receiver.region_id, 50) + TRUST_GAIN
    )
    receiver.trust_scores[sender.region_id] = min(
        100, receiver.trust_scores.get(sender.region_id, 50) + TRUST_GAIN
    )

    return "trade_success"


# ===========================================================================
# FUNCTION 5 — Run Trade Phase
# ===========================================================================

def run_trade_phase(regions_list: list, cycle: int = 0) -> list:
    """
    Run trade phase for one simulation cycle.

    Participation:
        - Region chose "trade" action, OR
        - Region has any resource below DEFICIT_THRESHOLD (survival pressure)

    Each region tries partners in trust-order until success.
    One successful trade per PAIR per cycle (traded_this_cycle set).
    Rejected attempts logged but iteration continues to next partner.
    """
    trade_events      = []
    traded_this_cycle = set()   # frozenset pairs that already traded

    for region in regions_list:
        if region.is_collapsed:
            continue

        has_deficit  = find_deficit_resource(region) is not None
        wants_to_trade = (
            getattr(region, "last_action", "none") == "trade"
            or has_deficit
        )
        if not wants_to_trade:
            continue

        partners = get_valid_partners(region, regions_list)
        if not partners:
            continue

        success = False
        for partner in partners:
            pair = frozenset([region.region_id, partner.region_id])
            if pair in traded_this_cycle:
                continue

            outcome = propose_trade(region, partner)

            if outcome == "trade_success":
                traded_this_cycle.add(pair)
                trade_events.append({
                    "type":          "trade",
                    "cycle":         cycle,
                    "source_region": region.region_id,
                    "target_region": partner.region_id,
                    "outcome":       "trade_success",
                    "description": (
                        f"{region.region_id.capitalize()} traded with "
                        f"{partner.region_id.capitalize()}"
                    ),
                })
                success = True
                break

            elif "rejected" in outcome:
                trade_events.append({
                    "type":          "trade",
                    "cycle":         cycle,
                    "source_region": region.region_id,
                    "target_region": partner.region_id,
                    "outcome":       outcome,
                    "description": (
                        f"Trade rejected: "
                        f"{region.region_id.capitalize()} -> "
                        f"{partner.region_id.capitalize()} ({outcome})"
                    ),
                })
                # Continue trying next partner

        if not success and getattr(region, "last_action", "none") == "trade":
            trade_events.append({
                "type":          "trade",
                "cycle":         cycle,
                "source_region": region.region_id,
                "target_region": "none",
                "outcome":       "trade_skipped",
                "description": (
                    f"{region.region_id.capitalize()} could not find "
                    f"a valid trade partner this cycle"
                ),
            })

    return trade_events


# ===========================================================================
# Test Cases
# ===========================================================================

if __name__ == "__main__":
    PASS = "[PASS]"
    FAIL = "[FAIL]"

    class MockRegion:
        def __init__(self, rid, water, food, energy, land, pop=500, mfg=0):
            self.region_id          = rid
            self.water              = float(water)
            self.food               = float(food)
            self.energy             = float(energy)
            self.land               = float(land)
            self.population         = float(pop)
            self.is_collapsed       = False
            self.last_action        = "trade"
            self.manufacturing_power = float(mfg)
            self.trust_scores       = {
                r: 50 for r in REGIONS if r != rid
            }

    # TEST 1 — Surplus / Deficit detection
    print("=" * 55)
    print("  TEST 1 — Surplus / Deficit")
    print("=" * 55)
    aq = MockRegion("aquaria", 80, 50, 25, 60)
    s = find_surplus_resource(aq)
    d = find_deficit_resource(aq)
    print(f"  Surplus: {s}  (want: water)  {PASS if s=='water' else FAIL}")
    print(f"  Deficit: {d}  (want: energy) {PASS if d=='energy' else FAIL}")
    print()

    # TEST 2 — All regions reachable (global trade)
    print("=" * 55)
    print("  TEST 2 — All Partners Reachable")
    print("=" * 55)
    all_r = [
        MockRegion("aquaria",   80, 50, 25, 60),
        MockRegion("agrovia",   40, 85, 35, 35),
        MockRegion("petrozon",  25, 30, 85, 50),
        MockRegion("urbanex",   35, 40, 35, 25, mfg=85),
        MockRegion("terranova", 50, 55, 50, 80),
    ]
    partners = get_valid_partners(all_r[0], all_r)
    print(f"  Aquaria partners: {[p.region_id for p in partners]}")
    print(f"  All 4 reachable? {PASS if len(partners)==4 else FAIL}")
    print()

    # TEST 3 — Full trade phase, 3+ successes
    print("=" * 55)
    print("  TEST 3 — Full Trade Phase")
    print("=" * 55)
    for r in all_r:
        r.last_action = "trade"
    events = run_trade_phase(all_r, cycle=1)
    successes = [e for e in events if e["outcome"] == "trade_success"]
    print(f"  Total events:  {len(events)}")
    print(f"  Successes:     {len(successes)}")
    for e in events:
        print(f"    {e['source_region']} -> {e['target_region']}: {e['outcome']}")
    print(f"  >= 3 successes? {PASS if len(successes) >= 3 else FAIL}")
    print()

    # TEST 4 — Urbanex manufacturing trade
    print("=" * 55)
    print("  TEST 4 — Urbanex Manufacturing Trade")
    print("=" * 55)
    ux = MockRegion("urbanex", 35, 40, 35, 25, mfg=85)
    ag = MockRegion("agrovia", 40, 85, 35, 35)
    res = propose_trade(ux, ag)
    print(f"  Outcome: {res}  {PASS if res=='trade_success' else FAIL}")
    print(f"  Mfg decreased? {PASS if ux.manufacturing_power < 85 else FAIL}")
    print()

    # TEST 5 — Low trust blocks
    print("=" * 55)
    print("  TEST 5 — Low Trust Blocks Trade")
    print("=" * 55)
    pt = MockRegion("petrozon", 25, 30, 85, 50)
    ux2 = MockRegion("urbanex", 35, 40, 35, 25)
    pt.trust_scores["urbanex"] = 10
    res2 = propose_trade(pt, ux2)
    blocked = "rejected" in res2 or "skipped" in res2
    print(f"  Outcome: {res2}  Blocked? {PASS if blocked else FAIL}")
    print()

    print("=" * 55)
    print("  All trade tests complete")
    print("=" * 55)
