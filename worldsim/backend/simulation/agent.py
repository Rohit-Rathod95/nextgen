"""
agent.py - Adaptive Agent Module for WorldSim

Each of the 5 regions has one autonomous agent that observes its
region state, selects an action, receives a reward from reward.py,
and evolves its strategy weights over 100 simulation cycles.

This is NOT neural-network RL. Agents use adaptive weight evolution:
four strategy weights (trade, hoard, invest, aggress) shift based
on outcome feedback, producing emergent personality differentiation.

Over time, some regions become Traders, others Hoarders, Investors,
or Aggressors - driven entirely by environmental pressure and reward.
"""

import copy
import random

# ---------------------------------------------------------------------------
# Region & Action Definitions
# ---------------------------------------------------------------------------

REGIONS = ["aquaria", "agrovia", "petrozon", "urbanex", "terranova"]

ACTIONS = ["trade", "hoard", "invest", "aggress", "emergency_hoard"]

# Normal actions eligible for weighted random selection (excludes emergency)
NORMAL_ACTIONS = ["trade", "hoard", "invest", "aggress"]

INITIAL_WEIGHTS = {
    "trade": 0.25,
    "hoard": 0.25,
    "invest": 0.25,
    "aggress": 0.25,
}

# ---------------------------------------------------------------------------
# Trust Constants
# ---------------------------------------------------------------------------

INITIAL_TRUST = 50
TRUST_MAX = 100
TRUST_MIN = 0

# ---------------------------------------------------------------------------
# Weight Bounds
# ---------------------------------------------------------------------------

WEIGHT_MIN = 0.05             # No strategy can drop below 5%
WEIGHT_MAX = 0.70             # No strategy can exceed 70%

# ---------------------------------------------------------------------------
# Resource Thresholds
# ---------------------------------------------------------------------------

CRITICAL_RESOURCE_THRESHOLD = 30    # Below this → flagged as critical
EMERGENCY_THRESHOLD = 20            # Below this → triggers emergency hoard
DESPERATION_THRESHOLD = 15          # Below this health → desperation aggression

# ---------------------------------------------------------------------------
# Trust Deltas - how much trust changes per event type
# ---------------------------------------------------------------------------

TRUST_TRADE_SUCCESS = 5
TRUST_TRADE_REJECTED = -8
TRUST_CONFLICT_WIN_ATTACKER = -25
TRUST_CONFLICT_LOSS_ATTACKER = -15
TRUST_OBSERVER_CONFLICT = -10
TRUST_ALLIANCE_BONUS = 2

# Alliance threshold - consecutive trade cycles to qualify
ALLIANCE_CYCLE_THRESHOLD = 10

# ---------------------------------------------------------------------------
# Trust Thresholds for Decision Logic
# ---------------------------------------------------------------------------

TRUST_TRADE_BOOST_THRESHOLD = 70    # High trust → trade boost
TRUST_TRADE_PARTNER_MIN = 40        # Minimum trust to consider trade
TRUST_AGGRESSION_TARGET_MAX = 20    # Low trust → aggression target

# ---------------------------------------------------------------------------
# Decision Modifiers
# ---------------------------------------------------------------------------

DESPERATION_AGGRESS_BOOST = 0.15    # Temporary aggress boost when desperate
TRUST_TRADE_BOOST = 0.10            # Temporary trade boost with trusted neighbor
DESPERATION_HEALTH_RATIO = 1.5      # Neighbor health must exceed own × this

# ---------------------------------------------------------------------------
# Reward Signal Scaling
# ---------------------------------------------------------------------------

STRONG_SIGNAL_THRESHOLD = 0.5       # |reward| above this → amplify updates
STRONG_SIGNAL_MULTIPLIER = 1.5
WEAK_SIGNAL_THRESHOLD = 0.1         # |reward| below this → dampen updates
WEAK_SIGNAL_MULTIPLIER = 0.3

# ---------------------------------------------------------------------------
# History Limits
# ---------------------------------------------------------------------------

HISTORY_LIMIT = 10                  # Max entries in reward/action history
TREND_WINDOW = 5                    # Number of recent rewards for trend calc
TREND_SENSITIVITY = 0.05            # Delta threshold for improving/declining

