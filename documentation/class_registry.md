# Godless MUD: Class Registry (GCA Standard)

> [!NOTE]
> This registry tracks class-specific hooks into the global `event_engine`. Every committed class MUST update this list to prevent event collisions.

---

## 🥋 CORE CLASSES

### MONK
*   **Module**: `logic/modules/monk/`
*   **State Hook**: `on_combat_tick` (Sync calculation, Flow decay)
*   **Action Hook**: `on_combat_hit` (Stance effects)
*   **Special**: Stance-based damage multipliers handled in `stances.py`.

### KNIGHT
*   **Module**: `logic/modules/knight/`
*   **Subscription**: `on_calculate_mitigation` (Armor Mastery)
*   **Subscription**: `on_combat_hit` (Brace / Bulwark triggers)

### BARBARIAN
*   **Module**: `logic/modules/barbarian/`
*   **Subscription**: `on_combat_tick` (Rage dissipation)
*   **Subscription**: `on_combat_hit` (Frenzy stacks)

---

## 🪄 ARCANE & HYBRID

### RED MAGE
*   **Module**: `logic/modules/red_mage/`
*   **Subscription**: `on_combat_hit` (Charge generation)
*   **Subscription**: `apply_combat_synergies` (Spellstrike triggers)

### ILLUSIONIST
*   **Module**: `logic/modules/illusionist/`
*   **Status**: ACTIVE DEVELOPMENT (V4.5 Expansion)
*   **Subscription**: `on_vision_scan` (Disguise/Mirror Image)

---

## 💀 DIVINE & DEFILED

### DEFILER
*   **Module**: `logic/modules/defiler/`
*   **Subscription**: `on_combat_hit` (Life Siphon)
*   **Subscription**: `on_entity_death` (Soul Harvesting)

---

## 📜 REGISTRY ADAPTIVE RULE
1.  **GATING**: Every listener **must** check the player's class: `if getattr(player, 'active_class', None) != '[class_name]': return`.
2.  **LINE LIMITS**: If a class `events.py` exceeds 300 lines, it must be sharded by event type (e.g. `combat_events.py`, `world_events.py`).
3.  **REGISTRATION**: All new modules must be imported in `logic/commands/module_loader.py`.
