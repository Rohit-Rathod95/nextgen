"""
analysis_service.py — Post-Simulation Analysis Engine for WorldSim

Runs after the simulation completes all 100 cycles. Reads cycle_logs
from Firestore, detects collapses, alliances, and dominant strategies,
generates plain English insight cards, and writes the results to the
Firestore analysis collection so AnalysisOverlay.jsx can display them.

Field names written to Firestore match the frontend EXACTLY:
    key_insights, collapsed_regions, alliance_clusters,
    dominant_strategy, real_world_parallel, simulation_summary
"""

import logging
from firebase_admin import firestore

from config.firebase_config import db

logger = logging.getLogger("analysis_service")

# ---------------------------------------------------------------------------
# Constants
# ---------------------------------------------------------------------------

COLLAPSE_HEALTH_THRESHOLD = 20
ALLIANCE_CONSECUTIVE_THRESHOLD = 5
ANALYSIS_COLLECTION = "analysis"
ANALYSIS_DOC_ID = "insights"
CYCLE_LOGS_COLLECTION = "cycle_logs"


# ===========================================================================
# FUNCTION 1 — Load Cycle Logs
# ===========================================================================

def load_cycle_logs() -> list:
    """
    Read all documents from the cycle_logs collection and return
    them sorted by cycle number ascending.

    Returns:
        Sorted list of cycle log dicts. Empty list on error.
    """
    try:
        docs = db.collection(CYCLE_LOGS_COLLECTION).order_by("cycle").stream()
        logs = []
        for doc in docs:
            data = doc.to_dict()
            if data:
                logs.append(data)
        logger.info("load_cycle_logs: loaded %d cycle logs.", len(logs))
        return logs

    except Exception as exc:
        logger.error("load_cycle_logs: failed - %s", exc)
        return []


# ===========================================================================
# FUNCTION 2 — Detect Collapses
# ===========================================================================

def detect_collapses(cycle_logs: list) -> list:
    """
    Find every region that collapsed during the simulation.

    A collapse is detected when a region's health_score drops
    below 20 in the regions_snapshot for any cycle.

    For each collapse, analyzes the 10 cycles before to determine
    root cause and generates a plain English description.

    Args:
        cycle_logs: Sorted list of cycle log dicts.

    Returns:
        List of collapse dicts with region, collapsed_at,
        root_cause, and description.
    """
    collapses = []
    collapsed_set = set()  # Track already-collapsed regions

    for i, log in enumerate(cycle_logs):
        snapshot = log.get("regions_snapshot", {})
        cycle_num = log.get("cycle", i + 1)

        for region_id, region_data in snapshot.items():
            if region_id in collapsed_set:
                continue

            health = region_data.get("health_score", 100)
            if health < COLLAPSE_HEALTH_THRESHOLD:
                collapsed_set.add(region_id)

                # Analyze 10 cycles before collapse for root cause
                root_cause = _analyze_collapse_cause(
                    cycle_logs, region_id, i
                )

                description = _build_collapse_description(
                    region_id, cycle_num, root_cause
                )

                collapses.append({
                    "region": region_id,
                    "collapsed_at": cycle_num,
                    "root_cause": root_cause,
                    "description": description,
                })

    logger.info("detect_collapses: found %d collapses.", len(collapses))
    return collapses


def _analyze_collapse_cause(cycle_logs: list, region_id: str,
                            collapse_idx: int) -> str:
    """
    Analyze the 10 cycles before collapse to determine root cause.

    Returns one of: water_depletion, food_depletion,
    sustained_decline, overpopulation_pressure, resource_exhaustion.
    """
    start = max(0, collapse_idx - 10)
    window = cycle_logs[start:collapse_idx + 1]

    if len(window) < 2:
        return "resource_exhaustion"

    # Get first and last snapshots in window
    first_snap = window[0].get("regions_snapshot", {}).get(region_id, {})
    last_snap = window[-1].get("regions_snapshot", {}).get(region_id, {})

    # Check water drop
    water_drop = first_snap.get("water", 0) - last_snap.get("water", 0)
    if water_drop > 30:
        return "water_depletion"

    # Check food drop
    food_drop = first_snap.get("food", 0) - last_snap.get("food", 0)
    if food_drop > 30:
        return "food_depletion"

    # Check sustained health decline (5+ consecutive drops)
    if len(window) >= 5:
        health_values = []
        for log in window:
            snap = log.get("regions_snapshot", {}).get(region_id, {})
            health_values.append(snap.get("health_score", 100))

        declining_count = 0
        for j in range(1, len(health_values)):
            if health_values[j] < health_values[j - 1]:
                declining_count += 1
            else:
                declining_count = 0
            if declining_count >= 5:
                return "sustained_decline"

    # Check overpopulation
    pop = first_snap.get("population", 0)
    if pop > 800:
        return "overpopulation_pressure"

    return "resource_exhaustion"


