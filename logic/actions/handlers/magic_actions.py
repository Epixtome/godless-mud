"""
logic/actions/handlers/magic_actions.py
Magic logic: General Utility, Time, Bardic Songs, and Multi-Class Magic.
"""
import random
import asyncio
from logic.actions.registry import register
from logic.core import effects
from logic.engines import magic_engine, action_manager, blessings_engine
from logic.actions.skill_utils import _apply_damage, handle_dispel_magic
from logic.common import find_by_index, find_player_online, _get_target
from utilities.colors import Colors
from models import Item
from logic import systems, mob_manager

def _consume_resources(player, skill):
    magic_engine.consume_resources(player, skill)
    magic_engine.set_cooldown(player, skill)
    magic_engine.consume_pacing(player, skill)

@register("ray_of_light", "sunbeam")
def handle_ray_of_light(player, skill, args, target=None):
    direction = args.lower() if args else (target if isinstance(target, str) else None)
    if not direction:
        player.send_line("Cast Ray of Light in which direction?")
        return None, True
        
    power = blessings_engine.MathBridge.calculate_power(skill, player)
    player.send_line(f"You fire a {skill.name} to the {direction}!")
    player.room.broadcast(f"{player.name} fires a {skill.name} to the {direction}!", exclude_player=player)
    
    current_room = player.room
    # Pet-safe AOE beam
    for _ in range(2): # Penetrates 2 rooms
        targets = [m for m in current_room.monsters if getattr(m, 'leader', None) != player]
        targets += [p for p in current_room.players if p != player]
        
        for t in targets:
            _apply_damage(player, t, power, skill.name)
            if hasattr(t, 'send_line'):
                t.send_line(f"{Colors.BOLD}{Colors.WHITE}A searing beam of light strikes you!{Colors.RESET}")
        
        if direction in current_room.exits:
            next_room_id = current_room.exits[direction]
            next_room = player.game.world.rooms.get(next_room_id)
            if next_room and next_room != current_room:
                current_room = next_room
                current_room.broadcast(f"{Colors.BOLD}{Colors.WHITE}A beam of light shoots through the room!{Colors.RESET}")
            else:
                break
        else:
            break
            
    _consume_resources(player, skill)
    return None, True

@register("nexus")
def handle_nexus(player, skill, args, target=None):
    if not args:
        player.send_line("Create a nexus to whom?")
        return None, True
        
    target_player = find_player_online(player.game, args)
    if not target_player:
        player.send_line(f"Player '{args}' not found.")
        return None, True
        
    if target_player == player:
        player.send_line("You cannot create a nexus to yourself.")
        return None, True

    player.send_line(f"{Colors.CYAN}You begin channeling a Nexus to {target_player.name}...{Colors.RESET}")
    player.room.broadcast(f"{player.name} begins weaving a shimmering portal.", exclude_player=player)
    target_player.send_line(f"{Colors.CYAN}{player.name} is creating a Nexus to your location!{Colors.RESET}")

    async def _finish_nexus():
        portal = Item("Nexus Portal", f"A swirling portal to {target_player.name}.", value=0)
        portal.flags = ["portal", "nexus", "decay"]
        portal.metadata = {"destination": target_player.room.id}
        portal.timer = 10
        
        player.room.items.append(portal)
        systems.register_decay(player.game, portal, player.room)
        
        player.room.broadcast(f"A {Colors.CYAN}Shimmering Nexus{Colors.RESET} rips open!")

    action_manager.start_action(player, 10.0, _finish_nexus, tag="casting", fail_msg="The Nexus collapses!")
    _consume_resources(player, skill)
    return None, True

@register("song_of_courage", "anthem")
def handle_song_of_courage(player, skill, args, target=None):
    effects.apply_effect(player, "song_courage", 9999, verbose=False)
    
    # Party-wide Buff
    allies = [p for p in player.room.players] + [m for m in player.room.monsters if getattr(m, 'leader', None) == player]
    
    for t in allies:
        effects.apply_effect(t, "buff_courage", 30)
        if hasattr(t, 'send_line'):
            t.send_line(f"{Colors.CYAN}{player.name}'s song fills you with courage!{Colors.RESET}")
            
    player.send_line(f"You begin performing {skill.name}.")
    _consume_resources(player, skill)
    return None, True

@register("space", "temporal")
def handle_temporal(player, skill, args, target=None):
    """Phase shift or temporal effects."""
    if "phase_bubble" in skill.identity_tags:
        effects.apply_effect(player, "phased", 30, verbose=False)
        player.send_line(f"{Colors.CYAN}You shift slightly out of phase with reality.{Colors.RESET}")
        player.room.broadcast(f"{player.name} begins to shimmer and turn translucent.", exclude_player=player)
    return None, True

@register("lullaby")
def handle_lullaby(player, skill, args, target=None):
    player.send_line(f"You play a soothing melody...")
    player.room.broadcast(f"{player.name} plays a soft, sleepy melody.", exclude_player=player)
    
    # Targets enemies only
    targets = [m for m in player.room.monsters if getattr(m, 'leader', None) != player]
    targets += [p for p in player.room.players if p != player]

    for t in targets:
        effects.apply_effect(t, "sleep", 10)
        
    _consume_resources(player, skill)
    return None, True

