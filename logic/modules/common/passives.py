"""
logic/modules/common/passives.py
Domain: Stat-modifiers & Background Logic.

Purpose:
    Handles passive bonuses that do not require active user input but
    respond to game events (ticks, damage taken, etc).

Target Mechanics for Migration:
    - Adrenaline (Combat momentum logic)
    - Iron Skin (Generic mitigation buffs)
    - Shared "Stance" logic that isn't Monk-specific.

Architecture Note:
    This file will likely contain Event Listeners subscribed to event_engine.
"""
