# GODLESS SYSTEM REGISTRY: Versions, References & Terms

This artifact is the definitive compilation of all versioned overhauls, system acronyms, and architectural protocols within the Godless MUD project.

---

## 📅 VERSION HISTORY & ERAS

| Version | Name | Key Milestones | Status |
| :--- | :--- | :--- | :--- |
| **V7.2** | **Topographical Refactor** | Perception Matrix, Ridge Rule, Elevation Shading. | **ACTIVE** |
| **V6.1** | **Unified Construction** | Architect's Drawer, Kit & Stencil System, `@building` mode. | Stable |
| **V6.0** | **Admin & Stability** | GCR System, Deity Void Resolution, persistent `@vision`. | Stable |
| **V5.3** | **Logic-Data Wall** | Help Sharding, Player Model Sharding (300-line compliance). | Baseline |
| **V5.0** | **Modular Evolution** | Gated Module Init, Resource Purge, UTS Resonance Cache. | Legacy |
| **V4.5** | **Great Realignment** | Root Refactor (`logic/core/`), Sharded God Objects. | Legacy |
| **V2.x** | **Legacy Era** | Hardcoded logic, monolithic files, no event bus. | Archived |

---

## 🔤 SYSTEM ACRONYMS & DEFINITIONS

### **GCA (Godless Class Architecture)**
The universal blueprint for all 50+ classes. Defined in `GEMINI.md`. Ensures classes use standardized `events.py`, `state.py`, and `actions.py` structures.

### **GCR (Godless Combat Rating)**
A V6.0 system that scores entities based on Axis focus (Stability, Position, etc.), Gear, and Environment. Used for taming difficulty and player power assessment. Defined in `logic/core/math/rating.py`.

### **URM (Unified Resource Management)**
The V5.3 standard for class-specific resources (Chi, Fury, Entropy). Logic must use `logic/core/resources.py` or the `resource_registry.py` instead of direct `ext_state` modification.

### **UTS / Resonance (Unified Tag Synergy)**
The system that calculates "Voltage" from tags on gear, blessings, and effects. V5.0 introduced the **Resonance Cache** (O(1) lookups) via the `ResonanceAuditor`.

### **FS (Favor Service)**
The V7.2 economic engine. Implements diminishing returns, daily caps, and the "Triple Sink" Favor model (Kit Swap, Resurrection, Blessings). Located in `logic/core/services/favor_service.py`.

### **IT (Influence Tides)**
The V7.2 projection system. Calculates kingdom territory based on active Shrines and projects a 10-tick visual "Pulse" onto the `influence` map. Managed by `InfluenceService`.

### **GCR System Axes**
- **Stability**: Resistance to Prone/Stun/Off-Balance.
- **Position**: Effectiveness in Forest/High Ground.
- **Endurance**: Vitality and resource regeneration scaling.
- **Flow**: (Monk specific) Combo potential.

---

## 📜 ARCHITECTURAL PROTOCOLS

### **The "Clean Border" Protocol**
Validation happens only at entry points (`input_handler` or `persistence`). Logic modules assume all incoming data is 100% valid.

### **The "Facade" Import Standard**
Never import deep from subdirectories. Use `logic.core` facades (e.g., `from logic.core import combat`).

### **The "Logic-Data Wall" (V5.3)**
Python handles **Events/Side Effects**; JSON handles **Math/Scaling/Potency**. No hardcoded damage numbers in code.

### **The "Ridge Rule" (V7.2)**
Elevation Occlusion: Higher terrain physically blocks vision of entities or pings behind it on the Tactical Map.

### **The "Gatekeeper" Pattern**
Generic "Can I act?" checks (Stunned, Dead, Casting) are centralized in `input_handler.py`.

---

## 📏 CORE RULES & LIMITS

- **300-Line Limit**: No Python logic file may exceed 300 lines (enforced to prevent God Objects).
- **The "@" Prefix Protocol**: The `@` character is strictly reserved for administrative/building commands.
- **Surgical Edit Rule**: For files over 150 lines, use windowed editing to prevent silent deletions.
- **Naming Ghost Protocol**: All constants and engine-facing utilities must use `UPPER_CASE`.
- **Lean Agent Protocol**: Efficiency rules for AI (Skills first, Artifact memory, targeted validation).

---
> [!TIP]
> **Living Document**: This registry should be updated whenever a new version is declared or a core system acronym is coined.
