# GODLESS COMMAND REFERENCE

## 1. Core Player Commands

### Movement & Exploration
*   **look / l**: View the current room and local tactical map.
*   **map**: Displays a larger tactical map based on your vision radius.
*   **scan**: Scans the area for enemies. Vision radius influences the search depth.
*   **go <direction>**: Move in a cardinal direction (n, s, e, w, u, d).

### Information & Character
*   **score**: View your stats, kingdom affiliation, and favor.
*   **inventory / inv**: List items in your pack.
*   **equipment / eq**: View your wearing armor and weapons.
*   **deck**: View your equipped blessings and their charges.
*   **help <topic>**: Search the comprehensive help system (blessings, status, and commands merged).

### Combat & Skills
*   **kill <target>**: Initiate combat.
*   **commune**: At a shrine, interact with your deity to swap blessings or gain favor.
*   **sacrifice <corpse>**: Offer a fallen enemy to your deity for favor.

## 2. Vision & Tactical Systems
The Vision Engine dynamically calculates your tactical view based on:
1.  **Elevation**: Being higher (Z) allows you to see over lower obstacles.
2.  **Opacity**: Forests and Mountains block Line of Sight (LoS).
3.  **Skills**: 
    *   `Eagle Eye`: Increases map radius and scan depth by +2.
    *   `Farsight`: Increases map radius by +1.
4.  **Stealth**: `Haven` status effects can hide rooms from external view.

## 3. Administrative & Architect Commands
Building commands are prefixed with `@` in normal mode, or can be used **prefix-less** in **Architect Mode** (`@building on`).

### Architect Core
*   **kit / drawer**: Opens the visual Kit Drawer to select architectural **Stencils**.
*   **kit load <name>**: Swaps the active library (e.g., `coastal`, `mountain`).
*   **dig <dir>**: Creates a new room using the active Stencil's attributes.
*   **paint <w> <h> [dir]**: Paints a grid of rooms with the active Stencil.
*   **auto <dig|stitch> <on|off>**: Automated construction while walking or digging.

### World Maintenance
*   **@link <dir> <id>**: Manually links rooms across zones or distance.
*   **@audit**: Checks the current zone for integrity issues (disconnected rooms).
*   **@fixids**: Re-syncs room IDs with their current world coordinates.
*   **@set room <attr> <val>**: Fine-tuned modification of room properties.
*   **@tp <x> <y> <z>**: Teleport to absolute world coordinates.

### Server & System
*   **@worldmap**: Low-fidelity render of the entire Aethelgard continent.
*   **@zonemap**: Renders the full boundaries of the current zone.
*   **@restart**: Safely shuts down and reboots the MUD server.

---
*For a full catalog of developer scripts, see the `scripts/` directory.*