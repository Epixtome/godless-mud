# Changelog

## [Unreleased]
### Added
- **Zone Generator**: Created `utilities/zone_generator.py` for procedural creation of zones based on config templates.
- **New Zones**: Generated `elderwood`, `light_mine` (Crystal Caverns), `dark_swamp` (Obsidian Marsh), `light_cap` (Sanctum), `dark_cap` (Noxus), `instinct_cap` (Ironbark), and `light_farm` (Golden Fields).
- **Reputation System**: Added `reputation` to Player model. Added `Gatekeeper` mob tag which triggers aggro on players with low reputation.
- **Body Parts**: Added `body_parts` to Monster model, allowing specific targeting (e.g., Hydra heads, Crab shell) via the `sunder` skill.
- **Skills**: Implemented `track` (find direction to mob), `sunder` (damage body parts), `howl` (pet rally), and `raise_dead` (necromancy).
- **Admin Tools**: Added `@link` and `@unlink` to manually connect rooms/zones. Added `@applyeffect` for testing status effects.
- **Status Effects**: Added `bleed` (DoT) and `stun` (Action Block).

### Changed
- **Map System**: Rewrote `logic/mapper.py` to use Breadth-First Search (BFS) instead of coordinate scanning. This allows the map to correctly display linked zones even if their coordinates are distant.
- **Farsight**: Converted `farsight` from a passive skill to an active spell (`cast farsight <dir>`). It now ignores Fog of War, allowing true scouting of unexplored areas.
- **Digging**: Updated `@dig` to prevent merging rooms from different zones that share the same coordinates.
- **Combat**: Updated `combat_processor.py` to check for `aggressive` and `gatekeeper` mobs before processing player turns.
- **Loader**: Updated `core/loader.py` to use `glob` for loading zone files and added a fallback for flat JSON structures.

### Previous Changes
- **Rogue Class**: Added a full suite of Rogue abilities to `blessings.json` and the `Rogue` class definition to `classes.json`.
- **Elementalist Class**: Added elemental synergy spells for the `Elementalist` class and its definition.
- **Paladin Class**: Added `Paladin` class definition and a suite of Light/STR blessings (Smite, Lay on Hands, etc.) assigned to Solas.
- **Cleric Class**: Added `Cleric` class definition and a suite of Light/Healing/Protection blessings assigned to Lumos, Sophia, and Fortuna.
- **Barbarian Class**: Added `Barbarian` class definition and a suite of Instinct/Martial/Rage blessings assigned to Krog.
- **Knight Class**: Added `Knight` class definition and a suite of Light/Tactics/Mount blessings assigned to Solas, Celeris, and Fortuna.
- **Warrior Class**: Added `Warrior` class definition and a suite of Martial/Weapon/Control blessings assigned to Krog, Solas, Celeris, and Malice.
- **Berserker Class**: Added `Berserker` class definition and a suite of Rage blessings (Bloodlust, Twin Axes) assigned to Krog, Feral, and Ursus.
- **Alchemist Class**: Added `Alchemist` class definition and a suite of Alchemy blessings assigned to Lumos, Vex, Echo, Sophia, Celeris, and Aegis.
- **State System**: Upgraded `blessings_engine` to check for player states (`is_mounted`, `stance`) and equipment (`shield`).
- **Mount System**: Implemented `mount` and `dismount` commands.
- **Action Pacing**: Reworked action pacing to be opt-in via `max_per_round` in `blessings.json`, removing the global skill/spell limit per round.
- **Scout & Ranger Classes**: Added class definitions and blessings for `Scout` (Farsight, Eagle Eye) and `Ranger` (Marksmanship).
- **Map System**: Implemented `map` command with Fog of War based on visited rooms.
- **Ranged Combat**: Implemented `aim` to lock targets and `track` to find them, enabling ranged skill execution via `skills.py`.
- **Gods' Hall**: Created a new test zone, The Gods' Hall, accessible from the Hub, containing avatars of all 18 deities for easy testing of the blessing and class systems.
- **Zone System**: Added `Zone` model and updated `Room` to support X, Y, Z coordinates and Zone IDs.
- **Z-Plane Mapping**: Updated `mapper.py` to filter rooms by elevation (Z-axis).
- **Door Logic**: Added `Door` class and updated `Room` to support open/closed/locked states on exits.
- **Command Manager**: Created `logic/command_manager.py` for centralized, safe command registration and error handling.
- **Action Modules**: Refactored `logic/basic.py` into atomic modules in `logic/actions/` (movement, combat, items, etc.).
- **Help System**: Dynamic help menu that lists commands, blessings, and lore.
- **Gatekeeper**: Implemented centralized action validation in `input_handler.py` to handle states like "Stunned" or "Dead".
- **Status Effects**: Added `status_effects_engine.py` and `data/status_effects.json` to manage buffs and debuffs.

