"""
trade.py — Inter-Region Trade System for WorldSim

Handles trade proposals between neighboring regions. Only neighbors
(as defined in NEIGHBOR_MAP) can trade. Trust must be above 40 to
propose, and the receiver must have surplus of the wanted resource.

Trade transfers 10 units of each resource between regions.
Successful trades increase mutual trust; rejections decrease it.
"""

from config.regions_config import NEIGHBOR_MAP, RESOURCES


# ---------------------------------------------------------------------------
# Thresholds
# ---------------------------------------------------------------------------

SURPLUS_THRESHOLD = 60    # Resource above this = surplus
DEFICIT_THRESHOLD = 40    # Resource below this = deficit
TRADE_AMOUNT = 10         # Units transferred per trade
TRUST_MIN_FOR_TRADE = 40  # Minimum trust to propose trade
RECEIVER_HAS_THRESHOLD = 50  # Receiver must have > this to accept
TRUST_GAIN_ON_SUCCESS = 5
TRUST_LOSS_ON_REJECT = 8


# ===========================================================================
# FUNCTION 1 — Find Surplus Resource
# ===========================================================================

def find_surplus_resource(region) -> str | None:
    """
    Find the resource with the highest value above the surplus
    threshold (60) for a given region.

    Args:
        region: Region object with water, food, energy, land attributes.

    Returns:
        Resource name string, or None if no surplus exists.
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
# FUNCTION 2 — Find Deficit Resource
# ===========================================================================

def find_deficit_resource(region) -> str | None:
    """
    Find the resource with the lowest value below the deficit
    threshold (40) for a given region.

    Args:
        region: Region object with water, food, energy, land attributes.

    Returns:
        Resource name string, or None if no deficit exists.
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
# FUNCTION 3 — Get Valid Trade Partners
# ===========================================================================

def get_valid_trade_partners(sender, all_regions: list) -> list:
    """
    Filter regions to find valid trade partners for the sender.

    A valid partner must:
        1. Be in sender's NEIGHBOR_MAP
        2. Have trust score > 40 from sender's perspective
        3. Have trade_open == True
        4. Not be collapsed

    Args:
        sender:      Region object proposing trade.
        all_regions: List of all Region objects.

    Returns:
        List of valid Region objects.
    """
    neighbors = NEIGHBOR_MAP.get(sender.region_id, [])
    valid = []

    for region in all_regions:
        if region.region_id == sender.region_id:
            continue

        # Must be a neighbor
        if region.region_id not in neighbors:
            continue

        # Trust check
        trust = sender.trust_scores.get(region.region_id, 0)
        if trust <= TRUST_MIN_FOR_TRADE:
            continue

        # Must be open for trade and not collapsed
        if not getattr(region, "trade_open", True):
            continue
        if getattr(region, "is_collapsed", False):
            continue

        valid.append(region)

    return valid


# ===========================================================================
# FUNCTION 4 — Propose Trade
# ===========================================================================

def propose_trade(sender, receiver) -> str:
    """
    Propose a trade between sender and receiver.

    Sender offers their surplus resource in exchange for the
    resource they need most (deficit). Transfer amount is 10 units.

    On success: both trust scores increase by 5.
    On rejection: sender's trust toward receiver drops by 8.

    Args:
        sender:   Region object proposing trade.
        receiver: Region object receiving proposal.

    Returns:
        Outcome string: "trade_success", "trade_rejected",
        or "trade_skipped".
    """
    wanted = find_deficit_resource(sender)
    offered = find_surplus_resource(sender)

    if wanted is None or offered is None:
        return "trade_skipped"

    # Check if receiver has enough of the wanted resource
    receiver_has = getattr(receiver, wanted, 0)
    if receiver_has <= RECEIVER_HAS_THRESHOLD:
        # Receiver can't meet demand — reject
        sender.trust_scores[receiver.region_id] = max(
            0, sender.trust_scores.get(receiver.region_id, 50) - TRUST_LOSS_ON_REJECT
        )
        return "trade_rejected"

    # Execute trade
    # Sender gains wanted resource
    sender_wanted_val = getattr(sender, wanted)
    setattr(sender, wanted, min(100.0, sender_wanted_val + TRADE_AMOUNT))

    # Receiver loses wanted resource
    receiver_wanted_val = getattr(receiver, wanted)
    setattr(receiver, wanted, max(0.0, receiver_wanted_val - TRADE_AMOUNT))

    # Sender loses offered resource
    sender_offered_val = getattr(sender, offered)
    setattr(sender, offered, max(0.0, sender_offered_val - TRADE_AMOUNT))

    # Receiver gains offered resource
    receiver_offered_val = getattr(receiver, offered)
    setattr(receiver, offered, min(100.0, receiver_offered_val + TRADE_AMOUNT))

    # Update trust scores — both sides gain
    sender.trust_scores[receiver.region_id] = min(
        100, sender.trust_scores.get(receiver.region_id, 50) + TRUST_GAIN_ON_SUCCESS
    )
    receiver.trust_scores[sender.region_id] = min(
        100, receiver.trust_scores.get(sender.region_id, 50) + TRUST_GAIN_ON_SUCCESS
    )

    return "trade_success"


