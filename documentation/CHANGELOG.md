# Godless MUD: Architectural History & Changelog

> [!IMPORTANT]
> **V4.5: THE ARCHITECTURAL REALIGNMENT**: As of March 7th, 2026, the project has undergone a massive cleanup to resolve drift, shard God Objects, and unify logic domains.

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