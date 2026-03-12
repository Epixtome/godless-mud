from utilities.colors import Colors
from utilities import combat_formatter
from models import Monster, Player
from logic.common import find_by_index
from utilities import telemetry
from logic.core import resources, effects

def _apply_damage(attacker, target, damage, source_name, exploit_status=None):
    # Vaulting Evasion Check
    if "vaulting" in getattr(target, 'status_effects', {}):
        attacker.send_line(f"{target.name} is high in the air and cannot be hit!")
        return

    # Final Damage Calculation (pre-resource engine processing)
    raw_damage = max(1, damage)
    
    # --- TACTICAL PHYSICS: High Ground Bonus ---
    if attacker and hasattr(attacker, 'room') and hasattr(target, 'room'):
        att_elev = getattr(attacker.room, 'elevation', 0)
        tgt_elev = getattr(target.room, 'elevation', 0)
        elev_diff = att_elev - tgt_elev
        
        if elev_diff > 0:
            # Advantage: +10% damage per point of elevation diff
            bonus = 1.0 + (elev_diff * 0.10)
            raw_damage = int(raw_damage * bonus)
            attacker.send_line(f"{Colors.GREEN}[High Ground Advantage!]{Colors.RESET}")
        elif elev_diff < 0:
            # Disadvantage: -5% damage per point of elevation diff
            penalty = 1.0 - (abs(elev_diff) * 0.05)
            raw_damage = int(raw_damage * max(0.5, penalty))
            attacker.send_line(f"{Colors.YELLOW}[Attacking from Low Ground]{Colors.RESET}")
    
    # Reveal Attacker if they were hidden (Post-Damage)
    if attacker and hasattr(attacker, 'status_effects') and "concealed" in attacker.status_effects:
        effects.remove_effect(attacker, "concealed")
        attacker.send_line(f"{Colors.YELLOW}You are revealed!{Colors.RESET}")
        if attacker.room:
            attacker.room.broadcast(f"{attacker.name} appears from the shadows!", exclude_player=attacker)
            
    # Telemetry: Log the skill hit
    if attacker:
        telemetry.log_event(attacker, "COMBAT_DETAIL", {
            "target": target.name,
            "final": raw_damage, # Using raw_damage as the final damage reported by this function
            "source": source_name,
            "type": "skill"
        })
    
    # Messaging
    att_name = attacker.name if attacker else "Trap"
    
    if exploit_status:
        att_msg = f"{Colors.BOLD}{Colors.YELLOW}EXPLOIT! You strike {target.name} while they are {exploit_status.upper()} for {raw_damage}!{Colors.RESET}"
        tgt_msg = f"{Colors.RED}{att_name} exploits your {exploit_status} for {raw_damage} damage!{Colors.RESET}"
    else:
        # Use formatting engine for kinetic verbs
        att_msg, tgt_msg, _ = combat_formatter.format_combat_messages(attacker, target, raw_damage)
        
    if attacker: attacker.send_line(att_msg)
    if hasattr(target, 'send_line'):
        target.send_line(tgt_msg)

    # 3. Apply Damage via Resource Engine (Handles events, clamping, and take_damage facade)
    from logic.core import event_engine
    event_engine.dispatch("on_combat_hit", {'attacker': attacker, 'target': target, 'damage': raw_damage})
    
    resources.modify_resource(target, "hp", -raw_damage, source=attacker if attacker else "Effect", context=source_name)
        
    # Trigger Combat State (Auto-retaliate / Aggro) - Only if target is still alive
    if target.hp > 0 and attacker and attacker.room == target.room:
        if not attacker.fighting:
            attacker.fighting = target
            attacker.state = "combat"
            
        if hasattr(target, 'fighting'):
            if not target.fighting:
                target.fighting = attacker
                if hasattr(target, 'state'): target.state = "combat"
            if attacker not in target.attackers:
                target.attackers.append(attacker)

def handle_dispel_magic(player, skill, args, target=None):
    if not args:
        player.send_line("Dispel what?")
        return None, True
        
    # Logic for dispelling items or effects would go here
    player.send_line("You find nothing magical to dispel on that target.")
    return None, True