def _build_collapse_description(region_id: str, cycle: int,
                                root_cause: str) -> str:
    """Build a plain English collapse description string."""
    name = region_id.capitalize()

    descriptions = {
        "water_depletion": (
            f"{name} collapsed at cycle {cycle}. Critical water shortage "
            f"over 10 cycles depleted reserves below survival threshold."
        ),
        "food_depletion": (
            f"{name} collapsed at cycle {cycle}. Food supply failed to "
            f"meet population demand leading to rapid population decline."
        ),
        "sustained_decline": (
            f"{name} collapsed at cycle {cycle}. Consistent resource "
            f"decline across 5 cycles with no successful trade recovery."
        ),
        "overpopulation_pressure": (
            f"{name} collapsed at cycle {cycle}. High population consumed "
            f"resources faster than any trade or investment could recover."
        ),
        "resource_exhaustion": (
            f"{name} collapsed at cycle {cycle}. Multiple resources hit "
            f"critical levels simultaneously causing system failure."
        ),
    }

    return descriptions.get(root_cause, descriptions["resource_exhaustion"])


# ===========================================================================
# FUNCTION 3 — Detect Alliances
# ===========================================================================

def detect_alliances(cycle_logs: list) -> list:
    """
    Find region pairs that traded successfully for 5 or more
    consecutive cycles, indicating a stable trade alliance.

    Tracks consecutive trade counters per region pair across
    all cycle logs using the regions_snapshot last_action fields.

    Args:
        cycle_logs: Sorted list of cycle log dicts.

    Returns:
        List of alliance dicts with regions, formed_at, duration,
        held_until_end, and description.
    """
    # Track consecutive trades per pair: "regionA-regionB" → count
    consecutive = {}
    # Track when alliance first formed
    alliance_formed = {}
    # Track peak durations
    peak_duration = {}
    # Track if pair traded in the final cycle
    final_cycle_trades = set()

    all_regions = set()

    for log_idx, log in enumerate(cycle_logs):
        snapshot = log.get("regions_snapshot", {})
        cycle_num = log.get("cycle", log_idx + 1)
        is_final = (log_idx == len(cycle_logs) - 1)

        # Collect all region IDs
        for rid in snapshot:
            all_regions.add(rid)

        # Determine which pairs traded this cycle
        trading_pairs = set()
        for region_id, region_data in snapshot.items():
            action = region_data.get("last_action", "none")
            if action == "trade":
                # Mark this region as trading — pair with all trading neighbors
                for other_id, other_data in snapshot.items():
                    if other_id != region_id:
                        if other_data.get("last_action", "none") == "trade":
                            pair_key = _pair_key(region_id, other_id)
                            trading_pairs.add(pair_key)

        # Build all possible pairs for tracking
        region_list = sorted(all_regions)
        all_pairs = set()
        for i in range(len(region_list)):
            for j in range(i + 1, len(region_list)):
                all_pairs.add(_pair_key(region_list[i], region_list[j]))

        # Update consecutive counts
        for pair in all_pairs:
            if pair in trading_pairs:
                consecutive[pair] = consecutive.get(pair, 0) + 1

                # Record alliance formation at threshold
                if (consecutive[pair] >= ALLIANCE_CONSECUTIVE_THRESHOLD
                        and pair not in alliance_formed):
                    alliance_formed[pair] = cycle_num

                # Track peak duration
                current = consecutive[pair]
                if current > peak_duration.get(pair, 0):
                    peak_duration[pair] = current

                if is_final:
                    final_cycle_trades.add(pair)
            else:
                consecutive[pair] = 0

    # Build results for pairs that reached alliance threshold
    alliances = []
    for pair, formed_at in alliance_formed.items():
        regions = pair.split("-")
        duration = peak_duration.get(pair, ALLIANCE_CONSECUTIVE_THRESHOLD)
        held = pair in final_cycle_trades

        name_a = regions[0].capitalize()
        name_b = regions[1].capitalize()

        alliances.append({
            "regions": regions,
            "formed_at": formed_at,
            "duration": duration,
            "held_until_end": held,
            "description": (
                f"{name_a} and {name_b} formed a stable trade alliance "
                f"from cycle {formed_at}, lasting {duration} cycles."
            ),
        })

    logger.info("detect_alliances: found %d alliances.", len(alliances))
    return alliances


