> [!CAUTION]
> **LEGACY ARCHITECTURE**: This document reflects Godless MUD v2.x architecture (Pre-Feb 14, 2026 Reset). **Do not use for implementation.** Reference ARCHITECTURE.md for current V3.1+ standards.

# GODLESS: WORLD VISION & GENERATION RULES (V2.1)

## 1. Global Topology & Kingdoms
The world of Godless is a vast, contiguous landmass. There is no central hub; the world is a sprawling wilderness divided into three primary Kingdom spheres of influence. Danger and reward scale dynamically as players move further into the lawless "Borderlands."

### The Three Kingdoms

| Kingdom | Theme | Primary Deities | Capital | Terrain Palette |
| :--- | :--- | :--- | :--- | :--- |
| Light | Order, Justice, White Stone | Solas, Aurelius, Sophia | Sanctum | Marble, Lakes, Peaks |
| Dark | Ambition, Mystery, Obsidian | Nox, Umbra, Malice | Noxus | Basalt, Caves, Swamps |
| Instinct | Nature, Fury, Freedom | Sylva, Krog, Feral | Ironbark | Forest, Jungle, Canyons |

---

## 2. Dynamic Security System
Security is not a static zone attribute but a Normalized Float (S) (1.0 to 0.0) calculated by the distance (d) to the nearest Kingdom Capital relative to a Kingdom's influence radius (R).

Formula: S = clamp(1.0 - (d / R), 0, 1)

* **High-Sec (1.0 - 0.5):** Non-PvP. Guards instantly kill aggressors. Death results in no item loss.
* **Low-Sec (0.4 - 0.1):** PvP enabled. Outposts/Gate guards only. Death results in inventory drop (recoverable).
* **Null-Sec (0.0):** Lawless Borderlands. No guards. Death results in full loot drop (Inventory + Equipment). Best resources and Raid Bosses are found here.

---

## 3. World Generation Standards

### 3.1 Geological Adjacency Validation
The world generator must perform a validation pass. If a terrain type is placed next to a "forbidden" neighbor, the tile must be "flipped" to a valid transition:

| Terrain Type | Forbidden Neighbor | Mitigation / Buffer |
| :--- | :--- | :--- |
| Mountain | Deep_Water | Requires a 2-tile buffer of Plains or Beach. |
| Desert | Ice/Snow | Impossible climate; requires a 10-tile Plains buffer. |
| Swamp | Desert | Only spawns adjacent to River or Coastal Water. |
| Forest | Ice/Snow | Transition must go: Forest -> Tundra -> Snow. |

### 3.2 Verticality & The Z-Axis
The world uses a coordinate-based Z-axis ranging from +5 (Peaks) to -5 (Abyss).
* **Transitions**: Moving into a Chasm or Hole triggers an automatic fall to Z-1.
* **Waterfalls**: Natural transitions from high to low Z-levels adjacent to water. Movement is one-way (Down). Moving up requires a climb action or ladder attribute.
* **Tactical PVP**: The Z-axis is a combat feature. Height advantage grants accuracy/damage bonuses in the combat_engine.

---

## 4. World Building Workflow (AI-Assisted)
Godless uses an AI-Assisted Hand-Crafting model to maintain artistic quality while automating boilerplate tasks.

1. **Generation**: Use utilities/zone_generator.py to create the initial JSON grid with palettes.
2. **Painting**: Use @paint <w> <h> to create large grids (fields, forests) instantly.
3. **Stitching**: 
    * @snapzone <from> <to> <dir>: Aligns one zone to the edge of another.
    * @autostitch: Scans coordinates and creates reciprocal exits between adjacent rooms.
4. **Persistence**: @savezone <id> compresses the room data into palettes and saves to data/zones/.

---

## 5. Engineering Guardrails
* **No Hardcoded Exits**: All world connections must be defined in the JSON rooms or created via @dig.
* **Stateless Geography**: Room logic must not rely on local variables. Use room flags and metadata.
* **Coordinate Authority**: The World object is the single source of truth for location. Never store player coordinates solely in the player model; always verify against the Room index.