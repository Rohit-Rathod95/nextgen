"""
reward.py — Reward Calculation Module for WorldSim

Computes a single reward score at the end of each simulation cycle
for a given region. The reward drives adaptive strategy evolution
in agent.py by quantifying how well a region performed across
population growth, resource balance, depletion risk, and climate
instability.

Reward Formula:
    reward = (POPULATION_WEIGHT × population_change_ratio)
           + (RESOURCE_WEIGHT  × resource_balance_score)
           - (DEPLETION_WEIGHT × depletion_penalty)
           - (INSTABILITY_WEIGHT × instability_penalty)

Final reward is clamped to [-1.0, +1.0] and rounded to 4 decimals.
"""

# ---------------------------------------------------------------------------
# Constants — reward component weights and thresholds
# ---------------------------------------------------------------------------

POPULATION_WEIGHT = 0.4       # Weight for population change component
RESOURCE_WEIGHT = 0.3         # Weight for resource balance component
DEPLETION_WEIGHT = 0.2        # Weight for resource depletion penalty
INSTABILITY_WEIGHT = 0.1      # Weight for climate instability penalty

CRITICAL_THRESHOLD = 30       # Resources below this level trigger depletion penalty
RESOURCE_COUNT = 4            # Total resource types: water, food, energy, land
MAX_CLIMATE_HITS = 3          # Maximum expected climate events per cycle (for normalization)

RESOURCE_KEYS = ("water", "food", "energy", "land")
REWARD_MIN = -1.0             # Lower bound for final reward
REWARD_MAX = 1.0              # Upper bound for final reward
REWARD_PRECISION = 4          # Decimal places for rounding


# ---------------------------------------------------------------------------
# Helper — clamp a value between a minimum and maximum
# ---------------------------------------------------------------------------

def _clamp(value: float, lo: float, hi: float) -> float:
    """Restrict a numeric value to the range [lo, hi]."""
    return max(lo, min(hi, value))


# ---------------------------------------------------------------------------
# Component 1 — Population Change Ratio
# ---------------------------------------------------------------------------

def calculate_population_change(old_state: dict, new_state: dict) -> float:
    """
    Compute the relative change in population between two cycle states.

    Args:
        old_state: Region state dictionary BEFORE the cycle.
        new_state: Region state dictionary AFTER the cycle.

    Returns:
        Population change ratio clamped to [-1.0, +1.0].
        Returns 0.0 if the old population is zero or negative (edge case).
    """
    old_pop = old_state.get("population", 0)
    new_pop = new_state.get("population", 0)

    # Guard against division by zero or nonsensical negative populations
    if old_pop <= 0:
        return 0.0

    # Ratio: positive means growth, negative means decline
    ratio = (new_pop - old_pop) / old_pop

    return _clamp(ratio, REWARD_MIN, REWARD_MAX)


# ---------------------------------------------------------------------------
# Component 2 — Resource Balance Score
# ---------------------------------------------------------------------------

def calculate_resource_balance(new_state: dict) -> float:
    """
    Compute the average resource level across all four resource types,
    normalized to [0.0, 1.0].

    A score of 1.0 means all resources are at maximum (100).
    A score of 0.0 means all resources are fully depleted.

    Args:
        new_state: Region state dictionary AFTER the cycle.

    Returns:
        Normalized average resource level between 0.0 and 1.0.
    """
    # Sum up each resource value (each is on a 0–100 scale)
    total = sum(new_state.get(key, 0) for key in RESOURCE_KEYS)

    # Normalize: divide by (count × max_per_resource) to get 0.0–1.0
    balance = total / (RESOURCE_COUNT * 100)

    return _clamp(balance, 0.0, 1.0)


# ---------------------------------------------------------------------------
# Component 3 — Depletion Penalty
# ---------------------------------------------------------------------------

def calculate_depletion_penalty(new_state: dict) -> float:
    """
    Count the number of resources that have fallen below the critical
    threshold (30) and normalize by the total resource count.

    Penalizes regions that let individual resources bottom out, even
    if the overall average is acceptable.

    Args:
        new_state: Region state dictionary AFTER the cycle.

    Returns:
        Penalty between 0.0 (no depleted resources) and 1.0 (all depleted).
    """
    # Count how many of the four resources are critically low
    depleted_count = sum(
        1 for key in RESOURCE_KEYS
        if new_state.get(key, 0) < CRITICAL_THRESHOLD
    )

    # Normalize to 0.0–1.0 range
    return depleted_count / RESOURCE_COUNT


