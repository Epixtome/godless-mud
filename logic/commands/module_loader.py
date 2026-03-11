"""
Centralized module loader for Godless classes.
Shards the registration to keep skill_commands.py under the 300-line limit.
"""

def register_all_modules():
    """Main entry point to register all modules."""
    _register_common_modules() # Common skills can be overridden by specialized classes
    _register_core_modules()
    _register_martial_modules()
    _register_arcane_modules()
    _register_divine_modules()
    _register_hybrid_modules()

def _register_core_modules():
    """Original core system registrations."""
    from logic.modules.monk import stances, monk, events as monk_events
    monk_events.register_events()
    from logic.modules.knight import knight, events as knight_events
    knight_events.register_events()
    from logic.modules.barbarian import actions as barb_actions, events as barb_events
    barb_events.register_events()
    from logic.modules.mage import actions as mage_actions, events as mage_events
    mage_events.register_events()
    from logic.modules.assassin import actions as assassin_actions, events as assassin_events
    assassin_events.register_events()
    from logic.modules.cleric import actions as cleric_actions, events as cleric_events
    cleric_events.register_events()
    from logic.modules.defiler import actions as defiler_actions, events as defiler_events
    defiler_events.register_events()
    from logic.modules.beastmaster import actions as bm_actions, events as bm_events
    bm_events.register_events()

def _register_martial_modules():
    """Batch 1: Martial Front."""
    from logic.modules.warrior import events as warrior_ev
    from logic.modules.archer import events as archer_ev
    archer_ev.register_events()
    from logic.modules.berserker import events as berserker_ev
    from logic.modules.dragoon import events as dragoon_ev
    from logic.modules.gunner import events as gunner_ev
    from logic.modules.hunter import events as hunter_ev
    from logic.modules.ninja import events as ninja_ev
    from logic.modules.samurai import events as samurai_ev
    from logic.modules.soldier import events as soldier_ev
    from logic.modules.thief import events as thief_ev

def _register_arcane_modules():
    """Batch 2: Arcane Council."""
    from logic.modules.alchemist import events as alchemist_ev
    from logic.modules.black_mage import events as black_mage_ev
    from logic.modules.blue_mage import events as blue_mage_ev
    from logic.modules.grey_mage import events as grey_mage_ev
    from logic.modules.magician import events as magician_ev
    from logic.modules.sorcerer import events as sorcerer_ev
    from logic.modules.temporalist import events as temporalist_ev
    from logic.modules.warlock import actions, events as warlock_ev
    from logic.modules.witch import events as witch_ev
    from logic.modules.red_mage import events as red_mage_ev

def _register_divine_modules():
    """Batch 3: Divine and Special."""
    from logic.modules.paladin import events as paladin_ev
    from logic.modules.priest import events as priest_ev
    from logic.modules.necromancer import events as necromancer_ev
    from logic.modules.summoner import events as summoner_ev
    from logic.modules.soul_reaver import events as soul_reaver_ev
    from logic.modules.soul_weaver import events as soul_weaver_ev
    from logic.modules.druid import events as druid_ev
    from logic.modules.elementalist import events as elementalist_ev
    from logic.modules.bard import events as bard_ev
    from logic.modules.dancer import events as dancer_ev
    from logic.modules.guardian import events as guardian_ev

def _register_hybrid_modules():
    """Batch 4: Tech and Hybrid."""
    from logic.modules.engineer import events as engineer_ev
    from logic.modules.machinist import events as machinist_ev
    from logic.modules.chemist import events as chemist_ev
    from logic.modules.puppet_master import events as puppet_master_ev
    from logic.modules.gambler import events as gambler_ev
    from logic.modules.illusionist import events as illusionist_ev
    from logic.modules.ranger import events as ranger_ev
    from logic.modules.rogue import events as rogue_ev
    from logic.modules.shadow_blade import events as shadow_blade_ev
    from logic.modules.shadow_dancer import events as shadow_dancer_ev
    from logic.modules.twin import events as twin_ev
    from logic.modules.wanderer import events as wanderer_ev
    from logic.modules.death_knight import events as death_knight_ev

def _register_common_modules():
    """Common martial and utility modules."""
    from logic.modules.common import offensive, defensives, maneuvers, utility as common_utility
