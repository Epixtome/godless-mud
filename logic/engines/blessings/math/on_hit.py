"""
logic/engines/blessings/math/on_hit.py
Handles application of on-hit effects from Blessings and Gear.
"""
import logging
from logic.core import effects
from utilities.colors import Colors

logger = logging.getLogger("GodlessMUD")

def apply_on_hit(player, target, blessing=None):
    """Applies on_hit effects defined in JSON and Gear flags."""
    if getattr(player, 'suppress_on_hit', False): return

    # 1. Blessing-Specific On-Hit
    if blessing:
        on_hit = getattr(blessing, 'on_hit', None)
        if on_hit and isinstance(on_hit, dict):
            status = on_hit.get('apply_status')
            if status:
                duration = on_hit.get('duration', 10)
                is_refresh = effects.has_effect(target, status)
                effects.apply_effect(target, status, duration)
                if not is_refresh and hasattr(target, 'room') and target.room:
                    target.room.broadcast(f"{Colors.YELLOW}{target.name} is knocked {status.replace('_', ' ').title()}!{Colors.RESET}", exclude_player=None)

            bal_dmg = on_hit.get('balance_damage')
            if bal_dmg and target:
                from logic.core.utils import combat_logic
                b_tags = set(getattr(blessing, 'identity_tags', []))
                combat_logic.check_posture_break(target, bal_dmg, source=player, tags=b_tags)

            if on_hit.get('interrupt') and target:
                if hasattr(target, 'current_action') and target.current_action:
                    target.current_action = None
                    if hasattr(target, 'send_line'): target.send_line(f"{Colors.RED}Your concentration is SHATTERED! Action interrupted.{Colors.RESET}")

        # legacy/V2 list effects
        effect_list = getattr(blessing, 'effects', [])
        if effect_list:
            for effect in effect_list:
                eff_id = effect.get('id')
                duration = effect.get('duration', 4)
                tgt_type = effect.get('target', 'enemy')
                if tgt_type == 'enemy' and target: effects.apply_effect(target, eff_id, duration)
                elif tgt_type == 'self' and player: effects.apply_effect(player, eff_id, duration)

    # 2. Universal Tactical Hooks (The Grammar)
    if hasattr(player, 'equipped_weapon') and player.equipped_weapon:
        w = player.equipped_weapon
        w_flags = getattr(w, 'flags', [])
        w_tags = getattr(w, 'tags', [])
        
        # Bleed/Poison
        if "bleed" in w_flags or "bleed" in w_tags:
            effects.apply_effect(target, "bleed", 10)
        if "poison" in w_flags or "poison" in w_tags or effects.has_effect(player, "poisoned_weapon"):
            effects.apply_effect(target, "poison", 10)
            
        # [V6.0] Deterministic Interactions
        # Weight vs Off-Balance = Prone
        if ("weight" in w_tags or "weight" in w_flags) and effects.has_effect(target, "off_balance"):
            effects.apply_effect(target, "prone", 4)
            if hasattr(player, 'send_line'):
                player.send_line(f"{Colors.YELLOW}The weight of your {w.name} crushes the unsteady {target.name} to the ground!{Colors.RESET}")

        # Serrated = Bleed
        if "serrated" in w_tags:
            effects.apply_effect(target, "bleed", 15)

        # Unstable = Confusion
        if "unstable" in w_tags:
            effects.apply_effect(target, "confused", 5)
