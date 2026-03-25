# Godless MUD: Architectural History & Changelog

> [!IMPORTANT]
> **V4.5: THE ARCHITECTURAL REALIGNMENT**: As of March 7th, 2026, the project has undergone a massive cleanup to resolve drift, shard God Objects, and unify logic domains.

## [[V6.1] ERA: Unified Construction Suite] - 2026-03-17
### Added
- **KIT & STENCIL SYSTEM**: Replaced the legacy "palette" system with a professional "Architect's Drawer." Supported by `kit load` and `kit` (drawer UI).
- **ARCHITECT MODE**: New prefix-less building state enabled via `@building on`. Allows rapid construction (dig, link, paint) without the `@` symbol.
- **SHARDED CONSTRUCTION SUITE**: Decomposed the monolithic builder into specialized shards: `dig.py`, `paint.py`, `edit.py`, `world.py`, `stamp.py`, and `cleanup_commands.py`.
- **STENCIL-AWARE ENGINES**: Updated movement and painting engines to automatically apply attributes (terrain, description, elevation) from the active stencil during construction.

### Changed
- **HOUSEKEEPING**: Purged deprecated `painting.py`, `bulk.py` (placeholder), and consolidated NPC management into `construction/npcs.py`.
- **DIRTY-FLAG PERSISTENCE**: All building commands now strictly utilize the `room.dirty` flag, delegating saves to the server heartbeat to prevent data corruption.
- **WORKFLOW REFINEMENT**: Updated `building_suite_workflow.md` with the new Architect-first construction protocol.

### Fixed
- **SPATIAL NULL GATING**: Fixed a server-crashing `NoneType` error when `spatial.rebuild()` was called during a paint operation if the spatial engine was in mid-refresh.

## [[V6.0] ERA: Admin & Stability] - 2026-03-15
### Fixed
- **DEITY VOID RESOLUTION**: Populated `world.deities` in `proto_loader.py` and added guard clauses to `distribute_favor`. Prevents server-crashing `IndexError` on mob death. (V6.0 Milestone).
- **SOCKET SURVIVABILITY**: Updated `network_engine.py` to pipe connection-killing exceptions to `telemetry.log_bug_report`, ensuring all server crashes are recorded in `bugs.jsonl`.
- **STATUS BYPASS**: Admin commands (`@`) now bypass status effect blocks (Stunned, Bound, etc.), ensuring server-side maintenance is always possible via `input_handler.py`.
- **ITEM TRANSFER INTEGRITY**: Fixed `transfer_item` in `logic/core/items.py` to correctly handle room-to-inventory transfers by referencing `room.items`.

### Changed
- **PERSISTENT ADMIN VISION**: Refactored `@vision` into a persistent toggle that enhances `look`, `inventory`, and `equipment` with ID-level metadata.
- **SURGICAL PURGE**: Enhanced `@purge` to support targeted deletion of specific IDs in both rooms and player inventories.

### Added
- **DEBUG LESSONS LEARNED**: Created `debug_lessons_learned.md` to track recurring architectural pitfalls and improved debugging protocols.
- **`COMMAND_REFERENCE.md`**: Available admin and player commands.
- **`building_suite_workflow.md`**: The master guide for handcrafted world-shaping.
- **`engine_v5_3_refinement.md`**: Summary of V5.3 structural fixes and handover details.

## [[V5.3] ERA: Housekeeping & Bug Resolutions] - 2026-03-14
### Fixed
- **STEALTH STABILITY**: Added property setters for `concealment` and `perception` in `Player` model (Fixes crash on `hide`).
- **COMBAT EXIT SNAPPINESS**: 
    - Forced `handle_target_loss` immediately after a successful `push`.
    - Refined `input_handler.py` to allow movement if the current target is gone/dead, bypassing the 2.0s World Tick delay.
- **SHATTER-LOOP PREVENTION**: Recovery from breakage statuses (`prone`, `off_balance`, `stunned`) now automatically resets `Balance` to 100 in `effects.py`.
- **SCAN DIRECTION**: Corrected Y-axis inversion (North is -Y).

### Changed
- **HELP SHARDING**: Decomposed massive `help.json` into sharded files in `data/help/` (System, Classes, Lore, Tags) as per GEMINI.md standards.
- **PLAYER MODEL REFACTOR**: Sharded class-logic out of `player.py` to `player_logic.py`, reducing core model to 297 lines (Complies with 300-line limit).

