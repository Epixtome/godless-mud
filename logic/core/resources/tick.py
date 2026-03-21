"""
logic/core/resources/tick.py
Passive Regeneration and Resource Tick Processing.
"""
from logic.core import resource_registry, effects
from logic.constants import Tags
from utilities import telemetry
from .modify import modify_resource
from .stamina import calculate_stamina_regen
from .mana import calculate_conc_regen
from .posture import calculate_balance_regen, calculate_heat_decay

def process_tick(player):
    """
    Processes all resource regeneration and state checks for a player.
    Called by systems.passive_regen.
    """
    # 1. HP Regen
    if not player.is_in_combat():
        # Routed through modify_resource for telemetry
        modify_resource(player, "hp", 1, source="Regen", context="Passive", log=False)

    # 2. Concentration
    if Tags.CONCENTRATION in player.resources and player.resources.get(Tags.CONCENTRATION, 0) < player.get_max_resource(Tags.CONCENTRATION):
        conc_regen, max_conc = calculate_conc_regen(player)
        modify_resource(player, Tags.CONCENTRATION, conc_regen, source="Regen", context="Passive", log=False)

    # 3. Stamina Regen
    stamina_regen, max_stamina = calculate_stamina_regen(player)
    modify_resource(player, "stamina", stamina_regen, source="Regen", context="Passive", log=False)

    # 4. Heat Dissipation
    if Tags.HEAT in player.resources and player.resources.get(Tags.HEAT, 0) > 0:
        heat_decay, max_heat = calculate_heat_decay(player)
        modify_resource(player, Tags.HEAT, -heat_decay, source="Dissipation", context="Passive", log=False)

    # 5. Balance Regeneration (Posture Protocol)
    if 'balance' in player.resources and player.resources.get('balance', 0) < 100:
        bal_regen, max_bal = calculate_balance_regen(player)
        modify_resource(player, "balance", bal_regen, source="Regen", context="Passive", log=False)

    # 6. Status/State Cleanup
    if player.resources.get("stamina", 0) > (player.get_max_resource("stamina") * 0.5):
        if "panting" in getattr(player, 'status_effects', {}):
            effects.remove_effect(player, "panting", verbose=True)

    # 7. Kit-Specific Resources
    _process_kit_resources(player)

    # 8. Vitals Snapshot
    if player.game.tick_count % 5 == 0:
        telemetry.log_vitals(player)

def _process_kit_resources(player):
    """Iterates through registered resources for the player's kit."""
    kit_id = getattr(player, 'active_kit', {}).get('id')
    if not kit_id: return
    
    defs = resource_registry.get_resources_for_kit(kit_id)
    for rd in defs:
        # 1. Handle Regeneration
        if rd.regen != 0:
            modify_resource(player, rd.id, rd.regen, source="Regen", context="Passive", log=False)
            
        # 2. Handle Decay
        if rd.decay != 0:
            if rd.decay_threshold_ticks > 0:
                last_act = player.ext_state.get(kit_id, {}).get('last_attack_tick', 0)
                if (player.game.tick_count - last_act) < rd.decay_threshold_ticks:
                    continue
            
            modify_resource(player, rd.id, -rd.decay, source="Decay", context="Passive", log=False)
