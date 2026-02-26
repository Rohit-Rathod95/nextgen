"""
firestore_service.py - Firestore Write Service for WorldSim

This is the ONLY module that writes to Firestore. All simulation
state persistence flows through the functions defined here.

Collections:
    regions      - Live state for each of the 5 regions
    world_state  - Global simulation metadata (cycle, running, speed)
    events       - Individual simulation events (trades, conflicts, climate)
    cycle_logs   - Full world snapshot per cycle for historical replay
    analysis     - Auto-generated strategic insights and narratives

Every function is wrapped in try/except and returns a boolean
indicating success. No function ever raises an exception upward -
the simulation must never crash due to a database write failure.
"""

import logging
from datetime import datetime

from config.firebase_config import db
from firebase_admin import firestore

# ---------------------------------------------------------------------------
# Logger
# ---------------------------------------------------------------------------

logger = logging.getLogger("firestore_service")


def _check_db() -> bool:
    """Return True if Firestore is available, False otherwise."""
    if db is None:
        logger.debug("Firestore not available — write skipped.")
        return False
    return True

# ---------------------------------------------------------------------------
# Collection Name Constants
# ---------------------------------------------------------------------------

COLLECTION_REGIONS = "regions"
COLLECTION_WORLD_STATE = "world_state"
COLLECTION_EVENTS = "events"
COLLECTION_CYCLE_LOGS = "cycle_logs"
COLLECTION_ANALYSIS = "analysis"

# Document ID constants
WORLD_STATE_DOC_ID = "current"
ANALYSIS_DOC_ID = "insights"


# ---------------------------------------------------------------------------
# FUNCTION 1 - Write Single Region State
# ---------------------------------------------------------------------------

def write_region_state(region_data: dict) -> bool:
    """
    Write a single region's complete state to Firestore.

    Performs a full document replacement (merge=False) so the document
    always reflects the exact current state with no stale fields.

    Args:
        region_data: Dictionary containing all region fields.
                     Must include "region_id" as the document key.

    Returns:
        True if the write succeeded, False otherwise.
    """
    if not _check_db():
        return False
    try:
        region_id = region_data.get("region_id")
        if not region_id:
            logger.error("write_region_state: missing 'region_id' in region_data.")
            return False

        # Attach server timestamp for write tracking
        data = {**region_data, "updated_at": firestore.SERVER_TIMESTAMP}

        # Full document replacement - no merging with old fields
        doc_ref = db.collection(COLLECTION_REGIONS).document(region_id)
        doc_ref.set(data, merge=False)

        logger.info("write_region_state: wrote region '%s' successfully.", region_id)
        return True

    except Exception as exc:
        logger.error("write_region_state: failed for region '%s' - %s",
                      region_data.get("region_id", "unknown"), exc)
        return False


# ---------------------------------------------------------------------------
# FUNCTION 2 - Write All Regions (Batched)
# ---------------------------------------------------------------------------

def write_all_regions(regions_list: list) -> bool:
    """
    Write all 5 regions in a single atomic batch operation.

    Firestore batched writes guarantee that either ALL regions update
    together or NONE do - preventing inconsistent world state reads
    on the frontend.

    Args:
        regions_list: List of 5 region data dictionaries, each containing
                      all region fields including "region_id".

    Returns:
        True if the batch commit succeeded, False otherwise.
    """
    if not _check_db():
        return False
    try:
        batch = db.batch()

        for region_data in regions_list:
            region_id = region_data.get("region_id")
            if not region_id:
                logger.error("write_all_regions: skipping region with missing 'region_id'.")
                continue

            # Attach server timestamp to each region document
            data = {**region_data, "updated_at": firestore.SERVER_TIMESTAMP}

            ref = db.collection(COLLECTION_REGIONS).document(region_id)
            batch.set(ref, data, merge=False)

        # Atomic commit - all or nothing
        batch.commit()

        logger.info("write_all_regions: wrote %d regions successfully.", len(regions_list))
        return True

    except Exception as exc:
        logger.error("write_all_regions: batch commit failed - %s", exc)
        return False


# ---------------------------------------------------------------------------
# FUNCTION 3 - Write World State
# ---------------------------------------------------------------------------

