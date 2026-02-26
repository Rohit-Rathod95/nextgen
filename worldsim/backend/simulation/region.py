"""
region.py - Region Model for WorldSim

Each region tracks 4 resources (0-100 scale), population,
strategy weights, trust scores, and health. Serialises to a FLAT
dict via to_dict() that exactly matches Firestore + frontend expectations.

Region IDs are strictly lowercase.
"""

from config.regions_config import (
    CONSUMPTION_RATES, SPECIAL_ABILITIES,
    REGIONS, CRITICAL_THRESHOLD,
    EMERGENCY_THRESHOLD, COLLAPSE_THRESHOLD, COLLAPSE_POPULATION,
    SURPLUS_THRESHOLD, DEFICIT_THRESHOLD,
    THRIVING_THRESHOLD, STRESS_THRESHOLD, COLLAPSE_RESOURCE_THRESHOLD,
    POPULATION_GROWTH_RATE, POPULATION_DECLINE_RATE,
    POPULATION_COLLAPSE_RATE, POPULATION_MIN,
    INITIAL_TRUST, INITIAL_WEIGHT,
)


class Region:
    """
    Represents one of the 5 simulation regions.
    Tracks resources, population, strategy, trust, and health.
    """

    # -----------------------------------------------------------------------
    # __init__
    # -----------------------------------------------------------------------

    def __init__(self, region_id: str, water: float, food: float,
                 energy: float, land: float, population: float):
        self.region_id = region_id

        # Resources (0-100 scale)
        self.water  = float(water)
        self.food   = float(food)
        self.energy = float(energy)
        self.land   = float(land)

        # Population
        self.population          = float(population)
        self.starting_population = float(population)
        self.population_change       = 0.0
        self.population_change_ratio = 0.0

        # Health & status
        self.health_score  = 100.0
        self.is_collapsed  = False
        self.trade_open    = True

        # Per-cycle state
        self.cycle                  = 0
        self.climate_hits_this_cycle = 0  # reset at start of each cycle in world.py

        # Config-driven rates
        self.consumption_rates = CONSUMPTION_RATES[region_id]
        self.special_ability   = SPECIAL_ABILITIES.get(region_id, {})

        # Urbanex manufacturing economy (prevents resource-only collapse)
        if region_id == "urbanex":
            self.manufacturing_power = float(
                self.special_ability.get("initial_value", 85)
            )
        else:
            self.manufacturing_power = 0.0

        # Strategy learning
        self.strategy_weights = {
            "trade": INITIAL_WEIGHT, "hoard": INITIAL_WEIGHT,
            "invest": INITIAL_WEIGHT, "aggress": INITIAL_WEIGHT,
        }
        self.trust_scores = {r: INITIAL_TRUST for r in REGIONS if r != region_id}

        self.last_action    = "none"
        self.strategy_label = "Balanced"
        self.last_reward    = 0.0

        # Replay history
        self.history        = []
        self.land_multiplier = 1.0

    # -----------------------------------------------------------------------
    # METHOD: consume
    # -----------------------------------------------------------------------

    def consume(self):
        """
        Deplete resources based on per-region rates and current population.
        Population adjustment REMOVED — update_population() owns all pop dynamics.
        """
        drain_multiplier = self.population / 1000.0
        depleted = 0

        for resource in ["water", "food", "energy", "land"]:
            rate   = self.consumption_rates[resource]
            drain  = rate * drain_multiplier
            before = getattr(self, resource)
            after  = before - drain

            if after <= 0:
                depleted += 1
                setattr(self, resource, 0.0)
            else:
                setattr(self, resource, after)

        # Soft population penalty ONLY when resources are completely depleted
        # (depletion = resource hit zero this cycle, not just low)
        if depleted >= 2:
            self.population = max(POPULATION_MIN, self.population * 0.97)
        elif depleted == 1:
            self.population = max(POPULATION_MIN, self.population * 0.99)

    # -----------------------------------------------------------------------
    # METHOD: update_population
    # -----------------------------------------------------------------------

    def update_population(self):
        """
        Dynamic population based on avg resource level.
        Called AFTER consume() + apply_special_ability() each cycle.

        Thriving  (avg > 60): +2%/cycle
        Stable    (30-60):     0%
        Stressed  (15-30):    -3%/cycle
        Collapsing (< 15):   -10%/cycle
        """
        avg = (self.water + self.food + self.energy + self.land) / 4.0

        if avg > THRIVING_THRESHOLD:
            rate = POPULATION_GROWTH_RATE
        elif avg > STRESS_THRESHOLD:
            rate = 0.0
        elif avg > COLLAPSE_RESOURCE_THRESHOLD:
            rate = -POPULATION_DECLINE_RATE
        else:
            rate = -POPULATION_COLLAPSE_RATE

        old_pop = self.population
        max_pop = self.starting_population * 3.0
        self.population = max(
            float(POPULATION_MIN),
            min(self.population * (1.0 + rate), max_pop)
        )
        self.population = round(self.population)

        self.population_change = self.population - old_pop
        self.population_change_ratio = (
            self.population_change / old_pop if old_pop > 0 else 0.0
        )

    # -----------------------------------------------------------------------
    # METHOD: apply_special_ability
    # -----------------------------------------------------------------------

    def apply_special_ability(self):
        """
        Apply this region's unique passive ability once per cycle.
        Called AFTER consume() so regen offsets consumption naturally.

        aquaria   -> +3.0 water/cycle  (Amazon basin)
        agrovia   -> +3.0 food/cycle   (monsoon, land > 25)
        petrozon  -> +2.5 energy/cycle (oil extraction)
        urbanex   -> +1.0 mfg_power/cycle (manufacturing regen)
        terranova -> +land if invest action (land development)
        """
        ability = self.special_ability.get("ability")

        if ability == "water_regeneration":
            regen = self.special_ability.get("regen_rate", 3.0)
            self.water = min(100.0, self.water + regen)

        elif ability == "food_regeneration":
            threshold = self.special_ability.get("land_threshold", 25)
            if self.land > threshold:
                regen = self.special_ability.get("regen_rate", 3.0)
                self.food = min(100.0, self.food + regen)

        elif ability == "energy_regeneration":
            regen = self.special_ability.get("regen_rate", 2.5)
            self.energy = min(100.0, self.energy + regen)

        elif ability == "manufacturing_power":
            # Manufacturing capacity slowly rebuilds each cycle
            regen = self.special_ability.get("regen_rate", 1.0)
            self.manufacturing_power = min(
                100.0, self.manufacturing_power + regen
            )

        elif ability == "land_development":
            # Land improves when investing — multiplied return
            if self.last_action == "invest":
                multiplier  = self.special_ability.get("invest_multiplier", 2.0)
                improvement = 1.0 * multiplier
                self.land   = min(100.0, self.land + improvement)
            else:
                # Passive land improvement from general development
                passive = self.special_ability.get("regen_rate", 1.5) * 0.3
                self.land = min(100.0, self.land + passive)

    # -----------------------------------------------------------------------
    # METHOD: apply_climate
    # -----------------------------------------------------------------------

    def apply_climate(self, event_type: str) -> str:
        """Apply a climate event. Tracks hits for analysis reporting."""
        self.climate_hits_this_cycle += 1

        if event_type == "drought":
            self.water = max(0.0, self.water - self.water * 0.40)
        elif event_type == "flood":
            self.food  = max(0.0, self.food  - self.food  * 0.30)
        elif event_type == "energy_crisis":
            self.energy = max(0.0, self.energy - self.energy * 0.35)
        elif event_type == "fertile_season":
            self.food = min(100.0, self.food + self.food * 0.20)
        elif event_type == "solar_surge":
            self.energy = min(100.0, self.energy + self.energy * 0.25)

        return event_type

    # -----------------------------------------------------------------------
    # METHOD: calculate_health
    # -----------------------------------------------------------------------

    def calculate_health(self) -> float:
        """
        Compute health score (0-100).

        Formula:
            avg_resource * 0.7  +  pop_factor  +  trade_bonus
            + manufacturing_bonus (Urbanex only)

        Urbanex collapse guard: never collapses if manufacturing_power > 25.
        Standard collapse: health <= COLLAPSE_THRESHOLD AND population <= COLLAPSE_POPULATION.
        """
        avg = (self.water + self.food + self.energy + self.land) / 4.0

        # Population factor: growth bonus when resources OK, penalty under stress
        if avg > STRESS_THRESHOLD:
            pop_factor = min(
                self.population / self.starting_population, 2.0
            ) * 10.0
        else:
            pop_factor = max(
                0.0,
                10.0 - (self.population / self.starting_population * 5.0)
            )

        # Urbanex manufacturing bonus: up to +15 health from mfg power
        manufacturing_bonus = 0.0
        if self.region_id == "urbanex":
            manufacturing_bonus = (self.manufacturing_power / 100.0) * 15.0

        trade_bonus = 5.0 if self.trade_open else 0.0

        health = avg * 0.7 + pop_factor + trade_bonus + manufacturing_bonus
        self.health_score = round(min(100.0, max(0.0, health)), 2)

        # Collapse detection — Urbanex protected by manufacturing_power
        if self.health_score <= COLLAPSE_THRESHOLD:
            if self.population <= COLLAPSE_POPULATION:
                if not (self.region_id == "urbanex" and
                        self.manufacturing_power > 25):
                    self.is_collapsed = True

        return self.health_score

    # -----------------------------------------------------------------------
    # METHOD: log_history
    # -----------------------------------------------------------------------

    def log_history(self):
        """Append snapshot to history. Cap at 100 entries."""
        if len(self.history) >= 100:
            self.history.pop(0)

        self.history.append({
            "cycle":               self.cycle,
            "water":               round(self.water, 2),
            "food":                round(self.food, 2),
            "energy":              round(self.energy, 2),
            "land":                round(self.land, 2),
            "population":          round(self.population),
            "health_score":        self.health_score,
            "last_action":         self.last_action,
            "strategy_label":      self.strategy_label,
            "manufacturing_power": round(self.manufacturing_power, 2),
            "population_change":   self.population_change,
        })

    # -----------------------------------------------------------------------
    # METHOD: to_dict
    # -----------------------------------------------------------------------

    def to_dict(self) -> dict:
        """
        Return FLAT dictionary for Firestore persistence.
        All field names match frontend firestore_listener.js exactly.
        """
        return {
            "region_id":              self.region_id,
            "water":                  round(self.water, 2),
            "food":                   round(self.food, 2),
            "energy":                 round(self.energy, 2),
            "land":                   round(self.land, 2),
            "population":             round(self.population),
            "starting_population":    round(self.starting_population),
            "health_score":           self.health_score,
            "is_collapsed":           self.is_collapsed,
            "trade_open":             self.trade_open,
            "last_action":            self.last_action,
            "strategy_label":         self.strategy_label,
            "last_reward":            round(self.last_reward, 4),
            "manufacturing_power":    round(self.manufacturing_power, 2),
            "cycle":                  self.cycle,
            "population_change":      round(self.population_change, 2),
            "population_change_ratio": round(self.population_change_ratio, 4),
            # Flat strategy weights
            "trade_weight":   round(self.strategy_weights["trade"],   4),
            "hoard_weight":   round(self.strategy_weights["hoard"],   4),
            "invest_weight":  round(self.strategy_weights["invest"],  4),
            "aggress_weight": round(self.strategy_weights["aggress"], 4),
            # Flat trust scores
            "trust_aquaria":   self.trust_scores.get("aquaria",   INITIAL_TRUST),
            "trust_agrovia":   self.trust_scores.get("agrovia",   INITIAL_TRUST),
            "trust_petrozon":  self.trust_scores.get("petrozon",  INITIAL_TRUST),
            "trust_urbanex":   self.trust_scores.get("urbanex",   INITIAL_TRUST),
            "trust_terranova": self.trust_scores.get("terranova", INITIAL_TRUST),
            # Climate tracking — read by analysis_service.generate_simulation_summary
            "climate_hits":           self.climate_hits_this_cycle,
        }

    # -----------------------------------------------------------------------
    # METHOD: get_resource_status
    # -----------------------------------------------------------------------

    def get_resource_status(self) -> dict:
        """Return resource status buckets for agent observation."""
        return {
            "critical":  [r for r in RESOURCES if getattr(self, r) < CRITICAL_THRESHOLD],
            "emergency": [r for r in RESOURCES if getattr(self, r) < EMERGENCY_THRESHOLD],
            "surplus":   [r for r in RESOURCES if getattr(self, r) > SURPLUS_THRESHOLD],
            "deficit":   [r for r in RESOURCES if getattr(self, r) < DEFICIT_THRESHOLD],
        }

    # -----------------------------------------------------------------------
    # METHOD: reset
    # -----------------------------------------------------------------------

    def reset(self, initial_data: dict):
        """Reset region to initial values for a new simulation run."""
        self.water  = float(initial_data["water"])
        self.food   = float(initial_data["food"])
        self.energy = float(initial_data["energy"])
        self.land   = float(initial_data["land"])
        self.population          = float(initial_data["population"])
        self.starting_population = float(initial_data["population"])

        self.health_score  = 100.0
        self.is_collapsed  = False
        self.trade_open    = True
        self.cycle         = 0
        self.climate_hits_this_cycle = 0

        self.strategy_weights = {
            "trade": INITIAL_WEIGHT, "hoard": INITIAL_WEIGHT,
            "invest": INITIAL_WEIGHT, "aggress": INITIAL_WEIGHT,
        }
        self.trust_scores = {r: INITIAL_TRUST for r in REGIONS if r != self.region_id}

        self.last_action    = "none"
        self.strategy_label = "Balanced"
        self.last_reward    = 0.0
        self.population_change       = 0.0
        self.population_change_ratio = 0.0
        self.history                 = []

        if self.region_id == "urbanex":
            self.manufacturing_power = float(
                self.special_ability.get("initial_value", 85)
            )
        else:
            self.manufacturing_power = 0.0