# ---------------------------------------------------------------------------
# Component 4 — Instability Penalty
# ---------------------------------------------------------------------------

def calculate_instability_penalty(new_state: dict) -> float:
    """
    Penalize regions based on the number of climate events that
    struck during this cycle, normalized against the expected maximum.

    Args:
        new_state: Region state dictionary AFTER the cycle.

    Returns:
        Penalty between 0.0 (no climate hits) and 1.0 (max or more hits).
    """
    hits = new_state.get("climate_hits_this_cycle", 0)

    # Normalize and clamp — more than MAX_CLIMATE_HITS still caps at 1.0
    return _clamp(hits / MAX_CLIMATE_HITS, 0.0, 1.0)


# ---------------------------------------------------------------------------
# Main — Calculate Reward
# ---------------------------------------------------------------------------

def calculate_reward(old_state: dict, new_state: dict) -> float:
    """
    Compute the composite reward score for a region after one simulation cycle.

    Combines four weighted components:
        +  population growth  (encourages expansion)
        +  resource balance   (encourages sustainability)
        −  depletion penalty  (punishes critical shortages)
        −  instability penalty(punishes vulnerability to climate)

    Args:
        old_state: Region state dictionary BEFORE the cycle.
        new_state: Region state dictionary AFTER the cycle.

    Returns:
        Final reward score clamped to [-1.0, +1.0], rounded to 4 decimals.
    """
    # Calculate each component independently
    pop_change = calculate_population_change(old_state, new_state)
    res_balance = calculate_resource_balance(new_state)
    depletion = calculate_depletion_penalty(new_state)
    instability = calculate_instability_penalty(new_state)

    # Weighted combination — positive components add, penalties subtract
    reward = (
        POPULATION_WEIGHT   * pop_change
        + RESOURCE_WEIGHT   * res_balance
        - DEPLETION_WEIGHT  * depletion
        - INSTABILITY_WEIGHT * instability
    )

    # Clamp and round for clean output
    reward = _clamp(reward, REWARD_MIN, REWARD_MAX)

    return round(reward, REWARD_PRECISION)


# ---------------------------------------------------------------------------
# Debugging — Full Reward Breakdown
# ---------------------------------------------------------------------------

def get_reward_breakdown(old_state: dict, new_state: dict) -> dict:
    """
    Return all four reward components and the final composite score
    as a dictionary. Useful for analysis dashboards and debugging.

    Args:
        old_state: Region state dictionary BEFORE the cycle.
        new_state: Region state dictionary AFTER the cycle.

    Returns:
        Dictionary with keys:
            population_component  — weighted population change
            resource_component    — weighted resource balance
            depletion_component   — weighted depletion penalty (positive = bad)
            instability_component — weighted instability penalty (positive = bad)
            final_reward          — composite reward score
    """
    pop_change = calculate_population_change(old_state, new_state)
    res_balance = calculate_resource_balance(new_state)
    depletion = calculate_depletion_penalty(new_state)
    instability = calculate_instability_penalty(new_state)

    final = calculate_reward(old_state, new_state)

    return {
        "population_component": round(POPULATION_WEIGHT * pop_change, REWARD_PRECISION),
        "resource_component": round(RESOURCE_WEIGHT * res_balance, REWARD_PRECISION),
        "depletion_component": round(DEPLETION_WEIGHT * depletion, REWARD_PRECISION),
        "instability_component": round(INSTABILITY_WEIGHT * instability, REWARD_PRECISION),
        "final_reward": final,
    }


# ---------------------------------------------------------------------------
# Test Cases
# ---------------------------------------------------------------------------

