"""
logic/modules/mage/mage.py
The Mage Domain: Spells, Mana management, and Shielding logic.
"""
from logic.actions.registry import register
from logic.core import event_engine, status_effects_engine, resource_engine
from logic.engines import action_manager
from utilities.colors import Colors
from logic import common

def _consume_resources(player, skill):
    from logic.engines import magic_engine
    magic_engine.consume_resources(player, skill)
    magic_engine.set_cooldown(player, skill)
    magic_engine.consume_pacing(player, skill)

# --- SKILL HANDLERS ---

@register("magic_shield")
def handle_magic_shield(player, skill, args, target=None):
    """
    Magic Shield: Buffs the mage and toggles arcane_shield in ext_state.
    Provides huge defense but drains concentration on every hit.
    """
    status_effects_engine.apply_effect(player, "magic_shield", 30) # 60 seconds
    player.ext_state.get('mage', {})['arcane_shield'] = True
    player.send_line(f"{Colors.BLUE}You shroud yourself in a shimmering azure field!{Colors.RESET}")
    return player, True

@register("magic_missile")
def handle_magic_missile(player, skill, args, target=None):
    target = common._get_target(player, args, target, "Cast Magic Missile on whom?")
    if not target: return None, True

    player.send_line(f"{Colors.CYAN}You begin channeling arcane energy...{Colors.RESET}")
    player.room.broadcast(f"{player.name} begins chanting.", exclude_player=player)

    async def _unleash():
        if player.room != target.room:
            player.send_line("Target out of range.")
            return
            
        player.send_line(f"{Colors.CYAN}Three missiles of force streak towards {target.name}!{Colors.RESET}")
        player.room.broadcast(f"Three missiles of force streak from {player.name} to {target.name}!", exclude_player=player)
        
        # Power scaling from Int
        from logic.engines import blessings_engine
        power = blessings_engine.MathBridge.calculate_power(skill, player)
        dmg_per_missile = int(power / 3) # Split total power into 3 bolts
        
        from logic.actions.skill_utils import _apply_damage
        import asyncio
        for _ in range(3):
            if target.hp > 0:
                _apply_damage(player, target, dmg_per_missile, "Magic Missile")
                await asyncio.sleep(0.2)

    from logic.engines import action_manager
    action_manager.start_action(player, 4.0, _unleash, tag="casting", fail_msg="Concentration broken!")
    _consume_resources(player, skill)
    return target, True

@register("fireball")
def handle_fireball(player, skill, args, target=None):
    player.send_line(f"{Colors.RED}You begin channeling a massive fireball...{Colors.RESET}")
    player.room.broadcast(f"{player.name} begins gathering flames!", exclude_player=player)

    async def _unleash():
        from logic.engines import blessings_engine
        power = blessings_engine.MathBridge.calculate_power(skill, player)
        aoe_power = int(power * 0.5)
        
        player.send_line(f"{Colors.RED}You unleash the Fireball! It explodes!{Colors.RESET}")
        player.room.broadcast(f"{player.name} unleashes a massive Fireball that explodes!", exclude_player=player)

        # Robust Targeting (Mobs + Players)
        targets = [m for m in player.room.monsters] + [p for p in player.room.players if p != player]
        
        if not targets:
            player.send_line("The fire explodes harmlessly.")
            return

        from logic.actions.skill_utils import _apply_damage
        for t in targets:
            _apply_damage(player, t, aoe_power, "Fireball")
            status_effects_engine.apply_effect(t, "burn", 10)

    action_manager.start_action(player, 2.0, _unleash, tag="casting", fail_msg="Concentration broken!")
    _consume_resources(player, skill)
    return None, True

@register("freeze")
def handle_freeze(player, skill, args, target=None):
    """
    Freeze: Applies 'frozen' status to the target.
    """
    target = common._get_target(player, args, target, "Freeze whom?")
    if not target: return None, True

    player.send_line(f"{Colors.CYAN}You channel absolute zero towards {target.name}!{Colors.RESET}")
    player.room.broadcast(f"{player.name} channels a freezing beam at {target.name}!", exclude_player=player)

    async def _unleash():
        if player.room != target.room:
            player.send_line("Target out of range.")
            return

        # Power scaling (even though it's primarily a status skill, we might deal small damage)
        from logic.engines import blessings_engine
        power = blessings_engine.MathBridge.calculate_power(skill, player)
        
        from logic.actions.skill_utils import _apply_damage
        _apply_damage(player, target, power, "Freeze")
        
        # Frozen status is handled by apply_on_hit in generic logic if we didn't use a custom handler,
        # but since we are here, we handle it explicitly.
        status_effects_engine.apply_effect(target, "frozen", 4)
        player.send_line(f"{Colors.BOLD}{Colors.CYAN}{target.name} is FROZEN!{Colors.RESET}")

    from logic.engines import action_manager
    action_manager.start_action(player, 1.5, _unleash, tag="casting", fail_msg="Concentration broken!")
    _consume_resources(player, skill)
    return target, True

