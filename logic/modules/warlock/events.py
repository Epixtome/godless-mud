from logic.core import event_engine, resources, effects
import utilities.telemetry as telemetry
import time
from utilities.colors import Colors

def register_events():
    """Subscribes Warlock hooks to the event engine."""
    event_engine.subscribe("on_combat_tick", handle_warlock_heartbeat)
    event_engine.subscribe("calculate_damage_modifier", on_calculate_damage_modifier)
    event_engine.subscribe("on_combat_hit", on_combat_hit)
    event_engine.subscribe("on_take_damage", on_take_damage)
    event_engine.subscribe("on_calculate_skill_cost", on_calculate_skill_cost)

def handle_warlock_heartbeat(player):
    if getattr(player, 'active_class', None) != 'warlock':
        return
    
    warlock_state = player.ext_state.get('warlock', {})
    
    if warlock_state.get('link_target') and time.time() > warlock_state.get('link_expiry', 0):
        warlock_state['link_target'] = None
        player.send_line(f"{Colors.MAGENTA}Your Malignant Bond has faded.{Colors.RESET}")

    # 2. Handle Despair Aura
    if warlock_state.get('despair_aura') and player.room:
        targets = [m for m in player.room.monsters] + [p for p in player.room.players if p != player]
        if targets:
            player.send_line(f"{Colors.DARK_GRAY}Your aura of Despair saps the will of those around you...{Colors.RESET}")
            for t in targets:
                resources.modify_resource(t, "stamina", -5, source=player.name, context="Despair Aura")

def on_calculate_damage_modifier(ctx):
    """
    1. The 'Desperation' Buff: Power increases as HP decreases.
    2. 'Shield Breaker' Passive: Ignores Magic Shield's 20% reduction.
    """
    attacker = ctx.get('attacker') or ctx.get('player')
    target = ctx.get('target')
    if not attacker or getattr(attacker, 'active_class', None) != 'warlock':
        return

    # Scaling: 1.0x at 100% HP, up to 3.0x at 1% HP.
    hp_percent = attacker.hp / attacker.max_hp
    if hp_percent < 1.0:
        multiplier = 1.0 + (1.0 - hp_percent) * 2.0
        ctx['multiplier'] = ctx.get('multiplier', 1.0) * multiplier

    # Ignore Magic Shield (Passive)
    # The bypass is handled globally in mage.py on_take_damage
    # This prevents double-buffing while maintaining flavor
    if target and effects.has_effect(target, "magic_shield"):
        attacker.send_line(f"{Colors.RED}[SHIELD BREAKER] Your dark power ignores the magical defense!{Colors.RESET}")

def on_combat_hit(ctx):
    """The 'Decay' Stack: Apply Decay on Dark hits."""
    attacker = ctx.get('attacker')
    target = ctx.get('target')
    blessing = ctx.get('blessing')

    if not attacker or getattr(attacker, 'active_class', None) != 'warlock' or not target:
        return

    # Check for Dark/Occult tags or specific warlock skills
    tags = getattr(blessing, 'identity_tags', [])
    if "dark" in tags or "occult" in tags or "warlock" in tags:
        warlock_state = attacker.ext_state.get('warlock', {})
        t_id = target.id
        
        stacks = warlock_state['decay_stacks'].get(t_id, 0)
        if stacks < 5:
            stacks += 1
            warlock_state['decay_stacks'][t_id] = stacks
            attacker.send_line(f"{Colors.DARK_GRAY}Decay spreads to {target.name} ({stacks}/5).{Colors.RESET}")
            
            if stacks == 5:
                effects.apply_effect(target, "atrophy", 10) # 10s Atrophy
                attacker.send_line(f"{Colors.RED}*** {target.name} has entered ATROPHY! ***{Colors.RESET}")

def on_take_damage(ctx):
    """Soul-Linking (Malignant Bond): Reflect 30% damage to linked target."""
    target = ctx.get('target') # The warlock
    damage = ctx.get('damage', 0)
    attacker = ctx.get('attacker')

    if not target or getattr(target, 'active_class', None) != 'warlock':
        return

    warlock_state = target.ext_state.get('warlock', {})
    link_id = warlock_state.get('link_target')
    
    if link_id and time.time() < warlock_state.get('link_expiry', 0):
        # Find the linked entity in the room or world
        link_entity = None
        for p in target.room.players:
            if p.id == link_id: link_entity = p; break
        if not link_entity:
            for m in target.room.mobs:
                if m.id == link_id: link_entity = m; break
        
        if link_entity and link_entity.hp > 0:
            reflect_dmg = int(damage * 0.3)
            if reflect_dmg > 0:
                target.send_line(f"{Colors.MAGENTA}Malignant Bond reflects {reflect_dmg} damage to {link_entity.name}!{Colors.RESET}")
                resources.modify_resource(link_entity, "hp", -reflect_dmg, source=target.name, context="Malignant Bond")

def on_calculate_skill_cost(ctx):
    """Sanguine Exchange: High-tier skills cost HP instead of Stamina."""
    player = ctx.get('player')
    blessing = ctx.get('blessing')
    costs = ctx.get('costs')

    if not player or getattr(player, 'active_class', None) != 'warlock':
        return

    # Only core Warlock skills above Tier 2 use HP
    if "warlock" in getattr(blessing, 'identity_tags', []) and getattr(blessing, 'tier', 1) >= 3:
        hp_cost = int(player.max_hp * 0.05) # 5% Max HP cost
        costs["hp"] = hp_cost
        costs["stamina"] = 0
        player.send_line(f"{Colors.RED}[BLOOD TO VOID] You sacrifice {hp_cost} HP for power.{Colors.RESET}")

# Auto-register on import
register_events()
