"""
logic/constants/calibration.py
Centralized calibration constants for game balance.
The 'All-Seeing Orb' that governs physics and limits.
"""

class MaxValues:
    HP = 250
    DEFENSE = 50
    DAMAGE = 75
    DECK_SIZE = 8  # Maximum active blessings/skills at once

class HeatCoefficients:
    MOVE_BASE = 8
    OVERHEAT_DURATION = 3.0

class ScalingRules:
    # [V6.0] Non-Linear Scaling (Diminishing Returns)
    DR_COEFFICIENT = 0.5   # Controls scaling curve
    BREAKTHROUGH_THRESHOLD = 10 
    BREAKTHROUGH_BONUS = 0.25 # 25% Flat Bonus
    
    WEIGHT_HEAT_PENALTY = 0.1  # Heat per point of Weight
    SHARP_DAMAGE_BONUS = 0.02  # % Damage per point of Sharp
    
    # Weight Class Thresholds (LBS)
    WEIGHT_LIGHT_MAX = 15
    WEIGHT_MEDIUM_MAX = 45 
    HEAVY_WEIGHT_THRESHOLD = 45

class CombatBalance:
    VOLTAGE_SCALING = 0.10 # [DEPRECATED]
    
    # [V5.0] Posture Protocol
    BASE_MITIGATION_LIGHT = 0.05
    BASE_MITIGATION_MEDIUM = 0.15
    BASE_MITIGATION_HEAVY = 0.30
    
    STABILITY_SCALING = 0.3  # Stability subtracts from incoming posture damage
    LETHALITY_MULT = 1.0     # Final damage multiplier
    
    # Stamina Penalties (Weight Based)
    STAMINA_PENALTY_MEDIUM = 1.2
    STAMINA_PENALTY_HEAVY = 1.6

    # [V6.0] Deterministic Tactical Rules
    DODGE_PENALTY_MEDIUM = 0.15
    DODGE_PENALTY_HEAVY = 0.40
    POSTURE_BREAK_DAMAGE_MULT = 1.5

class MaterialGrammar:
    # Material-Element Multipliers (Deterministic Payoffs)
    METAL_LIGHTNING_MULT = 1.50   # Conductivity
    METAL_COLD_PENALTY = 0.10     # Frostbite conduction
    
    WOOD_FIRE_MULT = 1.40        # Flammability
    WOOD_LIGHTNING_RESIST = 0.20 # Insulation
    
    CLOTH_FIRE_MULT = 1.60       # High flammability
    CLOTH_ARCANE_RESONANCE = 0.15 # Mana conduction
    
    VOID_MATERIAL_ARCANE_MULT = 1.25 # Power resonance
    VOID_MATERIAL_HOLY_WEAKNESS = 1.50 # Instability

class CombatRating:
    """[V6.0] Godless Combat Rating (GCR) Constants."""
    STATE_VALUES = {
        "prone": 3,
        "off_balance": 2,
        "blinded": 3,
        "brace": 1,
        "bleeding": 2,
        "hidden": 2,
        "wet": 2,
        "frozen": 4,
        "poisoned": 3,
        "burning": 3,
        "shocked": 2,
        "stunned": 4,
        "confused": 3
    }

    AXIS_DEFAULTS = {
        "position": 1.0,
        "tempo": 1.0,
        "vision": 1.0,
        "endurance": 1.0,
        "elemental": 1.0,
        "utility": 1.0
    }
    
    # Base multipliers for class-specific axis focus
    CLASS_FOCUS_MULT = 1.2