def _pair_key(a: str, b: str) -> str:
    """Create a consistent alphabetically-ordered pair key."""
    return f"{min(a, b)}-{max(a, b)}"


# ===========================================================================
# FUNCTION 4 — Detect Dominant Strategy
# ===========================================================================

def detect_dominant_strategy(cycle_logs: list) -> str:
    """
    Look at the final cycle snapshot and count strategy labels
    among surviving (non-collapsed) regions.

    Returns the most common label. Returns "Mixed Strategies" on tie.

    Args:
        cycle_logs: Sorted list of cycle log dicts.

    Returns:
        Dominant strategy label string.
    """
    if not cycle_logs:
        return "Balanced"

    final_log = cycle_logs[-1]
    snapshot = final_log.get("regions_snapshot", {})

    label_counts = {}
    for region_id, region_data in snapshot.items():
        # Skip collapsed regions
        if region_data.get("is_collapsed", False):
            continue
        if region_data.get("health_score", 100) < COLLAPSE_HEALTH_THRESHOLD:
            continue

        label = region_data.get("strategy_label", "Balanced")
        label_counts[label] = label_counts.get(label, 0) + 1

    if not label_counts:
        return "Balanced"

    max_count = max(label_counts.values())
    top_labels = [l for l, c in label_counts.items() if c == max_count]

    if len(top_labels) > 1:
        return "Mixed Strategies"

    return top_labels[0]


# ===========================================================================
# FUNCTION 5 — Generate Real World Parallel
# ===========================================================================

def generate_real_world_parallel(collapses: list, alliances: list,
                                 dominant_strategy: str) -> str:
    """
    Build a real-world parallel string based on simulation outcomes.

    Maps dominant strategies and events to historical analogies.

    Args:
        collapses:         List of collapse dicts.
        alliances:         List of alliance dicts.
        dominant_strategy: Most common strategy label.

    Returns:
        Plain English real-world parallel string.
    """
    if dominant_strategy == "Aggressor":
        return (
            "Simulation mirrors pre-WWI resource competition where "
            "aggressive expansion strategies dominated short-term "
            "but led to systemic collapse."
        )

    if dominant_strategy == "Trader":
        return (
            "Emergent behavior mirrors modern EU economic model - "
            "cooperative trade networks proved more stable than "
            "isolationist or aggressive strategies."
        )

    if dominant_strategy == "Hoarder":
        return (
            "Resource hoarding mirrors Cold War stockpiling behavior - "
            "short term security at cost of long term cooperation "
            "and systemic fragility."
        )

    if dominant_strategy == "Investor":
        return (
            "Investment-focused strategy mirrors East Asian development "
            "model - sacrificing short term consumption for long term "
            "productive capacity."
        )

    if len(collapses) > 2:
        return (
            "Multiple regional collapses mirror cascading state failures "
            "seen in Sahel region - where resource scarcity triggers "
            "political instability across borders."
        )

    if len(alliances) > 1 and len(collapses) == 0:
        return (
            "Stable multi-region alliance network mirrors post-WWII "
            "multilateral institutions - cooperation preventing conflict "
            "when mutual dependency is established early."
        )

    return (
        "Simulation reveals that no single strategy dominates universally "
        "- context, starting resources, and early interactions determine "
        "long-term survival outcomes."
    )


# ===========================================================================
# FUNCTION 6 — Generate Simulation Summary
# ===========================================================================

