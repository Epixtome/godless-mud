from utilities.colors import Colors
from utilities import combat_formatter
from models import Monster, Player

def _apply_damage(attacker, target, damage, source_name):
    # Apply Defense
    defense = 0
    if hasattr(target, 'get_defense'):
        defense = target.get_defense()
    elif hasattr(target, 'equipped_armor') and target.equipped_armor:
        defense = target.equipped_armor.defense
    
    # Apply Body Part Multipliers (e.g. Broken Shell)
    multiplier = 1.0
    if hasattr(target, 'get_damage_modifier'):
        multiplier = target.get_damage_modifier()

    final_damage = max(1, int((damage - defense) * multiplier))
    target.hp -= final_damage
    
    # Messaging
    att_msg, tgt_msg, _ = combat_formatter.format_damage(attacker.name, target.name, final_damage, source=source_name)
    attacker.send_line(att_msg)
    if hasattr(target, 'send_line'):
        target.send_line(tgt_msg)
        
    # Death Check (Simplified, relies on next heartbeat to clean up corpse usually, 
    # but we can trigger death logic here if we want instant feedback)
    if target.hp <= 0:
        attacker.send_line(f"{Colors.BOLD}{Colors.YELLOW}You have defeated {target.name}!{Colors.RESET}")
        # Execute death logic immediately
        if isinstance(target, Monster):
            from logic.engines import combat_processor
            combat_processor.handle_mob_death(attacker.game, target, attacker)
        elif isinstance(target, Player):
            from logic.engines import combat_processor
            combat_processor.handle_player_death(attacker.game, target, attacker)
            
        # Clear combat state immediately for the attacker
        if attacker.fighting == target:
            attacker.fighting = None
            attacker.state = "normal"
        return
        
    # Trigger Combat State
    if not attacker.fighting and target.hp > 0:
        attacker.fighting = target
        attacker.state = "combat"
        attacker.send_line(f"{Colors.RED}You attack {target.name}!{Colors.RESET}")
        
    if hasattr(target, 'fighting'):
        if not target.fighting:
            target.fighting = attacker
            if hasattr(target, 'state'): target.state = "combat"
        if attacker not in target.attackers:
            target.attackers.append(attacker)
