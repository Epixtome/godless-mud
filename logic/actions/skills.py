import logic.command_manager as command_manager
from logic.engines import blessings_engine
from logic.engines import magic_engine
from logic.engines import status_effects_engine
from logic import search
from utilities.colors import Colors
from logic.common import find_by_index
from logic.actions import handlers as skill_handlers


# REGISTRY: Maps a specific tag to a handler function.
# The order matters less here, as we look for the *first matching tag* in the skill.
SKILL_DISPATCH = {
    "backstab": skill_handlers.handle_backstab,
    "marksmanship": skill_handlers.handle_marksmanship,
    "track": skill_handlers.handle_scout,
    "thievery": skill_handlers.handle_thievery,
    "poison": skill_handlers.handle_poison,
    "alchemy": skill_handlers.handle_alchemy,
    "raise_dead": skill_handlers.handle_necromancy,
    "howl": skill_handlers.handle_beast_master,
    "space": skill_handlers.handle_temporal,
    "shield": skill_handlers.handle_shield_bash,
    "rescue": skill_handlers.handle_rescue,
    "sunder": skill_handlers.handle_sunder,
    "pommel_strike": skill_handlers.handle_pommel_strike,
    "trip": skill_handlers.handle_trip,
    "drag": skill_handlers.handle_drag,
    "push": skill_handlers.handle_push,
    "fear": skill_handlers.handle_scare,
    "struggle": skill_handlers.handle_struggle,
    # Generic handlers
    "buff": skill_handlers.handle_buff,
    "rage": skill_handlers.handle_buff,
}

def try_execute_skill(player, command_line):
    """
    Parses input to see if it matches an equipped skill (blessing).
    Syntax: <skill_name> [target/direction]
    Example: "kick goblin", "flask_toss north", "snipe"
    """
    parts = command_line.split()
    trigger = parts[0].lower()
    args = " ".join(parts[1:]) if len(parts) > 1 else ""
    
    # Find blessing by name in equipped list
    # Support fuzzy matching (e.g. "charge" -> "mounted_charge")
    skill = None
    candidates = []
    for b_id in player.equipped_blessings:
        b = player.game.world.blessings.get(b_id)
        if b:
            # Ensure it is actually a skill (not a spell like Farsight)
            if "skill" not in b.identity_tags:
                continue

            b_name = b.name.lower().replace(" ", "_")
            if b_name == trigger:
                skill = b
                break
            elif trigger in b_name:
                candidates.append(b)
    
    if not skill and len(candidates) == 1:
        skill = candidates[0]
            
    if not skill:
        return False

    # It's a skill! Execute it.
    _execute_skill(player, skill, args)
    return True

def _execute_skill(player, skill, args):
    # 1. Validation (Auditor)
    can_cast, reason = blessings_engine.Auditor.can_invoke(skill, player)
    if not can_cast:
        player.send_line(reason)
        return

    # 1.5 Pacing Check (Actions per Round)
    can_pace, reason_pace = magic_engine.check_pacing(player, skill)
    if not can_pace:
        player.send_line(reason_pace)
        return

    # 2. Dispatch
    target = None
    handled = False

    # Optimized Dispatch: Check tags against the registry
    # This avoids creating 20+ lambda functions every time a skill is used.
    for tag, handler_func in SKILL_DISPATCH.items():
        if tag in skill.identity_tags:
            # Special case for alchemy which needed two tags in the old code
            if tag == "alchemy" and "ranged" not in skill.identity_tags:
                continue
                
            t_ent, stop = handler_func(player, skill, args)
            if stop:
                return
            if t_ent:
                target = t_ent
                handled = True
            
            # If the handler applied its own damage and resources, stop now.
            if stop:
                return

            break

    # 2.5 Handle AoE Skills (Stomp, Whirl) - Checked BEFORE single target validation
    if "aoe" in skill.identity_tags and ("stomp" in skill.identity_tags or "whirl" in skill.identity_tags):
        power = blessings_engine.MathBridge.calculate_power(skill, player)
        targets = [m for m in player.room.monsters] + [p for p in player.room.players if p != player]
        
        if not targets:
            player.send_line("There is no one else here.")
            return
            
        for t in targets:
            skill_handlers._apply_damage(player, t, power, skill.name)
            if "stomp" in skill.identity_tags:
                status_effects_engine.apply_effect(t, "stun", 4)
                if hasattr(t, 'send_line'):
                    t.send_line(f"{Colors.YELLOW}You are stunned by the impact!{Colors.RESET}")
        
        return # AoE handled

    # Standard Melee/Room Targeting (Default)
    if not handled and not target:
        if args:
            target = find_by_index(player.room.monsters + player.room.players, args)
            if not target:
                player.send_line("You don't see them here.")
                return
        elif player.fighting:
            target = player.fighting
        else:
            player.send_line("Use skill on whom?")
            return

    # 3. Apply Effects
    # Calculate Power
    power = blessings_engine.MathBridge.calculate_power(skill, player)

    # Handle Single Target
    if target:
        # Prevent damage if it's a utility/buff skill that fell through
        if any(tag in skill.identity_tags for tag in ["buff", "utility", "passive", "protection", "aura"]):
            player.send_line(f"You use {skill.name}.")
        else:
            skill_handlers._apply_damage(player, target, power, skill.name)
        
    # If a specific handler already dealt with resources, don't double-dip
    # This is implicitly handled by handlers returning stop=True
    if handled:
        return

    # 4. Consume Resources & Cooldown
    magic_engine.consume_resources(player, skill)
    magic_engine.set_cooldown(player, skill)
    magic_engine.consume_pacing(player, skill)
    
    # Chi Generation
    if "chi_builder" in skill.identity_tags:
        player.resources['chi'] = min(5, player.resources.get('chi', 0) + 1)
        player.send_line(f"{Colors.YELLOW}You gain 1 Chi.{Colors.RESET}")