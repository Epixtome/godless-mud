"""
logic/core/resources/modify.py
Central Modifier Engine for Resources.
"""
import logging
from logic.core import resource_registry
from logic.constants import Tags
from utilities import telemetry
from logic import calibration

logger = logging.getLogger("GodlessMUD")

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
                from logic.core import combat
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

def get_resource(entity, resource):
    """
    Returns the current value of a resource, handling storage location (ext_state or resources).
    """
    if str(resource).lower() == "hp":
        return getattr(entity, "hp", 0)

    kit_id = getattr(entity, "active_kit", {}).get("id", "")
    definition = resource_registry.get_definition(str(kit_id), resource) if kit_id else None

    if definition and hasattr(entity, "ext_state") and entity.active_class:
        target_dict = entity.ext_state.get(entity.active_class, {})
        return target_dict.get(resource, 0)
    
    if hasattr(entity, "resources"):
        return entity.resources.get(resource, 0)
    
    return 0
    
def get_max_resource(entity, resource):
    """
    [V7.2] Returns the maximum capacity for a resource.
    Resolves via ResourceDefinition, max_getter, or fallback (100).
    """
    if str(resource).lower() == "hp":
        return getattr(entity, "max_hp", 100)
        
    kit_id = getattr(entity, 'active_kit', {}).get('id', '')
    definition = resource_registry.get_definition(str(kit_id), resource) if kit_id else None
    
    if definition:
        if definition.max_getter:
            return definition.max_getter(entity)
        return definition.max
    
    # Fallback to model-defined helper or generic 100
    if hasattr(entity, 'get_max_resource'):
        return entity.get_max_resource(resource)
        
    return 100
