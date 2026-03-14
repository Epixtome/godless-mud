import logging
from utilities.colors import Colors
from logic.core import effects
from utilities import telemetry
from logic.constants import Tags
from . import resource_registry

logger = logging.getLogger("GodlessMUD")

from logic import calibration

def update_max_hp(entity):
    """
    Recalculates Max HP based on Base + Gear Bonus.
    """
    if not hasattr(entity, 'equipped_armor'): return
    
    base_hp = 100 # Standard Base HP
    bonus = 0
    
    slots = ["equipped_armor", "equipped_head", "equipped_neck", "equipped_arms", "equipped_hands", "equipped_legs", "equipped_feet", "equipped_offhand"]
    for slot in slots:
        item = getattr(entity, slot, None)
        if item:
            bonus += getattr(item, 'bonus_hp', 0)
            
    entity._max_hp = base_hp + bonus
    entity.hp = min(entity.hp, entity.max_hp)

def calculate_total_weight(entity):
    """
    [DEPRECATED] Use logic.core.utils.player_logic.calculate_total_weight instead.
    """
    from logic.core.utils import player_logic
    return player_logic.calculate_total_weight(entity, only_equipped=True)

def modify_resource(entity, resource, amount, source="System", context="Adjustment", log=True):
    """
    Centralized method to modify resources.
    Handles clamping, overflow (Pips), and underflow.
    """
    # 0. Handle HP (Attribute, not dict)
    if str(resource).lower() == "hp":
        if hasattr(entity, 'hp') and hasattr(entity, 'max_hp'):
            if amount < 0:
                # Route through combat facade for standardized damage pipeline
                from . import combat
                actual = combat.apply_damage(entity, -amount, source=source, context=context)
                if log:
                    telemetry.log_resource_delta(entity, "HP", -actual, source.name if hasattr(source, 'name') else source, context=context)
                return

            # V2 Logic: Holy Breakthrough Overheal
            max_cap = entity.max_hp
            if hasattr(entity, 'breakthroughs') and isinstance(entity.breakthroughs, dict) and entity.breakthroughs.get('holy'):
                max_cap = int(entity.max_hp * 1.2)
            
            current = entity.hp
            new_val = max(0, min(max_cap, entity.hp + amount))
            if new_val == current: return # Delta-Only: No change
            
            entity.hp = new_val
            if log:
                telemetry.log_resource_delta(entity, "HP", amount, source.name if hasattr(source, 'name') else source, context=context)
        return

    # 1. Resource Target Resolution (Standard vs Class-Specific)
    target_dict = None
    kit_id = getattr(entity, 'active_kit', {}).get('id', '')
    
    # Check registry for storage preference
    definition = resource_registry.get_definition(str(kit_id), resource) if kit_id else None
    
    if definition and hasattr(entity, 'ext_state') and entity.active_class:
        # Prefer ext_state for registered class resources
        target_dict = entity.ext_state.get(entity.active_class)
    elif hasattr(entity, 'resources') and resource in entity.resources:
        target_dict = entity.resources
    elif hasattr(entity, 'ext_state') and hasattr(entity, 'active_class') and entity.active_class:
        # Fallback for unregistered resources that exist in ext_state
        if resource in entity.ext_state.get(entity.active_class, {}):
            target_dict = entity.ext_state[entity.active_class]
    
    # Special bypass for Stamina/Concentration/Heat etc.
    if not target_dict and str(resource).lower() in ["stamina", "concentration", "heat", "chi", "balance"]:
        target_dict = getattr(entity, 'resources', None)

    if target_dict is None:
        return

    # Get current and max
    current = target_dict.get(resource, 0)
    
    # Determine Max
    max_val = 100
    if definition:
        max_val = definition.max
        if definition.max_getter:
            max_val = definition.max_getter(entity)
    elif max_val == 100: # Definition not found or default
        if hasattr(entity, 'get_max_resource'):
            max_val = entity.get_max_resource(resource)
        elif resource == Tags.CHI:
            max_val = 5
    
    # V2 Physics: Stamina Tax (Weight Class)
    if str(resource).lower() == "stamina" and amount < 0:
        from logic.core.utils import combat_logic
        wc = combat_logic.get_weight_class(entity)
        
        # Stamina multiplier logic
        mult = 1.0
        if wc == "heavy":
            mult = calibration.CombatBalance.STAMINA_PENALTY_HEAVY
        elif wc == "medium":
            mult = calibration.CombatBalance.STAMINA_PENALTY_MEDIUM
            
        amount = int(amount * mult)

    # Calculate new value
    new_val = current + amount
    
    # Clamp
    if resource == Tags.CONCENTRATION:
        new_val = max(-max_val, min(max_val, new_val))
    elif resource in [Tags.HEAT, "stamina", "balance", "entropy", "momentum", "flow_pips", "echoes"]:
         # Positive-only resources
         new_val = max(0, min(max_val, new_val))
    else:
        new_val = max(0, min(max_val, new_val))
        
    if new_val == current:
        return # Delta-Only: No change
        
    target_dict[resource] = new_val
    
    # Sync: If we updated ext_state, also update legacy/display resources dict
    if target_dict is not getattr(entity, 'resources', None) and hasattr(entity, 'resources'):
        if resource in entity.resources:
            entity.resources[resource] = new_val

    if log:
        telemetry.log_resource_delta(entity, resource, amount, source, context=context)

    if log:
        telemetry.log_resource_delta(entity, resource, amount, source, context=context)

