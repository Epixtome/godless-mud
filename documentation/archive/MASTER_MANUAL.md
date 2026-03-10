> [!CAUTION]
> **LEGACY ARCHITECTURE**: This document reflects Godless MUD v2.x architecture (Pre-Feb 14, 2026 Reset). **Do not use for implementation.** Reference ARCHITECTURE.md for current V4.5+ standards.

# GODLESS MUD: MASTER MANUAL

> **Version:** 0.2.0 (Gold Standard)
> **Status:** Active Development
> **Last Updated:** 2026-02-10

---

## TABLE OF CONTENTS
1.  [SECTION I: GAME DESIGN DOCUMENT (GDD)](#section-i-game-design-document-gdd)
2.  [SECTION II: WORLD VISION & RULES](#section-ii-world-vision--rules)
3.  [SECTION III: CLASS REFERENCE](#section-iii-class-reference)
4.  [SECTION IV: COMMAND REFERENCE](#section-iv-command-reference)
5.  [SECTION V: CHANGELOG](#section-v-changelog)

> **NOTE:** For Engineering Standards, File Structure, and System Architecture, please refer to **`ARCHITECTURE.md`**.

---

## SECTION I: GAME DESIGN DOCUMENT (GDD)
*(Formerly `GDD.md`)*

### 1. Overview
**Godless** is a text-based Multi-User Dungeon (MUD) built in Python. It features a level-less progression system where character power is derived from **Gear** and **Blessings** (abilities). Players align with Deities across three Kingdoms to build a custom "deck" of abilities, which in turn unlocks specialized Classes based on their choices.

### 2. Core Systems
*   **Engine**: Asynchronous Telnet server using Python's `asyncio`.
*   **Heartbeat**: A global game tick (currently 2 seconds) that drives time-dependent systems like combat rounds, regeneration, and weather.
*   **Persistence**: Player data (stats, inventory, location, deck) is saved to and loaded from JSON files.
*   **Hot-Reloading**: Admin capability to reload game logic and data without stopping the server.
*   **Pagination**: Built-in buffer system to handle long output (like help menus) with "Press Enter" prompts.
*   **Input Handling**: Centralized system managing command dispatch, admin overrides, and user-defined **Aliases**.

### 3. Character Progression
#### Stats
The six primary attributes driving all scaling:
*   **STR** (Strength)
*   **DEX** (Dexterity)
*   **CON** (Constitution)
*   **WIS** (Wisdom)
*   **INT** (Intelligence)
*   **LUK** (Luck)

#### Resources
*   **HP**: Health Points. Regenerates passively based on CON.
*   **Favor**: Divine currency earned by killing monsters. Used to purchase Blessings from Deities.
*   **Concentration**: Mental focus required for Spells and complex Skills.
    *   **Regen**: Recovers when resting or out of combat.
    *   **Loss**: Decreases when taking damage in combat (1-5 per hit).
    *   **Upkeep**: Continuous drain for sustaining powerful states (e.g., Rage, Bard Songs).
    *   **Overcast**: You can cast spells without enough Concentration, but you take HP damage and suffer debuffs ("Mental Strain").
    *   **Cost**: Spells cost a percentage of Max Concentration.

#### Identity Timeline
Your class is dynamic, determined by the **Tags** on your **Equipped Blessings**.
*   **Unlocking**: You permanently unlock a class when your **Known Blessings** (collection) meet specific tag requirements.
*   **Activating**: You become that class when your **Equipped Blessings** (deck) meet the requirements.

#### Progression Stages
Your class is not a permanent choice but a reflection of your current loadout.
1.  **Adept (T1)**: Aligned with a Stat or Kingdom via **Primary Tags** (e.g., `[Int]`, `[Light]`).
2.  **Class (T2)**: Defined by an Archetype via **Secondary Tags** (e.g., `[Fire]`, `[Stealth]`).
3.  **Master (T3)**: Unlocks Prestige Classes via **Hybrid/Advanced Tags** (e.g., `[Shadow]`).
4.  **Legend (T4)**: Achieved by equipping the Class Ultimate.

#### Synergies
Passive stat bonuses unlocked by having specific tag combinations in your active deck.
*   *Example*: **Holy Fortitude** (Requires 2 `[Light]` tags) -> Grants **+3 CON**.
*   *Example*: **Shadow Reflexes** (Requires 2 `[Dark]` tags) -> Grants **+3 DEX**.

### 4. The Blessings Engine
Magic and abilities are handled through a deck-building system.

*   **Deities**: Entities belonging to Kingdoms (Light, Dark, Instinct) that sell Blessings for Favor via the `commune` command. **Deck Building** (Memorize/Forget) can only be performed while communing with the specific Deity that granted the blessing.
*   **Blessings**: Active abilities with specific properties:
    *   **Tiers**:
        *   **T1 (Universal Tools)**: Core combat fundamentals (Kick, Focus). No strong identity signal. Mostly martial or base-stat flavored. These allow anyone to function; they do not define you. Limit: **4**.
        *   **T2 (The Spark)**: First signal of direction. Mechanically distinct but could belong to multiple archetypes (e.g., Stomp fits Tank/Barbarian). Introduces class-flavored mechanics and begins tag weighting. Limit: **3**.
        *   **T3 (Identity Maker)**: Mechanically unmistakable. Hard directional shift with high tag weight. Locks in archetype momentum (e.g., Whirlwind -> Barbarian). Taking these makes your identity obvious. Limit: **2**.
        *   **T4 (Playstyle Specialization)**: Capstone refinement. Not just class-defining, but *playstyle*-defining (e.g., turning a Barbarian into a Berserker vs Juggernaut). Requires specific Class Identity. Limit: **1**.
    *   **Progression Arc**: Competency (T1) -> Direction (T2) -> Declaration (T3) -> Specialization (T4).
    *   **Scaling**: Power is calculated dynamically via `MathBridge` using player stats.
    *   **Auditor**: A validation system that checks Stats, Identity Tags, Equipment (`shield`), and Player State (`is_mounted`, `stance`) before a blessing can be cast.
    *   **Charges**: Limited uses per blessing, restored via rest (planned).

#### 4.1 The Tagging & Recipe Model
To support hundreds of blessings and classes, the system uses a **Tagging Layer** between the Blessing and the Auditor. The Auditor does not look for specific blessing names; it scans the **Tags** attached to the equipped blessings.

**Structure:**
| Layer | Component | Example |
| :--- | :--- | :--- |
| **Data** | The Blessing | "Volt-Shot" (The actual skill) |
| **Metadata** | The Tags | Kingdom: Light, Type: Ranged, Stat: DEX |
| **Logic** | The Recipe | If Ranged >= 3 AND Light >= 3 -> Reveal "Gunner" |
| **Identity** | The Title | Player is now a Gunner. |

#### 4.2 The Resonance Funnel Workflow
Adding new content follows a strict workflow:
1.  **The Blessing**: Create the ability (e.g., "Earthquake").
2.  **The Tags**: Assign tags (e.g., `[Instinct]`, `[Nature-Magic]`).
3.  **The Class Recipe**: Define the Class (e.g., "Geomancer") as needing specific tag counts (e.g., 4 `[Nature-Magic]` + 2 `[Wisdom]`).
4.  **Result**: The Auditor automatically recognizes any player meeting criteria as a Geomancer.

### 5. Combat
*   **Real-Time**: Combat occurs automatically on the heartbeat tick.
*   **Sticky Combat**: Once engaged, players enter a `combat` state. They automatically target any entity in their `attackers` list if their primary target dies. Combat only ends when all aggressors are defeated or the player flees.
*   **Target Locking**: Players cannot switch their primary auto-attack target mid-combat using `kill`. They must use specific abilities or flee to change focus. Targeted skills (spells/kicks) can still hit secondary targets.
*   **Auto-Attacks**:
    *   **Weapons**: Roll damage dice (e.g., "2d3") + Stat Scaling (e.g., 1.5x STR).
    *   **Unarmed**: Scales slightly with STR.
*   **Action Pacing**: Players can perform a limited number of actions per 2-second round (Tick). This is enforced by `magic_engine.check_pacing`.
    *   **Default**: Most abilities are limited only by their individual `cooldown` and resource cost.
    *   **Spam Control**: Specific abilities (like `kick`) can be limited via the `max_per_round` rule in their JSON definition.
*   **Defense**: Armor provides flat damage mitigation.
*   **Regeneration**: 1 HP/tick (Passive), 10% Max HP/tick (Resting).
*   **Death**:
    *   **Monsters**: Drop a **Corpse** container holding their loot.
    *   **Players**: Currently resurrect at full HP upon death.
*   **Commands**: `kill`, `flee`.

### 6. Companions & Social
*   **Friendship**: Players can build trust with specific NPCs by giving them gifts (`gift <item> <npc>`).
*   **Recruitment**: Once friendship reaches a threshold (50/100), the NPC can be recruited to follow the player.
*   **Behavior**:
    *   **Follow**: Companions automatically move when their leader moves.
    *   **Combat**: Companions automatically assist their leader in combat.

### 7. World Architecture
The world is structured hierarchically to support factional territory, PvP security levels, and 3D mapping.

#### 7.1 Hierarchy
1.  **Kingdom**: The highest level of territory (Light, Dark, Instinct). Determines the starting location for new characters and influences biome.
2.  **Zone**: A large geographical region (e.g., "The Whispering Woods").
    *   **Security Status**:
        *   **Safe (High-Sec)**: Near capital. No PvP. Guarded by elite NPCs.
        *   **Neutral (Low-Sec)**: Transition zones. PvP allowed. Limited guards.
        *   **Danger (Null-Sec)**: Deep wilds. Free-for-all PvP. High-risk resources.
    *   **Borders**: Connections between zones are "Choke Points" guarded by NPCs based on the destination's security level.
3.  **Area**: A logical grouping of rooms within a Zone (e.g., "The Rusty Tavern" inside "Town Square"). Used for environmental tags (Indoors, Underwater).
4.  **Room**: The atomic unit of space.
    *   **Coordinates**: (X, Y, Z) for mapping.
    *   **Exits**: Cardinal directions (N, S, E, W) + Up/Down only. Diagonal exits are not supported to ensure clean map rendering. Can have Doors/Locks.

#### 7.2 Building Tools
*   **@dig <dir>**: Creates a new room in the specified direction. If a room already exists at those coordinates, it links to it instead of overwriting.
*   **@autodig**: Toggles a mode where walking into a wall automatically digs a new room.
*   **@link / @unlink**: Manually connect or disconnect rooms.
*   **@desc / @name**: Edit room details in real-time.
*   **@addmob / @additem**: Add static spawns to the room definition.
*   **@deleteroom**: Removes a room and cleans up all incoming links.
*   **@setzone / @setterrain**: Updates room metadata.
*   **@copyroom**: Copies Name/Desc/Zone from current room to a neighbor.
*   **@setcoords**: Manually fixes grid alignment.
*   **@stitch**: Connects two zones by aligning their borders automatically.
*   **@snapzone**: Moves an entire zone to align with a specific room.
*   **@shiftzone**: Manually moves an entire zone by X/Y/Z offsets.
*   **@zonemap**: Displays a high-level survey of all zones and detects gaps.
*   **@savezone <id>**: Persists changes to `data/zones/{id}.json`. This will be crucial for saving our hand-crafted regions.

#### 7.3 Persistence & State
*   **Static Data**: Loaded from `data/zones/*.json`. Defines the "Factory Default" state of the world.
*   **Dynamic State**: Saved to `data/world_state.json`. Tracks dropped items, dead bosses, and current room contents.
*   **Conflict Resolution**: Dynamic State overrides Static Data on load. If you add a new static mob to a zone file, it will not appear until the dynamic state is wiped or the mob is manually spawned, as the state file remembers the room being "empty".
*   **Procedural Generation**: New zones are created using `utilities/zone_generator.py` and populated via scripts, ensuring consistent formatting.

#### 7.4 Navigation & Environment (Verticality & Plane Changes)
*   **Map**: A 5x5 ASCII grid generated dynamically based on the player's location.
*   **Fog of War**: A larger `map` command shows all previously visited rooms in the current zone. Blessings like `Eagle Eye` and `Farsight` can enhance this map.
*   **Navigation**: Standard cardinal directions (N, S, E, W) plus Up/Down.
*   **Visuals**: ANSI color coding for entities and a dynamic status prompt.
*   **Weather**: Zone-specific weather cycles that update periodically (e.g., Rain in Instinct, Fog in Dark).
*   **Time**: Global day/night cycle with descriptive messaging.

### 8. Itemization
*   **Equipment**:
    *   **Armor**: Provides Defense and Stat Bonuses.
    *   **Weapons**: Define Damage Dice and Stat Scaling.
*   **Looting**: Items must be looted from Corpses after killing monsters.
*   **Management**: Commands to `get`, `drop`, `equip`, `remove`, and view `inventory`/`equipment`.
*   **Containers**: Support for putting items in and taking items out of containers (chests, corpses) using `put` and `get`. Supports indexed targeting (`2.corpse`) and bulk operations (`get all`).

### 9. Current Content (Data)
*   **Kingdoms**: Instinct, Dark.
*   **Deities**: Full roster of 18 deities implemented across all three Kingdoms.
*   **Classes**: Defined in `data/classes.json` and documented in `class_reference.md`.
*   **Blessings**: Full suite of T1 Foundations, T2 Sparks, T3 Masteries, and T4 Ultimates.
*   **Zones**: The Crossroads, Path of Dawn, Shadowed Trail, Overgrown Track.
*   **Mobs**: Goblin, Light Wisp, Shadow Stalker, Wild Boar.
*   **Bosses**: Avatars of Sylva, Nox, and Krog.

### 10. Roadmap

#### Phase 1: The Prime Directive (Current)
- [x] **Migration**: Move all commands to `logic/commands/`.
- [x] **Strict Math**: Ensure all scaling uses `MathBridge`.
- [x] **Economy**: Implement `shop.py` and currency exchange.
- [x] **Persistence**: Ensure all player state (cooldowns, buffs) saves correctly.

#### Phase 2: The Living World
- [x] **Spawning**: Dynamic mob respawning based on zone population (`mob_manager`).
- [x] **Crafting**: System to combine monster drops into items (`crafting_engine`, `logic/commands/item_commands.py`).
- [x] **Quests**: NPC dialogue and objective tracking (`quest_engine`).
- [x] **Refactoring**: Move hardcoded recipes from `crafting_engine.py` to `data/recipes.json`.

#### Phase 3: Deep Progression
- [x] **Blessing Rework**: Revamp deck building, memorization mechanics, and usage (`deck.py`).
- [x] **Attunement**: Commune feature for Deities (`commune.py`).
- [x] **Attributes**: Separate Score/Attributes logic for clearer progression.

#### Phase 4: Class Expansion (Priority)
- [x] **Monk**: Chi resource, Stance switching (Tiger/Crane).
- [x] **Bard**: Song system, Concentration upkeep for buffs.
- [x] **Necromancer**: Corpse consumption, Minion summoning (Basic).
- [x] **Samurai**: Iaido mechanics, First-strike bonuses.

#### System Status Report
| System | Component Location | State | Notes |
| :--- | :--- | :--- | :--- |
| **Core Loop** | `godless_mud.py`, `logic/systems.py` | **Stable** | Heartbeat triggers `combat_processor` and regen. |
| **Gatekeeper** | `logic/input_handler.py` | **Stable** | Centralized validation is working. Admin overrides are secure. |
| **Combat** | `commands/combat_commands.py`, `engines/combat_engine.py` | **Stable** | Includes `kill`, `flee`, `consider`, `sacrifice`. Math is isolated. |
| **Magic/Skills** | `commands/spell_commands.py`, `commands/skill_commands.py`, `logic/actions/` | **Stable** | `Auditor` gates usage. Skills delegated to `actions/` package. |
| **Crafting** | `commands/item_commands.py`, `engines/crafting_engine.py` | **Stable** | Loads recipes from `data/recipes.json`. |
| **Quests** | `commands/quests_commands.py`, `engines/quest_engine.py` | **Stable** | Supports Kill/Item objectives and rewards. |
| **Admin/Builder** | `commands/admin/` | **Rich** | Full suite of tools (`@dig`, `@spawn`, `@restart`). |
| **Mapping** | `logic/mapper.py` | **Stable** | BFS-based rendering with Z-plane support. |
| **Data/Models** | `models.py`, `core/world.py` | **Stable** | Clear separation of State (`World`) and Data Structure (`Models`). |
| **Generation** | `utilities/zone_generator.py` | **Active** | Procedural generation for new zones. |

---

## SECTION II: WORLD VISION & RULES
*(Formerly `world/00_vision_and_rules.md`)*

### 1. Global Topology
The world is a vast, contiguous landmass. No central Hub. Three distinct Kingdom regions.

### 2. Dynamic Security System
Security is calculated by proximity to Kingdom Capitals.
*   **High-Sec (1.0 - 0.5)**: No PvP. Guards kill aggressors.
*   **Low-Sec (0.4 - 0.1)**: PvP Allowed. Guards at outposts.
*   **Null-Sec (0.0)**: Lawless. Free-for-all. Best resources.

### 3. World Generation Rules
*   **Adjacency**: Mountains need buffers. Deserts cannot touch Snow.
*   **Barriers**: Mountains and Rivers act as natural chokepoints.
*   **Verticality**: Z-axis ranges from -5 (Deep Caves) to +5 (Peaks).

### 4. Key Tooling
*   `@paint <w> <h>`: Create grids.
*   `@snapzone <from> <to> <dir>`: Align zones.
*   `@autostitch`: Link adjacent rooms.
*   `@savezone <id>`: Persist changes.

### 5. Lore & Kingdoms
*   **Light (Sanctum)**: Order, Civilization, Hierarchy.
    *   *Deities*: Solara (Sun/Fire), Aurelius (Protection/Justice).
*   **Dark (Noxus)**: Ambition, Mystery, Individualism.
    *   *Deities*: Nox (Stealth/Assassination), Umbra (Void/Magic).
*   **Instinct (Ironbark)**: Nature, Survival, Freedom.
    *   *Deities*: Sylva (Nature/Wisdom), Krog (Strength/Fury).

---

## SECTION III: CLASS REFERENCE
*(Formerly `class_reference.md`)*

### Philosophy
Classes are **Identities** recognized when a player's Blessing Deck resonates with specific Tags.

### 1. Class Definitions

#### **Warrior** (Base)
*   **Role**: Frontline Fighter
*   **Requirements**: `[martial]: 3`, `[weapon]: 2`
*   **Key Blessings**: Kick, Bash, Parry, Sunder, Pommel Strike.

#### **Mage** (Base)
*   **Role**: Arcane Caster
*   **Requirements**: `[spell]: 3`, `[int]: 3`
*   **Key Blessings**: Fireball, Magic Missile, Mana Shield, Arcane Blink.

#### **Rogue** (Base)
*   **Role**: Skirmisher
*   **Requirements**: `[dex]: 3`, `[stealth]: 1`
*   **Key Blessings**: Backstab, Hide, Gouge, Quick Step.

#### **Cleric** (Base)
*   **Role**: Healer
*   **Requirements**: `[light]: 3`, `[healing]: 2`
*   **Key Blessings**: Cure Light, Bless, Purify, Sanctuary.

#### **Ranger** (Base)
*   **Role**: Hunter / Tracker
*   **Requirements**: `[instinct]: 3`, `[marksmanship]: 2`
*   **Key Blessings**: Track, Snipe, Volley, Camouflage.

---

### 2. Advanced Classes (Kingdom Specific)

#### **Paladin** (Light)
*   **Role**: Holy Tank
*   **Requirements**: `[light]: 3`, `[protection]: 2`
*   **Key Blessings**: Divine Smite, Holy Shield, Lay on Hands (T2).

#### **Knight** (Light)
*   **Role**: Mounted Combatant
*   **Requirements**: `[light]: 2`, `[mount]: 1`, `[martial]: 2`
*   **Key Blessings**: Mount, Charge, Trample, Joust.

#### **Bard** (Light/Instinct)
*   **Role**: Buffer / Support
*   **Requirements**: `[song]: 2`, `[support]: 2`
*   **Key Blessings**: Song of Courage, Lullaby, Anthem of War.

#### **Assassin** (Dark)
*   **Role**: Burst DPS
*   **Requirements**: `[dark]: 3`, `[lethal]: 2`
*   **Key Blessings**: Assassinate, Poison Weapon, Garrote.

#### **Necromancer** (Dark)
*   **Role**: Summoner
*   **Requirements**: `[dark]: 3`, `[summon]: 2`
*   **Key Blessings**: Raise Dead, Bone Spear, Life Tap.

#### **Warlock** (Dark)
*   **Role**: Debuffer / Drain
*   **Requirements**: `[dark]: 3`, `[curse]: 2`
*   **Key Blessings**: Curse, Hex, Drain Life, Fear.

#### **Witch** (Dark)
*   **Role**: Thorns / Control
*   **Requirements**: `[dark]: 3`, `[malediction]: 1`
*   **Key Blessings**: Malediction, Hex, Curse.

#### **Barbarian** (Instinct)
*   **Role**: Momentum / Control
*   **Requirements**: `[instinct]: 3`, `[momentum]: 2`
*   **Key Blessings**: Whirlwind, Drag, Second Attack, Stomp.

#### **Druid** (Instinct)
*   **Role**: Nature Caster
*   **Requirements**: `[instinct]: 3`, `[nature]: 2`
*   **Key Blessings**: Entangle, Regrowth, Lightning Call, Shapeshift.

#### **Monk** (Instinct)
*   **Role**: Unarmed Fighter
*   **Requirements**: `[martial]: 3`, `[unarmed]: 2`
*   **Key Blessings**: Tiger Palm, Blackout Kick, Tiger Stance, Meditate.

---

### 3. Prestige Classes (Specialized)

#### **Samurai**
*   **Concept**: Precision striker using "Iaido".
*   **Requirements**: `[blade]: 3`, `[focus]: 2`
*   **Key Blessings**: Iaido (Sheathe), Draw Slash, Third Eye, Meditate.

#### **Ninja**
*   **Concept**: Mobility and stealth skirmisher.
*   **Requirements**: `[ninjutsu]: 2`, `[mobility]: 2`
*   **Key Blessings**: Shuriken Toss, Shadow Step, Smoke Bomb, Vanish.

#### **Dragoon**
*   **Concept**: Aerial assaults.
*   **Requirements**: `[mobility]: 3`, `[polearm]: 1`
*   **Key Blessings**: Jump, Dragon Dive, High Jump.

#### **Alchemist**
*   **Concept**: Item-based caster.
*   **Requirements**: `[alchemy]: 3`, `[utility]: 1`
*   **Key Blessings**: Flask Toss, Transmute, Brew Potion.

#### **Engineer**
*   **Concept**: Construct builder.
*   **Requirements**: `[gadget]: 2`, `[int]: 3`
*   **Key Blessings**: Deploy Turret, Repair, Blast Mine.

#### **Gambler**
*   **Concept**: RNG manipulation.
*   **Requirements**: `[luck]: 3`, `[chance]: 2`
*   **Key Blessings**: Coin Toss, Roll Dice, Jackpot.

#### **Red Mage**
*   **Concept**: Hybrid Caster.
*   **Requirements**: `[light]: 2`, `[dark]: 2`
*   **Key Blessings**: Dualcast, Verfire, Verstone.

#### **Blue Mage**
*   **Concept**: Monster Skill Learner.
*   **Requirements**: `[mimic]: 2`, `[int]: 3`
*   **Key Blessings**: Observe, Absorb, Monster Skill (Learned).

---

## SECTION IV: COMMAND REFERENCE

### 1. Player Commands
*   **Combat**: `kill <target>`, `cast <spell>`, `use <skill>`
*   **Info**: `score`, `inv`, `eq`, `deck`, `map`, `scan`, `consider`
*   **Action**: `commune` (at shrines)

### 2. Admin / Builder Commands
*   **Building**: `@dig`, `@paint`, `@brush`, `@paste`, `@gen_grid`
*   **Editing**: `@set room <attr> <val>`, `@massedit`, `@replace`
*   **Mapping**: `@worldmap`, `@zonemap`, `@tp`
*   **Entities**: `@spawn`, `@purge`, `@inspect`
*   **System**: `@restart`, `@reloadbans`, `@whoson`

---

## SECTION V: CHANGELOG
*(Formerly `CHANGELOG.md`)*

### [Unreleased]
#### Added
- **Documentation**: Consolidated all docs into `MASTER_MANUAL.md`.
- **Event Engine**: Implemented `logic/engines/event_engine.py` (Pub/Sub).
- **Effect Registry**: Refactored `status_effects_engine.py` to use registry pattern.
- **Refactor**: Updated `combat_engine` and `magic_engine` to use Event Bus and Registries.
- **Lore System**: Added `lore` command.
- **Zone Generator**: Procedural creation tools.

#### Changed
- **Combat**: Implemented "Sticky Combat" and "Ghost Target" fixes.
- **Map System**: Rewrote `mapper.py` to use BFS.
- **Input Handling**: Hardened `input_handler.py`.

#### Fixed
- **Circular Imports**: Resolved via `logic/common.py` and lazy imports.
- **Startup Crashes**: Fixed `ModuleNotFoundError` issues.
- **Combat**: Fixed prompt updates and mob health display.
```
