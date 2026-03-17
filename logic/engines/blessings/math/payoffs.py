"""
logic/engines/blessings/math/payoffs.py
Handles deterministic tactical payoffs (The Godless Grammar).
"""
import logging
from logic.core import effects
from logic.core.systems.status import definitions

logger = logging.getLogger("GodlessMUD")

def calculate_environmental_bonus(blessing, player, target, base_power):
    """
    Evaluates bonuses from Terrain and Room conditions.
    """
    bonus = 0
    room = getattr(player, 'room', None)
    if not room: return 0

    identity = getattr(blessing, 'identity_tags', [])
    terrain = getattr(room, 'terrain', '').lower()
    
    # --- Terrain-Based Grammar ---
    if terrain == 'forest' and ("nature" in identity or "beast" in identity):
        bonus += int(base_power * 0.2) # Home field advantage
        
    if terrain in ['mountain', 'stone', 'caves'] and "earth" in identity:
        bonus += int(base_power * 0.2)
        
    if terrain == 'water' and "fire" in identity:
        bonus -= int(base_power * 0.5) # Steam hiss (reduced damage)
        
    if terrain == 'void' and ("arcane" in identity or "void" in identity):
        bonus += int(base_power * 0.25)

    # --- Room-Status Grammar (Weather & Events) ---
    r_effects = getattr(room, 'status_effects', {})
    current_weather = room.get_weather() if hasattr(room, 'get_weather') else "clear"
    
    # Weather Payoffs
    if current_weather == "golden_mist" and "divine" in identity:
        bonus += int(base_power * 0.25)
    if current_weather == "shadow_haze" and ("dark" in identity or "stealth" in identity):
        bonus += int(base_power * 0.25)
    if current_weather == "void_storm" and ("void" in identity or "arcane" in identity):
        bonus += int(base_power * 0.25)
    if current_weather == "pollen_drift" and "nature" in identity:
        bonus += int(base_power * 0.25)
    if current_weather == "blinding_light" and "divine" in identity:
        bonus += int(base_power * 0.15)

    # Room Condition Payoffs
    if "bloodspattered" in r_effects and "dark" in identity:
        bonus += int(base_power * 0.15) # Morbidity bonus
        
    if "frozen_ground" in r_effects and "ice" in identity:
        bonus += int(base_power * 0.2)

    return bonus

def calculate_grammar_bonus(blessing, player, target, base_power):
    """
    Evaluates the 'Grammar' of combat: How tags interact with states.
    Pillar: Deterministic (No RNG) tactical payoffs.
    """
    bonus = 0
    identity = getattr(blessing, 'identity_tags', [])
    
    # 1. State-Based Payoffs
    if target:
        # --- Elemental Payoffs ---
        if "lightning" in identity and effects.has_effect(target, "wet"):
            bonus += base_power # 2x Damage for Shocking wet targets
            
        if "fire" in identity and effects.has_effect(target, "frozen"):
            bonus += base_power # Shatter mechanic
        elif "fire" in identity and effects.has_effect(target, "cold"):
            bonus += int(base_power * 0.5) # Thaw bonus
            
        if "ice" in identity and effects.has_effect(target, "wet"):
            bonus += int(base_power * 0.5) # Snap freeze potential
        elif "ice" in identity and effects.has_effect(target, "burning"):
            # Fire/Ice cancellation could be handled in logic, here we just do neutral damage
            pass

        # --- Vision & Exposure Payoffs ---
        if "divine" in identity and (effects.has_effect(target, "dazzled") or effects.has_effect(target, "blinded")):
            bonus += int(base_power * 1.5) # Holy Smite Payoff
            
        if "psychic" in identity and effects.has_effect(target, "confused"):
            bonus += int(base_power * 1.5) # Mind Shatter Payoff
            
        if "ranged" in identity and effects.has_effect(target, "marked"):
            bonus += int(base_power * 0.2) # Mark for Death bonus
        elif "ranged" in identity and effects.has_effect(target, "hidden"):
            # Harder to hit, but if you do, maybe no bonus? 
            # Hidden usually prevents selection, but if aoe, we handle it.
            pass

        # --- Support & Wind Grammar ---
        if "wind" in identity and "ranged" in identity:
            # Arrows carry further/faster in wind (Global weather check)
            pass

        # --- Positional & Tempo Payoffs ---
        if "beast" in identity and (effects.has_effect(target, "stunned") or effects.has_effect(target, "prone")):
            bonus += base_power # Pack Tactics Payoff
            
        if "finisher" in identity and "dark" in identity:
            # Morbidity Scaling: count debuffs
            t_effects = getattr(target, 'status_effects', {})
            debuff_count = len([s for s in t_effects if s in definitions.HARD_DEBUFFS or s in definitions.SOFT_DEBUFFS])
            bonus += int(base_power * 0.3 * debuff_count)
            
        if "arcane" in identity and "red_mage" in identity and effects.has_effect(player, "dualcast"):
             bonus += base_power # Guaranteed 2x for Dualcast

    # 2. Environmental Payoffs (Terrain/Weather)
    bonus += calculate_environmental_bonus(blessing, player, target, base_power)
         
    return bonus
