import logging
from utilities.colors import Colors
from logic.core import effects
from utilities import telemetry
from logic.constants import Tags

logger = logging.getLogger("GodlessMUD")

WEIGHT_CLASSES = {
    "light": 0,
    "medium": 20, # 20-50
    "heavy": 51   # > 50
}

WEIGHT_MULTIPLIERS = {
    "light": 1.0,
    "medium": 1.3,
    "heavy": 1.6
}

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
    Sums weight tags from equipped gear and assigns weight_class.
    """
    # Safety: Mobs don't have weight classes or complex gear slots
    if not hasattr(entity, 'equipped_weapon'):
        return "light"

    total_weight = 0
    
    # 1. Inventory Weight
    if hasattr(entity, 'inventory'):
        for item in entity.inventory:
            total_weight += getattr(item, 'weight', 0)
    
    # Check equipped slots
    slots = [
        "equipped_weapon", "equipped_offhand", "equipped_armor",
        "equipped_head", "equipped_neck", "equipped_shoulders",
        "equipped_arms", "equipped_hands", "equipped_finger_l",
        "equipped_finger_r", "equipped_legs", "equipped_feet",
        "equipped_floating", "equipped_mount"
    ]
    
    for slot in slots:
        item = getattr(entity, slot, None)
        if item:
            tags = getattr(item, 'tags', [])
            if isinstance(tags, dict):
                total_weight += tags.get('weight', 0)
            else:
                total_weight += getattr(item, 'weight', 0)
                
    # Assign Class
    w_class = "light"
    if total_weight >= WEIGHT_CLASSES["heavy"]:
        w_class = "heavy"
    elif total_weight >= WEIGHT_CLASSES["medium"]:
        w_class = "medium"
        
    entity.weight_class = w_class
    
    # Legacy support
    entity.is_heavy = (w_class in ["heavy", "titanic"])
    
    return w_class

def modify_resource(entity, resource, amount, source="System", context="Adjustment", log=True):
    """
    Centralized method to modify resources.
    Handles clamping, overflow (Pips), and underflow.
    """
    # Safety Guard: Ensure resource exists (except HP which is an attribute)
    if str(resource).lower() != "hp" and str(resource).lower() != "stamina":
        if not hasattr(entity, 'resources') or resource not in entity.resources:
            return

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

    # 1. Handle Dictionary Resources
    if not hasattr(entity, 'resources'):
        return
    # Get current and max
    current = entity.resources.get(resource, 0)
    
    # Determine Max
    max_val = 100
    if hasattr(entity, 'get_max_resource'):
        max_val = entity.get_max_resource(resource)
    elif resource == Tags.CHI:
        max_val = 5 # Default for mobs/others if not specified
    
    # V2 Physics: Stamina Tax (Weight Class)
    if str(resource).lower() == "stamina" and amount < 0:
        calculate_total_weight(entity)
        wc = getattr(entity, 'weight_class', 'light')
        mult = WEIGHT_MULTIPLIERS.get(wc, 1.0)
        amount = int(amount * mult)

    # Calculate new value
    new_val = current + amount
    
    # Clamp
    if resource == Tags.CONCENTRATION:
        # Allow negative concentration for Overcast mechanics
        # Clamp floor at -100% Max (Debt Ceiling)
        new_val = max(-max_val, min(max_val, new_val))
    elif resource == Tags.HEAT:
        # Heat clamps between 0 and Max
        new_val = max(0, min(max_val, new_val))
    elif str(resource).lower() == "stamina":
        # Stamina clamps between 0 and Max
        new_val = max(0, min(max_val, new_val))
    else:
        new_val = max(0, min(max_val, new_val))
        
    if new_val == current:
        return # Delta-Only: No change
        
    entity.resources[resource] = new_val
    if log:
        telemetry.log_resource_delta(entity, resource, amount, source, context=context)

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
    
    # Weight Class Logic (Light recovers faster)
    if not getattr(player, 'is_heavy', False):
        regen += 5 
        
    # Resting Bonus
    if player.is_resting:
        regen += 10
        
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

    # 5. Vitals Snapshot (Every 10s / 5 ticks)
    if player.game.tick_count % 5 == 0:
        telemetry.log_vitals(player)
