"""
trade.py

Handles mechanical resource transfers between regions with deficits and surpluses.
"""

from typing import List, Dict
from backend.simulation.region import Region
from backend.config.regions_config import DEFICIT_THRESHOLD, SURPLUS_THRESHOLD

class TradeEngine:
    """
    Engine responsible for executing trades between regions mechanically.
    """
    def resolve_trades(self, regions: List[Region]) -> List[Dict]:
        """
        Executes trades by moving 20 units of resources from regions with surpluses 
        to regions with deficits. Avoids double counting trades in the same cycle.
        
        Args:
            regions: A list of Region objects.
            
        Returns:
            A list of dictionary metadata detailing each trade event.
        """
        trade_events: List[Dict] = []
        resources = ["water", "food", "energy"]
        
        # Track traded regions to prevent double-counting per resource type per cycle
        traded_this_cycle = set()
        
        for res in resources:
            for r_a in regions:
                for r_b in regions:
                    if r_a.name == r_b.name:
                        continue
                        
                    # Create unique trade key to ensure regions only get involved once per resource
                    trade_key_a = f"{r_a.name}_{res}"
                    trade_key_b = f"{r_b.name}_{res}"
                    
                    if trade_key_a in traded_this_cycle or trade_key_b in traded_this_cycle:
                        continue
                    
                    val_a = getattr(r_a, res)
                    val_b = getattr(r_b, res)
                    
                    if val_a < DEFICIT_THRESHOLD and val_b > SURPLUS_THRESHOLD:
                        amount_to_trade = 20.0
                        
                        # Only transfer if B has enough resource
                        if val_b >= amount_to_trade:
                            setattr(r_b, res, val_b - amount_to_trade)
                            setattr(r_a, res, getattr(r_a, res) + amount_to_trade)
                            
                            trade_events.append({
                                "from": r_b.name,
                                "to": r_a.name,
                                "resource": res,
                                "amount": amount_to_trade
                            })
                            
                            traded_this_cycle.add(trade_key_a)
                            traded_this_cycle.add(trade_key_b)
                            
        return trade_events