# ---------------------------------------------------------------------------
# Module-level RESOURCES reference (imported by trade.py, conflict.py)
# ---------------------------------------------------------------------------

RESOURCES = ["water", "food", "energy", "land"]


# ===========================================================================
# Test Cases
# ===========================================================================

if __name__ == "__main__":
    PASS = "[PASS]"
    FAIL = "[FAIL]"

    print("=" * 60)
    print("  TEST 1 — Urbanex Manufacturing Collapse Guard")
    print("=" * 60)
    ux = Region("urbanex", water=5, food=5, energy=5, land=5, population=80)
    ux.manufacturing_power = 50  # high mfg
    ux.calculate_health()
    print(f"  Health: {ux.health_score}  Collapsed: {ux.is_collapsed}")
    print(f"  Not collapsed due to mfg? {PASS if not ux.is_collapsed else FAIL}")
    print()

    print("=" * 60)
    print("  TEST 2 — Aquaria Water Regeneration")
    print("=" * 60)
    aq = Region("aquaria", water=50, food=50, energy=50, land=50, population=500)
    for _ in range(5):
        aq.consume()
        aq.apply_special_ability()
    print(f"  Water after 5 cycles regen: {aq.water:.1f} (started 50, drain ~0.6/c, regen 3.0)")
    grew = aq.water > 50
    print(f"  Water net positive? {PASS if grew else FAIL}")
    print()

    print("=" * 60)
    print("  TEST 3 — Population Growth (Aquaria avg > 60)")
    print("=" * 60)
    aq2 = Region("aquaria", water=80, food=80, energy=80, land=80, population=500)
    for i in range(1, 6):
        aq2.update_population()
    grew = aq2.population > 500
    print(f"  Population: {aq2.population}  Grew? {PASS if grew else FAIL}")
    print()

    print("=" * 60)
    print("  TEST 4 — to_dict() contains climate_hits field")
    print("=" * 60)
    r = Region("petrozon", water=30, food=30, energy=85, land=50, population=450)
    r.apply_climate("drought")
    d = r.to_dict()
    has_hits  = "climate_hits" in d
    hits_val  = d.get("climate_hits", -1)
    print(f"  climate_hits present? {PASS if has_hits else FAIL}  value={hits_val}")
    print(f"  climate_hits == 1?    {PASS if hits_val == 1 else FAIL}")
    print()

    print("=" * 60)
    print("  All Region tests complete")
    print("=" * 60)