@register("haste", "accelerate")
def handle_haste(player, skill, args, target=None):
    target = _get_target(player, args, target, "Cast Haste on whom?")
    if not target: return None, True

    effects.apply_effect(target, "haste", 30)
    player.send_line(f"{Colors.CYAN}You accelerate time around {target.name}!{Colors.RESET}")
    _consume_resources(player, skill)
    return target, True

@register("slow", "decelerate")
def handle_slow(player, skill, args, target=None):
    target = _get_target(player, args, target, "Cast Slow on whom?")
    if not target: return None, True

    effects.apply_effect(target, "slow", 20)
    player.send_line(f"{Colors.MAGENTA}You warp time around {target.name}, slowing them down!{Colors.RESET}")
    _consume_resources(player, skill)
    return target, True

@register("refresh")
def handle_refresh(player, skill, args, target=None):
    target = _get_target(player, args, target, "Refresh whom?")
    if not target: return None, True

    power = blessings_engine.MathBridge.calculate_power(skill, player)
    target.resources['stamina'] = min(100, target.resources.get('stamina', 0) + power)
    
    player.send_line(f"You cast {skill.name} on {target.name}, restoring stamina.")
    _consume_resources(player, skill)
    return target, True

@register("haven")
def handle_haven(player, skill, args, target=None):
    haven = Item("Haven", "A shimmering dome of protective magic.", value=0)
    haven.flags = ["magic", "decay", "immobile"]
    haven.timer = 30
    
    player.room.items.append(haven)
    systems.register_decay(player.game, haven, player.room)
    
    player.send_line(f"You erect a {Colors.YELLOW}Haven{Colors.RESET} to block prying eyes.")
    _consume_resources(player, skill)
    return None, True

@register("dispel", "negate")
def handle_dispel(player, skill, args, target=None):
    return handle_dispel_magic(player, skill, args, target)

@register("summon_ifrit", "grand_summon")
def handle_summons(player, skill, args, target=None):
    # Check for existing pet
    existing = next((m for m in player.room.monsters if m.leader == player), None)
    if existing:
        player.send_line(f"You already have a companion: {existing.name}.")
        return None, True

    mob_id = "ifrit" if skill.id == "summon_ifrit" else "grand_eidolon"
    duration = 4.0 if skill.id == "summon_ifrit" else 6.0
    
    player.send_line(f"{Colors.RED}You begin the ritual to summon {mob_id}...{Colors.RESET}")
    player.room.broadcast(f"{player.name} begins a summoning ritual.", exclude_player=player)

    async def _finish():
        minion = mob_manager.spawn_mob(player.room, mob_id, player.game)
        if minion:
            minion.leader = player
            minion.flags.append("pet")
            minion.ai_state = "follow"
            
            # Summoner Bonus
            if getattr(player, 'active_class', None) == "summoner":
                bonus = int(minion.max_hp * 0.30)
                minion.max_hp += bonus
                from logic.core import resources
                resources.modify_resource(minion, "hp", bonus, source="Summoner Bonus")
                player.send_line(f"{Colors.MAGENTA}(Summoner) Your minion rises with empowered vigor!{Colors.RESET}")
            
            player.send_line(f"{minion.name} rises to serve you!")
        else:
            player.send_line(f"Summon failed (Mob '{mob_id}' not found).")

    action_manager.start_action(player, duration, _finish, tag="casting", fail_msg="The ritual is interrupted!")
    _consume_resources(player, skill)
    return None, True

@register("wall_of_fire", "wall_of_force")
def handle_walls(player, skill, args, target=None):
    wall_type = "Wall of Fire" if skill.id == "wall_of_fire" else "Wall of Force"
    color = Colors.RED if skill.id == "wall_of_fire" else Colors.CYAN
    
    wall = Item(wall_type, f"A shimmering {wall_type}.", value=0)
    wall.flags = ["magic", "decay"]
    if skill.id == "wall_of_force":
        wall.flags.append("immobile")
    wall.timer = 10 if skill.id == "wall_of_fire" else 20
    
    player.room.items.append(wall)
    systems.register_decay(player.game, wall, player.room)
    
    player.send_line(f"You conjure a {color}{wall_type}{Colors.RESET}!")
    player.room.broadcast(f"{player.name} conjures a {wall_type}!", exclude_player=player)
    
    _consume_resources(player, skill)
    return None, True

@register("prism")
def handle_prism(player, skill, args, target=None):
    target = _get_target(player, args, target, "Cast Prism on whom?") or player
    
    if player.round_actions.get('prism', 0) >= 1:
        player.send_line("You can only cast Prism once per round.")
        return None, True

    power = blessings_engine.MathBridge.calculate_power(skill, player)
    from logic.core import resources
    resources.modify_resource(target, "hp", power, source=player, context="Prism")
    
    player.send_line(f"You cast Prism on {target.name}, healing them for {power}.")
    
    # Custom Cost Logic (Concentration)
    max_conc = player.get_max_resource('concentration')
    cost = int(max_conc * 0.05)
    player.resources['concentration'] = max(0, player.resources.get('concentration', 0) - cost)
    
    # Manually increment pacing since we bypass standard consume
    player.round_actions['prism'] = player.round_actions.get('prism', 0) + 1
    magic_engine.set_cooldown(player, skill)
    magic_engine.consume_pacing(player, skill)
    
    return target, True
