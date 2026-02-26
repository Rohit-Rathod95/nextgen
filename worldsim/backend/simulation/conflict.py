"""
conflict.py

Handles mechanical conflict resolution between two competing regions over a resource.
"""

from typing import Dict
from backend.simulation.region import Region
from backend.config.regions_config import MIN_RESOURCE, MAX_RESOURCE

class ConflictEngine:
    """
    Engine responsible for mechanically resolving conflicts between two regions.
    """
    def resolve_conflict(self, attacker: Region, defender: Region, resource: str) -> Dict:
        """
        Executes conflict mechanics between an attacker and defender over a resource.
        The winner steals 25 units, the loser loses 15 energy.
        
        Args:
            attacker: The Region initiating the conflict.
            defender: The Region being attacked.
            resource: The string representing the resource in contention.
            
        Returns:
            Dictionary containing conflict metadata.
        """
        strength_attacker = attacker.energy + (attacker.population * 0.1)
        strength_defender = defender.energy + (defender.population * 0.1)
        
        if strength_attacker > strength_defender:
            winner = attacker
            loser = defender
        else:
            winner = defender
            loser = attacker
            
        steal_amount = 25.0
        energy_penalty = 15.0
        
        # Deduct from loser
        loser_resource_val = getattr(loser, resource)
        # Handle case where loser has less than 25 units
        actual_stolen = min(steal_amount, loser_resource_val) 
        
        setattr(loser, resource, loser_resource_val - actual_stolen)
        loser.energy -= energy_penalty
        
        # Add to winner
        winner_resource_val = getattr(winner, resource)
        setattr(winner, resource, winner_resource_val + actual_stolen)
        
        # Clamp bounds
        setattr(loser, resource, max(MIN_RESOURCE, min(MAX_RESOURCE, getattr(loser, resource))))
        loser.energy = max(MIN_RESOURCE, min(MAX_RESOURCE, loser.energy))
        
        setattr(winner, resource, max(MIN_RESOURCE, min(MAX_RESOURCE, getattr(winner, resource))))
        winner.energy = max(MIN_RESOURCE, min(MAX_RESOURCE, winner.energy))
        
        return {
            "winner": winner.name,
            "loser": loser.name,
            "resource": resource,
            "amount": actual_stolen
        }
