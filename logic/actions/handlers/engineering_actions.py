"""
logic/actions/handlers/engineering_actions.py
Skills related to Engineering: Turrets, Decoys, Repair, and Traps.
"""
from logic.actions.registry import register
from logic.core import mob_manager, systems
from logic.engines import action_manager
from logic.common import _get_target
from models import Monster, Item
from utilities.colors import Colors

def _consume(player, skill):
    from logic.engines import magic_engine
    magic_engine.consume_resources(player, skill)
    magic_engine.set_cooldown(player, skill)
    magic_engine.consume_pacing(player, skill)

@register("decoy")
def handle_decoy(player, skill, args, target=None):
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
            turret.tags.append("pet")
            turret.ai_state = "guard" 
            player.send_line(f"{Colors.GREEN}Turret deployed!{Colors.RESET}")

    action_manager.start_action(player, 4.0, _finish_deploy, tag="crafting", fail_msg="Construction interrupted.")
    _consume(player, skill)
    return None, True

@register("repair")
def handle_repair(player, skill, args, target=None):
    target_obj = _get_target(player, args, target, "Repair what?")
    if not target_obj: return None, True
        
    if "construct" not in getattr(target_obj, 'tags', []):
        player.send_line(f"{target_obj.name} is not a machine.")
        return None, True
        
    heal = 30 
    from logic.core import resources
    resources.modify_resource(target_obj, "hp", heal, source=player, context="Repair")
    player.send_line(f"You repair {target_obj.name} for {heal} HP.")
    
    _consume(player, skill)
    return target_obj, True

@register("trap_net", "trap_fire", "trap_stamina", "trap_sense")
def handle_traps(player, skill, args, target=None):
    trap_type = skill.id.replace("trap_", "")
    
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
