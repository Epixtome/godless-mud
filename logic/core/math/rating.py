"""
logic/core/math/rating.py
[V6.0] Godless Combat Rating (GCR) System.
Scores entities based on Axis focus, State application, Gear, and Environment.
"""
import logging
from logic import calibration
from logic.core import effects

logger = logging.getLogger("GodlessMUD")

def calculate_entity_rating(entity):
    """
    Calculates the final Combat Rating (CR) for a Player or Monster.
    Formula: CR = Σ(AbilityScores) * GearMultipliers * EnvironmentalModifiers
    """
    # 1. Base Ability Scores (Deck or Mob Kit)
    ability_total = 0.0
    
    if getattr(entity, 'is_player', False):
        # Players: Sum of active blessings in the deck
        if hasattr(entity, 'active_kit'):
            deck = entity.active_kit.get('deck', entity.active_kit.get('blessings', []))
            for b_id in deck:
                blessing = entity.game.world.blessings.get(b_id)
                if blessing:
                    ability_total += calculate_ability_score(blessing, entity)
    else:
        # Monsters: Sum of intrinsic ability scores
        # Mobs have axes defined in their tags/metadata
        ability_total = calculate_mob_base_score(entity)

    # 2. Gear Multipliers
    gear_mult = 1.0
    if getattr(entity, 'is_player', False):
        gear_mult = calculate_gear_multipliers(entity)

    # 3. Environmental Modifiers (Terrain, Room States)
    env_mod = calculate_environmental_modifiers(entity)

    final_cr = ability_total * gear_mult * env_mod
    return round(final_cr, 2)

def calculate_ability_score(blessing, entity):
    """
    Scores a single ability based on states applied and axis focus.
    Formula: AbilityScore = Σ(state_applied * axis_multiplier)
    """
    score = 0
    
    # 1. State Application Score
    # Check what states the blessing applies (identity tags or effects field)
    applied_states = getattr(blessing, 'status_effects', [])
    if isinstance(applied_states, dict):
        applied_states = applied_states.keys()
    
    for state in applied_states:
        val = calibration.CombatRating.STATE_VALUES.get(state, 1) # Default 1 if not in table
        score += val

    # 2. Damage Scaling Factor (Normalizing raw power)
    # If it does high damage, it's inherently more powerful even without states
    potency = getattr(blessing, 'potency', 1.0)
    score += (potency * 2.0)

    # 3. Axis Focus Multiplier
    # If the blessing's tags match the class's primary axes, apply multiplier
    axis_mult = 1.0
    class_axes = get_class_axes(entity)
    blessing_tags = getattr(blessing, 'identity_tags', [])
    
    for tag in blessing_tags:
        if tag in class_axes:
            axis_mult = max(axis_mult, calibration.CombatRating.CLASS_FOCUS_MULT)
            
    return score * axis_mult

def calculate_mob_base_score(mob):
    """Calculates CR for a monster based on its tags and axes."""
    score = 0
    tags = getattr(mob, 'tags', [])
    
    # Axis scores derived from tags
    axes_score = 0
    for axis in calibration.CombatRating.AXIS_DEFAULTS.keys():
        if axis in tags:
            axes_score += 2 # Generic axis contribution
    
    # State application score
    # Note: Mob state application is usually hardcoded in combat_logic, 
    # but we check metadata/tags for hints.
    for state in calibration.CombatRating.STATE_VALUES.keys():
        if f"applies_{state}" in tags:
            axes_score += calibration.CombatRating.STATE_VALUES[state]

    # Vitals Scaling
    vitals_mult = (mob.max_hp / 100.0) * (getattr(mob, 'damage', 1) / 5.0)
    
    return (axes_score + 1.0) * max(0.5, vitals_mult)

def calculate_gear_multipliers(player):
    """Calculates gear-based CR multipliers."""
    mult = 1.0
    slots = ["equipped_weapon", "equipped_offhand", "equipped_armor", "equipped_head", 
             "equipped_neck", "equipped_shoulders", "equipped_arms", "equipped_hands", 
             "equipped_legs", "equipped_feet", "equipped_finger_l", "equipped_finger_r",
             "equipped_floating", "equipped_mount"]
             
    for slot in slots:
        item = getattr(player, slot, None)
        if item:
            # [V6.0] Combat Rating Scaling (Primary)
            cr = getattr(item, 'combat_rating', 0)
            if cr > 0:
                # Every 10 GCR on an item adds 10% to the total character multiplier
                mult += (cr / 10.0) * 0.1
            else:
                # Legacy Rarity/Power scaling
                power = getattr(item, 'power', 1.0)
                if power > 1.0:
                    mult += (power - 1.0) * 0.1
            
            # Specific axis modifiers (e.g., Bracers of Stability)
            item_tags = getattr(item, 'tags', [])
            if "endurance" in item_tags:
                mult *= 1.05
            if "vision" in item_tags:
                mult *= 1.05
                
    return mult

def calculate_environmental_modifiers(entity):
    """Evaluates terrain and weather impact on CR."""
    mod = 1.0
    room = getattr(entity, 'room', None)
    if not room: return 1.0
    
    from logic.engines.blessings.math import payoffs
    
    terrain = getattr(room, 'terrain', '').lower()
    # High ground / Choke points handled via metadata flags
    if "high_ground" in room.flags:
        mod *= 1.2
    if "choke_point" in room.flags:
        mod *= 1.1

    # Class-Terrain Affinity
    class_axes = get_class_axes(entity)
    if terrain == 'forest' and 'position' in class_axes:
        mod *= 1.1
    elif terrain == 'mountain' and 'endurance' in class_axes:
        mod *= 1.1
        
    return mod

def get_class_axes(entity):
    """Returns the primary axes for the entity's class (Agnostic)."""
    # GCA standard: classes define axes in their kit/json
    if not getattr(entity, 'is_player', False):
        return [] # Monsters handle axes via tags in calculate_mob_base_score

    # Dynamically resolve from active kit (Master Source of Truth)
    kit_axes = []
    if hasattr(entity, 'active_kit'):
        kit_axes = entity.active_kit.get('axes', [])
    
    return kit_axes