@register("lightning_bolt")
def handle_lightning_bolt(player, skill, args, target=None):
    target = common._get_target(player, args, target, "Cast at whom?")
    if not target: return None, True

    # Weather Check for Flavor/Power
    zone_id = player.room.zone_id
    if zone_id and zone_id in player.game.world.zones:
        zone = player.game.world.zones[zone_id]
        current_weather = getattr(zone, 'weather', 'clear')
        if current_weather not in ["rain", "storm"]:
            player.send_line(f"You cannot call down lightning in {current_weather} weather! You need a storm.")
            return None, True

    from logic.engines import blessings_engine
    power = blessings_engine.MathBridge.calculate_power(skill, player)
    
    # Dualcast Logic
    casts = 2 if status_effects_engine.has_effect(player, "dualcast") else 1
    if casts == 2:
        status_effects_engine.remove_effect(player, "dualcast")
        player.send_line(f"{Colors.MAGENTA}Dualcast!{Colors.RESET}")

    from logic.actions.skill_utils import _apply_damage
    for _ in range(casts):
        player.send_line(f"You hurl a bolt of lightning at {target.name}!")
        _apply_damage(player, target, power, "Lightning Bolt")
    
    _consume_resources(player, skill)
    return target, True

@register("dualcast")
def handle_dualcast(player, skill, args, target=None):
    status_effects_engine.apply_effect(player, "dualcast", 9999)
    player.send_line(f"{Colors.MAGENTA}You focus your mind to cast your next spell twice!{Colors.RESET}")
    _consume_resources(player, skill)
    return None, True

@register("arcane_surge")
def handle_arcane_surge(player, skill, args, target=None):
    """
    Arcane Surge: Restores 40 stamina but stumbles/stalls for 3s.
    """
    player.send_line(f"{Colors.LIGHT_CYAN}You draw raw arcane power directly into your lungs!{Colors.RESET}")
    resource_engine.modify_resource(player, "stamina", 40)
    status_effects_engine.apply_effect(player, "stalled", 3)
    _consume_resources(player, skill)
    return None, True

@register("frost_nova")
def handle_frost_nova(player, skill, args, target=None):
    player.send_line(f"{Colors.BOLD}{Colors.BLUE}You gather a freezing vortex around you...{Colors.RESET}")
    player.room.broadcast(f"{player.name} begins to freeze the very air!", exclude_player=player)

    async def _unleash():
        player.send_line(f"{Colors.BOLD}{Colors.CYAN}FROST NOVA! An explosion of ice hits everyone!{Colors.RESET}")
        player.room.broadcast(f"A ring of frost explodes from {player.name}!", exclude_player=player)

        targets = [m for m in player.room.monsters] + [p for p in player.room.players if p != player]
        
        from logic.engines import blessings_engine
        power = blessings_engine.MathBridge.calculate_power(skill, player)
        aoe_power = int(power * 0.6) # Slightly higher base than fireball since ice is cooler

        from logic.actions.skill_utils import _apply_damage
        for t in targets:
            _apply_damage(player, t, aoe_power, "Frost Nova")
            # 50% chance to freeze for longer
            if status_effects_engine.apply_effect(t, "frozen", 6):
                player.send_line(f"{Colors.CYAN}{t.name} is encased in ice!{Colors.RESET}")

    action_manager.start_action(player, 1.5, _unleash, tag="casting", fail_msg="Concentration broken!")
    _consume_resources(player, skill)
    return None, True

def on_build_prompt(ctx):
    """Injects [MANA] display for Mages."""
    player = ctx.get('player')
    prompts = ctx.get('prompts')
    
    if getattr(player, 'active_class', None) == 'mage':
        conc = player.resources.get('concentration', 0)
        max_conc = player.get_max_resource('concentration')
        # Display as MANA for flavor (Light Cyan for better visibility)
        prompts.append(f"{Colors.LIGHT_CYAN}MANA: {conc}/{max_conc}{Colors.RESET}")

def on_take_damage(ctx):
    """
    Magic Shield Mechanic: 
    Redirects 50% damage to 'concentration' if shield is active.
    """
    player = ctx.get('target')
    damage = ctx.get('damage', 0)
    
    if not player:
        return
        
    if status_effects_engine.has_effect(player, 'magic_shield'):
        # Warlock Passive: Ignore Magic Shields
        attacker = ctx.get('source')
        if attacker and getattr(attacker, 'active_class', None) == 'warlock':
            return
            
        shield_reduction = int(damage * 0.5)
        # Drain Conc instead of HP
        resource_engine.modify_resource(player, 'concentration', -shield_reduction, source="Magic Shield", context="Absorbed")
        ctx['damage'] = damage - shield_reduction
        player.send_line(f"{Colors.BLUE}Your Magic Shield absorbs {shield_reduction} damage!{Colors.RESET}")

# --- REGISTRATION ---
event_engine.subscribe("on_build_prompt", on_build_prompt)
event_engine.subscribe("on_take_damage", on_take_damage)
