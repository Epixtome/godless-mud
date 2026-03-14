
# GODLESS LOGIC BLUEPRINT (SYSTEM MAP)
**Version: 5.0 (Event-Driven Domain Standard)**

This document maps the relationships between systems to reduce the cognitive load required for debugging and feature development.

## 1. THE COMMAND FLOW
When a player types a command (e.g., `bash`):

1. **`logic/handlers/input_handler.py`** (The Dispatcher)
   - Checks priority: `Dynamic Skill` -> `Registered Command`.
   - Checks constraints: `Dead`, `Stunned`, `Effect Blocking`.
2. **`logic/commands/skill_commands.py`** (The Skill Router)
   - Verifies if the blessing exists in the player's active kit.
   - Calls the specific skill handler in `logic/modules/[class]/`.
3. **`logic/modules/[class]/actions.py`** (The Domain Handler)
   - Executes custom class behavior.
   - Delegates heavy lifting to **Engines** (Combat, Magic, etc.).

---

## 2. THE COMBAT ENGINE ECOSYSTEM
Combat is a "Loud" system that relies on state consistency.

- **`logic/core/combat.py`** (Standard Facade)
  - Universal entry for `apply_damage` (silent) and `start_combat`.
- **`logic/engines/combat_processor.py`** (The Logic Core)
  - Handles the math: Mitigation -> Scaling -> Potency.
  - Triggers **Broadcasting** via `utilities/combat_formatter.py`.
- **`logic/engines/blessings/math_bridge.py`** (The Data Interpreter)
  - Translates JSON strings into Python numbers for damage and duration.

---

## 3. DATA SHARDING HIERARCHY
Data is sharded to prevent monolithic file corruption and speed up Git operations.

| Data Domain | Shard Directory | Loader Registry |
| :--- | :--- | :--- |
| **Blessings** | `data/blessings/` | `World.blessings` |
| **Monsters** | `data/mobs_shards/` | `World.monsters` |
| **Help** | `data/help/` | `World.help` |
| **Items** | `data/items/` | `World.items` |
| **Zones** | `data/zones/` | `World.rooms` |

---

## 4. CRITICAL RECURSION ALERTS (WATCH OUT)
- **Broadcasting**: `combat_processor` ALWAYS broadcasts. Never call `player.send_line` *and* `execute_attack` in the same handler.
- **Resource Costs**: `magic_engine` handles resource subtraction automatically after a skill handler returns `True`. Do not manually subtract stamina/mana unless bypassing the engine.
- **Auditor**: `Auditor.check_requirements` is the guard. If a skill fails to fire, check `data/blessings/[class].json` for requirement mismatches first.

---

## 5. RECURRING "GROWING PAINS" (COMMON BUG PATTERNS)
- **Missing Tags**: If a mob does 1 damage, it's missing its scaling tags (`light`, `dark`, etc.).
- **Dangling Exits**: Rooms that point to non-existent IDs. Use `@audit` (admin command) or `scripts/dev/audit_data.py`.
- **State Leak**: If a status effect doesn't wear off, check `logic/core/systems/regen.py` to ensure the entity is being ticked.