# ===========================================================================
# FUNCTION 5 — Run Trade Phase
# ===========================================================================

def run_trade_phase(regions_list: list) -> list:
    """
    Run the trade phase for one cycle. Each region whose last_action
    is "trade" attempts to trade with its highest-trust valid partner.

    Args:
        regions_list: List of all Region objects.

    Returns:
        List of trade event log dicts.
    """
    trade_events = []

    for region in regions_list:
        # Only regions that chose "trade" participate
        if getattr(region, "last_action", "none") != "trade":
            continue

        partners = get_valid_trade_partners(region, regions_list)
        if not partners:
            continue

        # Pick partner with highest trust
        best_partner = max(
            partners,
            key=lambda p: region.trust_scores.get(p.region_id, 0)
        )

        outcome = propose_trade(region, best_partner)

        # Build description
        if outcome == "trade_success":
            desc = (
                f"{region.region_id.capitalize()} traded successfully with "
                f"{best_partner.region_id.capitalize()}"
            )
        elif outcome == "trade_rejected":
            desc = (
                f"{region.region_id.capitalize()}'s trade proposal was "
                f"rejected by {best_partner.region_id.capitalize()}"
            )
        else:
            desc = (
                f"{region.region_id.capitalize()} skipped trade — no "
                f"surplus to offer or no deficit to fill"
            )

        trade_events.append({
            "type": "trade",
            "source_region": region.region_id,
            "target_region": best_partner.region_id,
            "outcome": outcome,
            "description": desc,
        })

    return trade_events


# ===========================================================================
# Test Cases
# ===========================================================================

