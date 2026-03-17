# Godless: Event Bus Topology
> Auto-generated Living Artifact mapping Pub/Sub architecture.

## Event: `after_move`
**Dispatched By (Triggers):**
- logic\commands\movement_commands.py (Line 133)

**Subscribed By (Listeners):**
- logic\core\quests.py (Line 6)
- logic\modules\beastmaster\events.py (Line 179)
- logic\modules\illusionist\events.py (Line 106)

---
## Event: `before_move`
**Dispatched By (Triggers):**
- logic\commands\movement_commands.py (Line 31)

**Subscribed By (Listeners):**
- *(No listeners found)*

---
## Event: `calculate_base_damage`
**Dispatched By (Triggers):**
- logic\core\combat.py (Line 33)
- logic\core\combat.py (Line 38)

**Subscribed By (Listeners):**
- logic\passives\hooks.py (Line 30)
- logic\passives\hooks.py (Line 27)
- logic\passives\hooks.py (Line 17)
- logic\passives\hooks.py (Line 32)
- logic\passives\hooks.py (Line 28)

---
## Event: `calculate_damage_modifier`
**Dispatched By (Triggers):**
- logic\engines\blessings\math_bridge.py (Line 161)
- logic\core\combat.py (Line 64)

**Subscribed By (Listeners):**
- logic\modules\knight\events.py (Line 10)
- logic\passives\effects\resonance.py (Line 47)
- logic\passives\hooks.py (Line 33)
- logic\passives\hooks.py (Line 22)
- logic\passives\hooks.py (Line 25)
- logic\modules\warlock\events.py (Line 11)
- logic\modules\monk\events.py (Line 9)
- logic\passives\hooks.py (Line 24)

---
## Event: `calculate_disarm_chance`
**Dispatched By (Triggers):**
- logic\modules\common\offensive.py (Line 59)

**Subscribed By (Listeners):**
- *(No listeners found)*

---
## Event: `calculate_extra_attacks`
**Dispatched By (Triggers):**
- logic\engines\combat_processor.py (Line 133)

**Subscribed By (Listeners):**
- logic\passives\hooks.py (Line 20)
- logic\modules\barbarian\events.py (Line 8)
- logic\modules\warlock\events.py (Line 14)

---
## Event: `calculate_steal_chance`
**Dispatched By (Triggers):**
- logic\actions\handlers\thievery_actions.py (Line 62)

**Subscribed By (Listeners):**
- *(No listeners found)*

---
## Event: `combat_after_damage`
**Dispatched By (Triggers):**
- logic\engines\combat_actions.py (Line 195)

**Subscribed By (Listeners):**
- logic\passives\hooks.py (Line 36)
- logic\passives\hooks.py (Line 23)
- logic\passives\hooks.py (Line 40)
- logic\passives\hooks.py (Line 50)

---
## Event: `combat_check_crit`
**Dispatched By (Triggers):**
- *(No direct dispatches found - possibly dynamic)*

**Subscribed By (Listeners):**
- logic\passives\hooks.py (Line 29)
- logic\passives\hooks.py (Line 31)

---
## Event: `combat_check_dodge`
**Dispatched By (Triggers):**
- logic\engines\combat_actions.py (Line 88)

**Subscribed By (Listeners):**
- logic\passives\hooks.py (Line 9)
- logic\modules\monk\events.py (Line 12)
- logic\passives\hooks.py (Line 10)
- logic\passives\hooks.py (Line 11)
- logic\passives\hooks.py (Line 12)

---
## Event: `combat_turn_end`
**Dispatched By (Triggers):**
- logic\engines\combat_processor.py (Line 157)

**Subscribed By (Listeners):**
- logic\passives\hooks.py (Line 21)

---
## Event: `combat_turn_start`
**Dispatched By (Triggers):**
- logic\engines\combat_processor.py (Line 91)

**Subscribed By (Listeners):**
- logic\core\systems\ai\__init__.py (Line 106)
- logic\passives\hooks.py (Line 37)

---
## Event: `effect_tick`
**Dispatched By (Triggers):**
- logic\core\effects.py (Line 146)

**Subscribed By (Listeners):**
- logic\core\systems\status\ticks.py (Line 43)