### Changed
- **Commune**: Restored the state-based "trance" for `commune`. Players now enter a dedicated interaction mode when communing with a deity.
- **Deck**: Restored `deck` as a standalone command (`logic/actions/deck.py`) usable both inside and outside of communion.
- **Deities**: Cleaned up and standardized the full list of 18 deities in `data/deities.json`.
- **Refactor**: Split `basic.py` into `logic/actions/` to follow the Prime Directive.
- **Refactor**: Created `logic/common.py` to resolve circular dependencies in `movement` and `information`.
- **Refactor**: Updated `logic/actions/information.py` to use `logic/common.py` and safe imports.
- **Refactor**: Performed a full import sweep and corrected architectural violations in `admin.py` and `spells.py` to prevent circular dependencies.
- **Refactor**: Centralized dice rolling logic into `utilities/utils.py` and updated `combat_engine.py` to use it, removing redundant code.
- **Refactor**: Decoupled combat logic from `systems.py` into `logic/engines/combat_processor.py`. This stabilizes the combat loop against hot-reloads and separates scheduling from execution.
- **Documentation**: Consolidated `PRIME_DIRECTIVE.md` into `gemini.md` to establish a Single Source of Truth for coding standards.
- **Maintenance**: Cleaned up accidental nested directories (`c/`) and enforced file locations for `crafting_engine` and `common.py`.
- **Maintenance**: Deleted misplaced `data/systems.py` duplicate; confirmed `logic/systems.py` is the authority for heartbeat logic.
- **Maintenance**: Deleted duplicate `logic/actions/common.py` and consolidated helpers into `logic/common.py`.
- **Maintenance**: Performed deep directory cleanup (removed `models_old`, `logic/godless_mud.py`, `registry.py`, `dice.py`).
- **Maintenance**: Merged root `deck.py` features into `logic/actions/deck.py` and removed root duplicates (`commune.py`, `class_engine.py`).
- **Architecture**: Implemented `utilities/integrity.py` to automatically detect misplaced files and data drift at startup.
- **Restoration**: Re-implemented `consider` command in `logic/actions/combat.py` (lost during legacy cleanup).
- **Feature**: Added `sacrifice` command to `combat.py` for gaining favor from corpses.
- **Feature**: Added `@setdeity` admin command to assign deities to rooms.
- **Refactor**: Moved crafting recipes from hardcoded dictionary to `data/recipes.json`.
- **Feature**: Added index targeting (e.g., `kill 2.skeleton`) via `logic/common.py`.
- **Feature**: Updated `look` to support looking inside containers (`look in corpse`).
- **Fix**: Updated `Beast Master` class requirements in `data/classes.json` to match existing blessing tags.
- **Feature**: Split `score` into `score` (stats/manifestations) and `attributes` (sheet/gold/favor).
- **Fix**: Restored `logic/engines/crafting_engine.py` to the correct directory to resolve `ModuleNotFoundError`.
- **Mapper**: Switched from coordinate-based iteration to Breadth-First Search (BFS) for line-of-sight mapping (respecting doors).
- **Input Handling**: Hardened `input_handler.py` against empty inputs and integrated with `CommandManager`.
- **Cleanup**: Removed legacy command files (`movement.py`, `combat.py`, etc.) from the `logic/` root to enforce the new `logic/actions/` structure.
- **Renaming**: Renamed `magic.py` to `spells.py` in `logic/actions/` to avoid namespace conflicts.
- **Visuals**: Updated map rendering to a compact, retro style using `#` for rooms and `@` for the player.
- **Robustness**: Implemented `open` and `close` commands with reciprocal door synchronization.
- **Migration**: Completed migration of `combat`, `items`, and `spells` into atomic action modules.
- **Architecture**: Enforced `MathBridge` usage in `spells.py` and `input_handler.py` to centralize scaling logic.
- **Refactor**: Moved all engine logic (`combat`, `magic`, `class`, `synergy`) into `logic/engines/` to enforce strict layering.
- **Standards**: Established PEP 8 naming conventions in the Prime Directive.
- **Persistence**: Implemented `Player.save()` and `Player.get_prompt()` to fix runtime crashes.
- **Features**: Added `social.py` (say, emote) and `help_system.py` (dynamic help list) to `logic/actions/`.
- **Economy**: Implemented `shop.py` (buy/sell/list) and `commune.py` (buy blessings with Favor).
- **Deck Building**: Implemented `deck.py` with `memorize` and `forget` commands to manage equipped blessings.
- **Combat Visuals**: Added descriptive damage text and health status indicators in `systems.py`.
- **Map Visuals**: Improved map stability with grid anchors and updated header format.
- **Creative Mode**: Added full suite of builder tools (`@deleteroom`, `@copyroom`, `@setcoords`, `@roominfo`) and centralized admin security.
- **Heartbeat**: Fixed `godless_mud.py` to correctly register `reset_round_counters` and `status_effects_engine` by using the global subscriber list.
- **Cleanup**: Removed all duplicate files (`magic_engine3.py`, root files, misplaced JSONs) to enforce architectural integrity.
- **Deck Building**: Moved `memorize` and `forget` commands to the `commune` interaction. Players must now visit specific deities to modify their deck.
- **Commands**: Added `blessings` (or `known`) to list all learned blessings. Added `where` to show location info.
- **Lore**: Added help entries for major Deities.
- **Commands**: Added `scan` command for players to see mobs in the current and adjacent rooms.
- **Combat**: Implemented "Sticky Combat" state machine. Players now stay in combat until all attackers are defeated or they flee. Added `attackers` list to entities to manage aggro.
- **Combat Tuning**: Updated `flee` to instantly clear combat state. Reduced passive regen to 1 HP/tick. Increased rest regen to 10% Max HP/tick.
- **Quest System**: Implemented `quest_engine.py` and refactored `quests.py` and `systems.py` to use it. Added `update_kill_progress` logic.
- **Cleanup**: Removed duplicate `memorize`/`forget` commands from `deck.py`.
- **Environment**: Implemented global Time of Day messages and Zone-based Weather cycles in `systems.py`.
- **Social**: Added `gift` command to `social.py` to build friendship with NPCs.
- **Companions**: Added `can_be_companion` flag to Mobs and `friendship` tracking to Players.
- **Polish**: Corpse names now reflect the specific mob name (e.g., "corpse of a Goblin").
- **Fix**: Fixed `@spawn` command in `admin.py` to correctly set the `room` attribute on spawned mobs, resolving immediate combat disengagement.
- **Fix**: Updated `systems.py` combat loop to process death logic even if target HP is <= 0, preventing "invalid target" drops.
- **Combat**: Restricted `kill` command to prevent target switching mid-combat. Players must flee or finish their current fight. Skills can still target secondary enemies without switching focus.
- **Looting**: Updated `get` command to support looting from containers/corpses (`get all from corpse`, `get sword from chest`).
- **Looting**: Improved `get` and `put` to support indexed targeting (`2.corpse`) and implicit syntax (`get sword corpse`).
- **Combat**: Centralized target validation in `combat_engine.py` and standardized damage output colors via `combat_formatter.py`.

