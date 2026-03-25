# GODLESS ARCHITECT: THE CONSTRUCTOR'S GUIDE

> **Status:** V7.0 (Flattened Surface Standard)  
> **Target:** Administrative Builders & World Design

---

## 1. ARCHITECT MODE
Godless uses a low-friction **Architect Mode** to allow builders to work without typing `@` prefixes for every command.

- **Toggle On**: `@building on`
- **Toggle Off**: `exit` or `@building off`

**When ACTIVE:**
*   Commands like `dig`, `paint`, `set`, and `kit` work directly.
*   The **Builder HUD** is visible, showing your active Kit, Stencil, and Coordinates.

---

## 2. THE KIT DRAWER (`@kit` / `@drawer`)
The Kit Drawer is your architectural library. It contains **Stencils** (blueprints) for terrain, rooms, and infrastructure.

1.  **Open Drawer**: Type `kit` or `drawer`.
2.  **Select Stencil**: Type the **Number** of the stencil (e.g., `1`, `2`, `3`).
3.  **Load New Kit**: Type `kit load <name>` (e.g., `kit load mountain`, `kit load coastal`).

---

## 3. CORE CONSTRUCTION COMMANDS

### A. The 'Dig' Protocol
*   **Usage**: `dig <direction>`
*   **Effect**: Creates a new room in the specified direction using the **Active Stencil**.
*   **Auto-Link**: If `auto_link` is on, it automatically stitches the rooms together in the grid.

### B. The 'Paint' Protocol
*   **Usage**: `paint <width> <height> [direction]`
*   **Effect**: Stamps a grid of rooms in the world. Ideal for clearing large plains or dense forests.

### C. Manual Overrides
*   **@set <attr> <val>**: Directly change a room's `name`, `desc`, `terrain`, `elevation`, or `z`.
*   **@link <dir> <id>**: Manually connect two rooms. Useful for non-cardinal or long-distance portals.

---

## 4. THE TWO-TIER COORDINATE SYSTEM (V7.0)
Godless uses a "Flattened" world with tactical elevation.

*   **Coordinate (Z)**: This is your physical plane. 
    *   `Z: 0` is the **Surface**. 
    *   `Z: -1` to `-100` are **Underworld** layers.
*   **Elevation**: This is your tactical height. 
    *   Stored in `room.elevation`.
    *   Affects combat math and map radius.

**Rule of Thumb**: Moving a mountain? Use `@set elevation`. Moving to a cellar? Use `@set z -1`.

---

## 5. IN-GAME HELP (`@builderhelp`)
For detailed command syntax and flags, use the in-game constructor's guide:
- **`@builderhelp`** or **`@bh`**: Lists every administrative construction tool.
- **`help <command>`**: Provides usage examples for specific building tools.

---

## 6. AVAILABLE KITS (data/blueprints/kits/)
*   `default`: Basic rooms and transitions.
*   `mountain`: Incline paths, summits, and peaks.
*   `coastal`: Sand, water banks, and shallows.
*   `cavern`: Damp stone, narrow tunnels, and large chambers.
*   `forest`: Paths, dense thickets, and clearings.