### Added
- **SYSTEM ARCHITECTURE ARTIFACT**: Created `system_architecture.md` as a living technical reference for AI agents to reduce token usage during re-analysis.

## [[V5.0] ERA: The Modular Evolution] - 2026-03-13
### Changed
- **GATED MODULE INITIALIZATION**: Refactored `trigger_module_inits` in `persistence.py` to only initialize the `common` module and the player's `active_class`. This prevents omni-init pollution and cross-class state leakage.
- **RESOURCE PURGE PROTOCOL**: Enhanced `sync_resources` to aggressively prune attributes not belonging to the active kit (Fixes "Score Bloat").
- **MONK FINISHER STANDARDIZATION**: Dragon Strike and Iron Palm now utilize the `handle_attack` pipeline instead of `apply_damage`, ensuring full compatibility with Stance multipliers and UTS scaling.
- **UTS CACHE SYSTEM**: Implemented `get_global_tag_count` on `Player` for O(1) tag synergy checks, utilizing a dirty-flagged cache.

### Added
- **DYNAMIC PROMPT VISIBILITY**: Introduced `display_in_prompt: False` metadata flag for status effects, allowing hidden mechanics (Stances/Flow) while keeping them registered.
- **CHARACTER SCORE ENHANCEMENT**: Added `Weight Class` and `Crit Chance` to the `score` summary.

## [[V4.5] ERA: The Great Realignment] - 2026-03-07
### Changed
- **STRUCTURAL HOMOGENIZATION**: Moved root `/core/` to `logic/core/`. Consolidated duplicate handlers into `logic/handlers/`.
- **SHARDED GOD OBJECTS**: 
    - Sharded `systems.py` into `logic/core/systems/` (Combat, Regen, Decay, Weather, AI, Environmental).
    - Extracted messaging and tag resolution from `combat_actions.py` to utilities.
- **SLIM ENTRY POINT**: Refactored `godless_mud.py` to extract Network (`network_engine.py`) and Auth (`auth_handler.py`) logic.
- **DATA-DRIVEN LOOT**: Moved hardcoded loot templates to `data/loot_tables.json`.

### Added
- **CLASS REGISTRY**: Created `documentation/class_registry.md` to track global event subscriptions (GCA Standard).
- **ARCHIVE**: Formally archived legacy manuals in `documentation/archive/`.

## [[V4.5] ERA: Scaling & Calibration] - 2026-03-07
### Added
- **CALIBRATION**: Created `logic/calibration.py` for centralized game balance.
- **POSTURE SYSTEM**: Integrated Off-Balance and Stance effects into the combat pipeline.
- **MONK REFINEMENT**: Fixed Flow Mastery and Dragon Strike scaling.

## [ERA: Script & Tool Reorganization] - 2026-03-06
### Added
- **CENTRALIZED SCRIPTS**: Created `scripts/` with categorized sub-bins: `world/`, `blessings/`, `uts/`, `combat/`, `dev/`.
- **UTILITY PRUNING**: Cleaned `utilities/` to only contain engine-critical dependencies (Telemetry, Mapper).
- **SCRIPT CATALOG**: Created `script_catalog.md` as a high-efficiency reference for all dev tools.

## [ERA: Documentation Anchor] - 2026-03-03
### Added
- **LEGACY SHARDING**: Created `documentation/legacy/` directory to isolate outdated V2.x docs.
- **LEGACY HEADERS**: Added `[!CAUTION]` headers to all files in the legacy folder to prevent architectural drift.
- **ANCHORING**: Consolidated current standards into `ARCHITECTURE.md` (V4.5) and `GAME_DESIGN.md` (V4.5).

## [ERA: Data-Driven Refactor] - 2026-02-14
### CRITICAL ARCHITECTURAL RESET
- **DEPRECATED**: Entire `logic/skills/` and `logic/features/` directories purged.
- **NEW STANDARD**: Implemented Action-Component Architecture.
- **NEW PATHS**: All active logic now resides in `logic/actions/` and `logic/passives/`.
- **DATA-DRIVEN**: 90% of blessings now run through `base_executor.py` via JSON.

### Added
- Created `logic/actions/registry.py` for skill routing.
- Created `logic/passives/hooks.py` for event subscription.
- Standardized `MathBridge` for all scaling calculations.