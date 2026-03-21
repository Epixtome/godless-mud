"""
logic/core/math/grammar.py
The 'Verb Calculus' of Godless.
Refactored [V7.0] to a Data-Driven Registry structure.
"""
import logging
import json
import os
from logic.constants import Tags
from logic.core import effects, resources

logger = logging.getLogger("GodlessMUD")

_REGISTRY = None
REGISTRY_PATH = "data/grammar_rules.json"

def get_registry():
    """Lazy-loads the grammar registry."""
    global _REGISTRY
    if _REGISTRY is None:
        try:
            if os.path.exists(REGISTRY_PATH):
                with open(REGISTRY_PATH, 'r', encoding='utf-8') as f:
                    _REGISTRY = json.load(f)
            else:
                _REGISTRY = {"transitions": [], "scaling": {}}
        except Exception as e:
            logger.error(f"Failed to load Grammar Registry: {e}")
            _REGISTRY = {"transitions": [], "scaling": {}}
    return _REGISTRY

def reload_registry():
    """Forces a refresh of the grammar registry from disk."""
    global _REGISTRY
    _REGISTRY = None
    return get_registry()

def resolve_state_transitions(attacker, target, attack_tags):
    """
    Evaluates how the attack's tags interact with the target's current states.
    Reads rules from data/grammar_rules.json.
    """
    if not target or not attacker: return
    
    registry = get_registry()
    active_effects = getattr(target, 'status_effects', {})
    grammar_mods = getattr(attacker, 'current_tags', {}) # Aggregated from gear
    
    # Get Current Terrain for interaction rules
    current_room = getattr(attacker, 'room', None)
    terrain = getattr(current_room, 'terrain', 'plains').lower() if current_room else 'plains'

    for rule in registry.get("transitions", []):
        trigger = rule.get("trigger_tag")
        if trigger not in attack_tags: continue
        
        # 1. State Gating (Required Status)
        req_state = rule.get("required_state")
        if req_state and req_state not in active_effects:
            continue
            
        # 2. Terrain Gating
        req_terrain = rule.get("terrain_interaction")
        if req_terrain and req_terrain != terrain:
            continue
            
        # 3. Apply Resource Modifiers (Heat/Concentration)
        res_target = rule.get("resource_target")
        if res_target:
            mod = rule.get("modifier", 0)
            # Apply gear-based additive grammar mods (e.g. G_HEAT_ADD)
            mod_bonus = grammar_mods.get(f"G_{res_target.upper()}_ADD", 0)
            resources.modify_resource(target, res_target, mod + mod_bonus, source=attacker.name)

        # 4. Apply State Transitions
        result_state = rule.get("result_state")
        if result_state:
            duration = rule.get("duration", 3)
            # Gear Modifier Support (e.g. G_DUR_PRONE)
            dur_bonus = grammar_mods.get(f"G_DUR_{result_state.upper()}", 0)
            effects.apply_effect(target, result_state, duration + dur_bonus, log_event=True)
            
        # 5. Messaging
        if rule.get("message") and hasattr(target, 'send_line'):
            target.send_line(rule.get("message"))
        if rule.get("attacker_message") and hasattr(attacker, 'send_line'):
            attacker.send_line(rule.get("attacker_message"))

    # 6. Global Scaling & Modifiers (Future hooks)
    # [V7.0] Deterministic terrain-physics bypass (e.g. Volley over Mountains)
    if Tags.VOLLEY in attack_tags and terrain == "mountain":
         # Logic hooks for LoS bypass go here in the engine
         pass
