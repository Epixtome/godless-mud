# GEMINI.md: AI Engineering & Development Guide for Godless

> **Status:** ACTIVE PROTOCOL (V5.3 - Updated from Monk Overhaul)  
> **Target Audience:** Gemini, GCA, Antigravity, and any Agentic AI working on this codebase.  
> **Mandatory Rule:** All structural, logic, and data changes MUST conform to this document. "Quick fixes" or "Scripting-style" code that violates these patterns will be rejected and refactored.

---

## 1. THE FIVE PILLARS OF GODLESS ENGINEERING
These are absolute constraints. Deviating from these pillars introduces technical debt and circular dependencies.

1.  **The "Clean Border" Protocol**: No self-healing logic or `isinstance()` checks inside logic modules. Assume data is 100% valid once it reaches the game logic. Validation happens at the entry point (Persistence or Input Handlers).
2.  **The "Modular Initialization" Protocol**: Core engine MUST only initialize modules relevant to the player's `active_class` plus `common`. Never permit "Omni-init" (loading all 50+ classes per player).
3.  **The "Facade" Import Standard**: Never reach deep into sub-directories. Use `from logic.core import event_engine` instead of the full path. All core systems are exported via `logic/core/__init__.py`. Use Relative Imports (`from . import ...`) for files within the same module.
3.  **The "Event-Driven" Decoupling**: Core engines MUST be class-agnostic. Use the `event_engine` to hook class-specific behaviors. **Never** use `if player.class == 'monk'` inside a core engine. Core display systems (Messaging/Prompts) follow this same pattern.
4.  **The "Surgical" Edit Rule**: Do not rewrite files over 150 lines. Use windowed editing and granular function overrides. Perform a "Pre-and-Post Integrity Audit" (list functions before/after) to ensure no silent deletions.
5.  **The "No-Band-Aid" Policy**: Fix the root cause (logic, path, or schema). Never use `try...except` to mask an `AttributeError` or data mismatch.
6.  **The "Anemic Model" Delegation**: Domain models (`Player`, `Monster`) must not contain active business logic. They are passive data containers that delegate to core facades (e.g., `combat.apply_damage`) or services within `logic/core/`.
7.  **The "Naming Ghost" Protocol**: Maintain absolute naming consistency. Do not use variations like `DGREY` vs `dGREY`. Standardize on **UPPER_CASE** for constants and utilities.

---

## 2. PROJECT STRUCTURE & DOMAINS
Godless is an Asynchronous Domain-Driven engine. Logic is strictly sharded.

- **`logic/core/`**: Providers. Universal, class-agnostic engines (Math, Systems).
    - *Facades*: `combat.py`, `resources.py`, `effects.py`, `quests.py`. All logic must pass through these facades.
- **`logic/handlers/`**: The Interface. Contains `input_handler.py` and `command_manager.py`.
- **`data/`**: The Source of Truth. Sharded JSON for blessings, classes, items, and zones.
- **`utilities/`**: Core Helpers. Engine-facing modules (Mapper, Telemetry, Colors) importable by `logic/`.
- **`scripts/`**: Developer Tools. Categorized autonomous scripts (world, blessings, uts, combat, dev).
- **`godless_mud.py`**: The Entry Point. Initializes all systems and starts the async loop.

---

## 3. THE GODLESS CLASS ARCHITECTURE (GCA)
The GCA is the universal blueprint for all 50+ classes. New classes (Illusionist, Knight, etc.) must follow this structure to ensure compatibility with the core engine.

### A. State Isolation (`state.py`)
Class-specific variables **must not** be added to the base `Player`.
- **Standard**: All class data lives in `player.ext_state['class_name']`.
- **Initialization**: Provide an `initialize_[class](player)` function inside `state.py`.
- **Logic-Data Wall (V5.3)**: Python handles *Event Process/Side Effects*; JSON handles *Potency (Math/Scaling)*. 
    - **No Math in Listeners**: All scaling factors must be defined in JSON `potency_rules`.
    - **Evaluator Gateway**: All damage calculations must pass through `logic.engines.blessings.math_bridge.calculate_power()`.