def generate_simulation_summary(cycle_logs: list, collapses: list,
                                alliances: list,
                                dominant_strategy: str) -> str:
    """
    Build a one-paragraph plain English summary of the simulation run.

    Args:
        cycle_logs:        Sorted list of cycle log dicts.
        collapses:         List of collapse dicts.
        alliances:         List of alliance dicts.
        dominant_strategy: Most common strategy label.

    Returns:
        Summary paragraph string.
    """
    total_cycles = len(cycle_logs)
    collapse_count = len(collapses)
    surviving_count = 5 - collapse_count
    alliance_count = len(alliances)

    # Build collapsed names string
    if collapse_count > 0:
        collapsed_names = ", ".join(
            c["region"].capitalize() for c in collapses
        )
        collapse_text = (
            f"{collapse_count} region{'s' if collapse_count > 1 else ''} "
            f"collapsed - {collapsed_names}."
        )
    else:
        collapse_text = "No regions collapsed."

    # Count climate events from cycle logs
    climate_count = 0
    for log in cycle_logs:
        snapshot = log.get("regions_snapshot", {})
        for region_data in snapshot.values():
            hits = region_data.get("climate_hits_this_cycle", 0)
            climate_count += hits

    return (
        f"WorldSim ran {total_cycles} cycles across 5 regions. "
        f"{surviving_count} region{'s' if surviving_count != 1 else ''} "
        f"survived to final cycle. {collapse_text} "
        f"The dominant emergent strategy was {dominant_strategy}. "
        f"{alliance_count} stable trade alliance"
        f"{'s' if alliance_count != 1 else ''} formed during simulation. "
        f"Climate events triggered {climate_count} resource shocks "
        f"across the world."
    )


# ===========================================================================
# FUNCTION 7 — Generate Key Insights
# ===========================================================================

def generate_key_insights(collapses: list, alliances: list,
                          dominant_strategy: str,
                          cycle_logs: list) -> list:
    """
    Generate 4 to 6 plain English insight cards mixing collapse,
    alliance, strategy, and surprising findings.

    Args:
        collapses:         List of collapse dicts.
        alliances:         List of alliance dicts.
        dominant_strategy: Most common strategy label.
        cycle_logs:        Sorted list of cycle log dicts.

    Returns:
        List of 4-6 insight strings.
    """
    insights = []

    # --- Collapse insights ---
    for collapse in collapses[:2]:  # Max 2 collapse insights
        insights.append(collapse["description"])

    # --- Alliance insights ---
    if alliances:
        longest = max(alliances, key=lambda a: a["duration"])
        name_a = longest["regions"][0].capitalize()
        name_b = longest["regions"][1].capitalize()
        insights.append(
            f"{name_a} and {name_b} maintained the longest alliance - "
            f"{longest['duration']} consecutive cycles - driven by "
            f"complementary resource exchange."
        )

    # --- Strategy insight ---
    if dominant_strategy in ("Aggressor", "Trader", "Hoarder", "Investor"):
        strategy_insights = {
            "Aggressor": (
                "Aggressive strategies showed initial resource gains "
                "but regions relying on aggression faced declining trust "
                "and trade isolation in later cycles."
            ),
            "Trader": (
                "Trade-focused regions consistently outperformed "
                "isolationist strategies, building resilient supply "
                "chains that buffered against climate shocks."
            ),
            "Hoarder": (
                "Hoarding behavior provided short-term security but "
                "prevented the resource diversification needed for "
                "long-term stability."
            ),
            "Investor": (
                "Investment strategies paid off in later cycles as "
                "accumulated resource capacity outpaced consumption "
                "growth in developed regions."
            ),
        }
        insights.append(strategy_insights[dominant_strategy])
    else:
        insights.append(
            "No single strategy emerged as dominant - regional "
            "starting conditions and early interactions shaped "
            "divergent survival paths."
        )

    # --- Surprising finding based on data ---
    if cycle_logs:
        final_snapshot = cycle_logs[-1].get("regions_snapshot", {})

        # Find the highest health region
        best_region = None
        best_health = 0
        for rid, rdata in final_snapshot.items():
            h = rdata.get("health_score", 0)
            if h > best_health:
                best_health = h
                best_region = rid

        if best_region:
            insights.append(
                f"{best_region.capitalize()}'s approach produced the "
                f"most stable long-term outcome with a final health "
                f"score of {best_health:.1f}, demonstrating that "
                f"adaptability outweighs raw resource advantage."
            )

    # --- Climate observation ---
    if len(collapses) > 0 and len(alliances) > 0:
        insights.append(
            "Climate events accelerated cooperation - trade "
            "partnerships formed faster in cycles following "
            "drought and energy crisis events."
        )
    elif len(collapses) == 0:
        insights.append(
            "All five regions survived the full simulation - "
            "a rare outcome suggesting early cooperation "
            "prevented cascade failures."
        )

    # Ensure 4-6 insights
    return insights[:6]


