"""
region.py — Region Model for WorldSim

Defines each region's resource state, population, strategy weights,
trust scores, and per-cycle behaviors (consumption, climate, health).

Every region serializes to a FLAT dictionary via to_dict() matching
exactly what the frontend expects — no nested objects for weights
or trust scores.

All region IDs are strictly lowercase.
"""

from config.regions_config import (
    REGIONS, RESOURCES, CRITICAL_THRESHOLD,
    EMERGENCY_THRESHOLD, COLLAPSE_THRESHOLD,
    CONSUMPTION_RATES, INITIAL_TRUST, INITIAL_WEIGHT,
    SPECIAL_ABILITIES,
)

# ---------------------------------------------------------------------------
# Population dynamics constants
# ---------------------------------------------------------------------------

POPULATION_GROWTH_RATE = 0.02       # 2% per cycle when thriving
POPULATION_STABLE_RATE = 0.00       # 0% when moderate
POPULATION_DECLINE_RATE = 0.03      # 3% per cycle under stress
POPULATION_COLLAPSE_RATE = 0.10     # 10% per cycle near collapse
POPULATION_MIN = 10                 # absolute minimum — allows collapse scenarios
POPULATION_MAX_MULTIPLIER = 3.0     # max 3x starting population

THRIVING_THRESHOLD = 50             # avg resources above this -> grow (was 60, too high)
STRESS_THRESHOLD = 25               # avg resources below this -> decline (was 30)
COLLAPSE_RESOURCE_THRESHOLD = 10    # avg resources below this -> collapse rate (was 15)


# ===========================================================================
# Region Class
# ===========================================================================

