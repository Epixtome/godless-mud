"""
logic/core/services/favor_service.py
Manages the accrual and sacrifice of Favor for Deity-Shrine links.
"""
import logging
from utilities.colors import Colors

logger = logging.getLogger("GodlessMUD")

def award_favor(player, deity_id, amount):
    """Awards favor to a player with a specific deity."""
    if not hasattr(player, 'favor'):
        player.favor = {}
    
    player.favor[deity_id] = player.favor.get(deity_id, 0) + amount
    player.send_line(f"{Colors.YELLOW}You have gained {amount} favor with {deity_id.title()}.{Colors.RESET}")
    
    # Fire event for class ability unlocks or other favor-dependent logic
    from logic.core.engines import event_engine
    event_engine.dispatch("on_favor_gain", player=player, deity_id=deity_id, amount=amount)

def sacrifice_favor(player, deity_id, amount, shrine):
    """Sacrifices favor at a shrine to boost its potency."""
    current_favor = player.favor.get(deity_id, 0)
    if current_favor < amount:
        player.send_line(f"You only have {current_favor} favor with {deity_id.title()}. You need {amount}.")
        return False
        
    player.favor[deity_id] -= amount
    shrine.favor_reservoir += amount
    
    # Increase shrine potency based on favor sacrifice
    # 1 favor = 1 potency point (Subject to scaling/rebalancing)
    shrine.potency += amount
    
    player.send_line(f"You sacrifice {amount} favor to {shrine.name}. Its presence swells.")
    
    from logic.core.engines import event_engine
    event_engine.dispatch("shrine_potency_boost", shrine=shrine, deity_id=deity_id, amount=amount)
    return True

def can_unlock_class_ability(player, deity_id, cost):
    """Checks if a player has enough favor to unlock an ability."""
    return player.favor.get(deity_id, 0) >= cost

def unlock_class(player, deity_id, cost, class_id):
    """Drains favor to unlock a new class node for the player."""
    if not can_unlock_class_ability(player, deity_id, cost):
        return False
        
    player.favor[deity_id] -= cost
    if class_id not in player.unlocked_classes:
        player.unlocked_classes.append(class_id)
        
    player.send_line(f"{Colors.BOLD}{Colors.YELLOW}You have unlocked the path of the {class_id.title()}!{Colors.RESET}")
    
    from logic.core.engines import event_engine
    event_engine.dispatch("on_class_unlocked", player=player, deity_id=deity_id, class_id=class_id, cost=cost)
    return True
