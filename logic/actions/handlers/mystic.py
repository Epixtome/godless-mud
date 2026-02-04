from logic import mob_manager
from utilities.colors import Colors
from models import Corpse
from .common import _apply_damage
from logic.common import find_by_index

def handle_buff(player, skill, args):
    """Handles self-buffs like Rage or Stone Skin."""
    from logic.engines import magic_engine, status_effects_engine
    if "rage" in skill.identity_tags:
        status_effects_engine.apply_effect(player, "berserk_rage", 20, verbose=False)
        player.send_line(f"{Colors.RED}You roar with primal fury!{Colors.RESET}")
        player.room.broadcast(f"{player.name} roars with primal fury!", exclude_player=player)
    elif "stone_skin" in skill.identity_tags:
        status_effects_engine.apply_effect(player, "stone_skin", 60, verbose=False)
        player.send_line(f"{Colors.GREEN}Your skin hardens into impenetrable rock!{Colors.RESET}")
        player.room.broadcast(f"{player.name}'s skin turns grey and stony.", exclude_player=player)
    elif "crane_stance" in skill.identity_tags:
        status_effects_engine.apply_effect(player, "crane_stance", 60, verbose=False)
        player.send_line(f"{Colors.CYAN}You shift into the Crane Stance.{Colors.RESET}")
        player.room.broadcast(f"{player.name} assumes a graceful, defensive posture.", exclude_player=player)
    elif "defensive_stance" in skill.identity_tags:
        status_effects_engine.apply_effect(player, "defensive_stance", 60, verbose=False)
        player.send_line(f"{Colors.YELLOW}You raise your guard, entering a Defensive Stance.{Colors.RESET}")
        player.room.broadcast(f"{player.name} adopts a guarded combat posture.", exclude_player=player)
    elif "venom_coat" in skill.identity_tags:
        status_effects_engine.apply_effect(player, "venom_coat", 60, verbose=False)
        player.send_line(f"{Colors.GREEN}You coat your weapon in vile toxins.{Colors.RESET}")
        player.room.broadcast(f"{player.name} coats their weapon in poison.", exclude_player=player)
    
    # Buffs consume resources immediately upon application
    magic_engine.consume_resources(player, skill)
    magic_engine.set_cooldown(player, skill)
    magic_engine.consume_pacing(player, skill)
    return None, True

def handle_alchemy(player, skill, args):
    from logic.engines import blessings_engine, magic_engine
    direction = args.lower()
    if direction in player.room.exits:
        target_room = player.room.exits[direction]
        player.send_line(f"You hurl {skill.name} to the {direction}!")
        player.room.broadcast(f"{player.name} hurls a flask to the {direction}!", exclude_player=player)
    elif not direction:
        player.send_line(f"You smash {skill.name} on the ground!")
        player.room.broadcast(f"{player.name} smashes a flask on the ground!", exclude_player=player)
        target_room = player.room
    else:
        player.send_line("Invalid direction.")
        return None, True

    # Apply AoE Damage immediately
    power = blessings_engine.MathBridge.calculate_power(skill, player)
    targets = target_room.monsters + [p for p in target_room.players if p != player]
    
    if not targets:
        player.send_line("The flask explodes harmlessly.")
        if target_room != player.room:
            target_room.broadcast(f"A flask flies in and explodes!")
    else:
        for t in targets:
            _apply_damage(player, t, power, skill.name)
            if target_room != player.room:
                if hasattr(t, 'send_line'):
                    t.send_line(f"{Colors.RED}A flask flies in from nowhere! You take {power} damage!{Colors.RESET}")
        
        if target_room != player.room:
            target_room.broadcast(f"A flask thrown by {player.name} explodes!", exclude_player=player)

    magic_engine.consume_resources(player, skill)
    magic_engine.set_cooldown(player, skill)
    magic_engine.consume_pacing(player, skill)
    return None, True

def handle_necromancy(player, skill, args):
    corpse = next((i for i in player.room.items if isinstance(i, Corpse)), None)
    if not corpse:
        player.send_line("There are no corpses here to raise.")
        return None, True

    player.room.items.remove(corpse)
    player.room.broadcast(f"{player.name} chants over {corpse.name}, and it begins to twitch!", exclude_player=player)
    player.send_line(f"You breathe unlife into {corpse.name}!")
    mob_manager.spawn_mob(player.game, "skeleton", player.room)
    return None, True

def handle_beast_master(player, skill, args):
    pet = next((m for m in player.room.monsters if m.leader == player), None)
    if not pet:
        player.send_line("You have no companion to command.")
        return None, True

    player.send_line(f"You command {pet.name} to howl!")
    player.room.broadcast(f"{pet.name} lets out a piercing howl!", exclude_player=player)
    
    if len(player.room.monsters) < 6:
        mob_manager.spawn_mob(player.game, pet.prototype_id, player.room)
        player.room.broadcast(f"A new {pet.name} emerges from the wilds!")
    else:
        player.send_line("The area is too crowded.")
    return None, True

def handle_temporal(player, skill, args):
    from logic.engines import status_effects_engine
    if "phase_bubble" in skill.identity_tags:
        # Apply a status effect that allows passing locked doors (logic to be added in movement)
        status_effects_engine.apply_effect(player, "phased", 30, verbose=False)
        player.send_line(f"{Colors.CYAN}You shift slightly out of phase with reality.{Colors.RESET}")
        player.room.broadcast(f"{player.name} begins to shimmer and turn translucent.", exclude_player=player)
        return None, True
    
    return None, True

def handle_scare(player, skill, args):
    from logic.engines import magic_engine
    target = find_by_index(player.room.monsters + player.room.players, args) if args else player.fighting
    if target:
        from logic.engines import status_effects_engine
        status_effects_engine.apply_effect(target, "fear", 10)
        player.send_line(f"{Colors.RED}You scream at {target.name}, filling them with fear!{Colors.RESET}")
        # Force flee logic could go here or be handled by the fear effect in combat_processor
        if hasattr(target, 'send_line'):
            target.send_line(f"{Colors.RED}You are terrified of {player.name}!{Colors.RESET}")
        magic_engine.consume_resources(player, skill)
        magic_engine.set_cooldown(player, skill)
        magic_engine.consume_pacing(player, skill)
    return target, False
