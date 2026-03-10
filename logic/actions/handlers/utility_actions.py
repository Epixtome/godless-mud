"""
logic/actions/handlers/utility_actions.py
Utility logic: Tracking, Scouting, Harvesting, and Life support.
"""
import random
from logic.actions.registry import register
from logic.core import event_engine, effects
from logic.engines import blessings_engine, vision_engine
from logic.common import find_by_index, _get_target
from logic import search
from utilities.colors import Colors
from utilities import mapper

def _consume(player, skill):
    from logic.engines import magic_engine
    magic_engine.consume_resources(player, skill)
    magic_engine.set_cooldown(player, skill)
    magic_engine.consume_pacing(player, skill)

@register("track")
def handle_track(player, skill, args, target=None):
    if not args:
        player.send_line("Track what?")
        return None, True
        
    target_obj, dist, direction = search.find_nearby(player.room, args, max_range=5)
    
    if target_obj:
        if dist == 0:
            player.send_line(f"You found tracks! {target_obj.name} is here!")
        else:
            player.send_line(f"You found tracks leading {Colors.CYAN}{direction}{Colors.RESET}. ({dist} rooms away)")
    else:
        player.send_line("You find no tracks matching that description.")

    _consume(player, skill)
    return None, True

@register("farsight", "eagle_eye")
def handle_farsight(player, skill, args, target=None):
    direction = args.lower() if args else None
    if not direction:
        player.send_line("Cast Farsight in which direction?")
        return None, True

    curr = player.room
    steps = 0
    while steps < 10 and direction in curr.exits:
        target_id = curr.exits[direction]
        curr = player.game.world.rooms.get(target_id)
        if not curr: break
        steps += 1
        
    if not curr:
        player.send_line("You cannot see anything in that direction.")
        return None, True

    visible_grid = vision_engine.get_visible_rooms(curr, radius=10, world=player.game.world, check_los=False)
    map_lines = mapper.draw_grid(visible_grid, curr, radius=10, visited_rooms=None, ignore_fog=True)
    
    player.send_line("\n".join(map_lines))
    player.send_line(f"{Colors.CYAN}You project your mind to the {direction}...{Colors.RESET}")
    return None, True

@register("harvest", "gather")
def handle_harvest(player, skill, args, target=None):
    resource_node = None
    if args:
        resource_node = find_by_index(player.room.items, args)
    else:
        for item in player.room.items:
            if hasattr(item, 'flags') and "resource" in item.flags:
                resource_node = item
                break
    
    if not resource_node:
        player.send_line("There is nothing here to harvest.")
        return None, True

    player.send_line(f"You begin harvesting {resource_node.name}...")
    
    async def _finish_harvest():
        player.send_line(f"{Colors.GREEN}You successfully harvest materials from {resource_node.name}.{Colors.RESET}")
        player.send_line(f"{Colors.CYAN}You find some raw materials!{Colors.RESET}")
        
    from logic.engines import action_manager
    action_manager.start_action(player, 3.0, _finish_harvest, tag="harvesting", fail_msg="Harvesting interrupted.")
    _consume(player, skill)
    return None, True

@register("bandage", "first_aid")
def handle_bandage(player, skill, args, target=None):
    target_ent = _get_target(player, args, target, "Bandage whom?")
    if not target_ent: return None, True

    player.send_line(f"You begin applying a bandage to {target_ent.name}...")

    async def _finish_bandage():
        if "bleed" in getattr(target_ent, 'status_effects', {}):
            effects.remove_effect(target_ent, "bleed")
            if hasattr(target_ent, 'send_line'):
                target_ent.send_line(f"{Colors.GREEN}The bleeding stops.{Colors.RESET}")
            
        heal_amt = 25 
        from logic.core import resources
        resources.modify_resource(target_ent, "hp", heal_amt, source=player, context="Bandage")
        player.send_line(f"{Colors.GREEN}You finish bandaging {target_ent.name}. (+{heal_amt} HP){Colors.RESET}")
        
    from logic.engines import action_manager
    action_manager.start_action(player, 5.0, _finish_bandage, tag="bandaging", fail_msg="Bandaging interrupted.")
    _consume(player, skill)
    return None, True

@register("scout")
def handle_scout(player, skill, args, target=None):
    player.send_line(f"{Colors.GREEN}You scout the surroundings...{Colors.RESET}")
    visible_grid = vision_engine.get_visible_rooms(player.room, radius=3, world=player.game.world, check_los=True)
    
    for (rx, ry), room in visible_grid.items():
        if rx == 0 and ry == 0: continue
        if room.monsters or room.players:
            entities = [m.name for m in room.monsters] + [p.name for p in room.players if p != player]
            player.send_line(f"[{rx}, {ry}] {room.name}: {Colors.RED}{', '.join(entities)}{Colors.RESET}")
            
    _consume(player, skill)
    return None, True

@register("analyze")
def handle_analyze(player, skill, args, target=None):
    target_ent = _get_target(player, args, target, "Analyze whom?")
    if not target_ent: return None, True

    player.send_line(f"{Colors.CYAN}--- Analysis: {target_ent.name} ---{Colors.RESET}")
    player.send_line(f"HP: {target_ent.hp}/{target_ent.max_hp}")
    if hasattr(target_ent, 'tags'):
        player.send_line(f"Tags: {', '.join(target_ent.tags or [])}")
    if hasattr(target_ent, 'status_effects'):
        player.send_line(f"Status: {', '.join(target_ent.status_effects.keys())}")
        
    _consume(player, skill)
    return None, True

@register("smoke_bomb")
def handle_smoke_bomb(player, skill, args, target=None):
    player.room.broadcast(f"{Colors.WHITE}{player.name} smashes a smoke bomb! Thick smoke fills the room!{Colors.RESET}", exclude_player=None)
    
    from logic.core import combat
    for entity in player.room.players + player.room.monsters:
        if entity.fighting:
            combat.stop_combat(entity)
            if hasattr(entity, 'send_line'):
                entity.send_line(f"{Colors.YELLOW}Combat is interrupted by the smoke!{Colors.RESET}")
    
    _consume(player, skill)
    return None, True

@register("howl", "beast_master")
def handle_howl(player, skill, args, target=None):
    player.room.broadcast(f"{player.name} lets out a piercing howl!", exclude_player=player)
    _consume(player, skill)
    return None, True