def calculate_balance_regen(entity):
    """Calculates balance (posture) regeneration per tick."""
    max_bal = 100
    if hasattr(entity, 'get_max_resource'):
        max_bal = entity.get_max_resource('balance')
        
    # [V5.1] Posture Protocol: No passive balance regen in combat or while being attacked
    in_combat = (hasattr(entity, 'is_in_combat') and entity.is_in_combat())
    being_attacked = (hasattr(entity, 'attackers') and len(entity.attackers) > 0)
    
    regen = 0 if (in_combat or being_attacked) else 10
    
    # [V5.1] Generic Metadata Hook
    for effect_id in getattr(entity, 'status_effects', {}):
        meta = effects.get_effect_metadata(effect_id, getattr(entity, 'game', None))
        if isinstance(meta, dict):
            if meta.get('regen_suppressed'):
                return 0, max_bal
            # Explicit type check to satisfy linter
            val = meta.get('balance_regen_bonus', 0)
            if isinstance(val, (int, float)):
                regen += int(val)

    return regen, max_bal

def calculate_conc_regen(player):
    """Calculates concentration regeneration per tick."""
    max_conc = player.get_max_resource(Tags.CONCENTRATION)
    
    # Base Calculation (Friction System)
    # In-Combat: Passive regeneration. Halve the rate if the player was hit in the last 2 ticks.
    regen = 5
    
    # Tag Bonus (Small passive bonus from magic tags)
    regen += int(player.get_global_tag_count(Tags.MAGIC) * 0.5)
    
    # Modifiers
    if player.is_in_combat():
        # Tension Penalty: Halve regen if hit recently
        if (player.game.tick_count - player.last_hit_tick) <= 2:
            regen = int(regen * 0.5)
    else:
        # Out-of-Combat: Rapid recovery
        regen = 20

    if player.is_resting:
        regen = 30
    if "meditating" in player.status_effects:
        regen += 30
        
    return regen, max_conc

def calculate_stamina_regen(player):
    """Calculates stamina regeneration per tick."""
    # Check for Atrophy (Warlock Debuff)
    if effects.has_effect(player, "atrophy") or "atrophy" in getattr(player, 'status_effects', {}):
        return 0, player.get_max_resource("stamina")

    max_stamina = player.get_max_resource("stamina")
    
    # Base Regen
    regen = 5
    if not player.is_in_combat():
        regen = 15 # Out-of-combat boost
    
    # [V5.1] Generic Metadata Hook
    for effect_id in getattr(player, 'status_effects', {}):
        meta = effects.get_effect_metadata(effect_id, getattr(player, 'game', None))
        if isinstance(meta, dict):
            if meta.get('regen_suppressed'):
                return 0, max_stamina
            mult = meta.get('stamina_regen_mult', 1.0)
            if isinstance(mult, (int, float)):
                regen = int(regen * mult)

    # Weight Class Logic (Light/Medium recover faster)
    from logic.core.utils import combat_logic
    wc = combat_logic.get_weight_class(player)
    if wc == "light":
        regen += 8
    elif wc == "medium":
        regen += 4
        
    # Resting & Training Bonus
    if player.is_resting:
        regen += 10
        
    if "meditating" in getattr(player, 'status_effects', {}):
        # [V4.5] Meditate: Massive stamina recovery
        regen += 20
        
    return regen, max_stamina