def write_world_state(cycle: int, running: bool, speed: float) -> bool:
    """
    Write global simulation metadata to a single Firestore document.

    Always overwrites the same document ("current") so the frontend
    can subscribe to a single document path for live status updates.

    Args:
        cycle:   Current simulation cycle number (0-100).
        running: Whether the simulation is actively running.
        speed:   Simulation speed multiplier.

    Returns:
        True if the write succeeded, False otherwise.
    """
    if not _check_db():
        return False
    try:
        data = {
            "current_cycle": cycle,
            "is_running": running,
            "current_event": "None",
            "speed": speed,
            "updated_at": firestore.SERVER_TIMESTAMP,
        }

        doc_ref = db.collection(COLLECTION_WORLD_STATE).document(WORLD_STATE_DOC_ID)
        doc_ref.set(data, merge=False)

        logger.info("write_world_state: cycle=%d, running=%s.", cycle, running)
        return True

    except Exception as exc:
        logger.error("write_world_state: failed - %s", exc)
        return False


# ---------------------------------------------------------------------------
# FUNCTION 4 - Write Event
# ---------------------------------------------------------------------------

def write_event(event_type: str,
                cycle: int,
                source_region: str,
                target_region: str,
                description: str,
                outcome: str) -> bool:
    """
    Write a single simulation event to the events collection.

    Document ID is auto-generated by Firestore to allow unlimited
    events per cycle without key conflicts.

    Args:
        event_type:    One of "climate", "trade", "conflict", "collapse".
        cycle:         Cycle number when the event occurred.
        source_region: Region that initiated the event.
        target_region: Region affected by the event (may be same as source).
        description:   Human-readable event description.
        outcome:       Result of the event (e.g. "success", "failed").

    Returns:
        True if the write succeeded, False otherwise.
    """
    if not _check_db():
        return False
    try:
        data = {
            "type": event_type,
            "cycle": cycle,
            "source_region": source_region,
            "target_region": target_region,
            "description": description,
            "outcome": outcome,
            "timestamp": firestore.SERVER_TIMESTAMP,
        }

        # Auto-generated document ID for unlimited event logs
        db.collection(COLLECTION_EVENTS).add(data)

        logger.info("write_event: [%s] %s -> %s at cycle %d.",
                     event_type, source_region, target_region, cycle)
        return True

    except Exception as exc:
        logger.error("write_event: failed - %s", exc)
        return False


# ---------------------------------------------------------------------------
# FUNCTION 5 - Write Cycle Log
# ---------------------------------------------------------------------------

def write_cycle_log(cycle: int, regions_snapshot: dict, events_fired: list = None) -> bool:
    """
    Write a complete world snapshot for a specific cycle.

    Document ID is zero-padded (e.g. "cycle_001") for clean ordering
    in the Firestore console and frontend queries.

    Args:
        cycle:            Cycle number (1-100).
        regions_snapshot: Dictionary keyed by region_id, each containing
                          the full region state for this cycle.
        events_fired:     List of event dicts that occurred this cycle.
                          Required by analysis_service.

    Returns:
        True if the write succeeded, False otherwise.
    """
    if not _check_db():
        return False
    try:
        # Zero-pad cycle number for consistent ordering
        doc_id = f"cycle_{str(cycle).zfill(3)}"

        data = {
            "cycle": cycle,
            "regions_snapshot": regions_snapshot,
            "events_fired": events_fired or [],
            "timestamp": firestore.SERVER_TIMESTAMP,
        }

        doc_ref = db.collection(COLLECTION_CYCLE_LOGS).document(doc_id)
        doc_ref.set(data, merge=False)

        logger.info("write_cycle_log: wrote snapshot for cycle %d.", cycle)
        return True

    except Exception as exc:
        logger.error("write_cycle_log: failed for cycle %d - %s", cycle, exc)
        return False


# ---------------------------------------------------------------------------
# FUNCTION 6 - Write Analysis
# ---------------------------------------------------------------------------

