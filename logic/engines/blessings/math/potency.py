"""
logic/engines/blessings/math/potency.py
Evaluates complex scaling rules and pip-driven potency modifiers.
"""
import logging
from logic.core import effects

logger = logging.getLogger("GodlessMUD")

def _get_resource_value(player, key):
    """Helper to traverse player state for resources (e.g. 'monk.flow_pips')."""
    if not player or not key: return 0
    parts = key.split('.')
    if len(parts) == 2:
        return player.ext_state.get(parts[0], {}).get(parts[1], 0)
    return 0

def _set_resource_value(player, key, value):
    """Helper to set player state resources (e.g. resetting 'barbarian.momentum')."""
    if not player or not key: return
    parts = key.split('.')
    if len(parts) == 2:
        player.ext_state.setdefault(parts[0], {})[parts[1]] = value

def process_potency_modifiers(blessing, player, target=None):
    """
    Evaluates complex scaling rules defined in JSON shards.
    Pillar 6: Physics and Math should live in Data, not Logic.
    """
    mult = 1.0
    flat = 0
    rules = getattr(blessing, 'potency_rules', [])
    if not isinstance(rules, list):
        rules = [rules] if isinstance(rules, dict) else []

    for rule in rules:
        r_type = rule.get('type')
        if r_type == 'pip_scaling' and player:
            resource_key = rule.get('resource') 
            pips = _get_resource_value(player, resource_key)
            
            tiers = rule.get('tiers', [])
            matched_tier = None
            for tier in tiers:
                if pips <= tier.get('max', 999):
                    matched_tier = tier
                    break
            
            if matched_tier:
                base = matched_tier.get('base', 1.0)
                per = matched_tier.get('mult_per', 0)
                offset = matched_tier.get('offset', 0)
                mult *= (base + (pips - offset) * per)
            
            flat += pips * rule.get('flat_per', 0)

            if rule.get('consume'):
                _set_resource_value(player, resource_key, 0)
            
        elif r_type == 'hp_inverse' and player:
            hp_percent = player.hp / max(1, player.max_hp)
            max_bonus = rule.get('max_bonus', 2.0)
            mult *= (1.0 + (1.0 - hp_percent) * max_bonus)

        elif r_type == 'status_mod' and player:
            status_id = rule.get('status_id')
            if status_id and (effects.has_effect(player, status_id) or effects.has_effect(player, f"{status_id}_echo")):
                mult *= rule.get('multiplier', 1.0)
            
        elif r_type == 'mitigation_mod' and player:
            status_id = rule.get('status_id')
            if status_id and effects.has_effect(player, status_id):
                mult *= rule.get('multiplier', 1.0)
            
    return mult, flat
