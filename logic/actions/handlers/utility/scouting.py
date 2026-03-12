"""
logic/actions/handlers/utility/scouting.py
Vision and Intel skills: Scout, Track, Analyze, and Farsight.
"""
from logic.actions.registry import register
from logic.engines import vision_engine
from logic.common import _get_target
from logic.core import search
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
