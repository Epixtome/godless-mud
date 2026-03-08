"""
logic/core/utils/calibration.py
Centralized calibration constants for game balance.
"""

class MaxValues:
    HP = 250
    DEFENSE = 50
    DAMAGE = 75

class HeatCoefficients:
    MOVE_BASE = 8
    OVERHEAT_DURATION = 3.0

class ScalingRules:
    WEIGHT_HEAT_PENALTY = 0.1
    SHARP_DAMAGE_BONUS = 0.02