def write_analysis(insights: list,
                   dominant_strategy: str,
                   collapse_events: list,
                   alliance_events: list,
                   real_world_parallel: str) -> bool:
    """
    Write the auto-generated analysis report to Firestore.

    Overwrites a single "insights" document - only one analysis
    exists at a time, reflecting the latest simulation run.

    Args:
        insights:            List of insight strings.
        dominant_strategy:   The most common strategy label across regions.
        collapse_events:     List of collapse event descriptions.
        alliance_events:     List of alliance formation descriptions.
        real_world_parallel: Narrative connecting simulation to real-world patterns.

    Returns:
        True if the write succeeded, False otherwise.
    """
    if not _check_db():
        return False
    try:
        data = {
            "insights": insights,
            "dominant_strategy": dominant_strategy,
            "collapse_events": collapse_events,
            "alliance_events": alliance_events,
            "real_world_parallel": real_world_parallel,
            "generated_at": firestore.SERVER_TIMESTAMP,
        }

        doc_ref = db.collection(COLLECTION_ANALYSIS).document(ANALYSIS_DOC_ID)
        doc_ref.set(data, merge=False)

        logger.info("write_analysis: wrote %d insights.", len(insights))
        return True

    except Exception as exc:
        logger.error("write_analysis: failed - %s", exc)
        return False


# ---------------------------------------------------------------------------
# FUNCTION 7 - Initialize Regions
# ---------------------------------------------------------------------------

def initialize_regions(initial_data: list) -> bool:
    """
    Bootstrap all 5 regions and the world state for a new simulation run.

    Called once at simulation start. Writes initial region states using
    the batched write function and sets the world state to cycle 0.

    Args:
        initial_data: List of 5 region data dictionaries with initial
                      resource levels, population, and strategy weights.

    Returns:
        True if both the region write and world state write succeeded.
    """
    if not _check_db():
        return False
    try:
        # Write all 5 regions atomically
        regions_ok = write_all_regions(initial_data)
        if not regions_ok:
            logger.error("initialize_regions: failed to write initial region states.")
            return False

        # Set world state to cycle 0, not running
        world_ok = write_world_state(cycle=0, running=False, speed=1.0)
        if not world_ok:
            logger.error("initialize_regions: failed to write initial world state.")
            return False

        logger.info("initialize_regions: initialized %d regions at cycle 0.",
                     len(initial_data))
        return True

    except Exception as exc:
        logger.error("initialize_regions: failed - %s", exc)
        return False


# ---------------------------------------------------------------------------
# FUNCTION 8 - Clear Simulation Data
# ---------------------------------------------------------------------------

def clear_simulation_data() -> bool:
    """
    Delete all transient simulation data before a fresh run.

    Clears:
        - All documents in the events collection
        - All documents in the cycle_logs collection
        - The single "insights" document in the analysis collection

    Does NOT delete the regions collection (overwritten during init).

    Returns:
        True if all deletions succeeded, False otherwise.
    """
    if not _check_db():
        return True
    try:
        total_deleted = 0

        # --- Clear events collection ---
        events_docs = db.collection(COLLECTION_EVENTS).stream()
        events_batch = db.batch()
        events_count = 0
        for doc in events_docs:
            events_batch.delete(doc.reference)
            events_count += 1
            # Firestore batches are limited to 500 operations
            if events_count % 500 == 0:
                events_batch.commit()
                events_batch = db.batch()
        if events_count % 500 != 0:
            events_batch.commit()
        total_deleted += events_count

        # --- Clear cycle_logs collection ---
        logs_docs = db.collection(COLLECTION_CYCLE_LOGS).stream()
        logs_batch = db.batch()
        logs_count = 0
        for doc in logs_docs:
            logs_batch.delete(doc.reference)
            logs_count += 1
            if logs_count % 500 == 0:
                logs_batch.commit()
                logs_batch = db.batch()
        if logs_count % 500 != 0:
            logs_batch.commit()
        total_deleted += logs_count

        # --- Clear analysis document ---
        analysis_ref = db.collection(COLLECTION_ANALYSIS).document(ANALYSIS_DOC_ID)
        analysis_doc = analysis_ref.get()
        if analysis_doc.exists:
            analysis_ref.delete()
            total_deleted += 1

        logger.info(
            "clear_simulation_data: deleted %d documents "
            "(events=%d, cycle_logs=%d, analysis=%s).",
            total_deleted, events_count, logs_count,
            "1" if analysis_doc.exists else "0"
        )
        return True

    except Exception as exc:
        logger.error("clear_simulation_data: failed - %s", exc)
        return False


