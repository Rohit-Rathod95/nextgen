"""
region.py

Defines the Region class, its attributes, and local simulation behaviors.
"""

from typing import Dict, List
from backend.config.regions_config import (
    CONSUMPTION_RATE, MIN_RESOURCE, MAX_RESOURCE
)

class Region:
    """
    Represents a region in the simulation with resources, population, and inter-region trust.
    """
    def __init__(self, name: str, water: float, food: float, energy: float, land: float, population: float, other_region_names: List[str]):
        """
        Initializes a region's state.
        
        Args:
            name: The name of the region.
            water: Initial water level.
            food: Initial food level.
            energy: Initial energy level.
            land: Land metric.
            population: Region's population size.
            other_region_names: List of all other region names to initialize trust_scores.
        """
        self.name = name
        self.water = float(water)
        self.food = float(food)
        self.energy = float(energy)
        self.land = float(land)
        self.population = float(max(0.0, population))
        
        self.trust_scores: Dict[str, float] = {}
        for r_name in other_region_names:
            if r_name != self.name:
                self.trust_scores[r_name] = 0.5

    def _clamp_resource(self, value: float) -> float:
        """Helper to clamp resource values between config MIN and MAX."""
        return max(MIN_RESOURCE, min(MAX_RESOURCE, value))

    def consume_resources(self):
        """
        Calculates consumption based on population, subtracts from resources,
        and triggers population adjustment based on resource availability.
        """
        consumption = self.population * CONSUMPTION_RATE
        
        self.water -= consumption
        self.food -= consumption
        self.energy -= consumption
        
        self.adjust_population()
        
        # Resources must be clamped between 0 and 200 after consumption
        self.water = self._clamp_resource(self.water)
        self.food = self._clamp_resource(self.food)
        self.energy = self._clamp_resource(self.energy)

    def adjust_population(self):
        """
        Adjusts population per simulation rules:
        If any resource < 0: population decreases by 5%
        Else: population increases by 2%
        """
        if self.water < 0 or self.food < 0 or self.energy < 0:
            self.population *= 0.95  # decrease by 5%
        else:
            self.population *= 1.02  # increase by 2%
            
        self.population = max(0.0, self.population)

    def apply_climate(self, event_type: str):
        """
        Applies a climate event altering the region's resources.
        
        Args:
            event_type: A string identifying the type of climate event.
        """
        if event_type == "drought":
            self.water -= 20.0
        elif event_type == "flood":
            self.land -= 10.0
        elif event_type == "blizzard":
            self.energy -= 15.0
        elif event_type == "bountiful":
            self.food += 20.0
            
        self.water = self._clamp_resource(self.water)
        self.food = self._clamp_resource(self.food)
        self.energy = self._clamp_resource(self.energy)
        self.land = self._clamp_resource(self.land)

    def calculate_health(self) -> float:
        """
        Calculates the health of the region based on population ratio and resource balance.
        Formula:
            population_ratio = population / 700
            resource_balance = average(resource / 200)
            health = (0.5 * population_ratio) + (0.5 * resource_balance)
            
        Returns:
            The calculated health score.
        """
        population_ratio = self.population / 700.0
        
        # Taking average of water, food, and energy for the resource balance
        avg_resource = (self.water + self.food + self.energy) / 3.0
        resource_balance = avg_resource / 200.0
        
        health = (0.5 * population_ratio) + (0.5 * resource_balance)
        return health
