# Godless MUD: Architectural History & Changelog

> [!IMPORTANT]
> **V4.5: THE ARCHITECTURAL REALIGNMENT**: As of March 7th, 2026, the project has undergone a massive cleanup to resolve drift, shard God Objects, and unify logic domains.

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