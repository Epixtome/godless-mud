"""
logic/actions/handlers/utility_actions.py
Utility logic: Tracking, Traps, Locks, Harvesting.
"""
import random
from logic.actions.registry import register
from logic.core import event_engine
from logic.engines import action_manager, magic_engine, vision_engine, blessings_engine
from logic.common import find_by_index, _get_target
from logic import search
from utilities.colors import Colors
from utilities import mapper

def _consume(player, skill):
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

@register("pick_lock", "pick")
def handle_pick_lock(player, skill, args, target=None):
    if not args:
        player.send_line("Pick what?")
        return None, True

    target_obj = None
    direction = args.lower()
    if direction in player.room.doors:
        target_obj = player.room.doors[direction]
    else:
        target_obj = find_by_index(player.room.items + player.inventory, args)

    if not target_obj or getattr(target_obj, 'state', None) != 'locked':
        player.send_line("That is not locked.")
        return None, True

    player.send_line(f"You begin picking the lock on {target_obj.name}...")

    async def _finish_pick():
        base_chance = blessings_engine.MathBridge.calculate_power(skill, player)
        
        if random.randint(1, 100) <= base_chance:
            target_obj.state = 'closed'
            player.send_line(f"{Colors.GREEN}Click! You successfully pick the lock.{Colors.RESET}")
        else:
            player.send_line(f"{Colors.RED}You fail to pick the lock.{Colors.RESET}")

    action_manager.start_action(player, 4.0, _finish_pick, tag="picking", fail_msg="Lockpicking interrupted.")
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
        curr = curr.exits[direction]
        steps += 1
        
    visible_grid = vision_engine.get_visible_rooms(curr, radius=10, world=player.game.world, check_los=False)
    map_lines = mapper.draw_grid(visible_grid, curr, radius=10, visited_rooms=None, ignore_fog=True)
    
    player.send_line("\n".join(map_lines))
    player.send_line(f"{Colors.CYAN}You project your mind to the {direction}...{Colors.RESET}")
    return None, True

@register("thievery", "steal", "pickpocket")
def handle_thievery(player, skill, args, target=None):
    target = find_by_index(player.room.monsters + player.room.players, args)
    if not target:
        player.send_line("Steal from whom?")
        return None, True
        
    if target == player:
        player.send_line("You can't steal from yourself.")
        return None, True

    # Calculate Chance
    base_chance = blessings_engine.MathBridge.calculate_power(skill, player)
    
    ctx = {'player': player, 'target': target, 'chance': base_chance, 'skill': skill}
    event_engine.dispatch("calculate_steal_chance", ctx)
    
    if random.randint(1, 100) <= ctx['chance']:
        gold_stolen = random.randint(1, 10) + 10 # Standardized base gold
        if hasattr(target, 'gold') and target.gold > 0:
            actual_gold = min(target.gold, gold_stolen)
            target.gold -= actual_gold
            player.gold += actual_gold
            player.send_line(f"{Colors.GREEN}You deftly swipe {actual_gold} gold from {target.name}.{Colors.RESET}")
        else:
            player.send_line(f"You search {target.name}'s pockets but find nothing of value.")
    else:
        player.send_line(f"{Colors.RED}You are caught trying to steal from {target.name}!{Colors.RESET}")
        if hasattr(target, 'fighting') and not target.fighting:
            target.fighting = player
            target.state = "combat"
            if player not in target.attackers:
                target.attackers.append(player)
            player.room.broadcast(f"{target.name} attacks {player.name}!", exclude_player=player)

    _consume(player, skill)
    return None, True

@register("decoy")
def handle_decoy(player, skill, args, target=None):
    from models import Monster
    
    # Tool Check (Simplified for now)
    has_kit = any("kit" in item.name.lower() for item in player.inventory)
    if not has_kit and not getattr(player, 'godmode', False):
        player.send_line("You need an assassin's kit to construct a decoy.")
        return None, True

    decoy = Monster(f"Decoy of {player.name}", f"A crude wooden dummy dressed like {player.name}.", 50, 0, tags=["construct", "decoy"], max_hp=50, game=player.game)
    decoy.room = player.room
    decoy.temporary = True
    player.room.monsters.append(decoy)
    
    player.send_line(f"{Colors.CYAN}You deploy a decoy and slip away!{Colors.RESET}")
    player.room.broadcast(f"{player.name} deploys a decoy!", exclude_player=player)

    # Redirect Aggro
    for mob in player.room.monsters:
        if mob.fighting == player:
            mob.fighting = decoy
            if player in mob.attackers: mob.attackers.remove(player)
            mob.attackers.append(decoy)
            decoy.attackers.append(mob)
            
    player.fighting = None
    player.state = "normal"
    
    _consume(player, skill)
    return None, True

