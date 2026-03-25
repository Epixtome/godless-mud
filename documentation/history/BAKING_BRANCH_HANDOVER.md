# 🍪 STANDARDS SYNCHRONIZATION: THE BAKING PLAN (V7.2)

> **Current Branch:** `standard-synchronization-v7`  
> **Target Goal:** Bring all legacy V5.3 and V6.2 classes and systems up to the V7.2 "Topographical" and "Logic-Data Wall" standards.

---

## 🏔️ 1. PRIMARY ARCHITECTURAL GOALS
The objective of this phase is to eliminate "Version Drift" where core systems use V7.2 logic but individual classes are still operating on hardcoded V5.3/V6.2 logic.

1.  **Topographical Integration (V7.2)**: Re-wiring skills to check for **Elevation** (Ridge Rule) and **Perception Matrix** flags (Occlusion/Vision).
2.  **Logic-Data Wall (V5.3 Compliance)**: Moving all hardcoded math/multipliers out of class `events.py` and into JSON `potency_rules`.
3.  **Unified Resource Management (URM)**: Migrating all class reading/writing from direct `ext_state` access to the `resources.py` facade.
4.  **The 300-Line Limit**: Sharding core modules that have drifted over the line (e.g., `resources.py`).

---

## 🛠️ 2. LAGGING SYSTEMS INVENTORY (PRIORITY DEBT)

### **A. Class Implementation Debt**
| Class | Current Version | Issues |
| :--- | :--- | :--- |
| **Monk** | V6.2 | Math in `events.py` (L25, L52); direct `ext_state` reading for Chi. |
| **Barbarian** | V6.2 | Hardcoded scaling in `calculate_extra_attacks`; math in `on_calculate_mitigation`. |
| **Knight** | V6.2 | Needs integration with the V7.2 "High Ground" Elevation bonus. |
| **Wanderer** | V2.0 (Stub) | Incomplete kit (only 3 blessings instead of 8). |

### **B. Core Engine Debt**
- **`logic/core/resources.py`**: Currently **375 lines** (Exceeds the 300-line limit). Needs sharding.
- **`logic/engines/combat_actions.py`**: High coupling via inline imports; remains a candidate for structural decoupling.
- **Legacy Shims**: `logic/systems.py` still exists as a V4.5 compatibility layer and should eventually be phased out.

---

## 📜 3. CRITICAL PROTOCOLS TO ENFORCE

### **The "Clean Border" Protocol**
Validation happens at `input_handler`. Logic modules assume 100% valid data.

### **The "Logic-Data Wall" Standard**
- **PYTHON**: Handles the *Event Bus* and *Side Effects* (status applied, death dispatched).
- **JSON**: Handles the *Math* (damage ranges, duration factors, scaling multipliers).

### **The "Ridge Rule" Integration**
Skills that fire long-range "Tactical" logic MUST check `perception.occluded(attacker, target)` to ensure they aren't firing through terrain ridges introduced in the V7.2 refactor.

---

## 🧭 4. REFERENCE ARTIFACTS
For the full history and glossary, refer to:
- [GODLESS_SYSTEM_REGISTRY.md](file:///c:/Users/Chris/antigravity/Godless/documentation/GODLESS_SYSTEM_REGISTRY.md)
- [GEMINI.md](file:///c:/Users/Chris/antigravity/Godless/GEMINI.md) (Active Protocol)
- [AGENT_INDEX.md](file:///c:/Users/Chris/antigravity/Godless/documentation/AGENT_INDEX.md)

---
> [!IMPORTANT]
> **Next Step**: Choose a class (e.g., Monk or Barbarian) and perform a "Full Standards Bake" to migrate all logic to JSON potency rules and URM facades.
