"""
climate.py

Handles random climate events that impact region resources.
"""

import random
from typing import List, Optional, Dict
from backend.simulation.region import Region
from backend.config.regions_config import CLIMATE_PROBABILITY

class ClimateEngine:
    """
    Engine responsible for mechanically triggering random climate events.
    """
    def trigger_event(self, regions: List[Region]) -> Optional[Dict]:
        """
        Randomly triggers a climate event on a single region if probability condition is met.
        
        Args:
            regions: A list of Region objects in the simulation.
            
        Returns:
            A dictionary containing event metadata (type, region) if initiated, or None.
        """
        if random.random() < CLIMATE_PROBABILITY:
            region = random.choice(regions)
            event_type = random.choice(["drought", "flood", "energy_crisis"])
            
            # Apply mechanical effects
            if event_type == "drought":
                region.water *= 0.7
            elif event_type == "flood":
                region.food *= 0.8
            elif event_type == "energy_crisis":
                region.energy *= 0.75
                
            # Use the region's method to clamp resources natively
            region.apply_climate(event_type)
            
            return {
                "type": event_type,
                "region": region.name
            }
        
        return None