---
## Event: `magic_calculate_cooldown`
**Dispatched By (Triggers):**
- logic\engines\magic_engine.py (Line 50)

**Subscribed By (Listeners):**
- logic\passives\hooks.py (Line 51)
- logic\engines\stance_hooks.py (Line 19)

---
## Event: `magic_calculate_cost`
**Dispatched By (Triggers):**
- logic\engines\magic_engine.py (Line 138)

**Subscribed By (Listeners):**
- *(No listeners found)*

---
## Event: `magic_on_blessing_cast`
**Dispatched By (Triggers):**
- logic\engines\magic_engine.py (Line 135)

**Subscribed By (Listeners):**
- logic\modules\red_mage\events.py (Line 39)

---
## Event: `mob_spawned`
**Dispatched By (Triggers):**
- logic\core\services\world_service.py (Line 51)
- logic\mob_manager.py (Line 59)

**Subscribed By (Listeners):**
- logic\passives\hooks.py (Line 46)

---
## Event: `on_build_prompt`
**Dispatched By (Triggers):**
- *(No direct dispatches found - possibly dynamic)*

**Subscribed By (Listeners):**
- logic\modules\defiler\events.py (Line 10)
- logic\modules\engineer\events.py (Line 13)
- logic\modules\temporalist\events.py (Line 13)
- logic\modules\cleric\events.py (Line 9)
- logic\modules\paladin\events.py (Line 13)
- logic\modules\rogue\events.py (Line 13)
- logic\modules\warrior\events.py (Line 13)
- logic\modules\grey_mage\events.py (Line 13)
- logic\modules\barbarian\events.py (Line 12)
- logic\modules\wanderer\events.py (Line 17)
- logic\modules\bard\events.py (Line 13)
- logic\modules\magician\events.py (Line 13)
- logic\modules\monk\events.py (Line 13)
- logic\modules\dancer\events.py (Line 13)
- logic\modules\alchemist\events.py (Line 13)
- logic\modules\soul_reaver\events.py (Line 13)
- logic\modules\necromancer\events.py (Line 13)
- logic\modules\witch\events.py (Line 13)
- logic\modules\black_mage\events.py (Line 13)
- logic\modules\shadow_blade\events.py (Line 13)
- logic\modules\berserker\events.py (Line 13)
- logic\modules\shadow_dancer\events.py (Line 13)
- logic\modules\sorcerer\events.py (Line 13)
- logic\modules\beastmaster\events.py (Line 178)
- logic\modules\summoner\events.py (Line 13)
- logic\modules\machinist\events.py (Line 13)
- logic\modules\red_mage\events.py (Line 38)
- logic\modules\druid\events.py (Line 13)
- logic\modules\elementalist\events.py (Line 13)
- logic\modules\chemist\events.py (Line 13)
- logic\modules\hunter\events.py (Line 13)
- logic\modules\soul_weaver\events.py (Line 13)
- logic\modules\puppet_master\events.py (Line 13)
- logic\modules\soldier\events.py (Line 13)
- logic\modules\thief\events.py (Line 13)
- logic\modules\twin\events.py (Line 13)
- logic\modules\warlock\events.py (Line 10)
- logic\modules\illusionist\events.py (Line 104)
- logic\modules\ranger\events.py (Line 13)
- logic\modules\mage\events.py (Line 9)
- logic\modules\archer\events.py (Line 9)
- logic\modules\dragoon\events.py (Line 13)
- logic\modules\knight\events.py (Line 9)
- logic\modules\assassin\events.py (Line 9)
- logic\modules\gunner\events.py (Line 13)
- logic\modules\priest\events.py (Line 13)
- logic\modules\ninja\events.py (Line 13)
- logic\modules\samurai\events.py (Line 13)
- logic\modules\gambler\events.py (Line 13)
- logic\modules\death_knight\events.py (Line 13)
- logic\modules\blue_mage\events.py (Line 13)

---
## Event: `on_calculate_mitigation`
**Dispatched By (Triggers):**
- logic\engines\combat_actions.py (Line 110)

**Subscribed By (Listeners):**
- logic\modules\monk\events.py (Line 11)
- logic\modules\barbarian\events.py (Line 9)
- logic\modules\illusionist\events.py (Line 105)

