# Godless MUD: Class Registry (GCA Standard)

> [!NOTE]
> All classes in `logic/modules/` are dynamically loaded by `logic/commands/module_loader.py`. 
> This registry tracks specific hooks into the global `event_engine` for core and complex classes.

---

## 🛠️ DYNAMIC DISCOVERY PROTOCOL
The `module_loader` automatically imports and registers the following files if they exist in a class's module directory:
1.  **`events.py`**: Must contain a `register_events()` function or top-level subscriptions.
2.  **`actions.py`**: Implementation of specific skills/commands.
3.  **`stances.py`**: Stance-specific logic (primarily for Monk/Knight).

---

## 🥋 CORE CLASSES

### MONK
*   **Status**: **V5.3 - URM Integrated**
*   **Module**: `logic/modules/monk/`
*   **Combat Hooks**: `calculate_damage_modifier`, `on_combat_hit`, `on_take_damage`, `combat_check_dodge`
*   **UI Hook**: `on_build_prompt` (Visualizes Chi/Flow)
*   **Special**: Multi-hit scaling (Triple Kick) and Stance effects.

### KNIGHT
*   **Module**: `logic/modules/knight/`
*   **Combat Hooks**: `on_calculate_mitigation`, `on_combat_hit`, `on_take_damage`
*   **Special**: Armor Mastery and reactive Bulwark/Brace triggers.

### BARBARIAN
*   **Status**: **V5.3 - URM & Prompt Integrated**
*   **Module**: `logic/modules/barbarian/`
*   **Life-Cycle Hooks**: `on_combat_tick` (Rage timing), `on_combat_hit` (Fury generation), `on_take_damage` (Pain-to-Fury)
*   **Calculations**: `calculate_extra_attacks` (Fury-based scaling)
*   **UI Hook**: `on_build_prompt` (Visualizes Fury resource directly)

---

## 🐾 PETS & COMPANIONS

### BEASTMASTER
*   **Module**: `logic/modules/beastmaster/`
*   **Hooks**: `on_mob_death` (Pet loss), `after_move` (Follow logic), `on_combat_hit` (Assist strikes)
*   **Persistence**: Pet state (Health/Bond) is sharded in `player.ext_state['beastmaster']`.

### NECROMANCER
*   **Module**: `logic/modules/necromancer/`
*   **Hooks**: `on_entity_death` (Soul Harvesting)
*   **Registration**: Dynamic creation of `Summons` inheriting from `Monster`.

---

## 🪄 ARCANE & HYBRID

### RED MAGE
*   **Module**: `logic/modules/red_mage/`
*   **Combat Hooks**: `on_combat_hit` (Charge generation), `apply_combat_synergies` (Spellstrike)

### ILLUSIONIST
*   **Status**: **V5.3 - URM Integrated**
*   **Module**: `logic/modules/illusionist/`
*   **Vision Hook**: `on_vision_scan` (Disguise/Mirror Image)

### WARLOCK
*   **Status**: **V5.3 - URM Integrated**
*   **Module**: `logic/modules/warlock/`
*   **Resource**: `entropy`
*   **Combat Hooks**: `on_combat_hit` (Life Tap), `calculate_magic_damage` (Entropy battery)

---

## 📜 REGISTRY ADAPTIVE RULE
1.  **GATING**: Every listener **must** check the player's class: `if getattr(player, 'active_class', None) != '[class_name]': return`.
2.  **LINE LIMITS**: If a class `events.py` exceeds 300 lines, it must be sharded (e.g. `combat_events.py`, `world_events.py`).
3.  **CLEAN BORDER**: Assume all data passed to `events.py` is valid. Perform validation in the Facade before firing the event.
