"""
logic/modules/common/afflictions.py
Domain: Debuff Application & Removal.

Purpose:
    Handles the application of negative status effects and the logic
    for cleansing them (Medical or Magical).

Target Skills for Migration:
    - Cauterize (Bleed removal)
    - Shake Off (Stun/Daze removal)
    - Cleanse (Generic magic removal)

Architecture Note:
    Should interface heavily with logic.core.status_effects_engine.
"""