# ---------------------------------------------------------------------------
# Strategy Label Thresholds
# ---------------------------------------------------------------------------

DOMINANT_WEIGHT_THRESHOLD = 0.35    # Weight must exceed this to earn a label

# ---------------------------------------------------------------------------
# Weight Update Rules - outcome → {strategy: delta}
# ---------------------------------------------------------------------------

WEIGHT_UPDATE_RULES = {
    "trade_success":   {"trade": +0.05, "aggress": -0.02},
    "trade_rejected":  {"trade": -0.03, "hoard": +0.03},
    "hoard_success":   {"hoard": +0.04, "invest": -0.02},
    "hoard_hurt":      {"hoard": -0.04, "trade": +0.02},
    "invest_payoff":   {"invest": +0.05, "hoard": -0.01},
    "aggress_success": {"aggress": +0.05, "trade": -0.03},
    "aggress_failed":  {"aggress": -0.06, "hoard": +0.03},
    "emergency_hoard": {"hoard": +0.08, "aggress": +0.02,
                        "invest": -0.05, "trade": -0.05},
}

# Strategy key → human-readable label
STRATEGY_LABELS = {
    "trade": "Trader",
    "hoard": "Hoarder",
    "invest": "Investor",
    "aggress": "Aggressor",
}

RESOURCE_KEYS = ("water", "food", "energy", "land")


# ===========================================================================
# Agent Class
# ===========================================================================