if __name__ == "__main__":

    def print_test(label: str, old: dict, new: dict) -> None:
        """Pretty-print a test case with full reward breakdown."""
        breakdown = get_reward_breakdown(old, new)
        print(f"\n{'=' * 60}")
        print(f"  {label}")
        print(f"{'=' * 60}")
        print(f"  Population component : {breakdown['population_component']:+.4f}")
        print(f"  Resource component   : {breakdown['resource_component']:+.4f}")
        print(f"  Depletion component  : {breakdown['depletion_component']:+.4f}")
        print(f"  Instability component: {breakdown['instability_component']:+.4f}")
        print(f"  ─────────────────────────────────")
        print(f"  FINAL REWARD         : {breakdown['final_reward']:+.4f}")
        print(f"{'=' * 60}")

    # -----------------------------------------------------------------------
    # Test 1 — Healthy region improving
    # All resources above 60, population growing, no climate hits.
    # Expected: positive reward near +0.5
    # -----------------------------------------------------------------------
    old_healthy = {
        "region_id": "aquaria",
        "water": 65, "food": 70, "energy": 60, "land": 75,
        "population": 1000,
        "health_score": 80,
        "strategy_weights": {"trade": 0.4, "hoard": 0.2, "invest": 0.3, "aggress": 0.1},
        "trust_scores": {"aquaria": 1.0, "agrovia": 0.7, "petrozon": 0.5, "urbanex": 0.6, "terranova": 0.8},
        "last_action": "trade",
        "climate_hits_this_cycle": 0,
    }
    new_healthy = {
        "region_id": "aquaria",
        "water": 72, "food": 78, "energy": 68, "land": 80,
        "population": 1150,
        "health_score": 85,
        "strategy_weights": {"trade": 0.4, "hoard": 0.2, "invest": 0.3, "aggress": 0.1},
        "trust_scores": {"aquaria": 1.0, "agrovia": 0.7, "petrozon": 0.5, "urbanex": 0.6, "terranova": 0.8},
        "last_action": "trade",
        "climate_hits_this_cycle": 0,
    }
    print_test("TEST 1 — Healthy Region Improving", old_healthy, new_healthy)

    # -----------------------------------------------------------------------
    # Test 2 — Struggling region declining
    # Multiple resources below 30, population shrinking, 1 climate hit.
    # Expected: negative reward near -0.4
    # -----------------------------------------------------------------------
    old_struggling = {
        "region_id": "petrozon",
        "water": 35, "food": 40, "energy": 25, "land": 20,
        "population": 800,
        "health_score": 45,
        "strategy_weights": {"trade": 0.1, "hoard": 0.5, "invest": 0.1, "aggress": 0.3},
        "trust_scores": {"aquaria": 0.3, "agrovia": 0.4, "petrozon": 1.0, "urbanex": 0.2, "terranova": 0.3},
        "last_action": "hoard",
        "climate_hits_this_cycle": 0,
    }
    new_struggling = {
        "region_id": "petrozon",
        "water": 22, "food": 28, "energy": 18, "land": 15,
        "population": 650,
        "health_score": 30,
        "strategy_weights": {"trade": 0.1, "hoard": 0.5, "invest": 0.1, "aggress": 0.3},
        "trust_scores": {"aquaria": 0.3, "agrovia": 0.4, "petrozon": 1.0, "urbanex": 0.2, "terranova": 0.3},
        "last_action": "hoard",
        "climate_hits_this_cycle": 1,
    }
    print_test("TEST 2 — Struggling Region Declining", old_struggling, new_struggling)

    # -----------------------------------------------------------------------
    # Test 3 — Collapsed region
    # All resources near zero, population collapsed, 2 climate hits.
    # Expected: strongly negative reward near -0.9
    # -----------------------------------------------------------------------
    old_collapsed = {
        "region_id": "terranova",
        "water": 20, "food": 15, "energy": 10, "land": 12,
        "population": 500,
        "health_score": 20,
        "strategy_weights": {"trade": 0.05, "hoard": 0.1, "invest": 0.05, "aggress": 0.8},
        "trust_scores": {"aquaria": 0.1, "agrovia": 0.1, "petrozon": 0.1, "urbanex": 0.1, "terranova": 1.0},
        "last_action": "aggress",
        "climate_hits_this_cycle": 0,
    }
    new_collapsed = {
        "region_id": "terranova",
        "water": 3, "food": 2, "energy": 1, "land": 4,
        "population": 120,
        "health_score": 5,
        "strategy_weights": {"trade": 0.05, "hoard": 0.1, "invest": 0.05, "aggress": 0.8},
        "trust_scores": {"aquaria": 0.1, "agrovia": 0.1, "petrozon": 0.1, "urbanex": 0.1, "terranova": 1.0},
        "last_action": "aggress",
        "climate_hits_this_cycle": 2,
    }
    print_test("TEST 3 — Collapsed Region", old_collapsed, new_collapsed)