@register("deploy_turret", "turret")
def handle_deploy_turret(player, skill, args, target=None):
    from logic import mob_manager
    turrets = [m for m in player.room.monsters if m.leader == player and "turret" in m.tags]
    if len(turrets) >= 1:
        player.send_line("You already have a turret deployed here.")
        return None, True

    player.send_line(f"You begin assembling a turret...")
    player.room.broadcast(f"{player.name} starts building a contraption.", exclude_player=player)

    async def _finish_deploy():
        turret = mob_manager.spawn_mob(player.room, "turret", player.game)
        if turret:
            turret.leader = player
            turret.flags.append("pet")
            turret.ai_state = "guard" 
            player.send_line(f"{Colors.GREEN}Turret deployed!{Colors.RESET}")

    action_manager.start_action(player, 4.0, _finish_deploy, tag="crafting", fail_msg="Construction interrupted.")
    _consume(player, skill)
    return None, True

@register("flask_toss", "alchemy")
def handle_flask_toss(player, skill, args, target=None):
    # AoE Logic
    player.send_line(f"You hurl {skill.name}!")
    player.room.broadcast(f"{player.name} hurls a flask!", exclude_player=player)
    
    power = blessings_engine.MathBridge.calculate_power(skill, player)
    targets = [m for m in player.room.monsters] + [p for p in player.room.players if p != player]
    
    from logic.actions.skill_utils import _apply_damage
    for t in targets:
        _apply_damage(player, t, power, skill.name)

    _consume(player, skill)
    return None, True

@register("repair")
def handle_repair(player, skill, args, target=None):
    target = _get_target(player, args, target, "Repair what?")
    if not target: return None, True
        
    if "construct" not in getattr(target, 'tags', []):
        player.send_line(f"{target.name} is not a machine.")
        return None, True
        
    heal = 30 # Standardized base heal
    target.hp = min(target.max_hp, target.hp + heal)
    player.send_line(f"You repair {target.name} for {heal} HP.")
    
    _consume(player, skill)
    return target, True

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
        
    action_manager.start_action(player, 3.0, _finish_harvest, tag="harvesting", fail_msg="Harvesting interrupted.")
    _consume(player, skill)
    return None, True

@register("bandage", "first_aid")
def handle_bandage(player, skill, args, target=None):
    target = _get_target(player, args, target, "Bandage whom?")
    if not target: return None, True

    player.send_line(f"You begin applying a bandage to {target.name}...")

    async def _finish_bandage():
        from logic.core.engines import status_effects_engine
        if "bleed" in target.status_effects:
            status_effects_engine.remove_effect(target, "bleed")
            target.send_line(f"{Colors.GREEN}The bleeding stops.{Colors.RESET}")
            
        heal_amt = 25 # Standardized base heal
        target.hp = min(target.max_hp, target.hp + heal_amt)
        player.send_line(f"{Colors.GREEN}You finish bandaging {target.name}. (+{heal_amt} HP){Colors.RESET}")
        
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

@register("howl", "beast_master")
def handle_howl(player, skill, args, target=None):
    player.room.broadcast(f"{player.name} lets out a piercing howl!", exclude_player=player)
    _consume(player, skill)
    return None, True

@register("transmute")
def handle_transmute(player, skill, args, target=None):
    if not args:
        player.send_line("Transmute what?")
        return None, True
        
    item = find_by_index(player.inventory, args)
    if not item:
        player.send_line("You aren't carrying that.")
        return None, True
        
    value = item.value
    if value <= 0:
        player.send_line(f"You cannot transmute {item.name}, it has no value.")
        return None, True
        
    multiplier = 1.5 if getattr(player, 'active_class', None) == 'alchemist' else 1.0
    gold_gain = int(value * multiplier)
    
    player.inventory.remove(item)
    player.gold += gold_gain
    
    player.send_line(f"{Colors.YELLOW}You transmute {item.name} into {gold_gain} gold!{Colors.RESET}")
    _consume(player, skill)
    return None, True