---
## Event: `on_calculate_skill_cost`
**Dispatched By (Triggers):**
- logic\engines\blessings\auditor.py (Line 61)

**Subscribed By (Listeners):**
- logic\passives\hooks.py (Line 38)
- logic\passives\hooks.py (Line 39)
- logic\passives\hooks.py (Line 41)

---
## Event: `on_check_requirements`
**Dispatched By (Triggers):**
- logic\engines\blessings\auditor.py (Line 92)

**Subscribed By (Listeners):**
- *(No listeners found)*

---
## Event: `on_combat_hit`
**Dispatched By (Triggers):**
- logic\actions\skill_utils.py (Line 66)
- logic\engines\combat_actions.py (Line 193)

**Subscribed By (Listeners):**
- logic\passives\hooks.py (Line 26)
- logic\modules\defiler\events.py (Line 9)
- logic\modules\barbarian\events.py (Line 6)
- logic\passives\hooks.py (Line 19)
- logic\core\systems\engagement.py (Line 57)
- logic\passives\hooks.py (Line 18)
- logic\modules\beastmaster\events.py (Line 180)

---
## Event: `on_combat_tick`
**Dispatched By (Triggers):**
- logic\core\systems\regen.py (Line 9)

**Subscribed By (Listeners):**
- logic\modules\beastmaster\events.py (Line 176)
- logic\modules\barbarian\events.py (Line 11)
- logic\modules\monk\events.py (Line 14)

---
## Event: `on_death`
**Dispatched By (Triggers):**
- logic\core\combat.py (Line 130)
- logic\core\combat.py (Line 102)

**Subscribed By (Listeners):**
- logic\engines\combat_lifecycle.py (Line 236)

---
## Event: `on_enter_room`
**Dispatched By (Triggers):**
- logic\core\services\world_service.py (Line 116)

**Subscribed By (Listeners):**
- logic\passives\hooks.py (Line 49)
- logic\modules\assassin\events.py (Line 10)
- logic\modules\illusionist\events.py (Line 107)

---
## Event: `on_exit_room`
**Dispatched By (Triggers):**
- logic\commands\movement_commands.py (Line 56)

**Subscribed By (Listeners):**
- *(No listeners found)*

---
## Event: `on_mob_death`
**Dispatched By (Triggers):**
- logic\engines\combat_lifecycle.py (Line 122)

**Subscribed By (Listeners):**
- logic\modules\beastmaster\events.py (Line 177)
- logic\core\quests.py (Line 7)

---
## Event: `on_skill_execute`
**Dispatched By (Triggers):**
- logic\modules\common\utility.py (Line 29)

**Subscribed By (Listeners):**
- *(No listeners found)*

---
## Event: `on_status_applied`
**Dispatched By (Triggers):**
- logic\core\effects.py (Line 58)

**Subscribed By (Listeners):**
- logic\modules\barbarian\events.py (Line 10)
- logic\modules\warlock\events.py (Line 12)

---
## Event: `on_status_removed`
**Dispatched By (Triggers):**
- logic\core\effects.py (Line 88)

**Subscribed By (Listeners):**
- logic\modules\illusionist\events.py (Line 108)
- logic\engines\blessings\auditor.py (Line 260)
- logic\passives\hooks.py (Line 42)
- logic\modules\warlock\events.py (Line 13)

---
## Event: `on_take_damage`
**Dispatched By (Triggers):**
- logic\core\combat.py (Line 119)

**Subscribed By (Listeners):**
- logic\modules\monk\events.py (Line 10)
- logic\passives\hooks.py (Line 13)
- logic\modules\beastmaster\events.py (Line 175)
- logic\passives\hooks.py (Line 14)
- logic\modules\barbarian\events.py (Line 7)
- logic\modules\mage\events.py (Line 10)

---
## Event: `quest_completed`
**Dispatched By (Triggers):**
- logic\core\quests.py (Line 98)

**Subscribed By (Listeners):**
- *(No listeners found)*

---
## Event: `room_combat_tick`
**Dispatched By (Triggers):**
- logic\engines\combat_processor.py (Line 42)

**Subscribed By (Listeners):**
- logic\core\systems\ai\__init__.py (Line 105)

---
