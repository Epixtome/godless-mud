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