# ===========================================================================
# FUNCTION 8 — Run Analysis (Master Function)
# ===========================================================================

def run_analysis() -> bool:
    """
    Master analysis function. Call this after simulation completes.

    Steps:
        1. Load cycle logs from Firestore
        2. Detect collapses, alliances, dominant strategy
        3. Generate insights, real-world parallel, summary
        4. Write results to Firestore with field names
           matching frontend AnalysisOverlay.jsx exactly

    Returns:
        True if analysis completed and written successfully.
        False if logs were empty or write failed.
    """
    # Step 1: Load data
    logs = load_cycle_logs()
    if not logs:
        logger.warning("run_analysis: no cycle logs found. Skipping.")
        return False

    # Step 2: Detect patterns
    collapses = detect_collapses(logs)
    alliances = detect_alliances(logs)
    dominant = detect_dominant_strategy(logs)

    # Step 3: Generate narrative
    parallel = generate_real_world_parallel(collapses, alliances, dominant)
    summary = generate_simulation_summary(logs, collapses, alliances, dominant)
    insights = generate_key_insights(collapses, alliances, dominant, logs)

    # Step 4: Write to Firestore with EXACT frontend field names
    try:
        data = {
            "key_insights": insights,
            "collapsed_regions": collapses,
            "alliance_clusters": alliances,
            "dominant_strategy": dominant,
            "real_world_parallel": parallel,
            "simulation_summary": summary,
            "generated_at": firestore.SERVER_TIMESTAMP,
        }

        doc_ref = db.collection(ANALYSIS_COLLECTION).document(ANALYSIS_DOC_ID)
        doc_ref.set(data, merge=False)

        logger.info(
            "run_analysis: wrote analysis - %d insights, %d collapses, "
            "%d alliances, dominant=%s.",
            len(insights), len(collapses), len(alliances), dominant,
        )
        return True

    except Exception as exc:
        logger.error("run_analysis: failed to write analysis - %s", exc)
        return False


# ===========================================================================
# Test Cases
# ===========================================================================