class Region:
    """
    Represents a single region in the WorldSim simulation.

    Tracks 4 resources (water, food, energy, land), population,
    strategy weights, trust scores toward other regions, and
    health status. Provides serialization to flat dict for Firestore.
    """

    def __init__(self, region_id: str, water: float, food: float,
                 energy: float, land: float, population: float):
        """
        Initialize a region with starting resource values.

        Args:
            region_id:  Lowercase region identifier (e.g. "aquaria").
            water:      Starting water level (0–100 scale).
            food:       Starting food level (0–100 scale).
            energy:     Starting energy level (0–100 scale).
            land:       Starting land level (0–100 scale).
            population: Starting population count.
        """
        self.region_id = region_id

        # Resources (0–100 scale)
        self.water = float(water)
        self.food = float(food)
        self.energy = float(energy)
        self.land = float(land)

        # Population
        self.population = float(population)
        self.starting_population = float(population)  # locked at init for max-cap calc
        self.population_change = 0
        self.population_change_ratio = 0.0

        # Health
        self.health_score = 100.0

        # Per-region consumption rates from config
        self.consumption_rates = CONSUMPTION_RATES[region_id]

        # History for replay
        self.history = []

        # Current cycle counter
        self.cycle = 0

        # Strategy weights — stored ON the region for Firestore
        self.strategy_weights = {
            "trade": INITIAL_WEIGHT,
            "hoard": INITIAL_WEIGHT,
            "invest": INITIAL_WEIGHT,
            "aggress": INITIAL_WEIGHT,
        }

        # Trust scores toward every OTHER region (0-100 scale)
        self.trust_scores = {
            r: INITIAL_TRUST for r in REGIONS if r != region_id
        }

        # Action tracking
        self.last_action = "none"
        self.strategy_label = "Balanced"
        self.last_reward = 0.0

        # Status flags
        self.is_collapsed = False
        self.trade_open = True

        # Special ability — unique per-region passive/active edge
        self.special_ability = SPECIAL_ABILITIES.get(region_id, {})

        # Urbanex manufacturing capacity (China's manufacturing economy leverage)
        if region_id == "urbanex":
            self.manufacturing_power = float(
                self.special_ability.get("initial_value", 85)
            )
        else:
            self.manufacturing_power = 0.0

    # -----------------------------------------------------------------------
    # METHOD 0a - Apply Special Ability (call once per cycle, after consume)
    # -----------------------------------------------------------------------

    def apply_special_ability(self):
        """
        Apply this region's unique special ability once per cycle.
        Called AFTER consume() so regen offsets consumption naturally.

        - water_regeneration  (Aquaria):  +2.0 water/cycle — Amazon river
        - food_regeneration   (Agrovia):  +3.0 food/cycle if land > 30 — monsoon
        - energy_regeneration (Petrozon): +1.5 energy/cycle — oil extraction
        - manufacturing_power (Urbanex):  handled in trade.py — no passive regen
        - land_development    (Terranova): handled in agent invest logic
        """
        ability = self.special_ability.get("ability")

        if ability == "water_regeneration":
            # Amazon basin: water cycle replenishes reserves naturally
            regen = self.special_ability.get("regen_rate", 2.0)
            self.water = min(100.0, self.water + regen)

        elif ability == "food_regeneration":
            # Monsoon agriculture: requires cultivated land to function
            land_threshold = self.special_ability.get("land_threshold", 30)
            if self.land > land_threshold:
                regen = self.special_ability.get("regen_rate", 3.0)
                self.food = min(100.0, self.food + regen)

        elif ability == "energy_regeneration":
            # Oil reserve: passive extraction replenishes energy baseline
            regen = self.special_ability.get("regen_rate", 1.5)
            self.energy = min(100.0, self.energy + regen)

        elif ability == "manufacturing_power":
            # Manufacturing leverage handled per-trade in trade.py
            pass

        elif ability == "land_development":
            # Investment multiplier applied during agent invest decisions
            pass

    # -----------------------------------------------------------------------
    # METHOD 0b - Update Population (call AFTER consume, BEFORE calculate_health)
    # -----------------------------------------------------------------------

    def update_population(self):
        """
        Update population based on average resource level.
        Called once per cycle after consume() completes.

        Logic:
        - Thriving  (avg > 60): grow 2% per cycle
        - Stable    (avg 30-60): no change
        - Stressed  (avg 15-30): decline 3% per cycle
        - Collapsing (avg < 15): decline 10% per cycle

        Population is clamped between POPULATION_MIN
        and starting_population * POPULATION_MAX_MULTIPLIER.
        """
        avg_resources = (
            self.water + self.food +
            self.energy + self.land
        ) / 4

        if avg_resources > THRIVING_THRESHOLD:
            growth_rate = POPULATION_GROWTH_RATE
        elif avg_resources > STRESS_THRESHOLD:
            growth_rate = POPULATION_STABLE_RATE
        elif avg_resources > COLLAPSE_RESOURCE_THRESHOLD:
            growth_rate = -POPULATION_DECLINE_RATE
        else:
            growth_rate = -POPULATION_COLLAPSE_RATE

        old_population = self.population
        self.population = self.population * (1 + growth_rate)

        # Clamp population between min and max
        max_population = self.starting_population * POPULATION_MAX_MULTIPLIER
        self.population = max(
            float(POPULATION_MIN),
            min(self.population, max_population)
        )

        # Round to whole number
        self.population = round(self.population)

        # Track population change for reward calculation
        self.population_change = self.population - old_population
        self.population_change_ratio = (
            self.population_change / old_population
            if old_population > 0 else 0
        )

    # -----------------------------------------------------------------------
    # METHOD 1 — Consume Resources
    # -----------------------------------------------------------------------

    def consume(self):
        """
        Deplete resources based on per-region consumption rates
        and current population. Larger populations drain faster.

        Population decreases if resources are fully depleted:
            - 2+ resources hit 0 → population × 0.95
            - 1 resource hits 0  → population × 0.98
            - Minimum population is always 10
        """
        # Dynamic population drives drain: bigger population = more consumption.
        # update_population() (called next) owns all pop growth/decline logic.
        drain_multiplier = self.population / 1000.0
        depleted_count = 0

        for resource in RESOURCES:
            rate = self.consumption_rates.get(resource, 0.5)
            drain = rate * drain_multiplier
            current = getattr(self, resource)

            # Check if this drain will fully deplete the resource
            new_value = current - drain
            if new_value <= 0 and current > 0:
                depleted_count += 1

            # Apply drain and clamp immediately (per resource)
            setattr(self, resource, max(0.0, new_value))

        # NOTE: population adjustment REMOVED from here.
        # update_population() runs next in world.py and owns all pop dynamics.
        # Keeping the old depletion-based pop adjustment here caused double-counting.

    # -----------------------------------------------------------------------
    # METHOD 2 — Apply Climate Event
    # -----------------------------------------------------------------------

    def apply_climate(self, event_type: str) -> str:
        """
        Apply a climate event that reduces a specific resource.

        Supported events:
            "drought"        → water  -= 30% of current
            "flood"          → food   -= 20% of current
            "energy_crisis"  → energy -= 25% of current

        Args:
            event_type: One of "drought", "flood", "energy_crisis".

        Returns:
            The event_type string for logging.
        """
        if event_type == "drought":
            self.water -= self.water * 0.30
        elif event_type == "flood":
            self.food -= self.food * 0.20
        elif event_type == "energy_crisis":
            self.energy -= self.energy * 0.25

        # Clamp all resources to minimum 0
        self.water = max(0.0, self.water)
        self.food = max(0.0, self.food)
        self.energy = max(0.0, self.energy)
        self.land = max(0.0, self.land)

        return event_type

    # -----------------------------------------------------------------------
    # METHOD 3 — Calculate Health Score
    # -----------------------------------------------------------------------

    def calculate_health(self) -> float:
        """
        Compute region health score (0–100) from resources,
        population, and trade status.

        Formula:
            avg_resource = (water + food + energy + land) / 4
            pop_factor   = min(population / 1000, 2.0) × 10
            trade_bonus  = 5 if trade_open else 0
            health       = avg_resource × 0.7 + pop_factor + trade_bonus

        Triggers collapse if health drops to or below COLLAPSE_THRESHOLD.

        Returns:
            Updated health_score.
        """
        avg_resource = (self.water + self.food + self.energy + self.land) / 4.0
        trade_bonus = 5.0 if self.trade_open else 0.0

        # Population pressure: reward stable/declining pop during resource stress,
        # reward growth when resources are plentiful.
        if avg_resource > STRESS_THRESHOLD:
            # Resources OK — population growth is good
            pop_factor = min(
                self.population / self.starting_population,
                2.0
            ) * 10.0
        else:
            # Resources stressed — large population is a burden
            pop_factor = max(
                0.0,
                10.0 - ((self.population / self.starting_population) * 5.0)
            )

        health = (avg_resource * 0.7) + pop_factor + trade_bonus
        health = min(100.0, max(0.0, health))

        self.health_score = round(health, 2)

        # Collapse detection
        if self.health_score <= COLLAPSE_THRESHOLD:
            self.is_collapsed = True

        return self.health_score

    # -----------------------------------------------------------------------
    # METHOD 4 — Serialize to Flat Dictionary
    # -----------------------------------------------------------------------

    def to_dict(self) -> dict:
        """
        Return a complete FLAT dictionary for Firestore persistence.

        Strategy weights are written as individual flat fields
        (trade_weight, hoard_weight, etc.) — NOT as a nested dict.

        Trust scores are written as individual flat fields
        (trust_aquaria, trust_agrovia, etc.) — NOT as a nested dict.

        This matches exactly what the frontend expects.

        Returns:
            Flat dictionary with all region fields.
        """
        return {
            "region_id": self.region_id,
            "water": round(self.water, 2),
            "food": round(self.food, 2),
            "energy": round(self.energy, 2),
            "land": round(self.land, 2),
            "population": round(self.population, 0),
            "population_change": self.population_change,
            "population_change_ratio": round(self.population_change_ratio, 4),
            "starting_population": self.starting_population,
            "manufacturing_power": round(self.manufacturing_power, 1),
            "health_score": self.health_score,
            "is_collapsed": self.is_collapsed,
            "trade_open": self.trade_open,
            "last_action": self.last_action,
            "strategy_label": self.strategy_label,
            "last_reward": self.last_reward,
            "cycle": self.cycle,
            # Flat strategy weights
            "trade_weight": self.strategy_weights["trade"],
            "hoard_weight": self.strategy_weights["hoard"],
            "invest_weight": self.strategy_weights["invest"],
            "aggress_weight": self.strategy_weights["aggress"],
            # Flat trust scores
            "trust_aquaria": self.trust_scores.get("aquaria", 50),
            "trust_agrovia": self.trust_scores.get("agrovia", 50),
            "trust_petrozon": self.trust_scores.get("petrozon", 50),
            "trust_urbanex": self.trust_scores.get("urbanex", 50),
            "trust_terranova": self.trust_scores.get("terranova", 50),
        }

    # -----------------------------------------------------------------------
    # METHOD 5 — Log History
    # -----------------------------------------------------------------------

    def log_history(self):
        """
        Append a snapshot of the current state to the history list.
        Called once per cycle after all updates complete.

        Maximum 100 entries — oldest removed if exceeded.
        """
        self.history.append({
            "cycle": self.cycle,
            "water": round(self.water, 2),
            "food": round(self.food, 2),
            "energy": round(self.energy, 2),
            "land": round(self.land, 2),
            "population": round(self.population, 0),
            "population_change": self.population_change,
            "health_score": self.health_score,
            "last_action": self.last_action,
            "strategy_label": self.strategy_label,
        })

        # Cap at 100 entries
        if len(self.history) > 100:
            self.history = self.history[-100:]

    # -----------------------------------------------------------------------
    # METHOD 6 — Resource Status (for Agent Observation)
    # -----------------------------------------------------------------------

    def get_resource_status(self) -> dict:
        """
        Return a quick status dict for agent observation.

        Returns:
            Dictionary with lists of resource names by status:
                critical  — below CRITICAL_THRESHOLD (30)
                emergency — below EMERGENCY_THRESHOLD (20)
                surplus   — above 70
                deficit   — below 40
        """
        status = {
            "critical": [],
            "emergency": [],
            "surplus": [],
            "deficit": [],
        }

        for resource in RESOURCES:
            level = getattr(self, resource, 0)

            if level < EMERGENCY_THRESHOLD:
                status["emergency"].append(resource)
            if level < CRITICAL_THRESHOLD:
                status["critical"].append(resource)
            if level > 70:
                status["surplus"].append(resource)
            if level < 40:
                status["deficit"].append(resource)

        return status

    # -----------------------------------------------------------------------
    # METHOD 7 — Reset to Initial Values
    # -----------------------------------------------------------------------

    def reset(self, initial_data: dict):
        """
        Reset region to initial starting values for a new simulation run.
        initial_data comes from regions_config.INITIAL_REGIONS[region_id].

        Resets all resources, population, health, history, weights, trust.
        Does NOT change region_id.

        Args:
            initial_data: Dictionary with water, food, energy, land, population.
        """
        self.water = float(initial_data["water"])
        self.food = float(initial_data["food"])
        self.energy = float(initial_data["energy"])
        self.land = float(initial_data["land"])
        self.population = float(initial_data["population"])
        self.starting_population = float(initial_data["population"])
        self.population_change = 0
        self.population_change_ratio = 0.0

        self.health_score = 100.0
        self.history = []
        self.cycle = 0

        self.strategy_weights = {
            "trade": INITIAL_WEIGHT,
            "hoard": INITIAL_WEIGHT,
            "invest": INITIAL_WEIGHT,
            "aggress": INITIAL_WEIGHT,
        }

        self.trust_scores = {
            r: INITIAL_TRUST for r in REGIONS if r != self.region_id
        }

        self.last_action = "none"
        self.strategy_label = "Balanced"
        self.last_reward = 0.0
        self.is_collapsed = False
        self.trade_open = True

        # Reset special ability state
        self.special_ability = SPECIAL_ABILITIES.get(self.region_id, {})
        if self.region_id == "urbanex":
            self.manufacturing_power = float(
                self.special_ability.get("initial_value", 85)
            )
        else:
            self.manufacturing_power = 0.0


