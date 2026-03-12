"""
logic/core/systems/engagement.py
Centralized service for managing combatant relationships (aggro, retaliation, and social social hooks).
Decouples Execution from Communication.
"""
import logging
from models import Monster, Player
from logic.core import event_engine
from utilities.colors import Colors

logger = logging.getLogger("GodlessMUD")

def handle_engagement(ctx):
    """
    Subscribed to 'on_combat_hit'.
    Ensures that both sides of a combat exchange are aware of each other.
    """
    attacker = ctx.get('attacker')
    target = ctx.get('target')
    damage = ctx.get('damage', 0)
    
    if not attacker or not target:
        return
        
    # 1. Basic Symmetrical Update
    # Ensure attacker is in target's attackers list
    if hasattr(target, 'attackers') and attacker not in target.attackers:
        target.attackers.append(attacker)
        
    # 2. Reactive Engagement (Aggro)
    # If the target is not currently fighting, they turn to face the attacker
    if hasattr(target, 'fighting') and not target.fighting:
        # Check for "Practice Dummy" gate
        tags = getattr(target, 'tags', [])
        is_dummy = "training_dummy" in tags or ("target" in tags and "elite" not in tags and "tactical" not in tags)
        
        if not is_dummy:
            target.fighting = attacker
            if hasattr(target, 'state'):
                target.state = "combat"
                
            # Social Feedback
            if isinstance(target, Monster):
                if hasattr(target, 'room') and target.room:
                    target.room.broadcast(f"{Colors.YELLOW}{target.name} turns to engage {attacker.name}!{Colors.RESET}")
            elif isinstance(target, Player):
                target.send_line(f"{Colors.RED}*** {attacker.name.upper()} HAS ENGAGED YOU IN COMBAT! ***{Colors.RESET}")

    # 3. Social Aggro (Allies in the room)
    if isinstance(target, Monster) and hasattr(target, 'room') and target.room:
        # Find allies (mobs of same family or tagged as 'loyal')
        # This is a placeholder for future AI expansion (Social Pillar)
        pass

def initialize():
    """Registers engagement hooks with the event engine."""
    event_engine.subscribe("on_combat_hit", handle_engagement)
    logger.info("Engagement System initialized.")