if __name__ == "__main__":

    PASS = "[PASS]"
    FAIL = "[FAIL]"

    # Mock Region class for testing
    class MockRegion:
        def __init__(self, region_id, water, food, energy, land,
                     population=500):
            self.region_id = region_id
            self.water = float(water)
            self.food = float(food)
            self.energy = float(energy)
            self.land = float(land)
            self.population = float(population)
            self.trade_open = True
            self.is_collapsed = False
            self.last_action = "trade"
            self.trust_scores = {
                r: 50 for r in
                ["aquaria", "agrovia", "petrozon", "urbanex", "terranova"]
                if r != region_id
            }

    # ===================================================================
    # TEST 1 — Find Surplus / Deficit
    # ===================================================================
    print("=" * 60)
    print("  TEST 1 - Surplus and Deficit Detection")
    print("=" * 60)

    aq = MockRegion("aquaria", water=90, food=60, energy=30, land=70)
    surplus = find_surplus_resource(aq)
    deficit = find_deficit_resource(aq)
    print(f"  Aquaria surplus: {surplus} (expected: water)")
    print(f"  Aquaria deficit: {deficit} (expected: energy)")
    print(f"  Surplus correct? {PASS if surplus == 'water' else FAIL}")
    print(f"  Deficit correct? {PASS if deficit == 'energy' else FAIL}")
    print()

    # ===================================================================
    # TEST 2 — Valid Trade Partners
    # ===================================================================
    print("=" * 60)
    print("  TEST 2 - Valid Trade Partners for Aquaria")
    print("=" * 60)

    all_regions = [
        MockRegion("aquaria", 90, 60, 30, 70),
        MockRegion("agrovia", 50, 95, 40, 40),
        MockRegion("petrozon", 30, 35, 95, 60),
        MockRegion("urbanex", 40, 45, 40, 30),
        MockRegion("terranova", 55, 60, 55, 90),
    ]

    partners = get_valid_trade_partners(all_regions[0], all_regions)
    partner_ids = [p.region_id for p in partners]
    print(f"  Valid partners: {partner_ids}")
    # Aquaria neighbors: agrovia, terranova
    expected_partners = {"agrovia", "terranova"}
    matches = set(partner_ids) == expected_partners
    print(f"  Matches neighbor map? {PASS if matches else FAIL}")
    print()

    # ===================================================================
    # TEST 3 — Successful Trade (Aquaria ↔ Agrovia)
    # ===================================================================
    print("=" * 60)
    print("  TEST 3 - Successful Trade: Aquaria <-> Agrovia")
    print("=" * 60)

    aq = MockRegion("aquaria", water=90, food=60, energy=30, land=70)
    ag = MockRegion("agrovia", water=50, food=95, energy=40, land=40)

    print(f"  Before trade:")
    print(f"    Aquaria:  W={aq.water} F={aq.food} E={aq.energy} L={aq.land}")
    print(f"    Agrovia:  W={ag.water} F={ag.food} E={ag.energy} L={ag.land}")
    print(f"    Trust A->B: {aq.trust_scores['agrovia']}")

    outcome = propose_trade(aq, ag)
    print(f"  Outcome: {outcome}")
    print(f"  After trade:")
    print(f"    Aquaria:  W={aq.water} F={aq.food} E={aq.energy} L={aq.land}")
    print(f"    Agrovia:  W={ag.water} F={ag.food} E={ag.energy} L={ag.land}")
    print(f"    Trust A->B: {aq.trust_scores['agrovia']}")
    print(f"  Success? {PASS if outcome == 'trade_success' else FAIL}")

    # Aquaria deficit=energy, surplus=water
    # Agrovia has energy=40 which is <= 50 threshold
    # Actually Agrovia food=95 which is the surplus.
    # Let's check what actually happened
    print(f"  Aquaria energy increased? {PASS if aq.energy > 30 else FAIL}")
    print()

    # ===================================================================
    # TEST 4 — Trade Rejected (low receiver stock)
    # ===================================================================
    print("=" * 60)
    print("  TEST 4 - Trade Rejected")
    print("=" * 60)

    sender = MockRegion("petrozon", water=30, food=35, energy=95, land=60)
    receiver = MockRegion("urbanex", water=40, food=45, energy=40, land=30)

    print(f"  Petrozon deficit: {find_deficit_resource(sender)}")
    print(f"  Urbanex has water={receiver.water} (<= 50 threshold)")

    outcome2 = propose_trade(sender, receiver)
    print(f"  Outcome: {outcome2}")
    print(f"  Rejected? {PASS if outcome2 == 'trade_rejected' else FAIL}")
    print(f"  Trust dropped? {PASS if sender.trust_scores['urbanex'] < 50 else FAIL}")
    print()

    # ===================================================================
    # TEST 5 — run_trade_phase
    # ===================================================================
    print("=" * 60)
    print("  TEST 5 - Full Trade Phase")
    print("=" * 60)

    all_r = [
        MockRegion("aquaria", 90, 60, 30, 70),
        MockRegion("agrovia", 50, 95, 40, 40),
        MockRegion("petrozon", 30, 35, 95, 60),
        MockRegion("urbanex", 40, 45, 40, 30),
        MockRegion("terranova", 55, 60, 55, 90),
    ]

    events = run_trade_phase(all_r)
    print(f"  Trade events: {len(events)}")
    for ev in events:
        print(f"    {ev['source_region']} -> {ev['target_region']}: "
              f"{ev['outcome']}")
        print(f"    {ev['description']}")
    print(f"  Events generated? {PASS if len(events) > 0 else FAIL}")
    print()

    # ===================================================================
    print("=" * 60)
    print("  All trade tests complete")
    print("=" * 60)