### Fixed
- **Circular Imports**: Resolved circular dependency between `logic/__init__` and `logic/information`.
- **Startup Crash**: Fixed recurring `ModuleNotFoundError` for `logic.common` by creating the file in the correct directory.
- **Startup Warning**: Created missing `data/status_effects.json`.
- **Combat**: Fixed mob health prompt not updating every round. Added colors and spacing to combat output.
- **Combat**: Refactored `auto_attack` to batch prompt updates, preventing spam when multiple entities are fighting.
- **Rest**: Fixed `rest` command never waking the player up.
- **File Structure**: Moved `crafting_engine.py` to `logic/engines/` to resolve import error and match architecture.
- **Admin Commands**: Updated `admin.py` to use the new `World` object structure.
- **Map Display**: Restored map visualization by implementing `logic/mapper.py` with BFS traversal.
- **Input Handling**: Fixed case-sensitivity issue in `input_handler.py` preventing command execution.
- **Initialization**: Fixed `Player` model to correctly initialize `gold`, `favor`, and `aliases` for new characters.
- **System Commands**: Implemented `alias` and `unalias` commands.
- **Data Structure**: Moved `world_loader.py` to `core/loader.py` and consolidated JSONs into `data/`.
- **Zone Display**: Fixed "Unknown Zone" error by properly loading Zone data.
- **Data Integrity**: Consolidated mob definitions into `data/mobs.json` and enforced `max_hp` field.
- **Cleanup**: Removed redundant room/mob data from `world_data.json` in favor of `zones/` and `mobs.json`.
- **Data Separation**: Moved item definitions from `world_data.json` to `data/items.json`.

## [0.1.0] - Initial Prototype
- Basic combat, movement, and blessing system implemented.