def calculate_heat_decay(player):
    """Calculates heat dissipation per tick."""
    max_heat = player.get_max_resource(Tags.HEAT)
    
    # Base Dissipation
    decay = 2
    
    # Sticky Heat Logic
    # If waiting or resting, decay increases to 10.
    # Otherwise (combat/moving), it stays at 2.
    is_waiting = player.last_action in ["wait", "none", ""]
    
    if is_waiting or player.is_resting or not player.is_in_combat():
        decay = 10

    # Knight Passive: Thermal Mass (20% bonus when stationary)
    kit_name = player.active_kit.get('name', '').lower()
    if kit_name == 'knight' and is_waiting:
        decay = int(decay * 1.2)
        
    return decay, max_heat

def process_tick(player):
    """
    Processes all resource regeneration and state checks for a player.
    Called by systems.passive_regen.
    """
    # 0. Gear Logic (Plate)
    # If wearing Plate, gain Stability but generate Heat
    if hasattr(player, 'current_tags') and player.current_tags.get('material_plate', 0) > 0:
        # Passive Heat Generation (Insulation/Exertion)
        modify_resource(player, Tags.HEAT, 2, source="Plate Armor", context="Passive", log=False)

    # 1. HP Regen
    if not player.is_in_combat():
        # Routed through modify_resource for telemetry
        modify_resource(player, "hp", 1, source="Regen", context="Passive", log=False)

    # 2. Concentration
    # Gate: Only regen if not full (Delta-Only) and has capacity
    if Tags.CONCENTRATION in player.resources and player.resources.get(Tags.CONCENTRATION, 0) < player.get_max_resource(Tags.CONCENTRATION):
        conc_regen, max_conc = calculate_conc_regen(player)
        modify_resource(player, Tags.CONCENTRATION, conc_regen, source="Regen", context="Passive", log=False)

    # 3. Stamina Regen
    stamina_regen, max_stamina = calculate_stamina_regen(player)
    modify_resource(player, "stamina", stamina_regen, source="Regen", context="Passive", log=False)

    # 4. Heat Dissipation (Legacy Support)
    # Gate: Only decay if Heat > 0
    if Tags.HEAT in player.resources and player.resources.get(Tags.HEAT, 0) > 0:
        heat_decay, max_heat = calculate_heat_decay(player)
        modify_resource(player, Tags.HEAT, -heat_decay, source="Dissipation", context="Passive", log=False)

    # 5. Balance Regeneration (Posture Protocol)
    if 'balance' in player.resources and player.resources.get('balance', 0) < 100:
        bal_regen, max_bal = calculate_balance_regen(player)
        modify_resource(player, "balance", bal_regen, source="Regen", context="Passive", log=False)

    # 6. Status/State Cleanup
    # [V5.0] Auto-clear Panting if stamina recovered > 50%
    if player.resources.get("stamina", 0) > (player.get_max_resource("stamina") * 0.5):
        if "panting" in getattr(player, 'status_effects', {}):
            effects.remove_effect(player, "panting", verbose=True)

    # 7. Kit-Specific Resources (Automated via Registry)
    _process_kit_resources(player)

    # 8. Vitals Snapshot (Every 10s / 5 ticks)
    if player.game.tick_count % 5 == 0:
        telemetry.log_vitals(player)

def _process_kit_resources(player):
    """Iterates through registered resources for the player's kit."""
    kit_id = getattr(player, 'active_kit', {}).get('id')
    if not kit_id: return
    
    defs = resource_registry.get_resources_for_kit(kit_id)
    for rd in defs:
        # 1. Handle Regeneration
        if rd.regen != 0:
            modify_resource(player, rd.id, rd.regen, source="Regen", context="Passive", log=False)
            
        # 2. Handle Decay
        if rd.decay != 0:
            # Check Threshold (if defined)
            if rd.decay_threshold_ticks > 0:
                last_act = player.ext_state.get(kit_id, {}).get('last_attack_tick', 0)
                if (player.game.tick_count - last_act) < rd.decay_threshold_ticks:
                    continue
            
            modify_resource(player, rd.id, -rd.decay, source="Decay", context="Passive", log=False)