class Agent:
    """
    Adaptive agent for a single WorldSim region.

    Observes regional state, selects actions via weighted randomization,
    and evolves strategy weights based on reward feedback. Trust scores
    toward other regions modulate trade and aggression decisions.
    """

    def __init__(self, region_id: str):
        """
        Initialize an agent bound to a specific region.

        Args:
            region_id: One of the 5 region identifiers (e.g. "aquaria").
        """
        self.region_id = region_id

        # Strategy weights - always sum to 1.0
        self.strategy_weights = copy.deepcopy(INITIAL_WEIGHTS)

        # Trust scores toward every OTHER region (0–100 scale)
        self.trust_scores = {
            r: INITIAL_TRUST for r in REGIONS if r != self.region_id
        }

        # Action and reward tracking
        self.last_action = None
        self.last_reward = 0.0
        self.reward_history = []    # Rolling window of last N rewards
        self.action_history = []    # Rolling window of last N actions

        # Derived personality label based on dominant weight
        self.strategy_label = "Balanced"

        # Alliance tracking - consecutive trade cycles per partner
        self.alliance_cycles = {
            r: 0 for r in REGIONS if r != self.region_id
        }

        # Total cycles this agent has survived
        self.cycles_survived = 0

    # -----------------------------------------------------------------------
    # METHOD 1 - Observe
    # -----------------------------------------------------------------------

    def observe(self, region_state: dict, world_state: dict) -> dict:
        """
        Build an observation dictionary from the current region and world state.

        The agent does NOT see raw world data directly - it constructs
        a filtered view that mirrors what a regional leader would know.

        Args:
            region_state: This region's current state dictionary.
            world_state:  Dictionary of all regions keyed by region_id.

        Returns:
            Observation dict used by decide().
        """
        # --- Own resource snapshot ---
        own_resources = {
            key: region_state.get(key, 0) for key in RESOURCE_KEYS
        }

        own_population = region_state.get("population", 0)
        own_health = region_state.get("health_score", 0)

        # --- Flag resources below critical and emergency thresholds ---
        resource_critical = [
            key for key in RESOURCE_KEYS
            if region_state.get(key, 0) < CRITICAL_RESOURCE_THRESHOLD
        ]

        resource_emergency = [
            key for key in RESOURCE_KEYS
            if region_state.get(key, 0) < EMERGENCY_THRESHOLD
        ]

        # --- Neighbor health scores (other regions only) ---
        neighbor_health = {}
        for rid, rstate in world_state.items():
            if rid != self.region_id:
                neighbor_health[rid] = rstate.get("health_score", 0)

        # --- Compute recent reward trend ---
        recent_trend = self._compute_reward_trend()

        # --- Current cycle number ---
        cycle = region_state.get("cycle", self.cycles_survived)

        return {
            "own_resources": own_resources,
            "own_population": own_population,
            "own_health": own_health,
            "resource_critical": resource_critical,
            "resource_emergency": resource_emergency,
            "neighbor_health": neighbor_health,
            "neighbor_trust": copy.deepcopy(self.trust_scores),
            "recent_reward_trend": recent_trend,
            "cycle": cycle,
        }

    # -----------------------------------------------------------------------
    # METHOD 2 - Decide
    # -----------------------------------------------------------------------

    def decide(self, observation: dict) -> str:
        """
        Select an action based on the current observation.

        Decision follows a priority chain:
            1. Emergency override   → emergency_hoard
            2. Desperation check    → temporary aggress boost
            3. Trust-based boost    → temporary trade boost
            4. Weighted random pick → from 4 normal actions

        Args:
            observation: Dict returned by observe().

        Returns:
            Action string from ACTIONS.
        """
        # --- STEP 1: Emergency override ---
        # If ANY resource is below the emergency threshold, panic-hoard
        if observation.get("resource_emergency"):
            return "emergency_hoard"

        # Start with a copy of current weights for temporary adjustments
        adjusted = copy.deepcopy(self.strategy_weights)

        # --- STEP 2: Desperation aggression check ---
        # When health is critically low AND trending downward AND a
        # much-healthier neighbor exists, desperation makes aggression tempting
        own_health = observation.get("own_health", 0)
        trend = observation.get("recent_reward_trend", "stable")

        if own_health < DESPERATION_THRESHOLD and trend == "declining":
            neighbor_health = observation.get("neighbor_health", {})
            # Check if any neighbor is significantly healthier
            has_strong_neighbor = any(
                nh > own_health * DESPERATION_HEALTH_RATIO
                for nh in neighbor_health.values()
            )
            if has_strong_neighbor:
                adjusted["aggress"] += DESPERATION_AGGRESS_BOOST

        # --- STEP 3: Trust-based trade boost ---
        # If the most-trusted neighbor has high trust, lean into trade
        trust_scores = observation.get("neighbor_trust", {})
        if trust_scores:
            best_trust = max(trust_scores.values())
            if best_trust > TRUST_TRADE_BOOST_THRESHOLD:
                adjusted["trade"] += TRUST_TRADE_BOOST

        # --- STEP 4: Weighted random selection ---
        # Normalize adjusted weights so they sum to 1.0
        action_list = NORMAL_ACTIONS
        weights = [max(adjusted.get(a, 0), 0) for a in action_list]
        total = sum(weights)

        # Guard: if all weights are zero (shouldn't happen), equal chance
        if total <= 0:
            weights = [1.0] * len(action_list)
            total = sum(weights)

        normalized = [w / total for w in weights]

        # Weighted random choice
        selected = random.choices(action_list, weights=normalized, k=1)[0]
        return selected

    # -----------------------------------------------------------------------
    # METHOD 3 - Update Weights
    # -----------------------------------------------------------------------

    def update_weights(self, action: str, outcome: str, reward_score: float):
        """
        Evolve strategy weights based on the outcome of an action.

        Steps:
            1. Apply rule-based deltas scaled by reward magnitude
            2. Enforce per-weight bounds [WEIGHT_MIN, WEIGHT_MAX]
            3. Normalize to sum to 1.0
            4. Update reward & action histories
            5. Recompute strategy label

        Args:
            action:       The action that was taken this cycle.
            outcome:      Outcome key matching WEIGHT_UPDATE_RULES.
            reward_score: Numeric reward from reward.py.
        """
        # --- STEP 1: Apply weight update rules ---
        deltas = WEIGHT_UPDATE_RULES.get(outcome, {})

        # Scale factor based on reward magnitude - strong outcomes matter more
        if abs(reward_score) > STRONG_SIGNAL_THRESHOLD:
            scale = STRONG_SIGNAL_MULTIPLIER
        elif abs(reward_score) < WEAK_SIGNAL_THRESHOLD:
            scale = WEAK_SIGNAL_MULTIPLIER
        else:
            scale = 1.0

        for strategy, delta in deltas.items():
            if strategy in self.strategy_weights:
                self.strategy_weights[strategy] += delta * scale

        # --- STEP 2: Enforce weight bounds ---
        for strategy in self.strategy_weights:
            self.strategy_weights[strategy] = max(
                WEIGHT_MIN,
                min(WEIGHT_MAX, self.strategy_weights[strategy])
            )

        # --- STEP 3: Normalize to sum to 1.0 ---
        total = sum(self.strategy_weights.values())
        if total > 0:
            for strategy in self.strategy_weights:
                self.strategy_weights[strategy] /= total

        # --- STEP 4: Update reward history ---
        self.last_reward = reward_score
        self.reward_history.append(reward_score)
        if len(self.reward_history) > HISTORY_LIMIT:
            self.reward_history = self.reward_history[-HISTORY_LIMIT:]

        # --- STEP 5: Update action history ---
        self.last_action = action
        self.action_history.append(action)
        if len(self.action_history) > HISTORY_LIMIT:
            self.action_history = self.action_history[-HISTORY_LIMIT:]

        # --- STEP 6: Recompute strategy label ---
        self._update_strategy_label()

    # -----------------------------------------------------------------------
    # METHOD 4 - Update Trust
    # -----------------------------------------------------------------------

    def update_trust(self, event_type: str, target_region: str,
                     all_regions: list = None):
        """
        Adjust trust scores based on an interaction event.

        Handles trade success/rejection, conflict outcomes, and
        long-running alliance bonuses.

        Args:
            event_type:    One of "trade_success", "trade_rejected",
                           "conflict_win", "conflict_loss",
                           "alliance_maintained".
            target_region: The region involved in the event.
            all_regions:   List of all region IDs (needed for observer
                           trust penalties during conflicts).
        """
        if all_regions is None:
            all_regions = REGIONS

        if event_type == "trade_success":
            # Successful trade builds mutual trust
            if target_region in self.trust_scores:
                self.trust_scores[target_region] += TRUST_TRADE_SUCCESS

        elif event_type == "trade_rejected":
            # Rejected trade erodes trust toward the rejector
            if target_region in self.trust_scores:
                self.trust_scores[target_region] += TRUST_TRADE_REJECTED

        elif event_type == "conflict_win":
            # I won against target - all OBSERVERS lose trust toward me
            # (The attacker's own trust isn't updated here; world handles it)
            for rid in all_regions:
                if rid != self.region_id and rid != target_region:
                    # Observer regions see self as aggressive
                    if rid in self.trust_scores:
                        self.trust_scores[rid] += TRUST_OBSERVER_CONFLICT

        elif event_type == "conflict_loss":
            # I lost against target - smaller observer penalty
            for rid in all_regions:
                if rid != self.region_id and rid != target_region:
                    if rid in self.trust_scores:
                        # Losing is less threatening than winning
                        self.trust_scores[rid] += (TRUST_OBSERVER_CONFLICT // 2)

        elif event_type == "alliance_maintained":
            # Track consecutive trade cycles with this partner
            if target_region not in self.alliance_cycles:
                self.alliance_cycles[target_region] = 0
            self.alliance_cycles[target_region] += 1

            # After enough consecutive cycles, award alliance bonus
            if self.alliance_cycles[target_region] >= ALLIANCE_CYCLE_THRESHOLD:
                if target_region in self.trust_scores:
                    self.trust_scores[target_region] += TRUST_ALLIANCE_BONUS

        # --- Clamp all trust scores to valid range ---
        for rid in self.trust_scores:
            self.trust_scores[rid] = max(
                TRUST_MIN, min(TRUST_MAX, self.trust_scores[rid])
            )

    # -----------------------------------------------------------------------
    # METHOD 5 - State Snapshot
    # -----------------------------------------------------------------------

    def get_state_snapshot(self) -> dict:
        """
        Return the complete agent state for Firestore persistence.

        Called by firestore_service.py at the end of every cycle
        to write agent data to the database.

        Returns:
            Dictionary containing all agent fields.
        """
        return {
            "region_id": self.region_id,
            "strategy_weights": copy.deepcopy(self.strategy_weights),
            "trust_scores": copy.deepcopy(self.trust_scores),
            "last_action": self.last_action,
            "last_reward": self.last_reward,
            "strategy_label": self.strategy_label,
            "cycles_survived": self.cycles_survived,
            "reward_trend": self._compute_reward_trend(),
        }

    # -----------------------------------------------------------------------
    # METHOD 6 - Find Best Trade Partner
    # -----------------------------------------------------------------------

    def find_best_trade_partner(self, world_state: dict) -> str | None:
        """
        Identify the optimal region to trade with based on trust,
        trade availability, and complementary resource needs.

        Logic:
            1. Filter neighbors with trust > TRUST_TRADE_PARTNER_MIN
            2. Filter neighbors that are "trade_open" in world_state
            3. Find which resource self needs most (lowest value)
            4. Among eligible partners, pick the one with the highest
               surplus of that needed resource

        Args:
            world_state: Dict of all region states keyed by region_id.

        Returns:
            region_id of best partner, or None if no valid partner exists.
        """
        own_state = world_state.get(self.region_id, {})

        # Determine which resource self needs most (lowest level)
        own_resources = {
            key: own_state.get(key, 0) for key in RESOURCE_KEYS
        }
        if not own_resources:
            return None

        most_needed = min(own_resources, key=own_resources.get)

        best_partner = None
        best_surplus = -1

        for rid, rstate in world_state.items():
            # Skip self
            if rid == self.region_id:
                continue

            # Must have sufficient trust
            if self.trust_scores.get(rid, 0) <= TRUST_TRADE_PARTNER_MIN:
                continue

            # Must be marked as trade-open
            if not rstate.get("trade_open", False):
                continue

            # Check their surplus of the resource we need most
            partner_level = rstate.get(most_needed, 0)
            if partner_level > best_surplus:
                best_surplus = partner_level
                best_partner = rid

        return best_partner

    # -----------------------------------------------------------------------
    # METHOD 7 - Find Weakest Neighbor
    # -----------------------------------------------------------------------

    def find_weakest_neighbor(self, world_state: dict) -> str | None:
        """
        Identify the most vulnerable neighbor for aggression targeting.

        Logic:
            1. Filter regions where trust toward self < TRUST_AGGRESSION_TARGET_MAX
            2. Among those, find the one with the lowest health_score
            3. Target must be weaker than self (lower health)

        Args:
            world_state: Dict of all region states keyed by region_id.

        Returns:
            region_id of weakest valid target, or None if no target qualifies.
        """
        own_state = world_state.get(self.region_id, {})
        own_health = own_state.get("health_score", 0)

        weakest = None
        lowest_health = float("inf")

        for rid, rstate in world_state.items():
            # Skip self
            if rid == self.region_id:
                continue

            # Only target regions that distrust us (low trust toward self)
            if self.trust_scores.get(rid, INITIAL_TRUST) >= TRUST_AGGRESSION_TARGET_MAX:
                continue

            neighbor_health = rstate.get("health_score", 0)

            # Target must be weaker than self
            if neighbor_health >= own_health:
                continue

            # Track the weakest among valid targets
            if neighbor_health < lowest_health:
                lowest_health = neighbor_health
                weakest = rid

        return weakest

    # -----------------------------------------------------------------------
    # METHOD 8 - Reset
    # -----------------------------------------------------------------------

    def reset(self):
        """
        Reset the agent to its initial state for a new simulation run.

        Preserves region_id but clears all learned behavior, trust,
        and history so the agent starts fresh.
        """
        self.strategy_weights = copy.deepcopy(INITIAL_WEIGHTS)
        self.trust_scores = {
            r: INITIAL_TRUST for r in REGIONS if r != self.region_id
        }
        self.last_action = None
        self.last_reward = 0.0
        self.reward_history = []
        self.action_history = []
        self.strategy_label = "Balanced"
        self.alliance_cycles = {
            r: 0 for r in REGIONS if r != self.region_id
        }
        self.cycles_survived = 0

    # -----------------------------------------------------------------------
    # Internal Helpers
    # -----------------------------------------------------------------------

    def _compute_reward_trend(self) -> str:
        """
        Determine whether recent rewards are improving, declining, or stable.

        Compares the average of the last TREND_WINDOW rewards against
        the most recent reward using TREND_SENSITIVITY as threshold.

        Returns:
            "improving", "declining", or "stable".
        """
        if len(self.reward_history) < TREND_WINDOW:
            return "stable"

        recent = self.reward_history[-TREND_WINDOW:]
        avg = sum(recent) / len(recent)

        if avg > self.last_reward + TREND_SENSITIVITY:
            return "improving"
        elif avg < self.last_reward - TREND_SENSITIVITY:
            return "declining"
        else:
            return "stable"

    def _update_strategy_label(self):
        """
        Recompute the human-readable strategy label based on the
        current dominant weight. If no weight exceeds the dominance
        threshold, the agent is labeled "Balanced".
        """
        dominant_key = max(self.strategy_weights, key=self.strategy_weights.get)
        dominant_val = self.strategy_weights[dominant_key]

        if dominant_val > DOMINANT_WEIGHT_THRESHOLD:
            self.strategy_label = STRATEGY_LABELS.get(dominant_key, "Balanced")
        else:
            self.strategy_label = "Balanced"


# ===========================================================================
# Test Cases
# ===========================================================================

if __name__ == "__main__":

    def fmt_weights(w: dict) -> str:
        """Format weights dict for compact display."""
        return "  ".join(f"{k}: {v:.4f}" for k, v in w.items())

    def fmt_trust(t: dict) -> str:
        """Format trust dict for compact display."""
        return "  ".join(f"{k}: {v}" for k, v in t.items())

    PASS = "[PASS]"
    FAIL = "[FAIL]"

    # ===================================================================
    # TEST 1 - Initial State
    # ===================================================================
    print("=" * 60)
    print("  TEST 1 - Initial Agent State")
    print("=" * 60)

    agent = Agent("urbanex")
    print(f"  Region: {agent.region_id}")
    print(f"  Weights: {fmt_weights(agent.strategy_weights)}")
    print(f"  Trust:   {fmt_trust(agent.trust_scores)}")
    print(f"  Label:   {agent.strategy_label}")

    # Verify all weights are 0.25
    weights_ok = all(v == 0.25 for v in agent.strategy_weights.values())
    print(f"  All weights = 0.25? {PASS if weights_ok else FAIL}")

    # Verify all trust scores are 50
    trust_ok = all(v == INITIAL_TRUST for v in agent.trust_scores.values())
    print(f"  All trust = {INITIAL_TRUST}?   {PASS if trust_ok else FAIL}")

    # Verify urbanex is not in its own trust scores
    self_ok = "urbanex" not in agent.trust_scores
    print(f"  Self excluded?     {PASS if self_ok else FAIL}")
    print()

    # ===================================================================
    # TEST 2 - Emergency Override
    # ===================================================================
    print("=" * 60)
    print("  TEST 2 - Emergency Hoard Override")
    print("=" * 60)

    emergency_agent = Agent("aquaria")

    # Mock observation with water in emergency zone
    mock_obs = {
        "own_resources": {"water": 15, "food": 60, "energy": 55, "land": 70},
        "own_population": 800,
        "own_health": 40,
        "resource_critical": ["water"],
        "resource_emergency": ["water"],
        "neighbor_health": {"agrovia": 70, "petrozon": 50, "urbanex": 60, "terranova": 45},
        "neighbor_trust": {"agrovia": 50, "petrozon": 50, "urbanex": 50, "terranova": 50},
        "recent_reward_trend": "stable",
        "cycle": 5,
    }

    # Run 10 decisions - ALL should be emergency_hoard
    decisions = [emergency_agent.decide(mock_obs) for _ in range(10)]
    all_emergency = all(d == "emergency_hoard" for d in decisions)
    print(f"  Decisions: {decisions[:5]}...")
    print(f"  All emergency_hoard? {PASS if all_emergency else FAIL}")
    print()

    # ===================================================================
    # TEST 3 - Weight Evolution Over 20 Cycles
    # ===================================================================
    print("=" * 60)
    print("  TEST 3 - Weight Evolution (20 trade_success cycles)")
    print("=" * 60)

    evo_agent = Agent("agrovia")
    initial_trade = evo_agent.strategy_weights["trade"]
    initial_aggress = evo_agent.strategy_weights["aggress"]

    for cycle in range(1, 21):
        # Simulate trade_success with moderate positive reward
        evo_agent.update_weights("trade", "trade_success", reward_score=0.3)
        evo_agent.cycles_survived = cycle

        if cycle % 5 == 0:
            print(f"  Cycle {cycle:2d}: {fmt_weights(evo_agent.strategy_weights)}  "
                  f"label={evo_agent.strategy_label}")

    trade_grew = evo_agent.strategy_weights["trade"] > initial_trade
    aggress_shrank = evo_agent.strategy_weights["aggress"] < initial_aggress
    is_trader = evo_agent.strategy_label == "Trader"

    print(f"  Trade weight grew?     {PASS if trade_grew else FAIL}")
    print(f"  Aggress weight shrank? {PASS if aggress_shrank else FAIL}")
    print(f"  Label is 'Trader'?     {PASS if is_trader else FAIL}")
    print()

    # ===================================================================
    # TEST 4 - Trust Dynamics
    # ===================================================================
    print("=" * 60)
    print("  TEST 4 - Trust Dynamics")
    print("=" * 60)

    trust_agent = Agent("urbanex")
    initial_agrovia_trust = trust_agent.trust_scores["agrovia"]

    # 3 successful trades with agrovia
    for _ in range(3):
        trust_agent.update_trust("trade_success", "agrovia")

    # 1 conflict win against petrozon (observer trust drops for all others)
    trust_agent.update_trust("conflict_win", "petrozon", all_regions=REGIONS)

    print(f"  Trust scores after events:")
    for rid, score in trust_agent.trust_scores.items():
        print(f"    {rid:12s}: {score}")

    agrovia_up = trust_agent.trust_scores["agrovia"] > initial_agrovia_trust
    # After conflict_win against petrozon, observer trust toward other regions dropped
    # Specifically, trust toward non-petrozon, non-self regions got TRUST_OBSERVER_CONFLICT
    # agrovia trust = 50 + 3*5 + (-10) = 55, terranova = 50 + (-10) = 40

    print(f"  Agrovia trust increased?  {PASS if agrovia_up else FAIL}")

    # Check that observer regions got penalized
    terranova_dropped = trust_agent.trust_scores["terranova"] < INITIAL_TRUST
    print(f"  Terranova trust dropped?  {PASS if terranova_dropped else FAIL}")
    print()

    # ===================================================================
    # TEST 5 - Strategy Differentiation Across 5 Agents
    # ===================================================================
    print("=" * 60)
    print("  TEST 5 - Strategy Differentiation (5 agents)")
    print("=" * 60)

    agents = {rid: Agent(rid) for rid in REGIONS}

    # Feed each agent a different outcome to force distinct strategies
    outcome_map = {
        "urbanex":   "aggress_success",
        "aquaria":   "trade_success",
        "petrozon":  "hoard_success",
        "agrovia":   "invest_payoff",
        "terranova": "emergency_hoard",
    }

    for cycle in range(10):
        for rid, ag in agents.items():
            outcome = outcome_map[rid]
            action = outcome.split("_")[0]
            ag.update_weights(action, outcome, reward_score=0.35)
            ag.cycles_survived = cycle + 1

    print(f"  {'Region':12s}  {'Label':10s}  Weights")
    print(f"  {'-' * 56}")

    labels_seen = set()
    for rid in REGIONS:
        ag = agents[rid]
        labels_seen.add(ag.strategy_label)
        print(f"  {rid:12s}  {ag.strategy_label:10s}  {fmt_weights(ag.strategy_weights)}")

    # At least 3 distinct labels should emerge
    distinct = len(labels_seen) >= 3
    print(f"\n  Distinct labels emerged: {len(labels_seen)} - "
          f"{PASS if distinct else FAIL}")
    print()

    print("=" * 60)
    print("  ALL TESTS COMPLETE")
    print("=" * 60)
