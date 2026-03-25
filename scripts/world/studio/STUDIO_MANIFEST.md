# GODLESS STUDIO MANIFEST (V17.0)
## Project: Divine Interface Studio
**Status:** ACTIVE PROTOCOL (V17.0 - Pro Studio Layout)

---

## 1. VISION
The Godless Studio is a professional, three-column design suite that optimizes the "Designer-to-Engine" communication loop. It decouples high-level simulation tuning from granular brush-work by isolating them into dedicated functional zones (Palette, Canvas, Control Deck), ensuring maximum visual real-estate for the architectural vision.

---

## 2. RECENT UPDATES (V17.0)

### A. Professional 3-Column Architecture
- **Left Sidebar (The Palette)**: A dedicated vertical bar for all Biome and Infrastructure brushes. This removes search-time for tools and keeps the top bar clear for simulation data.
- **Center Pillar (The Vision)**: An expanded, centered design canvas that maximizes the viewport for intricate map work.
- **Right Sidebar (The Tuning Deck)**: A high-density control surface for engine weighting. Moving world-parameters here allows for real-time topographical tuning without obscuring the map.

### B. Numerical Precision Tuning
- **Spinbox Adjusters**: Replaced bulky sliders with precision **Numerical Spinboxes**. Designers can now input absolute values or increment weights in 0.1 steps for surgical topographic control.
- **Advanced Telemetry Deck**: Hover data has been expanded into a dedicated panel in the Right Sidebar, displaying absolute coordinates, biome identity, and precise Elevation/Moisture potential.

### C. Menu Consolidation
- **File & View Menus**: Relocated global session management (Save/Load/New) and Heatmap toggles to top-level desktop menus. This resolves "Toolbar Overcrowding" and prepares the Studio for future tool expansion.

---

## 3. ENGINE DIRECTORY MAP (Rules & Logic)
To edit the generation rules individually, refer to these sharded modules:

1. **Topography & Foundations**: [architect_climate.py](file:///C:/Users/Chris/antigravity/Godless/scripts/world/architect_climate.py)
   - *Logic*: Continental masks, Latitude bias, Biome Isolation, Land Density scaling.
2. **Tectonics & Erosion**: [architect_terrain.py](file:///C:/Users/Chris/antigravity/Godless/scripts/world/architect_terrain.py)
   - *Logic*: Ridge Walker (Mountain/Hill gradients), Peak intensity dampening.
3. **Hydrology & Gulfs**: [architect_natural.py](file:///C:/Users/Chris/antigravity/Godless/scripts/world/architect_natural.py)
   - *Logic*: **Great Gulfs** (Area-based erosion), Sea Cliff protection.
4. **Civilization & Ports**: [architect_infrastructure.py](file:///C:/Users/Chris/antigravity/Godless/scripts/world/architect_infrastructure.py)
   - *Logic*: Hub scouting, Urban growth (15x15 cap), **Coastal Harbor Pass (Docks)**.
5. **Metadata & Export**: [architect_export.py](file:///C:/Users/Chris/antigravity/Godless/scripts/world/architect_export.py)
   - *Logic*: Zonal sharding, Intent injection (CR/Spawn), Naming.

---

## 4. UPCOMING MILESTONES (V16.1)
- **Sovereignty Pins 2.0**: Interactive pins that define kingdom name and influence strength.
- **Climatological History**: Log files that track the "Why" behind a tile's biome (e.g., "Shadowed by Peak at 90,66").

*Verified and Sealed for Future Development (V16.0 Operational).*
