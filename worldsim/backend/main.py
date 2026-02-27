"""
main.py — FastAPI Application Entry Point for WorldSim

Provides REST API endpoints to control and monitor the simulation:

    POST /start   — Start a new simulation run (100 cycles)
    POST /pause   — Pause a running simulation
    POST /resume  — Resume a paused simulation
    POST /stop    — Stop the simulation entirely
    GET  /state   — Get current world state
    GET  /health  — Health check endpoint

CORS is configured to allow the frontend (port 5173) to connect.
The simulation runs as a background async task.
"""

import asyncio
import logging
from contextlib import asynccontextmanager

from fastapi import FastAPI, HTTPException, BackgroundTasks
from fastapi.middleware.cors import CORSMiddleware
from config.regions_config import TOTAL_CYCLES
from simulation.world import World

# ---------------------------------------------------------------------------
# Logging
# ---------------------------------------------------------------------------

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s | %(name)-18s | %(levelname)-5s | %(message)s",
    datefmt="%H:%M:%S",
)
logger = logging.getLogger("main")

# ---------------------------------------------------------------------------
# Global State
# ---------------------------------------------------------------------------

world = World()
simulation_task: asyncio.Task | None = None


# ---------------------------------------------------------------------------
# Lifespan (startup/shutdown)
# ---------------------------------------------------------------------------

@asynccontextmanager
async def lifespan(app: FastAPI):
    """Setup on startup, cleanup on shutdown."""
    logger.info("WorldSim API starting up...")
    world.setup()
    
    # Force reset Firestore state so frontend doesn't get stuck with ghost runs
    try:
        world.initialize_firestore()
    except Exception as exc:
        logger.warning("Firestore init skipped on startup (no credentials): %s", exc)
        
    logger.info("World initialized with %d regions.", len(world.regions))
    yield
    # Shutdown
    global simulation_task
    if simulation_task and not simulation_task.done():
        world.stop()
        simulation_task.cancel()
        logger.info("Simulation task cancelled on shutdown.")


# ---------------------------------------------------------------------------
# FastAPI App
# ---------------------------------------------------------------------------

app = FastAPI(
    title="WorldSim API",
    description="Adaptive Resource Scarcity and Strategy Evolution Simulator",
    version="1.0.0",
    lifespan=lifespan,
)

# root path — helpful when code mistakenly hits BASE without endpoint
@app.get("/")
async def root():
    return {"status": "ok", "message": "WorldSim API is running"}

# CORS — allow frontend dev server and deployed URLs (permit everything for demo)
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # wildcard allowed for hackathon/demo
    allow_credentials=True,
    allow_methods=["GET", "POST", "PUT", "DELETE", "OPTIONS"],
    allow_headers=["*"],
)


# ===========================================================================
# Endpoints
# ===========================================================================

# ─── Health Check ────────────────────────────────────────────────────────────

@app.get("/health")
async def health_check():
    """Health check — returns API status."""
    return {
        "status": "ok",
        "service": "worldsim-api",
        "regions_loaded": len(world.regions),
    }


# ─── Start Simulation ───────────────────────────────────────────────────────

@app.post("/start")
async def start_simulation():
    """
    Start a new 100-cycle simulation run.

    Resets the world to initial state, initializes Firestore,
    and launches the simulation as a background async task.
    """
    global simulation_task
    
    try:
        world.is_running = False
        world.is_paused = False
        world.current_cycle = 0
    except:
        pass

    # Fresh setup
    world.setup()

    # Initialize Firestore (may fail if no credentials)
    try:
        world.initialize_firestore()
    except Exception as exc:
        logger.warning(
            "Firestore init skipped (no credentials): %s", exc
        )

    # Launch as background task
    simulation_task = asyncio.create_task(world.run())

    logger.info("Simulation started via API.")
    return {
        "status": "started",
        "total_cycles": TOTAL_CYCLES,
        "regions": list(world.regions.keys()),
    }


# ─── Pause Simulation ───────────────────────────────────────────────────────

@app.post("/pause")
async def pause_simulation():
    """Pause the running simulation."""
    if not world.is_running:
        raise HTTPException(
            status_code=409, detail="No simulation is running.",
        )

    if world.is_paused:
        raise HTTPException(
            status_code=409, detail="Simulation is already paused.",
        )

    world.pause()
    return {
        "status": "paused",
        "cycle": world.cycle,
    }


# ─── Resume Simulation ──────────────────────────────────────────────────────

@app.post("/resume")
async def resume_simulation():
    """Resume a paused simulation."""
    if not world.is_running:
        raise HTTPException(
            status_code=409, detail="No simulation is running.",
        )

    if not world.is_paused:
        raise HTTPException(
            status_code=409, detail="Simulation is not paused.",
        )

    world.resume()
    return {
        "status": "resumed",
        "cycle": world.cycle,
    }


# ─── Stop Simulation ────────────────────────────────────────────────────────

@app.post("/stop")
async def stop_simulation():
    """Stop the simulation entirely."""
    global simulation_task

    world.stop()

    if simulation_task and not simulation_task.done():
        simulation_task.cancel()
        
    # Force sync Firestore state in case of frontend/backend desync
    from services.firestore_service import write_world_state
    try:
        write_world_state(cycle=world.cycle, running=False, speed=world.speed)
    except Exception as exc:
        logger.warning("Failed to write manual stop to Firestore: %s", exc)

    return {
        "status": "stopped",
        "final_cycle": world.cycle,
    }


# ─── Get World State ────────────────────────────────────────────────────────

@app.get("/state")
async def get_world_state():
    """
    Return the complete current world state.

    Includes cycle count, running status, all region data,
    and events from the current cycle.
    """
    return world.get_state()


# ─── Set Speed ───────────────────────────────────────────────────────────────

@app.post("/speed/{multiplier}")
async def set_speed(multiplier: float):
    """
    Set the simulation speed (seconds between cycles).

    Args:
        multiplier: Seconds to wait between cycles (0.1 = fast, 2.0 = slow).
    """
    if multiplier < 0.1 or multiplier > 10.0:
        raise HTTPException(
            status_code=400,
            detail="Speed must be between 0.1 and 10.0 seconds.",
        )

    world.speed = multiplier
    return {
        "status": "speed_updated",
        "speed": multiplier,
    }


# ===========================================================================
# Entry Point
# ===========================================================================

if __name__ == "__main__":
    import uvicorn

    logger.info("Starting WorldSim API on port 8000...")
    uvicorn.run(
        "main:app",
        host="0.0.0.0",
        port=8000,
        reload=True,
        log_level="info",
    )
