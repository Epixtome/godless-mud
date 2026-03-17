"""
logic/modules/assassin/actions.py
Assassin Skill Handlers: Backstab, Smoke Bomb, etc.
"""
from logic.actions.registry import register
from logic.core import effects, resources, combat
from logic.engines import action_manager, blessings_engine, magic_engine
from logic.actions.skill_utils import _apply_damage
from utilities.colors import Colors
from logic import common

def _consume_resources(player, skill):
    magic_engine.consume_resources(player, skill)
    magic_engine.set_cooldown(player, skill)
    magic_engine.consume_pacing(player, skill)

@register("hide")
def handle_hide(player, skill, args, target=None):
    """Attempt to vanish into the shadows."""
    if player.fighting or getattr(player, 'attackers', []):
        player.send_line("You cannot hide while in active combat or while being hunted!")
        return None, True

    player.send_line(f"{Colors.BLUE}You slip into the shadows...{Colors.RESET}")
    # [V6.0] Concealed now gives a massive concealment bonus in vision_logic
    effects.apply_effect(player, "concealed", 300) 
    player.concealment = 30 # Baseline 10 + 20 from status = 30
    
    _consume_resources(player, skill)
    return None, True

@register("backstab")
def handle_backstab(player, skill, args, target=None):
    """Strike from concealment for massive damage. Scales with Daggers/Precision."""
    target = common._get_target(player, args, target, "Backstab whom?")
    if not target: return None, True

    if "concealed" not in getattr(player, 'status_effects', {}):
        player.send_line("You must be concealed to backstab!")
        return None, True

    # [V6.0] Weapon-Based Damage Logic
    w = player.equipped_weapon
    w_tags = getattr(w, 'tags', [])
    
    # Base multiplier for backstab (3x)
    backstab_mult = 3.0
    
    # Dagger/Precision/Stiletto bonus
    if any(tag in w_tags for tag in ["precision", "stiletto", "dagger", "finesse"]):
        backstab_mult = 4.0
        player.send_line(f"{Colors.CYAN}The precision of your blade finds the perfect gap!{Colors.RESET}")
    elif any(tag in w_tags for tag in ["weight", "heavy_gear", "blunt"]):
        backstab_mult = 0.5
        player.send_line(f"{Colors.YELLOW}Your weapon is too unwieldy for a clean backstab!{Colors.RESET}")

    player.send_line(f"{Colors.RED}You emerge from the shadows and drive your blade into {target.name}'s back!{Colors.RESET}")
    player.room.broadcast(f"{player.name} appears behind {target.name} and strikes!", exclude_player=player)

    power = blessings_engine.MathBridge.calculate_power(skill, player, target)
    final_power = int(power * backstab_mult)
    
    # Use the core combat facade
    combat.handle_attack(player, target, final_power, "Backstab")
    
    # Reveal
    effects.remove_effect(player, "concealed")
    player.concealment = 10
    
    # Hardlock recovery
    effects.apply_effect(player, "stunned", 2)
    
    _consume_resources(player, skill)
    return target, True

@register("circle")
def handle_circle(player, skill, args, target=None):
    """Combat maneuver to strike from behind, shattering balance."""
    target = common._get_target(player, args, target, "Circle whom?")
    if not target: return None, True

    if not player.fighting:
        player.send_line("Circle is a combat maneuver; you are not currently fighting.")
        return None, True

    player.send_line(f"{Colors.BLUE}You dance around {target.name}, circling behind their guard!{Colors.RESET}")
    
    # [V6.0] Track positioning for Garrote/Finisher
    if 'assassin' not in player.ext_state:
        player.ext_state['assassin'] = {}
    player.ext_state['assassin']['positioning'] = {
        'target_id': target.name,
        'expire_tick': player.game.tick_count + 6 # 12s window
    }

    power = blessings_engine.MathBridge.calculate_power(skill, player, target)
    
    # Circle deals good damage and heavy balance damage
    combat.handle_attack(player, target, int(power * 1.5), "Circle")
    from logic.core.utils import combat_logic
    combat_logic.check_posture_break(target, 45, source=player, tags={"precision", "speed"})
    
    _consume_resources(player, skill)
    return target, True

