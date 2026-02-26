"""
world.py — World Simulation Orchestrator for WorldSim

Manages all 5 regions, their agents, and the per-cycle simulation
loop. Each cycle executes phases in strict order:

    1. Climate Events
    2. Consumption
    3. Agent Decisions
    4. Trade Phase
    5. Conflict Phase
    6. Reward Calculation
    7. Weight Adaptation
    8. Health Recalculation
    9. History Logging
   10. Firestore Persistence

Runs for TOTAL_CYCLES (100) or until manually paused.
"""

import asyncio
import logging
import time

from config.regions_config import (
    REGIONS, INITIAL_REGIONS, TOTAL_CYCLES, CYCLE_SPEED,
)
from simulation.region import Region
from simulation.agent import Agent
from simulation.climate import run_climate_phase
from simulation.trade import run_trade_phase
from simulation.conflict import run_conflict_phase
from simulation.reward import calculate_reward, get_reward_breakdown
from services.firestore_service import (
    write_all_regions, write_world_state, write_event,
    write_cycle_log, initialize_regions, clear_simulation_data,
)
from services.analysis_service import run_analysis

logger = logging.getLogger("world")


# ===========================================================================
# World Class
# ===========================================================================

class World:
    """
    Orchestrates the WorldSim simulation across 5 regions and 100 cycles.

    Holds all Region objects and their corresponding Agents.
    Manages the simulation loop, Firestore persistence, and
    post-simulation analysis.
    """

    def __init__(self):
        """Initialize the world with empty state."""
        self.regions: dict[str, Region] = {}
        self.agents: dict[str, Agent] = {}
        self.cycle = 0
        self.is_running = False
        self.is_paused = False
        self.speed = CYCLE_SPEED
        self.events_this_cycle: list = []
        self.all_events: list = []

    # -----------------------------------------------------------------------
    # Setup
    # -----------------------------------------------------------------------

    def setup(self):
        """
        Create all 5 regions and agents from INITIAL_REGIONS config.
        Reset cycle counter and clear previous simulation data.
        """
        self.regions = {}
        self.agents = {}
        self.cycle = 0
        self.is_running = False
        self.is_paused = False
        self.all_events = []

        for region_id, data in INITIAL_REGIONS.items():
            self.regions[region_id] = Region(
                region_id=region_id,
                water=data["water"],
                food=data["food"],
                energy=data["energy"],
                land=data["land"],
                population=data["population"],
            )
            self.agents[region_id] = Agent(region_id)

        logger.info("World setup complete — %d regions initialized.",
                     len(self.regions))

    # -----------------------------------------------------------------------
    # Firestore Initialization
    # -----------------------------------------------------------------------

    def initialize_firestore(self) -> bool:
        """
        Clear old data and write initial region states to Firestore.

        Returns:
            True if initialization succeeded.
        """
        try:
            clear_simulation_data()

            initial_data = [
                region.to_dict() for region in self.regions.values()
            ]
            success = initialize_regions(initial_data)

            if success:
                write_world_state(cycle=0, running=False, speed=self.speed)
                logger.info("Firestore initialized with %d regions.",
                             len(initial_data))
            return success

        except Exception as exc:
            logger.error("Firestore init failed: %s", exc)
            return False

    # -----------------------------------------------------------------------
    # Single Cycle Execution
    # -----------------------------------------------------------------------

    def run_cycle(self):
        """
        Execute one complete simulation cycle in strict phase order.

        Returns:
            List of event log dicts generated this cycle.
        """
        self.cycle += 1
        self.events_this_cycle = []

        regions_list = list(self.regions.values())

        # Snapshot BEFORE this cycle for reward calculation
        pre_states = {
            rid: region.to_dict() for rid, region in self.regions.items()
        }

        # ── Phase 1: Climate Events ────────────────────────────────
        climate_events = run_climate_phase(regions_list)
        for event in climate_events:
            event["cycle"] = self.cycle
            self.events_this_cycle.append(event)

        # ── Phase 2: Consumption ───────────────────────────────────
        for region in regions_list:
            region.consume()

        # ── Phase 2b: Special Abilities ────────────────────────────
        # Regen runs AFTER consume so it offsets depletion naturally.
        # Aquaria +2 water, Agrovia +3 food, Petrozon +1.5 energy per cycle.
        for region in regions_list:
            region.apply_special_ability()

        # ── Phase 2c: Population Dynamics ─────────────────────────
        # Runs AFTER consume+regen so avg_resources reflects true state.
        for region in regions_list:
            region.update_population()

        # ── Phase 3: Agent Decisions ───────────────────────────────
        for region_id, agent in self.agents.items():
            region = self.regions[region_id]
            status = region.get_resource_status()

            observation = {
                "water": region.water,
                "food": region.food,
                "energy": region.energy,
                "land": region.land,
                "population": region.population,
                "health_score": region.health_score,
                "critical": status["critical"],
                "emergency": status["emergency"],
                "surplus": status["surplus"],
                "deficit": status["deficit"],
                "resource_emergency": len(status["emergency"]) > 0,
                "trust_scores": region.trust_scores,
                "strategy_weights": region.strategy_weights,
                "is_collapsed": region.is_collapsed,
            }

            action = agent.decide(observation)
            region.last_action = action

        # ── Phase 4: Trade Phase ───────────────────────────────────
        # Pass cycle so distant-pair distance penalty applies after cycle 30.
        trade_events = run_trade_phase(regions_list, cycle=self.cycle)
        for event in trade_events:
            event["cycle"] = self.cycle
            self.events_this_cycle.append(event)

        # ── Phase 5: Conflict Phase ────────────────────────────────
        conflict_events = run_conflict_phase(regions_list)
        for event in conflict_events:
            event["cycle"] = self.cycle
            self.events_this_cycle.append(event)

        # ── Phase 6: Reward Calculation ────────────────────────────
        for region_id, region in self.regions.items():
            post_state = region.to_dict()
            reward = calculate_reward(pre_states[region_id], post_state)
            region.last_reward = reward

        # ── Phase 7: Weight Adaptation ─────────────────────────────
        for region_id, agent in self.agents.items():
            region = self.regions[region_id]
            action = region.last_action
            reward = region.last_reward

            # Determine outcome from events
            outcome = self._get_action_outcome(region_id)

            agent.update_weights(action, outcome, reward)

            # Sync agent weights back to region for Firestore
            region.strategy_weights = dict(agent.strategy_weights)
            region.strategy_label = agent.strategy_label

        # ── Phase 8: Health Recalculation ──────────────────────────
        for region in regions_list:
            region.calculate_health()
            region.cycle = self.cycle

        # ── Phase 9: History Logging ───────────────────────────────
        for region in regions_list:
            region.log_history()

        # ── Phase 10: Firestore Persistence ────────────────────────
        self._persist_cycle()

        # Accumulate events
        self.all_events.extend(self.events_this_cycle)

        return self.events_this_cycle

    # -----------------------------------------------------------------------
    # Helpers
    # -----------------------------------------------------------------------

    def _get_action_outcome(self, region_id: str) -> str:
        """
        Determine the outcome string for a region's action this cycle
        by checking the events generated.
        """
        for event in self.events_this_cycle:
            if event.get("source_region") == region_id:
                return event.get("outcome", "neutral")
            if event.get("target_region") == region_id:
                outcome = event.get("outcome", "neutral")
                # Flip outcome for defender perspective
                if outcome == "aggress_success":
                    return "aggress_defended_loss"
                if outcome == "aggress_failed":
                    return "aggress_defended_win"
                return outcome
        return "neutral"

    def _persist_cycle(self):
        """Write current cycle state to Firestore."""
        try:
            # Batch write all regions
            region_dicts = [r.to_dict() for r in self.regions.values()]
            write_all_regions(region_dicts)

            # Write world state
            write_world_state(
                cycle=self.cycle,
                running=self.is_running,
                speed=self.speed,
            )

            # Write cycle log snapshot
            snapshot = {
                rid: region.to_dict()
                for rid, region in self.regions.items()
            }
            write_cycle_log(self.cycle, snapshot)

            # Write individual events
            for event in self.events_this_cycle:
                write_event(
                    event_type=event.get("type", "unknown"),
                    cycle=self.cycle,
                    source_region=event.get("source_region",
                                            event.get("affected_region", "")),
                    target_region=event.get("target_region", ""),
                    description=event.get("description", ""),
                    outcome=event.get("outcome", ""),
                )

        except Exception as exc:
            logger.error("Cycle %d persistence failed: %s",
                          self.cycle, exc)

    # -----------------------------------------------------------------------
    # Simulation Loop
    # -----------------------------------------------------------------------

    async def run(self):
        """
        Run the full simulation loop for TOTAL_CYCLES.

        Can be paused/resumed via is_paused flag.
        Writes final analysis report after completion.
        """
        self.is_running = True
        self.is_paused = False
        logger.info("Simulation started — running %d cycles.", TOTAL_CYCLES)

        try:
            write_world_state(cycle=self.cycle, running=True,
                              speed=self.speed)

            while self.cycle < TOTAL_CYCLES and self.is_running:
                # Check for pause
                if self.is_paused:
                    write_world_state(cycle=self.cycle, running=False,
                                      speed=self.speed)
                    await asyncio.sleep(0.5)
                    continue

                # Run one cycle
                self.run_cycle()

                # Log progress every 10 cycles
                if self.cycle % 10 == 0:
                    surviving = sum(
                        1 for r in self.regions.values()
                        if not r.is_collapsed
                    )
                    logger.info(
                        "Cycle %d/%d — %d regions surviving.",
                        self.cycle, TOTAL_CYCLES, surviving,
                    )

                # Pace the simulation
                await asyncio.sleep(self.speed)

        except Exception as exc:
            logger.error("Simulation error at cycle %d: %s",
                          self.cycle, exc)
        finally:
            self.is_running = False
            write_world_state(cycle=self.cycle, running=False,
                              speed=self.speed)

        # Post-simulation analysis
        logger.info("Simulation complete at cycle %d. Running analysis...",
                     self.cycle)
        try:
            run_analysis()
            logger.info("Analysis written to Firestore.")
        except Exception as exc:
            logger.error("Post-simulation analysis failed: %s", exc)

    def pause(self):
        """Pause the simulation loop."""
        self.is_paused = True
        logger.info("Simulation paused at cycle %d.", self.cycle)

    def resume(self):
        """Resume a paused simulation."""
        self.is_paused = False
        logger.info("Simulation resumed at cycle %d.", self.cycle)

    def stop(self):
        """Stop the simulation loop entirely."""
        self.is_running = False
        logger.info("Simulation stopped at cycle %d.", self.cycle)

    # -----------------------------------------------------------------------
    # State Accessors
    # -----------------------------------------------------------------------

    def get_state(self) -> dict:
        """
        Return the complete current world state as a dict.

        Returns:
            Dictionary with cycle, running status, and all region states.
        """
        return {
            "cycle": self.cycle,
            "total_cycles": TOTAL_CYCLES,
            "is_running": self.is_running,
            "is_paused": self.is_paused,
            "speed": self.speed,
            "regions": {
                rid: region.to_dict()
                for rid, region in self.regions.items()
            },
            "events_this_cycle": self.events_this_cycle,
        }

    def get_surviving_count(self) -> int:
        """Return the number of non-collapsed regions."""
        return sum(
            1 for r in self.regions.values() if not r.is_collapsed
        )


