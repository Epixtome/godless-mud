from logic.core import event_engine
from .effects import defensive, offensive, resource, utility, resonance

def register_all():
    """Registers all passive hooks with the event engine."""
    # Resonance (Universal Scaling)
    resonance.register()
    # Defensive
    event_engine.subscribe("combat_check_dodge", defensive.apply_evasive_step)
    event_engine.subscribe("combat_check_dodge", defensive.apply_rogue_dodge)
    event_engine.subscribe("combat_check_dodge", defensive.apply_ninja_dodge)
    event_engine.subscribe("combat_check_dodge", defensive.apply_parry)
    event_engine.subscribe("on_take_damage", defensive.apply_class_defense)
    event_engine.subscribe("on_take_damage", defensive.apply_buff_mitigation)

    # Offensive
    event_engine.subscribe("calculate_base_damage", offensive.apply_assassin_opening)
    event_engine.subscribe("on_combat_hit", offensive.apply_mark_damage)
    event_engine.subscribe("on_combat_hit", offensive.apply_warrior_damage)
    event_engine.subscribe("calculate_extra_attacks", offensive.apply_haste_extra_attacks)
    event_engine.subscribe("combat_turn_end", offensive.combat_turn_extra_attacks)
    event_engine.subscribe("calculate_damage_modifier", offensive.dragoon_jump_mastery)
    event_engine.subscribe("combat_after_damage", offensive.apply_retribution_damage)
    event_engine.subscribe("calculate_damage_modifier", offensive.alchemist_flask_mastery)
    event_engine.subscribe("calculate_damage_modifier", offensive.healer_passives)
    event_engine.subscribe("on_combat_hit", offensive.malediction_reflection)
    event_engine.subscribe("calculate_base_damage", offensive.apply_weapon_oil_damage)
    event_engine.subscribe("calculate_base_damage", offensive.samurai_iaido_mechanic)
    event_engine.subscribe("combat_check_crit", offensive.third_eye_crit_bonus)
    event_engine.subscribe("calculate_base_damage", offensive.engineer_construct_mastery)
    event_engine.subscribe("combat_check_crit", offensive.gambler_luck)
    event_engine.subscribe("calculate_base_damage", offensive.beast_master_damage_bonus)
    event_engine.subscribe("calculate_damage_modifier", offensive.black_mage_power)

    # Resource
    event_engine.subscribe("combat_after_damage", resource.apply_berserker_momentum)
    event_engine.subscribe("combat_turn_start", resource.combat_turn_momentum)
    event_engine.subscribe("on_calculate_skill_cost", resource.black_mage_cost)
    event_engine.subscribe("on_calculate_skill_cost", resource.red_mage_momentum)
    event_engine.subscribe("combat_after_damage", resource.red_mage_melee_concentration)
    event_engine.subscribe("on_calculate_skill_cost", resource.apply_mana_reduction)
    event_engine.subscribe("on_status_removed", resource.handle_posture_recovery)

    # --- Systems ---
    from logic.factories.mob_loot_system import on_mob_spawned
    event_engine.subscribe("mob_spawned", on_mob_spawned)

    # Utility
    event_engine.subscribe("on_enter_room", utility.trap_trigger)
    event_engine.subscribe("combat_after_damage", utility.blue_mage_learning)
    event_engine.subscribe("magic_calculate_cooldown", utility.chronomancer_cooldown_reduction)