# ===========================================================================
# Test Cases
# ===========================================================================

if __name__ == "__main__":

    PASS = "[PASS]"
    FAIL = "[FAIL]"

    # ===================================================================
    # TEST 1 — Consumption Over 5 Cycles
    # ===================================================================
    print("=" * 60)
    print("  TEST 1 - Consumption Over 5 Cycles (Aquaria)")
    print("=" * 60)

    r = Region("aquaria", water=90, food=60, energy=30, land=70, population=500)
    print(f"  Initial: W={r.water:.1f} F={r.food:.1f} E={r.energy:.1f} L={r.land:.1f} P={r.population:.0f}")

    for i in range(1, 6):
        r.consume()
        print(f"  Cycle {i}: W={r.water:.1f} F={r.food:.1f} E={r.energy:.1f} L={r.land:.1f} P={r.population:.0f}")

    # Water should deplete fastest (rate 0.8 vs others)
    water_drop = 90 - r.water
    food_drop = 60 - r.food
    result = PASS if water_drop > food_drop else FAIL
    print(f"  Water depleted fastest? {result} (W dropped {water_drop:.1f} vs F dropped {food_drop:.1f})")
    print()

    # ===================================================================
    # TEST 2 — Climate Events
    # ===================================================================
    print("=" * 60)
    print("  TEST 2 - Climate Events")
    print("=" * 60)

    r2 = Region("petrozon", water=30, food=35, energy=95, land=60, population=450)

    # Drought
    before_w = r2.water
    r2.apply_climate("drought")
    print(f"  Drought: water {before_w:.1f} -> {r2.water:.1f} (lost {before_w - r2.water:.1f})")

    # Flood
    before_f = r2.food
    r2.apply_climate("flood")
    print(f"  Flood: food {before_f:.1f} -> {r2.food:.1f} (lost {before_f - r2.food:.1f})")

    # Energy crisis (NOT blizzard)
    before_e = r2.energy
    r2.apply_climate("energy_crisis")
    print(f"  Energy crisis: energy {before_e:.1f} -> {r2.energy:.1f} (lost {before_e - r2.energy:.1f})")

    # Confirm blizzard does nothing
    before_all = (r2.water, r2.food, r2.energy, r2.land)
    r2.apply_climate("blizzard")
    after_all = (r2.water, r2.food, r2.energy, r2.land)
    blizzard_noop = before_all == after_all
    print(f"  'blizzard' is no-op? {PASS if blizzard_noop else FAIL}")
    print()

    # ===================================================================
    # TEST 3 — to_dict() Flat Structure
    # ===================================================================
    print("=" * 60)
    print("  TEST 3 - to_dict() Flat Structure (Petrozon)")
    print("=" * 60)

    r3 = Region("petrozon", water=30, food=35, energy=95, land=60, population=450)
    d = r3.to_dict()

    # Check all required keys exist
    required_keys = [
        "region_id", "water", "food", "energy", "land", "population",
        "health_score", "is_collapsed", "trade_open", "last_action",
        "strategy_label", "last_reward", "cycle",
        "trade_weight", "hoard_weight", "invest_weight", "aggress_weight",
        "trust_aquaria", "trust_agrovia", "trust_urbanex", "trust_terranova",
    ]

    missing = [k for k in required_keys if k not in d]
    print(f"  Keys present: {len(d)}")
    print(f"  Missing keys: {missing if missing else 'None'}")
    print(f"  All required keys? {PASS if not missing else FAIL}")

    # Confirm flat (no nested dicts)
    nested = [k for k, v in d.items() if isinstance(v, dict)]
    print(f"  Nested dicts found: {nested if nested else 'None'}")
    print(f"  Flat structure? {PASS if not nested else FAIL}")

    # Print full dict
    for k, v in d.items():
        print(f"    {k}: {v}")
    print()

    # ===================================================================
    # TEST 4 — Collapse Detection
    # ===================================================================
    print("=" * 60)
    print("  TEST 4 - Collapse Detection")
    print("=" * 60)

    r4 = Region("urbanex", water=40, food=45, energy=40, land=30, population=950)
    r4.water = 5
    r4.food = 5
    r4.energy = 5
    r4.land = 5
    r4.population = 50

    health = r4.calculate_health()
    print(f"  Health after setting all resources to 5: {health}")
    print(f"  is_collapsed? {PASS if r4.is_collapsed else FAIL}")
    print()

    # ===================================================================
    # TEST 5 — History Logging
    # ===================================================================
    print("=" * 60)
    print("  TEST 5 - History Logging (5 cycles)")
    print("=" * 60)

    r5 = Region("terranova", water=55, food=60, energy=55, land=90, population=400)

    for cycle in range(1, 6):
        r5.cycle = cycle
        r5.consume()
        r5.calculate_health()
        r5.log_history()

    print(f"  History entries: {len(r5.history)}")
    print(f"  5 entries? {PASS if len(r5.history) == 5 else FAIL}")

    for entry in r5.history:
        print(f"    Cycle {entry['cycle']}: W={entry['water']:.1f} F={entry['food']:.1f} "
              f"E={entry['energy']:.1f} HP={entry['health_score']}")
    print()

    # ===================================================================
    # TEST 6 — Thriving region grows (NEW population dynamics)
    # ===================================================================
    print("=" * 60)
    print("  TEST 6 - Thriving Region Grows (Aquaria, all resources=80)")
    print("=" * 60)

    r6 = Region("aquaria", water=80, food=80, energy=80, land=80, population=500)
    print(f"  Start: population={r6.population}")
    for i in range(1, 11):
        r6.update_population()
        print(f"  Cycle {i:2d}: population={r6.population}  change={r6.population_change:+.0f}")
    grew = r6.population > 500
    print(f"  Population grew? {PASS if grew else FAIL}")
    print()

    # ===================================================================
    # TEST 7 — Stressed region declines
    # ===================================================================
    print("=" * 60)
    print("  TEST 7 - Stressed Region Declines (Urbanex, all resources=25)")
    print("=" * 60)

    r7 = Region("urbanex", water=25, food=25, energy=25, land=25, population=950)
    print(f"  Start: population={r7.population}")
    for i in range(1, 11):
        r7.update_population()
        print(f"  Cycle {i:2d}: population={r7.population}  change={r7.population_change:+.0f}")
    declined = r7.population < 950
    print(f"  Population declined? {PASS if declined else FAIL}")
    print()

    # ===================================================================
    # TEST 8 — Collapsing region rapid decline
    # ===================================================================
    print("=" * 60)
    print("  TEST 8 - Collapsing Region (all resources=10)")
    print("=" * 60)

    r8 = Region("petrozon", water=10, food=10, energy=10, land=10, population=450)
    print(f"  Start: population={r8.population}")
    for i in range(1, 6):
        r8.update_population()
        print(f"  Cycle {i}: population={r8.population}  change={r8.population_change:+.0f}")
    rapid = r8.population < 400
    print(f"  Rapid decline? {PASS if rapid else FAIL}")
    print()

    # ===================================================================
    # TEST 9 — Population cap enforced
    # ===================================================================
    print("=" * 60)
    print("  TEST 9 - Population Cap (Terranova start=400, max=1200)")
    print("=" * 60)

    r9 = Region("terranova", water=90, food=90, energy=90, land=90, population=400)
    for _ in range(50):
        r9.update_population()
    cap = 400 * POPULATION_MAX_MULTIPLIER
    capped = r9.population <= cap
    print(f"  After 50 cycles: population={r9.population}  cap={cap:.0f}")
    print(f"  Cap enforced? {PASS if capped else FAIL}")
    print()

    # ===================================================================
    # TEST 10 — to_dict() includes new population fields
    # ===================================================================
    print("=" * 60)
    print("  TEST 10 - to_dict() New Population Fields")
    print("=" * 60)

    r10 = Region("aquaria", water=80, food=80, energy=80, land=80, population=500)
    r10.update_population()
    d10 = r10.to_dict()
    has_change = "population_change" in d10
    has_ratio = "population_change_ratio" in d10
    has_start = "starting_population" in d10
    print(f"  population_change present?       {PASS if has_change else FAIL}  => {d10.get('population_change')}")
    print(f"  population_change_ratio present? {PASS if has_ratio else FAIL}  => {d10.get('population_change_ratio')}")
    print(f"  starting_population present?     {PASS if has_start else FAIL}  => {d10.get('starting_population')}")
    print()

    # ===================================================================
    print("=" * 60)
    print("  All Region tests complete")
    print("=" * 60)
