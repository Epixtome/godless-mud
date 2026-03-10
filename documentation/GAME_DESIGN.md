# GODLESS: GAME DESIGN DOCUMENT (V4.5)

## 1. PROJECT OVERVIEW
**Godless** is an asynchronous, text-based MUD built in Python (`asyncio`). It features a level-less progression system where character identity is derived from a dynamic "deck" of **Blessings** and gear. Players navigate a contiguous 3D coordinate world, aligning with Deities across three Kingdoms (Light, Dark, Instinct).

---

## 2. CORE ENGINE SYSTEMS
* **Asynchronous Heartbeat**: A global 2.0s game tick driving all time-dependent systems (Combat, Regen, Weather).
* **Hot-Reloading**: Full `importlib` support for refreshing logic and data without server downtime.
* **Pagination**: A built-in buffer system for long output (Help/Lore) with "Press Enter" prompts.
* **Input Handling**: Centralized command dispatch, admin overrides, and user-defined **Aliases**.

---

## 3. CHARACTER PROGRESSION (POTENCY OVER PROCESS)
Character growth in Godless is horizontal and gear-driven.
* **Voltage (Tags)**: Characters do not have base stats (STR/INT). Instead, they accumulate **Voltage** from their equipped Gear, Blessings, and active Status Effects.
* **Potency Scaling**: All skills and actions scale their damage or effectiveness directly from specific Tag totals (e.g., a sword strike scales with `martial` voltage).
* **Breakthroughs**: Reaching high thresholds in a tag (e.g., 10 `arcane`) unlocks **Passive Breakthroughs**—stat-altering milestones that represent extreme proficiency.
* **Favor**: Divine currency earned via combat; used to purchase Blessings from Shines or Deities.




---

## 4. THE BLESSINGS ENGINE (THE DECK)
Magic and skills utilize a **Tagging Layer** between data and logic.
* **Data**: The Blessing (e.g., "Volt-Shot").
* **Metadata**: The Tags (e.g., `[lightning]`, `[strike]`).
* **The Math Bridge**: Core engines use tags to calculate final power. Tags represent the *potency* (numbers), while the Python module handles the *process* (logic).
* **Synergies**: Minor passive bonuses triggered by tag combinations (e.g., +5% Fire Damage if `fire >= 5`).
* **Kits**: Skills are granted by equipping a **Class Kit**. Classes are NOT unlocked by tags; they are explicit identities.

---

## 5. COMBAT MECHANICS
* **Real-Time**: Auto-attacks and rounds resolve on the Heartbeat.
* **Sticky Combat**: Players enter a `combat` state and automatically cycle through their `attackers` list. Combat only ends on death or successful `flee`.
* **Target Locking**: Auto-attacks are fixed on the primary target. Switching targets mid-combat requires death of the target, flight, or specialized skills.
* **Action Pacing**: Enforced by `magic_engine.check_pacing`. Specific skills use `max_per_round` limits in JSON.
* **Defense**: Armor provides flat damage mitigation.

---

## 6. WORLD ARCHITECTURE & NAVIGATION

### 6.1 Hierarchy
1. **Kingdom**: Geopolitical alignment (Light, Dark, Instinct).
2. **Zone**: Geographical regions with dynamic **Security Levels** (High-Sec, Low-Sec, Null-Sec).
3. **Room**: Atomic unit of space using (X, Y, Z) coordinates. Supports cardinal exits + Up/Down.

### 6.2 Verticality & Physics (Z-Axis)
* **Range**: +5 (Peaks) to -5 (Deep Caves).
* **Physics**: Moving into a `Chasm` triggers an auto-fall to Z-1. `Waterfalls` allow one-way downward movement.

### 6.3 Building Toolset
* **Stitching**: `@snapzone` (Aligns borders), `@autostitch` (Reciprocal linking).
* **Painting**: `@paint <w> <h>` for instant grids.
* **Creation**: `@dig <dir>` for manual expansion and coordinate linking.

---

## 7. PERSISTENCE & DATA
* **Static Data**: Loaded from `data/zones/*.json` (Factory Defaults).
* **Dynamic State**: `world_state.json` tracks dropped items, dead bosses, and current room modifications. **State overrides Static Data on load.**
* **Looting**: Full support for container-based looting (`get all from corpse`) with indexed targeting (`2.corpse`).

---

## 8. COMPANIONS & SOCIAL
* **Friendship**: Trust built via the `gift` command. Recruitment available at 50/100 threshold.
* **Behavior**: Recruited NPCs utilize `Follow` and `Assist` behaviors to support the player in real-time.

# GDD UPDATE: THE RESILIENT IDENTITY PROTOCOL

## 1. THE KIT SYSTEM
Character identity is determined by the active **Kit** (defined in `data/kits.json`).
1. **Explicit Identity**: A player is a "Monk" because they have equipped the Monk kit, not because they have specific tags.
2. **Initial Gear**: Kits provide a starting set of gear and baseline blessings.
3. **Module Registration**: Equipping a kit registers the player with that class's specialized logic module (found in `logic/modules/`).

## 2. PASSIVE SYNERGIES
The system monitors tag combinations for minor stat boosts. These represent the character's affinity with specific domains but do not alter their core Class identity.