# ===========================================================================
# Test Cases
# ===========================================================================

if __name__ == "__main__":

    logging.basicConfig(
        level=logging.INFO,
        format="%(name)s - %(message)s",
    )

    PASS = "[PASS]"
    FAIL = "[FAIL]"

    # ===================================================================
    # TEST 1 — Setup creates 5 regions and agents
    # ===================================================================
    print("=" * 60)
    print("  TEST 1 - World Setup")
    print("=" * 60)

    world = World()
    world.setup()

    print(f"  Regions: {len(world.regions)}")
    print(f"  Agents:  {len(world.agents)}")
    print(f"  5 regions? {PASS if len(world.regions) == 5 else FAIL}")
    print(f"  5 agents?  {PASS if len(world.agents) == 5 else FAIL}")

    for rid, region in world.regions.items():
        print(f"    {rid}: W={region.water} F={region.food} "
              f"E={region.energy} L={region.land} P={region.population}")
    print()

    # ===================================================================
    # TEST 2 — Single cycle runs all phases
    # ===================================================================
    print("=" * 60)
    print("  TEST 2 - Single Cycle Execution (no Firestore)")
    print("=" * 60)

    # Monkey-patch Firestore functions to no-ops for testing
    import services.firestore_service as fs
    fs.write_all_regions = lambda x: True
    fs.write_world_state = lambda **kw: True
    fs.write_event = lambda **kw: True
    fs.write_cycle_log = lambda c, s: True

    # Re-import after patching
    world2 = World()
    world2.setup()

    # Override persist to use patched functions
    def mock_persist(self_ref):
        pass
    world2._persist_cycle = lambda: mock_persist(world2)

    events = world2.run_cycle()
    print(f"  Cycle advanced to: {world2.cycle}")
    print(f"  Cycle == 1? {PASS if world2.cycle == 1 else FAIL}")
    print(f"  Events generated: {len(events)}")

    # Check that regions were consumed
    aq = world2.regions["aquaria"]
    print(f"  Aquaria water: {aq.water:.2f} (should be < 90)")
    print(f"  Consumed? {PASS if aq.water < 90 else FAIL}")
    print()

    # ===================================================================
    # TEST 3 — 10 cycles accumulate
    # ===================================================================
    print("=" * 60)
    print("  TEST 3 - Run 10 Cycles")
    print("=" * 60)

    world3 = World()
    world3.setup()
    world3._persist_cycle = lambda: None

    for _ in range(10):
        world3.run_cycle()

    print(f"  Cycle: {world3.cycle}")
    print(f"  10 cycles? {PASS if world3.cycle == 10 else FAIL}")
    print(f"  Surviving: {world3.get_surviving_count()}/5")

    for rid, region in world3.regions.items():
        print(f"    {rid}: H={region.health_score:.1f} "
              f"P={region.population:.0f} "
              f"action={region.last_action} "
              f"label={region.strategy_label}")
    print()

    # ===================================================================
    # TEST 4 — get_state() returns complete dict
    # ===================================================================
    print("=" * 60)
    print("  TEST 4 - get_state()")
    print("=" * 60)

    state = world3.get_state()
    keys = ["cycle", "total_cycles", "is_running", "is_paused",
            "speed", "regions", "events_this_cycle"]
    missing = [k for k in keys if k not in state]
    print(f"  State keys: {list(state.keys())}")
    print(f"  Missing: {missing if missing else 'None'}")
    print(f"  All keys? {PASS if not missing else FAIL}")
    print(f"  Regions in state: {len(state['regions'])}")
    print()

    # ===================================================================
    print("=" * 60)
    print("  All world tests complete")
    print("=" * 60)
