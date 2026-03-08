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
    WEIGHT_HEAT_PENALTY = 0.1  # Heat per point of Weight
    SHARP_DAMAGE_BONUS = 0.02  # % Damage per point of Sharp
    HEAVY_WEIGHT_THRESHOLD = 50 # Total weight (Inventory + Equipment) to trigger Heavy penalties

class CombatBalance:
    VOLTAGE_SCALING = 0.10 # 10% per point of Voltage (Tag Count)