# ---------------------------------------------------------------------------
# Test Cases
# ---------------------------------------------------------------------------

if __name__ == "__main__":
    logging.basicConfig(level=logging.INFO, format="%(name)s - %(message)s")

    PASS = "[PASS]"
    FAIL = "[FAIL]"

    # --- Mock region data factory ---
    def mock_region(region_id, water=60, food=60, energy=60, land=60,
                    population=1000, health=70, cycle=1):
        return {
            "region_id": region_id,
            "water": water,
            "food": food,
            "energy": energy,
            "land": land,
            "population": population,
            "health_score": health,
            "strategy_weights": {
                "trade": 0.25, "hoard": 0.25,
                "invest": 0.25, "aggress": 0.25,
            },
            "trust_scores": {
                "aquaria": 50, "agrovia": 50,
                "petrozon": 50, "urbanex": 50,
                "terranova": 50,
            },
            "last_action": "trade",
            "strategy_label": "Balanced",
            "last_reward": 0.0,
            "cycle": cycle,
        }

    REGIONS = ["aquaria", "agrovia", "petrozon", "urbanex", "terranova"]

    # =================================================================
    # TEST 1 - Write Single Region
    # =================================================================
    print("=" * 60)
    print("  TEST 1 - Write Single Region")
    print("=" * 60)
    result1 = write_region_state(mock_region("aquaria", water=72, food=78))
    print(f"  write_region_state('aquaria'): {PASS if result1 else FAIL}")
    print()

    # =================================================================
    # TEST 2 - Write All Regions (Batched)
    # =================================================================
    print("=" * 60)
    print("  TEST 2 - Write All Regions (Batched)")
    print("=" * 60)
    all_regions = [mock_region(rid) for rid in REGIONS]
    result2 = write_all_regions(all_regions)
    print(f"  write_all_regions (5 regions): {PASS if result2 else FAIL}")
    print()

    # =================================================================
    # TEST 3 - Write Event
    # =================================================================
    print("=" * 60)
    print("  TEST 3 - Write Event")
    print("=" * 60)
    result3 = write_event(
        event_type="trade",
        cycle=5,
        source_region="aquaria",
        target_region="agrovia",
        description="Aquaria traded 10 water for 8 food with Agrovia.",
        outcome="success",
    )
    print(f"  write_event('trade'): {PASS if result3 else FAIL}")
    print()

    # =================================================================
    # TEST 4 - Write Cycle Log
    # =================================================================
    print("=" * 60)
    print("  TEST 4 - Write Cycle Log")
    print("=" * 60)
    snapshot = {rid: mock_region(rid, cycle=1) for rid in REGIONS}
    result4 = write_cycle_log(cycle=1, regions_snapshot=snapshot)
    print(f"  write_cycle_log(cycle=1): {PASS if result4 else FAIL}")
    print()

    # =================================================================
    # TEST 5 - Write Analysis
    # =================================================================
    print("=" * 60)
    print("  TEST 5 - Write Analysis")
    print("=" * 60)
    result5 = write_analysis(
        insights=[
            "Aquaria emerged as the dominant trader, forming alliances with 3 regions.",
            "Petrozon hoarded energy reserves but suffered from food shortages.",
            "Urbanex adopted aggressive expansion, destabilizing regional trust.",
        ],
        dominant_strategy="Trader",
        collapse_events=["Terranova collapsed at cycle 67 due to total resource depletion."],
        alliance_events=["Aquaria-Agrovia alliance formed at cycle 12 after 10 consecutive trades."],
        real_world_parallel=(
            "The simulation mirrors OPEC-era resource politics where energy-rich nations "
            "leveraged scarcity to dominate trade while agrarian economies formed defensive "
            "alliances to ensure food security."
        ),
    )
    print(f"  write_analysis: {PASS if result5 else FAIL}")
    print()

    # =================================================================
    # TEST 6 - Clear Simulation Data
    # =================================================================
    print("=" * 60)
    print("  TEST 6 - Clear Simulation Data")
    print("=" * 60)
    result6 = clear_simulation_data()
    print(f"  clear_simulation_data: {PASS if result6 else FAIL}")
    print()

    # =================================================================
    print("=" * 60)
    print("  All Firestore write functions tested")
    print("  Check Firebase console to verify documents")
    print("=" * 60)