@register("disarm_trap", "disable_trap")
def handle_disarm_trap(player, skill, args, target=None):
    target = find_by_index(player.room.items, args)
    if not target or "trap" not in getattr(target, 'flags', []):
        player.send_line("Disarm what?")
        return None, True

    player.send_line(f"You carefully attempt to disarm {target.name}...")
    
    async def _finish_disarm():
        if target in player.room.items:
            player.room.items.remove(target)
            player.send_line(f"{Colors.GREEN}You have successfully disarmed {target.name}.{Colors.RESET}")

    action_manager.start_action(player, 3.0, _finish_disarm, tag="disarming", fail_msg="Disarm interrupted.")
    _consume(player, skill)
    return None, True

@register("analyze")
def handle_analyze(player, skill, args, target=None):
    target = _get_target(player, args, target, "Analyze whom?")
    if not target: return None, True

    player.send_line(f"{Colors.CYAN}--- Analysis: {target.name} ---{Colors.RESET}")
    player.send_line(f"HP: {target.hp}/{target.max_hp}")
    if hasattr(target, 'tags'):
        player.send_line(f"Tags: {', '.join(target.tags)}")
    if hasattr(target, 'status_effects'):
        player.send_line(f"Status: {', '.join(target.status_effects.keys())}")
        
    _consume(player, skill)
    return None, True

@register("weapon_oil", "infuse_gear")
def handle_gear_buffs(player, skill, args, target=None):
    if skill.id == "weapon_oil" and not player.equipped_weapon:
        player.send_line("You need a weapon equipped.")
        return None, True
    if skill.id == "infuse_gear" and not player.equipped_armor:
        player.send_line("You need armor equipped.")
        return None, True
        
    status_effects_engine.apply_effect(player, skill.id, 60, verbose=False)
    player.send_line(f"{Colors.CYAN}You apply {skill.name} to your gear.{Colors.RESET}")
    _consume(player, skill)
    return None, True

@register("philosophers_stone")
def handle_philosophers_stone(player, skill, args, target=None):
    player.send_line(f"{Colors.YELLOW}You invoke the power of the Philosopher's Stone!{Colors.RESET}")
    player.room.broadcast(f"{player.name} glows with a blinding golden light!", exclude_player=player)
    
    player.hp = player.max_hp
    if hasattr(player, 'get_max_resource'):
        player.resources['stamina'] = player.get_max_resource('stamina')
        player.resources['concentration'] = player.get_max_resource('concentration')
    
    _consume(player, skill)
    return None, True

@register("smoke_bomb")
def handle_smoke_bomb(player, skill, args, target=None):
    player.room.broadcast(f"{Colors.WHITE}{player.name} smashes a smoke bomb! Thick smoke fills the room!{Colors.RESET}", exclude_player=None)
    
    for entity in player.room.players + player.room.monsters:
        if entity.fighting:
            entity.fighting = None
            if hasattr(entity, 'state'): entity.state = "normal"
            if hasattr(entity, 'attackers'): entity.attackers = []
            if hasattr(entity, 'send_line'):
                entity.send_line(f"{Colors.YELLOW}Combat is interrupted by the smoke!{Colors.RESET}")
    
    _consume(player, skill)
    return None, True

@register("trap_net", "trap_fire", "trap_stamina", "trap_sense")
def handle_traps(player, skill, args, target=None):
    trap_type = skill.id.replace("trap_", "")
    
    from models import Item
    from logic import systems
    
    trap = Item(f"{trap_type} trap", f"A concealed {trap_type} trap.", value=0)
    trap.flags = ["trap", "immobile", "decay"]
    trap.metadata = {"type": trap_type, "owner_id": player.name}
    trap.timer = 50
    
    player.room.items.append(trap)
    systems.register_decay(player.game, trap, player.room)
    
    player.send_line(f"You carefully place a {trap_type} trap.")
    player.room.broadcast(f"{player.name} places a trap on the ground.", exclude_player=player)
    
    _consume(player, skill)
    return None, True
