"""
logic/actions/handlers/thievery_actions.py
Skills related to Thievery: Stealing, Pickpocketing, Lockpicking, and Disarming.
"""
import random
from logic.actions.registry import register
from logic.core import event_engine
from logic.engines import blessings_engine, action_manager
from logic.common import find_by_index
from utilities.colors import Colors

def _consume(player, skill):
    from logic.engines import magic_engine
    magic_engine.consume_resources(player, skill)
    magic_engine.set_cooldown(player, skill)
    magic_engine.consume_pacing(player, skill)

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

@register("thievery", "steal", "pickpocket")
def handle_thievery(player, skill, args, target=None):
    target_ent = find_by_index(player.room.monsters + player.room.players, args)
    if not target_ent:
        player.send_line("Steal from whom?")
        return None, True
        
    if target_ent == player:
        player.send_line("You can't steal from yourself.")
        return None, True

    base_chance = blessings_engine.MathBridge.calculate_power(skill, player)
    ctx = {'player': player, 'target': target_ent, 'chance': base_chance, 'skill': skill}
    event_engine.dispatch("calculate_steal_chance", ctx)
    
    if random.randint(1, 100) <= ctx['chance']:
        gold_stolen = random.randint(1, 10) + 10 
        if hasattr(target_ent, 'gold') and target_ent.gold > 0:
            actual_gold = min(target_ent.gold, gold_stolen)
            target_ent.gold -= actual_gold
            player.gold += actual_gold
            player.send_line(f"{Colors.GREEN}You deftly swipe {actual_gold} gold from {target_ent.name}.{Colors.RESET}")
        else:
            player.send_line(f"You search {target_ent.name}'s pockets but find nothing of value.")
    else:
        player.send_line(f"{Colors.RED}You are caught trying to steal from {target_ent.name}!{Colors.RESET}")
        from logic.core import combat
        combat.start_combat(target_ent, player) if not target_ent.fighting else None
        player.room.broadcast(f"{target_ent.name} attacks {player.name}!", exclude_player=player)

    _consume(player, skill)
    return None, True

@register("disarm_trap", "disable_trap")
def handle_disarm_trap(player, skill, args, target=None):
    target_obj = find_by_index(player.room.items, args)
    if not target_obj or "trap" not in getattr(target_obj, 'flags', []):
        player.send_line("Disarm what?")
        return None, True

    player.send_line(f"You carefully attempt to disarm {target_obj.name}...")
    
    async def _finish_disarm():
        if target_obj in player.room.items:
            player.room.items.remove(target_obj)
            player.send_line(f"{Colors.GREEN}You have successfully disarmed {target_obj.name}.{Colors.RESET}")

    action_manager.start_action(player, 3.0, _finish_disarm, tag="disarming", fail_msg="Disarm interrupted.")
    _consume(player, skill)
    return None, True
