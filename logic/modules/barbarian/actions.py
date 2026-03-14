import random
from logic.core import effects, combat
from utilities.colors import Colors
from logic.actions.registry import register
from logic.actions.skill_utils import _apply_damage
from logic.engines import magic_engine, blessings_engine

def _consume_resources(player, skill):
    magic_engine.consume_resources(player, skill)
    magic_engine.set_cooldown(player, skill)
    magic_engine.consume_pacing(player, skill)

@register("bash")
def bash(attacker, skill, args, target=None):
    """Opener: Stuns the target."""
    from logic.common import _get_target
    target = _get_target(attacker, args, target, "Bash whom?")
    if not target: return None, True
    
    # Flavor line removed to prevent double-messaging with combat_processor
    
    # Delegate to processor for damage and on_hit (stun/balance)
    from logic.engines import combat_processor
    prompts = set()
    combat_processor.execute_attack(attacker, target, attacker.room, attacker.game, prompts, blessing=skill)
    
    _consume_resources(attacker, skill)
    return target, True

@register("dirt_kick")
def dirt_kick(attacker, skill, args, target=None):
    """Debuff: Blinds the target."""
    from logic.common import _get_target
    target = _get_target(attacker, args, target, "Kick dirt at whom?")
    if not target: return None, True
    
    attacker.send_line(f"{Colors.YELLOW}You kick a cloud of grit into {target.name}'s eyes!{Colors.RESET}")
    
    # Apply on_hit effects (blinded)
    blessings_engine.apply_on_hit(attacker, target, skill)
    
    _consume_resources(attacker, skill)
    return target, True

@register("drag")
def drag(attacker, skill, args, target=None):
    """Utility: Moves attacker and target to a connected room."""
    # Parse target and direction (e.g., "drag rat west")
    target_query = args
    direction = None
    if args and " " in args:
        parts = args.split()
        if len(parts) > 1 and parts[-1].lower() in attacker.room.exits:
            direction = parts[-1].lower()
            target_query = " ".join(parts[:-1])

    from logic.core import search
    target = search.find_living(attacker.room, target_query) if target_query else target
    if not target:
        attacker.send_line("Drag whom?")
        return None, True
    
    if not attacker.room: return None, True
    
    exits = attacker.room.exits
    if not exits:
        attacker.send_line("There's nowhere to drag them!")
        return None, True
        
    # Use specified direction or pick a random one
    if not direction or direction not in exits:
        direction = random.choice(list(exits.keys()))
    destination_id = exits[direction]
    
    attacker.send_line(f"{Colors.BOLD}{Colors.YELLOW}You grab {target.name} and drag them {direction}!{Colors.RESET}")
    target.send_line(f"{Colors.BOLD}{Colors.RED}{attacker.name} grabs you and drags you {direction}!{Colors.RESET}")
    
    # Broadcast to old room
    attacker.room.broadcast(f"{attacker.name} drags {target.name} out to the {direction}!", exclude_ids=[attacker.name, target.name])
    
    # Move them
    from logic.core.services import world_service
    target_room = attacker.game.world.rooms.get(destination_id)
    if target_room:
        world_service.move_entity(attacker, target_room)
        world_service.move_entity(target, target_room)
        
        # Broadcast to new room
        target_room.broadcast(f"{attacker.name} drags {target.name} into the room from the opposite side!", exclude_ids=[attacker.name, target.name])
        attacker.send_line(target_room.description) # Trigger a look
    else:
        attacker.send_line("The trail goes cold. You couldn't drag them there.")
    
    _consume_resources(attacker, skill)
    return target, True

@register("whirlwind")
def whirlwind(attacker, skill, args, target=None):
    """AOE: Consumes 50 Fury for massive damage."""
    attacker.send_line(f"{Colors.BOLD}{Colors.RED}You enter a cyclone of steel!{Colors.RESET}")
    
    # Calculate power once
    power = blessings_engine.calculate_power(skill, attacker, None)
    
    # Get all targets in room
    targets = [m for m in attacker.room.monsters if m != attacker]
    if not targets:
        attacker.send_line("There is no one here to strike.")
        return None, True
        
    for t in targets:
        if t.hp <= 0: continue
        # Initiate combat so they retaliate
        combat.start_combat(attacker, t)
        
        # Apply pre-calculated power
        attacker.send_line(f"Your whirlwind strikes {t.name} for {Colors.RED}{power}{Colors.RESET}!")
        combat.apply_damage(t, power, source=attacker, context="Whirlwind")

    _consume_resources(attacker, skill)
    return None, True

@register("struggle")
def struggle(attacker, skill, args, target=None):
    """Utility: Instantly break free from nets or similar CC."""
    if not effects.has_effect(attacker, "net"):
        attacker.send_line("You are not entangled in anything.")
        return None, True

    attacker.send_line(f"{Colors.BOLD}{Colors.YELLOW}With a primal roar, you tear the net apart!{Colors.RESET}")
    attacker.room.broadcast(f"{attacker.name} rips through the netting with brute strength!", exclude_player=attacker)
    
    effects.remove_effect(attacker, "net")
    
    _consume_resources(attacker, skill)
    return None, True

@register("bloodrage")
def bloodrage(attacker, skill, args, target=None):
    """Ultimate: Consumes 100 Fury to enter Rage Mode."""
    attacker.send_line(f"{Colors.BOLD}{Colors.RED}YOUR BLOOD BOILS! YOU ARE UNSTOPPABLE!{Colors.RESET}")
    attacker.room.broadcast(f"{Colors.BOLD}{Colors.RED}{attacker.name} screams in primal fury as their muscles swell!{Colors.RESET}", exclude_player=attacker)
    
    # Use generic executor to apply status effects and consume resources from JSON
    from logic.actions.base_executor import execute as handle_generic
    handle_generic(attacker, skill, args, target=attacker)
    return None, True