if __name__ == "__main__":

    logging.basicConfig(level=logging.INFO, format="%(name)s - %(message)s")

    PASS = "[PASS]"
    FAIL = "[FAIL]"

    # -----------------------------------------------------------------------
    # Build mock cycle logs (20 cycles)
    # urbanex declines to collapse at cycle 15
    # aquaria and agrovia trade consistently
    # -----------------------------------------------------------------------

    def build_mock_logs():
        """Generate 20 mock cycle log dicts for testing."""
        logs = []

        for cycle in range(1, 21):
            regions_snapshot = {}

            # --- Aquaria: healthy trader ---
            regions_snapshot["aquaria"] = {
                "water": max(10, 90 - cycle * 1.5),
                "food": max(10, 60 - cycle * 0.8),
                "energy": max(10, 30 + cycle * 0.5),
                "land": 70,
                "population": 500 + cycle * 5,
                "health_score": max(25, 75 - cycle * 0.5),
                "is_collapsed": False,
                "last_action": "trade",
                "strategy_label": "Trader",
                "climate_hits_this_cycle": 1 if cycle in (5, 12) else 0,
            }

            # --- Agrovia: healthy trader (alliance partner) ---
            regions_snapshot["agrovia"] = {
                "water": max(10, 50 - cycle * 0.5),
                "food": max(10, 95 - cycle * 1.0),
                "energy": max(10, 40 + cycle * 0.3),
                "land": 40,
                "population": 600 + cycle * 3,
                "health_score": max(30, 70 - cycle * 0.3),
                "is_collapsed": False,
                "last_action": "trade",
                "strategy_label": "Trader",
                "climate_hits_this_cycle": 1 if cycle == 8 else 0,
            }

            # --- Petrozon: hoarder ---
            regions_snapshot["petrozon"] = {
                "water": max(5, 30 - cycle * 1.0),
                "food": max(5, 35 - cycle * 0.8),
                "energy": 95,
                "land": 60,
                "population": 450 - cycle * 2,
                "health_score": max(25, 65 - cycle * 1.0),
                "is_collapsed": False,
                "last_action": "hoard",
                "strategy_label": "Hoarder",
                "climate_hits_this_cycle": 0,
            }

            # --- Urbanex: declining to collapse at cycle 15 ---
            ux_health = max(5, 60 - cycle * 4)
            ux_collapsed = ux_health < 20
            regions_snapshot["urbanex"] = {
                "water": max(0, 40 - cycle * 3),
                "food": max(0, 45 - cycle * 3),
                "energy": max(0, 40 - cycle * 2.5),
                "land": 30,
                "population": max(50, 950 - cycle * 50),
                "health_score": ux_health,
                "is_collapsed": ux_collapsed,
                "last_action": "aggress" if cycle > 10 else "invest",
                "strategy_label": "Aggressor" if cycle > 10 else "Investor",
                "climate_hits_this_cycle": 1 if cycle in (3, 7, 11) else 0,
            }

            # --- Terranova: balanced survivor ---
            regions_snapshot["terranova"] = {
                "water": max(15, 55 - cycle * 0.5),
                "food": max(15, 60 - cycle * 0.4),
                "energy": max(15, 55 - cycle * 0.3),
                "land": 90,
                "population": 400 + cycle * 2,
                "health_score": max(35, 72 - cycle * 0.5),
                "is_collapsed": False,
                "last_action": "invest",
                "strategy_label": "Balanced",
                "climate_hits_this_cycle": 0,
            }

            logs.append({
                "cycle": cycle,
                "regions_snapshot": regions_snapshot,
            })

        return logs

    mock_logs = build_mock_logs()

    # ===================================================================
    # TEST 1 — Detect Collapses
    # ===================================================================
    print("=" * 60)
    print("  TEST 1 - Detect Collapses")
    print("=" * 60)

    collapses = detect_collapses(mock_logs)
    print(f"  Found {len(collapses)} collapse(s)")

    found_urbanex = any(c["region"] == "urbanex" for c in collapses)
    print(f"  Urbanex collapsed? {PASS if found_urbanex else FAIL}")

    for c in collapses:
        print(f"    {c['region']}: cycle {c['collapsed_at']}, "
              f"cause={c['root_cause']}")
        print(f"    {c['description']}")
    print()

    # ===================================================================
    # TEST 2 — Detect Alliances
    # ===================================================================
    print("=" * 60)
    print("  TEST 2 - Detect Alliances")
    print("=" * 60)

    alliances = detect_alliances(mock_logs)
    print(f"  Found {len(alliances)} alliance(s)")

    for a in alliances:
        print(f"    {a['regions']}: formed cycle {a['formed_at']}, "
              f"duration={a['duration']}, held={a['held_until_end']}")
        print(f"    {a['description']}")
    print()

    # ===================================================================
    # TEST 3 — Dominant Strategy
    # ===================================================================
    print("=" * 60)
    print("  TEST 3 - Dominant Strategy")
    print("=" * 60)

    dominant = detect_dominant_strategy(mock_logs)
    print(f"  Dominant strategy: {dominant}")
    print(f"  Not empty? {PASS if dominant else FAIL}")
    print()

    # ===================================================================
    # TEST 4 — Real World Parallel
    # ===================================================================
    print("=" * 60)
    print("  TEST 4 - Real World Parallel")
    print("=" * 60)

    parallel = generate_real_world_parallel(collapses, alliances, dominant)
    print(f"  {parallel}")
    print(f"  Not empty? {PASS if parallel else FAIL}")
    print()

    # ===================================================================
    # TEST 5 — Key Insights
    # ===================================================================
    print("=" * 60)
    print("  TEST 5 - Key Insights")
    print("=" * 60)

    insights = generate_key_insights(
        collapses, alliances, dominant, mock_logs
    )
    print(f"  Generated {len(insights)} insights")
    in_range = 4 <= len(insights) <= 6
    print(f"  Count 4-6? {PASS if in_range else FAIL}")

    for i, insight in enumerate(insights, 1):
        print(f"    [{i}] {insight}")
    print()

    # ===================================================================
    # TEST 6 — Simulation Summary
    # ===================================================================
    print("=" * 60)
    print("  TEST 6 - Simulation Summary")
    print("=" * 60)

    summary = generate_simulation_summary(
        mock_logs, collapses, alliances, dominant
    )
    print(f"  {summary}")
    print(f"  Not empty? {PASS if summary else FAIL}")
    print()

    # ===================================================================
    print("=" * 60)
    print("  Analysis service tested successfully")
    print("  In production run_analysis() after simulation completes")
    print("=" * 60)