- **Unified Resource Management (URM)**: Use the `logic/core/resource_registry.py` for class resources (Chi, Fury, Entropy). Never modify `ext_state` directly outside of initialization; use `resources.modify_resource(player, name, delta)`.

### B. Event Hooks (`events.py`)
Class logic is injected into the global loop via `event_engine` subscriptions.
- **Gating**: Every listener **must** check the player's class: `if getattr(player, 'active_class', None) != '[class_name]': return`.
- **Registration**: All `events.py` and `actions.py` for a class MUST be imported in `logic/commands/module_loader.py`.

### C. Companion & Follower Logic
For classes with pets (Beastmaster) or summons (Necromancer).
- **Entity Isolation**: Companions must inherit from `Monster` to leverage room logic naturally.
- **Persistence**: Follower state (Health/Hunger/Sync) lives in the Player's `ext_state`.

---

## 4. DATA & SCHEMA STANDARDS

### A. The "Tags" Field Standard
- **Key**: Always use `"tags": []` for identity and scaling identifiers in JSON.
- **Legacy Support**: While `loader.py` supports `"gear_tags"`, this is deprecated. All new items (e.g., Illusionist gear) must use the `"tags"` key.

---

### A. The "Blueprint + Delta" Architecture
1.  **Shards (`data/zones/*.json`)**: Static world design (rooms, exits, default spawns).
2.  **Live State (`data/live/*.state.json`)**: Persistent deltas (dropped items, boss health, unique status). **Deltas override Blueprints on load.**

### B. Entity Identity Tags
- **UNIQUE**: Registry-checked to prevent quest-breaking duplication or farming.
- **DECAY**: Auto-purged from live state after a period.

---

## 5. EFFICIENT OPERATIONS PROTOCOL (LEAN AGENT)
To minimize token consumption and maximize speed, AI Agents must adhere to the following:

1.  **Skills First**: Use the `.agents/skills/` toolsets for navigation and scaffolding. Avoid `grep` if the Skill already defines the directory map.
2.  **Artifact Memory**: Maintain a "Living Artifact" (e.g., `class_registry.md`) to track system hooks. Do not search the codebase for information already recorded in an artifact.
3.  **Surgical Validation**: Use targeted scripts (like `scripts/dev/combat_sim.py`) to verify logic. Avoid full-system boots for unit-level changes.
4.  **Spatial Shard Restraint**: Never read large world JSON shards (e.g., `data/zones/aetheria.json`) directly. Use the **Map Renderer Skill** (`scripts/dev/map_renderer.py`) or targeted coordinate scripts. If a task requires a full-shard read, you MUST confirm with the USER first.

---

## 6. WORLD LOGIC & MAPPING
- **3D Coordinates**: (X, Y, Z) plus **Elevation** (-5 to +5).
- **Gatekeeper Pattern**: All "Can I act?" checks (Dead, Stunned, Casting) live in `input_handler.py`. Logic actions assume they are permitted to run.

---

## 7. COLLABORATIVE AI PROTOCOLS (GEMINI & GCA)
When multiple AIs work on the same class modules:
1.  **Shard Sovereignty**: All class-specific logic MUST stay within `logic/modules/[class]/`. 
2.  **Standardized Init**: Always use `initialize_[class](player)` in `state.py`.
3.  **The "@" Prefix Protocol**: The `@` character is reserved strictly for Administrative commands.
4.  **Facade Over Late Imports**: Use top-level imports from `logic/core/__init__.py`. **Late imports (inline) are deprecated** and should only be used as a last resort to break unavoidable circular dependencies. **Standard**: All core systems (Messaging, Combat, Resources) must be accessed via their specific `logic/core/` facade.
5.  **The 300-Line Limit**: No Python file may exceed 300 lines. 

---
**Failure to adhere to these standards will cause the Shadow Auditor to flag your code for recursive refactoring.**
