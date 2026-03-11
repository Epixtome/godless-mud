"""
logic/modules/mage/actions.py
Mage Skill Handlers: Magic Shield, Fireball, Freeze, etc.
"""
import asyncio
from logic.actions.registry import register
from logic.core import effects, resources, combat
from logic.engines import action_manager, magic_engine, blessings_engine
from utilities.colors import Colors
from logic import common

def _consume_resources(player, skill):
    magic_engine.consume_resources(player, skill)
    magic_engine.set_cooldown(player, skill)
    magic_engine.consume_pacing(player, skill)

@register("magic_shield")
def handle_magic_shield(player, skill, args, target=None):
    """Provides huge defense but drains concentration on every hit."""
    effects.apply_effect(player, "magic_shield", 30) # 60 seconds (scaled by tick rate)
    mage_data = player.ext_state.setdefault('mage', {})
    mage_data['arcane_shield'] = True
    player.send_line(f"{Colors.BLUE}You shroud yourself in a shimmering azure field!{Colors.RESET}")
    _consume_resources(player, skill)
    return player, True

@register("magic_missile")
def handle_magic_missile(player, skill, args, target=None):
    target = common._get_target(player, args, target, "Cast Magic Missile on whom?")
    if not target: return None, True

    player.send_line(f"{Colors.CYAN}You begin channeling arcane energy...{Colors.RESET}")
    player.room.broadcast(f"{player.name} begins chanting.", exclude_player=player)

    async def _unleash():
        if not target or target.room != player.room:
            player.send_line("Target is no longer here.")
            return
            
        player.send_line(f"{Colors.CYAN}Three missiles of force streak towards {target.name}!{Colors.RESET}")
        player.room.broadcast(f"Three missiles of force streak from {player.name} to {target.name}!", exclude_player=player)
        
        # Power scaling from Int
        power = blessings_engine.MathBridge.calculate_power(skill, player)
        dmg_per_missile = int(power / 3) # Split total power into 3 bolts
        
        for _ in range(3):
            if target and target.hp > 0:
                # Use combat facade
                combat.handle_attack(player, target, player.room, player.game, blessing=skill)
                # Wait, handle_attack recalculates power via blessing. 
                # If we want specific 'missile' damage, we might need a custom apply.
                # However, for Magic Missile, 3 mini-attacks is the feel.
                await asyncio.sleep(0.2)

    action_manager.start_action(player, 4.0, _unleash, tag="casting", fail_msg="Concentration broken!")
    _consume_resources(player, skill)
    return target, True

@register("fireball")
def handle_fireball(player, skill, args, target=None):
    player.send_line(f"{Colors.RED}You begin channeling a massive fireball...{Colors.RESET}")
    player.room.broadcast(f"{player.name} begins gathering flames!", exclude_player=player)

    async def _unleash():
        player.send_line(f"{Colors.RED}You unleash the Fireball! It explodes!{Colors.RESET}")
        player.room.broadcast(f"{player.name} unleashes a massive Fireball that explodes!", exclude_player=player)

        # Robust Targeting (Mobs + Players)
        targets = [m for m in player.room.monsters] + [p for p in player.room.players if p != player]
        
        if not targets:
            player.send_line("The fire explodes harmlessly.")
            return

        for t in targets:
            # AoE Fireball often has lower power per target, but here we just use the blessing execution.
            # The blessing JSON should ideally handle AoE scaling if using a generic executor.
            combat.handle_attack(player, t, player.room, player.game, blessing=skill)
            effects.apply_effect(t, "burn", 10)

    action_manager.start_action(player, 2.0, _unleash, tag="casting", fail_msg="Concentration broken!")
    _consume_resources(player, skill)
    return None, True

@register("lightning_bolt")
def handle_lightning_bolt(player, skill, args, target=None):
    target = common._get_target(player, args, target, "Cast at whom?")
    if not target: return None, True

    # Weather Check
    zone_id = player.room.zone_id
    if zone_id and zone_id in player.game.world.zones:
        zone = player.game.world.zones[zone_id]
        current_weather = getattr(zone, 'weather', 'clear')
        if current_weather not in ["rain", "storm"]:
            player.send_line(f"You cannot call down lightning in {current_weather} weather! You need a storm.")
            return None, True

    # Dualcast Logic
    casts = 2 if effects.has_effect(player, "dualcast") else 1
    if casts == 2:
        effects.remove_effect(player, "dualcast")
        player.send_line(f"{Colors.MAGENTA}Dualcast!{Colors.RESET}")

    for _ in range(casts):
        player.send_line(f"You hurl a bolt of lightning at {target.name}!")
        combat.handle_attack(player, target, player.room, player.game, blessing=skill)
    
    _consume_resources(player, skill)
    return target, True

@register("dualcast")
def handle_dualcast(player, skill, args, target=None):
    effects.apply_effect(player, "dualcast", 9999)
    player.send_line(f"{Colors.MAGENTA}You focus your mind to cast your next spell twice!{Colors.RESET}")
    _consume_resources(player, skill)
    return None, True

@register("arcane_surge")
def handle_arcane_surge(player, skill, args, target=None):
    player.send_line(f"{Colors.LIGHT_CYAN}You draw raw arcane power directly into your lungs!{Colors.RESET}")
    resources.modify_resource(player, "stamina", 40)
    effects.apply_effect(player, "stalled", 3)
    _consume_resources(player, skill)
    return None, True