@register("venom")
def handle_venom(player, skill, args, target=None):
    """Apply a lethal coating to your current weapon."""
    if not player.equipped_weapon:
        player.send_line("You have no weapon to poison!")
        return None, True

    player.send_line(f"{Colors.GREEN}You coat your {player.equipped_weapon.name} in a shimmering dark venom.{Colors.RESET}")
    # Apply a status that MathBridge checks or just add the tag to the weapon
    # For simplicity and persistence, we'll add a status effect to the player that on_hit logic can check
    effects.apply_effect(player, "poisoned_weapon", 60)
    
    _consume_resources(player, skill)
    return None, True

@register("trap")
def handle_set_trap(player, skill, args, target=None):
    """Set a hidden trap in the room. Types: trip, blind, web, sleep, fire."""
    if not args:
        player.send_line("Usage: trap <trip|blind|web|sleep|fire>")
        return None, True

    trap_type = args.lower().strip()
    from .utility import set_trap
    if set_trap(player, trap_type):
        _consume_resources(player, skill)
    
    return None, True

@register("smoke_bomb")
def handle_smoke_bomb(player, skill, args, target=None):
    """Deploy a smoke screen to confuse enemies and escape."""
    player.send_line(f"{Colors.YELLOW}You smash a smoke bomb at your feet!{Colors.RESET}")
    player.room.broadcast(f"{player.name} is enveloped in a thick cloud of smoke!", exclude_player=player)

    # Interrupt all enemies fighting the player
    enemies = [m for m in player.room.monsters if m.fighting == player]
    enemies += [p for p in player.room.players if p.fighting == player]
    
    for e in enemies:
        action_manager.interrupt(e)
        effects.apply_effect(e, "confused", 6)
        # Drop aggro
        if player in getattr(e, 'attackers', []):
            e.attackers.remove(player)
        e.fighting = None

    player.fighting = None
    player.attackers = []
    player.state = "normal"
    
    _consume_resources(player, skill)
    return None, True

@register("dirt_kick")
def handle_dirt_kick(player, skill, args, target=None):
    """Blinds the target."""
    target = common._get_target(player, args, target, "Kick dirt at whom?")
    if not target: return None, True

    player.send_line(f"You kick a spray of dirt into {target.name}'s eyes!")
    effects.apply_effect(target, "blinded", 10)
    
    # Engage Combat
    if target.hp > 0 and not player.fighting:
        player.fighting = target
        player.state = "combat"
        if player not in target.attackers:
            target.attackers.append(player)
            
    _consume_resources(player, skill)
    return target, True

@register("garrote")
def handle_garrote(player, skill, args, target=None):
    """Silences and stuns the target from behind."""
    target = common._get_target(player, args, target, "Garrote whom?")
    if not target: return None, True

    # [V6.0] Positioning Requirement (Requires Circle)
    pos = player.ext_state.get('assassin', {}).get('positioning', {})
    if pos.get('target_id') != target.name or pos.get('expire_tick', 0) < player.game.tick_count:
        player.send_line(f"{Colors.YELLOW}You must circle behind {target.name} before you can use the garrote!{Colors.RESET}")
        return None, True

    player.send_line(f"{Colors.RED}You loop the wire around {target.name}'s throat and pull tight!{Colors.RESET}")
    player.room.broadcast(f"{player.name} looms behind {target.name} and cinches a garrote wire around their throat!", exclude_player=player)
    
    # Apply hard CC
    effects.apply_effect(target, "silenced", 8)
    effects.apply_effect(target, "stunned", 2)
    
    # Engage Combat
    if target.hp > 0 and not player.fighting:
        player.fighting = target
        player.state = "combat"
        if player not in target.attackers:
            target.attackers.append(player)

    # Clear positioning advantage
    player.ext_state['assassin']['positioning'] = {}
    
    _consume_resources(player, skill)
    return target, True
